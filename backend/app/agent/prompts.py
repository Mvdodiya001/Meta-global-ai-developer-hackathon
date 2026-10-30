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


CLAIM_TOOL = {
    "type": "function",
    "name": "emit_claim",
    "description": (
        "Type one user question about the agreement as CT1 numeric_bound, "
        "CT2 required_element, CT3 in_force_on, CT4 role_applies, or UNKNOWN "
        "with an explanation when no type fits."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "claim_type": {"type": "string"},
            "params": {"type": "object"},
            "question_text": {"type": "string"},
            "explanation": {"type": "string"},
        },
        "required": ["claim_type", "params", "question_text"],
        "additionalProperties": False,
    },
}

CLAIM_TYPES = (
    "CT1 numeric_bound: the question compares a stated number (with unit) "
    'against a required bound. params: {"subject", "value" (number), "unit"}.\n'
    "CT2 required_element: the question asks whether the agreement requires "
    'a specific element or duty. params: {"element"}.\n'
    "CT3 in_force_on: the question asks whether a duty applies on a date. "
    'params: {"date" (YYYY-MM-DD), "subject"}; copy the date from the '
    "question, never invent one.\n"
    "CT4 role_applies: the question asks whether a party holds a role under "
    'the agreement. params: {"party", "role"}.\n'
    "UNKNOWN: opinion, summary, or anything no closed type can test. "
    "params: {} and a one-sentence explanation of why no type fits."
)


def build_claim_input(question: str, inventory: str, as_of: str) -> str:
    """Build the single-shot claim-typing input (T2.3)."""
    return (
        "Type the user question about the data-processing agreement below as exactly "
        "one closed claim type, or UNKNOWN. Call emit_claim exactly once. "
        "Type by what the question ASKS, not by what the answer might be. "
        f"Today is {as_of}; resolve relative dates against it.\n\n"
        "Clause inventory (ref + heading):\n"
        f"{inventory}\n\n"
        f"User question: {question}\n\n"
        f"Closed types:\n{CLAIM_TYPES}"
    )


def build_proof_input(
    question: str,
    claim_type: str,
    params: dict[str, object],
    as_of: str,
    matter_id: str,
    clause_ref: str,
    clause_heading: str,
    clause_text: str,
    inventory: str,
    fact_lines: list[str],
    source_lines: list[str],
) -> str:
    """Build the proof-drafting input for the agent loop (T2.5, F5)."""
    return (
        "Draft a deterministic proof for the claim below using ONLY the six tools. "
        "Each tool call counts toward a 12-call budget; plan for at most "
        "lookup_source, get_premise, verify_derivation and propose_finding. "
        "Do NOT call list_dependent_claims or request_lawyer_review — they "
        "belong to other tasks and only waste your budget. "
        "Always call lookup_source for the cited source before proposing, and "
        "always call verify_derivation on the exact proof object before "
        "propose_finding — propose only a proof the checker accepted. "
        "Cite only admitted premises (lawyer_confirmed or document_extracted). "
        "Quote provision and clause text verbatim. "
        "When the checker rejects a draft, fix the flagged steps and retry. "
        "End with propose_finding carrying the full proof object.\n\n"
        f"Session matter: {matter_id}. Use the ids below EXACTLY as written — "
        "never invent, shorten or reformat an id.\n\n"
        f"Claim: {question}\n"
        f"Claim type: {claim_type} params: {params}\n"
        f"As of: {as_of}\n\n"
        f"Target clause {clause_ref} {clause_heading}:\n{clause_text}\n\n"
        "Clause inventory (ref + heading):\n"
        f"{inventory}\n\n"
        "Sources (id | key | title):\n"
        + "\n".join(source_lines)
        + "\n\n"
        "Admitted premises (id | trust class | clause | statement):\n"
        + "\n".join(fact_lines)
        + "\n\n"
        "The proof object has exactly these fields: claim_id, as_of "
        '(YYYY-MM-DD, copy from "As of" above), conclusion ("holds" or '
        '"does not hold"), premises (list of {fact_id, statement, trust_class} '
        "copied verbatim from the admitted premises above), steps (list of "
        "step objects, the last one a conclude step). "
        "Step kinds and their fields: "
        'cite_fact {fact_id}; '
        "cite_rule {rule_card_id, citation {source_version_id, provision_id, "
        "span [start, end], sha256}} where the citation copies one provision "
        "from a lookup_source result (span [0, len(text)] of that provision, "
        "sha256 as returned); "
        "in_force {provision_id}; "
        "compare {value (number), op (one of <=, >=, ==, <, >), bound (number)}; "
        "contains_element {clause_id, quote} where quote is a verbatim "
        "substring of the target clause text above; "
        "role_applies {party, role, clause_id, quote} with the same verbatim "
        "quote rule; "
        'conclude {conclusion} repeating the proof conclusion. '
        "Prefer the smallest proof the checker accepts. "
        "The moment verify_derivation returns valid true, call propose_finding "
        "in the very next turn with the byte-identical proof object.\n"
    )


CHALLENGER_TOOL = {
    "type": "function",
    "name": "emit_objections",
    "description": (
        "Return structured objections to a draft proof, or an empty list "
        "to endorse it. blocking means the proof is invalid as drafted; "
        "note means a concern that does not invalidate it."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "objections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "severity": {"type": "string"},
                        "reason": {"type": "string"},
                        "quote": {"type": "string"},
                    },
                    "required": ["severity", "reason"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["objections"],
        "additionalProperties": False,
    },
}


def build_challenger_input(
    question: str,
    claim_type: str,
    params: dict[str, object],
    proof: dict[str, object],
    premise_lines: list[str],
    card_lines: list[str],
) -> str:
    """Build the skeptical second-pass review input (T6.1, F17).

    Deliberately different from the drafting prompt: no tools, no
    budget, no proof schema lesson — only the finished draft and the
    evidence to check it against.
    """
    return (
        "You are a skeptical reviewer, not the drafter. Below is a finished "
        "proof for the claim, plus the admitted premises and rule cards it "
        "may use. Your job is to try to break the proof.\n\n"
        "Check each item in order: (1) every cited premise appears verbatim "
        "in the admitted list with the same statement and an admitted trust "
        "class (lawyer_confirmed or document_extracted); (2) every cited "
        "rule card exists in the card list and the proof uses it for the "
        "right claim type; (3) every quoted string is a plausible verbatim "
        "quote; (4) the conclusion follows from the cited steps.\n\n"
        "Call emit_objections exactly once. blocking = the proof is invalid "
        "as drafted (name the failing check); note = a real concern that "
        "does not invalidate it. An empty objections list endorses the "
        "proof. Quote the offending proof text in quote when there is one.\n\n"
        f"Claim: {question}\n"
        f"Claim type: {claim_type} params: {params}\n\n"
        "Draft proof:\n"
        f"{proof}\n\n"
        "Admitted premises (id | trust class | clause | statement):\n"
        + "\n".join(premise_lines)
        + "\n\n"
        "Rule cards (id | claim type | provision | interpretation):\n"
        + "\n".join(card_lines)
        + "\n"
    )


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
