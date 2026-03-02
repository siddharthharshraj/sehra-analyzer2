"use client";

import { toast } from "sonner";
import { Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { apiDelete } from "@/lib/api-client";
import type { CodebookItem } from "@/lib/types";

interface CodebookTableProps {
  items: CodebookItem[];
  onRefresh: () => void;
}

export function CodebookTable({ items, onRefresh }: CodebookTableProps) {
  async function handleDelete(itemId: string) {
    try {
      await apiDelete(`/codebook/items/${itemId}`);
      toast.success("Question deleted");
      onRefresh();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to delete",
      );
    }
  }

  if (items.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-4">
        No questions in this section.
      </p>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Question</TableHead>
          <TableHead className="w-[100px]">Type</TableHead>
          <TableHead className="w-[80px]">Scoring</TableHead>
          <TableHead className="w-[80px]">Reverse</TableHead>
          <TableHead className="w-[60px]" />
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((item) => (
          <TableRow key={item.id}>
            <TableCell className="text-sm">{item.question}</TableCell>
            <TableCell>
              <Badge variant="secondary" className="text-xs">
                {item.type}
              </Badge>
            </TableCell>
            <TableCell className="text-sm">
              {item.has_scoring ? "Yes" : "No"}
            </TableCell>
            <TableCell className="text-sm">
              {item.is_reverse ? "Yes" : "No"}
            </TableCell>
            <TableCell>
              <Dialog>
                <DialogTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Delete Question</DialogTitle>
                    <DialogDescription>
                      Are you sure you want to delete this question? This
                      action cannot be undone.
                    </DialogDescription>
                  </DialogHeader>
                  <DialogFooter>
                    <Button
                      variant="destructive"
                      onClick={() => handleDelete(item.id)}
                    >
                      Delete
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
