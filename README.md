# UT Instructor Scraper

This project scrapes instructor information from UT Austin's course schedule system for Fall 2025.

## 🚀 **Quick Start**

1. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Run the scraper:**
   ```bash
   python ut_instructor_scraper_simple.py
   ```

3. **Log into UT Direct** when Chrome opens, then press Enter

## 📋 **What It Does**

- **Scrapes all courses** from 00000 to 99999 (100,000 total)
- **Extracts instructor names** from course schedule pages
- **Handles multiple instructors** per course
- **Removes duplicates** automatically
- **Saves to CSV** on your Desktop
- **Shows real-time progress** in terminal

## ⚡ **Performance**

- **Speed**: 0.1 second delay between requests
- **Duration**: ~2.8 hours for full scan
- **Progress**: Updates every course page
- **Memory**: Uses sets to avoid duplicates

## 📊 **Output**

Creates `UT_Fall2025_ScrapedInstructors.csv` on your Desktop with:
- **FirstName**: Instructor's first name
- **LastName**: Instructor's last name

## 🔧 **Technical Details**

### Dependencies
- `selenium`: Web automation and scraping
- `pandas`: Data manipulation and CSV export
- `webdriver-manager`: Chrome driver management

### URL Format
```
https://utdirect.utexas.edu/apps/registrar/course_schedule/20259/{course_number}/
```

### Element Targeting
- Looks for `td[@data-th='Instructor']` cells
- Handles multiple instructors per course (split by newlines)
- Skips courses with "Class information not available" errors

## 🛠 **Files**

- `ut_instructor_scraper_simple.py` - **Main scraper**
- `requirements.txt` - Python dependencies
- `README.md` - This documentation

## 🚨 **Notes**

- Requires UT Direct login
- Respects server with 0.1s delays
- Most course numbers (00000-99999) don't exist, so it's efficient
- Can be stopped and restarted if needed

## 🆘 **Troubleshooting**

If you get blocked or errors:
1. Increase the `time.sleep()` delay
2. Restart the script
3. Check your internet connection

## 📈 **Progress Example**

```
📊 Progress: 0.001% (00001/100000) - Found 3 instructors so far
📊 Progress: 0.002% (00002/100000) - Found 3 instructors so far
📊 Progress: 0.003% (00003/100000) - Found 5 instructors so far
```

## 🎯 **Deactivating the Environment**

When you're done working:
```bash
deactivate
```

