"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { Bot, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useCopilotContext } from "@/components/copilot/copilot-context";
import { useAuth } from "@/hooks/use-auth";

const pageTitles: Record<string, string> = {
  "/assessments": "Assessments",
  "/upload": "Upload",
  "/collect": "Collect",
  "/settings": "Settings",
  "/admin": "Manage Questions",
};

export function Header() {
  const pathname = usePathname();
  const { toggle, isOpen, sehraLabel } = useCopilotContext();
  const { user, logout } = useAuth();

  const isAssessmentDetail = /^\/assessments\/[^/]+$/.test(pathname);

  let title: string;
  if (isAssessmentDetail && sehraLabel) {
    title = sehraLabel;
  } else {
    title = pageTitles[pathname] || "SEHRA";
  }

  const initials = user?.name
    ? user.name
        .split(" ")
        .map((w) => w[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "?";

  return (
    <header className="sticky top-0 z-40 border-b border-gray-200/50 bg-white/80 backdrop-blur-xl">
      <div className="flex h-14 items-center justify-between px-6">
        <div>
          {isAssessmentDetail ? (
            <nav className="flex items-center gap-1.5 text-sm">
              <Link
                href="/assessments"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Assessments
              </Link>
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="font-semibold text-foreground">{title}</span>
            </nav>
          ) : (
            <div>
              <h1 className="text-lg font-semibold tracking-tight">{title}</h1>
              <p className="text-[10px] text-muted-foreground -mt-0.5">
                School Eye Health Rapid Assessment
              </p>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Copilot toggle */}
          <TooltipProvider delayDuration={300}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggle}
                  className={`gap-1.5 rounded-lg transition-colors ${
                    isOpen
                      ? "bg-[#0D7377]/10 text-[#0D7377]"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Bot className="h-4 w-4" />
                  <span className="hidden sm:inline text-sm">Copilot</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-[280px] text-xs">
                <p>Open AI Copilot &mdash; ask questions, edit analysis, export reports using natural language</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          {/* User avatar dropdown */}
          {user && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="relative h-8 w-8 rounded-full"
                  title={`${user.name} (${user.role})`}
                >
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-[#0D7377] text-white text-xs font-medium">
                      {initials}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuLabel className="font-normal">
                  <p className="text-sm font-medium">{user.name}</p>
                  <p className="text-xs text-muted-foreground">{user.role}</p>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link href="/settings">Settings</Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={logout}
                  className="text-red-600 focus:text-red-600"
                >
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </div>
    </header>
  );
}
