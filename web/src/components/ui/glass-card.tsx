"use client";

import { type ReactNode } from "react";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  padding?: boolean;
}

export function GlassCard({
  children,
  className = "",
  hover = false,
  padding = true,
}: GlassCardProps) {
  return (
    <div
      className={`glass-card ${hover ? "glass-card-hover" : ""} ${padding ? "p-5" : ""} ${className}`}
    >
      {children}
    </div>
  );
}
