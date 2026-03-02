"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiPost } from "@/lib/api-client";
import type { ShareLink } from "@/lib/types";

interface ShareFormProps {
  sehraId: string;
  onCreated: () => void;
}

export function ShareForm({ sehraId, onCreated }: ShareFormProps) {
  const [passcode, setPasscode] = useState("");
  const [expiresDays, setExpiresDays] = useState("7");
  const [loading, setLoading] = useState(false);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!passcode) {
      toast.error("Passcode is required");
      return;
    }

    setLoading(true);
    try {
      await apiPost<ShareLink>("/shares", {
        sehra_id: sehraId,
        passcode,
        expires_days: parseInt(expiresDays) || null,
      });
      toast.success("Share link created");
      setPasscode("");
      onCreated();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to create share link",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Create Share Link
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleCreate} className="flex items-end gap-3">
          <div className="space-y-1.5">
            <Label htmlFor="passcode">Passcode</Label>
            <Input
              id="passcode"
              type="password"
              value={passcode}
              onChange={(e) => setPasscode(e.target.value)}
              placeholder="Set passcode"
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="expires">Expires (days)</Label>
            <Input
              id="expires"
              type="number"
              value={expiresDays}
              onChange={(e) => setExpiresDays(e.target.value)}
              className="w-24"
              min="1"
            />
          </div>
          <Button
            type="submit"
            disabled={loading}
            className="bg-[#0D7377] hover:bg-[#095456]"
          >
            Create
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
