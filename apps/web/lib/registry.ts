// lib/registry.ts
import fs from "fs/promises";
import path from "path";

const DB_PATH = path.join(process.cwd(), "projects.json");

export type Project = {
  name: string;
  slug: string;
  localPath: string;
};

// Ensure DB file exists
async function initDB() {
  try {
    await fs.access(DB_PATH);
  } catch {
    await fs.writeFile(DB_PATH, JSON.stringify([]));
  }
}

export async function getProjects(): Promise<Project[]> {
  await initDB();
  const data = await fs.readFile(DB_PATH, "utf-8");
  return JSON.parse(data);
}

export async function createProject(project: Project) {
  const projects = await getProjects();
  if (projects.find((p) => p.slug === project.slug)) {
    throw new Error("Slug already exists");
  }
  projects.push(project);
  await fs.writeFile(DB_PATH, JSON.stringify(projects, null, 2));
}

export async function getProject(slug: string): Promise<Project | undefined> {
  const projects = await getProjects();
  return projects.find((p) => p.slug === slug);
}

export async function deleteProject(slug: string) {
  const projects = await getProjects();
  const filtered = projects.filter((p) => p.slug !== slug);
  await fs.writeFile(DB_PATH, JSON.stringify(filtered, null, 2));
}
