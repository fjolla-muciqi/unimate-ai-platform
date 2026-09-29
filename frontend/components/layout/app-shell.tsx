"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  BarChart3,
  BookOpen,
  CalendarDays,
  FileText,
  GraduationCap,
  LayoutDashboard,
  Loader2,
  LogOut,
  MessageSquare,
  Presentation,
  Settings2,
  UserCog,
  ShieldCheck,
  Users,
} from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ApiError, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { UserRole } from "@/lib/types";
import { cn, initials } from "@/lib/utils";

interface NavItem {
  href: string;
  label: string;
  icon: typeof LayoutDashboard;

  /** Bosh do të thotë: i dukshëm për çdo rol. */
  roles?: UserRole[];
}

const NAV_ITEMS: NavItem[] = [
  {
    href: "/dashboard",
    label: "Paneli",
    icon: LayoutDashboard,
    roles: ["STUDENT"],
  },
  {
    href: "/courses",
    label: "Lëndët e mia",
    icon: BookOpen,
    roles: ["STUDENT"],
  },
  {
    href: "/schedule",
    label: "Orari",
    icon: CalendarDays,
    roles: ["STUDENT"],
  },
  {
    href: "/exams",
    label: "Provimet",
    icon: GraduationCap,
    roles: ["STUDENT"],
  },
  {
    href: "/teaching",
    label: "Ligjëratat e mia",
    icon: Presentation,
    roles: ["PROFESSOR"],
  },
  {
    href: "/teaching/students",
    label: "Studentët e mi",
    icon: Users,
    roles: ["PROFESSOR"],
  },
  { href: "/chat", label: "Asistenti AI", icon: MessageSquare },
  { href: "/documents", label: "Dokumentet", icon: FileText },
  {
    href: "/admin",
    label: "Administrimi",
    icon: ShieldCheck,
    roles: ["ADMIN"],
  },
  {
    href: "/admin/students",
    label: "Studentët",
    icon: GraduationCap,
    roles: ["ADMIN"],
  },
  {
    href: "/admin/manage",
    label: "Menaxhimi",
    icon: Settings2,
    roles: ["ADMIN"],
  },
  {
    href: "/analytics",
    label: "Analitika",
    icon: BarChart3,
    roles: ["ADMIN"],
  },
  { href: "/profile", label: "Profili im", icon: UserCog },
];

const ROLE_LABELS: Record<UserRole, string> = {
  STUDENT: "Student",
  ADMIN: "Administrator",
  PROFESSOR: "Profesor",
};

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  // Studenti i sapo regjistruar nuk ka ende profil akademik, dhe pa të
  // asnjë faqe studenti nuk ka të dhëna. Kontrollohet një herë pas
  // kyçjes; `null` do të thotë "ende pa u kontrolluar".
  const [hasProfile, setHasProfile] = useState<boolean | null>(null);

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  useEffect(() => {
    if (!user) {
      return;
    }

    if (user.role !== "STUDENT") {
      setHasProfile(true);

      return;
    }

    api
      .myProfile()
      .then(() => setHasProfile(true))
      .catch((caught) =>
        // Vetëm 404 do të thotë "pa profil"; gabimet e tjera i shfaq
        // vetë faqja, si më parë.
        setHasProfile(!(caught instanceof ApiError && caught.status === 404)),
      );
  }, [user]);

  const onOnboarding = pathname === "/onboarding";

  useEffect(() => {
    if (hasProfile === false && !onOnboarding) {
      router.replace("/onboarding");
    }

    if (hasProfile === true && onOnboarding) {
      router.replace("/dashboard");
    }
  }, [hasProfile, onOnboarding, router]);

  const redirecting =
    (hasProfile === false && !onOnboarding) ||
    (hasProfile === true && onOnboarding);

  if (loading || !user || hasProfile === null || redirecting) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const visible = NAV_ITEMS.filter(
    (item) => !item.roles || item.roles.includes(user.role),
  );

  // Vetëm lidhja më specifike theksohet: te /admin/manage ndizet
  // "Menaxhimi", jo edhe "Administrimi".
  const activeHref = visible
    .filter(
      (item) =>
        pathname === item.href || pathname.startsWith(`${item.href}/`),
    )
    .reduce<string | null>(
      (best, item) =>
        best === null || item.href.length > best.length ? item.href : best,
      null,
    );

  const fullName = `${user.first_name} ${user.last_name}`;

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="hidden w-64 shrink-0 flex-col border-r bg-card lg:flex">
        <div className="flex h-16 items-center gap-2 border-b px-6">
          <div className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <GraduationCap className="size-5" />
          </div>
          <span className="text-lg font-semibold tracking-tight">
            UniMate AI
          </span>
        </div>

        <nav className="flex-1 space-y-1 p-3">
          {visible.map((item) => {
            const active = item.href === activeHref;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground",
                )}
              >
                <item.icon className="size-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t p-3">
          <div className="flex items-center gap-3 rounded-md px-3 py-2">
            <Avatar>
              <AvatarFallback>{initials(fullName)}</AvatarFallback>
            </Avatar>

            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{fullName}</p>
              <p className="truncate text-xs text-muted-foreground">
                {user.email}
              </p>
            </div>
          </div>

          <Button
            variant="ghost"
            className="mt-1 w-full justify-start text-muted-foreground"
            onClick={logout}
          >
            <LogOut className="size-4" />
            Dil
          </Button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center justify-between gap-4 border-b bg-card px-4 lg:px-8">
          <div className="flex items-center gap-2 lg:hidden">
            <div className="flex size-7 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <GraduationCap className="size-4" />
            </div>
            <span className="font-semibold">UniMate AI</span>
          </div>

          <div className="hidden lg:block" />

          <div className="flex items-center gap-3">
            <Badge variant="secondary">{ROLE_LABELS[user.role]}</Badge>

            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={logout}
              aria-label="Dil"
            >
              <LogOut className="size-4" />
            </Button>
          </div>
        </header>

        {/* Navigimi mobil: i njëjti rend si te shiriti anësor. */}
        <nav className="flex gap-1 overflow-x-auto border-b bg-card px-3 py-2 lg:hidden">
          {visible.map((item) => {
            const active = item.href === activeHref;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex shrink-0 items-center gap-2 rounded-md px-3 py-1.5 text-xs font-medium",
                  active
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground",
                )}
              >
                <item.icon className="size-3.5" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <main className="flex-1 p-4 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
