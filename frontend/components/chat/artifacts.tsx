"use client";

import { useState } from "react";
import { Check, RotateCcw, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Artifact, FlashcardSet, Quiz } from "@/lib/types";
import { cn } from "@/lib/utils";

function QuizCard({ quiz }: { quiz: Quiz }) {
  // Përgjigjja e zgjedhur për çdo pyetje; e pazgjedhur = pa hyrje.
  const [answers, setAnswers] = useState<Record<number, number>>({});

  const answered = Object.keys(answers).length;

  const correct = Object.entries(answers).filter(
    ([index, choice]) =>
      quiz.questions[Number(index)].correct_index === choice,
  ).length;

  return (
    <Card className="mt-3">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-2">
          <CardTitle>Kuiz: {quiz.topic}</CardTitle>

          <div className="flex items-center gap-2">
            {answered > 0 ? (
              <Badge variant="secondary">
                {correct}/{answered} saktë
              </Badge>
            ) : null}

            {answered > 0 ? (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setAnswers({})}
              >
                <RotateCcw className="size-3.5" />
                Rifillo
              </Button>
            ) : null}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-5">
        {quiz.questions.map((question, questionIndex) => {
          const chosen = answers[questionIndex];
          const isAnswered = chosen !== undefined;

          return (
            <div key={questionIndex} className="space-y-2">
              <p className="text-sm font-medium">
                {questionIndex + 1}. {question.question}
              </p>

              <div className="space-y-1.5">
                {question.options.map((option, optionIndex) => {
                  const isCorrect =
                    optionIndex === question.correct_index;
                  const isChosen = optionIndex === chosen;

                  return (
                    <button
                      key={optionIndex}
                      type="button"
                      disabled={isAnswered}
                      onClick={() =>
                        setAnswers((current) => ({
                          ...current,
                          [questionIndex]: optionIndex,
                        }))
                      }
                      className={cn(
                        "flex w-full items-center gap-2 rounded-md border px-3 py-2 text-left text-sm transition-colors",
                        !isAnswered && "hover:bg-accent",
                        isAnswered &&
                          isCorrect &&
                          "border-success/50 bg-success/10",
                        isAnswered &&
                          isChosen &&
                          !isCorrect &&
                          "border-destructive/50 bg-destructive/10",
                        isAnswered &&
                          !isChosen &&
                          !isCorrect &&
                          "opacity-60",
                      )}
                    >
                      {isAnswered && isCorrect ? (
                        <Check className="size-4 shrink-0 text-success" />
                      ) : null}

                      {isAnswered && isChosen && !isCorrect ? (
                        <X className="size-4 shrink-0 text-destructive" />
                      ) : null}

                      <span>{option}</span>
                    </button>
                  );
                })}
              </div>

              {isAnswered ? (
                <p className="rounded-md bg-muted/60 p-2.5 text-xs text-muted-foreground">
                  {question.explanation}
                </p>
              ) : null}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

function FlashcardsCard({ set }: { set: FlashcardSet }) {
  const [flipped, setFlipped] = useState<Record<number, boolean>>({});

  return (
    <Card className="mt-3">
      <CardHeader className="pb-3">
        <CardTitle>Flashcards: {set.topic}</CardTitle>
      </CardHeader>

      <CardContent className="grid gap-2 sm:grid-cols-2">
        {set.cards.map((card, index) => {
          const isFlipped = Boolean(flipped[index]);

          return (
            <button
              key={index}
              type="button"
              onClick={() =>
                setFlipped((current) => ({
                  ...current,
                  [index]: !current[index],
                }))
              }
              className={cn(
                "min-h-[92px] rounded-lg border p-3 text-left text-sm transition-colors",
                isFlipped
                  ? "border-primary/40 bg-primary/5"
                  : "hover:bg-accent",
              )}
            >
              <p className="mb-1 text-[10px] uppercase tracking-wide text-muted-foreground">
                {isFlipped ? "Përgjigja" : "Pyetja"}
              </p>
              <p>{isFlipped ? card.back : card.front}</p>
            </button>
          );
        })}
      </CardContent>
    </Card>
  );
}

/** Përmbajtja e strukturuar që AI Tutor Agent-i kthen bashkë me tekstin. */
export function Artifacts({ artifacts }: { artifacts: Artifact[] }) {
  return (
    <>
      {artifacts.map((artifact, index) =>
        artifact.type === "quiz" ? (
          <QuizCard key={index} quiz={artifact.data} />
        ) : (
          <FlashcardsCard key={index} set={artifact.data} />
        ),
      )}
    </>
  );
}
