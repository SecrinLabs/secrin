"use client";

import { cn } from "@/lib/utils";
import type { ChatMessage, ContextItem } from "@/types/chat";
import { AGENTS } from "@/types/chat";
import { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  Code,
  User,
  FileCode,
  Box,
  GitCommit,
  File,
} from "lucide-react";
import { MarkdownRenderer } from "./MarkdownRenderer";

interface ChatMessageProps {
  message: ChatMessage;
}

export function ChatMessageItem({ message }: ChatMessageProps) {
  const [showContext, setShowContext] = useState(false);
  const isUser = message.role === "user";
  const agent = message.agentType
    ? AGENTS.find((a) => a.type === message.agentType)
    : null;

  // Filter out empty context items
  const validContext = message.context?.filter(
    (item) =>
      item.name && item.name !== "N/A" && item.content && item.content.trim()
  );

  return (
    <div
      className={cn(
        "flex gap-3 p-4 rounded-lg",
        isUser ? "bg-muted/50" : "bg-background"
      )}
    >
      <div
        className={cn(
          "shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-secondary text-secondary-foreground"
        )}
      >
        {isUser ? (
          <User className="w-4 h-4" />
        ) : agent ? (
          <agent.Icon className="w-4 h-4" />
        ) : (
          <Code className="w-4 h-4" />
        )}
      </div>

      <div className="flex-1 min-w-0 space-y-2">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">
            {isUser ? "You" : agent?.label || "Assistant"}
          </span>
          {agent && !isUser && (
            <span className="text-xs text-muted-foreground">
              {agent.description}
            </span>
          )}
          <span className="text-xs text-muted-foreground ml-auto">
            {message.timestamp.toLocaleTimeString()}
          </span>
        </div>

        {isUser ? (
          <p className="whitespace-pre-wrap overflow-wrap-anywhere">
            {message.content}
          </p>
        ) : (
          <div className="relative">
            <MarkdownRenderer content={message.content} />
            {message.isStreaming && (
              <span className="inline-block w-2 h-4 ml-1 bg-primary animate-pulse" />
            )}
          </div>
        )}

        {validContext && validContext.length > 0 && (
          <div className="mt-4 pt-3 border-t border-border/50">
            <button
              onClick={() => setShowContext(!showContext)}
              className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-muted/50 hover:bg-muted transition-colors">
                <FileCode className="w-3.5 h-3.5" />
                <span className="font-medium">
                  {validContext.length} source
                  {validContext.length > 1 ? "s" : ""}
                </span>
                {showContext ? (
                  <ChevronUp className="w-3.5 h-3.5" />
                ) : (
                  <ChevronDown className="w-3.5 h-3.5" />
                )}
              </div>
            </button>

            {showContext && (
              <div className="mt-3 space-y-2">
                {validContext.map((item, index) => (
                  <ContextItemCard key={index} item={item} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

interface ContextItemCardProps {
  item: ContextItem;
}

function getContextIcon(type: string) {
  switch (type?.toLowerCase()) {
    case "function":
      return <Code className="w-3 h-3" />;
    case "class":
      return <Box className="w-3 h-3" />;
    case "commit":
      return <GitCommit className="w-3 h-3" />;
    case "file":
      return <File className="w-3 h-3" />;
    default:
      return <FileCode className="w-3 h-3" />;
  }
}

function ContextItemCard({ item }: ContextItemCardProps) {
  const [expanded, setExpanded] = useState(false);
  const maxPreviewLength = 300;
  const content = item.content || "";
  const needsExpansion = content.length > maxPreviewLength;

  return (
    <div className="group rounded-lg border border-border/60 bg-muted/30 overflow-hidden hover:border-border transition-colors">
      <div className="flex items-center justify-between px-3 py-2 bg-muted/50">
        <div className="flex items-center gap-2 min-w-0">
          <div className="flex items-center gap-1.5 shrink-0 text-muted-foreground">
            {getContextIcon(item.type)}
            <span className="text-xs font-medium uppercase tracking-wide">
              {item.type || "Code"}
            </span>
          </div>
          <span className="text-xs text-muted-foreground/60">•</span>
          <span className="text-xs font-mono text-foreground/80 truncate">
            {item.name}
          </span>
        </div>
        {item.score !== undefined && item.score > 0 && (
          <span className="text-[10px] font-medium text-muted-foreground bg-background/50 px-1.5 py-0.5 rounded shrink-0 ml-2">
            {(item.score * 100).toFixed(0)}%
          </span>
        )}
      </div>

      <div className="px-3 py-2 bg-background/50">
        <pre className="text-xs overflow-x-auto whitespace-pre-wrap font-mono text-foreground/70 leading-relaxed">
          {expanded || !needsExpansion
            ? content
            : `${content.slice(0, maxPreviewLength)}...`}
        </pre>
        {needsExpansion && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-primary/80 hover:text-primary hover:underline mt-2 font-medium"
          >
            {expanded ? "Show less" : "Show more"}
          </button>
        )}
      </div>
    </div>
  );
}
