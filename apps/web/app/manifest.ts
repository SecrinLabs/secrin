import type { MetadataRoute } from "next";
import { SITE } from "@/constants/site";
import { SEO } from "@/constants/seo";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: SEO.default.title,
    short_name: SITE.name,
    description: SEO.default.description,
    start_url: "/",
    display: "standalone",
    background_color: "#ffffff",
    theme_color: SITE.themeColor,
    orientation: "portrait-primary",
    categories: ["developer tools", "productivity", "utilities"],
    icons: [
      {
        src: "/android-icon-36x36.png",
        sizes: "36x36",
        type: "image/png",
      },
      {
        src: "/android-icon-48x48.png",
        sizes: "48x48",
        type: "image/png",
      },
      {
        src: "/android-icon-72x72.png",
        sizes: "72x72",
        type: "image/png",
      },
      {
        src: "/android-icon-96x96.png",
        sizes: "96x96",
        type: "image/png",
      },
      {
        src: "/android-icon-144x144.png",
        sizes: "144x144",
        type: "image/png",
      },
      {
        src: "/android-icon-192x192.png",
        sizes: "192x192",
        type: "image/png",
      },
    ],
  };
}
