import re
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from markdownify import markdownify as md
from sqlalchemy.orm import sessionmaker

from src.models.Sitemap import Sitemap
from src.models import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class SitemapScraper:
    def __init__(self, sitemap_url: str, output_base_dir: str = "./data"):
        self.sitemap_url = sitemap_url
        self.output_base_dir = output_base_dir
        self.site_name = self._get_site_name()
        self.db = SessionLocal()
        Sitemap.metadata.create_all(bind=engine)


    def _slugify(self, url: str) -> str:
        return re.sub(r'[^a-zA-Z0-9\-]', '-', url.strip('/').split('/')[-1])

    def _get_site_name(self) -> str:
        return urlparse(self.sitemap_url).netloc.replace('.', '-')

    def _get_all_urls(self) -> list:
        try:
            res = requests.get(self.sitemap_url)
            res.raise_for_status()
            tree = ET.fromstring(res.content)
            return [loc.text for loc in tree.findall(".//{*}loc")]
        except Exception as e:
            print(f"❌ Failed to parse sitemap: {e}")
            return []

    def _fetch_page_markdown(self, url: str) -> str:
        try:
            res = requests.get(url)
            res.raise_for_status()
            soup = BeautifulSoup(res.content, "html.parser")

            # ✅ Only extract `.mdx-content`
            content = soup.select_one(".mdx-content")
            if content:
                return md(str(content))
            return ""
        except Exception as e:
            print(f"❌ Failed to fetch {url}: {e}")
            return ""
        
    def _save_to_db(self, url: str, markdown: str):
        slug = self._slugify(url)
        existing = self.db.query(Sitemap).filter_by(URL=url).first()

        if existing:
            existing.Markdown = markdown
            print(f"♻️ Updated: {slug}")
        else:
            new_doc = Sitemap(
                Site=self.site_name,
                URL=url,
                Slug=slug,
                Markdown=markdown
            )
            self.db.add(new_doc)
            print(f"✅ Inserted: {slug}")

        self.db.commit()

    def scrape(self):
        urls = self._get_all_urls()
        print(f"Found {len(urls)} URLs in sitemap")

        for url in urls:
            print(f"🔗 Fetching: {url}")
            markdown = self._fetch_page_markdown(url)

            if not markdown.strip():
                print(f"⚠️ Skipped (empty or no .mdx-content): {url}")
                continue

            self._save_to_db(url, markdown)