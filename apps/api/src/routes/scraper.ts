// apps/api/src/routes/scraper.ts
import { Router } from "express";
import { Scraper } from "@workspace/scraper/src";

const router: Router = Router();

router.get("/", async (req, res) => {
  const { url } = req.query;

  if (typeof url !== "string") {
    res
      .status(400)
      .json({ success: false, error: "Missing or invalid 'url' query param" });
  }

  try {
    const scraper = new Scraper(url as string);
    const urls = await scraper.scrape();
    res.json({ success: true, data: urls });
  } catch (err) {
    res.status(500).json({ success: false, error: (err as Error).message });
  }
});

export default router;
