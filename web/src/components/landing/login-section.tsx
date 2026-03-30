"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Eye, BookOpen, LogIn } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/use-auth";
import { useInView } from "./use-in-view";

export function LoginSection() {
  const router = useRouter();
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { ref, isVisible } = useInView(0.1);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(username, password);
      router.push("/dashboard");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Invalid username or password",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section
      ref={ref}
      className="relative flex min-h-[80vh] flex-col items-center justify-center px-4 py-24"
      style={{
        background:
          "linear-gradient(135deg, #095456 0%, #0D7377 50%, #10857A 100%)",
      }}
    >
      {/* Subtle decorative element */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 h-80 w-[600px] rounded-full bg-white/[0.03] blur-3xl" />
      </div>

      <div
        className={`relative z-10 w-full max-w-sm transition-all duration-700 ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
      >
        <h2 className="text-center text-2xl font-bold text-white mb-2 sm:text-3xl">
          Ready to analyze?
        </h2>
        <p className="text-center text-sm text-white/60 mb-8">
          Sign in to your SEHRA Analyzer account
        </p>

        <Card className="w-full shadow-card-lg">
          <CardHeader className="space-y-4 text-center pb-2">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-[#0D7377]">
              <Eye className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-bold tracking-tight">SEHRA</h3>
              <p className="text-xs text-muted-foreground tracking-widest uppercase">
                Analysis Platform
              </p>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter your username"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                />
              </div>
              {error && (
                <p className="text-sm text-destructive">{error}</p>
              )}
              <Button
                type="submit"
                className="w-full bg-[#0D7377] hover:bg-[#095456]"
                disabled={loading}
              >
                {loading ? (
                  "Signing in..."
                ) : (
                  <>
                    <LogIn className="h-4 w-4 mr-2" />
                    Sign In
                  </>
                )}
              </Button>
            </form>
            <div className="mt-4 flex items-center justify-center gap-3 text-xs text-muted-foreground">
              <Link
                href="/docs"
                className="inline-flex items-center gap-1.5 hover:text-foreground transition-colors"
              >
                <BookOpen className="h-3.5 w-3.5" />
                Architecture Docs
              </Link>
              <span>·</span>
              <span>
                Built by{" "}
                <a
                  href="https://samanvayfoundation.org"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline hover:text-foreground transition-colors"
                >
                  Samanvay Foundation
                </a>
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
