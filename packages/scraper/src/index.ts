import axios from "axios";
import { parseStringPromise } from "xml2js";

export class Scraper {
  private sitemap: string;

  constructor(url: string) {
    this.sitemap = url;
  }

  async scrape() {
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
}
