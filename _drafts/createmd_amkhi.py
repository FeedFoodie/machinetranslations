from datetime import datetime, timezone, timedelta

def create_markdown_files_cli():
    """
    Generates a single markdown file with YAML front matter based on command-line input.
    """
    # --- Get Current Date & Time in GMT+8 ---
    tz_gmt8 = timezone(timedelta(hours=8))
    now = datetime.now(tz_gmt8)
    date_str = now.strftime("%Y-%m-%d")

    # --- Get User Input from Command Line ---
    try:
        chapter_num = int(input("Enter the chapter number (e.g., 401): ").strip())
    except ValueError:
        print("\n[Error] Invalid input. Please enter a valid number.")
        return

    # --- Generate Single File ---
    print("\n--- Generating File ---")

    filename = f"{date_str}-AMKHI{chapter_num}.md"
    yaml_date = now.strftime("%Y-%m-%d %H:%M:%S +0800")

    yaml_content = f"""---
layout: post
title: ""
comments: true
tags: [amkhi]
categories: [amkhi]
date: {yaml_date}
---
"""

    try:
        with open(filename, "w") as f:
            f.write(yaml_content)
        print(f"Successfully created: {filename}")
        print("\n--- Done. Created 1 file. ---")
    except IOError as e:
        print(f"[File Error] Could not write to file {filename}: {e}")

if __name__ == "__main__":
    create_markdown_files_cli()