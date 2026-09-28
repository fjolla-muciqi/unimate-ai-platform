import type {
  AdminOverview,
  AdminUser,
  AnalyticsOverview,
  AuditLog,
  AuditSummaryItem,
  ChatResponse,
  Conversation,
  ConversationDetail,
  Course,
  Dashboard,
  Deadline,
  Exam,
  MyProfile,
  Notification,
  Professor,
  ProfessorCourse,
  ProfessorDashboard,
  ProfessorStudent,
  Program,
  Schedule,
  UniDocument,
  User,
} from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const TOKEN_KEY = "unimate.token";

/** Tokeni ruhet në localStorage, prandaj lexohet vetëm në shfletues. */
export function getToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function readError(response: Response): Promise<string> {
  try {
    const body = await response.json();

    if (typeof body.detail === "string") {
      return body.detail;
    }

    // Gabimet e validimit të FastAPI vijnë si listë objektesh.
    if (Array.isArray(body.detail)) {
      return body.detail
        .map((item: { msg?: string }) => item.msg ?? "")
        .filter(Boolean)
        .join(", ");
    }
  } catch {
    // Përgjigje pa JSON — mbetet mesazhi i statusit.
  }

  return response.statusText || "Kërkesa dështoi.";
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    clearToken();

    throw new ApiError(401, "Sesioni skadoi. Kyçu përsëri.");
  }

  if (!response.ok) {
    throw new ApiError(response.status, await readError(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

/** CRUD-i administrativ: çdo burim ndjek të njëjtën formë REST. */
function resource<T>(path: string) {
  return {
    list: (): Promise<T[]> => request<T[]>(path),

    create: (payload: Record<string, unknown>): Promise<T> =>
      request<T>(path, {
        method: "POST",
        body: JSON.stringify(payload),
      }),

    update: (id: number, payload: Record<string, unknown>): Promise<T> =>
      request<T>(`${path}/${id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      }),

    remove: (id: number): Promise<void> =>
      request<void>(`${path}/${id}`, { method: "DELETE" }),
  };
}

export type Resource<T> = ReturnType<typeof resource<T>>;

export const admin = {
  courses: resource<Course>("/api/courses"),
  schedules: resource<Schedule>("/api/schedules"),
  exams: resource<Exam>("/api/exams"),
  // Pa `only_upcoming`, admini sheh edhe afatet që kanë kaluar.
  deadlines: resource<Deadline>("/api/deadlines"),
  notifications: resource<Notification>("/api/notifications"),
  programs: resource<Program>("/api/programs"),

  users(filters: { role?: string; search?: string } = {}): Promise<AdminUser[]> {
    const query = new URLSearchParams();

    if (filters.role) {
      query.set("role", filters.role);
    }

    if (filters.search) {
      query.set("search", filters.search);
    }

    const suffix = query.toString() ? `?${query}` : "";

    return request<AdminUser[]>(`/api/admin/users${suffix}`);
  },

  setUserActive(id: number, isActive: boolean): Promise<AdminUser> {
    return request<AdminUser>(`/api/admin/users/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: isActive }),
    });
  },
};

export const api = {
  async login(email: string, password: string): Promise<string> {
    // OAuth2PasswordRequestForm pret form-encoded, jo JSON.
    const body = new URLSearchParams({
      username: email,
      password,
    });

    const response = await fetch(`${BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body,
    });

    if (!response.ok) {
      throw new ApiError(response.status, await readError(response));
    }

    const data = (await response.json()) as { access_token: string };

    return data.access_token;
  },

  register(payload: {
    first_name: string;
    last_name: string;
    email: string;
    password: string;
  }): Promise<User> {
    return request<User>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  me(): Promise<User> {
    return request<User>("/api/auth/me");
  },

  changePassword(currentPassword: string, newPassword: string): Promise<void> {
    return request<void>("/api/auth/change-password", {
      method: "POST",
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });
  },

  myProfile(): Promise<MyProfile> {
    return request<MyProfile>("/api/student/me/profile");
  },

  createMyProfile(payload: {
    program_id: number;
    academic_year: number;
    semester: number;
    preferred_language: MyProfile["preferred_language"];
  }): Promise<MyProfile> {
    return request<MyProfile>("/api/student/me/profile", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  updateMyProfile(language: MyProfile["preferred_language"]): Promise<MyProfile> {
    return request<MyProfile>("/api/student/me/profile", {
      method: "PATCH",
      body: JSON.stringify({ preferred_language: language }),
    });
  },

  dashboard(): Promise<Dashboard> {
    return request<Dashboard>("/api/student/me/dashboard");
  },

  myCourses(): Promise<Course[]> {
    return request<Course[]>("/api/student/me/courses");
  },

  mySchedule(): Promise<Schedule[]> {
    return request<Schedule[]>("/api/student/me/schedule");
  },

  myExams(): Promise<Exam[]> {
    return request<Exam[]>("/api/student/me/exams");
  },

  professorDashboard(): Promise<ProfessorDashboard> {
    return request<ProfessorDashboard>(
      "/api/professor/me/dashboard",
    );
  },

  professorCourses(): Promise<ProfessorCourse[]> {
    return request<ProfessorCourse[]>("/api/professor/me/courses");
  },

  professorSchedule(): Promise<Schedule[]> {
    return request<Schedule[]>("/api/professor/me/schedule");
  },

  professorExams(): Promise<Exam[]> {
    return request<Exam[]>("/api/professor/me/exams");
  },

  professorStudents(courseCode?: string): Promise<ProfessorStudent[]> {
    const query = courseCode
      ? `?course_code=${encodeURIComponent(courseCode)}`
      : "";

    return request<ProfessorStudent[]>(
      `/api/professor/me/students${query}`,
    );
  },

  courses(): Promise<Course[]> {
    return request<Course[]>("/api/courses");
  },

  professors(): Promise<Professor[]> {
    return request<Professor[]>("/api/professors");
  },

  deadlines(onlyUpcoming = true): Promise<Deadline[]> {
    return request<Deadline[]>(
      `/api/deadlines?only_upcoming=${onlyUpcoming}`,
    );
  },

  notifications(): Promise<Notification[]> {
    return request<Notification[]>("/api/notifications");
  },

  chat(payload: {
    message: string;
    conversationId?: number | null;
  }): Promise<ChatResponse> {
    return request<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify({
        message: payload.message,
        conversation_id: payload.conversationId ?? null,
      }),
    });
  },

  conversations(): Promise<Conversation[]> {
    return request<Conversation[]>("/api/chat/conversations");
  },

  conversation(id: number): Promise<ConversationDetail> {
    return request<ConversationDetail>(
      `/api/chat/conversations/${id}`,
    );
  },

  deleteConversation(id: number): Promise<void> {
    return request<void>(`/api/chat/conversations/${id}`, {
      method: "DELETE",
    });
  },

  rateMessage(messageId: number, rating: -1 | 0 | 1): Promise<void> {
    return request<void>(`/api/chat/messages/${messageId}/feedback`, {
      method: "POST",
      body: JSON.stringify({ rating }),
    });
  },

  documents(): Promise<UniDocument[]> {
    return request<UniDocument[]>("/api/documents");
  },

  uploadDocument(form: FormData): Promise<UniDocument> {
    return request<UniDocument>("/api/documents/upload", {
      method: "POST",
      body: form,
    });
  },

  reindexDocument(id: number): Promise<UniDocument> {
    return request<UniDocument>(`/api/documents/${id}/reindex`, {
      method: "POST",
    });
  },

  deleteDocument(id: number): Promise<void> {
    return request<void>(`/api/documents/${id}`, { method: "DELETE" });
  },

  analytics(): Promise<AnalyticsOverview> {
    return request<AnalyticsOverview>("/api/analytics/overview");
  },

  adminOverview(): Promise<AdminOverview> {
    return request<AdminOverview>("/api/admin/overview");
  },

  auditLogs(limit = 50): Promise<AuditLog[]> {
    return request<AuditLog[]>(`/api/admin/audit-logs?limit=${limit}`);
  },

  auditSummary(): Promise<AuditSummaryItem[]> {
    return request<AuditSummaryItem[]>(
      "/api/admin/audit-logs/summary",
    );
  },
};
