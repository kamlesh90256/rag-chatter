"use client";

import { MoonStar, SunMedium } from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";

export function AppShell({ children }: { children: ReactNode }) {
  const [dark, setDark] = useState(true);

  useEffect(() => {
    const saved = window.localStorage.getItem("rag-theme");
    const nextDark = saved ? saved === "dark" : true;
    setDark(nextDark);
    document.documentElement.classList.toggle("light", !nextDark);
  }, []);

  const toggleTheme = () => {
    setDark((current) => {
      const next = !current;
      window.localStorage.setItem("rag-theme", next ? "dark" : "light");
      document.documentElement.classList.toggle("light", !next);
      return next;
    });
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(20,184,166,0.14),_transparent_22%),radial-gradient(circle_at_bottom_right,_rgba(59,130,246,0.14),_transparent_28%),linear-gradient(180deg,_rgba(4,7,13,1),_rgba(3,5,10,1))] text-foreground">
      <header className="sticky top-0 z-20 border-b border-white/10 bg-black/30 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-emerald-300/80">Creator Video Intelligence</p>
            <h1 className="font-display text-2xl font-semibold tracking-tight">RAG Platform</h1>
          </div>
          <Button variant="outline" onClick={toggleTheme} className="border-white/10 bg-white/5 text-sm text-white hover:bg-white/10">
            {dark ? <SunMedium className="h-4 w-4" /> : <MoonStar className="h-4 w-4" />}
            {dark ? "Light mode" : "Dark mode"}
          </Button>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
}
