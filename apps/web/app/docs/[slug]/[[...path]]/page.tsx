import fs from "fs/promises";
import path from "path";
import Markdoc, { Node, Tag, Config } from "@markdoc/markdoc";
import matter from "gray-matter";
import { getProject } from "@/lib/registry";
import { getDocsTree } from "@/lib/fs-utils";
import { MarkdocRenderer } from "@/components/docs/markdoc-renderer";
import { SidebarNav } from "@/components/docs/sidebar-nav";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { notFound } from "next/navigation";
import Link from "next/link";
import { BookOpen, Home, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";

// Helper to generate slug from text
function generateId(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

// Helper to extract text from Markdoc node for ID generation
function getNodeTextContent(node: Node): string {
  let text = "";
  for (const child of node.walk()) {
    if (child.type === "text" && typeof child.attributes.content === "string") {
      text += child.attributes.content;
    }
  }
  return text;
}

// Markdoc configuration with custom tags
const markdocConfig: Config = {
  tags: {
    alert: {
      render: "Alert",
      attributes: {
        type: { type: String, default: "default" },
      },
    },
    button: {
      render: "Button",
      attributes: {
        variant: { type: String, default: "default" },
      },
    },
    callout: {
      render: "Alert",
      attributes: {
        type: { type: String, default: "default" },
      },
    },
  },
  nodes: {
    heading: {
      render: "Heading",
      attributes: {
        level: { type: Number, required: true },
        id: { type: String },
      },
      transform(node: Node, config: Config) {
        const children = node.transformChildren(config);
        const text = getNodeTextContent(node);
        const id = generateId(text);
        const level = node.attributes.level || 1;

        return new Tag("Heading", { level, id }, children);
      },
    },
    paragraph: {
      render: "Paragraph",
    },
    list: {
      render: "List",
      attributes: {
        ordered: { type: Boolean, default: false },
      },
    },
    item: {
      render: "Item",
    },
    fence: {
      render: "CodeBlock",
      attributes: {
        language: { type: String },
        content: { type: String },
      },
    },
    code: {
      render: "Code",
      attributes: {
        content: { type: String },
      },
    },
    link: {
      render: "Link",
      attributes: {
        href: { type: String, required: true },
        title: { type: String },
      },
    },
    blockquote: {
      render: "Blockquote",
    },
    hr: {
      render: "Hr",
    },
    table: {
      render: "Table",
    },
    thead: {
      render: "Thead",
    },
    tbody: {
      render: "Tbody",
    },
    tr: {
      render: "Tr",
    },
    th: {
      render: "Th",
    },
    td: {
      render: "Td",
    },
    image: {
      render: "Image",
      attributes: {
        src: { type: String, required: true },
        alt: { type: String },
      },
    },
  },
};

interface PageProps {
  params: Promise<{ slug: string; path?: string[] }>;
}

export default async function DocPage({ params }: PageProps) {
  const { slug: projectSlug, path: pathSegments } = await params;

  // 1. Validate Project
  const projectConfig = await getProject(projectSlug);
  if (!projectConfig) {
    notFound();
  }

  // 2. Build Sidebar Data
  const sidebarTree = await getDocsTree(
    projectConfig.localPath,
    `/docs/${projectSlug}`
  );

  // 3. Resolve Current File
  const relativePath = pathSegments ? pathSegments.join("/") : "index";

  // Try multiple possible file paths
  const possiblePaths = [
    path.join(projectConfig.localPath, relativePath + ".mdoc"),
    path.join(projectConfig.localPath, relativePath + ".md"),
    path.join(projectConfig.localPath, relativePath, "index.mdoc"),
    path.join(projectConfig.localPath, relativePath, "index.md"),
    path.join(projectConfig.localPath, "index.mdoc"),
    path.join(projectConfig.localPath, "index.md"),
    path.join(projectConfig.localPath, "README.md"),
  ];

  let source = "";
  let fileFound = false;

  for (const p of possiblePaths) {
    try {
      source = await fs.readFile(p, "utf-8");
      fileFound = true;
      break;
    } catch {
      // Continue to next possible path
    }
  }

  // 4. Handle not found - show welcome page
  if (!fileFound) {
    return (
      <div className="flex h-screen overflow-hidden bg-background">
        <DocsLayout
          projectConfig={projectConfig}
          sidebarTree={sidebarTree}
          projectSlug={projectSlug}
        >
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <BookOpen className="h-16 w-16 text-muted-foreground/50 mb-6" />
            <h1 className="text-3xl font-bold mb-4">{projectConfig.name}</h1>
            <p className="text-muted-foreground max-w-md mb-2">
              Welcome to the documentation. Select a page from the sidebar to
              get started.
            </p>
            <p className="text-sm text-muted-foreground/70">
              Source:{" "}
              <code className="bg-muted px-1.5 py-0.5 rounded">
                {projectConfig.localPath}
              </code>
            </p>
            {sidebarTree.length === 0 && (
              <p className="text-sm text-amber-600 mt-4">
                No markdown files found in this directory.
              </p>
            )}
          </div>
        </DocsLayout>
      </div>
    );
  }

  // 5. Parse Content
  const { content: rawContent, data: frontmatter } = matter(source);

  const ast = Markdoc.parse(rawContent);
  const errors = Markdoc.validate(ast, markdocConfig);

  if (errors.length > 0) {
    console.warn("Markdoc validation errors:", errors);
  }

  // Transform AST to renderable JSON tree
  const contentTree = Markdoc.transform(ast, markdocConfig);

  // Generate table of contents from headings
  const headings = extractHeadings(ast);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <DocsLayout
        projectConfig={projectConfig}
        sidebarTree={sidebarTree}
        projectSlug={projectSlug}
      >
        <div className="flex">
          {/* Main Content */}
          <div className="flex-1 min-w-0">
            <ScrollArea className="h-screen">
              <article className="max-w-3xl mx-auto py-10 px-6">
                {frontmatter.title && (
                  <h1 className="text-4xl font-extrabold tracking-tight mb-2">
                    {frontmatter.title}
                  </h1>
                )}
                {frontmatter.description && (
                  <p className="text-xl text-muted-foreground mb-8">
                    {frontmatter.description}
                  </p>
                )}
                {(frontmatter.title || frontmatter.description) && (
                  <Separator className="mb-8" />
                )}
                <div className="prose-custom">
                  <MarkdocRenderer
                    content={JSON.parse(JSON.stringify(contentTree))}
                  />
                </div>
              </article>
            </ScrollArea>
          </div>

          {/* Table of Contents - Desktop */}
          {headings.length > 0 && (
            <aside className="hidden md:block w-56 shrink-0 border-l">
              <div className="sticky top-0 p-4">
                <h4 className="font-semibold text-sm mb-3">On this page</h4>
                <nav className="space-y-1">
                  {headings.map((heading, idx) => (
                    <a
                      key={idx}
                      href={`#${heading.id}`}
                      className="block text-sm text-muted-foreground hover:text-foreground transition-colors"
                      style={{ paddingLeft: `${(heading.level - 1) * 12}px` }}
                    >
                      {heading.text}
                    </a>
                  ))}
                </nav>
              </div>
            </aside>
          )}
        </div>
      </DocsLayout>
    </div>
  );
}

// Docs Layout Component
function DocsLayout({
  projectConfig,
  sidebarTree,
  projectSlug,
  children,
}: {
  projectConfig: { name: string; localPath: string };
  sidebarTree: import("@/lib/fs-utils").TreeNode[];
  projectSlug: string;
  children: React.ReactNode;
}) {
  return (
    <>
      {/* Sidebar */}
      <aside className="w-72 border-r bg-card hidden md:flex flex-col shrink-0">
        {/* Sidebar Header */}
        <div className="p-4 border-b">
          <div className="flex items-center gap-2 mb-2">
            <Link href="/">
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <Home className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/docs-admin">
              <Button variant="ghost" size="sm" className="h-8 text-xs">
                Admin
              </Button>
            </Link>
          </div>
          <h2 className="font-bold text-lg">{projectConfig.name}</h2>
        </div>

        {/* Sidebar Navigation */}
        <ScrollArea className="flex-1 p-4">
          {sidebarTree.length > 0 ? (
            <SidebarNav nodes={sidebarTree} projectSlug={projectSlug} />
          ) : (
            <p className="text-sm text-muted-foreground">
              No documentation files found.
            </p>
          )}
        </ScrollArea>

        {/* Sidebar Footer */}
        <div className="p-4 border-t text-xs text-muted-foreground">
          <a
            href={`file://${projectConfig.localPath}`}
            className="flex items-center gap-1 hover:text-foreground transition-colors"
          >
            <ExternalLink className="h-3 w-3" />
            Open in Finder
          </a>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-hidden">{children}</main>
    </>
  );
}

// Helper to extract headings for TOC using Markdoc's Node API
function extractHeadings(
  ast: Node
): Array<{ level: number; text: string; id: string }> {
  const headings: Array<{ level: number; text: string; id: string }> = [];

  // Use Markdoc's walk() method to traverse the AST
  for (const node of ast.walk()) {
    if (node.type === "heading") {
      const text = getNodeTextContent(node);
      const id = generateId(text);
      const level = (node.attributes.level as number) || 1;

      if (level <= 3) {
        headings.push({ level, text, id });
      }
    }
  }

  return headings;
}
