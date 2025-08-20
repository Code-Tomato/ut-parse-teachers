from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import os
import time
import webbrowser

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
    """Main scraping function with automatic Chrome setup"""
    print("🚀 Starting UT Instructor Scraper...")
    
    # Setup Chrome options
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Install and setup Chrome driver
    print("📥 Setting up Chrome driver...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    print("✅ Chrome started successfully!")
    print("🔐 Please log into UT Direct when the browser opens...")
    
    # Open UT Direct login page
    driver.get("https://utdirect.utexas.edu/")
    
    # Wait for user to log in
    input("Press Enter after you've logged into UT Direct...")

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
    
    # Base URL with correct format
    base_url = "https://utdirect.utexas.edu/apps/registrar/course_schedule/20259/{:05d}/"
    
    instructors = set()
    total_courses = end_unique - start_unique
    
    print(f"📚 Scraping {total_courses} courses ({start_unique:05d}-{end_unique - 1:05d})...")
    
    for i, unique in enumerate(range(start_unique, end_unique)):
        url = base_url.format(unique)
        
        # Progress indicator - show every page
        progress = (i / total_courses) * 100
        print(f"📊 Progress: {progress:.3f}% ({i+1:05d}/{total_courses:05d}) - Found {len(instructors)} instructors so far")
        
        # Save progress every 1000 courses
        if i > 0 and i % 1000 == 0:
            save_progress(instructors)
        
        try:
            driver.get(url)
            time.sleep(0.1)  # Fast but respectful delay
            
            # Check if there's an error message (course doesn't exist)
            error_elements = driver.find_elements(By.XPATH, "//div[@class='error']")
            if error_elements:
                continue  # Skip this course, it doesn't exist
            
            # Look for instructor names in the table
            instructor_cells = driver.find_elements(By.XPATH, "//td[@data-th='Instructor']")
            
            for cell in instructor_cells:
                # Get all text content from the cell
                cell_text = cell.text.strip()
                if cell_text:
                    # Split by lines and process each instructor
                    instructors_in_cell = cell_text.split('\n')
                    for instructor in instructors_in_cell:
                        instructor = instructor.strip()
                        if instructor and instructor not in ["Staff", "TBA", ""]:
                            instructors.add(instructor)
                        
        except Exception as e:
            print(f"⚠️  Skipped course {unique:05d}: {e}")
            continue
    
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
    
    driver.quit()

if __name__ == "__main__":
    scrape_instructors()
