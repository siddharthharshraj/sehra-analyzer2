"use client";

import { toast } from "sonner";
import { Copy, Trash2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { apiDelete } from "@/lib/api-client";
import type { ShareLink } from "@/lib/types";

interface ShareLinksTableProps {
  links: ShareLink[];
  onRefresh: () => void;
}

export function ShareLinksTable({ links, onRefresh }: ShareLinksTableProps) {
  async function handleRevoke(token: string) {
    try {
      await apiDelete(`/shares/${token}`);
      toast.success("Share link revoked");
      onRefresh();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to revoke",
      );
    }
  }

  function copyLink(token: string) {
    const url = `${window.location.origin}/share/${token}`;
    navigator.clipboard.writeText(url);
    toast.success("Link copied to clipboard");
  }

  if (links.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Active Share Links
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Token</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Expires</TableHead>
              <TableHead>Views</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-[100px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {links.map((link) => (
              <TableRow key={link.share_token}>
                <TableCell className="font-mono text-xs">
                  {link.share_token.slice(0, 12)}...
                </TableCell>
                <TableCell className="text-sm">
                  {link.created_at
                    ? new Date(link.created_at).toLocaleDateString()
                    : "-"}
                </TableCell>
                <TableCell className="text-sm">
                  {link.expires_at
                    ? new Date(link.expires_at).toLocaleDateString()
                    : "Never"}
                </TableCell>
                <TableCell>{link.view_count}</TableCell>
                <TableCell>
                  <Badge
                    variant={link.is_active ? "default" : "secondary"}
                  >
                    {link.is_active ? "Active" : "Revoked"}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => copyLink(link.share_token)}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                    {link.is_active && (
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleRevoke(link.share_token)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
