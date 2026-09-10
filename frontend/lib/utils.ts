import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const DAY_LABELS: Record<string, string> = {
  Monday: "E hënë",
  Tuesday: "E martë",
  Wednesday: "E mërkurë",
  Thursday: "E enjte",
  Friday: "E premte",
  Saturday: "E shtunë",
  Sunday: "E diel",
};

export const DAY_ORDER = Object.keys(DAY_LABELS);

/** "09:00:00" -> "09:00" */
export function formatTime(value: string): string {
  return value.slice(0, 5);
}

export function formatDate(value: string): string {
  return new Date(value).toLocaleDateString("sq-AL", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

export function formatDateTime(value: string): string {
  return new Date(value).toLocaleString("sq-AL", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Ditë deri te një datë; negative kur data ka kaluar. */
export function daysUntil(value: string): number {
  const target = new Date(value).getTime();

  return Math.ceil((target - Date.now()) / (1000 * 60 * 60 * 24));
}

export function initials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

export function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}
