---
name: write-a-skill
description: Create new agent skills with proper structure, conventions, and registration. Use when the user wants to create, write, author, or build a new skill for this plugin, or when adding a new capability to the ai-plugins repository.
---

# Write a Skill

Step-by-step workflow for creating a new skill in this repository. Every new skill follows the same structure and must be registered in `README.md`.

A skill exists to wrangle **predictability** out of a stochastic system — the agent taking the same _process_ every run, not the same output. Every decision below serves that goal.

**Bold terms** are defined in [`GLOSSARY.md`](GLOSSARY.md); consult it when a term is unfamiliar.

## Before You Start

1. **Read `AGENTS.md`** at the repo root for repository conventions and rules.
2. **Browse existing skills** in `skills/` to see the patterns in use. Good references:
   - `skills/code-review/SKILL.md` — multi-command routing skill
   - `skills/develop-feature/SKILL.md` — multi-phase workflow skill
   - `skills/jira-cli/SKILL.md` — CLI wrapper skill

## Step 1: Gather Requirements

Ask the user about:

- **Domain**: What task or workflow does the skill cover?
- **Use cases**: What specific scenarios should it handle?
- **Triggers**: What words or phrases should activate it? (e.g., "review", "deploy", "migrate")
- **Complexity**: Single workflow or multiple **branches** (distinct invocation paths)?
- **Invocation**: Should the agent fire this autonomously (**model-invoked**) or only when the user types its name (**user-invoked**)? See [Invocation Design](#invocation-design).
- **Scripts**: Does it need executable scripts, or is it instructions-only?
- **References**: Any external docs, APIs, or materials to include?

**Completion criterion**: You can state back the skill's purpose, every branch it handles, and whether it is model- or user-invoked, without asking another question.

## Step 2: Create the Skill Directory

```
skills/<skill-name>/
├── SKILL.md           # Main instructions (required)
├── GLOSSARY.md        # Definitions / reference (if terms accumulate)
├── REFERENCE.md       # Detailed reference docs (if content exceeds ~100 lines)
└── scripts/           # Utility scripts (if deterministic operations needed)
    └── helper.sh
```

The directory name must be `kebab-case` and match the skill's `name` field in the frontmatter.

**Completion criterion**: The directory exists with at least an empty `SKILL.md`.

## Step 3: Write SKILL.md

### Frontmatter (required)

Every `SKILL.md` starts with YAML frontmatter:

```yaml
---
name: <skill-name>
description: <what it does>. Use when <specific triggers>.
---
```

**Frontmatter rules:**
- `name` must match the directory name exactly.
- `description` is the **only thing the agent sees** when picking which skill to load. Make it count.
- First sentence: state the capability, front-loading a **leading word** that anchors the skill's identity.
- Second sentence: "Use when [specific triggers, keywords, contexts]."
- One trigger per **branch** — collapse synonyms. "Build features using TDD … asks for test-first development" is one branch written twice; keep only genuinely distinct branches.
- Cut identity already in the body — the description is for triggers, not repeating the overview.
- Max 1024 characters.

### Body Structure

Organize content using the **information hierarchy** — a ladder ranked by how immediately the agent needs the material:

1. **In-skill steps** — ordered actions the agent performs. The primary tier.
2. **In-skill reference** — definitions, rules, or facts consulted on demand. Secondary.
3. **Disclosed reference** — content pushed to a separate file (e.g., `GLOSSARY.md`), reached by a **context pointer**. Loaded only when needed.

```markdown
# Skill Title

Brief overview (1–2 sentences).

## Workflow

Step-by-step instructions. Use numbered lists for ordered processes.
Every step ends on a **completion criterion** — a checkable condition
that tells the agent the work is done.

## Guidelines

Constraints, edge cases, and best practices specific to this skill.
```

### Writing Rules

- **No hardcoded commands.** Do not embed specific make targets, CLI commands, or tool invocations as defaults. Instruct the agent to discover them by reading `AGENTS.md`, `Makefile`, or project configuration files. Even "example" commands in parentheses bias the agent.
- **End each step with a completion criterion.** Make it _checkable_ (can the agent tell done from not-done?) and _exhaustive_ where it matters ("every modified model accounted for", not "produce a change list"). A vague criterion invites **premature completion** — the agent's attention slipping to _being done_ rather than to the work.
- **Use leading words.** Find compact, pretrained terms that anchor behavior in the fewest tokens (e.g., _tight_ instead of "fast, deterministic, low-overhead"). A strong leading word recruits priors the model already holds — fewer tokens, sharper behavior.
- **Hunt no-ops.** Test each sentence: does it change behavior versus the default? If not, delete it. A weak leading word (_be thorough_ when the agent is already thorough) is a no-op; the fix is a stronger word (_relentless_), not more prose.
- **Prune aggressively.** Keep each meaning in a **single source of truth**. Run the no-op test sentence by sentence — when one fails, delete the whole sentence rather than trim words. Most prose that fails should go, not be rewritten.
- **Co-locate related material.** Keep a concept's definition, rules, and caveats under one heading rather than scattered, so reading one part brings its neighbours with it.
- **Cross-reference other skills** using relative paths when your skill depends on or extends another (e.g., `[review engine](../review-engine/SKILL.md)`).

### When to Split Files (Progressive Disclosure)

Move **reference** down the information hierarchy — out of `SKILL.md` and behind a **context pointer** — so the top stays legible. This is **progressive disclosure**.

Split into separate files when:

- `SKILL.md` exceeds ~100 lines (the skill is **sprawling**)
- Content has distinct domains (e.g., different review perspectives, separate API references)
- Only some **branches** need the material — inline what every branch needs, disclose what only some reach
- Reference is large but only consulted occasionally

Use relative links from `SKILL.md` to reference split files. The pointer's _wording_ decides how reliably the agent reaches the material — make it precise.

## Step 4: Write the Description

The description is the skill's machine-readable trigger and the source of its **context load** — the cost it imposes on the agent's context window every turn.

**Good description:**
```
Extract text and tables from PDF files, fill forms, merge documents.
Use when working with PDF files or when user mentions PDFs, forms,
or document extraction.
```

**Bad description:**
```
Helps with documents.
```

**Checklist:**
- [ ] Front-loads a **leading word** that anchors invocation
- [ ] First sentence states the capability clearly
- [ ] Second sentence lists specific trigger words/contexts
- [ ] One trigger per **branch** — no synonym duplication
- [ ] Under 1024 characters
- [ ] Written in third person
- [ ] Distinct from every other skill's description in this repo
- [ ] Does not repeat identity already in the body

## Step 5: Create the Command File

Every skill should have a matching command file at `commands/<skill-name>.md`.

Follow this pattern (derived from existing commands in this repo):

```markdown
---
name: <skill-name>
description: <short description of what the command does>.
---

# <Skill Title> Command

Follow the `<skill-name>` skill from this plugin.

Use the text after the command name as the input. If your command
runtime exposes `$ARGUMENTS`, treat it as that same value.

Read and follow:
- `skills/<skill-name>/SKILL.md`

<Brief guidance on default behavior or how to handle missing input.>
```

**Completion criterion**: The command file exists, its frontmatter is valid, and its "Read and follow" section points to the correct `SKILL.md`.

## Step 6: Update README.md

**This step is mandatory.** Open `README.md` at the repo root and add the new skill and command to the tables.

### Add to the Skills table

Insert a new row in alphabetical order:

```markdown
| <skill-name> | <short description> | [`skills/<skill-name>/`](skills/<skill-name>/) |
```

### Add to the Commands table

Insert a new row in alphabetical order:

```markdown
| <skill-name> | <short description> | [`commands/<skill-name>.md`](commands/<skill-name>.md) |
```

**Completion criterion**: Both tables contain the new entries in alphabetical order, and the directory tree in the Repository Structure section is updated.

## Step 7: Review Checklist

Before finishing, verify every item. Each is a **completion criterion** for the skill as a whole:

- [ ] `skills/<skill-name>/SKILL.md` exists with valid YAML frontmatter (`name`, `description`)
- [ ] `name` in frontmatter matches the directory name
- [ ] Description front-loads a **leading word** and includes trigger phrases ("Use when...")
- [ ] Description has one trigger per branch — no synonym duplication
- [ ] Steps end with checkable **completion criteria**
- [ ] No **no-ops** — every sentence changes behavior versus the default
- [ ] No **duplication** — each meaning has a **single source of truth**
- [ ] No hardcoded CLI commands or make targets in the skill body
- [ ] Content follows the **information hierarchy** — steps on top, reference below, disclosed reference behind pointers
- [ ] If `SKILL.md` exceeds ~100 lines, reference is split via **progressive disclosure**
- [ ] Consistent terminology — **leading words** used throughout, not restated as synonyms
- [ ] `commands/<skill-name>.md` exists with valid frontmatter and "Read and follow" section
- [ ] `README.md` updated with new entries in both Skills and Commands tables
- [ ] Cross-references to other skills use relative paths (e.g., `../review-engine/SKILL.md`)
- [ ] If scripts are included, they handle errors explicitly

---

## Reference

### Invocation Design

Two choices, trading different costs:

- **Model-invoked** — the skill keeps a `description`, so the agent fires it autonomously. Other skills can reach it too. Pays permanent **context load** (the description sits in the window every turn). Pick this when the agent must reach the skill on its own, or another skill must invoke it.
- **User-invoked** — the skill strips or disables its description. Only the user typing its name can invoke it. Zero context load, but pays **cognitive load** (the user must remember it exists). Pick this when the skill only fires by hand.

When user-invoked skills multiply past what you can remember, cure the cognitive load with a **router skill** — one skill that names the others and when to reach for each.

In this repo, most skills are model-invoked (they have descriptions with trigger phrases). Use `disable-model-invocation: true` in frontmatter only when the skill is a low-level utility that should never auto-trigger.

### Failure Modes

Use these to diagnose when a skill isn't working well:

- **Premature completion** — the agent ends a step before it's genuinely done, attention slipping to _being done_. Defence: sharpen the **completion criterion** first (cheap, local); only if it's irreducibly fuzzy _and_ you observe the rush, hide later steps by splitting the sequence.
- **Duplication** — the same meaning in more than one place. Costs maintenance, tokens, and inflates a meaning's prominence past its real rank. Collapse into a **leading word** or a single source of truth.
- **Sediment** — stale layers that settle because adding feels safe and removing feels risky. The default fate of any skill without a pruning discipline.
- **Sprawl** — a skill simply too long, even when every line is live and unique. The cure is the information hierarchy: disclose reference behind context pointers, split by branch or sequence.
- **No-op** — a line the model already obeys by default. The test: does it change behaviour versus the default? A weak leading word is a no-op; the fix is a stronger word, not a different technique.

### When to Add Scripts

Add utility scripts when:

- An operation is deterministic (validation, formatting, data transformation)
- The same code would be generated repeatedly by the agent
- Errors need explicit, reliable handling that generated code might miss

Scripts save tokens and improve reliability compared to having the agent regenerate boilerplate code each time.
