# Studimi pilot i përdorshmërisë — protokolli

Ky dokument është për ty, si drejtuese e studimit. Ndiqe njësoj me çdo
pjesëmarrës, që rezultatet të jenë të krahasueshme.

## Qëllimi

Të matet përdorshmëria e perceptuar e UniMate AI (SUS) dhe ndikimi i
citimeve në besimin e përdoruesit — PK2 e tezës dhe pyetja kërkimore
e temës *"Si ndikon përdorimi i burimeve dhe citimeve në besimin e
përdoruesit?"*

## Kush merr pjesë

- 10–12 persona që janë ose kanë qenë studentë. Nuk duhet të dinë
  programim.
- **Jo** persona që të kanë ndihmuar ta ndërtosh sistemin.
- Secili merr pjesë **një herë**. Mos plotëso asnjëherë pyetësorin në
  emër të dikujt tjetër.
- Secili **e përdor vetë sistemin** para pyetësorit. Të shikuarit e
  sistemit, ose një demonstrim, nuk mjafton: pyetjet e SUS dhe të
  besimit kanë kuptim vetëm pas përdorimit. Minimumi është t'i bëjë
  asistentit 3–4 pyetje dhe t'i shohë burimet poshtë përgjigjes.

Nëse në fund janë më pak (p.sh. 6), studimi raportohet si "pilot, n = 6".
Një numër i vogël i vërtetë është i pranueshëm; një numër i sajuar jo.

## Para seancave (një herë)

1. `docker compose up -d` dhe kontrollo që http://localhost:3000 hapet.
2. Kyçu si `student@unimate.edu` / `Student123!` dhe bëj një pyetje prove
   te chat-i, që modeli i embeddings të jetë i ngarkuar.
3. Krijo formularin në Google Forms nga `2-pyetesori.md`.
4. Kostoja: rreth 5–6 cent për pjesëmarrës; 12 pjesëmarrës ≈ 0.65 $.
5. Kyçu si admin dhe shëno numrin **"Pyetje (30 ditë)"** te paneli.
   Pas seancave, rritja e tij tregon sa pyetje bënë pjesëmarrësit — dëshmi
   në tezë që studimi u krye me përdorim të vërtetë.

## Seanca (rreth 15 minuta)

| Hapi | Koha | Çfarë bën |
|---|---|---|
| 1 | 2 min | Lexo tekstin e pëlqimit (`3-pelqimi.md`). Vazhdo vetëm nëse pranon. |
| 2 | 1 min | Hap aplikacionin të kyçur si studenti demo. Thuaj: *"Je Arta, studente në vitin e dytë. Ky është asistenti universitar."* |
| 3 | 10 min | Jepi detyrat më poshtë një nga një, të shkruara ose me zë. **Mos ndihmo** përveç nëse ngec mbi 2 minuta. |
| 4 | 3 min | Pjesëmarrësi plotëson vetë pyetësorin në Google Forms. Kodet P01, P02, … i cakton skripti sipas radhës së plotësimit. |

Para çdo pjesëmarrësi, te chat-i shtyp **"Bisedë e re"**, që të mos shohë
pyetjet e personit të mëparshëm.

### Detyrat

Lexoji fjalë për fjalë. Mos u trego ku gjendet përgjigjja.

| # | Detyra | Çfarë vëzhgon |
|---|---|---|
| D1 | "Gjej sa lëndë ke këtë semestër dhe kur është provimi yt i radhës." | A e gjen te paneli pa ndihmë? |
| D2 | "Pyet asistentin kur e ke provimin e radhës dhe në cilën sallë." | A merr përgjigje të saktë? |
| D3 | "Pyet asistentin sa herë mund të jepet një provim sipas rregullores. Pastaj shiko nga cili dokument erdhi përgjigjja." | A i sheh burimet poshtë përgjigjes? |
| D4 | "Pyet asistentin sa kushton parkingu i universitetit." | Informacioni nuk ekziston: si reagon pjesëmarrësi kur sistemi thotë se nuk e gjeti? |
| D5 | "Kërko nga asistenti një quiz me 3 pyetje për pemët binare dhe zgjidhe." | A e përdor quiz-in? (Zgjat ~40 s: thuaj që pritja është normale.) |
| D6 | "Bëj një pyetje çfarëdo për studimet, në anglisht." | A përgjigjet në anglisht? |
| D7 | "Gjej te faqja e orarit çfarë ligjëratash ke të mërkurën." | Navigimi pa AI. |

### Fleta e vëzhgimit

Për çdo pjesëmarrës shëno në një tabelë (Excel ose letër):

| Kodi | D1 | D2 | D3 | D3: e pa burimin? | D4 | D5 | D6 | D7 | Shënime |
|---|---|---|---|---|---|---|---|---|---|
| P01 | S | S | S | Po | S | ME | S | S | "e priti gjatë quiz-in" |

**S** = e kreu vetë, **ME** = me ndihmë, **D** = dështoi. Kodi i
pjesëmarrësit këtu ndjek radhën e seancave (i pari P01, i dyti P02, …),
që të përputhet me radhën e pyetësorëve.

Ruaje si `vezhgimet.csv` me këto kolona. Skripti i analizës e lexon.

## Pas seancave

1. Google Forms → **Responses → Download (.csv)** → ruaje si
   `pergjigjet.csv`.
2. Kopjo të dy skedarët te `backend/evaluation/results/usability/`.
3. `cd backend` dhe `.venv\Scripts\python -m evaluation.usability_analysis`.
4. Rezultati del te `results/usability/REPORT.md`, me numrat për
   Tabelën 5.7 të tezës.

## Rregullat e ndershmërisë

- Mos i ndrysho përgjigjet e pjesëmarrësve, as ato që nuk të pëlqejnë.
- Mos i përjashto pjesëmarrësit me rezultate të dobëta. Nëse përjashton
  dikë (p.sh. seanca u ndërpre), shkruaje në tezë me arsyen.
- Komentet e hapura citohen fjalë për fjalë, pa emra.
