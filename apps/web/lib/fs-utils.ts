// lib/fs-utils.ts
import fs from "fs/promises";
import path from "path";
import matter from "gray-matter";

export type TreeNode = {
  name: string;
  path: string; // URL path segment
  type: "file" | "folder";
  children?: TreeNode[];
};

export async function getDocsTree(
  dirPath: string,
  routePrefix: string
): Promise<TreeNode[]> {
  try {
    const entries = await fs.readdir(dirPath, { withFileTypes: true });

    const nodes = await Promise.all(
      entries.map(async (entry) => {
        const fullPath = path.join(dirPath, entry.name);

        // Skip hidden files and directories
        if (entry.name.startsWith(".")) {
          return null;
        }

        if (entry.isDirectory()) {
          const children = await getDocsTree(
            fullPath,
            path.join(routePrefix, entry.name)
          );
          // Only include folders that have content
          if (children.length === 0) {
            return null;
          }
          return {
            name: formatName(entry.name),
            type: "folder",
            path: entry.name,
            children,
          } as TreeNode;
        } else if (entry.name.endsWith(".md") || entry.name.endsWith(".mdoc")) {
          // Read frontmatter to get the "real" title instead of filename
          try {
            const fileContent = await fs.readFile(fullPath, "utf-8");
            const { data } = matter(fileContent);
            const cleanName = entry.name.replace(/\.mdoc$|\.md$/, "");

            return {
              name: data.title || formatName(cleanName),
              type: "file",
              path: path.join(routePrefix, cleanName),
            } as TreeNode;
          } catch {
            return null;
          }
        }
        return null;
      })
    );

    // Filter nulls and sort (Folders first, then files)
    return nodes
      .filter(Boolean)
      .sort((a, b) =>
        a!.type === b!.type ? 0 : a!.type === "folder" ? -1 : 1
      ) as TreeNode[];
  } catch (error) {
    console.error("Error reading docs tree:", error);
    return [];
  }
}

// Format kebab-case or snake_case to Title Case
function formatName(name: string): string {
  return name
    .replace(/[-_]/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
