"""Bounded page-aware entry point for the existing case Copilot."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from agents.fictional_copilot import answer_fictional_case_question
from agents.imported_copilot import answer_imported_case_question
from data.fictional_intake import assess_fictional_case, fictional_intake_path, read_fictional_case
from data.knowledge_search import DB_PATH


PAGE_PURPOSE = {
    "Case Queue": "The Case Queue lists stored fictional alerts. Select an alert to investigate its recorded activity; an alert is not a fraud finding.",
    "Investigation Workspace": "The Investigation Workspace brings the selected case's records, evidence, Copilot questions, human decision, and audit history together.",
    "Evidence & RAG": "Evidence & RAG shows source text, exact indexed chunks, retrieval, and evidence gaps. An indexed passage is not independent verification.",
    "Compliance Queue": "The Compliance Queue shows cases a human has escalated for review; it does not file a regulatory report.",
    "Analytics": "Analytics summarizes the fictional alert population and recorded investigator activity; its charts do not determine guilt.",
    "Global Search": "Global Search finds stored fictional customers, accounts, and transactions; a search match is not a verified relationship.",
    "Admin — Knowledge Base": "The Knowledge Base inspector shows the stored retrieval sources and chunks used for guidance.",
    "Admin — Rule Config": "Rule Configuration previews and stores illustrative alert thresholds; a matched rule is a review signal.",
    "Home": "Home introduces InvestigateIQ and links to the investigation workflow.",
    "Project & Team": "Project & Team shows the project purpose and a draft team roster; listed responsibilities are proposals, not verified contributions.",
}


def _selected_case_chunk(case_id: str, chunk_id: str) -> dict | None:
    """Return only a real passage in this case/customer scope."""
    if case_id.startswith("FIC-CASE-"):
        with closing(sqlite3.connect(fictional_intake_path())) as conn:
            packet = read_fictional_case(conn, case_id)
            assessment = assess_fictional_case(conn, case_id)
        if not assessment["source_integrity_confirmed"]:
            return None
        return next((chunk for chunk in packet["chunks"] if chunk["chunk_id"] == chunk_id), None)
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT c.chunk_id, c.doc_id, c.chunk_text, s.verification_status "
            "FROM case_evidence_chunks c JOIN case_evidence_sources s ON s.doc_id=c.doc_id "
            "JOIN alerts a ON a.case_id=? AND a.customer_id=c.customer_id "
            "WHERE c.chunk_id=? AND (c.case_id IS NULL OR c.case_id=a.case_id)",
            (case_id, chunk_id),
        ).fetchone()
        return dict(row) if row else None


def answer_context_question(question: str, page: str, case_id: str | None = None,
                            chunk_id: str | None = None) -> dict:
    """Answer from explicit page/case/chunk context; never infer an unseen case."""
    query = " ".join(question.lower().split())
    if any(phrase in query for phrase in ("what am i looking at", "what is this page", "explain this page")):
        return {"answer": PAGE_PURPOSE.get(page, "This page has no registered Copilot description."),
                "chunk_ids": [], "txn_ids": [], "sources": [], "source": "page_context"}
    if not case_id:
        return {"answer": "No case is selected. Choose a case in Case Queue before asking about its facts or evidence.",
                "chunk_ids": [], "txn_ids": [], "sources": [], "source": "missing_case_context"}
    if any(phrase in query for phrase in ("this evidence", "this chunk", "selected evidence", "selected chunk")):
        if not chunk_id:
            return {"answer": "No evidence passage is selected. Open a case source on Evidence & RAG and choose a chunk first.",
                    "chunk_ids": [], "txn_ids": [], "sources": [], "source": "missing_evidence_context"}
        passage = _selected_case_chunk(case_id, chunk_id)
        if not passage:
            return {"answer": "That passage is not available in the selected case's evidence. No citation can be given.",
                    "chunk_ids": [], "txn_ids": [], "sources": [], "source": "invalid_evidence_context"}
        status = passage.get("verification_status") or "verification not recorded"
        return {"answer": (f"Selected passage {chunk_id} from {passage['doc_id']} (status: {status}). "
                           f"Exact indexed text: {passage['chunk_text']} "
                           "This text describes a stored fictional record; it does not independently verify an original document or prove lawful or unlawful funds."),
                "chunk_ids": [chunk_id], "txn_ids": [], "sources": [chunk_id], "source": "selected_evidence"}
    if case_id.startswith("FIC-CASE-"):
        with closing(sqlite3.connect(fictional_intake_path())) as conn:
            packet = read_fictional_case(conn, case_id)
            assessment = assess_fictional_case(conn, case_id)
        return answer_fictional_case_question(question, packet, assessment)
    cached_path = Path(__file__).resolve().parents[1] / "data" / "cached_reports" / f"{case_id}.json"
    saved_info = None
    if cached_path.is_file():
        saved = json.loads(cached_path.read_text(encoding="utf-8"))
        saved_info = {"generated_at": saved.get("generated_at"),
                      "case_chunk_count": len(saved.get("evidence", {}).get("case_chunks", [])),
                      "transaction_count": len(saved.get("evidence", {}).get("window_transactions", [])),
                      "document_count": len(saved.get("evidence", {}).get("documents", [])),
                      "guidance_count": len(saved.get("guidance", []))}
    return answer_imported_case_question(question, case_id, saved_report_info=saved_info)
