
# ut_directory_scraper.py
# Usage examples:
#   python ut_directory_scraper.py --in UT_Fall2025_AllInstructors_Combined.csv
#   python ut_directory_scraper.py --in UT_Fall2025_AllInstructors_Combined.csv --first-col FirstName --last-col LastName --middle-col MI --out ut_directory_results.csv
#
# Features:
# - Accepts a UT-format CSV directly (First/Last columns; optional Middle/MI; or a single "Instructor"/"Name" column).
# - Preserves middle initials/names for the primary query.
# - If no unique match, automatically retries without the middle part.
# - Follows the 50-results page index links and fetches vCards for clean fields.
# - Requires authentication to access directory.utexas.edu
#
# pip install selenium beautifulsoup4 pandas webdriver-manager

import argparse, sys, re, csv, time, random
from typing import List, Dict, Optional, Tuple
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import Counter
import math

BASE = "https://directory.utexas.edu/"

def setup_driver():
    """Setup Chrome driver with options"""
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-images")  # Don't load images
    options.add_argument("--disable-plugins")  # Disable plugins
    options.add_argument("--disable-extensions")  # Disable extensions
    options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def polite_sleep(a=0.3, b=0.7):
    time.sleep(random.uniform(a, b))

def get(driver, url, params=None):
    """Get page using Selenium instead of requests"""
    polite_sleep()
    
    # Build URL with parameters
    if params:
        param_strings = [f"{k}={v}" for k, v in params.items()]
        url = f"{url}?{'&'.join(param_strings)}"
    
    driver.get(url)
    # Wait for page to load - reduced timeout
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
    except:
        # If timeout, just return what we have
        pass
    return driver.page_source

def is_single_result(soup: BeautifulSoup) -> bool:
    h = soup.select_one("#results .display-4")
    return bool(h and h.get_text(strip=True).startswith("Directory Information for"))

def extract_vcard_link(soup: BeautifulSoup) -> Optional[str]:
    a = soup.select_one("#results a[href*='/vcard/']")
    return urljoin(BASE, a["href"]) if a else None

def parse_vcard(text: str) -> Dict[str, str]:
    out = {"fn": "", "email": "", "org": "", "title": "", "tel": ""}
    for line in text.splitlines():
        line = line.strip()
        if line.upper().startswith("FN:"):
            out["fn"] = line[3:].strip()
        elif line.upper().startswith("EMAIL"):
            out["email"] = line.split(":", 1)[-1].strip()
        elif line.upper().startswith("ORG:"):
            out["org"] = line[4:].strip()
        elif line.upper().startswith("TITLE:"):
            out["title"] = line[6:].strip()
        elif line.upper().startswith("TEL"):
            out["tel"] = line.split(":", 1)[-1].strip()
    return out

def fetch_single_result(driver, detail_html: str) -> Dict[str, str]:
    soup = BeautifulSoup(detail_html, "html.parser")
    vurl = extract_vcard_link(soup)
    res = {"name":"", "email":"", "title":"", "department_or_org":"", "phone":""}
    if vurl:
        v = get(driver, vurl)
        data = parse_vcard(v)
        res.update({
            "name": data.get("fn",""),
            "email": data.get("email",""),
            "title": data.get("title",""),
            "department_or_org": data.get("org",""),
            "phone": data.get("tel",""),
        })
    # Also pick extra fields (School/College etc.) if present
    fields = {}
    for row in soup.select("#results .row.mb-3"):
        lab = row.select_one(".detail-field-label")
        val = row.select_one(".detail-field-value")
        if not lab or not val:
            continue
        key = lab.get_text(strip=True).replace(":", "")
        val_text = " ".join(val.get_text(" ", strip=True).split())
        fields[key] = val_text

    if not res["name"]:
        res["name"] = fields.get("Name", "")
    if not res["department_or_org"]:
        res["department_or_org"] = fields.get("School/College", "")

    return res

def parse_50_list(soup: BeautifulSoup) -> List[Tuple[str, str, str]]:
    out = []
    for row in soup.select("#results .row.mb-3.pl-2"):
        a = row.select_one("a[href*='?query='][href*='index=']")
        if not a: 
            continue
        href = urljoin(BASE, a["href"])
        name = a.get_text(strip=True)
        aff_txt = ""
        cont = row.select_one(".results-affiliation-info-container")
        if cont:
            aff_txt = " ".join(cont.get_text(" ", strip=True).split())
        out.append((href, name, aff_txt))
    return out

def is_faculty_row(aff_text: str) -> bool:
    return bool(re.search(r"\bfaculty\b|\bfaculty/staff\b|\bstaff\b", aff_text, re.I))

def search_variant(driver, name_query: str) -> Tuple[List[Dict[str,str]], List[Dict[str,str]]]:
    """Search one name string; return (confirmed_results, manual_review_results)."""
    params = {"query": name_query, "scope": "faculty_staff"}
    html = get(driver, BASE, params=params)
    soup = BeautifulSoup(html, "html.parser")

    # Single result?
    if is_single_result(soup):
        data = fetch_single_result(driver, html)
        # Check similarity score
        similarity_score = cosine_similarity(get_name_vector(name_query), get_name_vector(data.get("name", "")))
        
        if similarity_score >= 0.88:  # High confidence threshold
            data["matched"] = "single"
            data["query_used"] = name_query
            data["similarity_score"] = similarity_score
            print(f"    ✅ High confidence single match: '{data.get('name', '')}' (similarity: {similarity_score:.3f})")
            return [data], []
        else:
            # Everything else goes to manual review
            data["matched"] = "manual_review"
            data["query_used"] = name_query
            data["similarity_score"] = similarity_score
            if similarity_score >= 0.85:
                data["reason"] = "High similarity single result - needs manual verification"
            else:
                data["reason"] = f"Lower similarity single result ({similarity_score:.3f}) - needs manual check"
            print(f"    ⚠️  Single result flagged for manual review: '{data.get('name', '')}' (similarity: {similarity_score:.3f})")
            return [], [data]

    # 50/list page - collect all candidates and find the best match
    candidates = []
    candidate_data = {}
    
    for detail_url, list_name, aff in parse_50_list(soup):
        if not is_faculty_row(aff):
            continue
        
        print(f"    📋 Checking list item: '{list_name}'")
        
        # Quick similarity check on list name
        list_similarity = cosine_similarity(get_name_vector(name_query), get_name_vector(list_name))
        
        if list_similarity >= 0.88:  # Only download if high confidence
            print(f"    ✅ List name high confidence ({list_similarity:.3f}) - downloading details")
            detail_html = get(driver, detail_url)
            data = fetch_single_result(driver, detail_html)
            
            if any(data.values()):
                # Double-check with full name
                final_similarity = cosine_similarity(get_name_vector(name_query), get_name_vector(data.get("name", list_name)))
                
                if final_similarity >= 0.88:  # High confidence - return immediately
                    result_data = data
                    result_data["matched"] = "cosine_similarity"
                    result_data["query_used"] = name_query
                    result_data["similarity_score"] = final_similarity
                    result_data["affiliation_hint"] = aff
                    print(f"    ✅ High confidence match found: '{data.get('name', list_name)}' (similarity: {final_similarity:.3f})")
                    return [result_data], []
                else:
                    # Add to manual review without downloading vCard
                    manual_entry = {
                        "name": data.get("name", list_name),
                        "email": "",
                        "title": "",
                        "department_or_org": "",
                        "phone": "",
                        "matched": "manual_review",
                        "query_used": name_query,
                        "similarity_score": final_similarity,
                        "reason": f"List name high confidence but full name lower ({final_similarity:.3f}) - needs manual verification",
                        "affiliation_hint": aff
                    }
                    candidates.append(manual_entry)
        elif list_similarity >= 0.7:  # Medium confidence - flag for manual review without downloading
            print(f"    ⚠️  List name medium confidence ({list_similarity:.3f}) - flagging for manual review")
            manual_entry = {
                "name": list_name,
                "email": "",
                "title": "",
                "department_or_org": "",
                "phone": "",
                "matched": "manual_review",
                "query_used": name_query,
                "similarity_score": list_similarity,
                "reason": f"Medium confidence list match ({list_similarity:.3f}) - needs manual verification",
                "affiliation_hint": aff
            }
            candidates.append(manual_entry)
        else:
            print(f"    ❌ List name too low confidence ({list_similarity:.3f}) - skipping")
    
    if not candidates:
        print(f"    ❌ No faculty candidates found for '{name_query}'")
        # Add to manual review for user to search manually
        manual_entry = {
            "name": "",
            "email": "",
            "title": "",
            "department_or_org": "",
            "phone": "",
            "matched": "manual_review",
            "query_used": name_query,
            "similarity_score": 0.0,
            "reason": "No faculty candidates found - needs manual search"
        }
        return [], [manual_entry]
    
    # If we get here, we have manual review candidates
    # Return the best one for manual review
    best_candidate = max(candidates, key=lambda x: x["similarity_score"])
    print(f"    ⚠️  Best candidate flagged for manual review: '{best_candidate['name']}' (similarity: {best_candidate['similarity_score']:.3f})")
    return [], [best_candidate]

def normalize_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

def normalize_name_for_comparison(name: str) -> str:
    """Normalize name for comparison by removing titles, extra spaces, and converting to lowercase"""
    if not name:
        return ""
    # Remove common titles and suffixes
    name = re.sub(r'\b(Dr\.?|Professor|Prof\.?|Mr\.?|Mrs\.?|Ms\.?|PhD|MD|MBA|MA|MS|BA|BS)\b', '', name, flags=re.IGNORECASE)
    # Remove extra spaces and convert to lowercase
    name = re.sub(r'\s+', ' ', name.strip()).lower()
    return name

def get_name_vector(name: str) -> Counter:
    """Convert a name into a character frequency vector for cosine similarity"""
    normalized = normalize_name_for_comparison(name)
    
    # Simple character frequency approach
    vector = Counter(normalized)
    
    # Add word-level features for better nickname handling
    words = normalized.split()
    for word in words:
        if len(word) > 2:  # Only add meaningful words
            vector[f"word_{word}"] += 1
    
    return vector

def cosine_similarity(vec1: Counter, vec2: Counter) -> float:
    """Calculate cosine similarity between two character frequency vectors"""
    # Get all unique characters from both vectors
    all_chars = set(vec1.keys()) | set(vec2.keys())
    
    if not all_chars:
        return 0.0
    
    # Calculate dot product
    dot_product = sum(vec1.get(char, 0) * vec2.get(char, 0) for char in all_chars)
    
    # Calculate magnitudes
    mag1 = math.sqrt(sum(vec1.get(char, 0) ** 2 for char in all_chars))
    mag2 = math.sqrt(sum(vec2.get(char, 0) ** 2 for char in all_chars))
    
    # Avoid division by zero
    if mag1 == 0 or mag2 == 0:
        return 0.0
    
    return dot_product / (mag1 * mag2)

def find_best_match(search_name: str, candidates: List[str], threshold: float = 0.65) -> Tuple[Optional[str], float]:
    """Find the best matching name from a list of candidates using cosine similarity with nickname boost"""
    if not candidates:
        return None, 0.0
    
    search_vec = get_name_vector(search_name)
    best_match = None
    best_similarity = 0.0
    
    # Common nickname mappings
    nickname_mappings = {
        'gabi': 'gabriel', 'gabby': 'gabriel', 'gabriela': 'gabriel', 'gabrielle': 'gabriel',
        'bob': 'robert', 'rob': 'robert',
        'jim': 'james', 'jimmy': 'james',
        'mike': 'michael',
        'nick': 'nicholas',
        'chris': 'christopher', 'chris': 'christine',
        'kate': 'katherine', 'katie': 'katherine',
        'liz': 'elizabeth', 'beth': 'elizabeth',
        'joe': 'joseph',
        'tom': 'thomas',
        'dave': 'david',
        'dan': 'daniel',
        'sam': 'samuel', 'sam': 'samantha',
        'alex': 'alexander', 'alex': 'alexandra',
        'pat': 'patricia', 'pat': 'patrick',
    }
    
    for candidate in candidates:
        candidate_vec = get_name_vector(candidate)
        similarity = cosine_similarity(search_vec, candidate_vec)
        
        # Apply nickname boost
        search_words = normalize_name_for_comparison(search_name).split()
        candidate_words = normalize_name_for_comparison(candidate).split()
        
        # Check if any search word is a nickname for any candidate word
        nickname_boost = 0.0
        for search_word in search_words:
            for candidate_word in candidate_words:
                if search_word in nickname_mappings and nickname_mappings[search_word] == candidate_word:
                    nickname_boost = 0.1  # Boost similarity for nickname relationships
                    break
            if nickname_boost > 0:
                break
        
        similarity += nickname_boost
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = candidate
    
    # Only return if similarity meets threshold
    if best_similarity >= threshold:
        return best_match, best_similarity
    
    return None, 0.0

def names_match(search_name: str, found_name: str, threshold: float = 0.7) -> bool:
    """Check if the found name matches the search name using cosine similarity"""
    if not search_name or not found_name:
        return False
    
    search_normalized = normalize_name_for_comparison(search_name)
    found_normalized = normalize_name_for_comparison(found_name)
    
    # Exact match after normalization
    if search_normalized == found_normalized:
        return True
    
    # Calculate cosine similarity
    search_vec = get_name_vector(search_name)
    found_vec = get_name_vector(found_name)
    similarity = cosine_similarity(search_vec, found_vec)
    
    return similarity >= threshold

def build_name_variants(first: str, middle: str, last: str) -> List[str]:
    """Return [First Middle Last, First Last] if middle exists; else [First Last]. Preserve middle exactly as given."""
    first = normalize_spaces(first)
    middle = normalize_spaces(middle)
    last = normalize_spaces(last)
    variants = []
    if first and last:
        if middle:
            # Try full name first, then without middle
            variants.append(f'{first} {middle} {last}'.strip())
            variants.append(f'{first} {last}'.strip())
        else:
            variants.append(f'{first} {last}'.strip())
    elif first or last:
        variants.append(normalize_spaces(f'{first} {last}'))
    return variants

def build_variants_from_single(fullname: str) -> List[str]:
    """If a single column has the name; preserve middle part; also add no-middle fallback."""
    fullname = normalize_spaces(fullname)
    if not fullname:
        return []
    # If "Last, First Middle" -> rearrange to First Middle Last (preserve middle)
    if "," in fullname:
        last, rest = [x.strip() for x in fullname.split(",", 1)]
        parts = rest.split()
        if parts:
            first = parts[0]
            middle = " ".join(parts[1:])
        else:
            first, middle = "", ""
        last = last.split()[0]
        return build_name_variants(first, middle, last)
    else:
        # Already "First (Middle) Last" likely; also compute no-middle fallback
        parts = fullname.split()
        if len(parts) >= 3:
            first = parts[0]
            last = parts[-1]
            middle = " ".join(parts[1:-1])
            return build_name_variants(first, middle, last)
        elif len(parts) == 2:
            first, last = parts
            return build_name_variants(first, "", last)
        return [fullname]

def autodetect_columns(cols: List[str]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Return (first, middle, last, single)."""
    # exact/near-exact matches
    def find(names):
        for c in cols:
            if c.lower() in [n.lower() for n in names]:
                return c
        return None

    first = find(["FirstName", "First Name", "First"])
    last  = find(["LastName", "Last Name", "Last", "Surname"])
    middle = find(["MiddleName", "Middle Name", "Middle", "MI", "M.I.", "Middle Initial"])

    # Single-name fallbacks
    single = find(["Instructor", "Instructor Name", "Name", "Professor", "Primary Instructor", "FullName"])

    return first, middle, last, single

def read_names_from_csv(path: str, first_col: Optional[str], middle_col: Optional[str], last_col: Optional[str], single_col: Optional[str]) -> List[Tuple[str, List[str]]]:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    cols = list(df.columns)
    if not (first_col or last_col or single_col):
        # try autodetect
        first_col, middle_col, last_col, single_col = autodetect_columns(cols)

    if first_col and last_col:
        names = []
        mid_present = middle_col in cols if middle_col else False
        for _, r in df.iterrows():
            first = r.get(first_col, "")
            last = r.get(last_col, "")
            middle = r.get(middle_col, "") if mid_present else ""
            variants = build_name_variants(first, middle, last)
            if variants:
                # label is a canonical "First Middle Last" if possible
                label = normalize_spaces(" ".join([first, middle, last]))
                names.append((label if label.strip() else normalize_spaces(f"{first} {last}"), variants))
        return names

    if single_col:
        names = []
        for _, r in df.iterrows():
            nm = r.get(single_col, "")
            variants = build_variants_from_single(nm)
            if variants:
                names.append((normalize_spaces(nm), variants))
        return names

    raise SystemExit("Could not determine name columns. Provide --first-col/--last-col or --single-col.")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_csv", required=True, help="Input UT CSV (e.g., UT_Fall2025_AllInstructors_Combined.csv)")
    ap.add_argument("--out", dest="out_csv", default="ut_directory_results.csv")
    ap.add_argument("--first-col", dest="first_col", default=None, help="Column name for first name (optional if autodetect works)")
    ap.add_argument("--middle-col", dest="middle_col", default=None, help="Column name for middle/MI (optional)")
    ap.add_argument("--last-col", dest="last_col", default=None, help="Column name for last name (optional if autodetect works)")
    ap.add_argument("--single-col", dest="single_col", default=None, help="Single column containing full name (optional)")
    args = ap.parse_args()

    # Setup Selenium driver
    print("🚀 Starting Chrome browser...")
    driver = setup_driver()
    
    print("🔐 Please log into UT Directory when the browser opens...")
    print("📱 You'll need to complete Duo authentication when prompted.")
    
    # Open UT Directory login page
    driver.get("https://directory.utexas.edu/")
    
    # Wait for user to log in
    input("Press Enter after you've completed the Duo authentication and are logged into UT Directory...")
    
    # Test if we can access the directory
    driver.get("https://directory.utexas.edu/")
    time.sleep(2)
    
    # Check if we're still logged in
    if "login" in driver.current_url.lower() or "auth" in driver.current_url.lower():
        print("⚠️  Warning: Login session may not be valid.")
        print("🔐 Please make sure you're properly logged in before continuing.")
        input("Press Enter to continue anyway, or Ctrl+C to exit...")
    else:
        print("✅ Login session confirmed!")
    
    print("🔍 Login successful! Starting directory search process.")

    # Build (label, variants[]) from CSV
    try:
        label_variants = read_names_from_csv(args.in_csv, args.first_col, args.middle_col, args.last_col, args.single_col)
        print(f"📊 Processing {len(label_variants)} names...")
    except Exception as e:
        print(f"Input error: {e}", file=sys.stderr)
        driver.quit()
        sys.exit(2)

    seen = set()
    confirmed_rows = []
    manual_review_rows = []
    
    for idx, (label, variants) in enumerate(label_variants, 1):
        # De-dup identical labels
        if label.lower() in seen:
            continue
        seen.add(label.lower())

        print(f"[{idx}/{len(label_variants)}] {label}")
        # Try variants in order: quoted full (if available), full, no-middle
        found_any = False
        for v_idx, v in enumerate(variants):
            print(f"    🔍 Trying variant {v_idx + 1}/{len(variants)}: '{v}'")
            try:
                confirmed_results, manual_review_results = search_variant(driver, v)
                
                # Handle confirmed results
                if confirmed_results:
                    print(f"    ✅ Found {len(confirmed_results)} confirmed match(es) for '{v}'")
                    for data in confirmed_results:
                        out = {
                            "input_label": label,
                            "query_used": data.get("query_used", v),
                            "matched": data.get("matched",""),
                            "name": data.get("name",""),
                            "email": data.get("email",""),
                            "title": data.get("title",""),
                            "department_or_org": data.get("department_or_org",""),
                            "phone": data.get("phone",""),
                            "affiliation_hint": data.get("affiliation_hint",""),
                            "similarity_score": data.get("similarity_score", ""),
                        }
                        confirmed_rows.append(out)
                    found_any = True
                    break  # stop after first successful variant
                
                # Handle manual review results
                elif manual_review_results:
                    print(f"    ⚠️  Found {len(manual_review_results)} case(s) for manual review for '{v}'")
                    for data in manual_review_results:
                        out = {
                            "input_label": label,
                            "query_used": data.get("query_used", v),
                            "matched": data.get("matched",""),
                            "name": data.get("name",""),
                            "email": data.get("email",""),
                            "title": data.get("title",""),
                            "department_or_org": data.get("department_or_org",""),
                            "phone": data.get("phone",""),
                            "affiliation_hint": data.get("affiliation_hint",""),
                            "similarity_score": data.get("similarity_score", ""),
                            "reason": data.get("reason", ""),
                            "close_candidates": data.get("close_candidates", ""),
                        }
                        manual_review_rows.append(out)
                    found_any = True
                    break  # stop after first result (confirmed or manual review)
                
                else:
                    print(f"    ❌ No matches found for '{v}'")
                    
            except Exception as e:
                print(f"    ⚠️  Error searching for '{v}': {type(e).__name__}")
                manual_review_rows.append({
                    "input_label": label, "query_used": v,
                    "matched": f"error: {type(e).__name__}",
                    "name":"", "email":"", "title":"",
                    "department_or_org":"", "phone":"", "affiliation_hint": "",
                    "similarity_score": "", "reason": f"Search error: {type(e).__name__}",
                    "close_candidates": ""
                })
                # continue to next variant
        
        if not found_any:
            print(f"    ❌ No matches found for any variant of '{label}'")
            manual_review_rows.append({
                "input_label": label, "query_used": variants[0] if variants else "",
                "matched":"none", "name":"", "email":"", "title":"",
                "department_or_org":"", "phone":"", "affiliation_hint": "",
                "similarity_score": "", "reason": "No matches found for any variant",
                "close_candidates": ""
            })

    # Close the browser
    driver.quit()

    # Write confirmed results to main CSV
    if confirmed_rows:
        confirmed_df = pd.DataFrame(confirmed_rows, columns=[
            "input_label","query_used","matched","name","email","title","department_or_org","phone","affiliation_hint","similarity_score"
        ])
        confirmed_df.to_csv(args.out_csv, index=False)
        print(f"✅ Wrote {len(confirmed_df)} confirmed results -> {args.out_csv}")
    else:
        print("ℹ️  No confirmed results to write to main CSV")

    # Write manual review cases to separate CSV
    if manual_review_rows:
        manual_review_file = args.out_csv.replace('.csv', '_manual_review.csv')
        manual_review_df = pd.DataFrame(manual_review_rows, columns=[
            "input_label","query_used","matched","name","email","title","department_or_org","phone","affiliation_hint","similarity_score","reason","close_candidates"
        ])
        manual_review_df.to_csv(manual_review_file, index=False)
        print(f"⚠️  Wrote {len(manual_review_df)} cases for manual review -> {manual_review_file}")
    else:
        print("ℹ️  No manual review cases to write")

if __name__ == "__main__":
    main()
