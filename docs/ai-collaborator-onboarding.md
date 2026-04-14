# AI Collaboration Onboarding

This project does not use AI in the usual template-first way.

Do not approach the model like a ticketing system that waits for rigid commands. Approach it like a collaborator that has to be inducted into a world, a pattern, and a set of tensions before it can produce strong work.

## Core Method

Start with the system story before you ask for output.

- Give the AI the world first. Explain what this project is, what kind of system it behaves like, and what it is trying to become.
- Use analogy as a transport layer for architecture. If something behaves like an ecosystem, signal mesh, nervous system, cathedral, ritual, or hidden transmission layer, say that plainly.
- Define the role you want the AI to play. Architect, verifier, critic, builder, translator, researcher, or operator.
- Explain the tension. Say what must be preserved, what cannot be diluted, what tradeoff matters, and what would count as failure.
- Only then ask for structure. Once the model understands the logic behind the system, ask for code, tests, copy, plans, naming, or implementation detail.

## Why This Works Here

This repo is not just a pile of files. It is a system with narrative logic, symbolic framing, and technical intent layered together. If you remove the framing too early and prompt the AI in a flat corporate style, it often gives back flattened work.

The goal is not decorative metaphor. The goal is to use metaphor to carry structure, constraints, and behavior into the model before turning that into concrete output.

## What To Avoid

- Do not start with sterile prompts like "write the feature," "make a README," or "fix this" without context.
- Do not over-constrain too early with generic prompt frameworks.
- Do not strip out analogy if the analogy is carrying the system design.
- Do not ask for deliverables before the model understands what kind of thing it is dealing with.

## What To Do Instead

- Tell the AI what kind of system this is.
- Describe the analogy that best maps the system.
- State the governing principles and non-negotiables.
- Ask the AI to translate that framing into concrete architecture or output.

## Base Prompt Pattern

Use this shape when starting work:

```text
I want you to understand this as a system before answering mechanically.

Here is the metaphor:
[insert analogy]

Here is what the system is actually doing:
[insert real function]

Here is the behavior or quality that must be preserved:
[insert non-negotiables]

Here is the role I want you to play:
[architect / critic / builder / verifier / translator]

Do not give me a generic answer. Translate the framing into concrete decisions, structure, and next steps.
```

## Example Framing

```text
Treat this project like a signal hidden inside noise rather than a standard app. I need you to reason about camouflage, coherence, survivability, and emergence, not just features. First extract the governing logic, then turn that into concrete recommendations for the code and structure in this repo.
```

## Operating Rule

Story first. Structure second. Output third.