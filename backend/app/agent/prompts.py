"""T2.2: model prompts (Muse Spark only, temperature 0)."""

EXTRACTION_TOOL = {
    "type": "function",
    "name": "emit_extraction",
    "description": (
        "Emit the segmented clauses of a data-processing agreement plus one "
        "candidate fact per clause. Quote every clause body verbatim."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "clauses": {
                "type": "array",
                "minItems": 12,
                "maxItems": 12,
                "items": {
                    "type": "object",
                    "properties": {
                        "ref": {"type": "string"},
                        "heading": {"type": "string"},
                        "text": {"type": "string"},
                    },
                    "required": ["ref", "heading", "text"],
                    "additionalProperties": False,
                },
            },
            "facts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "statement": {"type": "string"},
                        "clause_ref": {"type": "string"},
                        "structured": {"type": "object"},
                    },
                    "required": ["statement", "clause_ref", "structured"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["clauses", "facts"],
        "additionalProperties": False,
    },
}


def build_extraction_input(document_text: str) -> str:
    """Build the single-shot extraction input for the Master DPA (T2.2, F3)."""
    return (
        "Segment the data-processing agreement below into its 12 numbered clauses "
        "(refs 1, 2, 3, 4, 5, 6, 7, 8, 9.1, 9.2, 10, 11). "
        "Call emit_extraction exactly once with ALL clauses and facts in that call. "
        "Quote each clause body verbatim: copy the exact characters, do not reword, "
        "summarise, or fix punctuation. "
        "For each clause give exactly one candidate fact: a concise statement of the "
        "clause's operative content, with clause_ref naming its clause and structured "
        "carrying at least {\"clause_ref\": ref} plus any numbers, dates, time limits, "
        "or party roles stated in the clause. "
        "The agreement is a fictional demo document; extract only what it says.\n\n"
        f"{document_text}"
    )
