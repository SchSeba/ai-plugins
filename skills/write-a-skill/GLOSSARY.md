# Glossary — Write a Skill

Domain vocabulary for skill authoring. This is the disclosed reference for [`write-a-skill`](SKILL.md), adapted from [mattpocock's writing-great-skills](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-great-skills/SKILL.md). **Bold terms** in any definition are themselves defined here.

## Core Concepts

### Predictability

The degree to which a skill makes the agent behave the same _way_ on every run — the same process, not the same output. The root virtue every other term serves.

### Leading Word

A compact concept already living in the model's pretraining that the agent thinks with while running the skill. It encodes a behavioural principle in the fewest possible tokens by invoking priors the model already holds (e.g., _lesson_, _fog of war_, _tracer bullets_). Repeated as a token — not as a sentence — it accumulates a distributed definition and anchors behaviour. In the body it anchors execution; in the **description** it anchors invocation. Reach for an existing pretrained word first; coining your own works but recruits no priors.

### Single Source of Truth

Each meaning lives in exactly one authoritative place, so changing the skill's behaviour is a one-place edit. **Duplication** is its violation.

## Information Architecture

### Information Hierarchy

A skill's content ranked by how immediately the agent needs it — a single ladder:

1. **In-skill steps** — ordered actions, the primary tier
2. **In-skill reference** — definitions, rules, facts, consulted on demand
3. **Disclosed reference** — content in a separate file, reached by a **context pointer**

Keep the top legible; push down whatever you can.

### Context Pointer

A reference in the agent's context that names out-of-context material and encodes the condition for reaching it. Its _wording_, not its target, decides when the agent reaches — and how reliably. A must-have target behind a weakly worded pointer is a variance bug: fix the wording first.

### Context Load

The cost a **model-invoked** skill imposes on the agent's context window — its **description**, always loaded, spending both tokens and attention. What **user-invoked** skills escape.

### Cognitive Load

The cost a **user-invoked** skill imposes on the human — the skills they must remember exist and when to reach for each. Not a cost to minimise unconditionally: it is the price of human agency.

### Progressive Disclosure

Moving **reference** down the ladder — out of `SKILL.md` and behind a **context pointer** — so the top stays legible. Licensed by **branching**: disclose what only some branches need, inline what every path needs.

### Co-location

Keeping material the agent needs at once in one place — a concept's definition, rules, and caveats under a single heading. The within-file companion to the **information hierarchy**.

## Skill Structure

### Branch

A distinct way a skill can be invoked — different runs taking different paths through it. A skill with many steps may carry many branches; a linear one has none.

### Steps

The ordered actions the agent performs. Every step ends on a **completion criterion**. Not every skill has steps: a skill can be all steps, all **reference**, or both.

### Completion Criterion

The condition that tells the agent a unit of work is done. Two properties matter: _clarity_ (can the agent tell done from not-done?) resists **premature completion**; _demand_ (how much it requires) sets **legwork**. The strongest criteria are both checkable and exhaustive.

### Legwork

The work an agent does within a single step — reading files, exploring the codebase, digging up what it needs rather than offloading to the user. Controlled by **completion criteria** demand and **leading words**, never written as its own step.

### Reference

Material the agent refers to on demand — definitions, facts, parameters, examples, conditional instructions. The prime candidate for **progressive disclosure**.

## Invocation

### Model-Invoked

A skill that keeps its **description**, so the agent fires it autonomously. Pays permanent **context load** in exchange for discoverability. Reachable by other skills.

### User-Invoked

A skill with its **description** stripped — reachable only by the human typing its name. Zero **context load**, but pays **cognitive load**.

### Router Skill

A **user-invoked** skill that points at other user-invoked skills — naming each and when to reach for it. The cure for **cognitive load** when user-invoked skills multiply.

### Granularity

How finely you divide skills. Finer division spends one of the two loads. Two cuts guide the division: by **invocation** (split off a model-invoked skill with a distinct **leading word**) and by **sequence** (split steps where later steps tempt the agent to rush).

## Failure Modes

### Premature Completion

Ending a step before it's genuinely done, because the agent's attention slips to _being done_. A between-steps failure: visible later steps pull the agent forward, the **completion criterion** clarity resists. Defence: sharpen the criterion first; only if irreducibly fuzzy _and_ you observe the rush, hide later steps by splitting.

### Duplication

The same meaning in more than one place. Costs maintenance, tokens, and inflates prominence past real rank. The accidental inverse of a **leading word**, which raises attention on purpose.

### Sediment

Stale layers that settle because adding feels safe and removing feels risky. The default fate of any skill without a pruning discipline.

### Sprawl

A skill simply too long, even when every line is live. The cure is the **information hierarchy**: disclose reference behind pointers, split by branch or sequence.

### No-Op

An instruction that changes nothing because the model already does it by default. The test: does this line change behaviour versus the default? A **leading word** too weak to beat the default is a no-op; the fix is a stronger word, not more prose.
