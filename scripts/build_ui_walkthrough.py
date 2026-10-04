"""Build a narrated, animated guide from captured public app screens.

The captured screens live in assets/walkthrough_screens. Cursor movement,
click rings, and page transitions are animated explanations, not a claim that
this MP4 is an unedited screen recording. All customer data is fictional.
"""

from __future__ import annotations

import os
import math
import re
import subprocess
import sys
import tempfile
import textwrap
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

try:
    from .build_walkthrough import find_ffmpeg, join_narration, synthesize_narration
except ImportError:  # Direct invocation: python scripts/build_ui_walkthrough.py
    from build_walkthrough import find_ffmpeg, join_narration, synthesize_narration


ROOT = Path(__file__).resolve().parents[1]
SCREENS = ROOT / "assets" / "walkthrough_screens"
OUTPUT = ROOT / "assets" / "investigateiq_walkthrough.mp4"
POSTER = ROOT / "assets" / "investigateiq_walkthrough_poster.png"
SUBTITLES = ROOT / "assets" / "investigateiq_walkthrough.vtt"
WIDTH, HEIGHT, FPS = 1280, 720, 12
VIDEO_TITLE = "InvestigateIQ: Evidence-to-Decision Walkthrough"
FONT = Path(r"C:\Windows\Fonts\segoeui.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\segoeuib.ttf")

# Screenshot scenes come from the deployed public application. The
# diagram scenes are explicitly explanatory graphics. Cursor movement is
# animation, not footage of an unedited interaction. CASE-041's sample
# decision form was not submitted in this capture.
SCENES = [
    {"screen": "41_public_floating_home_guest.png", "title": VIDEO_TITLE,
     "narration": "Welcome to Investigate IQ, an investigation copilot for reviewing banking alerts. We will follow Case zero four one from its alert through transactions, a cited draft, evidence retrieval, and a human next step. We will then open a separate fictional intake packet to show how a new numeric case is actually stored and recalculated. Both paths use fabricated data. Neither determines whether money is legal or illegal, and neither files a regulatory report.",
     "caption": "One case, every screen, and the full evidence trail.", "target": None},
    {"screen": "02_public_identity.png", "title": "1 · Enter the Workspace",
     "narration": "We begin on Home. Enter a display name, here Case Reviewer, and choose the Investigator workflow role. Then open the workspace. The name helps attribute actions inside Investigate IQ; it is not bank-grade login or identity verification. Later, if a decision is submitted, the product requires a written rationale and saves the action to its audit history. Selecting a role alone does not make a decision.",
     "caption": "Display name → Investigator role → Open workspace", "target": (1010, 385)},
    {"screen": "42_public_floating_home_ready.png", "title": "The End-to-End Route",
     "visual": "journey", "narration": "Here is the route we will actually follow. A fictional monitoring alert enters the Case Queue. The investigator opens the case, checks source transactions, and reads the copilot's draft. Evidence and R A G shows exactly which synthetic playbook document was indexed and what chunks were retrieved. The investigator, not the AI, chooses whether to close, ask for information, or escalate. Only a submitted escalation enters Compliance.",
     "caption": "Alert → Case → Evidence → Copilot → Human decision → Compliance", "target": None},
    {"screen": "42_public_floating_home_ready.png", "title": "2 · Home and Navigation",
     "narration": "Home explains what this product does and gives a route into the Case Queue. The left navigation also includes Investigation Workspace, Evidence and R A G, Compliance Queue, Analytics, Global Search, an information page, and two admin screens. The floating Ask Investigate IQ launcher stays at the lower right, independent of the navigation menu. Opening it does not change the case or leave the current page. We will visit each operational screen.",
     "caption": "Pages on the left; floating Copilot at the lower right.", "target": (1180, 660)},
    {"screen": "48_public_queue_current.png", "title": "3 · Understand the Case Queue",
     "narration": "The Case Queue is where an investigator begins. It lists fictional alerts with severity, status, scenario, and recorded trigger-rule metadata. The counts and filters help find work, but an alert is not evidence of a crime. This is not connected to a live bank monitoring system. A closed or Compliance-reviewed row can expose its Evidence button so the supporting records are inspectable; its action label is not an invitation to reopen a completed decision. The example we will use is Case zero four one, Coastal Wholesale Traders, a high-severity structuring-style alert.",
     "caption": "Queue counts orient the investigator; they do not prove wrongdoing.", "target": (711, 462)},
    {"screen": "49_public_queue_filtered.png", "title": "Find and Open CASE-041",
     "narration": "Type Coastal into the customer filter. The list narrows to Case zero four one. Its row shows the customer, the structuring alert label, high severity, open status, and recorded rule R three. The clearly labeled Open button takes us directly to this case's Investigation Workspace. The rule label is source-dataset metadata; this screen does not independently recalculate the alert. We open the case to check what actually happened.",
     "caption": "Search Coastal → CASE-041 → Investigation Workspace", "target": (1153, 512)},
    {"screen": "06_public_investigation_start.png", "title": "4 · Run the Investigation",
     "narration": "The workspace keeps the selected case and offers a saved investigation replay or live analysis. For a reliable walkthrough, we choose the saved Case zero four one report. It is a previously generated AI draft, not a fresh model run. Live analysis is available only when a model connection is configured. The pipeline gathers alert details, customer K Y C, transaction patterns, relationships, available documents, and playbook guidance before drafting findings for human review.",
     "caption": "CASE-041 + cached report = repeatable investigation view", "target": (510, 555)},
    {"screen": "07_public_case_summary.png", "title": "Read the Case Context",
     "narration": "The customer is Coastal Wholesale Traders, a wholesale distribution business. The review window contains six credits from September twenty second through September twenty seventh. The account's prior baseline average is three hundred ninety five thousand rupees. The trigger transaction is nine hundred seventy five thousand rupees, which is displayed as about two point five times that baseline. There are no prior cases in this dataset. These are context facts to verify, not a verdict.",
     "caption": "6 credits · ₹395,000 baseline · 2.5× trigger ratio", "target": (683, 238)},
    {"screen": "08_public_evidence.png", "title": "Separate Cash from Other Credits",
     "narration": "The six credits are not all identical. Four are recorded as cash deposits: transaction nineteen nine two seven for nine hundred seventy five thousand, nineteen nine two eight for nine hundred sixty thousand, nineteen nine three zero for nine hundred fifty five thousand, and nineteen nine three two for nine hundred eighty thousand rupees. Together those four cash entries total three million eight hundred seventy thousand rupees. The other two credits are recorded as payments from Retail Partner A and B, so they should not silently be described as cash.",
     "caption": "Four cited cash deposits total ₹3,870,000; two other credits are partner payments.", "target": (552, 404)},
    {"screen": "08_public_evidence.png", "title": "Check Findings and Missing Records",
     "narration": "The draft marks the deposit cluster as a red flag and cites the four cash transaction IDs. A separate finding says the file lacks documentation explaining why this pattern fits the customer's business. That missing document is not proof of an improper purpose; it is a reason to ask questions. The report asks for the business rationale and the agreements with the two retail partners. The Grounding Validator checks selected IDs and numeric wording, but not every sentence or the truth of an explanation.",
     "caption": "Cited pattern + missing explanation = investigate further, not conclude guilt.", "target": (575, 435)},
    {"screen": "44_public_floating_case_answer.png", "title": "5 · Ask the Copilot",
     "narration": "The floating Copilot opens on the right and shows the selected case. Suggested questions can fill the message field, and the investigator can also type a question and press Send at the bottom. The conversation appears above the composer. The selected case's answer can point to stored transactions or indexed passages. The saved investigation report is a separate historical draft, not a second chat. The Copilot's current answer is bounded by the records it can actually read.",
     "caption": "Choose or type → Send below → read answer above", "target": (1110, 627), "caption_top": True},
    {"screen": "44_public_floating_case_answer.png", "title": "Do Not Mistake a Citation for Proof",
     "narration": "Notice the distinction between a plausible answer and a verified conclusion. A citation tells us which transaction or playbook entry to inspect. It does not prove the prose is correct or that the activity is unlawful. The saved report even proposes escalation, but our second playbook requires a documented request for an explanation and no reasonable answer on file. We will not let the draft skip that condition. The investigator retains ownership of the next step.",
     "caption": "A source ID is a pointer for review, not an automatic verdict.", "target": (950, 349), "caption_top": True},
    {"screen": "45_public_floating_count_kyc.png", "title": "Ask About Transactions and KYC",
     "narration": "Now ask the case Copilot about transactions that are stored and whether K Y C is independently verified. For Case zero four one, the current answer counts sixteen rows in the supplied account dataset. The older saved report captured six transactions in its narrower review window. Neither number is a complete bank-month statement. The source alert identifies transaction nineteen nine two seven as its trigger; it does not independently classify every other row as suspicious. The workbook K Y C field says Verified, but zero original identity files were uploaded, so that label is not independent verification. The answer cites stored case passages for inspection.",
     "caption": "16 stored account rows · 6 in saved review · KYC label ≠ original proof", "target": (1010, 474)},
    {"screen": "46_public_floating_saved_current.png", "title": "Saved Report Versus Current Evidence",
     "narration": "A second question tests evidence provenance. The historical saved report captured zero case passages, while the current index contains twenty one for this case. The copilot names both scopes and their recorded times separately. It does not claim to know the old index version or when the extra passages arrived. A current citation cannot retroactively prove what the old report saw; the old report is retained as a snapshot.",
     "caption": "0 in saved draft · 21 currently indexed · historical version unknown", "target": (1020, 463)},
    {"screen": "39_public_exact_case_chunk.png", "title": "Open the Exact Case Passage",
     "narration": "Follow the copilot's cited case-ledger chunk to Evidence and R A G. The source identifier, verification status, and exact stored passage are visible here. This first chunk warns that the account rows are only the supplied fictional dataset, not a complete bank statement. The citation is an inspectable pointer; it does not authenticate the source or prove what happened at another bank.",
     "caption": "Copilot citation → exact stored text → verification limit", "target": (783, 421)},
    {"screen": "47_public_floating_chunk_answer.png", "title": "Question the Selected Passage",
     "narration": "The investigator can also ask the floating, page-aware Copilot, What does this chunk say? The page shows passage C zero beside the answer. The answer quotes the exact stored text and identifies its status as source rows only. It warns that the supplied dataset is not a complete bank statement. It does not invent an original document, counterparty K Y C, or a legal-money verdict. This is the boundary between useful retrieval and unsupported claims.",
     "caption": "Selected chunk + case scope → bounded answer", "target": (1040, 356)},
    {"screen": "10_public_rag_overview.png", "title": "6 · Open Evidence & RAG",
     "narration": "From the cited playbook, we move to Evidence and R A G without leaving the site. R A G means retrieval-augmented generation: retrieve relevant source passages first, then use those passages to support a draft with citations. For this case, we use Source and chunks, Search the index, and Method and code. The page also offers Case records and a Rule Lab; Fictional Intake appears when enabled. The playbook collection has twenty four synthetic documents and fifty seven indexed chunks. Case zero four one points to playbook P B A M L S T R zero one. A document citation identifies a source; it does not prove every generated claim.",
     "caption": "Source & chunks | Search the index | Method & code", "target": (151, 329)},
    {"screen": "10b_public_rag_source.png", "title": "Read the Original Document",
     "narration": "Here is the original text of P B A M L S T R zero one, titled Identify and document a structuring pattern. It instructs the investigator to list exact transactions, amounts, dates, channels, and the combined value. It also asks whether amounts are similar and whether the channel or counterparty changes. We can see the source itself, rather than trusting only an AI summary of it. This is synthetic guidance, not an approved Indian-bank policy or an official regulation.",
     "caption": "Open the cited playbook and compare its words with the case.", "target": (806, 314)},
    {"screen": "11_public_rag_chunks.png", "title": "See the Exact Chunk Boundaries",
     "narration": "The builder stores one metadata chunk containing the document title and escalation criterion. It then splits the body at sentence-ending punctuation and groups two sentences per body chunk. This source produces three indexed chunks: C zero, C one, and C two. The selected investigation retrieved the metadata chunk C zero, while the body chunks preserve the detailed instructions. Each passage can be opened and read on the same site, with its source ID and word count visible.",
     "caption": "Original document → metadata chunk + two body chunks", "target": (780, 470)},
    {"screen": "12_public_rag_retrieval.png", "title": "Search the Same Retrieval Index",
     "narration": "The Search the index view lets us type terms such as structuring cash deposits. SQLite F T S five matches those terms against the stored chunks, and B M twenty five ranks the matching passages. The Evidence Agent uses this search with the alert scenario as a filter, so the case receives relevant playbook guidance. This is lexical keyword retrieval, not embeddings or a vector database. Search results can open their source chunk here on the site.",
     "caption": "FTS5 keyword match → BM25 rank → exact source passage", "target": (789, 332)},
    {"screen": "11_public_rag_chunks.png", "title": "Trace the RAG Pipeline",
     "visual": "rag", "narration": "This is the full document path behind the screen. The authored markdown playbook is parsed into a source record. The builder creates a metadata chunk and two-sentence body chunks. SQLite stores those chunks and indexes their words. For a case, the Evidence Agent retrieves scenario-matched passages. The draft can cite a playbook ID, and the Grounding Validator checks that the ID actually came from the retrieved set. Finally, the human opens the source and judges whether the guidance applies.",
     "caption": "Playbook → chunks → FTS5 → Evidence Agent → draft → human check", "target": None},
    {"screen": "12_public_rag_retrieval.png", "title": "Explain the Code on the Site",
     "visual": "code",
     "narration": "The Method and code view keeps the implementation inside Investigate IQ. It has eight expandable steps covering alert calculation, guidance and case chunking, case and guidance search, transaction links, context gathering, and citation checks. This diagram highlights four representative functions. The code supports explainability, but the validator is limited: it checks selected citations and wording patterns, not the full factual correctness of a generated report.",
     "caption": "Eight code panels; four representative functions illustrated", "target": (785, 339)},
    {"screen": "14_public_human_decision.png", "title": "7 · Reach the Human Decision",
     "narration": "Back in the Investigation Workspace, the Human Decision panel offers close with no concern, request more information, or escalate to Compliance. The AI cannot select or submit any of them. The investigator's name and written reason are required for a recorded decision. This matters because the retrieved playbook is conditional, and the case file has no documented business explanation yet. A machine-generated escalation suggestion cannot replace those checks or the human decision.",
     "caption": "AI drafts; the investigator chooses and writes the reason.", "target": (543, 334), "caption_top": True},
    {"screen": "15_public_reasoned_decision.png", "title": "Our Proposed Next Step",
     "narration": "For this example, Request more information is the cautious option shown in the form. The proposed rationale asks for the business explanation of the cash-deposit cluster and agreements with Retail Partner A and B before a final conclusion. That is not the same as declaring the activity harmless; it keeps the issue open for follow-up. The rationale is drafted here. Until Submit decision is pressed, no decision is recorded and the case does not move to Compliance.",
     "caption": "A draft rationale alone does not record a decision.", "target": (747, 350)},
    {"screen": "26_public_intake_compliance.jpg", "title": "8 · What Compliance Receives", "visual": "compliance_states",
     "narration": "Now we open the Compliance Queue. The Case zero four one form was not submitted, so that example did not create an escalation. The case shown here is a separate fictional transaction packet that an investigator explicitly escalated with a written reason. Compliance can record three distinct outcomes. Acknowledge means Compliance reviewed it and needs no further action, so the queue shows Compliance reviewed — no further action. Return means the investigator must provide more information, so the queue shows Compliance returned — information needed. Refer means an onward referral was recorded, so the queue shows Compliance referred onward — recorded; it is not a filing. These labels make the outcome visible on the Case Queue and the audit trail. The product does not automatically file a suspicious transaction report or communicate with a regulator.",
     "caption": "Acknowledge → reviewed; Return → information needed; Refer → recorded onward referral."},
    {"screen": "17_public_analytics.png", "title": "9 · Analytics", "visual": "analytics",
     "narration": "Analytics is descriptive, so let us name every graph precisely. Alerts by severity counts the stored High, Medium, and Low labels. Alerts by typology counts alert categories such as structuring or velocity. Current status counts the latest workflow state, including source status and human or Compliance outcomes. High-severity share by typology is the proportion of each typology carrying the High label; it is not a probability of crime. Stored alert records by month counts fictional records dated in each month; it is not a risk trend. Finally, recorded human actions by person and by action type count saved workflow events, not staff productivity, case quality, or final outcomes. The axes and tooltips identify the unit for each chart. None of these graphs measures real-world crime detection, false positives, or model accuracy; that would require independent evaluation and real bank data.",
     "caption": "Six descriptive views: labels, workflow state, time, and recorded actions — never a verdict."},
    {"screen": "18_public_global_search.png", "title": "10 · Global Search",
     "narration": "Global Search is the quickest cross-reference tool. Search Coastal and the site locates the customer, related case, account, and transactions in the fictional dataset. A result can take us back to the Investigation Workspace, so we do not have to remember a case number. Evidence and R A G is different: it lets us inspect source documents and search guidance or case-evidence chunks within their scope. Search is a pointer to records, not a conclusion.",
     "caption": "Find linked records, then inspect their source evidence.", "target": (784, 500)},
    {"screen": "19_public_team.png", "title": "11 · Project & Team",
     "narration": "Project and the role guide explain who owns which part of this demonstration. The Investigator selects a case, reviews evidence, and records the accountable decision. The lead coordinates the investigation workflow and follow-up. The Compliance Officer performs the second human review of escalations and can acknowledge or return them. The Admin maintains the fictional knowledge base and rule previews after the separate passcode check. The confirmed roster is shown by name only: Sweta Singh, Soumya, Lakshmi Dudgikar, Rahul Sharma, Laxman Singh, Pankaj Bharsakale, and Rahul Chainani. These are planning responsibilities, not production permissions; a role label cannot prove identity or alter evidence.",
     "caption": "Named responsibilities clarify ownership; role labels are not authentication.", "target": (142, 127)},
    {"screen": "20_public_admin_knowledge.png", "title": "12 · Admin Knowledge Base",
     "narration": "Now open Admin Knowledge Base. Enter the configured passcode in the masked field and select Unlock; we never display or speak the code. The passcode opens an inspector, but it is only a limited gate, not bank-grade identity or role authorization. After unlocking, we can inspect the actual source documents, their chunks, and a live retrieval query.",
     "caption": "Masked passcode → read-only source and retrieval inspector", "target": (164, 366)},
    {"screen": "27_public_admin_knowledge_open.png", "title": "Inside the Knowledge Base",
     "narration": "The unlocked page reports twenty four synthetic playbook documents, fifty seven indexed chunks, and four hundred seventy six searchable terms. Each source is an O K F, or Open Knowledge Format, Markdown playbook with structured fields for its ID, scenario, title, escalation criteria, and version followed by guidance text. This is the guidance corpus for the source-database copilot. It is separate from customer K Y C records and from the new fictional intake packet; those case records are not O K F playbooks. Search here is lexical full-text retrieval, not an embedding model or a vector database.",
     "caption": "24 playbooks · 57 chunks · 476 indexed terms", "target": (585, 489)},
    {"screen": "30_public_admin_chunks_table.png", "title": "Inspect the Source-to-Chunk Map",
     "narration": "Open playbook P B A M L S T R zero one, the structuring guidance connected to Case zero four one. Its complete source text appears above the chunk table. One metadata chunk stores its title and escalation criterion; the body is split at sentence boundaries and grouped in two-sentence passages. Here we can see C zero, C one, and C two with their exact source text and word counts. A chunk is a searchable excerpt, not proof that a transaction is criminal.",
     "caption": "One source → C0 metadata + C1/C2 body passages", "target": (690, 509)},
    {"screen": "31_public_admin_search.png", "title": "Test Live Playbook Retrieval",
     "narration": "Type structuring cash deposits into the live retrieval field. SQLite F T S five matches the indexed words and B M twenty five ranks the returned passages. The first result here is a conditional escalation passage: the pattern, implausible business fit, and no reasonable explanation after a documented request must all be examined. The copilot can cite a source identifier, but the investigator still reads this exact passage and compares it with the transaction records.",
     "caption": "Keyword query → ranked chunk → read the condition", "target": (794, 542)},
    {"screen": "21_public_admin_rules.png", "title": "13 · Admin Rule Configuration",
     "narration": "The second admin page has its own masked passcode step. After unlocking, it displays saved R one and R two preview settings. These controls do not constitute the bank's production monitoring engine, and changing them does not regenerate existing queue alerts. We will inspect the saved values and run a read-only preview without saving a new configuration.",
     "caption": "Unlock settings; preview before any save", "target": (155, 399)},
    {"screen": "32_public_admin_rule_open.png", "title": "Read the Saved Thresholds",
     "narration": "The saved example settings are five times the account baseline for R one, eighty percent outbound proxy for R two, and a seventy two hour observation window. R two compares aggregate debits from the same account; it does not prove that the same credited rupees funded those debits or crossed another bank. Sliders allow a proposed change, but nothing is written until a named admin presses Save.",
     "caption": "5× baseline · 80% proxy · 72-hour window", "target": (801, 540)},
    {"screen": "33_public_admin_rule_preview.png", "title": "Preview Without Changing Alerts",
     "narration": "At the current settings, the read-only preview checked three hundred fictional accounts. Two met R one; none met both preview conditions. This is a sensitivity check over a sample, not the count of live alerts and not the calculation used for the separate fictional intake case. We do not save any threshold change in this walkthrough.",
     "caption": "300 checked · 2 R1 · 0 both · no save", "target": (799, 381)},
    {"screen": "22_public_intake_form.jpg", "title": "14 · Add a Fictional Transaction Packet",
     "narration": "Now open Fictional Intake inside Evidence and R A G. Enter an asserted monthly baseline of eighty thousand rupees, an incoming transfer amount of three hundred thousand, and an outgoing amount of one hundred eighty thousand. The application creates ten labeled synthetic rows, calculates a review signal, and saves one case in SQLite with five generated text records: profile, invalid sample P A N, invalid sample passport, ledger, and alert. No bank document or third-party alert is uploaded. The case then appears in the Case Queue.",
     "caption": "Numeric input → calculated signal → saved fictional case", "target": (786, 579)},
    {"screen": "34_public_intake_rows.png", "title": "Read the Ten Stored Transfers",
     "narration": "Open the stored ledger rows rather than trusting a static card. Four completed credits of three hundred thousand total one million two hundred thousand rupees. Six completed debits of one hundred eighty thousand total one million eighty thousand. The recorded external counterparty identifiers tell us where this fictional bank's ledger says money came from or went to. They do not supply the other bank's customer K Y C, opposite-side posting, or a verified chain of the same rupees.",
     "caption": "4 credits + 6 debits; external endpoints still unverified", "target": (823, 358)},
    {"screen": "24_public_intake_chunks.jpg", "title": "15 · Inspect the Evidence Boundary",
     "narration": "In the saved packet, each generated record can be read in full. Here the exact indexed passages and the case-scoped search are visible. The source text is split into passages, given a S H A two five six digest, and searched with SQLite F T S five. The result shows the saved transaction text, not a model's invented answer. But identity samples are deliberately invalid, no original identity file was uploaded, counterparty K Y C is unknown, and independent source-of-funds proof is missing. A transfer chain and a citation cannot establish whether money is legal or illegal.",
     "caption": "Exact source chunk → case-scoped search → explicit gaps", "target": (650, 559)},
    {"screen": "25_public_intake_review.jpg", "title": "16 · Review the Calculated Case",
     "narration": "Open the new case in the Investigation Workspace. Its separate calculated review reloads the saved rows and checks source fingerprints and exact chunks. The observed amounts are one million two hundred thousand in and one million eighty thousand out: fifteen times the asserted monthly baseline, ninety percent outbound, and six beneficiaries. Fixed questions give answers anchored to those source IDs; this is not the six-agent or Gemini report from Case zero four one. Original identity files, independent source-of-funds proof, counterparty K Y C, and settlement confirmation are absent. A human may request information or escalate with a written reason, but cannot close this incomplete packet as no concern.",
     "caption": "Saved rows → calculated review → reasoned human action", "target": (835, 606)},
    {"screen": "41_public_floating_home_guest.png", "title": "What the Case Actually Concludes",
     "visual": "closing", "narration": "Our conclusion is deliberately narrow. In Case zero four one, the cash-deposit cluster and playbook guidance justify asking for a business explanation and partner agreements; the draft alone does not record a decision. In the separate ten-transfer packet, the stored rows exceed the review threshold and an investigator recorded a reasoned escalation because independent evidence is missing. Neither case is proven legal or illegal by this application. A regulator filing did not occur. Investigate IQ shows the evidence trail and the unanswered questions; a human owns the judgment and the next action.",
     "caption": "Evidence supports follow-up; a human owns any recorded conclusion.", "target": None},
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT), size)


def wrap(draw: ImageDraw.ImageDraw, value: str, face: ImageFont.FreeTypeFont, limit: int) -> list[str]:
    lines: list[str] = []
    line = ""
    for word in value.split():
        trial = f"{line} {word}".strip()
        if line and draw.textbbox((0, 0), trial, font=face)[2] > limit:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return lines


def poster_image(screen: Image.Image) -> Image.Image:
    image = screen.convert("RGBA")
    shade = Image.new("RGBA", image.size, (7, 19, 39, 192))
    image = Image.alpha_composite(image, shade)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((112, 190, 1168, 532), radius=26,
                           fill=(15, 32, 59, 244), outline=(113, 159, 227, 255), width=3)
    draw.text((163, 225), "INVESTIGATEIQ", font=font(27, True), fill="#9EC6FF")
    draw.text((163, 285), "Evidence-to-Decision Walkthrough", font=font(40, True), fill="white")
    draw.text((166, 366), "Case review  |  evidence trail  |  human decision", font=font(25), fill="#D8E7FF")
    draw.ellipse((962, 302, 1060, 400), fill="#2E63BF", outline="#A6CAFF", width=3)
    draw.polygon([(1000, 323), (1000, 379), (1041, 351)], fill="white")
    draw.text((166, 464), "AI drafts. People decide. No regulatory filing.", font=font(22), fill="#AFCAEC")
    return image.convert("RGB")


def draw_pointer(draw: ImageDraw.ImageDraw, target: tuple[int, int], progress: float) -> None:
    """Keep a compact, high-contrast arrowhead on the item being discussed."""
    tx, ty = target
    offset_x = -66 if tx > WIDTH // 2 else 66
    offset_y = -52 if ty > HEIGHT // 2 else 52
    start = (tx + offset_x, ty + offset_y)
    distance = math.hypot(offset_x, offset_y)
    ux, uy = -offset_x / distance, -offset_y / distance
    tip = (round(tx - ux * 12), round(ty - uy * 12))
    wing = 13
    left = (round(tip[0] - ux * 22 - uy * wing), round(tip[1] - uy * 22 + ux * wing))
    right = (round(tip[0] - ux * 22 + uy * wing), round(tip[1] - uy * 22 - ux * wing))
    draw.line((start, tip), fill="white", width=13)
    draw.line((start, tip), fill="#115CC2", width=7)
    draw.polygon((tip, left, right), fill="#115CC2")
    draw.line((tip, left, right, tip), fill="white", width=2, joint="curve")
    radius = 12 + round(3 * (1 + math.sin(progress * 12 * math.pi)))
    draw.ellipse((tx - radius, ty - radius, tx + radius, ty + radius), outline="#115CC2", width=3)


# Coordinates refer to the actual 1280 × 720 screen captures. Each sequence
# follows the visible controls or evidence as that scene's narration advances.
SCENE_FOCUS = {
    1: [(1030, 359), (1040, 442), (974, 501)],
    3: [(1030, 103), (82, 162), (1180, 665)],
    4: [(496, 164), (524, 655), (890, 655)],
    5: [(1030, 360), (415, 507), (1153, 512)],
    6: [(480, 450), (744, 450), (1085, 450)],
    7: [(543, 113), (450, 242), (631, 242), (836, 242)],
    8: [(572, 235), (600, 395), (585, 523)],
    9: [(557, 505), (520, 348), (590, 585)],
    10: [(990, 98), (1060, 335), (1110, 640)],
    11: [(1020, 330), (1085, 468), (1080, 555)],
    12: [(1020, 310), (1060, 430), (1100, 550)],
    13: [(1020, 310), (1060, 430), (1100, 550)],
    14: [(765, 356), (775, 416), (527, 32)],
    15: [(960, 150), (1040, 330), (1040, 500)],
    16: [(522, 96), (502, 329), (760, 329)],
    17: [(660, 298), (680, 421), (792, 501)],
    18: [(745, 148), (683, 296), (631, 488), (638, 641)],
    19: [(750, 207), (637, 271), (704, 355)],
    21: [(754, 327), (1000, 401), (842, 473)],
    22: [(505, 91), (433, 335), (545, 504)],
    23: [(498, 181), (640, 339), (466, 440)],
    24: [(510, 120), (788, 397), (471, 694)],
    25: [(472, 165), (784, 642), (959, 643)],
    26: [(500, 501), (430, 650), (1125, 660)],
    27: [(495, 165), (795, 450), (935, 627)],
    28: [(497, 222), (713, 482), (412, 539)],
    29: [(491, 486), (599, 486), (795, 486)],
    30: [(635, 412), (700, 510), (1050, 510)],
    31: [(602, 447), (570, 541), (1005, 544)],
    32: [(495, 265), (713, 482), (412, 539)],
    33: [(502, 512), (776, 543), (1012, 541)],
    34: [(504, 256), (432, 378), (688, 380), (946, 380)],
    35: [(620, 309), (785, 580), (474, 639)],
    36: [(660, 270), (715, 399), (1057, 530)],
    37: [(592, 165), (583, 480), (635, 643)],
    38: [(660, 356), (700, 512), (840, 609)],
}

# A short, fixed-position label gives orientation without obscuring the
# evidence or controls in the captured application.
SCENE_LABELS = {
    1: "Enter the Workspace",
    3: "Home",
    4: "Case Queue",
    5: "Open CASE-041",
    6: "Run the Investigation",
    7: "Case Context",
    8: "Cash vs Other Credits",
    9: "Findings and Gaps",
    10: "Ask the Copilot",
    11: "Citation Is Not Proof",
    12: "Transactions and KYC",
    13: "Saved vs Current Evidence",
    14: "Exact Case Passage",
    15: "Question a Chunk",
    16: "Evidence & RAG",
    17: "Original Source",
    18: "Document Chunks",
    19: "Search the Index",
    21: "Method and Code",
    22: "Human Decision",
    23: "Proposed Next Step",
    24: "Compliance Queue",
    25: "Analytics",
    26: "Global Search",
    27: "About InvestigateIQ",
    28: "Knowledge Base",
    29: "Knowledge Base Metrics",
    30: "Source to Chunks",
    31: "Live Retrieval",
    32: "Rule Configuration",
    33: "Saved Thresholds",
    34: "Read-only Preview",
    35: "Fictional Intake",
    36: "Stored Transfers",
    37: "Exact Evidence Chunks",
    38: "Calculated Review",
}


def draw_scene_label(draw: ImageDraw.ImageDraw, scene_index: int) -> None:
    label = SCENE_LABELS[scene_index]
    face = font(17, True)
    width = draw.textbbox((0, 0), label, font=face)[2]
    draw.rounded_rectangle((315, 10, 339 + width, 46), radius=9,
                           fill="#102640", outline="#7BA8E7", width=1)
    draw.text((327, 17), label, font=face, fill="white")


def render_diagram(scene: dict, progress: float) -> Image.Image:
    """Animated explanatory map; deliberately distinct from app screenshots."""
    image = Image.new("RGB", (WIDTH, HEIGHT), "#0C1930")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((43, 39, 1237, 681), radius=28, fill="#142844", outline="#6596DA", width=2)
    draw.text((76, 68), "INVESTIGATEIQ  /  EXPLANATORY MAP", font=font(19, True), fill="#9FC9FF")
    draw.text((76, 112), scene["title"], font=font(39, True), fill="#FFFFFF")
    draw.text((78, 167), scene["caption"], font=font(22), fill="#D7E9FF")
    if scene["visual"] == "journey":
        nodes = [
            ("01", "Alert", "Fictional case enters queue"),
            ("02", "Case", "Review customer and credits"),
            ("03", "Evidence", "Check IDs and missing records"),
            ("04", "Copilot", "Read a cited draft, not a verdict"),
            ("05", "Human", "Choose and explain the action"),
            ("06", "Compliance", "Receives submitted escalations"),
        ]
    elif scene["visual"] == "rag":
        nodes = [
            ("01", "Playbook", "Authored source text"),
            ("02", "Chunks", "Metadata + two-sentence groups"),
            ("03", "FTS5", "Index terms and rank matches"),
            ("04", "Evidence agent", "Retrieve scenario guidance"),
            ("05", "Draft + check", "Cite IDs; validate selected claims"),
            ("06", "Human review", "Read original passage in context"),
        ]
    elif scene["visual"] == "code":
        nodes = [
            ("01", "chunk_body()", "Split source sentences into groups"),
            ("02", "search()", "FTS5 MATCH query and BM25 ranking"),
            ("03", "guidance_for()", "Filter retrieval to the alert scenario"),
            ("04", "validate()", "Check selected IDs and draft claims"),
        ]
    elif scene["visual"] == "compliance_states":
        nodes = [
            ("A", "Acknowledge", "Compliance reviewed — no further action"),
            ("R", "Return", "Compliance returned — information needed"),
            ("→", "Refer", "Compliance referred onward — recorded"),
        ]
    elif scene["visual"] == "analytics":
        nodes = [
            ("01", "Severity", "Count stored High, Medium, Low labels"),
            ("02", "Typology", "Count alert categories in the sample"),
            ("03", "Status", "Latest source or human workflow state"),
            ("04", "High share", "High-label proportion, not crime probability"),
            ("05", "Month", "Fictional records dated in each month"),
            ("06", "Human actions", "Saved events by person and action type"),
        ]
    elif scene["visual"] == "intake":
        nodes = [
            ("01", "Numeric input", "Amounts and expected activity"),
            ("02", "Ten transfers", "Generated fictional transfer chain"),
            ("03", "Rule signal", "Calculated from the saved rows"),
            ("04", "SQLite case", "One atomic case packet"),
            ("05", "Five records", "Labeled generated text, not uploads"),
            ("06", "Case Queue", "Visible when intake is enabled"),
        ]
    elif scene["visual"] == "intake_evidence":
        nodes = [
            ("01", "Source record", "Read complete generated text"),
            ("02", "Exact chunks", "Passages retain source IDs"),
            ("03", "SHA-256", "Digest checks stored text"),
            ("04", "Case search", "FTS5 over this case's passages"),
            ("05", "KYC gap", "Invalid samples; no original files"),
            ("06", "Review limit", "No lawfulness verdict from citations"),
        ]
    elif scene["visual"] == "intake_review":
        nodes = [
            ("01", "Reload rows", "Read saved transfer chain"),
            ("02", "Check links", "Verify packet integrity"),
            ("03", "Ask questions", "Fixed, source-anchored answers"),
            ("04", "Human action", "Request information or escalate"),
            ("05", "Write reason", "Name and rationale required"),
            ("06", "Compliance", "Only after escalation is submitted"),
        ]
    else:
        nodes = [
            ("✓", "What we saw", "Four cited cash deposits"),
            ("?", "What is missing", "Business explanation and agreements"),
            ("→", "What comes next", "Human request for information"),
        ]
    card_width, card_height = (530, 157) if scene["visual"] == "code" else (354, 157)
    positions = ([(76 + (index % 2) * 574, 231 + (index // 2) * 188) for index in range(len(nodes))]
                 if scene["visual"] == "code" else
                 [(76 + (index % 3) * 382, 231 + (index // 3) * 188) for index in range(len(nodes))])
    for index in range(len(nodes) - 1):
        x1, y1 = positions[index]
        x2, y2 = positions[index + 1]
        start = (x1 + card_width // 2, y1 + card_height // 2)
        end = (x2 + card_width // 2, y2 + card_height // 2)
        distance = math.dist(start, end)
        for part in range(0, int(distance), 19):
            if index + part / max(distance, 1) > progress * len(nodes):
                break
            t1, t2 = part / distance, min(1, (part + 9) / distance)
            draw.line((start[0] + (end[0] - start[0]) * t1,
                       start[1] + (end[1] - start[1]) * t1,
                       start[0] + (end[0] - start[0]) * t2,
                       start[1] + (end[1] - start[1]) * t2), fill="#7AB9FF", width=4)
    visible = max(1, math.ceil(progress * len(nodes)))
    for index, (marker, heading, detail) in enumerate(nodes[:visible]):
        x, y = positions[index]
        draw.rounded_rectangle((x, y, x + card_width, y + card_height), radius=18,
                               fill="#223D63", outline="#82B7FC", width=2)
        draw.rounded_rectangle((x + 15, y + 16, x + 67, y + 62), radius=11, fill="#3675D0")
        draw.text((x + 30, y + 24), marker, font=font(19, True), fill="white")
        draw.text((x + 19, y + 69), heading, font=font(23, True), fill="white")
        for line_index, line in enumerate(wrap(draw, detail, font(17), card_width - 39)[:2]):
            draw.text((x + 19, y + 106 + line_index * 23), line, font=font(17), fill="#CFE3FF")
    draw.text((78, 643), "Fictional case · human review required · no regulatory filing",
              font=font(16), fill="#B2CEE9")
    return image


def render_frame(scene: dict, scene_index: int, elapsed: float, duration: int,
                 base: Image.Image) -> Image.Image:
    progress = min(1.0, elapsed / duration)
    if scene.get("visual"):
        return render_diagram(scene, progress)
    if scene_index == 0:
        image = poster_image(base)
        draw = ImageDraw.Draw(image)
        draw_pointer(draw, (1007, 350), progress)
        draw.rounded_rectangle((160, 497, 1118, 504), radius=4, fill="#3E5E89")
        draw.rounded_rectangle((160, 497, 160 + round(958 * progress), 504),
                               radius=4, fill="#8AC4FF")
        return image
    # A slow camera move plus a travelling cursor makes the navigation
    # sequence legible instead of presenting motionless screenshots.
    scale = 1 + 0.025 * progress
    w, h = round(WIDTH * scale), round(HEIGHT * scale)
    enlarged = base.resize((w, h), Image.Resampling.BICUBIC)
    focus_points = SCENE_FOCUS.get(scene_index, [scene["target"] or (WIDTH // 2, HEIGHT // 2)])
    target = focus_points[min(len(focus_points) - 1, int(progress * len(focus_points)))]
    left = round((w - WIDTH) * target[0] / WIDTH)
    top = round((h - HEIGHT) * target[1] / HEIGHT)
    image = enlarged.crop((left, top, left + WIDTH, top + HEIGHT)).convert("RGB")
    draw = ImageDraw.Draw(image)
    draw_scene_label(draw, scene_index)
    adjusted = (round(target[0] * scale - left), round(target[1] * scale - top))
    draw_pointer(draw, adjusted, progress)
    return image


def vtt_time(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, remainder = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d}.{remainder:03d}"


def write_subtitles(scenes: list[dict], tracks: list[Path], durations: list[int], target: Path) -> None:
    """Time complete narration sentences against their actual speech tracks."""
    lines = ["WEBVTT", ""]
    scene_start = 0.0
    cue_number = 1
    for scene, track, scene_duration in zip(scenes, tracks, durations):
        with wave.open(str(track), "rb") as source:
            spoken_seconds = source.getnframes() / source.getframerate()
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", scene["narration"]) if part.strip()]
        total_words = sum(len(sentence.split()) for sentence in sentences)
        elapsed_words = 0
        for sentence in sentences:
            words = len(sentence.split())
            cue_start = scene_start + 0.1 + spoken_seconds * elapsed_words / total_words
            elapsed_words += words
            cue_end = scene_start + 0.1 + spoken_seconds * elapsed_words / total_words
            lines.extend([str(cue_number), f"{vtt_time(cue_start)} --> {vtt_time(cue_end)}",
                          textwrap.fill(sentence, width=62), ""])
            cue_number += 1
        scene_start += scene_duration
    target.write_text("\n".join(lines), encoding="utf-8")


def build() -> tuple[Path, Path]:
    missing = [scene["screen"] for scene in SCENES if not (SCREENS / scene["screen"]).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing captured app screens: {', '.join(missing)}")
    screen_images = [Image.open(SCREENS / scene["screen"]).convert("RGB").resize((WIDTH, HEIGHT))
                     for scene in SCENES]
    POSTER.parent.mkdir(parents=True, exist_ok=True)
    poster_image(screen_images[0]).save(POSTER)
    with tempfile.TemporaryDirectory(prefix="investigateiq-ui-video-") as temp:
        folder = Path(temp)
        narration = folder / "narration_all.wav"
        tracks = synthesize_narration(folder, SCENES)
        durations = join_narration(tracks, narration)
        pending_subtitles = SUBTITLES.with_suffix(".rendering.vtt")
        write_subtitles(SCENES, tracks, durations, pending_subtitles)
        pending_output = OUTPUT.with_suffix(".rendering.mp4")
        command = [find_ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
                   "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{WIDTH}x{HEIGHT}",
                   "-framerate", str(FPS), "-i", "-", "-i", str(narration),
                   "-c:v", "libopenh264", "-b:v", "300k", "-pix_fmt", "yuv420p",
                   "-c:a", "aac", "-b:a", "64k", "-metadata", f"title={VIDEO_TITLE}",
                   "-movflags", "+faststart", str(pending_output)]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            assert process.stdin is not None
            for index, (scene, duration, base) in enumerate(zip(SCENES, durations, screen_images)):
                for frame_number in range(duration * FPS):
                    image = render_frame(scene, index, frame_number / FPS, duration, base)
                    process.stdin.write(image.tobytes())
            process.stdin.close()
            error = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
            if process.wait() != 0:
                raise RuntimeError(f"FFmpeg could not render the guided video: {error}")
            os.replace(pending_output, OUTPUT)
            os.replace(pending_subtitles, SUBTITLES)
        finally:
            if process.poll() is None:
                process.kill()
    return OUTPUT, POSTER


if __name__ == "__main__":
    if "--subtitles-only" in sys.argv:
        with tempfile.TemporaryDirectory(prefix="investigateiq-captions-") as folder_name:
            folder = Path(folder_name)
            tracks = synthesize_narration(folder, SCENES)
            durations = join_narration(tracks, folder / "narration_all.wav")
            write_subtitles(SCENES, tracks, durations, SUBTITLES)
        print(SUBTITLES)
    else:
        print(build())
