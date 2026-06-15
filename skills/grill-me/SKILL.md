---
name: grill-me
description: Stress-test a plan, design, or architecture by conducting a relentless structured interview. Leverages review perspectives for systematic dimension coverage and explores the codebase to ask sharper questions. Use when a user wants to pressure-test an idea, get grilled on a design, or mentions "grill me".
---

# Grill Me

A structured interview skill that stress-tests a plan, design, or architecture decision by walking every branch of the decision tree, one question at a time.

## When to Use

- The user wants to pressure-test a plan, feature design, or architecture proposal.
- The user says "grill me", "challenge my design", "poke holes in this", or similar.
- A team wants to run a lightweight design review before committing to implementation.

## Arguments

- `$ARGUMENTS` — The plan, design, feature spec, RFC, or topic to grill. Can be free-form text, a file path, a PR description, or a link to an issue.

---

## Workflow

### Step 1: Understand the Subject

1. **Parse the input.** Determine what the user wants grilled:
   - A plan or proposal described inline
   - A file or document in the codebase (read it)
   - A PR description or issue link (fetch it)
   - A verbal idea the user just described

2. **Identify the scope.**
   - What decisions are being proposed?
   - What is explicitly out of scope?
   - What assumptions are being made?

3. **Restate the plan back to the user** in 2–3 sentences to confirm understanding before proceeding. Ask the user to correct any misunderstanding.

### Step 2: Determine Context

If a codebase is available, scan it to gather context that sharpens your questions.

1. **Explore the project structure.** Understand the language(s), framework(s), directory layout, and organizational patterns.
2. **Find project conventions.** Read `AGENTS.md`, `CONTRIBUTING.md`, `Makefile`, or equivalent files to understand how the project works. Do not hardcode any specific commands or targets.
3. **Locate relevant existing code.** Find the modules, packages, or components most related to the plan. Read them to understand current patterns and constraints.
4. **Map dependencies and integration points.** Identify what the plan touches, what depends on those areas, and where integration risks live.

> **Key principle:** If a question can be answered by exploring the codebase, explore the codebase instead of asking the user. Present your findings and ask the user to confirm or correct.

### Step 3: Select Grilling Dimensions

Read the review perspectives in [../review-engine/review-perspectives.md](../review-engine/review-perspectives.md) and select the dimensions most relevant to the user's plan.

**Always include:**
- **Security** — every plan has a security surface
- **Performance** — every plan has performance implications

**Include when relevant:**
- **Go / Python / Frontend** — if the plan involves code in that language
- **API** — if the plan involves endpoints, contracts, or external interfaces
- **Database** — if the plan touches data models, migrations, or queries
- **Kubernetes** — if the plan involves controllers, operators, CRDs, or cluster resources
- **Linux Systems** — if the plan involves sysfs, netlink, namespaces, or low-level system calls
- **Test** — if the plan changes testing strategy or test infrastructure
- **Dockerfile** — if the plan involves container image changes
- **Dependency** — if the plan introduces or removes dependencies
- **Integration & E2E Test** — if the plan spans multiple services or layers

**Additionally, always consider these cross-cutting concerns:**
- **Backwards compatibility** — will this break existing users or APIs?
- **Operational readiness** — how will this be deployed, monitored, rolled back?
- **Failure modes** — what happens when things go wrong?
- **Scalability** — does this approach hold at 10x or 100x scale?

Tell the user which dimensions you selected and why before starting questions.

### Step 4: Conduct the Interview

Walk through each selected dimension systematically. For **each question**:

1. **State the dimension** you are exploring (e.g., "Security", "API Design", "Failure Modes").
2. **Ask exactly one question.** Be specific, not vague. Reference concrete code, components, or scenarios you discovered in Step 2.
3. **Provide your recommended answer.** Based on your codebase exploration and domain knowledge, state what you think the best answer is.
4. **Wait for the user to respond** before moving to the next question. Do not batch questions.
5. **Follow up** if the answer reveals a new concern or an unresolved dependency. Pursue each branch to its conclusion before moving to the next dimension.

**Interview style:**
- Be relentless but constructive. The goal is to uncover blind spots, not to be adversarial.
- Prioritize questions that expose real risks: data loss, security holes, breaking changes, scalability cliffs, operational gaps.
- If the user's answer is vague, push for specifics. "How exactly?" and "What happens when that fails?" are your best tools.
- If you discover a genuine gap in the plan, flag it clearly and suggest a concrete resolution.

### Step 5: Cross-Cutting Analysis

After finishing the dimension-specific questions, perform these cross-cutting checks:

1. **Trace user flows end-to-end.** Walk through 3–5 realistic scenarios using the proposed design. At each step, ask: What is null or undefined? What happens if step N has not completed when step N+1 starts?

2. **Audit state assumptions.** When the plan reads existing state: When is this state set? Can the new code execute before it is set? What are the race windows?

3. **Check first-use and edge scenarios.** What if this is the first time? What if the resource does not exist yet? What if the system is mid-migration or mid-upgrade?

4. **Follow data across boundaries.** When the plan involves multiple components communicating (frontend/backend, service-to-service, controller-to-API), trace what data is available at each boundary and what format it is in.

5. **Distinguish correctness from integration correctness.** A function can be correct in isolation but wrong in context. Check the call sites, not just the function.

Present any issues found as questions, one at a time, following the same interview pattern as Step 4.

### Step 6: Summary

After all questions are resolved, produce a final summary:

```text
## Grill Session Summary

### Decisions Made
- {numbered list of decisions reached during the session}

### Open Items
- {numbered list of questions that remain unresolved or need further investigation}

### Risks Identified
- {numbered list of risks surfaced, with severity: critical / high / medium / low}

### Recommendations
- {numbered list of concrete next steps or changes to the plan}
```

If the user asks to save the summary, write it to a file. Otherwise, present it inline.

---

## Guidelines

- **One question at a time.** Never batch questions. Wait for the user's response before proceeding.
- **Codebase first.** If a question can be answered by reading code, read the code and present findings instead of asking.
- **Be specific.** Reference concrete files, functions, components, and scenarios. Vague questions get vague answers.
- **Provide recommended answers.** For every question, state what you think the answer should be. This gives the user something to react to.
- **Be relentless but constructive.** The goal is to make the plan better, not to prove it wrong.
- **Follow branches to their conclusion.** Do not move to the next dimension until the current branch is resolved.
- **No hardcoded commands.** When exploring a codebase, discover build, test, and lint commands by reading project files — never assume specific targets.
- **Security and performance are non-negotiable.** Always include these dimensions regardless of the plan's subject.
- **Cross-cutting checks catch the hardest bugs.** The most dangerous issues live at integration boundaries and in state assumptions.
