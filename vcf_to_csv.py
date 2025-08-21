#!/usr/bin/env python3
# vcf_to_csv.py
# Converts .vcf contact files to CSV format
# Extracts full names and emails, skips entries without emails

import os
import re
import pandas as pd
from pathlib import Path

def parse_vcf_file(file_path):
    """Parse a single .vcf file and extract name and email"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract full name (FN field)
        name_match = re.search(r'FN:(.+)', content, re.MULTILINE)
        full_name = name_match.group(1).strip() if name_match else ""
        
        # Extract email (EMAIL field)
        email_match = re.search(r'EMAIL[^:]*:(.+)', content, re.MULTILINE | re.IGNORECASE)
        email = email_match.group(1).strip() if email_match else ""
        
        # Split name into first and last
        if full_name:
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                last_name = name_parts[-1]  # Rightmost name is last name
                first_name = " ".join(name_parts[:-1])  # Everything else is first name
            else:
                first_name = full_name
                last_name = ""
        else:
            first_name = ""
            last_name = ""
        
        return first_name, last_name, email
        
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return "", ""

def process_vcf_folder(folder_path, output_file="vcf_contacts.csv"):
    """Process all .vcf files in a folder and create CSV output"""
    
    folder = Path(folder_path)
    if not folder.exists():
        print(f"Folder {folder_path} does not exist!")
        return
    
    # Find all .vcf files
    vcf_files = list(folder.glob("*.vcf"))
    print(f"Found {len(vcf_files)} .vcf files in {folder_path}")
    
    if not vcf_files:
        print("No .vcf files found!")
        return
    
    # Process each file
    contacts = []
    skipped_count = 0
    
    for vcf_file in vcf_files:
        print(f"Processing: {vcf_file.name}")
        first_name, last_name, email = parse_vcf_file(vcf_file)
        
        if email:  # Only include if email exists
            contacts.append({
                "First Name": first_name,
                "Last Name": last_name,
                "Email": email
            })
        else:
            skipped_count += 1
            print(f"  Skipped {vcf_file.name} - no email found")
    
    if not contacts:
        print("No contacts with emails found!")
        return
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(contacts)
    
    # Sort by last name, then first name
    df = df.sort_values(["Last Name", "First Name"])
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    
    print(f"\n✅ Successfully processed {len(contacts)} contacts with emails")
    print(f"❌ Skipped {skipped_count} contacts without emails")
    print(f"📊 Output saved to: {output_file}")
    
    # Show some stats
    print(f"\n📈 Summary:")
    print(f"  - Total .vcf files: {len(vcf_files)}")
    print(f"  - Contacts with emails: {len(contacts)}")
    print(f"  - Contacts without emails: {skipped_count}")
    print(f"  - Success rate: {len(contacts)/(len(contacts)+skipped_count)*100:.1f}%")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        folder_path = "all_people"  # Default folder name
    
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = "vcf_contacts.csv"  # Default output file
    
    print(f"🔍 Processing .vcf files from: {folder_path}")
    print(f"📄 Output will be saved to: {output_file}")
    print("-" * 50)
    
    process_vcf_folder(folder_path, output_file)
