"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { User, Bot, Loader2 } from "lucide-react";

interface Message {
  id: string;
  content: string;
  sender: "user" | "bot";
  timestamp: Date;
  isTyping?: boolean;
}

interface DevSecrinChatProps {
  className?: string;
}

export function DevSecrinChat({ className }: DevSecrinChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [hasStartedChat, setHasStartedChat] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current && hasStartedChat) {
      const scrollContainer = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [messages, hasStartedChat]);

  // Focus textarea on mount
  useEffect(() => {
    if (textareaRef.current && !hasStartedChat) {
      textareaRef.current.focus();
    }
  }, [hasStartedChat]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: "user",
      timestamp: new Date(),
    };

    // If this is the first message, add welcome message first
    if (!hasStartedChat) {
      const welcomeMessage: Message = {
        id: "welcome",
        content:
          "Hello! I'm DevSecrin, your security assistant. I can help you with security best practices, vulnerability assessments, and secure development guidelines.",
        sender: "bot",
        timestamp: new Date(),
      };
      setMessages([welcomeMessage, userMessage]);
      setHasStartedChat(true);
    } else {
      setMessages((prev) => [...prev, userMessage]);
    }

    setInputValue("");
    setIsLoading(true);

    // Simulate API call with typing indicator
    setTimeout(() => {
      const typingMessage: Message = {
        id: "typing",
        content: "DevSecrin is thinking...",
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
    // Shift+Enter will naturally create a new line
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  };

  // Landing page view (before first message)
  if (!hasStartedChat) {
    return (
      <div
        className={`flex flex-col h-full bg-background transition-all duration-700 ease-in-out ${className}`}
      >
        {/* Centered content */}
        <div className="flex-1 flex items-center justify-center px-6">
          <div className="w-full max-w-3xl space-y-8">
            {/* Header */}
            <div className="text-center space-y-6">
              <div className="flex items-center justify-center gap-4 mb-8">
                <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center">
                  <span className="text-primary-foreground text-lg font-bold">
                    D
                  </span>
                </div>
                <h1 className="text-4xl font-bold tracking-tight text-foreground">
                  DevSecrin
                </h1>
              </div>
              <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
                What can I help with?
              </p>
            </div>

            {/* Input area */}
            <Card className="bg-card border-border shadow-lg rounded-3xl py-0">
              <div className="p-4">
                <Textarea
                  ref={textareaRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask anything"
                  className="min-h-[20px] max-h-[200px] resize-none border-0 bg-transparent focus-visible:ring-0 text-base leading-relaxed placeholder:text-muted-foreground"
                  disabled={isLoading}
                />
              </div>
            </Card>

            {/* Quick suggestions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {[
                "What are the OWASP Top 10 vulnerabilities?",
                "How to implement secure authentication?",
                "Best practices for API security",
                "Guide for secure code review process",
              ].map((suggestion, index) => (
                <Button
                  key={index}
                  variant="outline"
                  className="h-auto p-4 text-left justify-start text-sm text-muted-foreground hover:text-foreground hover:bg-card border-border"
                  onClick={() => setInputValue(suggestion)}
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Chat interface view (after first message)
  return (
    <div
      className={`flex flex-col h-full bg-background transition-all duration-700 ease-in-out ${className}`}
    >
      {/* Header */}
      <header className="shrink-0 border-b border-border px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
            <span className="text-primary-foreground text-sm font-medium">
              D
            </span>
          </div>
          <div className="min-w-0">
            <h1 className="text-lg font-medium tracking-tight text-foreground">
              DevSecrin
            </h1>
            <p className="text-sm text-muted-foreground">Security Assistant</p>
          </div>
        </div>
      </header>

      {/* Chat Messages */}
      <ScrollArea ref={scrollAreaRef} className="flex-1 p-6">
        <div className="max-w-4xl mx-auto">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-4 animate-in slide-in-from-bottom-4 duration-500 ${
                message.sender === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {message.sender === "bot" && (
                <Avatar className="w-8 h-8 shrink-0">
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
                className={`flex flex-col gap-2 max-w-[70%] ${
                  message.sender === "user" ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`rounded-2xl px-4 py-3 ${
                    message.sender === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-card text-card-foreground"
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
                </div>

                <span className="text-xs text-muted-foreground px-2">
                  {formatTime(message.timestamp)}
                </span>
              </div>

              {message.sender === "user" && (
                <Avatar className="w-8 h-8 shrink-0">
                  <AvatarFallback className="bg-secondary text-secondary-foreground">
                    <User className="w-4 h-4" />
                  </AvatarFallback>
                </Avatar>
              )}
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* Input Area - Now at bottom */}
      <div className="shrink-0 border-t border-border px-6 py-4">
        <div className="max-w-4xl mx-auto">
          <Card className="bg-card border-border rounded-3xl p-0">
            <div className="px-4 py-3">
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask anything"
                className="border-0 bg-transparent focus-visible:ring-0 text-base h-auto py-2"
                disabled={isLoading}
              />
            </div>
          </Card>

          <p className="text-xs text-muted-foreground mt-3 text-center">
            DevSecrin can make mistakes. Check important info. • Press Enter to
            send • Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  );
}
