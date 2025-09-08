"use client";

import * as React from "react";
import * as Switch from "@radix-ui/react-switch";
import { Moon, Sun } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "next-themes";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null; // render nothing on server

  const isDark = theme === "dark";

  return (
    <div className="px-2">
      <Switch.Root
        checked={isDark}
        onCheckedChange={(checked) => setTheme(checked ? "dark" : "light")}
        className={cn(
          "peer inline-flex h-6 w-12 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
          isDark ? "bg-primary" : "bg-gray-300"
        )}
      >
        <Switch.Thumb
          className={cn(
            "flex h-5 w-5 items-center justify-center rounded-full bg-white shadow-md transition-transform duration-300 data-[state=checked]:translate-x-6 data-[state=unchecked]:translate-x-0"
          )}
        >
          {isDark ? (
            <Moon className="h-3 w-3 text-gray-900" />
          ) : (
            <Sun className="h-3 w-3 text-yellow-400" />
          )}
        </Switch.Thumb>
      </Switch.Root>
    </div>
  );
}
