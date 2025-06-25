import axios from "axios";
import { parseStringPromise } from "xml2js";
import { JSDOM } from "jsdom";
import TurndownService from "turndown";

export class Scraper {
  private sitemap: string;

  constructor(url: string) {
    this.sitemap = url;
  }

  private async _getUrls(): Promise<string[]> {
    try {
      const response = await axios.get(this.sitemap);
      const xml = response.data;
      const parsed = await parseStringPromise(xml);

      const urls: string[] = parsed.urlset.url.map(
        (entry: any) => entry.loc[0]
      );

      return urls;
    } catch (err) {
      console.error("❌ Failed to parse sitemap:", err);
      return [];
    }
  }

  public async scrape(): Promise<{ url: string; markdown: string }[]> {
    const results: { url: string; markdown: string }[] = [];

    try {
      const urls = await this._getUrls();
      const turndownService = new TurndownService({
        headingStyle: "atx",
        codeBlockStyle: "fenced",
        bulletListMarker: "-",
      });

      for (const url of urls) {
        try {
          const response = await axios.get(
            "https://cal.com/docs/self-hosting/installation"
          );
          const dom = new JSDOM(response.data);
          const document = dom.window.document;

          console.log(url);

          const contentElement =
            document.querySelector(".mdx-content") ||
            document.querySelector("article") ||
            document.body;

          const markdown = turndownService.turndown(contentElement.innerHTML);

          results.push({ url, markdown });

          //mdx-content relative mt-8 prose prose-gray dark:prose-invert

          // Remove this if you want to scrape all pages
          break;
        } catch (err: any) {
          console.warn(`⚠️ Failed to fetch or parse: ${url}`, err.message);
        }
      }

      return results;
    } catch (err) {
      console.error("❌ Failed to scrape:", err);
      return [];
    }
  }
}
