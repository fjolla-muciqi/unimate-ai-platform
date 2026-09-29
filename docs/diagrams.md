# UniMate AI — diagramet e sistemit

Diagramet ndjekin kodin ashtu siç është në repo. Janë në Mermaid: VS Code
(me shtesën *Markdown Preview Mermaid Support*) dhe GitHub i shfaqin
drejtpërdrejt. Për Word, hap diagramin te <https://mermaid.live>, ngjit
kodin dhe eksportoje si PNG ose SVG.

Përmbajtja:

1. Use Case — kush çfarë bën
2. C4 — konteksti dhe kontejnerët
3. ER — skema e bazës së të dhënave
4. Sequence — rruga e një pyetjeje nëpër agjentë
5. Activity — pipeline-i i dokumenteve dhe kërkimi hibrid
6. Class — modulet e agjentëve

---

## 1. Use Case

Tre rolet e temës. Rolet i cakton JWT-ja; asnjë endpoint nuk pranon rol
nga trupi i kërkesës.

```mermaid
flowchart LR
    S([Student])
    P([Profesor])
    A([Administrator])

    subgraph UniMate AI
        UC1[Regjistrohet dhe plotëson profilin akademik]
        UC2[Sheh lëndët, orarin, provimet dhe afatet]
        UC3[Pyet asistentin AI dhe merr burime]
        UC4[Gjeneron quiz dhe flashcards]
        UC5[Vlerëson përgjigjet ↑/↓]
        UC6[Sheh historikun e bisedave]
        UC7[Ndryshon fjalëkalimin dhe gjuhën]
        UC8[Sheh lëndët që ligjëron dhe studentët e tyre]
        UC9[Ngarkon dhe ri-indekson dokumente]
        UC10[Menaxhon lëndët, orarin, provimet, afatet, njoftimet]
        UC11[Aktivizon / çaktivizon llogari]
        UC12[Sheh analitikën dhe regjistrin e sigurisë]
    end

    S --- UC1
    S --- UC2
    S --- UC3
    S --- UC4
    S --- UC5
    S --- UC6
    S --- UC7

    P --- UC3
    P --- UC7
    P --- UC8
    P --- UC9

    A --- UC7
    A --- UC9
    A --- UC10
    A --- UC11
    A --- UC12
```

---

## 2. C4

### Niveli 1 — Konteksti

```mermaid
flowchart TB
    student([Student / Profesor / Admin])
    unimate[UniMate AI<br/>platforma universitare me asistent multi-agent]
    claude[Anthropic API<br/>claude-sonnet-5]
    hf[Hugging Face Hub<br/>modeli i embeddings, shkarkohet një herë]

    student -- "HTTPS, shfletues" --> unimate
    unimate -- "Messages API me tool use" --> claude
    unimate -. "herën e parë" .-> hf
```

### Niveli 2 — Kontejnerët (`docker-compose.yml`)

```mermaid
flowchart TB
    user([Përdoruesi])

    subgraph Docker Compose
        web[web<br/>Next.js 16, TypeScript,<br/>Tailwind, shadcn/ui<br/>:3000]
        api[api<br/>FastAPI, Pydantic v2,<br/>SQLAlchemy 2, agjentët<br/>:8000]
        pg[(postgres<br/>PostgreSQL 17<br/>të dhënat akademike,<br/>bisedat, audit-i)]
        qd[(qdrant<br/>vektorët e fragmenteve,<br/>384 dimensione)]
        vol[/uploads_data<br/>PDF, DOCX, TXT/]
        cache[/model_cache<br/>sentence-transformers/]
    end

    claude[Anthropic API]

    user --> web
    web -- "REST + JWT" --> api
    api -- "SQL" --> pg
    api -- "kërkim vektorial" --> qd
    api --> vol
    api --> cache
    api -- "tool use" --> claude
```

---

## 3. ER — skema e bazës

17 tabela, të krijuara nga 11 migrime Alembic. `PK` = çelës primar,
`FK` = çelës i huaj.

```mermaid
erDiagram
    users ||--o| student_profiles : "ka profil"
    users ||--o| professors : "llogaria e"
    users ||--o{ conversations : zotëron
    users ||--o{ documents : ngarkon
    users ||--o{ notifications : krijon
    users ||--o{ audit_logs : shkakton

    faculties ||--o{ programs : ka
    faculties ||--o{ professors : punëson

    programs ||--o{ courses : përmban
    programs ||--o{ student_profiles : "ndjekin"
    programs |o--o{ deadlines : "për programin"
    programs |o--o{ notifications : "për programin"

    professors |o--o{ courses : ligjëron
    courses ||--o{ schedules : "ka orar"
    courses ||--o{ exams : "ka provime"
    courses ||--o{ enrollments : ""
    student_profiles ||--o{ enrollments : ""
    courses ||--o{ course_prerequisites : "kërkon"

    conversations ||--o{ messages : përmban
    documents ||--o{ document_chunks : "ndahet në"

    users {
        int id PK
        string email UK
        string password_hash "Argon2"
        string role "STUDENT | PROFESSOR | ADMIN"
        bool is_active
    }
    student_profiles {
        int id PK
        int user_id FK
        string student_number UK
        int program_id FK
        int academic_year
        int semester
        string preferred_language "sq | en"
    }
    professors {
        int id PK
        int user_id FK
        int faculty_id FK
        string title
        string office
        string consultation_hours
    }
    faculties {
        int id PK
        string name
    }
    programs {
        int id PK
        int faculty_id FK
        string name
        string degree_level
        int total_ects
        int duration_years
        string graduation_requirements
    }
    courses {
        int id PK
        string code UK
        string name
        int ects
        int semester
        string syllabus
        int program_id FK
        int professor_id FK
    }
    course_prerequisites {
        int id PK
        int course_id FK
        int prerequisite_id FK
    }
    enrollments {
        int id PK
        int student_profile_id FK
        int course_id FK
        string status
    }
    schedules {
        int id PK
        int course_id FK
        string day_of_week
        time start_time
        time end_time
        string room
    }
    exams {
        int id PK
        int course_id FK
        string exam_type
        datetime exam_date
        string room
    }
    deadlines {
        int id PK
        int program_id FK "bosh = të gjitha programet"
        string title
        string deadline_type
        datetime due_date
    }
    notifications {
        int id PK
        int program_id FK
        int created_by FK
        string title
        string severity
        bool is_active
    }
    documents {
        int id PK
        int uploaded_by FK
        string title
        string file_path
        string document_type
        string status "PENDING | PROCESSING | INDEXED | FAILED"
        int chunk_count
        bool is_active "fshirje e butë"
    }
    document_chunks {
        int id PK
        int document_id FK
        string vector_id "id-ja në Qdrant"
        int page_number
        int chunk_index
        string content
        string content_hash
    }
    conversations {
        int id PK
        int user_id FK
        string title
        bool is_active
    }
    messages {
        int id PK
        int conversation_id FK
        string role "user | assistant"
        string content
        json sources
        json agents_used
        json artifacts
        int latency_ms
        int rating "1 | -1 | 0"
        bool is_unanswered
        string blocked_by
    }
    audit_logs {
        int id PK
        int user_id FK
        string event_type
        string rule
        string detail
        datetime created_at
    }
```

---

## 4. Sequence — një pyetje nëpër agjentë

Shembull: *"Kur e kam provimin e Algoritmeve dhe çfarë duhet të mësoj?"*
Modeli thërret tools të dy agjentëve në të njëjtën përgjigje.

```mermaid
sequenceDiagram
    autonumber
    actor S as Studenti
    participant W as Frontend (Next.js)
    participant R as /api/chat (FastAPI)
    participant G as Guardrail Agent
    participant O as Orchestrator (Router implicit)
    participant C as Claude (claude-sonnet-5)
    participant T as Tools e agjentëve
    participant DB as PostgreSQL
    participant Q as Qdrant
    participant V as Response Validator

    S->>W: shkruan pyetjen
    W->>R: POST /api/chat + JWT
    R->>DB: historiku i bisedës
    R->>G: check_request(pyetja)

    alt sulm (prompt injection, të dhëna të huaja…)
        G-->>R: bllokuar + rregulla
        R->>DB: audit_logs
        R-->>W: refuzim, agents_used = [guardrail]
    else e lejuar
        R->>O: handle_chat_message
        loop deri në 6 iteracione
            O->>C: system + 13 tools + mesazhet (prefiksi nga cache)
            C-->>O: tool_use: get_my_exams, get_course_details
            O->>T: ekzekuto tools (roli dhe profili nga JWT)
            T->>DB: provimet e studentit, syllabus-i
            opt search_university_documents
                T->>Q: kërkim hibrid (vektor + fjalë)
                Q-->>T: fragmente me dokument dhe faqe
            end
            T-->>O: tool_result + agjentët [schedule, academic]
        end
        C-->>O: përgjigjja me citime [1], [2]
        O->>V: validate_answer
        V-->>O: heq citimet e shpikura, shënon "pa përgjigje"
        O->>G: check_response (sekrete, system prompt)
        G-->>O: e lejuar
        O-->>R: përgjigje + burime + agjentë + latencë
        R->>DB: messages (sources, agents_used, latency_ms)
        R-->>W: ChatResponse
    end

    W-->>S: përgjigjja, burimet dhe agjentët e përdorur
```

---

## 5. Activity — dokumentet dhe kërkimi

### Pipeline-i i ingestimit

```mermaid
flowchart TD
    A([Admini / profesori ngarkon PDF, DOCX ose TXT]) --> B[Ruhet skedari; status PENDING]
    B --> C[BackgroundTask: status PROCESSING]
    C --> D[Nxirret teksti faqe për faqe]
    D --> E[Ndarje sipas fjalive: fragmente 500 karaktere,<br/>fjalia e fundit përsëritet si mbivendosje]
    E --> F[Fragmentet ruhen në PostgreSQL]
    F --> G[Embeddings: multilingual MiniLM, 384 dimensione]
    G --> H[Vektorët e vjetër fshihen, të rinjtë shkruhen në Qdrant]
    H --> I{Numri përputhet?}
    I -- po --> J([INDEXED])
    I -- jo --> K([FAILED me arsyen])
    D -. gabim .-> K
    G -. gabim .-> K

    R([Rinisje e API-t gjatë përpunimit]) --> S[recover_documents: PENDING/PROCESSING → FAILED]
    S --> K
    K --> L[Admini shtyp Ri-indekso] --> C
```

### Kërkimi hibrid

```mermaid
flowchart TD
    Q([Pyetja]) --> E[Embedding i pyetjes]
    E --> V[Qdrant: 4 × k kandidatë sipas ngjashmërisë kosinus]
    V --> F{ngjashmëria ≥ 0.25?}
    F -- jo --> X[hidhet]
    F -- po --> K[Pika leksikore: pjesa e rrënjëve të pyetjes<br/>që gjenden në fragment]
    K --> S[Renditja: vektori + 0.3 × leksikore]
    S --> T[k = 5 fragmentet e para]
    T --> D{Dokumenti aktiv?}
    D -- jo --> X
    D -- po --> O([Fragmente me titull, dokument dhe faqe])
```

---

## 6. Class — agjentët

Router Agent-i është implicit: modeli zgjedh tools, dhe `TOOL_OWNERS`
tregon cilit agjent i përket secili tool. Kështu çdo përgjigje ruan
saktësisht cilët agjentë e trajtuan.

```mermaid
classDiagram
    class AgentName {
        <<enumeration>>
        ACADEMIC
        SCHEDULE
        TUTOR
        STUDENT_SERVICES
        GUARDRAIL
    }

    class Registry {
        TOOL_OWNERS: dict~str, AgentName~
        agent_for_tool(tool_name) AgentName
    }

    class ToolContext {
        db: Session
        user: User
        profile: StudentProfile
        professor: Professor
        sources: SourceRegistry
        agents_used: list~AgentName~
        artifacts: list~dict~
    }

    class SourceRegistry {
        chunks: list~RetrievedChunk~
        register(chunk) int
    }

    class Orchestrator {
        run_agent(question, context, history) str
        handle_chat_message(message, user, db) AgentResult
        build_system_blocks(role) list
    }

    class AgentResult {
        answer: str
        chunks: list~RetrievedChunk~
        agents_used: list~str~
        artifacts: list~dict~
        latency_ms: int
        is_unanswered: bool
        blocked_by: str
    }

    class GuardrailAgent {
        check_request(message) Verdict
        check_response(answer, system_prompt) Verdict
    }

    class ValidatorAgent {
        validate_answer(answer, source_count, used_any_agent)
    }

    class AcademicAgent {
        search_university_documents
        search_course_catalog
        get_my_courses
        get_course_details
    }

    class ScheduleAgent {
        get_my_schedule
        get_my_exams
        get_deadlines
    }

    class TutorAgent {
        explain_topic(level sipas vitit akademik)
        generate_quiz() Quiz
        generate_flashcards() FlashcardSet
    }

    class StudentServicesAgent {
        get_my_profile
        get_my_notifications
        get_my_students
    }

    Orchestrator --> GuardrailAgent : para dhe pas
    Orchestrator --> ValidatorAgent
    Orchestrator --> ToolContext : krijon për çdo pyetje
    Orchestrator --> AgentResult : kthen
    ToolContext --> SourceRegistry
    Registry --> AgentName
    Orchestrator ..> Registry : agjenti nga tool-i
    Orchestrator ..> AcademicAgent
    Orchestrator ..> ScheduleAgent
    Orchestrator ..> TutorAgent
    Orchestrator ..> StudentServicesAgent
```
