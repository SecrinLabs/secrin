// apps/api/src/index.ts
import express from "express";
import scraperRoute from "./routes/scraper";

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use("/scraper", scraperRoute); // exposes GET /scraper?url=...

app.listen(PORT, () => {
  console.log(`API running at http://localhost:${PORT}`);
});
