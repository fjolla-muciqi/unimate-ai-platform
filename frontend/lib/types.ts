export type UserRole = "STUDENT" | "ADMIN" | "PROFESSOR";

export interface User {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
}

export interface Source {
  number: number;
  document_id: number | null;
  title: string | null;
  file_name: string | null;
  document_type: string | null;
  page_number: number | null;
  score: number;
}

export interface QuizQuestion {
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
}

export interface Quiz {
  topic: string;
  questions: QuizQuestion[];
}

export interface Flashcard {
  front: string;
  back: string;
}

export interface FlashcardSet {
  topic: string;
  cards: Flashcard[];
}

export type Artifact =
  | { type: "quiz"; data: Quiz }
  | { type: "flashcards"; data: FlashcardSet };

export interface ChatResponse {
  answer: string;
  sources: Source[];
  conversation_id: number | null;
  message_id: number | null;
  agents_used: string[];
  artifacts: Artifact[];
  is_unanswered: boolean;

  // Rregulla e Guardrail Agent-it kur kërkesa ose përgjigjja u bllokua.
  blocked_by: string | null;
}

export interface Conversation {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  sources: Source[] | null;
  agents_used: string[] | null;
  artifacts: Artifact[] | null;
  rating: number | null;
  is_unanswered: boolean;
  blocked_by: string | null;
  created_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: ChatMessage[];
}

export interface Course {
  id: number;
  code: string;
  name: string;
  description: string | null;
  ects: number;
  semester: number;
  program_id: number;
  syllabus: string | null;
  professor_id: number | null;
}

export interface Schedule {
  id: number;
  course_id: number;
  day_of_week: string;
  start_time: string;
  end_time: string;
  room: string | null;
}

export interface Exam {
  id: number;
  course_id: number;
  exam_type: string;
  exam_date: string;
  room: string | null;
}

export type DocumentStatus =
  | "PENDING"
  | "PROCESSING"
  | "INDEXED"
  | "FAILED";

export interface UniDocument {
  id: number;
  title: string;
  description: string | null;
  file_name: string;
  document_type: string;
  academic_year: string | null;
  uploaded_by: number;
  uploaded_at: string;
  is_active: boolean;
  status: DocumentStatus;
  status_detail: string | null;
  chunk_count: number;
  indexed_at: string | null;
}

export interface Deadline {
  id: number;
  title: string;
  description: string | null;
  deadline_type: string;
  due_date: string;
  program_id: number | null;
}

export interface Notification {
  id: number;
  title: string;
  body: string;
  severity: string;
  program_id: number | null;
  created_at: string;
  is_active: boolean;
}

export interface Professor {
  id: number;
  first_name: string;
  last_name: string;
  full_name: string;
  title: string | null;
  email: string | null;
  office: string | null;
  consultation_hours: string | null;
  faculty_id: number | null;
}

export interface DashboardSlot {
  course_code: string;
  course_name: string;
  start_time: string;
  end_time: string;
  room: string | null;
}

export interface DashboardExam {
  course_code: string;
  course_name: string;
  exam_type: string;
  exam_date: string;
  room: string | null;
  days_until: number;
}

export interface DashboardProgress {
  earned_ects: number;
  in_progress_ects: number;
  required_ects: number;
  percent: number;
}

export interface Dashboard {
  full_name: string;
  student_number: string;
  program_name: string;
  academic_year: number;
  semester: number;
  active_courses: number;
  today: string;
  today_schedule: DashboardSlot[];
  upcoming_exams: DashboardExam[];
  upcoming_deadlines: number;
  active_notifications: number;
  available_documents: number;
  progress: DashboardProgress;
}

export interface AgentUsage {
  agent: string;
  label: string;
  count: number;
  share: number;
}

export interface AnalyticsOverview {
  total_conversations: number;
  total_questions: number;
  total_answers: number;
  unanswered_count: number;
  unanswered_rate: number;
  average_latency_ms: number | null;
  median_latency_ms: number | null;
  answers_with_sources: number;
  citation_rate: number;
  ratings: {
    positive: number;
    negative: number;
    unrated: number;
    satisfaction: number | null;
  };
  agent_usage: AgentUsage[];
  multi_agent_answers: number;
  multi_agent_rate: number;
  frequent_questions: { question: string; count: number }[];
  recent_unanswered: {
    message_id: number;
    question: string;
    created_at: string;
  }[];
}

export interface AdminOverview {
  total_students: number;
  total_professors: number;
  total_admins: number;
  total_programs: number;
  total_courses: number;
  total_documents: number;
  indexed_documents: number;
  failed_documents: number;
  pending_documents: number;
  total_chunks: number;
  questions_last_30_days: number;
  blocked_last_30_days: number;
}

export interface AuditLog {
  id: number;
  user_id: number | null;
  user_email: string | null;
  event_type: string;
  rule: string | null;
  detail: string;
  created_at: string;
}

export interface AuditSummaryItem {
  event_type: string;
  count: number;
}

export interface ProfessorCourse {
  id: number;
  code: string;
  name: string;
  ects: number;
  semester: number;
  enrolled_students: number;
}

export interface ProfessorStudent {
  student_profile_id: number;
  full_name: string;
  email: string;
  student_number: string;
  academic_year: number;
  course_code: string;
  course_name: string;
}

export interface ProfessorDashboard {
  full_name: string;
  title: string | null;
  faculty_name: string | null;
  office: string | null;
  consultation_hours: string | null;
  courses_taught: number;
  total_students: number;
  today: string;
  today_schedule: DashboardSlot[];
  upcoming_exams: DashboardExam[];
  my_documents: number;
}
