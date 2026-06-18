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
# ntfy.sh Topic
NTFY_TOPIC = os.environ.get('NTFY_TOPIC')
# Telegram bot configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TG_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TGID_NORTHBLADETL')

# Series title mapping
SERIES_TITLES = {
    'absr': 'Absolute Regression',
    'amkhi': 'Assistant Manager Kim Hates Idols',
}

# Series role mapping for Discord mentions
SERIES_ROLES = {
    'absr': '1408104314366328873',
    'amkhi': '1509028385215746178',
}

def send_ntfy_notification(tag, chapter_num, chapter_id):
    """
    Send a push notification via ntfy.sh.
    """
    if not NTFY_TOPIC:
        print("⚠️  ntfy topic not configured. Skipping ntfy notification.")
        return

    series_name = SERIES_TITLES.get(tag.lower(), tag.upper())
    title = f"{tag.upper()} Chapter {chapter_num}"
    message = f"{series_name} Chapter {chapter_num} has been posted!"
    url = f"https://mtl.northbladetl.com/{tag.lower()}/{chapter_id}.html"

    try:
        response = requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode('utf-8'),
            headers={
                "Title": title,
                "Priority": "default",          # can be 'high', 'urgent', etc.
                "Tags": "loudspeaker,page_facing_up",
                "Click": url,                  # opens the chapter when tapped
                "Attach": "https://i.imgur.com/U5CiyoG.png"  # optional icon
            },
            timeout=10
        )

        if response.status_code == 200:
            print(f"✅ ntfy notification sent: {title}")
        else:
            print(f"⚠️  ntfy returned status {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send ntfy notification: {e}")
    except Exception as e:
        print(f"❌ Error in ntfy notification: {e}")

from pingram import Pingram

def send_telegram_notification(tag, chapter_num, chapter_id):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram credentials missing. Skipping Telegram notification.")
        return
    
    series_name = SERIES_TITLES.get(tag.lower(), tag.upper())
    title = f"{tag.upper()} Chapter {chapter_num}"
    url = f"https://mtl.northbladetl.com/{tag.lower()}/{chapter_id}.html"
    
    # Format: Clean, readable message
    message = f"{series_name} Chapter {chapter_num} has been posted!\n{url}"
    
    try:
        bot = Pingram(token=TELEGRAM_BOT_TOKEN)
        response = bot.message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        
        # Pingram returns response object; check status
        if response.status_code == 200:
            print(f"✅ Telegram notification sent: {title}")
        else:
            print(f"⚠️  Telegram returned status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Failed to send Telegram notification: {e}")

def send_discord_notification(tag, chapter_num, chapter_id):
    if DISCORD_WEBHOOK_URL:
        role_id = SERIES_ROLES.get(tag.lower())
        role_mention = f"<@&{role_id}>"
        message = f"{role_mention} {tag.upper()} Chapter {chapter_num} - https://mtl.northbladetl.com/{tag.lower()}/{chapter_id}.html"
        
        try:
            payload = {
                "content": message,
                "username": "Foodie_Bot",
                "avatar_url": "https://files.catbox.moe/h4z8gt.png"
            }
            response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            if response.status_code == 204:
                print(f"✅ Discord notification sent: {message}")
            else:
                print(f"⚠️  Discord webhook returned status {response.status_code}")
        except Exception as e:
            print(f"❌ Discord notification error: {e}")
    else:
        print("⚠️  Discord webhook not configured – skipping.")    

def send_notifications(tag, chapter_num, chapter_id):
    def send_after_delay():
        print(f"⏳ Notifications scheduled for {tag} Chapter {chapter_num}...")
        time.sleep(180)
        
        send_discord_notification(tag, chapter_num, chapter_id)
        send_ntfy_notification(tag, chapter_num, chapter_id)
        send_telegram_notification(tag, chapter_num, chapter_id)
    
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
        
        result = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True)
        current_branch = result.stdout.strip()
        
        if current_branch != branch:
            print(f"  Switching from '{current_branch}' to '{branch}'...")
            subprocess.run(['git', 'checkout', branch], check=True, stdin=subprocess.DEVNULL)
        
        subprocess.run(['git', 'add', '.'], check=True, stdin=subprocess.DEVNULL)
        
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        changed_files = [line for line in result.stdout.split('\n') if line.strip()]
        file_count = len(changed_files)
        file_word = "file" if file_count == 1 else "files"
        
        commit_message = f"Update: {file_count} {file_word}"
        subprocess.run(['git', 'commit', '-m', commit_message], check=True, stdin=subprocess.DEVNULL)
        
        # -c gc.auto=0 prevents git from running garbage collection during push
        subprocess.run(['git', '-c', 'gc.auto=0', 'push', 'origin', branch], check=True, stdin=subprocess.DEVNULL)
        
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
            
            # Schedule notifications
            print("\n--- SCHEDULING NOTIFICATIONS ---")
            notification_threads = []
            for chapter_info in processed_chapters:
                thread = send_notifications(
                    chapter_info['tag'],
                    chapter_info['chapter_num'],
                    chapter_info['chapter_id']
                )
                notification_threads.append(thread)
            print(f"✓ Scheduled {len(processed_chapters)} notification(s) for 3 minutes from now")

            try:
                # Wait for all notification threads to complete
                for thread in notification_threads:
                    thread.join(timeout=200)
                
                print("✅ All notifications sent successfully!")
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