# Faz 0 closeout + Faz 1 AG kickoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Point all Kalsiyum docs at `D:\Project Cal\Project_Calcium`, close Faz 0, and produce a paste-ready Antigravity Faz 1 scaffold brief.

**Architecture:** Docs-only Cursor pass first (path truth + handoff). Antigravity later executes UE Blueprint work from the brief; this plan does not edit `.uasset` files.

**Tech Stack:** Markdown docs in `Docs/Kalsiyum`; Unreal Engine 5.8 project at `Project_Calcium` (stock Third Person template already present).

**Spec:** `Docs/Kalsiyum/docs/superpowers/specs/2026-11-22-faz0-closeout-faz1-ag-kickoff-design.md`

## Global Constraints

- Only UE root: `D:\Project Cal\Project_Calcium` (never create a second project under `ue-project/`)
- Naming from SCOPE: `BP_TP_Kalsiyum`, third person, no story
- Dual-AI: AG scaffolds Faz 1; Cursor polish is later — do not both own the same BP event graph
- No combat / limbs / mood / campfire in this kickoff
- Chat is not memory — handoff + prompts must be self-contained

## Review Focus

- An agent opens `Docs/Kalsiyum/ue-project/` looking for `.uproject` → must find a clear pointer to `Project_Calcium` instead
- AG brief still says `ue-project` → must say `Project_Calcium` + existing asset names
- Handoff Current focus still Faz 0 after closeout → must be Faz 1 `[AG]`
- README still tells human to create a new TP project → must say project already exists at path
- Workspace wording implies docs folder is the UE root → must distinguish docs root vs UE root

## File map

| File | Responsibility |
|------|----------------|
| `Docs/Kalsiyum/AGENT_HANDOFF.md` | Current focus Faz 1 `[AG]`; Faz 0 → Done; owners; how to test placeholder for AG |
| `Docs/Kalsiyum/docs/WORKFLOW.md` | Faz 0 checked done; path text → `Project_Calcium` |
| `Docs/Kalsiyum/ue-project/README.md` | Redirect: real project lives at `../../Project_Calcium` |
| `Docs/Kalsiyum/README.md` | Layout table + quick start paths |
| `Docs/Kalsiyum/docs/ANTIGRAVITY_PROMPTS.md` | Faz 1 prompt uses real path + stock asset names |
| `Docs/Kalsiyum/docs/CURSOR_PROMPTS.md` | Path refs if any say `ue-project` for UE |
| `Docs/Kalsiyum/AGENTS.md` | Confirm UE path line if missing |
| `Docs/Kalsiyum/docs/superpowers/plans/...-ag-brief.md` **or** section in prompts | Paste-ready AG brief (also mirrored into ANTIGRAVITY_PROMPTS) |

---

### Task 1: Path truth in README + ue-project stub

**Files:**
- Modify: `Docs/Kalsiyum/README.md`
- Modify: `Docs/Kalsiyum/ue-project/README.md`
- Modify: `Docs/Kalsiyum/AGENTS.md` (add one line UE root if absent)

**Interfaces:**
- Consumes: Spec locked path `D:\Project Cal\Project_Calcium`
- Produces: Humans/agents reading README never instructed to New Project into `ue-project/`

- [ ] **Step 1: Verification that fails today**

Run (PowerShell from `D:\Project Cal`):

```powershell
Select-String -Path "Docs\Kalsiyum\README.md","Docs\Kalsiyum\ue-project\README.md" -Pattern "Project_Calcium" -SimpleMatch
```

Expected: no matches (or incomplete) — proves path truth missing.

- [ ] **Step 2: Update `ue-project/README.md`**

Replace create-here instructions with: do **not** create a project here; real `.uproject` is `D:\Project Cal\Project_Calcium\Project_Calcium.uproject`; this folder is legacy docs stub only.

- [ ] **Step 3: Update `Docs/Kalsiyum/README.md`**

Table/quick start: UE project = `../Project_Calcium` (sibling of `Docs`), not `ue-project/`. Keep docs folder purpose clear.

- [ ] **Step 4: `AGENTS.md` one-liner**

Add: Unreal root = `D:\Project Cal\Project_Calcium`.

- [ ] **Step 5: Re-run search**

```powershell
Select-String -Path "Docs\Kalsiyum\README.md","Docs\Kalsiyum\ue-project\README.md","Docs\Kalsiyum\AGENTS.md" -Pattern "Project_Calcium" -SimpleMatch
```

Expected: each file has ≥1 hit; `ue-project/README.md` contains “do not create” / redirect language.

---

### Task 2: Close Faz 0 in handoff + WORKFLOW

**Files:**
- Modify: `Docs/Kalsiyum/AGENT_HANDOFF.md`
- Modify: `Docs/Kalsiyum/docs/WORKFLOW.md`

**Interfaces:**
- Consumes: Task 1 path wording
- Produces: Current focus = Faz 1 `[AG]`; Faz 0 items in Done

- [ ] **Step 1: Update `AGENT_HANDOFF.md`**

- Current focus → **Faz 1 — TP hareket + kamera iskeleti** `[AG]`
- Checklist: character toward `BP_TP_Kalsiyum`; IMC Interact (+ optional Sprint); SpringArm baseline; no combat
- Move Faz 0 bullets to Done (project exists at `Project_Calcium`, stock TP present)
- Blocked: clear “UE yok” / set “awaiting AG Faz 1 PIE notes”
- How to test: leave stub for AG to fill after PIE
- Notes: Cursor owns polish after AG; do not both edit same BP graph

- [ ] **Step 2: Update `docs/WORKFLOW.md` Faz 0**

Mark Faz 0 checkboxes done; replace `ue-project/` with `Project_Calcium` in Faz 0 and any “Workspace: … ue-project” lines (~line 159).

- [ ] **Step 3: Verify**

```powershell
Select-String -Path "Docs\Kalsiyum\AGENT_HANDOFF.md" -Pattern "Faz 1" | Select-Object -First 5
Select-String -Path "Docs\Kalsiyum\docs\WORKFLOW.md" -Pattern "ue-project"
```

Expected: handoff shows Faz 1 as current; WORKFLOW has no unchecked Faz 0 create-ue-project instruction (redirect/done only).

---

### Task 3: Antigravity paste brief + prompt refresh

**Files:**
- Modify: `Docs/Kalsiyum/docs/ANTIGRAVITY_PROMPTS.md` (Faz 1 section)
- Modify: `Docs/Kalsiyum/docs/CURSOR_PROMPTS.md` (path refs if present)
- Create: `Docs/Kalsiyum/docs/superpowers/plans/2026-11-22-antigravity-faz1-brief.md` (single paste block)

**Interfaces:**
- Consumes: Handoff Faz 1 focus; stock assets under `Content/ThirdPerson`, `Content/Input`
- Produces: One markdown file the human can copy entirely into Antigravity

- [ ] **Step 1: Write `2026-11-22-antigravity-faz1-brief.md`**

Must include verbatim:

- Workspace / UE root: `D:\Project Cal\Project_Calcium`
- Also open/read docs: `D:\Project Cal\Docs\Kalsiyum` (`ANTIGRAVITY.md`, `SCOPE`, `AGENT_HANDOFF`, `WORKFLOW`)
- Existing assets: `BP_ThirdPersonCharacter`, `BP_ThirdPersonGameMode`, `BP_ThirdPersonPlayerController`, `IMC_Default`, `IA_Move`/`IA_Look`/`IA_Jump`, `Lvl_ThirdPerson`
- Goals: path to `BP_TP_Kalsiyum`; add Interact (+ optional Sprint); SpringArm baseline; document IMC names in handoff
- Out of scope: combat, polish camera lag, story
- Finish: update `AGENT_HANDOFF.md` How to test; do not start Faz 2

- [ ] **Step 2: Replace Faz 1 block in `ANTIGRAVITY_PROMPTS.md`**

Same facts as the brief; remove `In ue-project:` wording.

- [ ] **Step 3: Fix `CURSOR_PROMPTS.md` path strings if they cite `ue-project` as UE root**

- [ ] **Step 4: Verify**

```powershell
Select-String -Path "Docs\Kalsiyum\docs\ANTIGRAVITY_PROMPTS.md","Docs\Kalsiyum\docs\superpowers\plans\2026-11-22-antigravity-faz1-brief.md" -Pattern "Project_Calcium","BP_TP_Kalsiyum","ue-project"
```

Expected: `Project_Calcium` + `BP_TP_Kalsiyum` present; no instruction to create project in `ue-project`.

---

### Task 4: Human handoff checklist (no code)

**Files:** none required (optional note in handoff Notes)

- [ ] **Step 1: List for the human (write into chat when executing)**

1. Open `D:\Project Cal\Project_Calcium` in Antigravity (UE project)
2. Keep `Docs\Kalsiyum` readable (same machine path)
3. Paste contents of `docs/superpowers/plans/2026-11-22-antigravity-faz1-brief.md`
4. After AG done: Cursor does camera/interact polish `[CU]`

- [ ] **Step 2: Done criteria**

All Task 1–3 verifies pass; brief file exists and is paste-ready.
