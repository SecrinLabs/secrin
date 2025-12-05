import type { LucideIcon } from "lucide-react";
import { Compass, History, Bug, LayoutGrid, ShieldCheck } from "lucide-react";

export type AgentType =
  | "pathfinder"
  | "chronicle"
  | "diagnostician"
  | "blueprint"
  | "sentinel";

export interface AgentInfo {
  type: AgentType;
  label: string;
  description: string;
  Icon: LucideIcon;
}

export const AGENTS: AgentInfo[] = [
  {
    type: "pathfinder",
    label: "Pathfinder",
    description: "Code structure & navigation",
    Icon: Compass,
  },
  {
    type: "chronicle",
    label: "Chronicle",
    description: "Commit history & evolution",
    Icon: History,
  },
  {
    type: "diagnostician",
    label: "Diagnostician",
    description: "Debugging & error analysis",
    Icon: Bug,
  },
  {
    type: "blueprint",
    label: "Blueprint",
    description: "Architecture reasoning",
    Icon: LayoutGrid,
  },
  {
    type: "sentinel",
    label: "Sentinel",
    description: "Code review & quality checks",
    Icon: ShieldCheck,
  },
];

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  agentType?: AgentType;
  isStreaming?: boolean;
  context?: ContextItem[];
}

export interface ContextItem {
  type: string;
  name: string;
  content: string;
  score?: number;
}

export interface ChatRequest {
  question: string;
  agent_type: AgentType;
  search_type: "vector" | "hybrid";
  context_limit: number;
  stream: boolean;
}

export interface StreamChunk {
  type: "context" | "answer_chunk" | "metadata" | "error";
  content?: string;
  context?: ContextItem[];
  metadata?: {
    model: string;
    provider: string;
    node_types: string[];
  };
  error?: string;
}
