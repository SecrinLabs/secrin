"use client";

import { cn } from "@/lib/utils";
import type { ChatMessage, ContextItem } from "@/types/chat";
import { AGENTS } from "@/types/chat";
import { useState } from "react";
import { ChevronDown, ChevronUp, Code, User, Bot } from "lucide-react";

interface ChatMessageProps {
  message: ChatMessage;
}

export function ChatMessageItem({ message }: ChatMessageProps) {
  const [showContext, setShowContext] = useState(false);
  const isUser = message.role === "user";
  const agent = message.agentType
    ? AGENTS.find((a) => a.type === message.agentType)
    : null;

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
          <Bot className="w-4 h-4" />
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

        <div className="prose prose-sm dark:prose-invert max-w-none">
          <p className="whitespace-pre-wrap wrap-break-word">
            {message.content}
            {message.isStreaming && (
              <span className="inline-block w-2 h-4 ml-1 bg-primary animate-pulse" />
            )}
          </p>
        </div>

        {message.context && message.context.length > 0 && (
          <div className="mt-3">
            <button
              onClick={() => setShowContext(!showContext)}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              <Code className="w-3 h-3" />
              {message.context.length} context item
              {message.context.length > 1 ? "s" : ""}
              {showContext ? (
                <ChevronUp className="w-3 h-3" />
              ) : (
                <ChevronDown className="w-3 h-3" />
              )}
            </button>

            {showContext && (
              <div className="mt-2 space-y-2">
                {message.context.map((item, index) => (
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

function ContextItemCard({ item }: ContextItemCardProps) {
  const [expanded, setExpanded] = useState(false);
  const maxPreviewLength = 200;
  const needsExpansion = item.content.length > maxPreviewLength;

  return (
    <div className="border rounded-md overflow-hidden bg-muted/30">
      <div className="flex items-center justify-between px-3 py-2 bg-muted/50 border-b">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium px-2 py-0.5 rounded bg-primary/10 text-primary">
            {item.type}
          </span>
          <span className="text-sm font-mono">{item.name}</span>
        </div>
        {item.score !== undefined && (
          <span className="text-xs text-muted-foreground">
            Score: {(item.score * 100).toFixed(1)}%
          </span>
        )}
      </div>
      <div className="p-3">
        <pre className="text-xs overflow-x-auto whitespace-pre-wrap font-mono">
          {expanded || !needsExpansion
            ? item.content
            : `${item.content.slice(0, maxPreviewLength)}...`}
        </pre>
        {needsExpansion && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-primary hover:underline mt-2"
          >
            {expanded ? "Show less" : "Show more"}
          </button>
        )}
      </div>
    </div>
  );
}
