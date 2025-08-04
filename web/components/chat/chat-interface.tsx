"use client";

import { useState, useRef, useEffect } from "react";
import { Send, User, Bot, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { AppPerameter } from "@/constants/AppPerameters";

interface Message {
  id: string;
  content: string;
  sender: "user" | "bot";
  timestamp: Date;
  isTyping?: boolean;
}

interface ChatInterfaceProps {
  className?: string;
}

export function ChatInterface({ className }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      content: AppPerameter.welcomeBotMessage,
      sender: "bot",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    // Simulate API call with typing indicator
    setTimeout(() => {
      const typingMessage: Message = {
        id: "typing",
        content: AppPerameter.thinkingMessage,
        sender: "bot",
        timestamp: new Date(),
        isTyping: true,
      };
      setMessages((prev) => [...prev, typingMessage]);
    }, 500);

    // Simulate bot response
    setTimeout(() => {
      setMessages((prev) => prev.filter((msg) => msg.id !== "typing"));

      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: generateBotResponse(userMessage.content),
        sender: "bot",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botResponse]);
      setIsLoading(false);
    }, 2000);
  };

  const generateBotResponse = (userInput: string): string => {
    const input = userInput.toLowerCase();

    if (input.includes("security") || input.includes("vulnerability")) {
      return "Security is paramount in software development. I recommend implementing defense-in-depth strategies, regular security audits, and following the OWASP guidelines. Would you like me to elaborate on any specific security domain?";
    }

    if (input.includes("password") || input.includes("authentication")) {
      return "For strong authentication: use multi-factor authentication, implement proper password policies (minimum 12 characters, complexity requirements), consider passwordless solutions, and ensure secure password storage with proper hashing algorithms like bcrypt or Argon2.";
    }

    if (input.includes("api") || input.includes("endpoint")) {
      return "API security best practices include: implementing proper authentication and authorization, input validation, rate limiting, HTTPS enforcement, API versioning, and comprehensive logging. Consider using API gateways for centralized security controls.";
    }

    return "I understand your concern. Based on current security best practices, I recommend following a structured approach to address this. Would you like me to provide specific guidance on implementation or point you to relevant security frameworks?";
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  };

  return (
    <div className={`flex flex-col h-screen bg-background ${className}`}>
      {/* Header - Fixed */}
      <header className="fixed top-0 left-0 right-0 z-10 shrink-0 border-b border-border/10 px-6 py-4 bg-background/95 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
            <span className="text-primary-foreground text-sm font-medium">
              D
            </span>
          </div>
          <div className="min-w-0">
            <h1 className="text-lg font-medium tracking-tight">DevSecrin</h1>
            <p className="text-sm text-muted-foreground">Security Assistant</p>
          </div>
        </div>
      </header>

      {/* Chat Messages */}
      <ScrollArea
        ref={scrollAreaRef}
        className="flex-1 px-6 overflow-y-auto"
        style={{ marginTop: "88px", marginBottom: "120px" }}
      >
        <div className="py-6 space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${
                message.sender === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {message.sender === "bot" && (
                <Avatar className="w-8 h-8 border border-border/20 shrink-0">
                  <AvatarFallback className="bg-primary text-primary-foreground">
                    {message.isTyping ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Bot className="w-4 h-4" />
                    )}
                  </AvatarFallback>
                </Avatar>
              )}

              <div
                className={`flex flex-col gap-1 max-w-[70%] ${
                  message.sender === "user" ? "items-end" : "items-start"
                }`}
              >
                <Card
                  className={`p-4 shadow-sm ${
                    message.sender === "user"
                      ? "bg-primary text-primary-foreground"
                      : message.isTyping
                      ? "bg-muted border-border/20"
                      : "bg-muted border-border/20"
                  }`}
                >
                  <p className="text-sm leading-relaxed">
                    {message.isTyping ? (
                      <span className="flex items-center gap-2">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        {message.content}
                      </span>
                    ) : (
                      message.content
                    )}
                  </p>
                </Card>

                <span className="text-xs text-muted-foreground px-1">
                  {formatTime(message.timestamp)}
                </span>
              </div>

              {message.sender === "user" && (
                <Avatar className="w-8 h-8 border border-border/20 shrink-0">
                  <AvatarFallback className="bg-secondary">
                    <User className="w-4 h-4" />
                  </AvatarFallback>
                </Avatar>
              )}
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* Input Area - Fixed */}
      <div className="fixed bottom-0 left-0 right-0 z-10 shrink-0 border-t border-border/10 px-6 py-4 bg-background/95 backdrop-blur-sm">
        <div className="flex gap-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about security best practices, vulnerabilities, or compliance..."
            className="flex-1 border-border/20 focus:border-border/40 bg-background"
            disabled={isLoading}
          />
          <Button
            onClick={handleSendMessage}
            size="icon"
            className="shrink-0"
            disabled={!inputValue.trim() || isLoading}
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </div>

        <p className="text-xs text-muted-foreground mt-2 px-1">
          Press Enter to send • Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
