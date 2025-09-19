"use client";

import { type LucideIcon } from "lucide-react";

import { Collapsible, CollapsibleTrigger } from "@/components/ui/collapsible";
import {
  SidebarGroup,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import Link from "next/link";

export function NavMain({
  items,
}: {
  items: {
    title: string;
    url: string;
    icon?: LucideIcon;
    isActive?: boolean;
    items?: {
      title: string;
      url: string;
    }[];
  }[];
}) {
  return (
    <SidebarGroup>
      <SidebarMenu className="space-y-1">
        {items.map((item) => (
          <Collapsible
            key={item.title}
            asChild
            defaultOpen={item.isActive}
            className="group/collapsible"
          >
            <SidebarMenuItem>
              <CollapsibleTrigger className="cursor-pointer" asChild>
                <Link href={item.url}>
                  <SidebarMenuButton
                    tooltip={item.title}
                    className={`
                      flex items-center gap-3 px-6 py-6 transition
                      text-base font-medium
                      hover:bg-muted
                      ${item.isActive ? "bg-muted" : "text-foreground"}
                    `}
                  >
                    {item.icon && (
                      <item.icon
                        className={`"h-5 w-5 text-muted-foreground group-hover/collapsible:text-primary"`}
                      />
                    )}
                    <span className="text-lg">{item.title}</span>
                  </SidebarMenuButton>
                </Link>
              </CollapsibleTrigger>
            </SidebarMenuItem>
          </Collapsible>
        ))}
      </SidebarMenu>
    </SidebarGroup>
  );
}
