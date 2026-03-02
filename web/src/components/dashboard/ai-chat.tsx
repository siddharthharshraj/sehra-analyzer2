"use client";

import { useState, useRef, useEffect } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageSquare, Send } from "lucide-react";
import { useChat } from "@/hooks/use-chat";
import { TEAL, RED } from "@/lib/constants";
import type { ChartSpec } from "@/lib/types";

const CHART_COLORS = [TEAL, "#10857A", "#14967E", "#18A781", "#1CB885", RED];

interface AIChatProps {
  sehraId: string;
}

function MiniChart({ spec }: { spec: ChartSpec }) {
  if (spec.type === "bar") {
    return (
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={spec.data}>
          <XAxis dataKey="label" tick={{ fontSize: 10 }} />
          <YAxis />
          <Tooltip />
          <Bar dataKey="value" fill={TEAL} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    );
  }

  if (spec.type === "pie") {
    return (
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie
            data={spec.data}
            dataKey="value"
            nameKey="label"
            cx="50%"
            cy="50%"
            outerRadius={80}
            label={({ name }) => name as string}
          >
            {spec.data.map((_, i) => (
              <Cell
                key={i}
                fill={CHART_COLORS[i % CHART_COLORS.length]}
              />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    );
  }

  if (spec.type === "radar") {
    return (
      <ResponsiveContainer width="100%" height={200}>
        <RadarChart data={spec.data}>
          <PolarGrid />
          <PolarAngleAxis dataKey="label" tick={{ fontSize: 10 }} />
          <Radar dataKey="value" stroke={TEAL} fill={TEAL} fillOpacity={0.3} />
          <Tooltip />
        </RadarChart>
      </ResponsiveContainer>
    );
  }

  return null;
}

export function AIChat({ sehraId }: AIChatProps) {
  const { messages, isLoading, sendMessage } = useChat();
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleSend() {
    if (!input.trim() || isLoading) return;
    sendMessage(input.trim(), sehraId);
    setInput("");
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          <MessageSquare className="h-4 w-4" />
          AI Assistant
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[300px] pr-4">
          {messages.length === 0 && (
            <p className="text-sm text-muted-foreground">
              Ask questions about this SEHRA assessment...
            </p>
          )}
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`mb-3 ${
                msg.role === "user" ? "text-right" : "text-left"
              }`}
            >
              <div
                className={`inline-block max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                  msg.role === "user"
                    ? "bg-[#0D7377] text-white"
                    : "bg-muted"
                }`}
              >
                {msg.text}
                {msg.chart && (
                  <div className="mt-2">
                    <MiniChart spec={msg.chart} />
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="mb-3 text-left">
              <div className="inline-block rounded-lg bg-muted px-3 py-2 text-sm text-muted-foreground">
                Thinking...
              </div>
            </div>
          )}
          <div ref={scrollRef} />
        </ScrollArea>

        <div className="mt-3 flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about this assessment..."
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            disabled={isLoading}
          />
          <Button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="bg-[#0D7377] hover:bg-[#095456] px-3"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
