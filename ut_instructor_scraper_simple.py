from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import os
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Global variables for session management
login_driver = None
session_cookies = None

def get_driver(headless=True, use_existing_session=False):
    """Get or create a webdriver instance for the current thread"""
    global login_driver, session_cookies
    
    if use_existing_session and login_driver:
        # Use the existing logged-in driver
        return login_driver
    
    # Create new driver
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    if headless:
        options.add_argument("--headless")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--window-size=800,600")
    else:
        # For visible mode, use smaller windows and position them
        options.add_argument("--window-size=600,400")
        # Try to use tabs instead of new windows
        options.add_argument("--new-window")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Apply session cookies if available
    if session_cookies and not use_existing_session:
        try:
            driver.get("https://utdirect.utexas.edu/")
            for cookie in session_cookies:
                driver.add_cookie(cookie)
            print(f"🍪 Applied {len(session_cookies)} cookies to new browser")
        except Exception as e:
            print(f"⚠️  Could not apply cookies: {e}")
    
    return driver

def scrape_courses_batch(course_numbers, headless=True, debug=False, use_existing_session=False):
    """Scrape a batch of courses using a single browser instance"""
    global login_driver
    
    try:
        # Get a driver (either new or existing logged-in one)
        driver = get_driver(headless, use_existing_session)
        
        all_instructors = []
        
        for i, unique in enumerate(course_numbers):
            try:
                url = f"https://utdirect.utexas.edu/apps/registrar/course_schedule/20259/{unique:05d}/"
                
                # Add timeout and retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        driver.set_page_load_timeout(10)  # 10 second timeout
                        driver.get(url)
                        
                        # Dynamic delay based on attempt number
                        if attempt == 0:
                            time.sleep(0.1)  # Fast for first attempt
                        else:
                            time.sleep(0.5 * (attempt + 1))  # Longer delays for retries
                        
                        break  # Success, exit retry loop
                        
                    except Exception as e:
                        if attempt < max_retries - 1:
                            if debug:
                                print(f"⚠️  Course {unique:05d} attempt {attempt + 1} failed: {e}, retrying...")
                            time.sleep(1)  # Wait before retry
                            continue
                        else:
                            raise e  # Last attempt failed
                
                # Clear browser cache periodically to prevent slowdown
                if i > 0 and i % 50 == 0:
                    try:
                        driver.delete_all_cookies()
                        driver.execute_script("window.localStorage.clear();")
                        driver.execute_script("window.sessionStorage.clear();")
                        if debug:
                            print(f"🧹 Cleared browser cache after {i} courses")
                    except:
                        pass
                
                # Debug: Print page title and URL
                if debug:
                    print(f"🔍 Course {unique:05d}: {driver.title} | {driver.current_url}")
                
                # Check if there's an error message (course doesn't exist)
                error_elements = driver.find_elements(By.XPATH, "//div[@class='error']")
                if error_elements:
                    if debug:
                        print(f"❌ Course {unique:05d}: Course doesn't exist")
                    continue  # Course doesn't exist
                
                # Look for instructor names in the table
                instructor_cells = driver.find_elements(By.XPATH, "//td[@data-th='Instructor']")
                
                if debug:
                    print(f"📊 Course {unique:05d}: Found {len(instructor_cells)} instructor cells")
                
                for cell in instructor_cells:
                    # Get all text content from the cell
                    cell_text = cell.text.strip()
                    if cell_text:
                        # Split by lines and process each instructor
                        instructors_in_cell = cell_text.split('\n')
                        for instructor in instructors_in_cell:
                            instructor = instructor.strip()
                            if instructor and instructor not in ["Staff", "TBA", ""]:
                                all_instructors.append(instructor)
                
                if debug and all_instructors:
                    print(f"👨‍🏫 Course {unique:05d}: Found instructors: {all_instructors[-len(instructor_cells):]}")
                    
            except Exception as e:
                print(f"⚠️  Skipped course {unique:05d}: {e}")
                continue
        
        return all_instructors
        
    except Exception as e:
        print(f"⚠️  Error in batch processing: {e}")
        return []

def save_progress(instructors):
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
        file_path = os.path.join(desktop, "UT_Fall2025_ScrapedInstructors.csv")
        df.to_csv(file_path, index=False)
        
        print(f"💾 Progress saved: {len(split_names)} instructors to CSV")

def scrape_instructors():
    """Main scraping function with concurrent processing"""
    global login_driver, session_cookies
    
    print("🚀 Starting UT Instructor Scraper...")
    
    # Setup initial Chrome driver for login
    print("📥 Setting up Chrome driver for login...")
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    login_driver = webdriver.Chrome(service=service, options=options)
    
    print("✅ Chrome started successfully!")
    print("🔐 Please log into UT Direct when the browser opens...")
    
    # Open UT Direct login page
    login_driver.get("https://utdirect.utexas.edu/")
    
    # Wait for user to log in
    input("Press Enter after you've logged into UT Direct...")
    
    # Store the login driver globally for reuse
    session_cookies = None
    
    try:
        session_cookies = login_driver.get_cookies()
        print(f"🍪 Captured {len(session_cookies)} cookies from login session")
        
        # Test if we can access a protected page
        login_driver.get("https://utdirect.utexas.edu/apps/registrar/course_schedule/20259/00001/")
        time.sleep(1)
        
        # Check if we're still logged in
        if "login" in login_driver.current_url.lower() or "auth" in login_driver.current_url.lower():
            print("⚠️  Warning: Login session may not be valid.")
        else:
            print("✅ Login session confirmed - will reuse this browser for scraping")
            
    except Exception as e:
        print(f"⚠️  Could not capture cookies: {e}")
        session_cookies = None
    
    print("🔍 Login successful! The browser window will stay open for reference.")
    print("💡 You can keep it open to monitor the scraping process or close it manually.")
    
    # Ask user about scraping options
    print("\n🔧 Configuration Options:")
    print("1. Use existing logged-in browser (fastest, single window)")
    print("2. Create new headless browsers (faster, no visible windows)")
    print("3. Create new visible browsers (slower, multiple windows)")
    
    mode_input = input("Choose mode (1/2/3, default: 1): ").strip()
    
    if mode_input == "2":
        headless_mode = True
        use_existing_session = False
        print("🚀 Starting with new headless browsers...")
    elif mode_input == "3":
        headless_mode = False
        use_existing_session = False
        print("🚀 Starting with new visible browser windows...")
    else:
        headless_mode = False
        use_existing_session = True
        print("🚀 Starting with existing logged-in browser...")
    
    debug_input = input("Enable debug output? (y/n, default: n): ").strip().lower()
    debug_mode = debug_input == 'y'
    
    if debug_mode:
        print("🐛 Debug mode enabled - you'll see detailed output for each course")
    
    # Don't close the login driver - let user decide when to close it

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
    
    instructors = set()
    total_courses = end_unique - start_unique
    processed_count = 0
    
    print(f"📚 Scraping {total_courses} courses ({start_unique:05d}-{end_unique - 1:05d})...")
    
    # Process courses in batches
    batch_size = 20  # Process 20 courses at a time
    all_course_numbers = list(range(start_unique, end_unique))
    
    for i in range(0, len(all_course_numbers), batch_size):
        batch = all_course_numbers[i:i + batch_size]
        processed_count += len(batch)
        
        print(f"📦 Processing batch {i//batch_size + 1}/{(len(all_course_numbers) + batch_size - 1)//batch_size} (courses {batch[0]:05d}-{batch[-1]:05d})")
        
        # Scrape this batch
        batch_instructors = scrape_courses_batch(batch, headless_mode, debug_mode, use_existing_session)
        
        # Add to our collection
        for instructor in batch_instructors:
            instructors.add(instructor)
        
        # Progress indicator
        progress = (processed_count / total_courses) * 100
        print(f"📊 Progress: {progress:.3f}% ({processed_count:05d}/{total_courses:05d}) - Found {len(instructors)} instructors so far")
        
        # Save progress every 1000 courses
        if processed_count > 0 and processed_count % 1000 == 0:
            save_progress(instructors)
    
    # Clean up drivers
    if not use_existing_session:
        try:
            if login_driver:
                login_driver.quit()
        except:
            pass
    
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
        file_path = os.path.join(desktop, "UT_Fall2025_ScrapedInstructors.csv")
        df.to_csv(file_path, index=False)
        
        print(f"💾 Saved {len(split_names)} instructors to: {file_path}")
        
        # Open the file
        try:
            webbrowser.open("file://" + file_path)
        except:
            print(f"📁 File saved to: {file_path}")
    else:
        print("❌ No instructor data found!")

if __name__ == "__main__":
    scrape_instructors()
