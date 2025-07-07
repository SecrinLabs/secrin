"use client";

import { useState } from "react";

import { Input } from "@workspace/ui/components/input";
import { Button } from "@workspace/ui/components/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/card";
import { ScrollArea } from "@workspace/ui/components/scroll-area";
import { Alert, AlertDescription } from "@workspace/ui/components/alert";
import { Badge } from "@workspace/ui/components/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@workspace/ui/components/collapsible";
import {
  Send,
  Bot,
  User,
  Brain,
  ChevronDown,
  ChevronUp,
  Loader2,
} from "lucide-react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@workspace/ui/components/accordion";

interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  thinking?: string;
  timestamp: Date;
}

export default function ChatPage() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showThinking, setShowThinking] = useState<{ [key: string]: boolean }>(
    {}
  );

  async function handleSend() {
    if (!message.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: message,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setError("");
    setLoading(true);
    const currentMessage = message;
    setMessage("");

    try {
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: currentMessage }),
      });

      if (!res.ok) {
        setError("Failed to get response from the server.");
      } else {
        const data = await res.json();
        const answer = data?.answer || "";
        const thinkMatch = answer.match(/<think>([\s\S]*?)<\/think>/i);

        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: "assistant",
          content: thinkMatch
            ? answer.replace(/<think>[\s\S]*?<\/think>/i, "").trim()
            : answer,
          thinking: thinkMatch ? thinkMatch[1].trim() : undefined,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, assistantMessage]);
      }
    } catch (err) {
      setError("Network error. Please check your connection.");
    }

    setLoading(false);
  }

  const toggleThinking = (messageId: string) => {
    setShowThinking((prev) => ({
      ...prev,
      [messageId]: !prev[messageId],
    }));
  };

  return (
    <div className="h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 p-4 flex items-center justify-center">
      <div className="w-full max-w-4xl h-full max-h-[95vh]">
        <Card className="h-full flex flex-col shadow-xl border-0 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm">
          <CardHeader className="flex-shrink-0 border-b bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-t-lg">
            <CardTitle className="flex items-center gap-2 text-xl">
              <Bot className="h-6 w-6" />
              Chat with DevSecrin
              <Badge
                variant="secondary"
                className="ml-auto bg-white/20 text-white border-white/30"
              >
                AI Assistant
              </Badge>
            </CardTitle>
          </CardHeader>

          <CardContent className="flex-1 flex flex-col p-0 min-h-0">
            <ScrollArea className="flex-1 min-h-0">
              <div className="p-6 space-y-4">
                {messages.length === 0 && (
                  <div className="text-center py-12">
                    <Bot className="h-12 w-12 mx-auto text-slate-400 mb-4" />
                    <h3 className="text-lg font-medium text-slate-600 dark:text-slate-300 mb-2">
                      Welcome to DevSecrin Chat
                    </h3>
                    <p className="text-slate-500 dark:text-slate-400">
                      Start a conversation by typing your message below
                    </p>
                  </div>
                )}

                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex gap-3 ${msg.type === "user" ? "justify-end" : "justify-start"}`}
                  >
                    {msg.type === "assistant" && (
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center">
                          <Bot className="h-4 w-4 text-white" />
                        </div>
                      </div>
                    )}

                    <div
                      className={`max-w-[75%] ${msg.type === "user" ? "order-1" : ""}`}
                    >
                      {msg.thinking && (
                        <div className="mt-2 mb-2">
                          <Collapsible>
                            <CollapsibleTrigger
                              className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
                              onClick={() => toggleThinking(msg.id)}
                            >
                              <Brain className="h-4 w-4" />
                              Model thinking
                              {showThinking[msg.id] ? (
                                <ChevronUp className="h-4 w-4" />
                              ) : (
                                <ChevronDown className="h-4 w-4" />
                              )}
                            </CollapsibleTrigger>
                            <CollapsibleContent className="mt-2">
                              <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3 max-w-full">
                                <div className="text-sm text-amber-800 dark:text-amber-200 whitespace-pre-wrap break-words">
                                  {msg.thinking}
                                </div>
                              </div>
                            </CollapsibleContent>
                          </Collapsible>
                        </div>
                      )}
                      <div
                        className={`rounded-2xl px-4 py-3 ${
                          msg.type === "user"
                            ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white"
                            : "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                        }`}
                      >
                        <div className="whitespace-pre-wrap break-words text-sm leading-relaxed">
                          {msg.content}
                        </div>
                      </div>

                      <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                        {msg.timestamp.toLocaleTimeString()}
                      </div>
                    </div>

                    {msg.type === "user" && (
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 rounded-full bg-slate-300 dark:bg-slate-600 flex items-center justify-center">
                          <User className="h-4 w-4 text-slate-600 dark:text-slate-300" />
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {loading && (
                  <div className="flex gap-3 justify-start">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center">
                        <Bot className="h-4 w-4 text-white" />
                      </div>
                    </div>
                    <div className="bg-slate-100 dark:bg-slate-800 rounded-2xl px-4 py-3">
                      <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        DevSecrin is thinking...
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>

            {error && (
              <div className="flex-shrink-0 p-4 border-t">
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              </div>
            )}

            <div className="flex-shrink-0 p-4 border-t bg-slate-50 dark:bg-slate-800/50">
              <div className="flex gap-2">
                <Input
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Type your message..."
                  className="flex-1 bg-white dark:bg-slate-900"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !loading && message.trim()) {
                      handleSend();
                    }
                  }}
                  disabled={loading}
                />
                <Button
                  onClick={handleSend}
                  disabled={loading || !message.trim()}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 mt-2 text-center">
                Press Enter to send • Powered by DevSecrin AI
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
