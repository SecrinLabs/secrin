"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { User, Bot, Loader2, AlertCircle } from "lucide-react";
import { useChat } from "@/hooks/useChat";
import { MarkdownRenderer } from "@/components/ui/markdown-renderer";
import { AppPerameter } from "@/constants/AppPerameters";
import { Icons } from "../Icons";

interface Message {
  id: string;
  content: string;
  sender: "user" | "bot";
  timestamp: Date;
  isTyping?: boolean;
  isError?: boolean;
}

interface DevSecrinChatProps {
  className?: string;
}

export function DevSecrinChat({ className }: DevSecrinChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [hasStartedChat, setHasStartedChat] = useState(false);
  const [conversationId, setConversationId] = useState<string>("");
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Initialize chat hook
  const chat = useChat({
    onSuccess: (data) => {
      // Update conversation ID if provided
      if (data.conversation_id) {
        setConversationId(data.conversation_id);
      }

      // Add bot response to messages
      const botResponse: Message = {
        id: `bot_${Date.now()}`,
        content: data.answer,
        sender: "bot",
        timestamp: data.timestamp ? new Date(data.timestamp) : new Date(),
      };

      setMessages((prev) =>
        prev.filter((msg) => !msg.isTyping).concat(botResponse)
      );
    },
    onError: (error) => {
      // Remove typing indicator and add error message
      setMessages((prev) => prev.filter((msg) => !msg.isTyping));

      const errorMessage: Message = {
        id: `error_${Date.now()}`,
        content: `Sorry, I encountered an error: ${error.message}. Please try again.`,
        sender: "bot",
        timestamp: new Date(),
        isError: true,
      };

      setMessages((prev) => [...prev, errorMessage]);
    },
  });

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
    if (!inputValue.trim() || chat.isLoading) return;

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
        content: AppPerameter.welcomeBotMessage,
        sender: "bot",
        timestamp: new Date(),
      };
      setMessages([welcomeMessage, userMessage]);
      setHasStartedChat(true);
    } else {
      setMessages((prev) => [...prev, userMessage]);
    }

    const messageToSend = inputValue;
    setInputValue("");

    // Add typing indicator
    const typingMessage: Message = {
      id: "typing",
      content: AppPerameter.thinkingMessage,
      sender: "bot",
      timestamp: new Date(),
      isTyping: true,
    };
    setMessages((prev) => [...prev, typingMessage]);

    // Send message to API
    chat.sendMessage({
      question: messageToSend,
      conversation_id: conversationId || undefined,
    });
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
                    <Icons.logo />
                  </span>
                </div>
                <h1 className="text-4xl font-bold tracking-tight text-foreground">
                  {AppPerameter.appName}
                </h1>
              </div>
              <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
                {AppPerameter.whatCanIHelpWith}
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
                  disabled={chat.isLoading}
                />
              </div>
            </Card>

            {/* Quick suggestions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {[
                AppPerameter.landingPageQuestion1,
                AppPerameter.landingPageQuestion2,
                AppPerameter.landingPageQuestion3,
                AppPerameter.landingPageQuestion4,
              ].map((suggestion, index) => (
                <Button
                  key={index}
                  variant="outline"
                  className="h-auto p-4 text-left justify-start text-sm text-muted-foreground hover:text-foreground hover:bg-card border-border rounded-3xl"
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
          <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center">
            <span className="text-primary-foreground text-sm font-medium">
              <Icons.logo />
            </span>
          </div>
          <div className="min-w-0">
            <h1 className="text-lg font-medium tracking-tight text-foreground">
              {AppPerameter.appName}
            </h1>
            <p className="text-sm text-muted-foreground">
              {AppPerameter.appProfessionName}
            </p>
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
                      : message.isError
                      ? "bg-destructive/10 text-destructive border border-destructive/20"
                      : "bg-card text-card-foreground"
                  }`}
                >
                  {message.isTyping ? (
                    <p className="text-sm leading-relaxed">
                      <span className="flex items-center gap-2">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        {message.content}
                      </span>
                    </p>
                  ) : message.isError ? (
                    <p className="text-sm leading-relaxed">
                      <span className="flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 shrink-0" />
                        {message.content}
                      </span>
                    </p>
                  ) : message.sender === "bot" ? (
                    <MarkdownRenderer content={message.content} />
                  ) : (
                    <p className="text-sm leading-relaxed">{message.content}</p>
                  )}
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
                disabled={chat.isLoading}
              />
            </div>
          </Card>

          <p className="text-xs text-muted-foreground mt-3 text-center">
            {AppPerameter.footerImportantInfo}
          </p>
        </div>
      </div>
    </div>
  );
}
