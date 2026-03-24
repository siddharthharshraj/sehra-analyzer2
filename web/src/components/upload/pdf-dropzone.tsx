"use client";

import { useCallback, useState } from "react";
import { Upload, FileText, X, AlertCircle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface PDFDropzoneProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

export function PDFDropzone({ onFileSelect, disabled }: PDFDropzoneProps) {
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState("");

  const validate = useCallback((f: File): string | null => {
    if (f.type !== "application/pdf" && !f.name.toLowerCase().endsWith(".pdf")) {
      return "Only PDF files are accepted. Please select a .pdf file.";
    }
    if (f.size > 50 * 1024 * 1024) {
      return `File is too large (${(f.size / 1024 / 1024).toFixed(1)} MB). Maximum size is 50 MB.`;
    }
    if (f.size === 0) {
      return "This file appears to be empty. Please select a valid PDF.";
    }
    return null;
  }, []);

  const handleFile = useCallback(
    (f: File) => {
      const err = validate(f);
      if (err) {
        setError(err);
        return;
      }
      setError("");
      setFile(f);
    },
    [validate],
  );

  return (
    <div className="space-y-3">
      <TooltipProvider delayDuration={400}>
      <Tooltip>
      <TooltipTrigger asChild>
      <Card
        className={`border-2 border-dashed transition-all duration-200 ${
          dragActive
            ? "border-[#0D7377] bg-[#0D7377]/5 shadow-lg shadow-[#0D7377]/10 scale-[1.01] drag-active-pulse"
            : error
              ? "border-red-300 hover:border-red-400"
              : "border-muted-foreground/25 hover:border-muted-foreground/50"
        } ${disabled ? "pointer-events-none opacity-50" : "cursor-pointer"}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
          const f = e.dataTransfer.files[0];
          if (f) handleFile(f);
        }}
        onClick={() => {
          if (disabled) return;
          const input = document.createElement("input");
          input.type = "file";
          input.accept = ".pdf";
          input.onchange = (e) => {
            const f = (e.target as HTMLInputElement).files?.[0];
            if (f) handleFile(f);
          };
          input.click();
        }}
      >
        <CardContent className="flex flex-col items-center gap-3 py-12">
          <div
            className={`flex h-14 w-14 items-center justify-center rounded-2xl transition-all duration-200 ${
              dragActive
                ? "bg-[#0D7377]/15 scale-110"
                : "bg-gray-100"
            }`}
          >
            <Upload
              className={`h-7 w-7 transition-all duration-200 ${
                dragActive
                  ? "text-[#0D7377] -translate-y-1"
                  : "text-muted-foreground"
              }`}
            />
          </div>
          <div className="text-center">
            <p className="font-medium">
              {dragActive
                ? "Drop your PDF here"
                : "Drag & drop your SEHRA PDF here"}
            </p>
            <p className="text-sm text-muted-foreground">
              or click to browse (PDF, max 50 MB)
            </p>
          </div>
        </CardContent>
      </Card>
      </TooltipTrigger>
      <TooltipContent side="bottom" className="max-w-[280px] text-sm">
        <p>Supports SEHRA PDF forms (both digital and scanned). Maximum file size: 50 MB. The system will automatically detect the format.</p>
      </TooltipContent>
      </Tooltip>
      </TooltipProvider>

      {/* Inline error with icon */}
      {error && (
        <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2.5">
          <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-medium text-red-800">Invalid file</p>
            <p className="text-xs text-red-600 mt-0.5">{error}</p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="ml-auto h-6 w-6 text-red-400 hover:text-red-600 hover:bg-red-100 shrink-0"
            onClick={(e) => {
              e.stopPropagation();
              setError("");
            }}
          >
            <X className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}

      {file && (
        <div className="flex items-center justify-between rounded-lg border p-3">
          <div className="flex items-center gap-3">
            <FileText className="h-5 w-5 text-[#0D7377]" />
            <div>
              <p className="text-sm font-medium">{file.name}</p>
              <p className="text-xs text-muted-foreground">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={(e) => {
                e.stopPropagation();
                setFile(null);
              }}
            >
              <X className="h-4 w-4" />
            </Button>
            <Button
              onClick={(e) => {
                e.stopPropagation();
                onFileSelect(file);
              }}
              className="bg-[#0D7377] hover:bg-[#095456]"
              disabled={disabled}
            >
              Analyze
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
