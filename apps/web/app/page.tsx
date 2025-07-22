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
    <div className="min-h-screen bg-gray-50 dark:bg-neutral-950 p-6 flex items-center justify-center">
      <div className="w-full max-w-4xl h-full max-h-[90vh]">
        <Card className="h-full flex flex-col shadow-2xl border border-gray-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 rounded-2xl overflow-hidden">
          <CardHeader className="flex-shrink-0 border-b border-gray-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-6">
            <CardTitle className="flex items-center gap-3 text-2xl font-semibold text-gray-900 dark:text-white">
              <div className="p-2 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600">
                <Bot className="h-6 w-6 text-white" />
              </div>
              Chat with DevSecrin
              <Badge
                variant="secondary"
                className="ml-auto bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-neutral-700 font-medium"
              >
                AI Assistant
              </Badge>
            </CardTitle>
          </CardHeader>

          <CardContent className="flex-1 flex flex-col p-0 min-h-0">
            <ScrollArea className="flex-1 min-h-0">
              <div className="p-6 space-y-6">
                {messages.length === 0 && (
                  <div className="text-center py-16">
                    <div className="p-4 rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600 w-fit mx-auto mb-6">
                      <Bot className="h-16 w-16 text-white" />
                    </div>
                    <h3 className="text-2xl font-semibold text-gray-900 dark:text-white mb-3">
                      Welcome to DevSecrin Chat
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400 text-lg max-w-md mx-auto">
                      Your intelligent DevOps assistant is ready to help. Ask
                      questions about security, development, or operations.
                    </p>
                  </div>
                )}

                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex gap-4 ${msg.type === "user" ? "justify-end" : "justify-start"}`}
                  >
                    {msg.type === "assistant" && (
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
                          <Bot className="h-5 w-5 text-white" />
                        </div>
                      </div>
                    )}

                    <div
                      className={`max-w-[75%] ${msg.type === "user" ? "order-1" : ""}`}
                    >
                      {msg.thinking && (
                        <div className="mt-2 mb-4">
                          <Collapsible>
                            <CollapsibleTrigger
                              className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800"
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
                            <CollapsibleContent className="mt-3">
                              <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-xl p-4 max-w-full">
                                <div className="text-sm text-orange-800 dark:text-orange-200 whitespace-pre-wrap break-words leading-relaxed">
                                  {msg.thinking}
                                </div>
                              </div>
                            </CollapsibleContent>
                          </Collapsible>
                        </div>
                      )}
                      <div
                        className={`rounded-2xl px-5 py-4 max-w-[85%] ${
                          msg.type === "user"
                            ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg"
                            : "bg-gray-100 dark:bg-neutral-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-neutral-700"
                        }`}
                      >
                        <div className="whitespace-pre-wrap break-words text-sm leading-relaxed">
                          {msg.content}
                        </div>
                      </div>

                      <div className="text-xs text-gray-500 dark:text-gray-400 mt-2 px-1">
                        {msg.timestamp.toLocaleTimeString()}
                      </div>
                    </div>

                    {msg.type === "user" && (
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 rounded-xl bg-gray-300 dark:bg-neutral-700 flex items-center justify-center shadow-lg">
                          <User className="h-5 w-5 text-gray-600 dark:text-gray-300" />
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {loading && (
                  <div className="flex gap-4 justify-start">
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
                        <Bot className="h-5 w-5 text-white" />
                      </div>
                    </div>
                    <div className="bg-gray-100 dark:bg-neutral-800 border border-gray-200 dark:border-neutral-700 rounded-2xl px-5 py-4">
                      <div className="flex items-center gap-3 text-gray-600 dark:text-gray-400">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        DevSecrin is thinking...
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>

            {error && (
              <div className="flex-shrink-0 p-6 border-t border-gray-200 dark:border-neutral-800">
                <Alert
                  variant="destructive"
                  className="border-red-200 dark:border-red-800"
                >
                  <AlertDescription className="text-red-800 dark:text-red-200">
                    {error}
                  </AlertDescription>
                </Alert>
              </div>
            )}

            <div className="flex-shrink-0 p-6 border-t border-gray-200 dark:border-neutral-800 bg-gray-50 dark:bg-neutral-900/50">
              <div className="flex gap-3">
                <Input
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Type your message..."
                  className="flex-1 bg-white dark:bg-neutral-800 border-gray-300 dark:border-neutral-600 focus:border-blue-500 dark:focus:border-blue-400 rounded-xl px-4 py-3 text-gray-900 dark:text-gray-100"
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
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 rounded-xl px-6 py-3 shadow-lg"
                >
                  {loading ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <Send className="h-5 w-5" />
                  )}
                </Button>
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-3 text-center">
                Press Enter to send • Powered by DevSecrin AI
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
