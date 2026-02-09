import os
import shutil
import tkinter as tk
from tkinter import filedialog
import subprocess
import requests
import time
import threading
import re

# Discord webhook URL
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

# Series role mapping for Discord mentions
SERIES_ROLES = {
    'absr': '1408104314366328873',
}

def send_discord_notification_async(tag, chapter_num, chapter_id):
    """
    Schedule a Discord notification to be sent after 5 minutes.
    This runs in a separate thread to avoid blocking the main script.
    """
    def send_after_delay():
        print(f"⏳ Discord notification scheduled for {tag} Chapter {chapter_num} in 3 min...")
        time.sleep(180)
        
        if not DISCORD_WEBHOOK_URL or "YOUR_WEBHOOK" in DISCORD_WEBHOOK_URL:
            print("⚠️  Discord webhook URL not configured. Skipping notification.")
            return
            
        role_id = SERIES_ROLES.get(tag.lower())
        role_mention = f"<@&{role_id}>"            
        message = f"{role_mention} {tag.upper()} Chapter {chapter_num} - https://mtl.northbladetl.com/{tag.lower()}/{chapter_id}.html"
        
        try:
            # Create the webhook payload
            payload = {
                "content": message,
                "username": "Foodie_Bot",
                "avatar_url": "https://i.imgur.com/U5CiyoG.png"
            }
            
            response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            
            if response.status_code == 204:
                print(f"✅ Discord notification sent: {message}")
            else:
                print(f"⚠️  Discord webhook returned status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to send Discord notification: {e}")
        except Exception as e:
            print(f"❌ Error in Discord notification: {e}")
    
    # Start the delayed notification in a separate thread
    notification_thread = threading.Thread(target=send_after_delay)
    notification_thread.start()
    return notification_thread

def git_push(repo_path, branch='main'):
    """Push changes to GitHub repository with specified branch"""
    try:
        original_dir = os.getcwd()
        os.chdir(repo_path)
        
        print(f"\nPushing changes to {os.path.basename(repo_path)} (branch: {branch})...")
        
        # Switch to the correct branch
        result = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True)
        current_branch = result.stdout.strip()
        
        if current_branch != branch:
            print(f"  Switching from '{current_branch}' to '{branch}'...")
            subprocess.run(['git', 'checkout', branch], check=True)
        
        # Git commands
        subprocess.run(['git', 'add', '.'], check=True)
        
        # Get number of files changed for commit message
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        changed_files = [line for line in result.stdout.split('\n') if line.strip()]
        file_count = len(changed_files)
        file_word = "file" if file_count == 1 else "files"
        
        commit_message = f"Update: {file_count} {file_word}"
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        subprocess.run(['git', 'push', 'origin', branch], check=True)
        
        print(f"✓ Successfully pushed to {os.path.basename(repo_path)} ({branch})")
        
        os.chdir(original_dir)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Git error for {os.path.basename(repo_path)}: {e}")
        os.chdir(original_dir)
        return False
    except Exception as e:
        print(f"✗ Error pushing to {os.path.basename(repo_path)}: {e}")
        os.chdir(original_dir)
        return False

def process_markdown_files():
    # Base directory - only public repo
    public_repo_dir = r'C:\Users\rebec\Documents\GitHub\machinetranslations'
    
    # Ensure public repo directory exists
    if not os.path.exists(public_repo_dir):
        print(f"✗ Public repository directory not found: {public_repo_dir}")
        return
    
    posts_dest_dir = os.path.join(public_repo_dir, '_posts')
    os.makedirs(posts_dest_dir, exist_ok=True)
    
    # Setup file dialog
    root = tk.Tk()
    root.withdraw()
    
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    file_paths = filedialog.askopenfilenames(
        title="Select Markdown file(s) to publish",
        initialdir=script_dir,  # Start in the script's directory
        filetypes=(("Markdown files", "*.md"), ("All files", "*.*"))
    )
    
    if not file_paths:
        return
        
    processed_count = 0
    
    # Track processed files for Discord notifications
    processed_chapters = []
    
    for file_path in file_paths:
        filename = os.path.basename(file_path)
        try:
            # Extract tag and chapter info from filename
            # Format: 2025-12-26-SIMB477.md
            chapter_match = re.search(r'\d{4}-\d{2}-\d{2}-(.+?)\.md$', filename)
            if chapter_match:
                chapter_id = chapter_match.group(1)  # e.g., SIMB477
                
                # Extract tag (first part before numbers)
                tag_match = re.match(r'([A-Za-z]+)', chapter_id)
                if tag_match:
                    tag = tag_match.group(1).upper()
                else:
                    tag = "UNKNOWN"
                
                # Extract chapter number
                chapter_num_match = re.search(r'(\d+)$', chapter_id)
                chapter_num = int(chapter_num_match.group(1)) if chapter_num_match else 0
                
                # Store for Discord notification
                processed_chapters.append({
                    'tag': tag,
                    'chapter_id': chapter_id,
                    'chapter_num': chapter_num,
                    'filename': filename
                })
            else:
                print(f"  ⚠️  Could not extract chapter info from {filename}")
                tag = "UNKNOWN"
                chapter_id = ""
                chapter_num = 0

            # Copy the file to _posts folder without any changes
            dest_path = os.path.join(posts_dest_dir, filename)
            shutil.copy2(file_path, dest_path)
            
            # Remove the original file (cut and paste)
            os.remove(file_path)
            
            print(f"✓ Processed {filename}:")
            print(f"  - Moved to: {dest_path}")
            print(f"  - Tag: {tag}, Chapter: {chapter_num}")
            
            processed_count += 1
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    if processed_count > 0:
        print(f"\n✓ Successfully moved {processed_count} file(s) to _posts folder")
        
        # Push to GitHub
        print(f"\nPushing to repository: {os.path.basename(public_repo_dir)}")
        if git_push(public_repo_dir, 'gh-pages'):
            print("✓ Repository updated successfully")
            
            # Schedule Discord notifications
            print("\n--- SCHEDULING DISCORD NOTIFICATIONS ---")
            notification_threads = []
            for chapter_info in processed_chapters:
                thread = send_discord_notification_async(
                    chapter_info['tag'],
                    chapter_info['chapter_num'],
                    chapter_info['chapter_id']
                )
                notification_threads.append(thread)
            print(f"✓ Scheduled {len(processed_chapters)} Discord notification(s) for 3 minutes from now")
            
            if not DISCORD_WEBHOOK_URL or "YOUR_WEBHOOK" in DISCORD_WEBHOOK_URL:
                print("\n⚠️  IMPORTANT: Discord webhook not configured!")
                print("   To enable Discord notifications:")
                print("   1. Create a webhook in your Discord server")
                print("   2. Replace the DISCORD_WEBHOOK_URL variable at the top of this script")
            
            # Keep the main thread alive to let notifications finish
            print("\n⏳ Waiting for Discord notifications to be sent (approx. 3 minutes)...")
            print("   You can close the window with Ctrl+C if you want to exit early.")
            
            try:
                # Wait for all notification threads to complete
                for thread in notification_threads:
                    thread.join(timeout=190)  # 2 minutes + 10 seconds buffer
                
                print("✅ All Discord notifications sent successfully!")
            except KeyboardInterrupt:
                print("\n⚠️  Script interrupted. Some notifications may not be sent.")
            except Exception as e:
                print(f"⚠️  Error waiting for notifications: {e}")
        else:
            print("✗ Failed to push to repository")
    else:
        print("✗ No files were processed.")

if __name__ == "__main__":
    process_markdown_files()