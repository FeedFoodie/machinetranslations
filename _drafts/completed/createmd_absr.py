from datetime import datetime

def create_markdown_files_cli():
    """
    Generates a single markdown file with YAML front matter based on command-line input.
    """
    # --- Get Today's Date ---
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")

    # --- Get User Input from Command Line ---
    try:
        # Ask for the single number for the filename
        chapter_num = input("Enter the chapter number (e.g., 401): ").strip()

        # Ask for the time
        time_str = input("Enter the time (HH:MM): ").strip()

        # --- Validate and Parse Inputs ---
        chapter_num = int(chapter_num)

        # Combine today's date with the user-provided time
        chapter_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

    except ValueError:
        print("\n[Error] Invalid input. Please enter a valid number and time in HH:MM format.")
        return

    # --- Generate Single File ---
    print("\n--- Generating File ---")
    
    # Format the filename, e.g., 2025-08-09-ABSR401.md
    filename = f"{date_str}-ABSR{chapter_num}.md"
    
    # Format the date for the YAML content, including timezone
    yaml_date = chapter_time.strftime("%Y-%m-%d %H:%M:%S +0800")

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
        print("\n--- Done. Created 1 file. ---")
    except IOError as e:
        print(f"[File Error] Could not write to file {filename}: {e}")

if __name__ == "__main__":
    create_markdown_files_cli()