"""Java dhe lloji i materialit nga emri i skedarit."""

import pytest

from app.modules.documents.naming import (
    material_title,
    parse_material_type,
    parse_week,
)


@pytest.mark.parametrize(
    ("file_name", "week"),
    [
        ("Java03_Ligjerata.pdf", 3),
        ("Java 12 - Ushtrime.pdf", 12),
        ("Ligjërata 4.pdf", 4),
        ("Week_07_Lecture.pdf", 7),
        ("W10.pdf", 10),
        ("03 - Hash tabelat.pdf", 3),
        ("CS201_Java05_Pemet.pdf", 5),
        ("Hyrje ne algoritme.pdf", None),
        ("news2.pdf", None),
        ("Java 40.pdf", None),
    ],
)
def test_week_is_read_from_the_file_name(file_name, week):
    assert parse_week(file_name) == week


@pytest.mark.parametrize(
    ("file_name", "material_type"),
    [
        ("Java03_Ligjerata.pdf", "LECTURE"),
        ("Week 2 Lecture slides.pdf", "LECTURE"),
        ("Java03_Ushtrime.pdf", "EXERCISE"),
        ("Lab 4.pdf", "EXERCISE"),
        ("Ligjerata me ushtrime 5.pdf", "EXERCISE"),
        ("Java 3.pdf", None),
    ],
)
def test_material_type_is_read_from_the_file_name(file_name, material_type):
    assert parse_material_type(file_name) == material_type


def test_title_names_course_week_type_and_group():
    assert (
        material_title("CS201", 4, "LECTURE", "Grupi A", "x.pdf")
        == "CS201 · Java 4 · Ligjëratë · Grupi A"
    )
    assert material_title("CS201", None, None, None, "Hyrje.pdf") == "Hyrje"
