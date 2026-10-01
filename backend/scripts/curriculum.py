"""Kurrikula e programit "Shkenca Kompjuterike dhe Inxhinieri".

Lëndët dhe semestrat ndjekin planin real të programit, me drejtshkrim të
normalizuar. Kodet SKI-xxx dhe shpërndarja e ECTS-ve janë DEMONSTRATIVE,
jo zyrtare: 30 ECTS për semestër, 180 gjithsej. Programi e shënon këtë me
`ects_is_official = False`, dhe administratori i ndryshon ECTS-të te
"Lëndët" pa prekur kodin.

Strukturë: viti 1 = semestrat 1-2, viti 2 = 3-4, viti 3 = 5-6.
"""

FACULTY_NAME = "Shkenca Kompjuterike dhe Inxhinieri"
PROGRAM_NAME = "Shkenca Kompjuterike dhe Inxhinieri"

# Emrat e mëparshëm të demos, që baza ekzistuese të riemërtohet në vend.
LEGACY_FACULTY_NAME = "Fakulteti i Inxhinierisë Kompjuterike"
LEGACY_PROGRAM_NAME = "Shkenca Kompjuterike"

FACULTY_DESCRIPTION = (
    "Fakulteti i shkencave kompjuterike dhe inxhinierisë: programim, "
    "sisteme, rrjeta, të dhëna dhe inteligjencë artificiale."
)

PROGRAM = {
    "degree_level": "BACHELOR",
    "specialization": None,
    "total_ects": 180,
    "ects_is_official": False,
    "duration_years": 3,
    "description": (
        "Program bachelor trevjeçar (6 semestra, 180 ECTS) në shkenca "
        "kompjuterike dhe inxhinieri. Shpërndarja e ECTS-ve nëpër lëndë "
        "në këtë sistem është demonstrative, jo zyrtare."
    ),
    "graduation_requirements": (
        "Për diplomim kërkohen 180 ECTS, përfundimi i të gjitha lëndëve "
        "të kurrikulës dhe mbrojtja e temës së diplomës."
    ),
}

DEMONSTRATIVE_NOTE = "ECTS demonstrative, jo zyrtare."

# (kodi, emri, ECTS, semestri, përshkrimi)
CURRICULUM = [
    # Viti 1, semestri 1
    ("SKI-101", "Hyrje në Shkenca Kompjuterike dhe Programim", 5, 1,
     "Konceptet bazë të kompjuterikës dhe programimi strukturor."),
    ("SKI-102", "Shkrim Akademik dhe Seminar", 5, 1,
     "Shkrimi akademik, citimi i burimeve dhe prezantimi."),
    ("SKI-103", "Gjuhë Angleze për Inxhinieri", 5, 1,
     "Anglishtja teknike për lexim dhe komunikim profesional."),
    ("SKI-104", "Arkitektura dhe Organizimi i Kompjuterëve", 5, 1,
     "Përfaqësimi i të dhënave, procesori, memoria dhe gjuha assembly."),
    ("SKI-105", "Bazat e Inxhinierisë Elektrike dhe Elektronike", 5, 1,
     "Qarqet elektrike, komponentët elektronikë dhe matjet."),
    ("SKI-106", "Matematikë 1", 5, 1,
     "Funksionet, limitet, derivatet dhe zbatimet e tyre."),
    # Viti 1, semestri 2
    ("SKI-201", "Shkenca Kompjuterike 1", 5, 2,
     "Programimi i avancuar: strukturat e të dhënave, testimi dhe gabimet."),
    ("SKI-202", "Ndërveprimi Kompjuter–Njeri", 5, 2,
     "Dizajni i ndërfaqeve, përdorshmëria dhe vlerësimi me përdorues."),
    ("SKI-203", "Hyrje në Sigurinë e Informacionit", 5, 2,
     "Kriptografia, autentikimi, sulmet e zakonshme dhe mbrojtja."),
    ("SKI-204", "Qarqet Digjitale dhe Sinjalet", 5, 2,
     "Logjika booleane, qarqet kombinuese dhe sekuenciale."),
    ("SKI-205", "Sistemet Operative", 5, 2,
     "Proceset, fijet, menaxhimi i memories dhe sistemet e skedarëve."),
    ("SKI-206", "Matematikë 2", 5, 2,
     "Integralet, algjebra lineare dhe hyrje në probabilitet."),
    # Viti 2, semestri 3
    ("SKI-301", "Shkenca Kompjuterike 2", 5, 3,
     "Programimi i orientuar në objekte: klasat, trashëgimia, "
     "polimorfizmi dhe modelet e dizajnit."),
    ("SKI-302", "Strukturat Diskrete 1", 5, 3,
     "Logjika, bashkësitë, relacionet, kombinatorika dhe grafet."),
    ("SKI-303", "Sistemet e Bazës së të Dhënave", 5, 3,
     "Modelimi relacional, SQL, normalizimi dhe transaksionet."),
    ("SKI-304", "Rrjeta Kompjuterike dhe Komunikim", 5, 3,
     "Modeli TCP/IP, protokollet, adresimi dhe siguria bazë e rrjetit."),
    ("SKI-305", "Hyrje në Algoritme", 5, 3,
     "Kompleksiteti algoritmik, listat, pemët, hash tabelat, "
     "renditja dhe kërkimi."),
    ("SKI-306", "Dizajni dhe Zhvillimi i Webit", 5, 3,
     "Frontend, backend, API REST dhe bazat e të dhënave në web."),
    # Viti 2, semestri 4
    ("SKI-401", "Lëndë Laboratorike 1", 5, 4,
     "Projekte praktike në laborator mbi lëndët e vitit të dytë."),
    ("SKI-402", "Strukturat Diskrete 2", 5, 4,
     "Teoria e grafeve, rekurrencat dhe automatet e fundme."),
    ("SKI-403", "Sisteme dhe Sinjale", 5, 4,
     "Sinjalet në kohë të vazhduar dhe diskrete, transformimet."),
    ("SKI-404", "Inxhinieria Softuerike", 5, 4,
     "Kërkesat, projektimi, testimi dhe metodologjitë agile."),
    ("SKI-405", "Bazat e të Dhënave Big Data", 5, 4,
     "Bazat NoSQL, përpunimi i shpërndarë dhe vëllimet e mëdha."),
    ("SKI-406", "Algoritmet dhe Strukturat e të Dhënave", 5, 4,
     "Pemët e balancuara, grafet, programimi dinamik dhe algoritmet "
     "greedy."),
    # Viti 3, semestri 5
    ("SKI-501", "Sistemet e Ndërlidhura", 5, 5,
     "Sistemet embedded, mikrokontrollerët dhe ndërlidhja me pajisje."),
    ("SKI-502", "Paternat e Dizajnit dhe Refaktorimi i Kodit", 5, 5,
     "Paternat krijuese, strukturore dhe të sjelljes; refaktorimi."),
    ("SKI-503", "Menaxhimi i Projekteve dhe Ndërmarrësia", 5, 5,
     "Planifikimi i projekteve softuerike dhe bazat e ndërmarrësisë."),
    ("SKI-504", "Dizajni i Sistemit të Softuerit", 5, 5,
     "Projektimi i sistemeve: shkallëzueshmëria, disponueshmëria, API-të."),
    ("SKI-505", "Bazat e Inteligjencës Artificiale", 5, 5,
     "Kërkimi, arsyetimi, mësimi i makinës dhe modelet gjuhësore."),
    ("SKI-506", "Interneti i Gjërave (IoT)", 5, 5,
     "Sensorët, protokollet IoT dhe platformat e të dhënave."),
    # Viti 3, semestri 6
    ("SKI-601", "Testimi i Softuerit dhe Sigurimi i Cilësisë", 5, 6,
     "Testimi njësi, integrues dhe i sistemit; cilësia e softuerit."),
    ("SKI-602", "Programimi i Lojërave", 5, 6,
     "Motorët e lojërave, grafika 2D/3D dhe logjika e lojës."),
    ("SKI-603", "Lëndë Laboratorike 2", 4, 6,
     "Projekte praktike në laborator mbi lëndët e vitit të tretë."),
    ("SKI-604", "Cloud Computing", 4, 6,
     "Virtualizimi, kontejnerët dhe shërbimet në cloud."),
    ("SKI-605", "Arkitektura Softuerike", 4, 6,
     "Stilet arkitekturore, mikroshërbimet dhe vendimet e arkitekturës."),
    ("SKI-606", "Tema e Diplomës", 8, 6,
     "Hulumtimi, zhvillimi dhe mbrojtja e temës së diplomës."),
]

# Lëndët e demos së mëparshme, të riemërtuara në vend: regjistrimet,
# grupet, materialet dhe bisedat e studimit të përdorshmërisë mbeten.
LEGACY_CODES = {
    "CS101": "SKI-101",
    "CS102": "SKI-302",
    "CS103": "SKI-201",
    "CS104": "SKI-104",
    "CS201": "SKI-305",
    "CS202": "SKI-303",
    "CS203": "SKI-301",
    "CS204": "SKI-304",
    "CS205": "SKI-404",
    "CS301": "SKI-505",
    "CS302": "SKI-203",
    "CS303": "SKI-306",
    "CS304": "SKI-606",
}

# Parakushtet (demonstrative): lënda -> lëndët që duhen kaluar më parë.
PREREQUISITES = {
    "SKI-201": ["SKI-101"],
    "SKI-206": ["SKI-106"],
    "SKI-301": ["SKI-201"],
    "SKI-303": ["SKI-101"],
    "SKI-305": ["SKI-201"],
    "SKI-402": ["SKI-302"],
    "SKI-404": ["SKI-301"],
    "SKI-405": ["SKI-303"],
    "SKI-406": ["SKI-305"],
    "SKI-502": ["SKI-404"],
    "SKI-504": ["SKI-404"],
    "SKI-505": ["SKI-406"],
    "SKI-506": ["SKI-304"],
    "SKI-601": ["SKI-404"],
    "SKI-605": ["SKI-504"],
}


def semester_ects(semester: int) -> int:
    return sum(ects for _, _, ects, number, _ in CURRICULUM if number == semester)
