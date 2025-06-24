import axios from "axios";
import { parseStringPromise } from "xml2js";
import { JSDOM } from "jsdom";
import TurndownService from "turndown";

export class Scraper {
  private sitemap: string;

  constructor(url: string) {
    this.sitemap = url;
  }

  async _getUrls() {
    try {
      const response = await axios.get(this.sitemap);
      const xml = response.data;

      const parsed = await parseStringPromise(xml);

      const urls: string[] = parsed.urlset.url.map(
        (entry: any) => entry.loc[0]
      );

      return urls;
    } catch (err) {
      console.error("Failed to parse sitemap:", err);
      return [];
    }
  }

  async scrape() {
    try {
      const urls = await this._getUrls();

      var res = [];

      if (urls.length) {
        for (var url of urls) {
          const response = await axios(url);
          if (response) {
            const jsDOM = new JSDOM(response.data);
            const document = jsDOM.window.document;

            const contentElement =
              document.querySelector("main") || document.body;

            const turndownService = new TurndownService();
            const markdown = turndownService.turndown(contentElement.innerHTML);

            res.push(markdown);

            break;
          }
        }
      }

      return res;
    } catch (err) {
      console.error("Failed to parse sitemap:", err);
      return [];
    }
  }
}
