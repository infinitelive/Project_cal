# Design: Faz 0 closeout + Faz 1 Antigravity kickoff

Date: 2026-11-22  
Status: approved

## Intent / why

Agents must share one real Unreal root and a clear next owner. Docs still point at empty `ue-project/`; the playable project already lives at `D:\Project Cal\Project_Calcium`. Closing that gap unblocks dual-AI work without a second template.

## Goals

1. Treat `Project_Calcium` as the only UE project path in Kalsiyum docs/handoff.
2. Mark Faz 0 done once path + open-both-IDEs notes are correct.
3. Hand Antigravity a paste-ready **Faz 1 scaffold** brief (input/camera/character naming), Cursor polish later.

## Non-goals

- Combat, limbs, mood, campfire, story (Faz 2+)
- Rewriting the whole Third Person template from scratch
- Cursor polish of camera feel in this kickoff (that stays `[CU]` after AG)

## Anti-goals

- Two agents editing the same Blueprint event graph in one session
- Creating a second project under `ue-project/`
- Perfect block / FPS / roguelite scope creep

## Constraints

- UE5, PC, third person only; naming from `docs/SCOPE.md`
- Blueprint-first is fine for v0.1
- Source of truth: Git + `Docs/Kalsiyum` files; chat is not memory
- Graph map exists at `D:\Project Cal\graphify-out\` (optional AG consult)

## Approaches considered

| | Approach | Tradeoff |
|---|----------|----------|
| **A (picked)** | Docs hizala → AG Faz 1 brief | 10 dk docs first; agents stay aligned |
| B | AG immediately, docs later | Faster start; wrong-path risk |
| C | Inventory spike then scaffold | Safer but redundant — template already clear |

**Picked: A** — user confirmed.

## How (builder-facing)

### Cursor (this session, after plan approval)

- Update `AGENT_HANDOFF.md`, `docs/WORKFLOW.md`, `ue-project/README.md` (and any path refs) so root = `D:\Project Cal\Project_Calcium`
- Produce Antigravity paste brief for Faz 1
- Do **not** deep-edit character BPs here unless needed for docs accuracy

### Antigravity (next session)

Starting from stock TP assets already present:

- `Content/ThirdPerson/Blueprints/BP_ThirdPersonCharacter` (+ GameMode / PlayerController)
- `Content/Input/IMC_Default` + `IA_Move` / `IA_Look` / `IA_Jump`
- Map: `Lvl_ThirdPerson`

Deliver Faz 1 scaffold only:

1. Character path toward `BP_TP_Kalsiyum` (duplicate/rename/child — AG picks idiomatic UE; keep GameMode wired)
2. Enhanced Input: keep Move/Look/Jump; add **Interact** (+ optional Sprint) to IMC
3. SpringArm + follow camera baseline (readable over-shoulder; not glued)
4. Smoke notes in handoff: PIE walk, orbit camera, interact key fires (even if interact is stub)

Out of scope for AG this pass: camera lag polish, melee, lock-on feel (Cursor after).

## Left to the builder

- Exact duplicate vs rename vs child Blueprint
- Sprint yes/no (optional in WORKFLOW)
- Interact as line trace stub vs empty input binding

## Success

- Docs + handoff never send an agent to empty `ue-project/` for the `.uproject`
- AG can finish Faz 1 scaffold without asking “where is the project?”
- After AG: PIE walks; `[CU]` can polish camera/interact
