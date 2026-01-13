from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import os
import time
import webbrowser

def scrape_single_course(driver, unique, debug=False):
    """Scrape a single course"""
    try:
        url = f"https://utdirect.utexas.edu/apps/registrar/course_schedule/20262/{unique:05d}/"
        
        # Add timeout and retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                driver.set_page_load_timeout(30)
                driver.get(url)
                time.sleep(0.3)  # Wait for page to load
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    if debug:
                        print(f"⚠️  Course {unique:05d} attempt {attempt + 1} failed: {e}, retrying...")
                    time.sleep(1)
                    continue
                else:
                    raise e
        
        # Check if there's an error message (course doesn't exist)
        error_elements = driver.find_elements(By.XPATH, "//div[@class='error']")
        if error_elements:
            if debug:
                print(f"❌ Course {unique:05d}: Course doesn't exist")
            return []
        
        # Look for instructor names in the table
        instructor_cells = driver.find_elements(By.XPATH, "//td[@data-th='Instructor']")
        
        if debug:
            print(f"📊 Course {unique:05d}: Found {len(instructor_cells)} instructor cells")
        
        course_instructors = []
        for cell in instructor_cells:
            cell_text = cell.text.strip()
            if cell_text:
                instructors_in_cell = cell_text.split('\n')
                for instructor in instructors_in_cell:
                    instructor = instructor.strip()
                    if instructor and instructor not in ["Staff", "TBA", ""]:
                        course_instructors.append(instructor)
        
        if debug and course_instructors:
            print(f"👨‍🏫 Course {unique:05d}: Found instructors: {course_instructors}")
        
        return course_instructors
        
    except Exception as e:
        print(f"⚠️  Skipped course {unique:05d}: {e}")
        return []

def save_progress(instructors, append_mode=False, run_id=None):
    """Save current progress to CSV file"""
    if instructors:
        cleaned = sorted(list(instructors))
        split_names = []
        
        for name in cleaned:
            if "," in name:
                parts = name.split(",", 1)
                if len(parts) == 2:
                    last_name = parts[0].strip()
                    first_name = parts[1].strip()
                    split_names.append([first_name, last_name])
            else:
                split_names.append([name, ""])
        
        df = pd.DataFrame(split_names, columns=["FirstName", "LastName"])
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        
        if append_mode and run_id is None:
            # Append mode - add to existing file
            base_file_path = os.path.join(desktop, "UT_Spring2026_ScrapedInstructors.csv")
            
            if os.path.exists(base_file_path):
                # Read existing data
                existing_df = pd.read_csv(base_file_path)
                # Combine with new data
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                # Remove duplicates
                combined_df = combined_df.drop_duplicates(subset=['FirstName', 'LastName'])
                # Save combined data
                combined_df.to_csv(base_file_path, index=False)
                print(f"💾 Appended {len(split_names)} new instructors to existing file. Total: {len(combined_df)} instructors")
            else:
                # Create new file
                df.to_csv(base_file_path, index=False)
                print(f"💾 Created new file with {len(split_names)} instructors")
        else:
            # Unique filename mode
            if run_id:
                file_path = os.path.join(desktop, f"UT_Spring2026_ScrapedInstructors_Run{run_id}.csv")
            else:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(desktop, f"UT_Spring2026_ScrapedInstructors_{timestamp}.csv")
            
            df.to_csv(file_path, index=False)
            print(f"💾 Progress saved: {len(split_names)} instructors to {os.path.basename(file_path)}")

def scrape_instructors():
    """Main scraping function - simple and reliable"""
    print("🚀 Starting UT Instructor Scraper - Simple & Reliable Version")
    
    # Configuration
    debug_mode = False
    
    print("🔐 Setting up authentication...")
    print("📥 Setting up Chrome driver...")
    
    # Setup Chrome driver
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    print("✅ Chrome started successfully!")
    print("🔐 Please log into UT Direct when the browser opens...")
    print("📱 You'll need to complete Duo authentication when prompted.")
    
    # Open UT Direct login page
    driver.get("https://utdirect.utexas.edu/")
    
    # Wait for user to log in
    input("Press Enter after you've completed the Duo authentication and are logged into UT Direct...")
    
    # Test if we can access a protected page
    driver.get("https://utdirect.utexas.edu/apps/registrar/course_schedule/20262/00001/")
    time.sleep(2)
    
    # Check if we're still logged in
    if "login" in driver.current_url.lower() or "auth" in driver.current_url.lower():
        print("⚠️  Warning: Login session may not be valid.")
        print("🔐 Please make sure you're properly logged in before continuing.")
        input("Press Enter to continue anyway, or Ctrl+C to exit...")
    else:
        print("✅ Login session confirmed!")
    
    print("🔍 Login successful! Starting scraping process.")

    # Ask user for start/end of unique course number range
    def ask_int(prompt, default, min_val, max_val):
        while True:
            raw = input(f"{prompt} (default {default:05d}): ").strip()
            if raw == "":
                return default
            if raw.isdigit():
                val = int(raw)
                if min_val <= val <= max_val:
                    return val
            print(f"❌ Please enter a number between {min_val:05d} and {max_val:05d}, or press Enter for default.")

    start_unique = ask_int("Enter starting unique number (00000–99999)", 0, 0, 99999)
    end_unique = ask_int("Enter ending unique number EXCLUSIVE (must be > start, max 100000)", 100000, start_unique + 1, 100000)
    
    # Ask about file handling for multiple runs
    print("\n📁 File Handling for Multiple Runs:")
    print("1. Append to existing file (combine results from multiple runs)")
    print("2. Create unique filename for this run")
    print("3. Overwrite existing file (default behavior)")
    
    file_choice = input("Choose file handling (1/2/3, default 3): ").strip()
    
    append_mode = False
    run_id = None
    
    if file_choice == "1":
        append_mode = True
        print("✅ Will append results to existing file")
    elif file_choice == "2":
        run_id = input("Enter run ID (e.g., 'A', 'B', '1', '2'): ").strip()
        if not run_id:
            run_id = time.strftime("%Y%m%d_%H%M%S")
        print(f"✅ Will create unique file: UT_Spring2026_ScrapedInstructors_Run{run_id}.csv")
    else:
        print("✅ Will overwrite existing file (default)")
    
    instructors = set()
    total_courses = end_unique - start_unique
    processed_count = 0
    
    print(f"📚 Scraping {total_courses} courses ({start_unique:05d}-{end_unique - 1:05d})...")
    print("💡 You can watch the scraping process in the browser window!")
    print("💡 The browser will stay open throughout the entire process.")
    
    try:
        for unique in range(start_unique, end_unique):
            course_instructors = scrape_single_course(driver, unique, debug_mode)
            
            # Add to our collection
            for instructor in course_instructors:
                instructors.add(instructor)
            
            processed_count += 1
            
            # Progress indicator every 10 courses
            if processed_count % 10 == 0:
                progress = (processed_count / total_courses) * 100
                print(f"📊 Progress: {progress:.1f}% ({processed_count:05d}/{total_courses:05d}) - Found {len(instructors)} instructors so far")
            
            # Save progress every 1000 courses
            if processed_count > 0 and processed_count % 1000 == 0:
                save_progress(instructors, append_mode, run_id)
    
    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
        print(f"📊 Partial results: {len(instructors)} instructors found so far")
    
    except Exception as e:
        print(f"⚠️  Error during scraping: {e}")
    
    print(f"✅ Scraping complete! Found {len(instructors)} unique instructors")
    
    # Clean and split names
    cleaned = sorted(list(instructors))
    split_names = []
    
    for name in cleaned:
        if "," in name:
            parts = name.split(",", 1)
            if len(parts) == 2:
                last_name = parts[0].strip()
                first_name = parts[1].strip()
                split_names.append([first_name, last_name])
        else:
            # Handle names without commas (just add as is)
            split_names.append([name, ""])
    
    # Output to CSV
    if split_names:
        df = pd.DataFrame(split_names, columns=["FirstName", "LastName"])
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        
        if append_mode:
            # Append mode
            base_file_path = os.path.join(desktop, "UT_Spring2026_ScrapedInstructors.csv")
            
            if os.path.exists(base_file_path):
                # Read existing data
                existing_df = pd.read_csv(base_file_path)
                # Combine with new data
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                # Remove duplicates
                combined_df = combined_df.drop_duplicates(subset=['FirstName', 'LastName'])
                # Save combined data
                combined_df.to_csv(base_file_path, index=False)
                print(f"💾 Final results: {len(split_names)} new instructors added. Total: {len(combined_df)} instructors")
            else:
                # Create new file
                df.to_csv(base_file_path, index=False)
                print(f"💾 Created new file with {len(split_names)} instructors")
            
            file_path = base_file_path
        else:
            # Unique filename mode
            if run_id:
                file_path = os.path.join(desktop, f"UT_Spring2026_ScrapedInstructors_Run{run_id}.csv")
            else:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(desktop, f"UT_Spring2026_ScrapedInstructors_{timestamp}.csv")
            
            df.to_csv(file_path, index=False)
            print(f"💾 Saved {len(split_names)} instructors to: {os.path.basename(file_path)}")
        
        # Open the file
        try:
            webbrowser.open("file://" + file_path)
        except:
            print(f"📁 File saved to: {file_path}")
    else:
        print("❌ No instructor data found!")
    
    print("🔍 Browser window will remain open. You can close it manually when done.")

if __name__ == "__main__":
    scrape_instructors()
