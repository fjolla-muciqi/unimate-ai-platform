import { GraduationCap } from "lucide-react";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Kolona e majtë shpjegon çfarë është produkti — te mbrojtja
          e temës faqja e kyçjes është e para që shihet. */}
      <div className="hidden flex-col justify-between bg-primary p-12 text-primary-foreground lg:flex">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl bg-primary-foreground/15">
            <GraduationCap className="size-6" />
          </div>
          <span className="text-xl font-semibold">UniMate AI</span>
        </div>

        <div className="space-y-6">
          <h1 className="max-w-md text-3xl font-semibold leading-tight">
            Platforma universitare e centralizuar, me asistent AI
            multi-agent.
          </h1>

          <ul className="space-y-3 text-sm text-primary-foreground/85">
            <li>
              Orari, provimet dhe lëndët e tua — në një pyetje të
              vetme.
            </li>
            <li>
              Përgjigje mbi rregulloret zyrtare, gjithmonë me
              dokumentin dhe faqen e cituar.
            </li>
            <li>
              Guardrail Agent që bllokon çdo kërkesë për të dhëna
              jashtë fushës sate.
            </li>
          </ul>
        </div>

        <p className="text-xs text-primary-foreground/60">
          Të dhënat demo janë fiktive dhe shërbejnë vetëm për
          prezantim.
        </p>
      </div>

      <div className="flex items-center justify-center p-6">
        <div className="w-full max-w-sm">{children}</div>
      </div>
    </div>
  );
}
