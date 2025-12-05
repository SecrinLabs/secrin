"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { cn } from "@/lib/utils";
import { Copy, Check } from "lucide-react";
import { useState } from "react";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({
  content,
  className,
}: MarkdownRendererProps) {
  return (
    <div
      className={cn("prose prose-sm dark:prose-invert max-w-none", className)}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Code blocks with syntax highlighting
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || "");
            const isInline = !match;

            if (isInline) {
              return (
                <code
                  className="px-1.5 py-0.5 rounded bg-muted font-mono text-sm"
                  {...props}
                >
                  {children}
                </code>
              );
            }

            return (
              <CodeBlock language={match[1]}>
                {String(children).replace(/\n$/, "")}
              </CodeBlock>
            );
          },
          // Style other elements
          p({ children }) {
            return <p className="mb-3 last:mb-0">{children}</p>;
          },
          ul({ children }) {
            return (
              <ul className="list-disc pl-6 mb-3 space-y-1">{children}</ul>
            );
          },
          ol({ children }) {
            return (
              <ol className="list-decimal pl-6 mb-3 space-y-1">{children}</ol>
            );
          },
          li({ children }) {
            return <li className="leading-relaxed">{children}</li>;
          },
          h1({ children }) {
            return (
              <h1 className="text-xl font-bold mb-3 mt-4 first:mt-0">
                {children}
              </h1>
            );
          },
          h2({ children }) {
            return (
              <h2 className="text-lg font-bold mb-2 mt-4 first:mt-0">
                {children}
              </h2>
            );
          },
          h3({ children }) {
            return (
              <h3 className="text-base font-semibold mb-2 mt-3 first:mt-0">
                {children}
              </h3>
            );
          },
          blockquote({ children }) {
            return (
              <blockquote className="border-l-4 border-primary/30 pl-4 italic text-muted-foreground my-3">
                {children}
              </blockquote>
            );
          },
          a({ href, children }) {
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
              >
                {children}
              </a>
            );
          },
          table({ children }) {
            return (
              <div className="overflow-x-auto my-3">
                <table className="min-w-full border-collapse border border-border">
                  {children}
                </table>
              </div>
            );
          },
          th({ children }) {
            return (
              <th className="border border-border bg-muted px-3 py-2 text-left font-semibold">
                {children}
              </th>
            );
          },
          td({ children }) {
            return (
              <td className="border border-border px-3 py-2">{children}</td>
            );
          },
          hr() {
            return <hr className="my-4 border-border" />;
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

interface CodeBlockProps {
  language: string;
  children: string;
}

function CodeBlock({ language, children }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(children);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group my-3 rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-zinc-800 text-zinc-400 text-xs">
        <span>{language}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 hover:text-zinc-200 transition-colors"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5" />
              <span>Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <SyntaxHighlighter
        style={oneDark}
        language={language}
        PreTag="div"
        customStyle={{
          margin: 0,
          borderRadius: 0,
          fontSize: "0.875rem",
        }}
      >
        {children}
      </SyntaxHighlighter>
    </div>
  );
}
