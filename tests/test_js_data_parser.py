"""Tests for JS asset parsing and publication document building."""

from src.ingestion.js_data_ingester import (
    infer_publication_category,
    publication_to_document,
    strip_html,
)
from src.ingestion.js_data_parser import parse_js_window_array

SAMPLE_REFERENCE_JS = """
window.publications = [
  {
    "id": "J32",
    "title": "Example <i>Paper</i> Title",
    "published": "Published in <i>Journal</i>, 2024",
    "authors": "Smith, A., Doe, B.",
    "download_link": "https://doi.org/10.1234/example",
    "abstract": "A short abstract.",
    "citation": "Smith, A. (2024). Example."
  },
  {
    "id": "BC5",
    "title": "Book chapter title",
    "authors": "Author, X.",
    "abstract": "Chapter abstract.",
    "citation": "Author, X. (2025). Chapter."
  }
];
"""


def test_parse_publications_strict():
    pubs = parse_js_window_array(SAMPLE_REFERENCE_JS, "publications", relaxed=False)
    assert len(pubs) == 2
    assert pubs[0]["id"] == "J32"


def test_infer_publication_category():
    assert infer_publication_category("J32") == "journal"
    assert infer_publication_category("C12") == "conference"
    assert infer_publication_category("B2") == "book"
    assert infer_publication_category("BC5") == "book_chapter"


def test_strip_html():
    assert strip_html("Published by <i>Springer</i>, 2015") == "Published by Springer, 2015"


def test_publication_to_document():
    doc = publication_to_document(
        {
            "id": "J32",
            "title": "VR Study",
            "authors": "Antons, J.-N.",
            "published": "Journal 2024",
            "abstract": "We studied VR.",
            "citation": "Antons (2024).",
            "download_link": "https://doi.org/10.1/example",
        },
        "https://immersive-reality-lab.de",
    )
    assert doc["metadata"]["doc_type"] == "publication"
    assert doc["metadata"]["pub_id"] == "J32"
    assert doc["metadata"]["category"] == "journal"
    assert "VR Study" in doc["content"]
    assert "We studied VR." in doc["content"]
    assert doc["url"].endswith("publicationDetail.html?id=J32")
