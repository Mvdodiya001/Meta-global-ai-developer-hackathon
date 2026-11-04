"""Intake domain: documents/audio in, proposed evidence out.

Owns: clause extraction from text, scanned-page transcription (vision),
and voice dictation (ASR). Everything intake produces is *proposed*
evidence: facts become document_extracted only when stored against a
document version by the matters/API layer, and voice facts stay
ai_inferred until a lawyer approves them (premises flow, evidence).

Public interface: extract, scan, transcribe. The model gateway and
prompts stay in `app.agent` (shared model boundary).
Forbidden: deciding findings; admitting premises.
"""

from app.modules.intake import docx, extract, scan, transcribe

__all__ = ["docx", "extract", "scan", "transcribe"]
