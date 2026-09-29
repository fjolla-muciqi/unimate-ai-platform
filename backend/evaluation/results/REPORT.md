# UniMate AI — rezultatet e vlerësimit

## 1. Retrieval (RAG)

22 pyetje me burim të njohur; modeli i embeddings `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, fragmente 500/120 karaktere.

| Niveli | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| Dokumenti i saktë | 95% | 100% | 100% | 0.977 |
| Faqja e saktë | 82% | 100% | 100% | 0.902 |

## 2. Ndikimi i ndarjes së tekstit (ablacion)

| Konfigurimi | Fragmente | Faqja Hit@1 | Faqja Hit@3 | MRR |
|---|---:|---:|---:|---:|
| Karaktere 1000/150 (ndarja e vjetër) | 7 | 41% | 68% | 0.561 |
| Fjali 1000/150 | 7 | 41% | 68% | 0.561 |
| Fjali 700/150 | 11 | 50% | 68% | 0.603 |
| Fjali 500/120 | 15 | 64% | 91% | 0.765 |
| Fjali 350/80 | 20 | 73% | 82% | 0.788 |
| Fjali 250/60 | 29 | 64% | 82% | 0.739 |

Prodhimi përdor 500/120. Me 22 pyetje, një dallim prej 5 pikësh përqindjeje është një pyetje.

## 2b. Kërkimi hibrid: vektorë + përputhje fjalësh

Pesha 0 është kërkimi vetëm semantik. Pesha u zgjodh mbi të njëjtat pyetje që e matin, prandaj vlerat janë optimiste për pyetje të reja.

| Pesha | Faqja Hit@1 | Faqja Hit@3 | Faqja Hit@5 | MRR |
|---:|---:|---:|---:|---:|
| 0.0 | 64% | 91% | 91% | 0.765 |
| 0.1 | 73% | 91% | 100% | 0.836 |
| 0.2 | 77% | 100% | 100% | 0.871 |
| 0.3 | 82% | 100% | 100% | 0.902 |
| 0.5 | 82% | 100% | 100% | 0.902 |
| 0.8 | 86% | 100% | 100% | 0.924 |

Prodhimi përdor peshën 0.0.

## 3. Routing i agjentëve

Modeli `claude-sonnet-5`, effort `medium`, 35 pyetje të vlerësuara.

- **E saktë**: u aktivizuan saktësisht agjentët e pritur.
- **E mbuluar**: u aktivizuan të gjithë agjentët e pritur, ndoshta edhe ndonjë tjetër.

| Kategoria | Pyetje | E saktë | E mbuluar |
|---|---:|---:|---:|
| Academic Knowledge | 15 | 93% | 100% |
| Schedule and Deadline | 6 | 67% | 100% |
| Student Services | 3 | 100% | 100% |
| AI Tutor | 4 | 50% | 75% |
| Bashkëpunim (2+ agjentë) | 3 | 100% | 100% |
| Pa përgjigje në dokumente | 2 | 100% | 100% |
| Guardrail (sulme) | 2 | 100% | 100% |
| **Gjithsej** | **35** | **86%** | **97%** |

Në shqip: 96% e mbuluar (24 pyetje).

Në anglisht: 100% e mbuluar (11 pyetje).

Pyetjet e drejtuara gabim:

- `T04` Më jep një përmbledhje të temave të lëndës CS203. — pritej AI Tutor Agent, u përdor Academic Knowledge Agent

## 4. Cilësia e përgjigjeve

| Treguesi | Vlera |
|---|---:|
| Përgjigje me faktet e pritura | 100% |
| Quiz / flashcards të prodhuara | 100% |
| Pyetje nga dokumentet që citojnë dokumentin e saktë | 100% |
| Pyetje pa përgjigje ku sistemi e pranoi mungesën | 100% |
| Pyetje me përgjigje ku sistemi tha gabimisht "nuk gjeta" | 0% |
| Sulme të bllokuara nga Guardrail | 100% |
| Përgjigje ku bashkëpunuan 2+ agjentë | 21% |
| Koha e përgjigjes, mesatare / mediane | 12 056 ms / 7 898 ms |
| Kostoja e vlerësimit | 0.289 $ |

## 5. Multi-agent + RAG kundrejt një chatbot-i të vetëm

I njëjti model; chatbot-i nuk ka tools, dokumente as të dhënat e studentit.

| Pyetja | Multi-agent | Chatbot i vetëm |
|---|:---:|:---:|
| `A01` Sa herë mund ta jap një provim sipas rregullores? | ✓ | ✗ |
| `A02` Sa kredite ECTS duhen për t'u diplomuar? | ✓ | ✓ |
| `A03` Kur bëhet regjistrimi i semestrit dimëror? | ✓ | ✗ |
| `A05` Si formohet nota përfundimtare e një lënde? | ✓ | ✗ |
| `A07` How many ECTS credits can be recognized when I transfer from another university? | ✓ | ✗ |
| `A08` Cila është literatura e lëndës CS201? | ✓ | ✗ |
| `A12` Kush e ligjëron lëndën CS202? | ✓ | ✗ |
| `A13` Deri në çfarë ore është e hapur biblioteka të premten? | ✓ | ✗ |
| `A14` Cilat janë kushtet për të aplikuar për bursë akademike? | ✓ | ✗ |
| `S01` Kur e kam provimin e radhës? | ✓ | ✗ |
| `S03` When is my Algorithms final exam and in which room? | ✓ | ✗ |
| `V03` What is my student number? | ✓ | ✗ |
| **Saktësia** | **100%** | **8%** |
