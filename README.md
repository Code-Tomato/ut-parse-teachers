# UT Instructor Scraper Project

A comprehensive toolset for scraping instructor information from UT Austin's course schedule and directory system. This project consists of four main scripts that work together to collect, process, and organize instructor data.

## 🎯 Project Overview

This project scrapes the Fall 2025 course schedule at UT Austin, extracts all instructor names, searches the UT directory for their contact information, and converts the results into a clean CSV format.
This project scrapes the Spring 2026 course schedule at UT Austin, extracts all instructor names, searches the UT directory for their contact information, and converts the results into a clean CSV format.

### Workflow Summary:
1. **Course Scraper**: Scrapes all courses (00000-99999) from UT's course schedule
2. **Directory Scraper**: Searches UT directory for each instructor's contact info
3. **Combiner** (optional): Combines multiple scraping runs
Results saved to Desktop as `UT_Spring2026_ScrapedInstructors.csv`

- **Python 3.8 or higher** (`python3 --version`)
- **Chrome browser** installed
- **UT Austin EID and password** (for authentication)
- **Duo authentication** access
```bash
python ut_directory_scraper.py --in UT_Spring2026_ScrapedInstructors.csv --out ut_directory_results.csv
```
### 1. Initial Setup
```bash
# Clone or download the project files
cd /path/to/project

Combines all `UT_Spring2026_ScrapedInstructors_Run*.csv` files
 Removes duplicates and sorts alphabetically
 Creates `UT_Spring2026_AllInstructors_Combined.csv`
# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

Combines all `UT_Spring2026_ScrapedInstructors_Run*.csv` files
 Removes duplicates and sorts alphabetically
 Creates `UT_Spring2026_AllInstructors_Combined.csv`

### 2. Run the Complete Workflow

#### Step 1: Scrape Course Instructors
`UT_Spring2026_ScrapedInstructors.csv` - Main output file
`UT_Spring2026_ScrapedInstructors_Run*.csv` - Individual run files (if using unique mode)
```
- Follow the prompts to authenticate with UT Direct
#### Step 2: Search UT Directory
```bash
```
- Authenticate with UT Directory when browser opens
- Searches for each instructor's contact information
- Creates two files: confirmed matches and manual review cases
python vcf_to_csv.py all_people vcf_contacts.csv
```
### 3. Optional: Combine Multiple Runs
If you ran the course scraper multiple times with different ranges:
```bash
python combine_instructors.py
- Creates `UT_Fall2025_AllInstructors_Combined.csv`


1. **Setup Environment**
   pip install -r requirements.txt
   ```

2. **Scrape Course Instructors** (2-4 hours)
   ```bash
   python ut_instructor_scraper_simple.py
   # Authenticate with UT Direct when prompted
   # Choose range 0-100000 (default)
   # Results: UT_Fall2025_ScrapedInstructors.csv on Desktop
   ```

3. **Search UT Directory** (1-2 hours)
   ```bash
   python ut_directory_scraper.py --in UT_Fall2025_ScrapedInstructors.csv --out ut_directory_results.csv
   # Authenticate with UT Directory when prompted
   # Results: ut_directory_results.csv + manual review file
   ```

4. **Convert vCard Files** (if applicable)
   ```bash
   python vcf_to_csv.py all_people vcf_contacts.csv
   # Results: vcf_contacts.csv with clean contact data
   ```

## 📁 Script Details

### 1. `ut_instructor_scraper_simple.py`
**Purpose**: Scrapes instructor names from UT's course schedule

**Features**:
- Scrapes courses from 00000 to 99999 (configurable range)
- Handles authentication with UT Direct
- Saves progress every 1000 courses
- Supports multiple run modes (append, unique files, overwrite)
- Robust error handling and retry logic

**Output**: CSV with `FirstName` and `LastName` columns

**Usage**:
```bash
python ut_instructor_scraper_simple.py
```

### 2. `ut_directory_scraper.py`
**Purpose**: Searches UT directory for instructor contact information

**Features**:
- Accepts CSV input with instructor names
- Auto-detects column names (FirstName, LastName, etc.)
- Searches multiple name variants for better matches
- Downloads vCard files for confirmed matches
- Creates separate files for confirmed vs. manual review cases

**Output**: 
- `ut_directory_results.csv` - Confirmed matches
- `ut_directory_results_manual_review.csv` - Cases needing review

**Usage**:
```bash
# Basic usage (auto-detects columns)
python ut_directory_scraper.py --in UT_Fall2025_ScrapedInstructors.csv --out ut_directory_results.csv

# Specify column names
python ut_directory_scraper.py --in input.csv --first-col FirstName --last-col LastName --out results.csv

# Single column with full names
python ut_directory_scraper.py --in input.csv --single-col Instructor --out results.csv
```

### 3. `combine_instructors.py`
**Purpose**: Combines multiple instructor CSV files from different scraping runs

**Features**:
- Automatically finds files matching pattern `UT_Fall2025_ScrapedInstructors_Run*.csv`
- Removes duplicate instructors
- Sorts by last name, then first name
- Provides statistics on the combination process

**Output**: `UT_Fall2025_AllInstructors_Combined.csv`

**Usage**:
```bash
python combine_instructors.py
```

### 4. `vcf_to_csv.py`
**Purpose**: Converts downloaded vCard (.vcf) files to CSV format

**Features**:
- Processes all .vcf files in a specified folder
- Extracts first name, last name, and email
- Skips entries without email addresses
- Sorts results alphabetically

**Output**: CSV with `First Name`, `Last Name`, and `Email` columns

**Usage**:
```bash
# Use default folder 'all_people'
python vcf_to_csv.py

# Specify folder and output file
python vcf_to_csv.py /path/to/vcf/folder output_contacts.csv
```

## 🔧 Configuration Options

### Course Scraper Options
- **Scraping Range**: Customize start/end course numbers
- **File Handling**: Choose between append, unique files, or overwrite
- **Debug Mode**: Enable detailed logging for troubleshooting

### Directory Scraper Options
- **Column Detection**: Auto-detects common column names or specify manually
- **Name Variants**: Automatically tries different name formats
- **Output Format**: Separate files for confirmed vs. manual review cases

## 📊 Output Files

### Course Scraper Output
- `UT_Fall2025_ScrapedInstructors.csv` - Main output file
- `UT_Fall2025_ScrapedInstructors_Run*.csv` - Individual run files (if using unique mode)

### Directory Scraper Output
- `ut_directory_results.csv` - Confirmed directory matches
- `ut_directory_results_manual_review.csv` - Cases requiring manual review
- `all_people/` folder - Downloaded vCard files (if enabled)

### VCF Converter Output
- `vcf_contacts.csv` - Converted contact information

## 🛠️ Troubleshooting

### Common Issues

**Authentication Problems**
- Ensure you complete Duo authentication
- Try running with visible browser mode first
- Check that your UT credentials work in regular browser

**Chrome Driver Issues**
- Script automatically downloads correct Chrome driver
- Ensure Chrome browser is installed and up to date

**File Permission Errors**
- Make sure virtual environment is activated
- Check that you have write permissions in the directory

**No Results Found**
- Verify the input CSV format matches expected columns
- Check that the scraping range includes valid course numbers
- Ensure you're properly authenticated with UT systems

### Performance Tips
- Use headless mode for faster execution after initial setup
- The course scraper saves progress every 1000 courses
- You can interrupt and restart from where you left off
- For large datasets, consider running in smaller batches

## 🔒 Security & Privacy

- Scripts only access public course information
- Login credentials are not stored
- Uses existing browser sessions for authentication
- No data is sent to external servers
- All processing happens locally on your machine

## 📈 Expected Results

### Course Scraper
- **Input**: Course numbers 00000-99999
- **Output**: ~1000-2000 unique instructor names
- **Time**: 2-4 hours for full range

### Directory Scraper
- **Input**: Instructor names from course scraper
- **Output**: Contact information for ~60-80% of instructors
- **Time**: 1-2 hours depending on number of instructors

### VCF Converter
- **Input**: Downloaded vCard files
- **Output**: Clean CSV with contact information
- **Time**: Seconds to minutes depending on file count

## 🤝 Support

If you encounter issues:
1. Check that all prerequisites are installed
2. Verify your UT credentials work in a regular browser
3. Try running with visible browser mode first
4. Ensure you have a stable internet connection
5. Check the troubleshooting section above

The scripts are designed to be robust and will continue even if some individual requests fail.

