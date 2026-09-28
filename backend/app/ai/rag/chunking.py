"""Ndarja e tekstit në fragmente për embeddings.

Fragmentet ndërtohen nga fjali të plota: një fjali e prerë në mes nuk
ka kuptim më vete, dhe embedding-u i saj bie larg pyetjes që i
përgjigjet. Fjalitë paketohen deri në `chunk_size` karaktere, dhe
fjalitë e fundit të një fragmenti (deri në `overlap` karaktere)
përsëriten në fillim të tjetrit, që përgjigjja të mos humbasë kur bie
në kufi mes dy fragmenteve.

Madhësia u zgjodh me matje: shih `evaluation/chunking_ablation.py`.
"""

import re

# Fund fjalie: pikë, pikëpyetje ose pikëçuditje, e ndjekur nga hapësirë.
# Numrat dhjetorë ("8.5") dhe orët ("09:00") nuk ndahen, sepse pas
# pikës nuk vjen hapësirë.
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _split_by_characters(
    text: str,
    chunk_size: int,
    overlap: int,
) -> list[str]:
    """Ndarja sipas karaktereve, për tekst pa kufij fjalish."""

    chunks: list[str] = []

    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - overlap

    return chunks


def split_text_into_chunks(
    text: str,
    chunk_size: int = 500,
    overlap: int = 120,
) -> list[str]:
    # Rreshtat e PDF-së janë thyerje faqosjeje, jo paragrafë.
    text = " ".join(text.split())

    if not text:
        return []

    sentences: list[str] = []

    for sentence in SENTENCE_END.split(text):
        # Një "fjali" më e gjatë se fragmenti (tabelë, listë pa pika)
        # ndahet sipas karaktereve, si më parë.
        if len(sentence) > chunk_size:
            sentences.extend(
                _split_by_characters(sentence, chunk_size, overlap)
            )
        else:
            sentences.append(sentence)

    chunks: list[str] = []
    current: list[str] = []
    current_length = 0

    for sentence in sentences:
        added = len(sentence) + (1 if current else 0)

        if current and current_length + added > chunk_size:
            chunks.append(" ".join(current))

            # Mbivendosja: fjalitë e fundit që nxënë brenda `overlap`.
            carried: list[str] = []
            carried_length = 0

            for previous in reversed(current):
                if carried_length + len(previous) > overlap:
                    break

                carried.insert(0, previous)
                carried_length += len(previous) + 1

            # Asnjë fragment nuk e kalon `chunk_size`, as me mbivendosje.
            if carried_length + len(sentence) > chunk_size:
                carried = []
                carried_length = 0

            current = carried
            current_length = max(carried_length - 1, 0)
            added = len(sentence) + (1 if current else 0)

        current.append(sentence)
        current_length += added

    if current:
        chunks.append(" ".join(current))

    return chunks
