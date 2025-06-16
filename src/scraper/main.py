import os
import re
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from markdownify import markdownify as md

# === CONFIG ===
SITEMAP_URL = "https://cal.com/docs/sitemap.xml"
OUTPUT_BASE_DIR = "./data"

# === HELPERS ===
def slugify(url: str) -> str:
    return re.sub(r'[^a-zA-Z0-9\-]', '-', url.strip('/').split('/')[-1])

def get_site_name(url: str) -> str:
    return urlparse(url).netloc.replace('.', '-')

def get_all_urls_from_sitemap(sitemap_url: str) -> list:
    res = requests.get(sitemap_url)
    tree = ET.fromstring(res.content)
    return [loc.text for loc in tree.findall(".//{*}loc")]

def fetch_page_content(url: str) -> str:
    res = requests.get(url)
    soup = BeautifulSoup(res.content, "html.parser")

    # Extract main readable content
    content = soup.find("main") or soup.find("article") or soup.body
    if content:
        return md(str(content))
    return ""

# === MAIN SCRIPT ===
def main():
    site_name = get_site_name(SITEMAP_URL)
    output_dir = os.path.join(OUTPUT_BASE_DIR, site_name)
    os.makedirs(output_dir, exist_ok=True)

    urls = get_all_urls_from_sitemap(SITEMAP_URL)
    print(f"Found {len(urls)} URLs in sitemap")

    for url in urls:
        print(f"🔗 Fetching: {url}")
        try:
            content_md = fetch_page_content(url)
            if not content_md.strip():
                print(f"⚠️ Skipped (empty content): {url}")
                continue

            filename = f"{slugify(url)}.md"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# Source: {url}\n\n{content_md}")
            print(f"✅ Saved: {filename}")
        except Exception as e:
            print(f"❌ Failed to fetch {url}: {e}")

if __name__ == "__main__":
    main()