"use client";

export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 px-3.5 py-2.5">
      <span className="typing-dot" />
      <span className="typing-dot" />
      <span className="typing-dot" />
    </div>
  );
}
