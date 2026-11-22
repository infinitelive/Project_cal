# Antigravity — Faz 1 brief (paste entire block)

Copy everything inside the fenced block below into a new Antigravity chat.

```
UE root: D:\Project Cal\Project_Calcium
Docs root: D:\Project Cal\Docs\Kalsiyum

Read first (docs): ANTIGRAVITY.md, docs/SCOPE.md, AGENT_HANDOFF.md, docs/WORKFLOW.md
Optional map: D:\Project Cal\graphify-out\GRAPH_REPORT.md

You own scaffolding only. Do not write story. Do not polish mouse/camera feel (Cursor does that after).
Single goal: AGENT_HANDOFF Current focus — Faz 1 [AG].

## Already in the project (stock Third Person)

- Map: Content/ThirdPerson/Lvl_ThirdPerson.umap
- Character: Content/ThirdPerson/Blueprints/BP_ThirdPersonCharacter
- GameMode: Content/ThirdPerson/Blueprints/BP_ThirdPersonGameMode
- PlayerController: Content/ThirdPerson/Blueprints/BP_ThirdPersonPlayerController
- Input: Content/Input/IMC_Default + IA_Move, IA_Look, IA_Jump

Do NOT create a second Unreal project under Docs/Kalsiyum/ue-project/.

## Deliver (Faz 1 scaffold only)

1. Character path toward BP_TP_Kalsiyum (duplicate / rename / child of BP_ThirdPersonCharacter — pick idiomatic UE; keep GameMode default pawn wired).
2. Enhanced Input: keep Move / Look / Jump; add Interact (+ optional Sprint) to IMC; create IA assets if missing.
3. SpringArm + follow camera baseline on the character (readable over-shoulder; not glued to the mesh).
4. Update Docs/Kalsiyum/AGENT_HANDOFF.md:
   - list exact IMC / IA asset names
   - How to test: PIE steps (walk, orbit camera, Interact key fires even if Interact is a stub)
   - Owner table: Character BP notes
5. Stop. Do not start Faz 2 (combat / dummy / lock-on).

## Out of scope

Combat, limbs, mood/flame, campfire, story, camera lag polish, hit-stop, Niagara.

## Finish line

When PIE smoke works: update AGENT_HANDOFF.md, mark Faz 1 AG checklist items done that you finished, leave [CU] polish for Cursor. Do not start the next phase.
```
