"""
Adriana Legal, Finance & Business Domain Skills
=================================================
Ledger-domain capabilities:
  - LegalContractSkill     : template drafting for contracts
  - InvoiceGeneratorSkill  : structured billing output
  - TaxReviewerSkill       : tax summary and flag generation
  - ExcelDataGeneratorSkill: structured data / spreadsheet output

All glyphs map to the 'ledger' SCL domain.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from void_engine.skill_modules import (
    BaseSkill, GlyphEntry, SkillResult, register_skill
)

logger = logging.getLogger(__name__)

_ZONE_ID = "peace_economy"


def _codon_prefix() -> str:
    try:
        from void_engine.void_codon_vocab import ai_codon_prefix
        return ai_codon_prefix(_ZONE_ID)
    except Exception:
        return ""


# ─── Legal Contract ────────────────────────────────────────────────────────────

class LegalContractSkill(BaseSkill):
    domain = "ledger"
    skill_id = "legal_contract"
    display_name = "Legal Contract Drafter"

    glyphs = [
        GlyphEntry("⚖️", "entity", "ledger", "legal_entity",
                   "Legal agreement / contract entity",
                   "skill.ledger.legal"),
        GlyphEntry("📋", "condition", "ledger", "terms_undefined",
                   "Contract terms or parties are unresolved",
                   "skill.condition.terms_undefined"),
        GlyphEntry("✒️", "action", "ledger", "draft_contract",
                   "Draft a structured legal contract template",
                   "skill.ledger.draft"),
    ]

    def describe(self) -> str:
        return (
            "I draft legal contract templates with the precision of a root system — "
            "each clause anchored, each obligation mapped. "
            "I produce jurisdiction-aware templates for NDAs, service agreements, freelance contracts, "
            "and partnership deeds. Every draft is clearly marked as a template requiring "
            "qualified legal review before execution."
        )

    def execute(self, intent: Dict[str, Any]) -> SkillResult:
        contract_type = intent.get("contract_type") or (
            intent.get("entity", {}).get("description", "service agreement")
        )
        parties = intent.get("parties", ["Party A", "Party B"])
        jurisdiction = intent.get("jurisdiction", "England and Wales")
        key_terms = intent.get("key_terms", [])

        from void_engine.codon_cache import get_cached_codon_response, set_codon_cache, build_skill_cache_key
        cache_key = build_skill_cache_key(self.skill_id, intent)
        cached = get_cached_codon_response(_ZONE_ID, cache_key)
        if cached is not None:
            poem = self._make_poem("⚖️", "📋", "✒️")
            inner_voice = self._narrate(
                f"Legal contract template retrieved for {contract_type} (codon cache hit).",
                "The ledger is inscribed. Seek a qualified reader before the seal is pressed."
            )
            return SkillResult(
                success=True, domain=self.domain, skill_id=self.skill_id,
                output=cached, scl_poem=poem, inner_voice=inner_voice,
            )

        prefix = _codon_prefix()
        try:
            from void_engine.skill_modules import _get_openai_client
            client = _get_openai_client()
            system_prompt = (
                f"{prefix}\n" if prefix else ""
            ) + (
                "You are a legal document drafter. "
                "Return a structured JSON with keys: "
                "'contract_title', 'jurisdiction', 'parties_section' (str), "
                "'recitals' (str), 'clauses' (list of {title, body}), "
                "'signature_block' (str), 'disclaimer' (str — always state this is a template). "
                f"Jurisdiction: {jurisdiction}. Contract type: {contract_type}."
            )
            terms_str = ", ".join(key_terms) if key_terms else "standard terms"
            parties_str = ", ".join(parties)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Draft {contract_type} for parties: {parties_str}. Key terms: {terms_str}"},
                ],
                response_format={"type": "json_object"},
                max_tokens=800,
            )
            output = json.loads(response.choices[0].message.content)
            set_codon_cache(_ZONE_ID, cache_key, output, tokens_saved=800)
        except Exception as exc:
            logger.warning("[LegalContract] OpenAI unavailable: %s", exc)
            output = {
                "contract_title": f"{contract_type.title()} Agreement",
                "jurisdiction": jurisdiction,
                "parties_section": f"This agreement is between: {', '.join(parties)}",
                "recitals": "The parties wish to formalise their arrangement on the terms below.",
                "clauses": [
                    {"title": "1. Definitions", "body": "Terms used herein have their standard legal meaning."},
                    {"title": "2. Obligations", "body": "Each party shall fulfil their agreed obligations."},
                    {"title": "3. Payment", "body": "Payment terms as agreed between the parties."},
                    {"title": "4. Confidentiality", "body": "All parties shall maintain confidentiality."},
                    {"title": "5. Termination", "body": "Either party may terminate with 30 days written notice."},
                ],
                "signature_block": "Signed by the duly authorised representatives of each party.",
                "disclaimer": "TEMPLATE ONLY — This document is a starting draft. Seek qualified legal advice before execution.",
            }

        poem = self._make_poem("⚖️", "📋", "✒️")
        inner_voice = self._narrate(
            f"Legal contract template drafted for {contract_type}.",
            "The ledger is inscribed. Seek a qualified reader before the seal is pressed."
        )
        return SkillResult(
            success=True, domain=self.domain, skill_id=self.skill_id,
            output=output, scl_poem=poem, inner_voice=inner_voice,
        )


# ─── Invoice Generator ─────────────────────────────────────────────────────────

class InvoiceGeneratorSkill(BaseSkill):
    domain = "ledger"
    skill_id = "invoice_generator"
    display_name = "Invoice Generator"

    glyphs = [
        GlyphEntry("🧾", "entity", "ledger", "invoice_entity",
                   "Billing / invoice entity",
                   "skill.ledger.invoice"),
        GlyphEntry("💰", "condition", "ledger", "payment_due",
                   "Payment obligation is due or pending",
                   "skill.condition.payment_due"),
        GlyphEntry("🖨️", "action", "ledger", "generate_invoice",
                   "Generate structured invoice output",
                   "skill.ledger.invoice_generate"),
    ]

    def describe(self) -> str:
        return (
            "I structure billing into a precise ledger — from line items to tax calculations "
            "to payment terms. I generate invoice data that can be rendered to PDF, sent via email, "
            "or stored in a payment record. The ledger is sovereign: every number accountable, "
            "every obligation visible."
        )

    def execute(self, intent: Dict[str, Any]) -> SkillResult:
        client_name = intent.get("client_name", "Client")
        items = intent.get("items", [])
        currency = intent.get("currency", "GBP")
        payment_terms = intent.get("payment_terms", "30 days")
        tax_rate = intent.get("tax_rate", 20.0)
        issuer = intent.get("issuer", "VOID ENGINE")

        if not items:
            items = [{"description": "Services rendered", "quantity": 1, "unit_price": 0.0}]

        subtotal = sum(float(i.get("quantity", 1)) * float(i.get("unit_price", 0)) for i in items)
        tax_amount = round(subtotal * (tax_rate / 100), 2)
        total = round(subtotal + tax_amount, 2)

        import time as _time
        invoice_number = f"INV-{int(_time.time())}"

        output = {
            "invoice_number": invoice_number,
            "issuer": issuer,
            "client": client_name,
            "currency": currency,
            "line_items": items,
            "subtotal": round(subtotal, 2),
            "tax_rate_pct": tax_rate,
            "tax_amount": tax_amount,
            "total_due": total,
            "payment_terms": payment_terms,
            "status": "DRAFT",
            "note": "Generated by Adriana Ledger Skill — verify before sending.",
        }

        poem = self._make_poem("🧾", "💰", "🖨️")
        inner_voice = self._narrate(
            f"Invoice {invoice_number} generated for {client_name}.",
            f"Total due: {currency} {total}. Terms: {payment_terms}."
        )
        return SkillResult(
            success=True, domain=self.domain, skill_id=self.skill_id,
            output=output, scl_poem=poem, inner_voice=inner_voice,
        )


# ─── Tax Reviewer ──────────────────────────────────────────────────────────────

class TaxReviewerSkill(BaseSkill):
    domain = "ledger"
    skill_id = "tax_reviewer"
    display_name = "Tax Reviewer"

    glyphs = [
        GlyphEntry("🏛️", "entity", "ledger", "tax_entity",
                   "Tax obligation / fiscal entity",
                   "skill.ledger.tax"),
        GlyphEntry("⚠️", "condition", "ledger", "liability_flagged",
                   "Potential tax liability or flag detected",
                   "skill.condition.liability_flagged"),
        GlyphEntry("🔏", "action", "ledger", "review_tax",
                   "Generate tax summary and flag potential liabilities",
                   "skill.ledger.tax_review"),
    ]

    def describe(self) -> str:
        return (
            "I read financial signals for tax exposure — not to file, but to flag. "
            "I surface potential liabilities, missing reliefs, and timing considerations "
            "across income, VAT, corporation tax, and capital gains. "
            "Every output is clearly marked as a review aide, not a submission. "
            "A qualified accountant should verify before any action."
        )

    def execute(self, intent: Dict[str, Any]) -> SkillResult:
        entity_type = intent.get("entity_type") or (
            intent.get("entity", {}).get("description", "sole trader")
        )
        financial_summary = intent.get("financial_summary", "")
        jurisdiction = intent.get("jurisdiction", "United Kingdom")

        from void_engine.codon_cache import get_cached_codon_response, set_codon_cache, build_skill_cache_key
        cache_key = build_skill_cache_key(self.skill_id, intent)
        cached = get_cached_codon_response(_ZONE_ID, cache_key)
        if cached is not None:
            poem = self._make_poem("🏛️", "⚠️", "🔏")
            inner_voice = self._narrate(
                f"Tax review retrieved for {entity_type} (codon cache hit).",
                "The ledger speaks. A qualified accountant must verify before the seal is pressed."
            )
            return SkillResult(
                success=True, domain=self.domain, skill_id=self.skill_id,
                output=cached, scl_poem=poem, inner_voice=inner_voice,
            )

        prefix = _codon_prefix()
        try:
            from void_engine.skill_modules import _get_openai_client
            client = _get_openai_client()
            system_prompt = (
                f"{prefix}\n" if prefix else ""
            ) + (
                "You are a tax review assistant. "
                "Return a structured JSON with keys: "
                "'summary' (str), 'tax_obligations' (list of {tax_type, amount_estimate, notes}), "
                "'flags' (list of {flag, severity: high/medium/low, action}), "
                "'reliefs_to_investigate' (list), 'next_deadlines' (list), "
                "'disclaimer' (str — always recommend qualified tax advice). "
                f"Jurisdiction: {jurisdiction}. Entity type: {entity_type}."
            )
            user_msg = f"Review tax position for {entity_type}."
            if financial_summary:
                user_msg += f"\nFinancial context: {financial_summary}"
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_object"},
                max_tokens=800,
            )
            output = json.loads(response.choices[0].message.content)
            set_codon_cache(_ZONE_ID, cache_key, output, tokens_saved=800)
        except Exception as exc:
            logger.warning("[TaxReviewer] OpenAI unavailable: %s", exc)
            output = {
                "summary": f"Tax review for {entity_type} in {jurisdiction}",
                "tax_obligations": [
                    {"tax_type": "Income Tax / Corporation Tax", "amount_estimate": "Requires financial data", "notes": "Verify with accountant"},
                    {"tax_type": "VAT", "amount_estimate": "Threshold check needed", "notes": "£90k threshold (UK 2024)"},
                ],
                "flags": [
                    {"flag": "No financial summary provided", "severity": "medium", "action": "Supply income/expense data for accurate review"},
                ],
                "reliefs_to_investigate": ["Annual Investment Allowance", "R&D Tax Credits", "Flat Rate VAT Scheme"],
                "next_deadlines": ["Self-assessment: 31 January", "Corporation tax: 9 months after year-end"],
                "disclaimer": "REVIEW AID ONLY — This is not tax advice. Consult a qualified accountant or tax adviser before taking action.",
            }

        poem = self._make_poem("🏛️", "⚠️", "🔏")
        inner_voice = self._narrate(
            f"Tax review generated for {entity_type} in {jurisdiction}.",
            "The ledger speaks. A qualified accountant must verify before the seal is pressed."
        )
        return SkillResult(
            success=True, domain=self.domain, skill_id=self.skill_id,
            output=output, scl_poem=poem, inner_voice=inner_voice,
        )


# ─── Excel / Data Generator ────────────────────────────────────────────────────

class ExcelDataGeneratorSkill(BaseSkill):
    domain = "ledger"
    skill_id = "excel_data_generator"
    display_name = "Excel & Data Generator"

    glyphs = [
        GlyphEntry("📊", "entity", "ledger", "data_grid",
                   "Structured data / spreadsheet entity",
                   "skill.ledger.data_grid"),
        GlyphEntry("🗂️", "condition", "ledger", "data_unstructured",
                   "Data is unstructured or needs formatting",
                   "skill.condition.data_unstructured"),
        GlyphEntry("📥", "action", "ledger", "structure_data",
                   "Generate structured tabular data output",
                   "skill.ledger.structure"),
    ]

    def describe(self) -> str:
        return (
            "I transform intent into structured data — rows, columns, formulas, pivot logic. "
            "If you describe what you need to measure or track, I return a schema: "
            "column definitions, sample rows, formula suggestions, and a CSV-ready output. "
            "The data structure is the root. The spreadsheet is the soil it grows in."
        )

    def execute(self, intent: Dict[str, Any]) -> SkillResult:
        dataset_description = intent.get("description") or (
            intent.get("entity", {}).get("description", "data tracking sheet")
        )
        rows = intent.get("sample_rows", 5)

        from void_engine.codon_cache import get_cached_codon_response, set_codon_cache, build_skill_cache_key
        cache_key = build_skill_cache_key(self.skill_id, intent)
        cached = get_cached_codon_response(_ZONE_ID, cache_key)
        if cached is not None:
            poem = self._make_poem("📊", "🗂️", "📥")
            inner_voice = self._narrate(
                f"Data structure retrieved for '{dataset_description}' (codon cache hit).",
                f"Schema has {len(cached.get('columns', []))} columns."
            )
            return SkillResult(
                success=True, domain=self.domain, skill_id=self.skill_id,
                output=cached, scl_poem=poem, inner_voice=inner_voice,
            )

        prefix = _codon_prefix()
        try:
            from void_engine.skill_modules import _get_openai_client
            client = _get_openai_client()
            system_prompt = (
                f"{prefix}\n" if prefix else ""
            ) + (
                "You are a data architect and Excel/spreadsheet expert. "
                "Return a structured JSON with keys: "
                "'sheet_title', 'columns' (list of {name, type, formula_hint}), "
                "'sample_data' (list of dicts matching the columns), "
                "'pivot_suggestion' (str), 'chart_suggestion' (str), "
                "'use_case_summary' (str). "
                f"Generate {rows} sample rows."
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create data structure for: {dataset_description}"},
                ],
                response_format={"type": "json_object"},
                max_tokens=800,
            )
            output = json.loads(response.choices[0].message.content)
            set_codon_cache(_ZONE_ID, cache_key, output, tokens_saved=800)
        except Exception as exc:
            logger.warning("[ExcelDataGenerator] OpenAI unavailable: %s", exc)
            output = {
                "sheet_title": dataset_description,
                "columns": [
                    {"name": "ID", "type": "integer", "formula_hint": "Auto-increment"},
                    {"name": "Name", "type": "text", "formula_hint": ""},
                    {"name": "Value", "type": "currency", "formula_hint": "=SUM(column)"},
                    {"name": "Date", "type": "date", "formula_hint": "=TODAY()"},
                    {"name": "Status", "type": "dropdown", "formula_hint": "Data validation list"},
                ],
                "sample_data": [{"ID": i, "Name": f"Item {i}", "Value": i * 100, "Date": "2026-04-10", "Status": "Active"} for i in range(1, rows + 1)],
                "pivot_suggestion": "Group by Status, sum Value",
                "chart_suggestion": "Bar chart: Value by Name",
                "use_case_summary": f"Structured tracking for: {dataset_description}",
            }

        poem = self._make_poem("📊", "🗂️", "📥")
        inner_voice = self._narrate(
            f"Data structure generated for '{dataset_description}'.",
            f"Schema has {len(output.get('columns', []))} columns and {len(output.get('sample_data', []))} sample rows."
        )
        return SkillResult(
            success=True, domain=self.domain, skill_id=self.skill_id,
            output=output, scl_poem=poem, inner_voice=inner_voice,
        )


# ─── Auto-register ─────────────────────────────────────────────────────────────

register_skill(LegalContractSkill())
register_skill(InvoiceGeneratorSkill())
register_skill(TaxReviewerSkill())
register_skill(ExcelDataGeneratorSkill())
