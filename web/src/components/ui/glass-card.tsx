"use client";

import { type ReactNode } from "react";

type GlowColor = "accent" | "green" | "red" | "yellow" | "orange" | "none";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  padding?: boolean;
  glow?: GlowColor;
}

export function GlassCard({
  children,
  className = "",
  hover = false,
  padding = true,
  glow = "none",
}: GlassCardProps) {
  const glowClass = glow !== "none" ? `glow-${glow}` : "";

  return (
    <div
      className={`glass-card ${hover ? "glass-card-hover" : ""} ${padding ? "p-5" : ""} ${glowClass} ${className}`}
    >
      {children}
    </div>
  );
}
