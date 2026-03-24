"use client";

import React from "react";
import { AlertCircle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

export class CopilotErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-full p-6 text-center">
          <div className="mb-3 rounded-full bg-red-50 dark:bg-red-950/30 p-3">
            <AlertCircle className="h-6 w-6 text-red-500" />
          </div>
          <h3 className="mb-1 font-medium text-sm">Something went wrong</h3>
          <p className="mb-4 text-xs text-muted-foreground max-w-[240px]">
            The Copilot encountered an error. Try again or start a new conversation.
          </p>
          <Button
            onClick={this.handleRetry}
            variant="outline"
            size="sm"
            className="gap-1.5"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Try again
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}
