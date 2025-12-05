"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import Link from "next/link";
import { ArrowLeft, Trash2, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChatMessageItem, ChatInput } from "@/components/chat";
import { ChatService } from "@/services/chat.service";
import type { AgentType, ChatMessage, ContextItem } from "@/types/chat";
import { AGENTS } from "@/types/chat";

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<AgentType>("pathfinder");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSendMessage = async (content: string) => {
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content,
      timestamp: new Date(),
      agentType: selectedAgent,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    const assistantMessageId = crypto.randomUUID();
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      timestamp: new Date(),
      agentType: selectedAgent,
      isStreaming: true,
    };

    setMessages((prev) => [...prev, assistantMessage]);

    try {
      let fullContent = "";
      let context: ContextItem[] = [];

      for await (const chunk of ChatService.streamChat(content, selectedAgent, {
        searchType: "hybrid",
        contextLimit: 5,
      })) {
        if (chunk.type === "error") {
          throw new Error(chunk.error);
        }

        if (chunk.type === "context" && chunk.context) {
          context = chunk.context;
        }

        if (chunk.type === "answer_chunk" && chunk.content) {
          fullContent += chunk.content;

          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: fullContent, context }
                : msg
            )
          );
        }
      }

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, isStreaming: false, context }
            : msg
        )
      );
    } catch (error) {
      console.error("Chat error:", error);

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content:
                  error instanceof Error
                    ? `Error: ${error.message}`
                    : "An error occurred while processing your request.",
                isStreaming: false,
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages([]);
  };

  const currentAgent = AGENTS.find((a) => a.type === selectedAgent);

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 border-b bg-card">
        <div className="flex items-center gap-3">
          <Link href="/">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="w-4 h-4" />
            </Button>
          </Link>
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-primary" />
            <h1 className="text-lg font-semibold">Chat</h1>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleClearChat}
          disabled={messages.length === 0}
          title="Clear chat"
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-8">
            {currentAgent && (
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                <currentAgent.Icon className="w-8 h-8 text-primary" />
              </div>
            )}
            <h2 className="text-2xl font-bold mb-2">
              Ask anything about your codebase
            </h2>
            <p className="text-muted-foreground max-w-md mb-8">
              Use the dropdown in the input below to select an agent. Each agent
              specializes in different aspects of code analysis.
            </p>

            {/* Suggestion Cards */}
            <div className="w-full max-w-2xl">
              <p className="text-sm text-muted-foreground mb-3">Try asking:</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <SuggestionCard
                  text="How is the authentication flow structured?"
                  onClick={() =>
                    handleSendMessage(
                      "How is the authentication flow structured?"
                    )
                  }
                  disabled={isLoading}
                />
                <SuggestionCard
                  text="What are the main API endpoints?"
                  onClick={() =>
                    handleSendMessage("What are the main API endpoints?")
                  }
                  disabled={isLoading}
                />
                <SuggestionCard
                  text="Explain the database schema"
                  onClick={() =>
                    handleSendMessage("Explain the database schema")
                  }
                  disabled={isLoading}
                />
                <SuggestionCard
                  text="Find potential security issues"
                  onClick={() =>
                    handleSendMessage("Find potential security issues")
                  }
                  disabled={isLoading}
                />
              </div>
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto py-4 px-4 space-y-4">
            {messages.map((message) => (
              <ChatMessageItem key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t bg-card p-4">
        <div className="max-w-4xl mx-auto">
          <ChatInput
            onSend={handleSendMessage}
            selectedAgent={selectedAgent}
            onAgentChange={setSelectedAgent}
            isLoading={isLoading}
          />
        </div>
      </div>
    </div>
  );
}

interface SuggestionCardProps {
  text: string;
  onClick: () => void;
  disabled?: boolean;
}

function SuggestionCard({ text, onClick, disabled }: SuggestionCardProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="p-3 text-left text-sm border rounded-lg hover:bg-accent hover:border-primary/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {text}
    </button>
  );
}
