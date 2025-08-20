# UT Instructor Scraper Setup Instructions

This script scrapes instructor information from UT Austin's course schedule system. Follow these steps to set up and run the scraper on your computer.

## Prerequisites

- **Python 3.8 or higher** (check with `python3 --version`)
- **Chrome browser** installed on your computer
- **UT Austin EID and password** (you'll need to authenticate with Duo)

## Step-by-Step Setup

### 1. Download the Files
Make sure you have these files in a folder:
- `ut_instructor_scraper_simple.py`
- `requirements.txt`

### 2. Open Terminal/Command Prompt
- **Mac/Linux**: Open Terminal
- **Windows**: Open Command Prompt or PowerShell

### 3. Navigate to the Script Folder
```bash
cd /path/to/your/script/folder
```
Replace `/path/to/your/script/folder` with the actual path where you saved the files.

### 4. Create a Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

You should see `(venv)` at the beginning of your command line when it's activated.

### 5. Install Dependencies
```bash
pip install -r requirements.txt
```

This will install:
- `selenium` (for web automation)
- `pandas` (for data processing)
- `webdriver-manager` (for Chrome driver management)

### 6. Run the Scraper
```bash
python ut_instructor_scraper_simple.py
```

## First-Time Setup Process

### 1. Choose Your Mode
When you run the script, you'll see three options:
- **Option 1**: Visible browser window (recommended for first time)
- **Option 2**: Headless mode (faster, no visible window)
- **Option 3**: Headless mode with debug output

**For first-time users, choose Option 1** to see what's happening.

### 2. Authentication Process
1. A Chrome browser window will open
2. Navigate to UT Direct login page
3. Enter your UT EID and password
4. Complete Duo authentication when prompted
5. Once logged in, return to the terminal and press Enter

### 3. Configure Scraping Range
- **Starting unique number**: Usually `0` (press Enter for default)
- **Ending unique number**: Usually `100000` (press Enter for default)
- This will scrape courses from 00000 to 99999

## What the Script Does

1. **Logs into UT Direct** using your credentials
2. **Scrapes course information** for the specified range
3. **Extracts instructor names** from each course
4. **Saves results** to a CSV file on your Desktop
5. **Opens the file** automatically when complete

## Output

The script creates a file called `UT_Fall2025_ScrapedInstructors.csv` on your Desktop with columns:
- `FirstName`: Instructor's first name
- `LastName`: Instructor's last name

## Troubleshooting

### Common Issues:

**"Chrome driver not found"**
- The script automatically downloads the correct Chrome driver
- Make sure you have Chrome browser installed

**"Authentication failed"**
- Make sure you complete the Duo authentication
- Try running with Option 1 (visible mode) first

**"Permission denied"**
- Make sure you're in the correct directory
- Check that the virtual environment is activated

**"Module not found"**
- Make sure you installed requirements: `pip install -r requirements.txt`
- Make sure virtual environment is activated

### Performance Tips:

- **First run**: Use Option 1 (visible mode) to authenticate
- **Subsequent runs**: Use Option 2 (headless mode) for speed
- **Large ranges**: The script saves progress every 1000 courses
- **Interruption**: You can stop with Ctrl+C and restart from where you left off

## Security Notes

- The script only accesses public course information
- Your login credentials are not stored
- The script uses your existing browser session
- No data is sent to external servers

## Support

If you encounter issues:
1. Make sure all prerequisites are installed
2. Try running with Option 1 first
3. Check that your UT credentials work in a regular browser
4. Ensure you have a stable internet connection

The script is designed to be robust and will continue even if some courses fail to load.

