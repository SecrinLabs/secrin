import { cn } from "@/lib/utils";

interface ChatLayoutProps {
  children: React.ReactNode;
  className?: string;
}

export function ChatLayout({ children, className }: ChatLayoutProps) {
  return (
    <div className={cn("h-screen bg-background flex flex-col", className)}>
      {children}
    </div>
  );
}
