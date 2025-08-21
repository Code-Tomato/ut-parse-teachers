import pandas as pd
import os
import glob

def combine_instructor_files():
    """Combine all instructor CSV files and sort them"""
    print("🔗 Combining all instructor CSV files...")
    
    # Find all CSV files in the current directory
    csv_files = glob.glob("UT_Fall2025_ScrapedInstructors_Run*.csv")
    
    if not csv_files:
        print("❌ No instructor CSV files found!")
        return
    
    print(f"📁 Found {len(csv_files)} CSV files:")
    for file in sorted(csv_files):
        print(f"   - {file}")
    
    # Read and combine all files
    all_dataframes = []
    total_instructors = 0
    
    for file in sorted(csv_files):
        try:
            df = pd.read_csv(file)
            print(f"📊 {file}: {len(df)} instructors")
            all_dataframes.append(df)
            total_instructors += len(df)
        except Exception as e:
            print(f"⚠️  Error reading {file}: {e}")
    
    if not all_dataframes:
        print("❌ No valid CSV files could be read!")
        return
    
    # Combine all dataframes
    print(f"\n🔗 Combining {len(all_dataframes)} files...")
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    
    print(f"📊 Before deduplication: {len(combined_df)} total instructors")
    
    # Remove duplicates
    original_count = len(combined_df)
    combined_df = combined_df.drop_duplicates(subset=['FirstName', 'LastName'])
    final_count = len(combined_df)
    duplicates_removed = original_count - final_count
    
    print(f"🧹 Removed {duplicates_removed} duplicate instructors")
    print(f"📊 After deduplication: {final_count} unique instructors")
    
    # Sort by LastName, then FirstName
    print("📝 Sorting by LastName, then FirstName...")
    combined_df = combined_df.sort_values(['LastName', 'FirstName']).reset_index(drop=True)
    
    # Save the combined file
    output_file = "UT_Fall2025_AllInstructors_Combined.csv"
    combined_df.to_csv(output_file, index=False)
    
    print(f"\n✅ Successfully combined all files!")
    print(f"💾 Saved to: {output_file}")
    print(f"📊 Final result: {final_count} unique instructors")
    
    # Show some statistics
    print(f"\n📈 Statistics:")
    print(f"   - Total files processed: {len(csv_files)}")
    print(f"   - Total instructors before deduplication: {total_instructors}")
    print(f"   - Duplicates removed: {duplicates_removed}")
    print(f"   - Final unique instructors: {final_count}")
    
    # Show first few entries
    print(f"\n📋 First 10 instructors:")
    for i, row in combined_df.head(10).iterrows():
        if pd.isna(row['LastName']) or row['LastName'] == '':
            print(f"   {i+1:3d}. {row['FirstName']}")
        else:
            print(f"   {i+1:3d}. {row['FirstName']} {row['LastName']}")
    
    if len(combined_df) > 10:
        print(f"   ... and {len(combined_df) - 10} more")
    
    return combined_df

if __name__ == "__main__":
    combine_instructor_files()
