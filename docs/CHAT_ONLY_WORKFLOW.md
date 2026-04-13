# Chat-Only Workflow (No Coding Required)

This project can be operated entirely from chat prompts.
You do not need to open code files, databases, or terminals manually.

## What To Ask In Chat

Use these exact requests to run the full loop:

1. Ingest your latest notes:
- "Run story-world ingest on the template file at threshold 0.35 and store to DB."

2. Build your weekly chronicle:
- "Build the story world chronicle markdown from the latest JSONL output."

3. Give me top analogies/perspectives:
- "Show top 20 analogies and perspectives grouped by Name cluster from story_world."

4. Open the UI navigation:
- "Start the server and tell me where to click for Signals Navigator."

5. Keep me synced after disconnect:
- "Resume from checkpoint and summarize what changed since the last run."

## Zero-Code UI Navigation

Open: `/knowledge-tree`

In the right panel:
- Use `Signals Navigator`
- Filter by:
  - signal type: all / analogy / perspective
  - Name cluster
  - search keywords
- Click any signal card to jump to its linked node reading

## Files You Care About (Reference Only)

- Input notes template: `data/story_world_ingest_template.jsonl`
- Ingested output: `data/story_world_ecosystem.jsonl`
- Chronicle output: `docs/STORY_WORLD_CHRONICLE.md`

## Cost-Safe Operating Mode

- Keep everything GitHub + local workspace based
- Avoid paid external tools/services
- Use this chat as control plane for ingestion, summarization, and navigation

## If You Disconnect

When you return, just type:
- "Continue from checkpoint and give me a short status update."
