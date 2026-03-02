"use client";

import { useState } from "react";
import { Eye, Lock } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface PasscodeFormProps {
  onSubmit: (passcode: string) => Promise<void>;
  error: string | null;
}

export function PasscodeForm({ onSubmit, error }: PasscodeFormProps) {
  const [passcode, setPasscode] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await onSubmit(passcode);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className="flex min-h-screen items-center justify-center px-4"
      style={{
        background: "linear-gradient(135deg, #095456 0%, #0D7377 50%, #10857A 100%)",
      }}
    >
      <Card className="w-full max-w-sm">
        <CardHeader className="space-y-4 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-[#0D7377]">
            <Eye className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">SEHRA Report</h1>
            <p className="text-sm text-muted-foreground">
              Enter the passcode to view this report
            </p>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="passcode">Passcode</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="passcode"
                  type="password"
                  value={passcode}
                  onChange={(e) => setPasscode(e.target.value)}
                  placeholder="Enter passcode"
                  className="pl-9"
                  required
                  autoFocus
                />
              </div>
            </div>
            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
            <Button
              type="submit"
              className="w-full bg-[#0D7377] hover:bg-[#095456]"
              disabled={loading}
            >
              {loading ? "Verifying..." : "View Report"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
