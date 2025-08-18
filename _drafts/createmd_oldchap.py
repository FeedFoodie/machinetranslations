from datetime import datetime, timedelta

def create_markdown_files_cli():
    """
    Generates markdown files with YAML front matter based on command-line input.
    """
    # --- Series Configuration ---
    # Maps lowercase abbreviation to the capitalization needed for filenames/layouts
    SERIES_CONFIG = {
        'qow': 'QOW',
        'asbw': 'ABSR',
        # Add other series here as needed
    }

    # --- Get User Input from Command Line ---
    try:
        # Ask for the series
        series_abbr = input("Enter the series abbreviation (e.g., qow, absr): ").strip().lower()
        if series_abbr not in SERIES_CONFIG:
            print(f"\n[Error] Invalid series abbreviation. Please use one of: {', '.join(SERIES_CONFIG.keys())}")
            return

        # Ask for the date
        date_str = input("Enter the date (YYYY-MM-DD): ").strip()
        # Validate date format to prevent errors later
        datetime.strptime(date_str, "%Y-%m-%d")

        # Ask for the range of numbers for the filenames
        start_num_str = input("Enter the starting number (e.g., 401): ").strip()
        end_num_str = input("Enter the ending number (e.g., 403): ").strip()

        # Ask for the starting time
        time_str = input("Enter the starting time (HH:MM): ").strip()

        # --- Validate and Parse Inputs ---
        start_num = int(start_num_str)
        end_num = int(end_num_str)

        if start_num > end_num:
            print("\n[Error] Starting number cannot be greater than the ending number.")
            return

        # Combine the user-provided date and time
        start_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

    except ValueError:
        print("\n[Error] Invalid input. Please enter a valid date (YYYY-MM-DD), numbers, and time (HH:MM).")
        return

    # --- Generate Files ---
    print("\n--- Generating Files ---")
    files_created_count = 0
    current_time = start_time
    
    # Get the correct capitalization for the filename from the config
    filename_series_prefix = SERIES_CONFIG[series_abbr]

    for i in range(start_num, end_num + 1):
        # Format the number with leading zeros to be 3 digits (e.g., 1 -> "001")
        number_str = f"{i:03d}"
        
        # Format the filename, e.g., 2025-08-07-QOW401.md
        filename = f"{date_str}-{filename_series_prefix}{number_str}.md"
        
        # Format the date for the YAML content, including timezone
        yaml_date = current_time.strftime("%Y-%m-%d %H:%M:%S +0800")

        # Create the YAML content dynamically based on the series abbreviation
        yaml_content = f"""---
layout: post{filename_series_prefix}
title: ""
comments: true
tags: [{series_abbr}]
categories: [{series_abbr}]
date: {yaml_date}
---
"""
        
        # Write the content to the file
        try:
            with open(filename, "w") as f:
                f.write(yaml_content)
            print(f"Successfully created: {filename}")
            files_created_count += 1
        except IOError as e:
            print(f"[File Error] Could not write to file {filename}: {e}")
            break # Stop if a file can't be created

        # Increment the time by one minute for the next file
        current_time += timedelta(minutes=1)

    print(f"\n--- Done. Created {files_created_count} file(s). ---")

if __name__ == "__main__":
    create_markdown_files_cli()