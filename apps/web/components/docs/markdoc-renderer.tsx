"use client";

import React from "react";
import Markdoc, { RenderableTreeNode } from "@markdoc/markdoc";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// Heading component with proper typing
function HeadingComponent({
  level,
  children,
  id,
}: {
  level: number;
  children: React.ReactNode;
  id?: string;
}) {
  const styles: Record<number, string> = {
    1: "text-4xl font-bold tracking-tight mb-6",
    2: "text-3xl font-semibold tracking-tight mt-10 mb-4 border-b pb-2",
    3: "text-2xl font-semibold mt-8 mb-3",
    4: "text-xl font-semibold mt-6 mb-2",
    5: "text-lg font-medium mt-4 mb-2",
    6: "text-base font-medium mt-4 mb-2",
  };

  const className = cn(styles[level] || styles[6]);

  switch (level) {
    case 1:
      return (
        <h1 id={id} className={className}>
          {children}
        </h1>
      );
    case 2:
      return (
        <h2 id={id} className={className}>
          {children}
        </h2>
      );
    case 3:
      return (
        <h3 id={id} className={className}>
          {children}
        </h3>
      );
    case 4:
      return (
        <h4 id={id} className={className}>
          {children}
        </h4>
      );
    case 5:
      return (
        <h5 id={id} className={className}>
          {children}
        </h5>
      );
    default:
      return (
        <h6 id={id} className={className}>
          {children}
        </h6>
      );
  }
}

// Custom component definitions for Markdoc
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const components: Record<string, React.ComponentType<any>> = {
  Alert: ({
    type = "default",
    children,
  }: {
    type?: "default" | "destructive";
    children: React.ReactNode;
  }) => (
    <Alert variant={type} className="my-4">
      <AlertTitle className="capitalize">
        {type === "destructive" ? "Error" : "Note"}
      </AlertTitle>
      <AlertDescription>{children}</AlertDescription>
    </Alert>
  ),

  Button: ({
    variant = "default",
    children,
  }: {
    variant?:
      | "default"
      | "destructive"
      | "outline"
      | "secondary"
      | "ghost"
      | "link";
    children: React.ReactNode;
  }) => <Button variant={variant}>{children}</Button>,

  Heading: HeadingComponent,

  Paragraph: ({ children }: { children: React.ReactNode }) => (
    <p className="leading-7 [&:not(:first-child)]:mt-4">{children}</p>
  ),

  List: ({
    ordered,
    children,
  }: {
    ordered: boolean;
    children: React.ReactNode;
  }) => {
    const Tag = ordered ? "ol" : "ul";
    return (
      <Tag className={cn("my-4 ml-6", ordered ? "list-decimal" : "list-disc")}>
        {children}
      </Tag>
    );
  },

  Item: ({ children }: { children: React.ReactNode }) => (
    <li className="mt-2">{children}</li>
  ),

  CodeBlock: ({
    children,
    content,
    language,
  }: {
    children?: React.ReactNode;
    content?: string;
    language?: string;
  }) => {
    // Markdoc passes fence content in 'content' attribute, but children may also exist
    const codeContent =
      content || (typeof children === "string" ? children : "");
    return (
      <pre className="my-4 overflow-x-auto rounded-lg bg-zinc-950 p-4">
        <code
          className={cn(
            "text-sm text-zinc-100",
            language && `language-${language}`
          )}
        >
          {codeContent}
        </code>
      </pre>
    );
  },

  Code: ({
    children,
    content,
  }: {
    children?: React.ReactNode;
    content?: string;
  }) => (
    <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-sm">
      {content || children}
    </code>
  ),

  Link: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a
      href={href}
      className="font-medium text-primary underline underline-offset-4 hover:no-underline"
      target={href.startsWith("http") ? "_blank" : undefined}
      rel={href.startsWith("http") ? "noopener noreferrer" : undefined}
    >
      {children}
    </a>
  ),

  Blockquote: ({ children }: { children: React.ReactNode }) => (
    <blockquote className="mt-6 border-l-4 border-primary pl-6 italic text-muted-foreground">
      {children}
    </blockquote>
  ),

  Hr: () => <hr className="my-8 border-muted" />,

  Table: ({ children }: { children: React.ReactNode }) => (
    <div className="my-6 w-full overflow-y-auto">
      <table className="w-full">{children}</table>
    </div>
  ),

  Thead: ({ children }: { children: React.ReactNode }) => (
    <thead className="border-b">{children}</thead>
  ),

  Tbody: ({ children }: { children: React.ReactNode }) => (
    <tbody>{children}</tbody>
  ),

  Tr: ({ children }: { children: React.ReactNode }) => (
    <tr className="border-b transition-colors hover:bg-muted/50">{children}</tr>
  ),

  Th: ({ children }: { children: React.ReactNode }) => (
    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
      {children}
    </th>
  ),

  Td: ({ children }: { children: React.ReactNode }) => (
    <td className="p-4 align-middle">{children}</td>
  ),

  Image: ({ src, alt }: { src: string; alt?: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt || ""} className="my-4 rounded-lg border" />
  ),
};

export function MarkdocRenderer({ content }: { content: RenderableTreeNode }) {
  return <>{Markdoc.renderers.react(content, React, { components })}</>;
}
