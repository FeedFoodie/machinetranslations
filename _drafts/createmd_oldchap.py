from datetime import datetime, timedelta

def create_markdown_files_cli():
    """
    Generates markdown files with YAML front matter based on command-line input.
    """
    # --- Get Today's Date ---
    today = datetime.now()
    #date_str = today.strftime("%Y-%m-%d")
    date_str = "2025-08-09"

    # --- Get User Input from Command Line ---
    try:
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

        # Combine today's date with the user-provided time
        start_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

    except ValueError:
        print("\n[Error] Invalid input. Please enter valid numbers and a time in HH:MM format.")
        return

    # --- Generate Files ---
    print("\n--- Generating Files ---")
    files_created_count = 0
    current_time = start_time
    for i in range(start_num, end_num + 1):
        # Format the filename, e.g., 2025-08-09-ABSR401.md
        filename = f"{date_str}-ABSR{i}.md"
        
        # Format the date for the YAML content, including timezone
        yaml_date = current_time.strftime("%Y-%m-%d %H:%M:%S +0800")

        # Create the YAML content
        yaml_content = f"""---
layout: postABSR
title: ""
comments: true
tags: [absr]
categories: [absr]
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