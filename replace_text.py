import os
import re

# List of all directories you want to process
directories_to_process = [f'_posts/']

# A dictionary for all the static text replacements
replacements = {
    "“": "\"",
    "”": "\"",
    "’": "'",
    "‘": "'",
    "…": "...",
    "saber": "dao",
    " nyang": " taels",
    "Jingyeok": "Blitz",
    "Yeong Hwain": "Yeom Hwain",
    "bodyguard martial artist": "bodyguard",
    "temporary Cult Leader": "Acting Cult Leader",
    "Mister": "Uncle",
    "Young Chief": "Young Sect Leader",
    "freelancers": "mercenaries",
    "freelancer": "mercenary",
    "My father": "Father",
    "his Master": "his master",
    "Blade Demon clan": "Blade Demon Sect",
    "Demonic Esssence Pill": "Demonic Essence Pill",
    "Cheonoeshindan": "Azure Jade Divine Pill",
    "Cheonwoeshindan": "Azure Jade Divine Pill",
    "Ma-hyeop": "demonic hero",
    "Cheonhamaeng": "World Alliance",
    "First Young Master": "First Young Lord",
    "Second Young Master": "Second Young Lord",
    "Saintess Palace Lady": "Saintess",
    "true energy": "inner qi",
    "complete mastery of the Twelfth Star": "Twelfth Star mastery",
    "The Blood Heaven Blade Demon Elder": "Elder Blood Heaven Blade Demon",
    "the Blood Heaven Blade Demon Elder": "Elder Blood Heaven Blade Demon",
    "The Blade Demon Elder": "Elder Blade Demon",
    "the Blade Demon Elder": "Elder Blade Demon",
    "Alliance Leader": "Alliance Chairman",
    "demonic blood": "paralysis acupoint",
    "Wind Heavenly": "Heavenly Wind",
    "* * *": "{sep}",
    "***": "{sep}"
}

# Loop through each directory in the list
for directory in directories_to_process:
    print(f"\n--- Processing directory: {directory} ---")
    try:
        # Use os.scandir() for a more efficient way to scan directories
        for entry in os.scandir(directory):
            # Process only files, ignore subdirectories
            if entry.is_file():
                try:
                    # Read the file content
                    with open(entry.path, "r", encoding="utf-8") as file:
                        text = file.read()

                    # Apply all other static replacements from the dictionary
                    for old, new in replacements.items():
                        text = text.replace(old, new)

                    # Write the modified content back to the same file
                    with open(entry.path, 'w', encoding='utf8') as file:
                        file.write(text)
                    
                    print(f"  ✓ Processed: {entry.name}")

                except Exception as e:
                    print(f"  ✗ Could not process file {entry.name}: {e}")

    except FileNotFoundError:
        print(f"  ✗ Error: Directory not found at '{directory}'")
    except Exception as e:
        print(f"  ✗ An unexpected error occurred while processing {directory}: {e}")

print("\n--- All processing complete. ---")