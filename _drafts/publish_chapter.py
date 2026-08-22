"""
Publish one or more MTL chapters to the Banana Translations site.

Adapted from cheptars/drafts/publish_chapter.py (the northbladetl.com version).

Each selected draft .md is split in two:
  * the YAML front matter  -> machinetranslations _posts/  (public repo, a stub)
  * the chapter body       -> cheptars/<TAG>/              (private repo)
The body is never published as HTML; the browser fetches it at runtime through
the Cloudflare Worker.  See _layouts/post.html and js/noscript.js.

Like the main site, this site has no paginator and no jekyll-feed: index.html
and feed.*.xml are static files that this script regenerates on every publish.
Building them from Liquid would mean iterating every stub post on every build,
and would put all ~900 ABSR chapters in the feed instead of the latest 10.
"""

import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog
import yaml
from datetime import datetime, date, timezone, timedelta
import subprocess
import requests
import json
import time
import threading
from pingram import Pingram

# -------------------------------------------------------------
# Configuration
# -------------------------------------------------------------
UTC8 = timezone(timedelta(hours=8))

REPO_OWNER = "feedfoodie"
REPO_NAME = "machinetranslations"

SITE_URL = "https://mtl.northbladetl.com"

# Local checkout of the public repo.
# NOTE: while machinetranslations2 is still the staging copy this points there.
#       After you replace machinetranslations with it, change this back to
#       ...\GitHub\machinetranslations
PUBLIC_REPO_DIR = r'C:\Users\rebec\Documents\GitHub\machinetranslations2'
PRIVATE_REPO_DIR = r'C:\Users\rebec\Documents\GitHub\cheptars'
BACKUP_DIR = r'C:\Users\rebec\Documents\GitHub\post_backup_mtl'

PUBLIC_BRANCH = 'gh-pages'
PRIVATE_BRANCH = 'main'

DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')
NTFY_TOPIC          = os.environ.get('NTFY_TOPIC')
TELEGRAM_BOT_TOKEN  = os.environ.get('TG_BOT_TOKEN')
TELEGRAM_CHAT_ID    = os.environ.get('TGID_NORTHBLADETL')

SERIES_TITLES = {
    'absr':  'Absolute Regression',
    'amkhi': 'Assistant Manager Kim Hates Idols',
}

# Discord role to ping per series. Leave a tag out (or set it to '') and the
# announcement still goes out, just without an @role mention.
SERIES_ROLES = {
    'absr':  '1408104314366328873',
    'amkhi': '1509028385215746178',
}

# Publishing schedule
FIRST_DELAY   = 180   # seconds after push before notifying (Jekyll build time)
BETWEEN_DELAY = 300   # seconds between each chapter's push (5 minutes)


# -------------------------------------------------------------
# GitHub helpers
# -------------------------------------------------------------
def get_github_token():
    try:
        result = subprocess.run(
            ['gh', 'auth', 'token'],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"x Failed to get token from gh: {e}")
        print("   Run 'gh auth login' first or set GITHUB_TOKEN environment variable.")
        return None


GITHUB_TOKEN = get_github_token()
if not GITHUB_TOKEN:
    print("Cannot proceed without authentication.")


def trigger_github_workflow():
    try:
        print("  Triggering workflow with gh CLI...")
        result = subprocess.run(
            ['gh', 'workflow', 'run', 'jekyll.yml', '--repo', f'{REPO_OWNER}/{REPO_NAME}'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("  OK GitHub workflow triggered!")
            return True
        print(f"  x gh CLI failed: {result.stderr.strip()}")
        print("  Falling back to API method...")
        return _trigger_github_workflow_api()
    except Exception as e:
        print(f"  x Error triggering workflow: {e}")
        return False


def _trigger_github_workflow_api():
    try:
        url = (f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
               "/actions/workflows/jekyll.yml/dispatches")
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }
        response = requests.post(
            url, headers=headers,
            json={"ref": "main", "inputs": {"skip_build": "false"}}
        )
        if response.status_code == 204:
            print("  OK GitHub workflow triggered via API!")
            return True
        print(f"  x API failed: {response.status_code} - {response.text}")
        return False
    except Exception as e:
        print(f"  x API error: {e}")
        return False


def git_push(repo_path, branch='main'):
    """Stage, commit, and push all changes in repo_path to branch."""
    original_dir = os.getcwd()
    try:
        os.chdir(repo_path)
        print(f"  Pushing {os.path.basename(repo_path)} -> {branch}...")

        result = subprocess.run(
            ['git', 'branch', '--show-current'], capture_output=True, text=True
        )
        if result.stdout.strip() != branch:
            subprocess.run(['git', 'checkout', branch], check=True)

        subprocess.run(['git', 'add', '.'], check=True)

        status = subprocess.run(
            ['git', 'status', '--porcelain'], capture_output=True, text=True
        )
        n = len([l for l in status.stdout.split('\n') if l.strip()])
        subprocess.run(
            ['git', 'commit', '-m', f"Update: {n} {'file' if n == 1 else 'files'}"],
            check=True
        )
        subprocess.run(['git', 'push', 'origin', branch], check=True)
        print(f"  OK Pushed {os.path.basename(repo_path)} ({branch})")
        return True

    except subprocess.CalledProcessError as e:
        print(f"  x Git error: {e}")
        return False
    except Exception as e:
        print(f"  x Push error: {e}")
        return False
    finally:
        os.chdir(original_dir)


# -------------------------------------------------------------
# Notification senders
# -------------------------------------------------------------
def send_discord_notification(tag, chapter_num, chapter_id):
    if not DISCORD_WEBHOOK_URL:
        print("  !  Discord webhook not configured - skipping.")
        return
    role_id = SERIES_ROLES.get(tag.lower())
    url = f"{SITE_URL}/{tag.lower()}/{chapter_id}.html"
    if role_id:
        mention = f"<@&{role_id}> "
    else:
        mention = ""
        print(f"  !  No Discord role ID for '{tag.lower()}' - posting without a ping.")
    message = f"{mention}{tag.upper()} Chapter {chapter_num} - {url}"
    try:
        resp = requests.post(
            DISCORD_WEBHOOK_URL,
            json={"content": message, "username": "Foodie_Bot",
                  "avatar_url": "https://files.catbox.moe/h4z8gt.png"},
            timeout=10
        )
        if resp.status_code == 204:
            print(f"  OK Discord: {tag.upper()} Ch.{chapter_num}")
        else:
            print(f"  !  Discord returned {resp.status_code}")
    except Exception as e:
        print(f"  x Discord error: {e}")


def send_ntfy_notification(tag, chapter_num, chapter_id):
    if not NTFY_TOPIC:
        print("  !  ntfy topic not configured - skipping.")
        return
    series_name = SERIES_TITLES.get(tag.lower(), tag.upper())
    url = f"{SITE_URL}/{tag.lower()}/{chapter_id}.html"
    try:
        resp = requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=f"{series_name} Chapter {chapter_num} has been posted!".encode('utf-8'),
            headers={
                "Title": f"{tag.upper()} Chapter {chapter_num}",
                "Priority": "default",
                "Tags": "loudspeaker,page_facing_up",
                "Click": url,
                "Attach": "https://i.imgur.com/U5CiyoG.png",
            },
            timeout=10
        )
        if resp.status_code == 200:
            print(f"  OK ntfy: {tag.upper()} Ch.{chapter_num}")
        else:
            print(f"  !  ntfy returned {resp.status_code}")
    except Exception as e:
        print(f"  x ntfy error: {e}")


def send_telegram_notification(tag, chapter_num, chapter_id):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  !  Telegram credentials missing - skipping.")
        return
    series_name = SERIES_TITLES.get(tag.lower(), tag.upper())
    url = f"{SITE_URL}/{tag.lower()}/{chapter_id}.html"
    message = f"{series_name} Chapter {chapter_num} has been posted!\n{url}"
    try:
        bot = Pingram(token=TELEGRAM_BOT_TOKEN)
        resp = bot.message(chat_id=TELEGRAM_CHAT_ID, text=message)
        if resp.status_code == 200:
            print(f"  OK Telegram: {tag.upper()} Ch.{chapter_num}")
        else:
            print(f"  !  Telegram returned {resp.status_code}")
    except Exception as e:
        print(f"  x Telegram error: {e}")


# -------------------------------------------------------------
# Text processing
# -------------------------------------------------------------
def replace_text(lines):
    replacements = {
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u2026": "...",
        "\\>":    ">",
    }
    lines = [_replace_in_line(line, replacements) for line in lines]
    return _join_blockquote_blanks(lines)


def _replace_in_line(line, replacements):
    for old, new in replacements.items():
        line = line.replace(old, new)
    return line


def _join_blockquote_blanks(lines):
    """Turn a blank line sitting between two blockquote paragraphs into a
    bare '>' line, per proper Markdown multiline blockquote syntax."""
    n = len(lines)
    for i in range(n):
        if lines[i].strip():
            continue
        prev_idx = i - 1
        while prev_idx >= 0 and not lines[prev_idx].strip():
            prev_idx -= 1
        next_idx = i + 1
        while next_idx < n and not lines[next_idx].strip():
            next_idx += 1
        if (prev_idx >= 0 and next_idx < n
                and lines[prev_idx].lstrip().startswith('>')
                and lines[next_idx].lstrip().startswith('>')):
            ending = ''
            if lines[i].endswith('\r\n'):
                ending = '\r\n'
            elif lines[i].endswith('\n'):
                ending = '\n'
            lines[i] = '>' + ending
    return lines


# -------------------------------------------------------------
# Date parsing
# -------------------------------------------------------------
def parse_date(date_value):
    """Return a timezone-aware datetime in UTC+8, from various input types."""
    if isinstance(date_value, datetime):
        return (date_value.replace(tzinfo=UTC8)
                if date_value.tzinfo is None
                else date_value.astimezone(UTC8))
    if isinstance(date_value, date):
        return datetime.combine(date_value, datetime.min.time()).replace(tzinfo=UTC8)
    if isinstance(date_value, str):
        for fmt in ('%Y-%m-%d %H:%M:%S %z', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
            try:
                parsed = datetime.strptime(date_value, fmt)
                return (parsed.replace(tzinfo=UTC8)
                        if parsed.tzinfo is None
                        else parsed.astimezone(UTC8))
            except ValueError:
                continue
    return None


# -------------------------------------------------------------
# TOC JSON updater
# -------------------------------------------------------------
def update_toc_json(public_repo_dir, filename, front_matter):
    """
    Append or update this chapter in _data/toc/<tag>.json.

    The TOC drives everything the stub post cannot know on its own: the chapter
    title and date in _layouts/post.html, the prev/next links, and the chapter
    dropdown. js/noscript.js then rebuilds the cheptars filename from the
    rendered <time datetime="..."> value, so the 'date' here MUST stay in sync
    with the date prefix of the file written into cheptars.
    """
    try:
        tags = front_matter.get('tags', [])
        if not tags:
            print(f"  !  No tags found for {filename}, skipping JSON update")
            return False

        tag = tags[0].lower().strip()
        chapter_match = re.search(r'\d{4}-\d{2}-\d{2}-(.+?)\.md$', filename)
        if not chapter_match:
            print(f"  !  Could not extract chapter ID from {filename}")
            return False

        chapter_id = chapter_match.group(1)
        m = re.search(r'(\d+)$', chapter_id)
        chapter_num = int(m.group(1)) if m else 0
        title = front_matter.get('title', chapter_id)
        date_str = str(front_matter.get('date', ''))

        json_path = os.path.join(public_repo_dir, '_data', 'toc', f'{tag}.json')

        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                try:
                    posts = json.load(f)
                except json.JSONDecodeError:
                    print(f"  !  Error reading {json_path}, starting fresh")
                    posts = []
        else:
            print(f"  !  JSON not found at {json_path}, creating new")
            posts = []

        existing = [i for i, p in enumerate(posts) if p.get('chapter_id') == chapter_id]

        if existing:
            idx = existing[0]
            posts[idx].update({
                'title':    title,
                'date':     date_str,
                'filename': filename,
                'url':      f"/{tag}/{chapter_id}.html",
            })
            if idx > 0:
                posts[idx - 1]['next_url'] = posts[idx]['url']
                posts[idx - 1]['next_title'] = title
            if idx < len(posts) - 1:
                posts[idx + 1]['prev_url'] = posts[idx]['url']
                posts[idx + 1]['prev_title'] = title
        else:
            new_post = {
                'title':       title,
                'chapter_id':  chapter_id,
                'chapter_num': chapter_num,
                'date':        date_str,
                'filename':    filename,
                'url':         f"/{tag}/{chapter_id}.html",
                'prev_url':    None,
                'prev_title':  None,
                'next_url':    None,
                'next_title':  None,
            }
            posts.append(new_post)
            if len(posts) > 1:
                prev = posts[-2]
                prev['next_url'] = new_post['url']
                prev['next_title'] = title
                new_post['prev_url'] = prev['url']
                new_post['prev_title'] = prev['title']

        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)

        print(f"  OK {tag}.json updated with {chapter_id}")
        return True

    except Exception as e:
        print(f"  x Error updating JSON for {filename}: {e}")
        return False


# -------------------------------------------------------------
# Index page generator
# -------------------------------------------------------------
# Kept here rather than in Liquid so the home page does not have to iterate
# every stub post on every build. Mirrors _layouts/home.html's old markup.
DISCLAIMER_HTML = """
<h2 id="disclaimer">Disclaimer</h2>
<ol>
<li>This is Foodie's MTL site, created because I don't like groups that paywall content. My human translations are at the <a href="http://northbladetl.com">main site, northbladetl.com</a></li>
<li>Copyrights to <a href="/ABSR/">Absolute Regression</a> are held by the author, Jang Yeonghun. Please buy the novel raws or official manhwa translation to support the author.</li>
<li>Copyrights to <a href="/AMKHI/">Assistant Manager Kim Hates Idols</a> are held by the author, Ex-Trainee. Please buy the novel raws to support the author.</li>
<li>Copyrights to <a href="/DOD/">Debut or Die</a> are held by the author, Baek Deoksu. Please buy the official translation or novel raws to support the author.</li>
<li>Copyrights to <a href="/TPD/">The Trashy PD Has To Survive as an Idol</a> are held by the author, Moonjin. Please buy the official translation or novel raws to support the author.</li>
<li>Do not take credit or make a profit from our work. Our translations can be read for free, with no ads. We do not ask for donations.</li>
<li>Although this is MTL, we use a glossary compiled by a human translator for our work, ensuring accurate translation of terms and consistent identification of pronouns.</li>
</ol>
"""

INDEX_DESCRIPTION = (
    "Read free English fan translations of novels like Absolute Regression, "
    "Assistant Manager Kim Hates Idols, Debut or Die, The Trashy PD Has To "
    "Survive as an Idol. No ads, no paywalls. Updated regularly."
)


def generate_index_page(posts_dir, site_root):
    try:
        all_posts = []
        for filename in (f for f in os.listdir(posts_dir) if f.endswith(".md")):
            filepath = os.path.join(posts_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            m = re.match(r'---\s*\n(.*?)\n---', content, re.DOTALL)
            if not m:
                continue
            fm = yaml.safe_load(m.group(1)) if m.group(1) else {}
            if not fm.get('date'):
                continue
            post_date = parse_date(fm['date'])
            if not post_date:
                continue
            slug = filename.split('-', 3)[3].replace('.md', '')
            url = f"/{fm.get('tags', ['uncategorized'])[0]}/{slug}.html"
            all_posts.append({
                'title': fm.get('title', 'Untitled'),
                'date':  post_date.astimezone(UTC8),
                'tags':  fm.get('tags', []),
                'url':   url,
            })

        all_posts.sort(key=lambda p: p['date'], reverse=True)

        items = []
        for post in all_posts[:20]:
            d = post['date']
            date_str = f"{d.strftime('%b')} {d.day}, {d.year}"
            tag_html = f"{post['tags'][0].upper()} " if post['tags'] else ""
            items.append(
                f'  <li>\n    <span class="post-meta">{date_str}</span>\n    '
                f'<h3>\n      {tag_html}<a href="{post["url"]}">{post["title"]}</a>\n    </h3>\n  </li>'
            )

        post_list_html = '<ul class="post-list">\n' + '\n'.join(items) + '\n</ul>'
        page_content = (
            '---\n'
            'layout: home\n'
            f'description: "{INDEX_DESCRIPTION}"\n'
            '---\n'
            f'{DISCLAIMER_HTML}\n'
            '<h2 id="latest-updates">Latest Updates</h2>\n'
            f'{post_list_html}\n'
        )
        with open(os.path.join(site_root, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(page_content)
        print("  OK index.html regenerated")
    except Exception as e:
        print(f"  x Error generating index page: {e}")


# -------------------------------------------------------------
# RSS feed generators
# -------------------------------------------------------------
def _rss_header(title, description, link, self_link, current_time):
    ts = current_time.strftime('%a, %d %b %Y %H:%M:%S +0800')
    return (
        '---\nlayout: null\n---\n'
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        '    <channel>\n'
        f'        <title>{title}</title>\n'
        f'        <description>{description}</description>\n'
        f'        <link>{link}</link>\n'
        f'        <atom:link href="{self_link}" rel="self" type="application/rss+xml"/>\n'
        f'        <pubDate>{ts}</pubDate>\n'
        f'        <lastBuildDate>{ts}</lastBuildDate>\n'
        '        <generator>BananaTL RSS Generator</generator>\n'
    )


def _rss_item(tag, title, series_title, post_date_str, post_url):
    safe_title = (title
                  .replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                  .replace('"', '&quot;').replace("'", '&apos;'))
    return (
        '        <item>\n'
        f'            <title>{tag.upper()} {safe_title}</title>\n'
        '            <author>somethingrandom@somethingrandom.com (FoodieMonster007)</author>\n'
        f'            <description>(BananaTL) {series_title} Chapter Update - {post_url}</description>\n'
        f'            <pubDate>{post_date_str}</pubDate>\n'
        f'            <link>{post_url}</link>\n'
        f'            <guid isPermaLink="true">{post_url}</guid>\n'
        f'            <category>{tag}</category>\n'
        '        </item>\n'
    )


def generate_tag_feed(public_repo_dir, tag, posts, series_title):
    try:
        feed_posts = posts[-10:] if len(posts) > 10 else posts
        current_time = datetime.now(UTC8)

        content = _rss_header(
            title=series_title,
            description=f"BananaTL - {series_title} Chapter Updates",
            link=f"{SITE_URL}/{tag}/",
            self_link=f"{SITE_URL}/feed.{tag}.xml",
            current_time=current_time,
        )
        for post in reversed(feed_posts):
            post_date = ""
            if post.get('date'):
                try:
                    dt = parse_date(post['date'])
                    if dt:
                        post_date = dt.astimezone(UTC8).strftime('%a, %d %b %Y %H:%M:%S +0800')
                except Exception:
                    pass
            content += _rss_item(
                tag, post.get('title', ''), series_title,
                post_date, f"{SITE_URL}{post.get('url', '')}"
            )
        content += '    </channel>\n</rss>'

        with open(os.path.join(public_repo_dir, f'feed.{tag}.xml'), 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  OK feed.{tag}.xml updated ({len(feed_posts)} posts)")
        return True
    except Exception as e:
        print(f"  x Error generating feed.{tag}.xml: {e}")
        return False


def generate_overall_feed(public_repo_dir, posts):
    try:
        feed_posts = posts[:10]
        current_time = datetime.now(UTC8)

        content = _rss_header(
            title="BananaTL - All Series",
            description="Latest chapter updates from BananaTL machine translations",
            link=f"{SITE_URL}/",
            self_link=f"{SITE_URL}/feed.xml",
            current_time=current_time,
        )
        for post in feed_posts:
            post_date = ""
            if post.get('date'):
                try:
                    dt = parse_date(post['date'])
                    if dt:
                        post_date = dt.astimezone(UTC8).strftime('%a, %d %b %Y %H:%M:%S +0800')
                except Exception:
                    pass
            tag = post.get('tag', '')
            series_title = SERIES_TITLES.get(tag, tag.upper())
            content += _rss_item(
                tag, post.get('title', ''), series_title,
                post_date, f"{SITE_URL}{post.get('url', '')}"
            )
        content += '    </channel>\n</rss>'

        with open(os.path.join(public_repo_dir, 'feed.xml'), 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  OK feed.xml updated ({len(feed_posts)} posts)")
        return True
    except Exception as e:
        print(f"  x Error generating feed.xml: {e}")
        return False


def update_feeds_for_new_post(public_repo_dir, tag):
    try:
        print(f"  Updating RSS feeds for {tag}...")
        series_title = SERIES_TITLES.get(tag, tag.upper())
        toc_dir = os.path.join(public_repo_dir, '_data', 'toc')

        # Tag-specific feed
        tag_json_path = os.path.join(toc_dir, f'{tag}.json')
        if os.path.exists(tag_json_path):
            with open(tag_json_path, 'r', encoding='utf-8') as f:
                tag_posts = json.load(f)
            generate_tag_feed(public_repo_dir, tag,
                              tag_posts[-10:] if len(tag_posts) > 10 else tag_posts,
                              series_title)

        # Overall feed - the 10 most recent chapters across the whole site.
        # No per-series slicing: every chapter competes on date alone, so a
        # burst of releases in one series is reflected as it actually happened.
        EXCLUDED = {'index.json', 'summary.json', 'tags_index.json'}
        all_posts = []
        for jf in os.listdir(toc_dir):
            if not jf.endswith('.json') or jf in EXCLUDED:
                continue
            cur_tag = jf.replace('.json', '')
            json_path = os.path.join(toc_dir, jf)
            with open(json_path, 'r', encoding='utf-8') as f:
                series_posts = json.load(f)
            for p in series_posts:
                p['tag'] = cur_tag
                all_posts.append(p)

        all_posts.sort(key=lambda x: x.get('date', ''), reverse=True)
        generate_overall_feed(public_repo_dir, all_posts[:10])

        print(f"  OK RSS feeds updated for {tag}")
        return True
    except Exception as e:
        print(f"  x Error updating feeds for {tag}: {e}")
        return False


# -------------------------------------------------------------
# Per-chapter publish (runs inside a scheduled thread)
# -------------------------------------------------------------
def _publish_chapter(chapter_info, public_repo_dir, posts_dest_dir):
    """
    Write one chapter stub to the public repo, update the TOC, push, trigger the
    build, wait FIRST_DELAY for Jekyll to finish, then send notifications.
    """
    filename          = chapter_info['filename']
    tag               = chapter_info['tag']
    tag_lower         = chapter_info['tag_lower']
    chapter_id        = chapter_info['chapter_id']
    chapter_num       = chapter_info['chapter_num']
    front_matter      = chapter_info['front_matter']
    front_matter_text = chapter_info['front_matter_text']

    sep = "=" * 52
    print(f"\n{sep}")
    print(f"  PUBLISHING: {tag} Chapter {chapter_num}  ({filename})")
    print(sep)

    # 1. Write front-matter-only .md to public _posts
    posts_filepath = os.path.join(posts_dest_dir, filename)
    try:
        with open(posts_filepath, 'w', encoding='utf-8') as f:
            f.write(front_matter_text)
        print(f"  OK Written to _posts: {posts_filepath}")
    except Exception as e:
        print(f"  x Could not write public .md: {e}")
        return

    # 2. Update TOC JSON (title, date, prev/next, dropdown entry)
    update_toc_json(public_repo_dir, filename, front_matter)

    # 3. Update RSS feeds (now that the TOC JSON contains this chapter)
    update_feeds_for_new_post(public_repo_dir, tag_lower)

    # 4. Regenerate home index
    generate_index_page(posts_dest_dir, public_repo_dir)

    # 5. Push public repo  <- countdown starts HERE
    if not git_push(public_repo_dir, PUBLIC_BRANCH):
        print(f"  x Push failed - skipping workflow + notifications for {tag} Ch.{chapter_num}")
        return

    # 6. Trigger Jekyll build
    if not trigger_github_workflow():
        print(f"  x Workflow trigger failed - skipping notifications for {tag} Ch.{chapter_num}")
        return

    # 7. Wait for Jekyll to finish building before notifying readers
    mins, secs = divmod(FIRST_DELAY, 60)
    time_str = f"{mins}m {secs}s" if mins else f"{secs}s"
    print(f"  ... Pushed to GitHub - waiting {time_str} for site to build before notifying...")
    time.sleep(FIRST_DELAY)

    # 8. Send notifications
    send_discord_notification(tag, chapter_num, chapter_id)
    send_ntfy_notification(tag, chapter_num, chapter_id)
    send_telegram_notification(tag, chapter_num, chapter_id)
    print(f"  OK All done for {tag} Chapter {chapter_num}")


def _schedule_and_publish(chapter_info, push_delay, public_repo_dir, posts_dest_dir):
    """Thread target: sleep push_delay (inter-chapter gap only), then publish.
    The notification delay (FIRST_DELAY) is counted from inside _publish_chapter,
    starting the moment the push to GitHub succeeds."""
    tag = chapter_info['tag']
    chapter_num = chapter_info['chapter_num']
    if push_delay > 0:
        mins, secs = divmod(push_delay, 60)
        time_str = f"{mins}m {secs}s" if mins else f"{secs}s"
        print(f"... {tag} Ch.{chapter_num} push in {push_delay}s ({time_str})...")
        time.sleep(push_delay)
    _publish_chapter(chapter_info, public_repo_dir, posts_dest_dir)


# -------------------------------------------------------------
# Main entry point
# -------------------------------------------------------------
def process_markdown_files():
    public_repo_dir = PUBLIC_REPO_DIR
    private_repo_dir = PRIVATE_REPO_DIR
    backup_dir = BACKUP_DIR

    os.makedirs(private_repo_dir, exist_ok=True)
    os.makedirs(backup_dir, exist_ok=True)
    posts_dest_dir = os.path.join(public_repo_dir, '_posts')

    # -- File selection ------------------------------------------
    root = tk.Tk()
    root.withdraw()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_paths = filedialog.askopenfilenames(
        title="Select Markdown file(s) to publish",
        initialdir=script_dir,
        filetypes=(("Markdown files", "*.md"), ("All files", "*.*"))
    )
    if not file_paths:
        print("No files selected.")
        return

    # ============================================================
    # PHASE 1 - Parse, write body to private repo, backup
    # (runs immediately, sequentially, for all selected files)
    # ============================================================
    sep = "=" * 52
    print(f"\n{sep}")
    print(f"  PHASE 1: Preparing {len(file_paths)} file(s)")
    print(sep)

    prepared_chapters = []

    for file_path in file_paths:
        filename = os.path.basename(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split front matter from body
            fm_end = content.find('---', 3)
            if fm_end == -1:
                print(f"  !  No front matter in {filename}, skipping")
                continue
            fm_end += 3
            front_matter_text = content[:fm_end]
            main_content = content[fm_end:].lstrip()

            fm_match = re.match(r'---\s*\n(.*?)\n---', front_matter_text, re.DOTALL)
            if not fm_match:
                print(f"  !  Could not parse front matter in {filename}, skipping")
                continue
            front_matter = yaml.safe_load(fm_match.group(1)) if fm_match.group(1) else {}

            if not main_content.strip():
                print(f"  !  {filename} has no chapter body - did you paste the text in? Skipping")
                continue

            tags = front_matter.get('tags', [])
            if not tags:
                print(f"  !  No tags in {filename}, skipping")
                continue
            tag = tags[0].upper()
            tag_lower = tags[0].lower()

            if tag_lower not in SERIES_TITLES:
                print(f"  !  '{tag_lower}' is not a known series for this site "
                      f"({', '.join(sorted(SERIES_TITLES))}) - skipping {filename}")
                continue

            chapter_match = re.search(r'\d{4}-\d{2}-\d{2}-(.+?)\.md$', filename)
            if chapter_match:
                chapter_id = chapter_match.group(1)
                m = re.search(r'(\d+)$', chapter_id)
                chapter_num = int(m.group(1)) if m else 0
            else:
                print(f"  !  Could not extract chapter info from {filename}")
                chapter_id = ""
                chapter_num = 0

            # The runtime fetch rebuilds this filename from the front-matter
            # date, so a mismatch means the chapter would 404 for readers.
            fm_date = str(front_matter.get('date', ''))[:10]
            if fm_date and not filename.startswith(fm_date):
                print(f"  !  {filename}: front-matter date ({fm_date}) does not match the "
                      f"filename date. Readers would get a 404 - skipping.")
                continue

            # Write processed body to PRIVATE repo
            modified_content = "".join(replace_text(main_content.splitlines(keepends=True)))
            private_series_dir = os.path.join(private_repo_dir, tag)
            os.makedirs(private_series_dir, exist_ok=True)
            private_filepath = os.path.join(private_series_dir, filename)
            with open(private_filepath, 'w', encoding='utf-8') as f:
                f.write(modified_content)

            # Backup original
            backup_filepath = os.path.join(backup_dir, filename)
            shutil.move(file_path, backup_filepath)

            print(f"  OK Prepared  {filename}")
            print(f"      Private: {private_filepath}")
            print(f"      Backup:  {backup_filepath}")

            prepared_chapters.append({
                'filename':          filename,
                'front_matter_text': front_matter_text,
                'front_matter':      front_matter,
                'tag':               tag,
                'tag_lower':         tag_lower,
                'chapter_id':        chapter_id,
                'chapter_num':       chapter_num,
            })

        except Exception as e:
            print(f"  x Error preparing {filename}: {e}")

    if not prepared_chapters:
        print("x No files could be prepared.")
        return

    # Push PRIVATE repo once, immediately - the body has to be live in cheptars
    # before any reader can be sent to the chapter page.
    print(f"\n{sep}")
    print("  Pushing PRIVATE repository (all chapters)")
    print(sep)
    if git_push(private_repo_dir, PRIVATE_BRANCH):
        print("  OK Private repository updated")
    else:
        print("  x Failed to update private repository")

    # ============================================================
    # PHASE 2 - Staggered public publishing
    #
    # Each chapter's thread waits only the inter-chapter gap
    # before pushing, then FIRST_DELAY starts counting from
    # the moment the push to GitHub succeeds:
    #
    # Chapter 1 -> push at T+0,               notify at T+FIRST_DELAY
    # Chapter 2 -> push at T+BETWEEN_DELAY,   notify at T+BETWEEN_DELAY+FIRST_DELAY
    # Chapter 3 -> push at T+2*BETWEEN_DELAY, notify at T+2*BETWEEN_DELAY+FIRST_DELAY
    # ============================================================
    print(f"\n{sep}")
    print("  PHASE 2: Scheduling staggered public publishing")
    print(f"  Notification delay after push: {FIRST_DELAY}s ({FIRST_DELAY // 60}m {FIRST_DELAY % 60}s)")
    print(f"  Between chapter pushes:        {BETWEEN_DELAY}s ({BETWEEN_DELAY // 60} min)")
    print(sep)

    publish_threads = []
    for i, chapter_info in enumerate(prepared_chapters):
        push_delay = i * BETWEEN_DELAY
        notify_at = push_delay + FIRST_DELAY
        p_mins, p_secs = divmod(push_delay, 60)
        n_mins, n_secs = divmod(notify_at, 60)
        push_str = f"{p_mins}m {p_secs}s" if p_mins else f"{p_secs}s"
        notify_str = f"{n_mins}m {n_secs}s"
        print(f"  #{i+1}: {chapter_info['tag']} Ch.{chapter_info['chapter_num']}"
              f"  ->  push T+{push_delay}s ({push_str})"
              f",  notify T+{notify_at}s ({notify_str})")

        t = threading.Thread(
            target=_schedule_and_publish,
            args=(chapter_info, push_delay, public_repo_dir, posts_dest_dir),
            daemon=False,
        )
        t.start()
        publish_threads.append(t)

    last_notify = (len(prepared_chapters) - 1) * BETWEEN_DELAY + FIRST_DELAY
    join_timeout = last_notify + 60   # 60 s buffer after final notification
    print(f"\n  Last notification fires at T+{last_notify}s. Script waits up to {join_timeout}s total.")

    try:
        for t in publish_threads:
            t.join(timeout=join_timeout)
        print("\nOK All chapters published and notified!")
    except KeyboardInterrupt:
        print("\n!  Interrupted. Threads are still running in the background.")
    except Exception as e:
        print(f"\n!  Unexpected error while waiting: {e}")


if __name__ == "__main__":
    process_markdown_files()
