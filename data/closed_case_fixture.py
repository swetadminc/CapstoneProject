"""A traceable fictional false-positive example, never an authentic bank closure.

The packet deliberately uses non-government, non-bank document summaries. Its
amounts and identifiers are checked against ledger rows in regression tests.
"""

from __future__ import annotations

import sqlite3


CASE_ID = "CASE-045"
CUSTOMER_ID = "CUST-DEMO-045"
ACCOUNT_ID = "ACC-DEMO-045"
CLIENT_ACCOUNT = "ACC-DEMO-045-CLIENT"
SUPPLIER_ACCOUNT = "ACC-DEMO-045-SUPPLIER"
CREDIT_ID = "TXN-DEMO-045-01"
DEBIT_ID = "TXN-DEMO-045-02"


def seed_closed_example(conn: sqlite3.Connection) -> None:
    """Seed one internally consistent *simulated* closure and supporting rows."""
    customers = [
        (CUSTOMER_ID, "Isha Rao", "Individual", "Retail - fictional example",
         "Freelance designer", 240000, 20000, 15000,
         "Design services — customer declaration", "Low",
         "Current — fictional dataset assertion", "2026-09-10", "India", "2025-04-01"),
        ("CUST-DEMO-045-CLIENT", "Cedar Studio Pvt Ltd", "Business", "Business - fictional example",
         "Creative services", 1800000, 150000, 120000,
         "Client project receipts — fictional declaration", "Low",
         "Current — fictional dataset assertion", "2026-09-10", "India", "2024-01-01"),
        ("CUST-DEMO-045-SUPPLIER", "North Paper Co", "Business", "Business - fictional example",
         "Design supplies", 900000, 75000, 60000,
         "Supply sales — fictional declaration", "Low",
         "Current — fictional dataset assertion", "2026-09-10", "India", "2024-01-01"),
    ]
    conn.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", customers)
    conn.executemany("INSERT INTO accounts VALUES (?,?,?,?,?,?,?,?,?)", [
        (ACCOUNT_ID, CUSTOMER_ID, "Savings", "2025-04-01", "INR", "Active", "Low", 1, None),
        (CLIENT_ACCOUNT, "CUST-DEMO-045-CLIENT", "Current", "2024-01-01", "INR", "Active", "Low", 1, None),
        (SUPPLIER_ACCOUNT, "CUST-DEMO-045-SUPPLIER", "Current", "2024-01-01", "INR", "Active", "Low", 1, None),
    ])
    conn.executemany("INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?,?,?)", [
        (CREDIT_ID, ACCOUNT_ID, "2026-09-24T10:30:00", "CR", 60000, "INR", "NEFT",
         CLIENT_ACCOUNT, "Cedar Studio Pvt Ltd", "DEMO-INV-045 design project", "Completed"),
        (DEBIT_ID, ACCOUNT_ID, "2026-09-25T11:15:00", "DR", 8000, "INR", "NEFT",
         SUPPLIER_ACCOUNT, "North Paper Co", "DEMO-REC-045 materials", "Completed"),
    ])
    conn.execute("INSERT INTO alerts VALUES (?,?,?,?,?,?,?,?,?,?,?)", (
        "ALERT-DEMO-045", CASE_ID, CUSTOMER_ID, ACCOUNT_ID,
        "One-time credit above declared monthly baseline", "amount-anomaly",
        "Simulated comparison: INR 60,000 credit / INR 20,000 expected monthly credit = 3.0x; review prompt only",
        "2026-09-24", "Low", CREDIT_ID, "Closed - Simulated Example",
    ))
    docs = [
        ("DOC-DEMO-045-INVOICE", "Fictional invoice summary", "2026-09-23",
         f"FICTIONAL SAMPLE, NOT AN ORIGINAL OR VERIFIED INVOICE. DEMO-INV-045: Isha Rao billed Cedar Studio Pvt Ltd INR 60,000 for a design project. This assertion references {CREDIT_ID}, {ACCOUNT_ID} and {CLIENT_ACCOUNT}; the matching amount and reference can be checked against the stored transaction row."),
        ("DOC-DEMO-045-ACCEPTANCE", "Fictional service acceptance summary", "2026-09-24",
         f"FICTIONAL SAMPLE, NOT INDEPENDENT CLIENT CONFIRMATION. Cedar Studio Pvt Ltd is depicted accepting the DEMO-INV-045 design work for INR 60,000. It cross-references {CREDIT_ID}; this text was authored for the same fixture, so it is not independent proof of completed services."),
        ("DOC-DEMO-045-SUPPLIER", "Fictional supplier receipt summary", "2026-09-25",
         f"FICTIONAL SAMPLE, NOT AN ORIGINAL OR VERIFIED RECEIPT. DEMO-REC-045 depicts an INR 8,000 materials purchase from North Paper Co, linked to {DEBIT_ID}, {ACCOUNT_ID} and {SUPPLIER_ACCOUNT}. The amount and reference match the stored debit row."),
        ("DOC-DEMO-045-REVIEW", "Simulated closure worksheet", "2026-09-26",
         f"SIMULATED REVIEW, NOT A RECORDED HUMAN DECISION. This demonstration would close the alert after comparing the INR 60,000 credit {CREDIT_ID} with the fictional invoice and service-acceptance summaries and the INR 8,000 debit {DEBIT_ID} with the fictional supplier receipt. The credit is 3.0 times the declared monthly baseline, but the packet illustrates a plausible project-payment explanation and no rapid full-value dispersal in these two stored rows. Missing: authentic originals, independent issuer/client confirmation, full account history, and external counterparty checks. This is not proof that funds are lawful; a real investigator must verify before closing."),
    ]
    conn.executemany("INSERT INTO documents VALUES (?,?,?,?,?,?,?)", [
        (doc_id, CUSTOMER_ID, CASE_ID, doc_type, date, summary, 0)
        for doc_id, doc_type, date, summary in docs
    ])
    conn.commit()
