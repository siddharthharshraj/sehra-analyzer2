"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Upload,
  ClipboardList,
  Settings,
  LogOut,
  Menu,
  Eye,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useAuth } from "@/hooks/use-auth";
import { useSidebarCollapsed } from "@/lib/sidebar-store";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/assessments", label: "Assessments", icon: LayoutDashboard },
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/collect", label: "Collect", icon: ClipboardList },
  { href: "/settings", label: "Settings", icon: Settings },
];

const adminItems = [
  { href: "/admin", label: "Manage Questions", icon: Settings },
];

function NavLink({
  href,
  label,
  icon: Icon,
  isActive,
  collapsed,
}: {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  isActive: boolean;
  collapsed: boolean;
}) {
  const link = (
    <Link
      href={href}
      className={cn(
        "flex items-center rounded-lg py-2.5 text-sm font-medium transition-colors",
        collapsed ? "justify-center px-2" : "gap-3 px-3",
        isActive
          ? "bg-white/20 text-white"
          : "text-white/70 hover:bg-white/10 hover:text-white",
      )}
    >
      <Icon className="h-4 w-4 shrink-0" />
      {!collapsed && label}
    </Link>
  );

  if (collapsed) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>{link}</TooltipTrigger>
        <TooltipContent side="right" sideOffset={8}>
          {label}
        </TooltipContent>
      </Tooltip>
    );
  }

  return link;
}

function NavContent({ collapsed }: { collapsed: boolean }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const isAdmin = user?.role === "admin";

  return (
    <div className="flex h-full flex-col">
      {/* Logo */}
      <div className={cn("py-6", collapsed ? "px-0 flex justify-center" : "px-6")}>
        <div className="flex items-center gap-2">
          <Eye className="h-6 w-6 shrink-0 text-white" />
          {!collapsed && (
            <div>
              <div className="text-sm font-bold tracking-wider text-white">
                SEHRA
              </div>
              <div className="text-[10px] tracking-widest text-white/70 uppercase">
                Analysis Platform
              </div>
            </div>
          )}
        </div>
      </div>

      <Separator className="bg-white/20" />

      {/* Navigation */}
      <nav className={cn("flex-1 space-y-1 py-4", collapsed ? "px-2" : "px-3")}>
        {navItems.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <NavLink
              key={item.href}
              href={item.href}
              label={item.label}
              icon={item.icon}
              isActive={isActive}
              collapsed={collapsed}
            />
          );
        })}

        {isAdmin && (
          <>
            <Separator className="my-3 bg-white/20" />
            {adminItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <NavLink
                  key={item.href}
                  href={item.href}
                  label={item.label}
                  icon={item.icon}
                  isActive={isActive}
                  collapsed={collapsed}
                />
              );
            })}
          </>
        )}
      </nav>

      {/* User info */}
      <div className={cn("border-t border-white/20 py-4", collapsed ? "px-2" : "px-4")}>
        {collapsed ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="mb-3 flex justify-center">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white/20 text-sm font-medium text-white">
                  {user?.name?.charAt(0)?.toUpperCase() || "?"}
                </div>
              </div>
            </TooltipTrigger>
            <TooltipContent side="right" sideOffset={8}>
              <p>{user?.name}</p>
              <p className="text-xs opacity-70">{user?.role}</p>
            </TooltipContent>
          </Tooltip>
        ) : (
          <div className="mb-3 px-2">
            <p className="text-sm font-medium text-white">{user?.name}</p>
            <p className="text-xs text-white/60">{user?.role}</p>
          </div>
        )}
        {collapsed ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                onClick={logout}
                className="w-full text-white/70 hover:bg-white/10 hover:text-white"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right" sideOffset={8}>
              Logout
            </TooltipContent>
          </Tooltip>
        ) : (
          <Button
            variant="ghost"
            size="sm"
            onClick={logout}
            className="w-full justify-start text-white/70 hover:bg-white/10 hover:text-white"
          >
            <LogOut className="mr-2 h-4 w-4" />
            Logout
          </Button>
        )}
      </div>
    </div>
  );
}

export function Sidebar() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const { collapsed, toggle } = useSidebarCollapsed();

  return (
    <TooltipProvider delayDuration={0}>
      {/* Desktop sidebar */}
      <aside
        className={cn(
          "hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:flex-col transition-all duration-200",
          collapsed ? "lg:w-16" : "lg:w-64",
        )}
        style={{
          background: "linear-gradient(180deg, #095456, #0D7377)",
        }}
      >
        <NavContent collapsed={collapsed} />

        {/* Collapse/Expand toggle */}
        <div className="border-t border-white/20 p-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={toggle}
            className={cn(
              "w-full text-white/70 hover:bg-white/10 hover:text-white",
              collapsed ? "justify-center" : "justify-start",
            )}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <>
                <ChevronLeft className="mr-2 h-4 w-4" />
                Collapse
              </>
            )}
          </Button>
        </div>
      </aside>

      {/* Mobile hamburger */}
      {mounted && (
        <div className="lg:hidden fixed top-0 left-0 z-50 p-4">
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="outline" size="icon">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent
              side="left"
              className="w-64 p-0 border-0"
              style={{
                background: "linear-gradient(180deg, #095456, #0D7377)",
              }}
            >
              <NavContent collapsed={false} />
            </SheetContent>
          </Sheet>
        </div>
      )}
    </TooltipProvider>
  );
}
