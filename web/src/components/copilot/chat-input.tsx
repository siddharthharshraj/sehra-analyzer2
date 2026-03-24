"use client";

import { useState } from "react";
import { Send, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  sehraId: string | null;
  sehraLabel: string | null;
  isStreaming: boolean;
  onSend: (message: string) => void;
  onCancel: () => void;
}

export function ChatInput({ sehraId, sehraLabel, isStreaming, onSend, onCancel }: ChatInputProps) {
  const [input, setInput] = useState("");

  function handleSend() {
    if (!input.trim() || isStreaming) return;
    onSend(input.trim());
    setInput("");
  }

  return (
    <div className="p-3 shrink-0 bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60">
      <div className="flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            sehraId
              ? `Ask about ${sehraLabel || "this assessment"}...`
              : "Ask anything..."
          }
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
          disabled={isStreaming}
          className={cn(
            "text-sm transition-all rounded-xl",
            isStreaming && "opacity-60 border-[#0D7377]/40",
          )}
        />
        {isStreaming ? (
          <TooltipProvider delayDuration={300}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  onClick={onCancel}
                  variant="outline"
                  size="icon"
                  className="shrink-0 rounded-xl"
                >
                  <Square className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="top" className="text-xs">Stop generating</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        ) : (
          <Button
            onClick={handleSend}
            disabled={!input.trim()}
            className="shrink-0 bg-gradient-to-br from-[#0D7377] to-[#095456] hover:from-[#095456] hover:to-[#073b3d] rounded-xl shadow-sm"
            size="icon"
          >
            <Send className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
}
