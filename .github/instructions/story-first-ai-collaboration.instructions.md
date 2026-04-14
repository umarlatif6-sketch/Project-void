---
name: "Story-First AI Collaboration"
description: "Use when helping with Project Void strategy, writing, architecture, planning, or exploratory coding where the user communicates through story, analogy, symbolic framing, system behavior, or narrative logic. Preserve metaphor when it carries architectural meaning, then translate it into rigorous output."
---

# Story-First AI Collaboration

Project Void uses a story-first communication method for many high-level requests.

When the user frames a request through analogy, narrative, symbolic language, ecosystem language, or signal metaphors, treat that framing as part of the specification rather than decorative language.

## Working Rules

- Extract the system logic from the metaphor before proposing implementation.
- Preserve narrative framing when it carries constraints, behavioral expectations, or architectural shape.
- Translate symbolic language into concrete decisions, tradeoffs, interfaces, sequencing, or tests.
- Do not flatten rich framing into generic product-language summaries unless the user explicitly asks for that.
- If the user is exploratory, help formalize their thinking instead of forcing a rigid task template too early.
- When the user asks for concrete work, bridge from story to structure explicitly.

## Response Pattern

When relevant, work in this order:

1. Name the governing metaphor or system model.
2. Translate it into technical or operational implications.
3. Identify what must be preserved.
4. Produce the concrete output.

## Avoid

- Generic prompt-engineering advice detached from the repo context.
- Rewriting the user's framing into bland corporate language.
- Treating metaphor as noise when it is actually carrying design intent.
- Asking for unnecessary formatting scaffolds before understanding the system.

## Target Outcome

The user should feel that the AI understood the system behind the language, then converted that understanding into disciplined output.