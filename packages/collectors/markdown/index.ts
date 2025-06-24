import fs from "fs";
import path from "path";
import { Collector } from "../base";
import axios from "axios";
import { parseStringPromise } from "xml2js";

var sitemap = "https://cal.com/docs/sitemap.xml";

export class MarkdownCollector implements Collector {
  constructor(private baseDir: string) {}

  async collect(): Promise<any> {
    // parse the links from sitemap
    const response = await axios.get(sitemap);
    const xml = response.data;

    const parsed = await parseStringPromise(xml);

    const urlEntries = parsed.urlset?.url ?? parsed.sitemapindex?.sitemap ?? [];

    const urls: string[] = [];
    for (const entry of urlEntries) {
      if (entry.loc && entry.loc[0]) {
        urls.push(entry.loc[0]);
      }
    }

    console.log(urls);

    // get the documents
    // store the documents
  }
}
