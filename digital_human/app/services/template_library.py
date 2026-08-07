"""HF 视觉渲染模板库 (single source of truth for available templates).

Currently ships ONE template (``news-data-v1``) — vertically sliced for future
extension (``comparison-chart-v1`` / ``title-card-v1`` / ``quote-card-v1`` /
``timeline-v1`` etc.) without changing the orchestrator contract.
"""
from __future__ import annotations

from pathlib import Path


TEMPLATES: dict[str, dict] = {
    "news-magazine-v1": {
        "version": "1.0.0",
        "composition_id": "news_main",
        "source_dir": "news_magazine_v1",
        "index_html": "index.html",
        "avatar_asset": None,
        "duration_sec_range": [5, 30],
        "required_input": ["title", "metrics"],
        "json_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "minLength": 1, "maxLength": 64},
                "subtitle": {"type": "string", "maxLength": 128},
                "metrics": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 4,
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "value": {"type": "string"},
                            "emphasis": {"type": "boolean"},
                        },
                        "required": ["label", "value"],
                        "additionalProperties": False,
                    },
                },
                "chart": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["pie", "bar", "none"]},
                        "unit": {"type": "string"},
                        "growth": {"type": "string"},
                        "color_scheme": {"type": "string"},
                        "label": {"type": "string"},
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {"type": "string"},
                                    "value": {"type": "number"},
                                },
                                "required": ["label", "value"],
                            },
                        },
                    },
                },
                "caption": {"type": "string", "maxLength": 256},
                "source": {"type": "string", "maxLength": 128},
                "duration_sec": {"type": "integer", "minimum": 5, "maximum": 30},
                "assets": {"type": "object"},
            },
            "required": ["title", "metrics"],
            "additionalProperties": True,
        },
    },
    "news-magazine-v1-ls": {
        "version": "1.0.0",
        "composition_id": "news_main_ls",
        "source_dir": "news_magazine_v1_ls",
        "index_html": "index.html",
        "avatar_asset": None,
        "duration_sec_range": [5, 30],
        "required_input": ["title", "metrics"],
        "json_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "minLength": 1, "maxLength": 64},
                "subtitle": {"type": "string", "maxLength": 128},
                "metrics": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 4,
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "value": {"type": "string"},
                            "emphasis": {"type": "boolean"},
                        },
                        "required": ["label", "value"],
                        "additionalProperties": False,
                    },
                },
                "chart": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["pie", "bar", "none"]},
                        "unit": {"type": "string"},
                        "growth": {"type": "string"},
                        "color_scheme": {"type": "string"},
                        "label": {"type": "string"},
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {"type": "string"},
                                    "value": {"type": "number"},
                                },
                                "required": ["label", "value"],
                            },
                        },
                    },
                },
                "caption": {"type": "string", "maxLength": 256},
                "source": {"type": "string", "maxLength": 128},
                "duration_sec": {"type": "integer", "minimum": 5, "maximum": 30},
                "assets": {"type": "object"},
            },
            "required": ["title", "metrics"],
            "additionalProperties": True,
        },
    },
    "news-data-v1": {
        "version": "1.0.0",
        "composition_id": "news_main",
        "source_dir": "test_demo",
        "index_html": "index.html",
        "avatar_asset": "avatar.b64",
        "duration_sec_range": [5, 30],
        "required_input": ["title", "metrics"],
        "json_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "minLength": 1, "maxLength": 64},
                "subtitle": {"type": "string", "maxLength": 128},
                "metrics": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 4,
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "value": {"type": "string"},
                            "emphasis": {"type": "boolean"},
                        },
                        "required": ["label", "value"],
                        "additionalProperties": False,
                    },
                },
                "chart": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "unit": {"type": "string"},
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {"type": "string"},
                                    "value": {"type": "number"},
                                },
                                "required": ["label", "value"],
                            },
                        },
                    },
                },
                "caption": {"type": "string", "maxLength": 256},
                "source": {"type": "string", "maxLength": 128},
                "duration_sec": {"type": "integer", "minimum": 5, "maximum": 30},
                "assets": {"type": "object"},
            },
            "required": ["title", "metrics"],
            "additionalProperties": True,
        },
    },
}


def list_templates() -> list[dict]:
    """Return a list of all available template metadata (sans json_schema for brevity)."""
    out: list[dict] = []
    for tid, meta in TEMPLATES.items():
        out.append(
            {
                "template_id": tid,
                "version": meta["version"],
                "composition_id": meta["composition_id"],
                "duration_sec_range": meta["duration_sec_range"],
                "required_input": meta["required_input"],
            }
        )
    return out


def get_template(template_id: str) -> dict | None:
    """Return full template spec (including json_schema) or None if missing."""
    return TEMPLATES.get(template_id)


def resolve_template_dir(template_id: str, hf_template_root: str) -> Path:
    """Resolve the on-disk template directory for a given template id.

    Raises:
        FileNotFoundError: If the template id is unknown or its source dir is missing.
    """
    meta = TEMPLATES.get(template_id)
    if meta is None:
        raise FileNotFoundError(f"Unknown template_id: {template_id}")
    root = Path(hf_template_root)
    src = root / meta["source_dir"]
    if not src.is_dir():
        raise FileNotFoundError(f"Template source dir missing: {src}")
    return src


def validate_input(template_id: str, input_data: dict) -> None:
    """Run jsonschema validation. Raises ``jsonschema.ValidationError`` on failure.

    Imported lazily so the module loads even if jsonschema is not yet installed.
    """
    import jsonschema

    meta = TEMPLATES[template_id]
    jsonschema.validate(instance=input_data, schema=meta["json_schema"])