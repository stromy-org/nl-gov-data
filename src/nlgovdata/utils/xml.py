"""SRU XML parsing helpers for KOOP responses."""

from __future__ import annotations

from typing import Any
from xml.etree.ElementTree import Element

from defusedxml import ElementTree as DET

NAMESPACES = {
    "zs": "http://www.loc.gov/zing/srw/",
    "gzd": "http://standaarden.overheid.nl/sru",
    "owms": "http://standaarden.overheid.nl/owms/terms/",
    "owmskern": "http://standaarden.overheid.nl/owms/terms/",
    "dt": "http://purl.org/dc/terms/",
    "w": "http://repository.overheid.nl/frbr/work/",
    "c": "http://standaarden.overheid.nl/cpv/",
}


def _text(node: Element | None) -> str | None:
    if node is None or node.text is None:
        return None
    value = node.text.strip()
    return value or None


def _first_text(root: Element, *paths: str) -> str | None:
    for path in paths:
        value = _text(root.find(path, NAMESPACES))
        if value:
            return value
    return None


def _record_to_dict(record: Element) -> dict[str, Any]:
    record_data = record.find(".//zs:recordData", NAMESPACES)
    if record_data is None:
        return {}

    identifier = _first_text(
        record_data,
        ".//owmskern:identifier",
        ".//identifier",
    )
    return {
        "identifier": identifier,
        "title": _first_text(record_data, ".//owmskern:title", ".//title"),
        "type": _first_text(record_data, ".//dt:type"),
        "modified": _first_text(record_data, ".//dt:modified"),
        "available": _first_text(record_data, ".//dt:available"),
        "issued": _first_text(record_data, ".//dt:issued"),
        "creator": _first_text(record_data, ".//dt:creator"),
        "summary": _first_text(record_data, ".//dt:description", ".//owmskern:description"),
        "dossier_number": _first_text(record_data, ".//w:dossiernummer"),
        "dossier_sub_number": _first_text(record_data, ".//w:ondernummer"),
        "subrubriek": _first_text(record_data, ".//w:subrubriek"),
        "product_area": _first_text(record_data, ".//c:product-area"),
        "preferred_url": _first_text(record_data, ".//gzd:preferred-url"),
        "portal_url": _first_text(record_data, ".//gzd:portal-url"),
        "pdf_url": _first_text(record_data, ".//gzd:pdf-url"),
        "metadata": {
            "record_identifier": _first_text(record, ".//zs:recordIdentifier"),
            "record_position": _first_text(record, ".//zs:recordPosition"),
        },
    }


def parse_koop_search_response(xml_text: str) -> dict[str, Any]:
    root = DET.fromstring(xml_text)
    count_text = _first_text(root, ".//zs:numberOfRecords")
    next_position = _first_text(root, ".//zs:nextRecordPosition")
    records = [_record_to_dict(record) for record in root.findall(".//zs:record", NAMESPACES)]
    return {
        "total_count": int(count_text or 0),
        "next_record_position": int(next_position) if next_position else None,
        "records": records,
    }
