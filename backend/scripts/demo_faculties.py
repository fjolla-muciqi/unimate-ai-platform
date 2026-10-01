"""Fakultetet shtesë të demos, me programe, lëndë dhe dokumente.

Fakulteti "Shkenca Kompjuterike dhe Inxhinieri" vjen nga `seed.py` dhe
`curriculum.py`; këtu shtohen tre fakultete të tjera, secili me program
trevjeçar, dy lëndë për semestër, një profesor me llogari dhe dokumentet
e veta.

Dokumentet e reja u përkasin vetëm fakulteteve të reja. Kështu
studentja demo (Shkenca Kompjuterike dhe Inxhinieri) kërkon në të njëjtat dokumente si
në vlerësimin e tezës, dhe rezultatet e saj mbeten të vlefshme.
"""

# Lëndët: (kodi, emri, ECTS, semestri, përshkrimi).
EXTRA_FACULTIES = [
    {
        "faculty": "Fakulteti i Ekonomisë dhe Menaxhmentit",
        "description": "Programet e ekonomisë, menaxhmentit dhe informatikës së biznesit.",
        "program": {
            "name": "Menaxhment dhe Informatikë Biznesi",
            "degree_level": "BACHELOR",
            "specialization": "Informatikë Biznesi",
            "total_ects": 180,
            "duration_years": 3,
            "description": "Menaxhment, financa dhe sisteme informative për biznesin.",
            "graduation_requirements": (
                "180 ECTS, praktika profesionale prej 6 javësh dhe "
                "mbrojtja e punimit të diplomës."
            ),
        },
        "professor": {
            "first_name": "Driton",
            "last_name": "Kelmendi",
            "title": "Prof. Asoc. Dr.",
            "email": "driton.kelmendi@unimate.edu",
            "office": "C-104",
            "consultation_hours": "E hënë 10:00-12:00, zyra C-104",
        },
        "teaches": ["EM201", "EM202", "EM204"],
        "courses": [
            ("EM101", "Hyrje në Ekonomi", 6, 1, "Kërkesa, oferta, tregjet dhe treguesit makroekonomikë."),
            ("EM102", "Matematikë për Biznes", 6, 1, "Funksionet, interesi i përbërë dhe optimizimi i thjeshtë."),
            ("EM103", "Kontabilitet Financiar", 6, 2, "Bilanci, pasqyra e të ardhurave dhe regjistrimet kontabël."),
            ("EM104", "Bazat e Menaxhmentit", 6, 2, "Planifikimi, organizimi, udhëheqja dhe kontrolli."),
            ("EM201", "Mikroekonomi", 6, 3, "Sjellja e konsumatorit, firmat dhe strukturat e tregut."),
            ("EM202", "Marketing", 6, 3, "Segmentimi, pozicionimi, marketingu digjital dhe hulumtimi i tregut."),
            ("EM203", "Statistikë Biznesi", 6, 4, "Statistika përshkruese, probabiliteti dhe regresioni."),
            ("EM204", "Menaxhim Financiar", 6, 4, "Buxhetimi, vlera në kohë e parasë dhe vendimet e investimit."),
            ("EM301", "Sisteme Informative të Biznesit", 6, 5, "ERP, bazat e të dhënave dhe analitika për vendimmarrje."),
            ("EM302", "Sipërmarrje", 6, 5, "Plani i biznesit, financimi dhe nisja e një ndërmarrjeje."),
            ("EM303", "Menaxhim Strategjik", 6, 6, "Analiza SWOT, avantazhi konkurrues dhe zbatimi i strategjisë."),
            ("EM304", "Punimi i Diplomës", 6, 6, "Hulumtimi dhe mbrojtja e punimit të diplomës."),
        ],
    },
    {
        "faculty": "Fakulteti Juridik",
        "description": "Programet e drejtësisë dhe të shkencave juridike.",
        "program": {
            "name": "Drejtësi",
            "degree_level": "BACHELOR",
            "specialization": "E Drejta Publike dhe Private",
            "total_ects": 180,
            "duration_years": 3,
            "description": "E drejta kushtetuese, penale, civile dhe ndërkombëtare.",
            "graduation_requirements": (
                "180 ECTS, klinika juridike prej 4 javësh dhe mbrojtja e "
                "punimit të diplomës."
            ),
        },
        "professor": {
            "first_name": "Vjosa",
            "last_name": "Gashi",
            "title": "Prof. Dr.",
            "email": "vjosa.gashi@unimate.edu",
            "office": "D-201",
            "consultation_hours": "E mërkurë 11:00-13:00, zyra D-201",
        },
        "teaches": ["JU201", "JU303"],
        "courses": [
            ("JU101", "Hyrje në të Drejtën", 6, 1, "Burimet e së drejtës, normat juridike dhe sistemet juridike."),
            ("JU102", "E Drejta Romake", 6, 1, "Institutet e së drejtës romake dhe ndikimi i tyre sot."),
            ("JU103", "E Drejta Kushtetuese", 6, 2, "Kushtetuta, ndarja e pushteteve dhe të drejtat themelore."),
            ("JU104", "Historia e Shtetit dhe e së Drejtës", 6, 2, "Zhvillimi i institucioneve shtetërore dhe juridike."),
            ("JU201", "E Drejta Penale", 6, 3, "Vepra penale, fajësia dhe sanksionet penale."),
            ("JU202", "E Drejta Civile", 6, 3, "Personat, pronësia, detyrimet dhe kontratat."),
            ("JU203", "E Drejta Administrative", 6, 4, "Administrata publike, aktet dhe procedura administrative."),
            ("JU204", "E Drejta e Punës", 6, 4, "Marrëdhënia e punës, kontrata dhe mbrojtja e punëtorit."),
            ("JU301", "E Drejta Ndërkombëtare Publike", 6, 5, "Shtetet, traktatet dhe organizatat ndërkombëtare."),
            ("JU302", "E Drejta e Biznesit", 6, 5, "Shoqëritë tregtare, kontratat tregtare dhe falimentimi."),
            ("JU303", "Procedura Penale", 6, 6, "Hetimi, akuza, gjykimi dhe mjetet juridike."),
            ("JU304", "Punimi i Diplomës", 6, 6, "Hulumtimi juridik dhe mbrojtja e punimit."),
        ],
    },
    {
        "faculty": "Fakulteti i Arkitekturës dhe Planifikimit Hapësinor",
        "description": "Programet e arkitekturës dhe të planifikimit urban.",
        "program": {
            "name": "Arkitekturë",
            "degree_level": "BACHELOR",
            "specialization": "Projektim Arkitektonik",
            "total_ects": 180,
            "duration_years": 3,
            "description": "Projektimi arkitektonik, konstruksionet dhe urbanistika.",
            "graduation_requirements": (
                "180 ECTS, portofoli përfundimtar dhe mbrojtja e projektit "
                "të diplomës."
            ),
        },
        "professor": {
            "first_name": "Besnik",
            "last_name": "Morina",
            "title": "Doc. Dr.",
            "email": "besnik.morina@unimate.edu",
            "office": "E-12",
            "consultation_hours": "E enjte 14:00-16:00, studio E-12",
        },
        "teaches": ["AR201", "AR203"],
        "courses": [
            ("AR101", "Bazat e Projektimit Arkitektonik", 8, 1, "Hapësira, forma, shkalla dhe kompozimi."),
            ("AR102", "Gjeometri Deskriptive", 6, 1, "Projeksionet, perspektiva dhe prerjet."),
            ("AR103", "Historia e Arkitekturës", 6, 2, "Arkitektura nga antikiteti deri në modernizëm."),
            ("AR104", "Vizatim Teknik dhe CAD", 6, 2, "Vizatimi teknik, AutoCAD dhe modelimi 3D."),
            ("AR201", "Studio Projektimi I", 8, 3, "Projektimi i një objekti banimi individual."),
            ("AR202", "Materialet dhe Konstruksionet", 6, 3, "Druri, betoni, çeliku dhe sistemet konstruktive."),
            ("AR203", "Studio Projektimi II", 8, 4, "Projektimi i një objekti publik me funksione të përziera."),
            ("AR204", "Urbanistikë", 6, 4, "Planifikimi urban, zonimi dhe hapësira publike."),
            ("AR301", "Arkitektura e Qëndrueshme", 6, 5, "Efiçienca e energjisë, materialet ekologjike dhe certifikimi."),
            ("AR302", "Instalimet në Ndërtesa", 6, 5, "Ngrohja, ventilimi, ujësjellësi dhe instalimet elektrike."),
            ("AR303", "Studio Projektimi III", 8, 6, "Projektim urban-arkitektonik në shkallë lagjeje."),
            ("AR304", "Projekti i Diplomës", 6, 6, "Projekti përfundimtar dhe mbrojtja para jurisë."),
        ],
    },
]


# Dokumentet e fakulteteve të reja. `faculty` ose `course` tregojnë
# kujt i përket dokumenti (shih `app/ai/rag/scope.py`).
FACULTY_DOCUMENTS: list[dict] = [
    {
        "file_name": "rregullorja-fakulteti-ekonomise.pdf",
        "title": "Rregullorja e Fakultetit të Ekonomisë dhe Menaxhmentit",
        "document_type": "REGULATION",
        "description": "Praktika profesionale, vlerësimi dhe punimi i diplomës.",
        "academic_year": "2025/2026",
        "faculty": "Fakulteti i Ekonomisë dhe Menaxhmentit",
        "pages": [
            [
                ("h1", "Rregullorja e Fakultetit të Ekonomisë dhe Menaxhmentit"),
                ("h2", "Neni 1 — Praktika profesionale"),
                ("p", "Studentët e vitit të tretë kryejnë praktikë profesionale "
                      "prej gjashtë javësh në një ndërmarrje ose institucion, "
                      "gjatë semestrit të pestë. Praktika vlerësohet me 6 kredite "
                      "ECTS dhe përfundon me një raport prej 10 deri në 15 "
                      "faqesh, të nënshkruar nga mentori në ndërmarrje."),
                ("h2", "Neni 2 — Vlerësimi"),
                ("p", "Nota përfundimtare në lëndët e fakultetit formohet nga "
                      "provimi përfundimtar me peshë 50 për qind, provimi i "
                      "ndërmjetëm me peshë 30 për qind dhe projekti në grup me "
                      "peshë 20 për qind. Projekti në grup realizohet nga "
                      "grupe prej tre deri në pesë studentësh."),
            ],
            [
                ("h2", "Neni 3 — Punimi i diplomës"),
                ("p", "Tema e punimit të diplomës regjistrohet deri më 31 mars "
                      "të vitit të tretë. Punimi ka 8 000 deri në 12 000 fjalë, "
                      "shkruhet sipas stilit të citimit APA dhe mbrohet para "
                      "një komisioni prej tre anëtarësh."),
                ("h2", "Neni 4 — Integriteti akademik"),
                ("p", "Çdo punim kontrollohet për plagjiaturë. Një ngjashmëri mbi "
                      "20 për qind me burime të pacituara sjell kthimin e "
                      "punimit për rishikim; përsëritja sjell masë disiplinore."),
            ],
        ],
    },
    {
        "file_name": "syllabus-em202-marketing.pdf",
        "title": "Syllabus: EM202 Marketing",
        "document_type": "SYLLABUS",
        "description": "Përmbajtja dhe vlerësimi i lëndës EM202.",
        "academic_year": "2025/2026",
        "course": "EM202",
        "pages": [
            [
                ("h1", "EM202 — Marketing"),
                ("h2", "Të dhënat e lëndës"),
                ("p", "Kodi: EM202. Kredite: 6 ECTS. Semestri: 3. Ligjërues: "
                      "Prof. Asoc. Dr. Driton Kelmendi, zyra C-104."),
                ("h2", "Përmbajtja"),
                ("p", "Javët 1-3: koncepti i marketingut dhe sjellja e "
                      "konsumatorit. Javët 4-6: segmentimi, targetimi dhe "
                      "pozicionimi. Javët 7-10: marketingu digjital, mediat "
                      "sociale dhe reklamimi. Javët 11-15: hulumtimi i tregut "
                      "dhe plani i marketingut."),
                ("h2", "Vlerësimi"),
                ("p", "Plani i marketingut për një produkt real 40 për qind, "
                      "provimi përfundimtar 45 për qind, pjesëmarrja 15 për "
                      "qind. Literatura: Kotler dhe Armstrong, Principles of "
                      "Marketing, botimi i 19-të."),
            ],
        ],
    },
    {
        "file_name": "rregullorja-fakulteti-juridik.pdf",
        "title": "Rregullorja e Fakultetit Juridik",
        "document_type": "REGULATION",
        "description": "Provimet me gojë, klinika juridike dhe frekuentimi.",
        "academic_year": "2025/2026",
        "faculty": "Fakulteti Juridik",
        "pages": [
            [
                ("h1", "Rregullorja e Fakultetit Juridik"),
                ("h2", "Neni 1 — Frekuentimi"),
                ("p", "Pjesëmarrja në ligjërata dhe ushtrime është e "
                      "detyrueshme në masën 75 për qind. Studenti që nuk e "
                      "plotëson këtë kusht nuk lejohet në provimin e rregullt "
                      "dhe e jep lëndën në afatin e shtatorit."),
                ("h2", "Neni 2 — Provimet"),
                ("p", "Provimet e lëndëve E Drejta Penale, E Drejta Civile dhe "
                      "Procedura Penale përbëhen nga një pjesë me shkrim dhe "
                      "një pjesë me gojë. Pjesa me gojë jepet vetëm pasi "
                      "studenti ka kaluar pjesën me shkrim me së paku 50 pikë."),
            ],
            [
                ("h2", "Neni 3 — Klinika juridike"),
                ("p", "Në vitin e tretë studentët kryejnë katër javë klinikë "
                      "juridike në gjykatë, prokurori ose zyrë avokatie, të "
                      "vlerësuara me 4 kredite ECTS. Klinika dokumentohet me "
                      "një ditar pune dhe një analizë rasti."),
                ("h2", "Neni 4 — Punimi i diplomës"),
                ("p", "Punimi i diplomës në drejtësi ka 10 000 deri në 15 000 "
                      "fjalë dhe citon legjislacionin dhe praktikën gjyqësore "
                      "me fusnota. Tema regjistrohet deri më 15 prill."),
            ],
        ],
    },
    {
        "file_name": "syllabus-ju201-e-drejta-penale.pdf",
        "title": "Syllabus: JU201 E Drejta Penale",
        "document_type": "SYLLABUS",
        "description": "Përmbajtja dhe vlerësimi i lëndës JU201.",
        "academic_year": "2025/2026",
        "course": "JU201",
        "pages": [
            [
                ("h1", "JU201 — E Drejta Penale"),
                ("h2", "Të dhënat e lëndës"),
                ("p", "Kodi: JU201. Kredite: 6 ECTS. Semestri: 3. Ligjëruese: "
                      "Prof. Dr. Vjosa Gashi, zyra D-201."),
                ("h2", "Përmbajtja"),
                ("p", "Javët 1-4: parimet e së drejtës penale dhe ligji penal "
                      "në kohë e hapësirë. Javët 5-9: vepra penale, elementet "
                      "e saj dhe fajësia. Javët 10-12: tentativa, "
                      "bashkëpunimi dhe shkaqet që përjashtojnë "
                      "përgjegjësinë. Javët 13-15: dënimet dhe masat "
                      "alternative."),
                ("h2", "Vlerësimi"),
                ("p", "Provimi me shkrim 60 për qind, provimi me gojë 30 për "
                      "qind, analiza e një vendimi gjyqësor 10 për qind. "
                      "Literatura bazë: Kodi Penal i Republikës së Kosovës."),
            ],
        ],
    },
    {
        "file_name": "rregullorja-fakulteti-arkitektures.pdf",
        "title": "Rregullorja e Fakultetit të Arkitekturës",
        "document_type": "REGULATION",
        "description": "Studiot, portofoli dhe laboratori i maketeve.",
        "academic_year": "2025/2026",
        "faculty": "Fakulteti i Arkitekturës dhe Planifikimit Hapësinor",
        "pages": [
            [
                ("h1", "Rregullorja e Fakultetit të Arkitekturës"),
                ("h2", "Neni 1 — Studiot e projektimit"),
                ("p", "Pjesëmarrja në studiot e projektimit është e "
                      "detyrueshme në masën 80 për qind. Çdo studio përfundon "
                      "me një prezantim para jurisë, ku studenti mbron "
                      "projektin me vizatime, poster dhe maket."),
                ("h2", "Neni 2 — Portofoli"),
                ("p", "Në fund të çdo viti akademik studenti dorëzon portofolin "
                      "vjetor me projektet e studiove, deri më 30 qershor. Pa "
                      "portofol të pranuar, studenti nuk kalon në vitin "
                      "pasardhës."),
            ],
            [
                ("h2", "Neni 3 — Laboratori i maketeve"),
                ("p", "Laboratori i maketeve është i hapur nga e hëna në të "
                      "premte, 08:00-18:00. Prerësi me lazer përdoret vetëm "
                      "pas trajnimit të sigurisë dhe me rezervim të paktën një "
                      "ditë më parë."),
                ("h2", "Neni 4 — Projekti i diplomës"),
                ("p", "Projekti i diplomës mbrohet para një jurie prej katër "
                      "anëtarësh, njëri prej të cilëve arkitekt praktikues "
                      "jashtë universitetit."),
            ],
        ],
    },
    {
        "file_name": "syllabus-ar201-studio-projektimi.pdf",
        "title": "Syllabus: AR201 Studio Projektimi I",
        "document_type": "SYLLABUS",
        "description": "Përmbajtja dhe vlerësimi i lëndës AR201.",
        "academic_year": "2025/2026",
        "course": "AR201",
        "pages": [
            [
                ("h1", "AR201 — Studio Projektimi I"),
                ("h2", "Të dhënat e lëndës"),
                ("p", "Kodi: AR201. Kredite: 8 ECTS. Semestri: 3. Ligjërues: "
                      "Doc. Dr. Besnik Morina, studio E-12."),
                ("h2", "Detyra e semestrit"),
                ("p", "Projektimi i një shtëpie familjare deri në 180 metra "
                      "katrorë në një parcelë reale në Prishtinë, nga analiza e "
                      "vendit deri te projekti ideor në shkallë 1:100."),
                ("h2", "Vlerësimi"),
                ("p", "Tri kritika të ndërmjetme 30 për qind, projekti "
                      "përfundimtar dhe maketi 60 për qind, skicat e ditarit "
                      "të projektimit 10 për qind."),
            ],
        ],
    },
]
