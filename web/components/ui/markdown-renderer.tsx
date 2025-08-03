import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import rehypeRaw from "rehype-raw";
import { ReactNode } from "react";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({
  content,
  className = "",
}: MarkdownRendererProps) {
  return (
    <div className={`prose prose-sm max-w-none dark:prose-invert ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight, rehypeRaw]}
        components={{
          // Custom heading styles
          h1: ({ children }: any) => (
            <h1 className="text-xl font-bold text-foreground mb-3 mt-4 first:mt-0">
              {children}
            </h1>
          ),
          h2: ({ children }: any) => (
            <h2 className="text-lg font-semibold text-foreground mb-2 mt-3 first:mt-0">
              {children}
            </h2>
          ),
          h3: ({ children }: any) => (
            <h3 className="text-base font-semibold text-foreground mb-2 mt-3 first:mt-0">
              {children}
            </h3>
          ),

          // Custom paragraph styles
          p: ({ children }: any) => (
            <p className="text-sm leading-relaxed text-card-foreground mb-3 last:mb-0">
              {children}
            </p>
          ),

          // Custom list styles
          ul: ({ children }: any) => (
            <ul className="list-disc pl-4 mb-3 space-y-1">{children}</ul>
          ),
          ol: ({ children }: any) => (
            <ol className="list-decimal pl-4 mb-3 space-y-1">{children}</ol>
          ),
          li: ({ children }: any) => (
            <li className="text-sm text-card-foreground">{children}</li>
          ),

          // Custom code styles
          code: ({ children, className, ...props }: any) => {
            const isInline = !className?.includes("language-");
            if (isInline) {
              return (
                <code
                  className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono text-primary"
                  {...props}
                >
                  {children}
                </code>
              );
            }
            return (
              <code
                className="block bg-muted p-3 rounded-lg text-xs font-mono overflow-x-auto"
                {...props}
              >
                {children}
              </code>
            );
          },

          // Custom blockquote styles
          blockquote: ({ children }: any) => (
            <blockquote className="border-l-4 border-primary/30 pl-4 py-2 my-3 bg-muted/50 rounded-r">
              {children}
            </blockquote>
          ),

          // Custom link styles
          a: ({ children, href }: any) => (
            <a
              href={href}
              className="text-primary hover:text-primary/80 underline underline-offset-2"
              target="_blank"
              rel="noopener noreferrer"
            >
              {children}
            </a>
          ),

          // Custom table styles
          table: ({ children }: any) => (
            <div className="overflow-x-auto my-3">
              <table className="min-w-full border border-border rounded-lg">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }: any) => (
            <thead className="bg-muted">{children}</thead>
          ),
          th: ({ children }: any) => (
            <th className="px-3 py-2 text-left text-xs font-semibold text-foreground border-b border-border">
              {children}
            </th>
          ),
          td: ({ children }: any) => (
            <td className="px-3 py-2 text-xs text-card-foreground border-b border-border">
              {children}
            </td>
          ),

          // Custom horizontal rule
          hr: () => <hr className="my-4 border-border" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
