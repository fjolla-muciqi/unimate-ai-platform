"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import {
  Loader2,
  MessageSquarePlus,
  Send,
  ShieldAlert,
  ThumbsDown,
  ThumbsUp,
  Trash2,
} from "lucide-react";

import { Artifacts } from "@/components/chat/artifacts";
import { Sources } from "@/components/chat/sources";
import { ErrorState } from "@/components/layout/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { ChatMessage, Conversation } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";

/** Emri i lexueshëm i secilit agjent, sipas registry-t të backend-it. */
const AGENT_LABELS: Record<string, string> = {
  academic: "Academic Knowledge Agent",
  schedule: "Schedule and Deadline Agent",
  tutor: "AI Tutor Agent",
  student_services: "Student Services Agent",
  guardrail: "Guardrail Agent",
};

const SUGGESTIONS = [
  "Kur e kam provimin e radhës?",
  "Çfarë kam sot në orar?",
  "Sa herë mund ta jap një provim sipas rregullores?",
  "Cili është afati i transferimit të studimeve?",
];

/** Mesazh që ende nuk ka id nga backend-i (pyetja e sapodërguar). */
type PendingMessage = Pick<ChatMessage, "role" | "content"> & {
  id: number;
  pending?: boolean;
};

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [messages, setMessages] = useState<
    (ChatMessage | PendingMessage)[]
  >([]);

  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const bottomRef = useRef<HTMLDivElement>(null);

  const loadConversations = useCallback(async () => {
    try {
      setConversations(await api.conversations());
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Bisedat nuk u ngarkuan.",
      );
    }
  }, []);

  useEffect(() => {
    void loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function openConversation(id: number) {
    setActiveId(id);
    setError(null);

    try {
      const detail = await api.conversation(id);

      setMessages(detail.messages);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Biseda nuk u hap.",
      );
    }
  }

  function startNewConversation() {
    setActiveId(null);
    setMessages([]);
    setError(null);
  }

  async function removeConversation(id: number) {
    try {
      await api.deleteConversation(id);

      if (id === activeId) {
        startNewConversation();
      }

      await loadConversations();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Biseda nuk u fshi.",
      );
    }
  }

  async function send(text: string) {
    const question = text.trim();

    if (!question || sending) {
      return;
    }

    setInput("");
    setSending(true);
    setError(null);

    // Pyetja shfaqet menjëherë; përgjigjja vjen kur modeli mbaron.
    setMessages((current) => [
      ...current,
      { id: -Date.now(), role: "user", content: question },
    ]);

    try {
      const response = await api.chat({
        message: question,
        conversationId: activeId,
      });

      setMessages((current) => [
        ...current,
        {
          id: response.message_id ?? -Date.now(),
          role: "assistant",
          content: response.answer,
          sources: response.sources,
          agents_used: response.agents_used,
          artifacts: response.artifacts,
          rating: null,
          is_unanswered: response.is_unanswered,
          blocked_by: response.blocked_by,
          created_at: new Date().toISOString(),
        },
      ]);

      if (response.conversation_id && response.conversation_id !== activeId) {
        setActiveId(response.conversation_id);
      }

      await loadConversations();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Përgjigjja dështoi.",
      );

      // Pyetja hiqet që studenti të mos mendojë se u dërgua.
      setMessages((current) => current.slice(0, -1));
    } finally {
      setSending(false);
    }
  }

  async function rate(messageId: number, rating: 1 | -1) {
    if (messageId < 0) {
      return;
    }

    setMessages((current) =>
      current.map((message) =>
        message.id === messageId
          ? ({ ...message, rating } as ChatMessage)
          : message,
      ),
    );

    try {
      await api.rateMessage(messageId, rating);
    } catch {
      // Vlerësimi është dytësor: një dështim nuk e ndërpret bisedën.
    }
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();

    void send(input);
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[260px_1fr]">
      <aside className="space-y-2">
        <Button
          variant="outline"
          className="w-full justify-start"
          onClick={startNewConversation}
        >
          <MessageSquarePlus className="size-4" />
          Bisedë e re
        </Button>

        <div className="space-y-1">
          {conversations.map((conversation) => (
            <div
              key={conversation.id}
              className={cn(
                "group flex items-center gap-1 rounded-md px-2 py-1.5 text-sm transition-colors",
                conversation.id === activeId
                  ? "bg-primary/10 text-primary"
                  : "hover:bg-accent",
              )}
            >
              <button
                type="button"
                className="min-w-0 flex-1 text-left"
                onClick={() => void openConversation(conversation.id)}
              >
                <span className="block truncate">
                  {conversation.title}
                </span>
                <span className="block text-xs text-muted-foreground">
                  {formatDate(conversation.updated_at)}
                </span>
              </button>

              <Button
                variant="ghost"
                size="icon"
                className="size-7 opacity-0 transition-opacity group-hover:opacity-100"
                onClick={() =>
                  void removeConversation(conversation.id)
                }
                aria-label="Fshi bisedën"
              >
                <Trash2 className="size-3.5" />
              </Button>
            </div>
          ))}
        </div>
      </aside>

      <div className="flex min-h-[calc(100vh-12rem)] flex-col">
        <div className="flex-1 space-y-4 overflow-y-auto pb-4">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center gap-6 py-12 text-center">
              <div className="space-y-2">
                <h2 className="text-xl font-semibold">
                  Pyet për studimet e tua
                </h2>
                <p className="max-w-md text-sm text-muted-foreground">
                  Asistenti përgjigjet nga të dhënat e tua akademike
                  dhe nga dokumentet zyrtare të universitetit, duke
                  cituar gjithmonë burimin.
                </p>
              </div>

              <div className="flex flex-wrap justify-center gap-2">
                {SUGGESTIONS.map((suggestion) => (
                  <Button
                    key={suggestion}
                    variant="outline"
                    size="sm"
                    onClick={() => void send(suggestion)}
                  >
                    {suggestion}
                  </Button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((message) => {
              if (message.role === "user") {
                return (
                  <div key={message.id} className="flex justify-end">
                    <div className="max-w-[80%] rounded-2xl rounded-br-sm bg-primary px-4 py-2.5 text-sm text-primary-foreground">
                      {message.content}
                    </div>
                  </div>
                );
              }

              const assistant = message as ChatMessage;
              const blocked = Boolean(assistant.blocked_by);

              return (
                <div key={message.id} className="flex justify-start">
                  <Card
                    className={cn(
                      "max-w-[85%]",
                      blocked && "border-destructive/40 bg-destructive/5",
                    )}
                  >
                    <CardContent className="p-4">
                      {blocked ? (
                        <div className="mb-2 flex items-center gap-2 text-xs font-medium text-destructive">
                          <ShieldAlert className="size-4" />
                          Bllokuar nga Guardrail Agent
                          <Badge variant="outline">
                            {assistant.blocked_by}
                          </Badge>
                        </div>
                      ) : null}

                      <p className="answer-body text-sm">
                        {assistant.content}
                      </p>

                      {assistant.sources ? (
                        <Sources sources={assistant.sources} />
                      ) : null}

                      {assistant.artifacts?.length ? (
                        <Artifacts artifacts={assistant.artifacts} />
                      ) : null}

                      <div className="mt-3 flex flex-wrap items-center gap-2 border-t pt-3">
                        {(assistant.agents_used ?? []).map((agent) => (
                          <Badge
                            key={agent}
                            variant={
                              agent === "guardrail"
                                ? "destructive"
                                : "secondary"
                            }
                          >
                            {AGENT_LABELS[agent] ?? agent}
                          </Badge>
                        ))}

                        {assistant.is_unanswered ? (
                          <Badge variant="warning">Pa përgjigje</Badge>
                        ) : null}

                        <div className="ml-auto flex gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className={cn(
                              "size-7",
                              assistant.rating === 1 && "text-success",
                            )}
                            onClick={() => void rate(assistant.id, 1)}
                            aria-label="Përgjigje e dobishme"
                          >
                            <ThumbsUp className="size-3.5" />
                          </Button>

                          <Button
                            variant="ghost"
                            size="icon"
                            className={cn(
                              "size-7",
                              assistant.rating === -1 &&
                                "text-destructive",
                            )}
                            onClick={() => void rate(assistant.id, -1)}
                            aria-label="Përgjigje jo e dobishme"
                          >
                            <ThumbsDown className="size-3.5" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              );
            })
          )}

          {sending ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              Agjentët po punojnë…
            </div>
          ) : null}

          <div ref={bottomRef} />
        </div>

        {error ? <ErrorState message={error} /> : null}

        <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
          <Textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              // Enter dërgon; Shift+Enter shkon në rresht të ri.
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void send(input);
              }
            }}
            placeholder="Shkruaj pyetjen tënde…"
            className="min-h-[52px] resize-none"
            disabled={sending}
          />

          <Button
            type="submit"
            size="icon"
            className="size-[52px] shrink-0"
            disabled={sending || !input.trim()}
            aria-label="Dërgo"
          >
            {sending ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Send className="size-4" />
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}
