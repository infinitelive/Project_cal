# Antigravity — Faz 2 brief (paste entire block)

Copy everything inside the fenced block below into a new Antigravity chat.

```
UE root: D:\Project Cal\Project_Calcium
Docs root: D:\Project Cal\Docs\Kalsiyum
CLI tip (spaces): junction C:\kalsiyum_ue -> Project_Calcium; put Python scripts under a path WITHOUT spaces.

Read first: ANTIGRAVITY.md, docs/SCOPE.md, AGENT_HANDOFF.md, docs/WORKFLOW.md (Faz 2)

You own scaffolding only. Do not polish attack timing, i-frames, or hit-stop (Cursor [CU] after).
Do not write story. Do not start Faz 3 (bone density / limb drop).

## Already done (do not redo / do not break)

- BP_TP_Kalsiyum (child of BP_ThirdPersonCharacter) is default pawn
- IMC_Default: Move/Look/Jump + IA_Interact (E) + IA_Sprint (LeftShift)
- SpringArm CU polish: Arm=300, Offset=(0,50,60), CameraLag=9, RotLag=10, Probe=12
- IA_Interact already does LineTrace 250uu — keep it; combat is separate inputs
- Human PIE confirmed: walk/camera/walls OK; Interact print works

## Deliver (Faz 2 scaffold only)

1. Input: add IA_LightAttack, IA_HeavyAttack, IA_Dodge on IMC_Default (sensible keys; document in handoff). Mouse LMB / RMB / Ctrl or Space-adjacent — pick idiomatic; don't steal E/Shift.
2. BP_EnemyDummy in /Game/ (or ThirdPerson/Blueprints): simple mesh, health (float or int), take-damage function, die/despawn or ragdoll stub. Place one in Lvl_ThirdPerson for PIE.
3. On BP_TP_Kalsiyum OR new AC_MeleeCombat component (prefer component — keep Character Event Graph thin):
   - Light / Heavy attack stubs (timer windows OR placeholder montages — OK)
   - Weapon trace OR short forward capsule/line during active window that damages Dummy
   - Dodge stub (impulse or root motion placeholder + brief i-frame bool — DO NOT tune duration)
4. Lock-on stub: find nearest BP_EnemyDummy in radius; soft face / camera hint only — polish later [CU].
5. Update Docs/Kalsiyum/AGENT_HANDOFF.md:
   - Current focus → Faz 2 [AG] checklist done items
   - Exact asset names (IMC/IA, AC_*, BP_EnemyDummy path)
   - How to test PIE steps (spawn, hit dummy to 0 HP, dodge key fires)
6. Stop. Do not start Faz 3. Leave TODO one-liners for Cursor timing polish.

## Out of scope

Bone Density, block stress, limb drop, mood/flame, campfire, story, camera feel retune, hit-stop tuning.

## Finish line

Compile clean. PIE: can kill Dummy with light/heavy stubs; dodge input does something visible. Then update handoff and stop.
```
