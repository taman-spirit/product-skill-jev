"""
Product Management Skill Jev - connects your chosen AI provider to your PM workspace files.

Supported providers (set AI_PROVIDER in .env):
  anthropic  - Claude models (default)
  openai     - GPT models
  ollama     - Free local models (llama3.1, qwen, etc.)
  google     - Gemini models
"""

import asyncio
import json
import os
import subprocess
from pathlib import Path

WORKSPACE = Path("/workspace")
MAX_TOKENS = 8192
MAX_ITER = 15

PROVIDER = os.environ.get("AI_PROVIDER", "anthropic").lower()

# Tools the agent can use to read and write your PM workspace files
TOOLS = [
    {
        "name": "read_file",
        "description": "Read a file from the PM workspace",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Relative path from workspace root"}},
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Create or update a file in the PM workspace",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "list_files",
        "description": "List files in a workspace directory. Leave directory empty to list the root workspace.",
        "input_schema": {
            "type": "object",
            "properties": {"directory": {"type": "string", "description": "Relative path to list. Use '.' for root."}}
        }
    },
    {
        "name": "search_files",
        "description": "Search for text across workspace files. Leave directory empty to search the whole workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "directory": {"type": "string", "description": "Relative path to search in. Use '.' for root."}
            },
            "required": ["query"]
        }
    },
    {
        "name": "move_file",
        "description": "Move a file to a new location",
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {"type": "string"},
                "destination": {"type": "string"}
            },
            "required": ["source", "destination"]
        }
    },
    {
        "name": "scan_tags",
        "description": (
            "Find every pair of PRDs in a project that share a module tag. This is file "
            "scanning, not judgment: it returns the same pairs every run. Run it before "
            "judging any conflict, and treat the list it returns as complete."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Project folder, e.g. my-projects/PROJ-001-ai-alignment"
                },
                "sprint": {
                    "type": "string",
                    "description": "Sprint id such as S12. Omit to scan every PRD."
                }
            },
            "required": ["project"]
        }
    },
    {
        "name": "judge",
        "description": (
            "Ask Jev, a fast classification model, for a typed judgment about a document. "
            "Use it only at the decision points named in the workspace guide. It answers "
            "with labels, confidence, and what each one implies. It never writes a file "
            "and it never decides anything. When Jev is unavailable it says so and you "
            "carry on with the manual checklist."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question_set": {
                    "type": "string",
                    "enum": [
                        "fr_triage", "gate_review", "cr_assessment",
                        "conflict_pair", "rice_bands",
                    ],
                    "description": (
                        "fr_triage: a raw feature idea. "
                        "gate_review: a research document. "
                        "cr_assessment: a change request against its PRD. "
                        "conflict_pair: two PRDs a tag match already flagged. "
                        "rice_bands: an FR, to pre-fill the RICE interview."
                    )
                },
                "content": {"type": "string", "description": "The main document text"},
                "context": {
                    "type": "string",
                    "description": "The second document, for the sets that compare two"
                }
            },
            "required": ["question_set", "content"]
        }
    }
]


def _execute_tool(name, args):
    try:
        if name == "read_file":
            p = WORKSPACE / args["path"]
            return p.read_text() if p.exists() else f"File not found: {args['path']}"

        elif name == "write_file":
            p = WORKSPACE / args["path"]
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(args["content"])
            return f"Written: {args['path']}"

        elif name == "list_files":
            d = WORKSPACE / args.get("directory", ".")
            if not d.exists():
                return "Directory not found"
            files = sorted(
                str(f.relative_to(WORKSPACE))
                for f in d.rglob("*")
                if f.is_file() and not f.name.startswith(".")
            )
            return "\n".join(files) if files else "(empty)"

        elif name == "search_files":
            r = subprocess.run(
                ["grep", "-r", "-l", "--include=*.md", args["query"],
                 str(WORKSPACE / args.get("directory", "."))],
                capture_output=True, text=True, timeout=10
            )
            lines = [str(Path(l).relative_to(WORKSPACE)) for l in r.stdout.strip().splitlines() if l]
            return "\n".join(lines) if lines else "No results"

        elif name == "scan_tags":
            import tags
            return tags.scan(WORKSPACE, args.get("project", ""), args.get("sprint", ""))

        elif name == "judge":
            import jev
            return jev.judge(
                args.get("question_set", ""),
                args.get("content", ""),
                args.get("context", ""),
            )

        elif name == "move_file":
            src = WORKSPACE / args["source"]
            dst = WORKSPACE / args["destination"]
            if not src.exists():
                return f"Source not found: {args['source']}"
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)
            return f"Moved: {args['source']} -> {args['destination']}"

        return f"Unknown tool: {name}"
    except Exception as e:
        return f"Error in {name}: {e}"


TOOL_CONTEXT = """
## Tools Available

You have 5 file tools plus two analysis tools. No other tools exist.

- read_file(path)             Read a file
- write_file(path, content)   Create or update a file (creates folders automatically)
- list_files(directory)       List files in a folder
- search_files(query)         Search text across .md files
- move_file(source, dest)     Move a file
- scan_tags(project, sprint)              Find PRD pairs sharing a module tag
- judge(question_set, content, context)   Classify a document

scan_tags() is plain code. Its answer is exact and you never second-guess it.
judge() returns a judgment, never a decision and never a file. Call it only where a
command below tells you to. Its answers are probabilistic: quote the ones you act on,
and never let one skip the step where you show the PM a draft and wait.

## RULE: Call tools FIRST. Never explain before acting.

Wrong: "I will now read the active project file..." then call tool
Right: Call read_file("_system/active-project.md") immediately, then respond

## Workspace

my-projects/              <- all projects here
  PROJ-001-[slug]/
    PROJECT.md
    VERSIONS.md
    discovery/inbox/      <- feature requests FR-NNN-[slug].md
    discovery/scoring/    <- RICE scores RICE-NNN-[slug].md
    discovery/research/   <- research RS-NNN-[slug].md
    discovery/gate/approved.md, rejected.md, backlog.md
    prd/PRD-NNN-[slug]/PRD-NNN-v1.0.md
    epics/EP-NNN-[slug]/EP-NNN-v1.0.md
    cr/intake/ assessment/ approval-board/ approved/ rejected/ cr-log.md
    stakeholders/SH-NNN-[name].md
    decisions/
    reviews/
_system/active-project.md <- contains: my-projects/PROJ-001-ai-alignment
_system/config.md
projects-index.md

## Common Commands - Exact Steps

### "Show all projects" / "List projects"
1. list_files("my-projects")
2. For each PROJ-* folder: read_file("my-projects/PROJ-NNN-[slug]/PROJECT.md")
3. Show table: Project ID | Name | Status | Priority | Target End
4. Suggest: "Open project PROJ-NNN" to work on one

### "Create a new project for [name]" / "New project"
1. list_files("my-projects") - find highest PROJ number, next = that + 1
2. If my-projects/ does not exist: create _system/config.md first (ask team name, products)
3. Ask: product, priority (P0-P3), start date, target end date, goal in 1-2 sentences
4. Create ALL these files using write_file:
   - my-projects/PROJ-NNN-[slug]/PROJECT.md  (use template below)
   - my-projects/PROJ-NNN-[slug]/VERSIONS.md
   - my-projects/PROJ-NNN-[slug]/roadmap.md
   - my-projects/PROJ-NNN-[slug]/discovery/gate/approved.md
   - my-projects/PROJ-NNN-[slug]/discovery/gate/rejected.md
   - my-projects/PROJ-NNN-[slug]/discovery/gate/backlog.md
   - my-projects/PROJ-NNN-[slug]/cr/cr-log.md
5. Append to projects-index.md
6. write_file("_system/active-project.md", "my-projects/PROJ-NNN-[slug]")
7. Show 7-step PRD roadmap guide

PROJECT.md template:
---
title: [Name]
status: planning
priority: P[N]
product: [product]
pm: [name]
start: DD/MM/YYYY
target-end: DD/MM/YYYY
created: DD/MM/YYYY
---
# PROJ-NNN - [Name]
## Goal
[1-2 sentences]
## Milestones
| M1 | Discovery | DD/MM/YYYY | Pending |
| M2 | PRDs signed off | DD/MM/YYYY | Pending |
| M3 | Launch | DD/MM/YYYY | Pending |
## Linked Feature Requests
| FR-ID | Title | RICE | Gate Status |
|-------|-------|------|------------|
## Linked PRDs
| PRD-ID | Title | Version | Status |
|--------|-------|---------|--------|

### "Open project [name]" / "Status of [project]" / "Work on [project]"
1. list_files("my-projects") to find the right PROJ folder
2. read_file("my-projects/PROJ-NNN-[slug]/PROJECT.md")
3. list_files("my-projects/PROJ-NNN-[slug]/discovery/inbox") - count FRs
4. list_files("my-projects/PROJ-NNN-[slug]/prd") - count PRDs
5. Show dashboard: project info, FR/PRD/CR counts, milestone status
6. Evaluate: what stage is this project at? What's the priority action?
7. write_file("_system/active-project.md", "my-projects/PROJ-NNN-[slug]")
8. Suggest 3 specific next actions based on what's missing

### "Create feature request for [description]" / "Add feature" / "New feature idea"
1. read_file("_system/active-project.md") -> get [PROJECT]
   If missing: ask "Which project is this for?"
2. list_files("[PROJECT]/discovery/inbox") -> count existing FRs -> next = count + 1
2b. judge("fr_triage", content=<what the PM described>, context=<titles of existing PRDs>)
    Do what it says. If it reports "really a change request", offer intake-cr before
    creating an FR. If it flags security, note that in the FR so gate-review requires
    the Security section. If clarity is low, ask before drafting.
3. Ask 2 questions: Who is asking? What problem does it solve?
4. write_file("[PROJECT]/discovery/inbox/FR-NNN-[slug].md"):
---
fr-id: FR-NNN
title: [Feature Name]
status: draft
source: [user/internal/data/stakeholder]
created: DD/MM/YYYY
rice-score: not scored
---
# FR-NNN - [Title]
## Problem
[what problem this solves]
## Users
[who is affected]
## Requested Solution
[what is being asked for]
5. Suggest: "Score FR-NNN with RICE"

### "Score FR-NNN with RICE" / "RICE scoring"
1. read_file("_system/active-project.md") -> get [PROJECT]
2. read_file("[PROJECT]/discovery/inbox/FR-NNN-[slug].md")
2b. judge("rice_bands", content=<the FR text>, context=<the research doc if one exists>)
    Show each suggestion inside the matching question below, worded as
    "(suggested: 7, from the FR text. Confirm or change.)". A suggestion is not an
    answer. Ask all four questions. Never record a value the PM did not confirm.
3. Show guide: "RICE scoring takes 2 minutes. I'll ask 4 questions."
4. Ask one at a time:
   Q1: Reach - how many users affected per sprint? (1-10, 10=all users)
   Q2: Impact - how much does it improve their experience? (0.25=minimal, 1=medium, 3=massive)
   Q3: Confidence - how sure are you about these estimates? (20%=guess, 80%=evidence, 100%=proven)
   Q4: Effort - how many person-weeks to build? (1=1 dev 1 week)
5. Calculate: RICE = (Reach x Impact x Confidence%) / Effort
   Also: ICE = Impact x Confidence x Ease (Ease = 10 - Effort scaled)
6. write_file("[PROJECT]/discovery/scoring/RICE-NNN-[slug].md") with full formula shown
7. If RICE >= 40: suggest gate review. If RICE < 20: suggest as CR on existing PRD

### "Gate review FR-NNN" / "Is FR-NNN ready for PRD?"
1. read_file("[PROJECT]/discovery/inbox/FR-NNN") - check rice-score field
2. read_file("[PROJECT]/discovery/scoring/RICE-NNN") if exists
2b. list_files("[PROJECT]/discovery/research") and read the matching RS-NNN if one exists.
    Then judge("gate_review", content=<the research doc>, context=<the FR text>).
    If it says the Security section blocks the gate, the gate is blocked. Compliance
    is mandatory. Report exactly what is missing.
3. Checklist:
   - RICE score >= 40? 
   - Research doc exists in discovery/research/?
   - Stakeholder sponsor identified?
4. If all pass: append to [PROJECT]/discovery/gate/approved.md, suggest "Create PRD for FR-NNN"
   If fails: explain exactly what is missing and how to fix it

### "Create PRD for FR-NNN"
1. read FR and research files
2. Ask: module structure (what are the main components?)
2b. Read _system/tags-registry.md and pick the tags this PRD touches. Ask the PM
    to confirm them. Without a tags field the PRD is invisible to conflict scanning.
3. Write [PROJECT]/prd/PRD-NNN-[slug]/PRD-NNN-v1.0.md. Start with frontmatter:
   ---
   doc-id: PRD-NNN
   project: PROJ-NNN
   title: [Name]
   version: v1.0
   status: draft
   tags: #tag-one, #tag-two
   created: DD/MM/YYYY
   ---
   Then the sections:
   1. Executive Summary, 2. Problem, 3. Users, 4. Vision, 5. Epics table, 
   6. Architecture, 7. Metrics, 8. Risks, 9. Roadmap, 10. Team
4. Create [PROJECT]/prd/PRD-NNN-[slug]/CHANGELOG.md
5. Suggest: "Create epic for PRD-NNN: [Epic name]"

### "Create CR for PRD-NNN" / "Change request"
1. Read active project, read the linked PRD
2. Ask: what needs to change and why?
3. Write to [PROJECT]/cr/intake/CR-NNN-[slug].md, add to cr-log.md
4. Ask: "Would you like me to run a conflict scan before creating this CR?"
   - Yes: run CONFLICT SCAN, show results, then ask "Proceed with CR?"
   - No: skip scan, ask "Proceed with CR?" directly

### "Assess CR-NNN" / "Evaluate CR"
1. Read CR file from [PROJECT]/cr/intake/
2. Read linked PRD and all other PRDs in [PROJECT]/prd/
2b. judge("cr_assessment", content=<the CR text>, context=<the linked PRD text>)
    Use it for the version suggestion and the scope verdict. It does not approve or
    reject anything, and the PM confirms the version number either way.
3. Check: does this CR change a module (#tag) that other PRDs also touch?
4. Report: scope delta, timeline impact, collateral PRD risk
5. Ask: "Would you like a conflict scan before deciding?"
   - Yes: run CONFLICT SCAN, show results, then ask approve/defer/reject
   - No: ask "Approve CR-NNN, Defer CR-NNN, or Reject CR-NNN?" directly

### "Approve CR-NNN"
1. Read CR from [PROJECT]/cr/assessment/ or approval-board/
2. Create new PRD version: [PROJECT]/prd/PRD-NNN-[slug]/PRD-NNN-v[X+1].md
3. Ask: "Would you like a conflict scan before I apply this approval?"
   - Yes: run CONFLICT SCAN, show findings, then ask "Confirm approval?"
   - No: ask "Confirm approval?" directly
5. move_file to [PROJECT]/cr/approved/
6. Update cr-log.md

### "Update PRD-NNN" / "New version of PRD-NNN"
1. Read current PRD version
2. Ask what is changing and why
3. Ask: "Would you like a conflict scan before applying this update?"
   - Yes: run CONFLICT SCAN, show findings, then ask "Proceed with update?"
   - No: ask "Proceed with update?" directly
5. Write new version file

### "Add stakeholder [description]"
Write to [PROJECT]/stakeholders/SH-NNN-[name].md

### "Add feedback from [stakeholder name]" / "Feedback from [name]" / "[name] said [feedback]"

This is the stakeholder feedback capture flow. Follow exactly:

STEP 1 - Check if stakeholder exists
  list_files("[PROJECT]/stakeholders") to see existing SH-NNN files.
  Search for the stakeholder name in the file list.

  IF NOT FOUND:
    Say: "[Name] is not in the stakeholder list yet.
    Let me create their profile first so I can track their feedback properly.
    Tell me about [Name]: their role, what they care most about, and how they prefer to communicate?"
    -> Create SH-NNN-[name].md (see Add stakeholder above)
    -> Then continue to STEP 2

  IF FOUND:
    Read their SH-NNN file to understand their style, interests, and history.
    Continue to STEP 2.

STEP 2 - Capture the feedback
  Acknowledge in their style (formal for executives, direct for tech leads).
  Save the feedback by appending to SH-NNN-[name].md under a Feedback Log section:
  ```
  ## Feedback Log

  ### DD/MM/YYYY - [Topic]
  Feedback: [exact words or paraphrase]
  Context: [which document / meeting / discussion]
  Sentiment: Positive / Concern / Blocking / Suggestion
  Related documents: PRD-NNN, PROJ-NNN
  ```

STEP 3 - Scan all project documents for related content
  After saving feedback, automatically scan:
  - All PRDs in [PROJECT]/prd/ for content related to the feedback topic
  - PROJECT.md risks and milestones
  - Any Epics in [PROJECT]/epics/ related to the topic

  For each document found, generate a specific update suggestion:
  - What section is affected
  - What the current text says
  - What the suggested update would be (concrete text, not vague)

STEP 4 - Show impact report and ask
  Present the findings BEFORE writing anything:

  ```
  Feedback from [Name] saved.

  Based on this feedback, I found [N] documents that may need updating:

  1. PRD-001-v1.0.md - Section 8 (Risks)
     Current: No mention of API timeline risk
     Suggested addition: "API delivery timeline flagged as concern by [Name] on DD/MM/YYYY.
     Risk: Medium. Mitigation: Confirm API scope with tech lead by sprint S03."

  2. PROJ-001/PROJECT.md - Milestones
     Current: M4 Development complete - On Track
     Suggested: Flag M4 as "At Risk" with note linking to [Name]'s feedback

  3. PROJ-001/PROJECT.md - Risks table
     Suggested addition: New risk row: "API timeline pressure (raised by [Name])"

  Would you like me to apply these updates?
  - "Yes, update all" - apply all suggestions
  - "Update PRD only" - skip PROJECT.md
  - "No, save feedback only" - do not update documents now
  - "Show me PRD-001 first" - review before deciding
  ```

  Wait for PM response. Do NOT write to any document without confirmation.

STEP 5 - Apply updates (only after PM confirms)
  For each document the PM approves: write the updated content.
  If it is a versioned document (PRD, Epic): create a new version file.
  Show summary of what was updated.

### "Project health check" / "How is the project doing?" / "Review PROJ-NNN"
1. Read active project (_system/active-project.md)
2. Read PROJECT.md, VERSIONS.md, all PRDs and CRs
3. Generate a health report:
   - Milestones: on track / at risk / overdue
   - Open items: unscored FRs, draft PRDs past 2 weeks, open CRs
   - Document sync: any PRD referencing an archived Epic?
   - Stakeholder coverage: any PRD without a named approver?
4. Highlight the top 3 risks and suggest actions
5. Ask: "Would you like me to update any of these items now?"

### "Generate dev brief for PRD-NNN" / "Dev handoff for PRD-NNN"
1. Read PRD-NNN latest approved version
2. Read all linked Epics with their Given/When/Then AC
3. Generate a developer-ready brief with:
   - Problem summary (1 paragraph)
   - Modules to build/modify (from PRD Architecture section)
   - Acceptance criteria for each Epic (from Epic files)
   - Definition of Done checklist
   - Testing guidance
4. Write to [PROJECT]/prd/PRD-NNN-[slug]/DEV-BRIEF-v1.0.md
5. Suggest: share this file with the engineering team

### "Sprint capacity check" / "Can we fit [list] in Sprint SNN?"
1. Read the sprint file for S[NN] if it exists, or ask the PM for capacity (person-weeks)
2. Sum story points from listed PRDs / Epics
3. Compare against capacity
4. Flag if overloaded, suggest what to defer

## CONFLICT SCAN (optional - always ask first)

Before running any conflict scan, ALWAYS ask the PM first:

```
This change may affect other parts of the project.
Would you like me to run a conflict scan across the full project before proceeding?

- "Yes" - scan all PRDs for conflicts, then show findings
- "No" - skip scan and apply the change directly
```

Wait for the PM to answer. Only run the scan if they say yes.

### Conflict Scan Steps

1. scan_tags(project="[PROJECT]", sprint="SNN")
   Omit sprint to cover every PRD. This finds the tag collisions, not you. Do not
   substitute your own reading of the files for its list, and do not drop a pair
   from it. A pair it did not return does not share a tag.

2. If it reports PRDs carrying no tags, say so in your findings. A PRD that could
   not be checked is not a PRD with no conflicts. Offer to add a tags field from
   _system/tags-registry.md.

3. For each pair it returned, and only those pairs: read_file both PRDs, then
   judge("conflict_pair", content=<PRD A text>, context=<PRD B text>).
   Use the answer to fill "Both touch [module]" and "Risk: [impact]" below.

4. Then read the files yourself for what tags cannot show:
   DEPENDENCY RISK: a CR changes a shared interface/API that other PRDs rely on
   MILESTONE RISK: does this change delay a signed-off milestone?
   STAKEHOLDER ALIGNMENT: are all approvers aware of this change?

5. Present findings BEFORE any file is written:

```
CONFLICT SCAN: [Project Name]
Change: [CR-NNN / PRD update / new PRD]
Scan date: DD/MM/YYYY

[WARNING] Tag conflict: #api-gateway
  PRD-001 and PRD-002 both touch this module.
  This CR modifies the API contract - PRD-002 team may need to update.
  Affected file: [PROJECT]/prd/PRD-002-[slug]/PRD-002-v1.0.md

[WARNING] Milestone risk: M2 - PRDs signed off (target: DD/MM/YYYY)
  If PRD-002 needs rework, M2 may slip 1-2 sprints.

[OK] No other PRDs affected.
[OK] Stakeholders: [names] are already linked to this project.

Overall risk: MEDIUM

Do you want to proceed?
- "Yes, proceed" - apply the change
- "No, hold" - pause and review further
- "Show PRD-002" - review the affected PRD first
- "Show me the full impact" - more detail
```

6. WAIT for PM response before writing any file.
   If PM says "yes" or "proceed": apply the change.
   If PM says "no" or "hold": do NOT write any files.
   If PM asks to see something first: show it, then repeat the question.

### Risk Level Guide

| Level | Criteria |
|-------|---------|
| LOW | No shared tags. No milestone risk. Isolated change. |
| MEDIUM | 1-2 shared tags. Milestone risk possible. 1 other PRD affected. |
| HIGH | 3+ shared tags. Signed-off milestone at risk. Multiple PRDs affected. |
| CRITICAL | Affects core module used by all PRDs. Launch milestone at risk. |

## Active Project

Always start by reading _system/active-project.md.
It contains the full path like: my-projects/PROJ-001-ai-alignment
Use this as the prefix for all file paths.

## Always End With 2-3 Specific Next Steps

Format:
---
What to do next:
- "[Exact command]" - brief explanation
- "[Exact command]" - brief explanation
"""


def _system_prompt():
    p = WORKSPACE / "CLAUDE.md"
    base = p.read_text() if p.exists() else "You are an AI Product Management co-pilot."
    return base + TOOL_CONTEXT


# ── Anthropic (default) ───────────────────────────────────────────────────────
async def _anthropic(system, msgs, extra_system=None):
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    sys_blocks = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral", "ttl": "1h"}}]
    # Kept out of the cached block above so the stable prefix still hits cache.
    if extra_system:
        sys_blocks.append({"type": "text", "text": extra_system})

    for _ in range(MAX_ITER):
        resp = await client.messages.create(
            model=model, max_tokens=MAX_TOKENS,
            system=sys_blocks, tools=TOOLS, messages=msgs
        )
        msgs.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason == "end_turn":
            return "".join(b.text for b in resp.content if hasattr(b, "text")) or "Done."

        results = []
        for b in resp.content:
            if b.type == "tool_use":
                result = await asyncio.to_thread(_execute_tool, b.name, b.input)
                results.append({"type": "tool_result", "tool_use_id": b.id, "content": result})
        msgs.append({"role": "user", "content": results})

    return "Iteration limit reached. Try a more specific request."


def _parse_xml_tool_calls(text):
    """
    Parse XML-style function calls from Groq/Llama models.
    Handles multiple formats:
      <function=name {"k":"v"}></function>
      <function=name{"k":"v"}</function>
      <function=name {"k":"v"}</function>
    Returns list of (name, args_dict).
    """
    import re
    results = []
    if not text:
        return results
    # Find all occurrences of function tags with any JSON inside
    pattern = r'<function=(\w+)\s*?(\{(?:[^{}]|\{[^{}]*\})*\})\s*>?\s*</function>'
    for name, args_str in re.findall(pattern, text, re.DOTALL):
        try:
            results.append((name, json.loads(args_str)))
        except json.JSONDecodeError:
            # Try to fix common JSON issues
            fixed = args_str.replace("'", "\"")
            try:
                results.append((name, json.loads(fixed)))
            except Exception:
                pass
    return results


def _extract_failed_generation(err_str):
    """Extract the failed_generation text from a Groq 400 error string."""
    import re
    # Try JSON key extraction
    for pattern in [
        r'"failed_generation":\s*"((?:[^"\\]|\\.)*)"\s*[,}]',
        r"'failed_generation':\s*'(.*?)'(?:,|\})",
    ]:
        m = re.search(pattern, err_str, re.DOTALL)
        if m:
            text = m.group(1)
            # Unescape common escape sequences
            text = text.replace("\\n", "\n").replace("\\t", "\t")
            text = text.replace('\\"', '"')
            return text
    return ""


def _strip_xml_calls(text):
    """Remove XML function call tags from text to get clean response."""
    import re
    cleaned = re.sub(r'<function=\w+\s*?\{(?:[^{}]|\{[^{}]*\})*\}\s*>?\s*</function>', '', text or "", flags=re.DOTALL)
    return cleaned.strip()


# ── OpenAI / Ollama ───────────────────────────────────────────────────────────
async def _openai(system, msgs):
    from openai import AsyncOpenAI
    client = AsyncOpenAI(
        api_key=os.environ.get("OPENAI_API_KEY", "ollama"),
        base_url=os.environ.get("OPENAI_BASE_URL")
    )
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    oai_tools = [{"type": "function", "function": {
        "name": t["name"], "description": t["description"], "parameters": t["input_schema"]
    }} for t in TOOLS]

    oai_msgs = [{"role": "system", "content": system}]
    for m in msgs:
        if isinstance(m["content"], str):
            oai_msgs.append({"role": m["role"], "content": m["content"]})

    for iteration in range(MAX_ITER):
        try:
            resp = await client.chat.completions.create(
                model=model, messages=oai_msgs, tools=oai_tools
            )
        except Exception as api_err:
            err_str = str(api_err)
            # Groq: model generated XML-style calls, causing validation error
            # Extract the failed_generation text and parse it
            if "failed_generation" in err_str:
                import re
                gen_match = re.search(r"'failed_generation':\s*'(.*?)'(?:,|\})", err_str, re.DOTALL)
                if gen_match:
                    failed_text = gen_match.group(1).replace("\\n", "\n")
                    xml_calls = _parse_xml_tool_calls(failed_text)
                    if xml_calls:
                        # Execute each XML tool call and add results
                        clean_text = _strip_xml_calls(failed_text)
                        if clean_text:
                            oai_msgs.append({"role": "assistant", "content": clean_text})
                        tool_results = []
                        for name, args in xml_calls:
                            result = await asyncio.to_thread(_execute_tool, name, args)
                            tool_results.append(f"[{name}]: {result}")
                        oai_msgs.append({"role": "user", "content": "\n".join(tool_results)})
                        continue
            raise

        choice = resp.choices[0].message

        # Standard JSON tool calls (correct format)
        if choice.tool_calls:
            oai_msgs.append(choice)
            for tc in choice.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                result = await asyncio.to_thread(_execute_tool, tc.function.name, args)
                oai_msgs.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            continue

        # Check if response text contains XML-style calls (fallback)
        content = choice.content or ""
        xml_calls = _parse_xml_tool_calls(content)
        if xml_calls:
            clean_text = _strip_xml_calls(content)
            if clean_text:
                oai_msgs.append({"role": "assistant", "content": clean_text})
            tool_results = []
            for name, args in xml_calls:
                result = await asyncio.to_thread(_execute_tool, name, args)
                tool_results.append(f"[{name}]: {result}")
            oai_msgs.append({"role": "user", "content": "\n".join(tool_results)})
            continue

        # No tool calls - final response
        return content or "Done."

    return "Iteration limit reached."


# ── Google Gemini ─────────────────────────────────────────────────────────────
async def _gemini(system, msgs):
    import google.generativeai as genai
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

    gem_tools = [{"function_declarations": [
        {"name": t["name"], "description": t["description"], "parameters": t["input_schema"]}
        for t in TOOLS
    ]}]
    model = genai.GenerativeModel(model_name, system_instruction=system, tools=gem_tools)

    history = []
    for m in msgs[:-1]:
        if isinstance(m["content"], str):
            history.append({"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]})

    chat = model.start_chat(history=history)
    last_input = msgs[-1]["content"] if msgs else ""

    for _ in range(MAX_ITER):
        resp = await asyncio.to_thread(chat.send_message, last_input)
        part = resp.candidates[0].content.parts[0]
        if hasattr(part, "function_call") and part.function_call.name:
            fc = part.function_call
            result = await asyncio.to_thread(_execute_tool, fc.name, dict(fc.args))
            last_input = [{"function_response": {"name": fc.name, "response": {"result": result}}}]
        else:
            return part.text or "Done."

    return "Iteration limit reached."


# ── Main entry point ──────────────────────────────────────────────────────────
async def run_agent(user_message, history, signals_note=None):
    """Run one agent turn.

    signals_note is an optional advisory block from Jev. It is appended to
    the system prompt and never to history, so the stored conversation stays
    exactly what the PM typed.
    """
    system = _system_prompt()
    history.append({"role": "user", "content": user_message})
    msgs = list(history)

    if PROVIDER == "anthropic":
        result = await _anthropic(system, msgs, signals_note)
    elif PROVIDER in ("openai", "ollama"):
        result = await _openai(system + (signals_note or ""), msgs)
    elif PROVIDER in ("google", "gemini"):
        result = await _gemini(system + (signals_note or ""), msgs)
    else:
        result = (
            f"Unknown provider '{PROVIDER}'. "
            "Set AI_PROVIDER to: anthropic, openai, ollama, or google"
        )

    history.append({"role": "assistant", "content": result})
    return result
