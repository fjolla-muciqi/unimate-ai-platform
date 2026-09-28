from datetime import UTC, datetime


def utcnow() -> datetime:
    """Koha aktuale në UTC, pa zonë kohore.

    Kolonat e bazës janë `DateTime` pa zonë dhe ruajnë UTC. Kjo
    zëvendëson `datetime.utcnow()`, që është i vjetëruar që nga
    Python 3.12, pa ndryshuar vlerat që shkruhen në bazë.
    """

    return datetime.now(UTC).replace(tzinfo=None)
