"""Fakultetet shtesë të demos, me programe, lëndë dhe dokumente FIKTIVE.

Fakulteti kryesor, "Shkenca Kompjuterike dhe Inxhinieri", vjen nga
`seed.py` dhe `curriculum.py`. Këtu janë katër fakultete dytësore, secili
me program trevjeçar, dy lëndë për semestër, një profesor fiktiv me
llogari dhe dy dokumente fiktive (rregullorja dhe një syllabus).

Ekzistojnë që kufizimi sipas fakultetit të provohet me të dhëna të
huaja: studentët e Shkencave Kompjuterike nuk duhet t'i shohin këto
dokumente. Asnjë e dhënë këtu nuk i përket një personi ose institucioni
real.
"""

FICTIONAL = "Dokument fiktiv për demonstrim. "

# Lëndët: (kodi, emri, ECTS, semestri, përshkrimi).
EXTRA_FACULTIES = [
    {
        "faculty": "Menaxhment, Biznes dhe Ekonomi",
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
        "faculty": "Shkenca Politike",
        "description": "Programet e shkencave politike dhe të marrëdhënieve ndërkombëtare.",
        "program": {
            "name": "Shkenca Politike",
            "degree_level": "BACHELOR",
            "specialization": "Marrëdhënie Ndërkombëtare",
            "total_ects": 180,
            "duration_years": 3,
            "description": "Sistemet politike, politikat publike dhe marrëdhëniet ndërkombëtare.",
            "graduation_requirements": (
                "180 ECTS, pjesëmarrja në simulimin e Kombeve të Bashkuara "
                "dhe mbrojtja e punimit të diplomës."
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
        "teaches": ["SP201", "SP303"],
        "courses": [
            ("SP101", "Hyrje në Shkenca Politike", 6, 1, "Shteti, pushteti, legjitimiteti dhe ideologjitë politike."),
            ("SP102", "Historia e Mendimit Politik", 6, 1, "Nga Platoni dhe Aristoteli te mendimi politik modern."),
            ("SP103", "Sistemet Politike Krahasuese", 6, 2, "Sistemet parlamentare, presidenciale dhe gjysmëpresidenciale."),
            ("SP104", "Metodat e Kërkimit në Shkencat Sociale", 6, 2, "Pyetësorët, intervistat, analiza e përmbajtjes dhe statistika bazë."),
            ("SP201", "Marrëdhëniet Ndërkombëtare", 6, 3, "Teoritë realiste, liberale dhe konstruktiviste; sistemi ndërkombëtar."),
            ("SP202", "Politikat Publike", 6, 3, "Cikli i politikave publike, hartimi, zbatimi dhe vlerësimi."),
            ("SP203", "Integrimi Evropian", 6, 4, "Institucionet e Bashkimit Evropian dhe procesi i zgjerimit."),
            ("SP204", "Administrata Publike", 6, 4, "Organizimi i administratës, shërbimi civil dhe reforma."),
            ("SP301", "Sjellja Politike dhe Zgjedhjet", 6, 5, "Sistemet zgjedhore, partitë dhe sjellja e votuesve."),
            ("SP302", "Diplomacia dhe Negociatat", 6, 5, "Diplomacia bilaterale dhe multilaterale, teknikat e negocimit."),
            ("SP303", "Siguria Ndërkombëtare", 6, 6, "Konfliktet, aleancat, terrorizmi dhe siguria njerëzore."),
            ("SP304", "Punimi i Diplomës", 6, 6, "Hulumtimi politologjik dhe mbrojtja e punimit."),
        ],
    },
    {
        "faculty": "Media dhe Komunikim",
        "description": "Programet e gazetarisë, medias digjitale dhe komunikimit.",
        "program": {
            "name": "Media dhe Komunikim",
            "degree_level": "BACHELOR",
            "specialization": "Media Digjitale",
            "total_ects": 180,
            "duration_years": 3,
            "description": "Gazetaria, prodhimi mediatik dhe komunikimi strategjik.",
            "graduation_requirements": (
                "180 ECTS, praktika në redaksi prej 4 javësh, portofoli me "
                "punime të publikuara dhe mbrojtja e punimit të diplomës."
            ),
        },
        "professor": {
            "first_name": "Dafina",
            "last_name": "Hasani",
            "title": "Doc. Dr.",
            "email": "dafina.hasani@unimate.edu",
            "office": "F-08",
            "consultation_hours": "E martë 13:00-15:00, zyra F-08",
        },
        "teaches": ["MK201", "MK301"],
        "courses": [
            ("MK101", "Hyrje në Komunikim", 6, 1, "Modelet e komunikimit, komunikimi masiv dhe ndërpersonal."),
            ("MK102", "Historia e Medias", 6, 1, "Shtypi, radioja, televizioni dhe interneti."),
            ("MK103", "Shkrimi Gazetaresk", 6, 2, "Lajmi, reportazhi, intervista dhe redaktimi."),
            ("MK104", "Fotografia Digjitale", 6, 2, "Kompozimi, drita dhe përpunimi i fotografisë."),
            ("MK201", "Komunikimi Digjital dhe Mediat Sociale", 6, 3, "Platformat sociale, algoritmet, përmbajtja dhe analitika."),
            ("MK202", "Etika e Medias", 6, 3, "Kodet etike, privatësia, burimet dhe dezinformimi."),
            ("MK203", "Prodhimi Audio-Vizual", 6, 4, "Skenari, xhirimi, montazhi dhe zëri."),
            ("MK204", "Marrëdhëniet me Publikun", 6, 4, "Komunikimi institucional, krizat dhe mediat."),
            ("MK301", "Gazetaria Hulumtuese", 6, 5, "Verifikimi i fakteve, të dhënat dhe dokumentet publike."),
            ("MK302", "Analiza e Audiencës", 6, 5, "Matja e audiencës, sondazhet dhe analitika digjitale."),
            ("MK303", "Komunikimi Strategjik", 6, 6, "Fushatat, mesazhet dhe planifikimi i komunikimit."),
            ("MK304", "Punimi i Diplomës", 6, 6, "Projekti mediatik ose hulumtimi dhe mbrojtja e tij."),
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
        "title": "Rregullorja e Fakultetit Menaxhment, Biznes dhe Ekonomi",
        "document_type": "REGULATION",
        "description": FICTIONAL + "Praktika profesionale, vlerësimi dhe punimi i diplomës.",
        "academic_year": "2025/2026",
        "faculty": "Menaxhment, Biznes dhe Ekonomi",
        "pages": [
            [
                ("h1", "Rregullorja e Fakultetit Menaxhment, Biznes dhe Ekonomi"),
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
        "description": FICTIONAL + "Përmbajtja dhe vlerësimi i lëndës EM202.",
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
        "file_name": "rregullorja-fakulteti-shkenca-politike.pdf",
        "title": "Rregullorja e Fakultetit Shkenca Politike",
        "document_type": "REGULATION",
        "description": FICTIONAL + "Frekuentimi, esetë seminarike, simulimi i OKB-së dhe diploma.",
        "academic_year": "2026/2027",
        "faculty": "Shkenca Politike",
        "pages": [
            [
                ("h1", "Rregullorja e Fakultetit Shkenca Politike"),
                ("h2", "Neni 1 — Frekuentimi"),
                ("p", "Pjesëmarrja në seminare është e detyrueshme në masën 70 "
                      "për qind. Studenti që mungon më shumë se katër seminare "
                      "pa arsye të dokumentuar humb të drejtën për eseun "
                      "seminarik të asaj lënde."),
                ("h2", "Neni 2 — Eseu seminarik"),
                ("p", "Çdo lëndë e vitit të dytë dhe të tretë kërkon një ese "
                      "seminarike prej 2 500 deri në 3 500 fjalë, e shkruar "
                      "sipas stilit të citimit Chicago. Eseu dorëzohet në javën "
                      "e dymbëdhjetë dhe vlen 25 për qind të notës."),
            ],
            [
                ("h2", "Neni 3 — Simulimi i Kombeve të Bashkuara"),
                ("p", "Në semestrin e pestë studentët marrin pjesë në një "
                      "simulim dy-ditor të Asamblesë së Përgjithshme të OKB-së, "
                      "ku përfaqësojnë një shtet të caktuar me short. Simulimi "
                      "vlerësohet me 3 kredite ECTS dhe është kusht për "
                      "diplomim."),
                ("h2", "Neni 4 — Punimi i diplomës"),
                ("p", "Punimi i diplomës ka 9 000 deri në 12 000 fjalë. Tema "
                      "regjistrohet deri më 1 prill të vitit të tretë, me "
                      "miratimin e mentorit, dhe mbrohet para një komisioni "
                      "prej tre anëtarësh."),
            ],
        ],
    },
    {
        "file_name": "syllabus-sp201-marredheniet-nderkombetare.pdf",
        "title": "Syllabus: SP201 Marrëdhëniet Ndërkombëtare",
        "document_type": "SYLLABUS",
        "description": FICTIONAL + "Përmbajtja dhe vlerësimi i lëndës SP201.",
        "academic_year": "2026/2027",
        "course": "SP201",
        "pages": [
            [
                ("h1", "SP201 — Marrëdhëniet Ndërkombëtare"),
                ("h2", "Të dhënat e lëndës"),
                ("p", "Kodi: SP201. Kredite: 6 ECTS. Semestri: 3. Ligjëruese: "
                      "Prof. Dr. Vjosa Gashi, zyra D-201."),
                ("h2", "Përmbajtja"),
                ("p", "Javët 1-3: sistemi ndërkombëtar dhe aktorët e tij. "
                      "Javët 4-7: realizmi, liberalizmi dhe konstruktivizmi. "
                      "Javët 8-11: organizatat ndërkombëtare dhe e drejta "
                      "ndërkombëtare. Javët 12-15: globalizimi, ekonomia "
                      "politike ndërkombëtare dhe sfidat e reja."),
                ("h2", "Vlerësimi"),
                ("p", "Provimi përfundimtar 50 për qind, eseu seminarik 25 për "
                      "qind, prezantimi i një krize ndërkombëtare 15 për qind, "
                      "pjesëmarrja 10 për qind. Literatura: Baylis, Smith dhe "
                      "Owens, The Globalization of World Politics."),
            ],
        ],
    },
    {
        "file_name": "rregullorja-fakulteti-media-komunikim.pdf",
        "title": "Rregullorja e Fakultetit Media dhe Komunikim",
        "document_type": "REGULATION",
        "description": FICTIONAL + "Studiot, praktika në redaksi, etika dhe portofoli.",
        "academic_year": "2026/2027",
        "faculty": "Media dhe Komunikim",
        "pages": [
            [
                ("h1", "Rregullorja e Fakultetit Media dhe Komunikim"),
                ("h2", "Neni 1 — Studiot e radios dhe televizionit"),
                ("p", "Studiot rezervohen përmes zyrës teknike të paktën dy "
                      "ditë më parë, për blloqe deri në tri orë. Pajisjet e "
                      "xhirimit merren me nënshkrim dhe kthehen brenda 48 "
                      "orësh; dëmtimi i pakujdesshëm paguhet nga studenti."),
                ("h2", "Neni 2 — Praktika në redaksi"),
                ("p", "Në semestrin e pestë studentët kryejnë praktikë prej "
                      "katër javësh në një redaksi, agjenci komunikimi ose "
                      "institucion publik. Praktika vlen 4 kredite ECTS dhe "
                      "dokumentohet me tri punime të publikuara."),
            ],
            [
                ("h2", "Neni 3 — Etika"),
                ("p", "Përdorimi i burimeve anonime në punimet e studentëve "
                      "kërkon miratimin paraprak të mentorit. Fotografitë e "
                      "personave të identifikueshëm publikohen vetëm me "
                      "pëlqimin e tyre të shkruar."),
                ("h2", "Neni 4 — Portofoli dhe diploma"),
                ("p", "Para mbrojtjes së diplomës, studenti dorëzon portofolin "
                      "me së paku dhjetë punime, nga të cilat të paktën tri të "
                      "publikuara. Tema e diplomës regjistrohet deri më 15 "
                      "mars të vitit të tretë."),
            ],
        ],
    },
    {
        "file_name": "syllabus-mk201-komunikimi-digjital.pdf",
        "title": "Syllabus: MK201 Komunikimi Digjital dhe Mediat Sociale",
        "document_type": "SYLLABUS",
        "description": FICTIONAL + "Përmbajtja dhe vlerësimi i lëndës MK201.",
        "academic_year": "2026/2027",
        "course": "MK201",
        "pages": [
            [
                ("h1", "MK201 — Komunikimi Digjital dhe Mediat Sociale"),
                ("h2", "Të dhënat e lëndës"),
                ("p", "Kodi: MK201. Kredite: 6 ECTS. Semestri: 3. Ligjëruese: "
                      "Doc. Dr. Dafina Hasani, zyra F-08."),
                ("h2", "Përmbajtja"),
                ("p", "Javët 1-4: platformat sociale dhe ekonomia e "
                      "vëmendjes. Javët 5-8: algoritmet e renditjes dhe "
                      "krijimi i përmbajtjes. Javët 9-12: analitika e "
                      "angazhimit dhe fushatat digjitale. Javët 13-15: "
                      "dezinformimi dhe verifikimi i fakteve."),
                ("h2", "Vlerësimi"),
                ("p", "Fushata digjitale në grup 40 për qind, provimi "
                      "përfundimtar 40 për qind, raporti analitik individual "
                      "20 për qind."),
            ],
        ],
    },
    {
        "file_name": "rregullorja-fakulteti-arkitektures.pdf",
        "title": "Rregullorja e Fakultetit të Arkitekturës",
        "document_type": "REGULATION",
        "description": FICTIONAL + "Studiot, portofoli dhe laboratori i maketeve.",
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
        "description": FICTIONAL + "Përmbajtja dhe vlerësimi i lëndës AR201.",
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
