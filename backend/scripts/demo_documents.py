"""Dokumentet demo të universitetit, si PDF të gjeneruara.

Pse PDF dhe jo tekst i thjeshtë: ekstraktori nxjerr numër faqeje
vetëm nga PDF-të, dhe citimi "dokumenti + faqja" është kërkesë e
temës. Një .txt do të citohej pa faqe.

Përmbajtja është fiktive por e strukturuar si rregullore reale, me
fakte konkrete (numra, afate, kushte) që pyetjet demo t'i gjejnë dhe
mentori të mund ta verifikojë citimin duke hapur faqen.
"""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)


# Çdo dokument: metadata + faqet. Një faqe është një listë blloqesh:
# ("h1" | "h2" | "p", teksti).
DEMO_DOCUMENTS: list[dict] = [
    {
        "file_name": "rregullorja-e-studimeve-bachelor.pdf",
        "title": "Rregullorja e Studimeve Bachelor",
        "document_type": "REGULATION",
        "description": (
            "Rregullat e përgjithshme të studimeve bachelor: "
            "regjistrimi, provimet, kreditet dhe diplomimi."
        ),
        "academic_year": "2025/2026",
        "pages": [
            [
                ("h1", "Rregullorja e Studimeve Bachelor"),
                ("h2", "Neni 1 — Fusha e zbatimit"),
                (
                    "p",
                    "Kjo rregullore zbatohet për të gjithë studentët "
                    "e ciklit të parë të studimeve në Fakultetin e "
                    "Inxhinierisë Kompjuterike, të regjistruar nga "
                    "viti akademik 2025/2026 e tutje.",
                ),
                ("h2", "Neni 2 — Kohëzgjatja dhe kreditet"),
                (
                    "p",
                    "Programi bachelor zgjat tre vite akademike dhe "
                    "përmban 180 kredite ECTS. Një vit akademik "
                    "përmban 60 kredite ECTS, të ndara në dy "
                    "semestra me nga 30 kredite secili.",
                ),
                (
                    "p",
                    "Studenti konsiderohet me status të rregullt kur "
                    "grumbullon të paktën 40 kredite ECTS brenda një "
                    "viti akademik. Nën këtë prag, studenti kalon në "
                    "status me kohë të pjesshme.",
                ),
                ("h2", "Neni 3 — Regjistrimi në semestër"),
                (
                    "p",
                    "Regjistrimi i semestrit dimëror bëhet nga 1 deri "
                    "më 15 tetor. Regjistrimi i semestrit veror bëhet "
                    "nga 1 deri më 15 shkurt. Regjistrimi i vonuar "
                    "lejohet brenda shtatë ditëve nga mbyllja e "
                    "afatit, kundrejt një tarife administrative prej "
                    "20 eurosh.",
                ),
            ],
            [
                ("h2", "Neni 4 — Provimet"),
                (
                    "p",
                    "Studenti ka të drejtë të paraqitet në provim "
                    "vetëm nëse është regjistruar në lëndë dhe ka "
                    "plotësuar kushtin e pjesëmarrjes prej 70 për "
                    "qind në ushtrime.",
                ),
                (
                    "p",
                    "Regjistrimi për provim mbyllet shtatë ditë para "
                    "datës së provimit. Pas këtij afati nuk pranohen "
                    "kërkesa, përveç rasteve të justifikuara me "
                    "raport mjekësor të dorëzuar brenda 48 orëve.",
                ),
                (
                    "p",
                    "Një lëndë mund të jepet maksimalisht katër herë. "
                    "Pas dështimit të katërt, studenti duhet ta "
                    "riregjistrojë lëndën në vitin pasardhës.",
                ),
                ("h2", "Neni 5 — Vlerësimi"),
                (
                    "p",
                    "Nota përfundimtare formohet nga provimi "
                    "përfundimtar me peshë 60 për qind, provimi i "
                    "ndërmjetëm me peshë 25 për qind dhe detyrat e "
                    "ushtrimeve me peshë 15 për qind. Nota kaluese "
                    "është 6, që korrespondon me 50 për qind të "
                    "pikëve totale.",
                ),
                (
                    "p",
                    "Studenti ka të drejtë të kërkojë rishikim të "
                    "vlerësimit brenda tri ditëve pune nga publikimi "
                    "i rezultateve.",
                ),
            ],
            [
                ("h2", "Neni 6 — Transferimi i studimeve"),
                (
                    "p",
                    "Transferimi nga një institucion tjetër i arsimit "
                    "të lartë lejohet vetëm në fillim të vitit "
                    "akademik. Kërkesa dorëzohet deri më 15 shtator "
                    "dhe shoqërohet me transkriptin e notave dhe "
                    "syllabuset e lëndëve të kaluara.",
                ),
                (
                    "p",
                    "Komisioni i njohjes vlerëson përputhshmërinë e "
                    "lëndëve. Njihen maksimalisht 90 kredite ECTS nga "
                    "studimet paraprake. Lëndët njihen kur përmbajtja "
                    "përputhet të paktën 75 për qind.",
                ),
                ("h2", "Neni 7 — Diplomimi"),
                (
                    "p",
                    "Studenti diplomohet pasi grumbullon 180 kredite "
                    "ECTS dhe mbron temën e diplomës. Tema e diplomës "
                    "ka 6 kredite ECTS dhe regjistrohet jo më vonë se "
                    "gjashtë muaj para mbrojtjes.",
                ),
                (
                    "p",
                    "Nota mesatare e diplomës llogaritet si mesatare "
                    "e ponderuar sipas kreditave të secilës lëndë.",
                ),
            ],
        ],
    },
    {
        "file_name": "syllabus-cs201-algoritme.pdf",
        "title": "Syllabus: CS201 Algoritme dhe Struktura të Dhënash",
        "document_type": "SYLLABUS",
        "description": (
            "Përmbajtja, literatura dhe vlerësimi i lëndës CS201."
        ),
        "academic_year": "2025/2026",
        "pages": [
            [
                (
                    "h1",
                    "CS201 — Algoritme dhe Struktura të Dhënash",
                ),
                ("h2", "Të dhënat e lëndës"),
                (
                    "p",
                    "Kodi: CS201. Kredite: 7 ECTS. Semestri: 3. "
                    "Ligjërues: Prof. Dr. Arben Hoxha, zyra B-210. "
                    "Konsultime: e martë 12:00-14:00.",
                ),
                ("h2", "Parakushtet"),
                (
                    "p",
                    "Studenti duhet të ketë kaluar lëndën CS101 "
                    "Hyrje në Programim. Njohuritë bazë të "
                    "matematikës diskrete janë të domosdoshme.",
                ),
                ("h2", "Përmbajtja javore"),
                (
                    "p",
                    "Javët 1-3: analiza e kompleksitetit, notacioni "
                    "O i madh, rekursioni. Javët 4-6: listat e "
                    "lidhura, stack, queue. Javët 7-9: pemët binare "
                    "të kërkimit, pemët AVL, heap. Javët 10-12: "
                    "tabelat hash dhe trajtimi i përplasjeve. "
                    "Javët 13-15: grafet, BFS, DFS, Dijkstra.",
                ),
            ],
            [
                ("h2", "Vlerësimi"),
                (
                    "p",
                    "Provimi përfundimtar 60 për qind, provimi i "
                    "ndërmjetëm 25 për qind, tri detyra "
                    "programimi 15 për qind. Pjesëmarrja në "
                    "ushtrime është e detyrueshme në masën 70 për "
                    "qind.",
                ),
                ("h2", "Literatura"),
                (
                    "p",
                    "Cormen, Leiserson, Rivest, Stein — Introduction "
                    "to Algorithms, botimi i katërt. Sedgewick, Wayne "
                    "— Algorithms, botimi i katërt. Materialet e "
                    "ligjëratave publikohen çdo javë në platformë.",
                ),
                ("h2", "Politika e detyrave"),
                (
                    "p",
                    "Detyrat dorëzohen individualisht. Dorëzimi i "
                    "vonuar pranohet deri në 48 orë me zbritje prej "
                    "20 për qind të pikëve. Plagjiatura sjell "
                    "vlerësim me zero për detyrën dhe raportim te "
                    "komisioni disiplinor.",
                ),
            ],
        ],
    },
    {
        "file_name": "udhezues-per-studentet-e-vitit-te-pare.pdf",
        "title": "Udhëzues për Studentët e Vitit të Parë",
        "document_type": "GUIDE",
        "description": (
            "Shërbimet studentore, bibliotekat, bursat dhe "
            "kontaktet kryesore."
        ),
        "academic_year": "2025/2026",
        "pages": [
            [
                ("h1", "Udhëzues për Studentët e Vitit të Parë"),
                ("h2", "Zyra e Studentëve"),
                (
                    "p",
                    "Zyra e Studentëve ndodhet në katin përdhes të "
                    "ndërtesës A, zyra A-012. Orari i pritjes: e hënë "
                    "deri e premte, 09:00-13:00. Aty merren "
                    "vërtetimet e statusit të studentit, transkriptet "
                    "e notave dhe formularët e regjistrimit.",
                ),
                ("h2", "Biblioteka"),
                (
                    "p",
                    "Biblioteka qendrore është e hapur nga e hëna në "
                    "të premte, 08:00-20:00, dhe të shtunën "
                    "09:00-14:00. Studenti mund të huazojë "
                    "njëkohësisht deri në pesë libra për një afat "
                    "prej 21 ditësh, i zgjatshëm një herë.",
                ),
                ("h2", "Llogaria universitare"),
                (
                    "p",
                    "Çdo student merr një adresë emaili institucional "
                    "në formatin emri.mbiemri@student.unimate.edu. "
                    "Kjo adresë është kanali zyrtar i komunikimit dhe "
                    "duhet kontrolluar të paktën një herë në javë.",
                ),
            ],
            [
                ("h2", "Bursat"),
                (
                    "p",
                    "Aplikimi për bursë akademike hapet më 1 nëntor "
                    "dhe mbyllet më 30 nëntor. Kushti minimal është "
                    "nota mesatare 8.5 dhe të paktën 50 kredite ECTS "
                    "të grumbulluara në vitin paraprak.",
                ),
                (
                    "p",
                    "Bursa sociale ka afat të njëjtë aplikimi dhe "
                    "kërkon dokumentacion mbi të ardhurat familjare. "
                    "Rezultatet shpallen brenda 30 ditëve nga mbyllja "
                    "e afatit.",
                ),
                ("h2", "Mbështetja teknike"),
                (
                    "p",
                    "Për probleme me llogarinë ose platformën "
                    "elektronike, shkruani në it@unimate.edu. Koha e "
                    "pritur e përgjigjes është dy ditë pune.",
                ),
                ("h2", "Këshilli Studentor"),
                (
                    "p",
                    "Këshilli Studentor mblidhet çdo të mërkurë të "
                    "parë të muajit në sallën A-201 dhe përfaqëson "
                    "studentët në organet drejtuese të fakultetit.",
                ),
            ],
        ],
    },
]


def _styles() -> dict:
    base = getSampleStyleSheet()

    return {
        "h1": ParagraphStyle(
            "DemoH1",
            parent=base["Title"],
            fontSize=17,
            leading=21,
            spaceAfter=14,
        ),
        "h2": ParagraphStyle(
            "DemoH2",
            parent=base["Heading2"],
            fontSize=12.5,
            leading=16,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "p": ParagraphStyle(
            "DemoBody",
            parent=base["BodyText"],
            fontSize=10.5,
            leading=15,
            spaceAfter=8,
        ),
    }


def write_pdf(spec: dict, target: Path) -> Path:
    """Shkruan një dokument demo si PDF me faqe të veçanta."""

    styles = _styles()

    document = SimpleDocTemplate(
        str(target),
        pagesize=A4,
        title=spec["title"],
        author="UniMate AI (të dhëna demo)",
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
    )

    flowables: list = []

    for index, page in enumerate(spec["pages"]):
        if index:
            flowables.append(PageBreak())

        for kind, text in page:
            flowables.append(Paragraph(text, styles[kind]))

        flowables.append(Spacer(1, 6))

    document.build(flowables)

    return target


__all__ = ["DEMO_DOCUMENTS", "write_pdf"]
