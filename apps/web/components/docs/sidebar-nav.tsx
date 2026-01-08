"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { type TreeNode } from "@/lib/fs-utils";
import { cn } from "@/lib/utils";
import { ChevronRight, FileText, Folder, FolderOpen } from "lucide-react";
import { useState } from "react";

interface SidebarNavProps {
  nodes: TreeNode[];
  projectSlug: string;
}

export function SidebarNav({ nodes, projectSlug }: SidebarNavProps) {
  return (
    <nav className="space-y-1">
      {nodes.map((node) => (
        <SidebarItem key={node.path} node={node} projectSlug={projectSlug} />
      ))}
    </nav>
  );
}

function SidebarItem({
  node,
  projectSlug,
}: {
  node: TreeNode;
  projectSlug: string;
}) {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(true);

  if (node.type === "folder") {
    return (
      <div className="space-y-1">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          <ChevronRight
            className={cn(
              "h-4 w-4 shrink-0 transition-transform",
              isOpen && "rotate-90"
            )}
          />
          {isOpen ? (
            <FolderOpen className="h-4 w-4 shrink-0 text-amber-500" />
          ) : (
            <Folder className="h-4 w-4 shrink-0 text-amber-500" />
          )}
          <span className="truncate">{node.name}</span>
        </button>
        {isOpen && node.children && (
          <div className="ml-4 border-l pl-2">
            {node.children.map((child) => (
              <SidebarItem
                key={child.path}
                node={child}
                projectSlug={projectSlug}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  const href = node.path.startsWith("/") ? node.path : `/${node.path}`;
  const isActive = pathname === href;

  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors",
        isActive
          ? "bg-primary/10 text-primary font-medium"
          : "text-foreground/70 hover:bg-muted hover:text-foreground"
      )}
    >
      <FileText className="h-4 w-4 shrink-0 text-blue-500" />
      <span className="truncate">{node.name}</span>
    </Link>
  );
}
