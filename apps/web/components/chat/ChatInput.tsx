"use client";

import { useState, useRef, FormEvent, KeyboardEvent } from "react";
import { Send, Loader2, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { AgentType } from "@/types/chat";
import { AGENTS } from "@/types/chat";

interface ChatInputProps {
  onSend: (message: string) => void;
  selectedAgent: AgentType;
  onAgentChange: (agent: AgentType) => void;
  isLoading?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  selectedAgent,
  onAgentChange,
  isLoading = false,
  placeholder = "Ask a question about your codebase...",
}: ChatInputProps) {
  const [input, setInput] = useState("");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentAgent = AGENTS.find((a) => a.type === selectedAgent);

  const handleSubmit = (e?: FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;

    onSend(input.trim());
    setInput("");

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  };

  const handleAgentSelect = (agentType: AgentType) => {
    onAgentChange(agentType);
    setIsDropdownOpen(false);
    textareaRef.current?.focus();
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <div className="relative flex items-end gap-2 p-3 border rounded-xl bg-background shadow-sm">
        {/* Agent Selector Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            type="button"
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className={cn(
              "flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg transition-colors",
              "border bg-muted/50 hover:bg-muted text-sm",
              "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1"
            )}
          >
            {currentAgent && (
              <currentAgent.Icon className="w-4 h-4 text-primary" />
            )}
            <span className="hidden sm:inline font-medium">
              {currentAgent?.label}
            </span>
            <ChevronDown
              className={cn(
                "w-3.5 h-3.5 text-muted-foreground transition-transform",
                isDropdownOpen && "rotate-180"
              )}
            />
          </button>

          {/* Dropdown Menu */}
          {isDropdownOpen && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setIsDropdownOpen(false)}
              />
              <div className="absolute bottom-full left-0 mb-2 z-20 w-64 py-1 bg-popover border rounded-lg shadow-lg">
                {AGENTS.map((agent) => (
                  <button
                    key={agent.type}
                    type="button"
                    onClick={() => handleAgentSelect(agent.type)}
                    className={cn(
                      "w-full flex items-center gap-3 px-3 py-2.5 text-left transition-colors",
                      "hover:bg-accent",
                      selectedAgent === agent.type && "bg-accent/50"
                    )}
                  >
                    <agent.Icon
                      className={cn(
                        "w-4 h-4",
                        selectedAgent === agent.type
                          ? "text-primary"
                          : "text-muted-foreground"
                      )}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium">{agent.label}</div>
                      <div className="text-xs text-muted-foreground truncate">
                        {agent.description}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>

        {/* Text Input */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder={placeholder}
          disabled={isLoading}
          rows={1}
          className={cn(
            "flex-1 resize-none bg-transparent outline-none",
            "placeholder:text-muted-foreground",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            "min-h-6 max-h-[200px] py-1.5"
          )}
        />

        {/* Send Button */}
        <Button
          type="submit"
          size="icon"
          disabled={!input.trim() || isLoading}
          className="shrink-0"
        >
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </Button>
      </div>
      <p className="text-xs text-muted-foreground mt-2 text-center">
        Press Enter to send, Shift+Enter for new line
      </p>
    </form>
  );
}
