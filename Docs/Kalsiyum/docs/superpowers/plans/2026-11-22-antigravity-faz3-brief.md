# Antigravity — Faz 3 brief (paste entire block)

Parallel session: Cursor `[CU]` owns **attack/dodge animation feel** on `AC_MeleeCombat` (Approach A).  
You own **Faz 3 scaffold only** (Approach C / Bone Density + risky block + limb drop).  
**Do not both edit the same Event Graph.**

Copy everything inside the fenced block below into a **new** Antigravity chat.

```
UE root: D:\Project Cal\Project_Calcium
Docs root: D:\Project Cal\Docs\Kalsiyum
CLI tip (spaces): junction C:\kalsiyum_ue -> Project_Calcium; put Python scripts under a path WITHOUT spaces.

Read first: ANTIGRAVITY.md, docs/SCOPE.md, AGENT_HANDOFF.md, docs/WORKFLOW.md (Faz 3)

You own scaffolding only. Do not polish attack montages, hit-stop, startup timing, or dodge feel (Cursor [CU] owns that NOW in parallel).
Do not write story. Do not start Faz 4 (DA_Limb_Viking/Ninja).

## PARALLEL LOCK (hard)

- DO NOT edit AC_MeleeCombat TriggerLightAttack / TriggerHeavyAttack / PerformMeleeTrace* / PlayAnim* / hit-stop chains.
- DO NOT retune Combat|Tuning attack vars (LightStartup, HitStop*, CameraPunchZ, montages).
- DO NOT break Faz 1 SpringArm / IA_Interact LineTrace.
- Character BP_TP_Kalsiyum Event Graph: keep THIN — only wire new inputs to NEW components.
- Prefer NEW assets: AC_BoneDensity, AC_LimbSocket (or AC_BlockStress), BP_DetachedLimb. Touch AC_MeleeCombat only if you must add a single safe hook (e.g. read bIsInvulnerable) — prefer events/interfaces over rewriting attack graphs.

## Already done (do not redo / do not break)

- BP_TP_Kalsiyum default pawn; IMC_Default with Interact/Sprint/Light/Heavy/Dodge/LockOn
- AC_MeleeCombat: light/heavy SphereTrace + dodge + lock-on; CU is adding visible attack anim via Play Slot Dynamic Montage
- BP_EnemyDummy in Lvl_ThirdPerson (BP_EnemyDummy_Faz2) — keep for combat tests
- Faz 1 CU SpringArm: Arm=300, Offset=(0,50,60), Lag 9/10, Probe=12

## Deliver (Faz 3 scaffold only)

1) Bone Density (= health for v0.1)
   - New component OR player attribute on a NEW component (prefer AC_BoneDensity on BP_TP_Kalsiyum).
   - Float CurrentBoneDensity / MaxBoneDensity (defaults e.g. 100).
   - Take damage reduces Bone Density (hook AnyDamage on character OR forward from existing damage path WITHOUT rewriting melee traces).
   - Print on change: [Kalsiyum] BoneDensity: X — enough for PIE smoke.
   - Optional stub UI later [CU]; PrintString OK now.

2) Risky block (no perfect block)
   - New input IA_Block on IMC_Default (e.g. Q or Mouse4 — do NOT steal LMB/RMB/E/Shift/LCtrl/Tab/MMB). Document key in handoff.
   - Hold/toggle stub on NEW component (AC_BlockStress or inside AC_LimbSocket): while blocking, incoming damage reduced OR converted partly to JointStress.
   - JointStress float accumulates on blocked hits; when JointStress >= threshold → trigger limb break (below).
   - NO i-frame during block. NO perfect-parry window.

3) Limb drop (one arm for smoke)
   - AC_LimbSocket (or equivalent): tracks bHasRightArm (bool) default true.
   - On break: set bHasRightArm=false, spawn BP_DetachedLimb (simple static/skeletal mesh actor) at hand/shoulder socket or actor location + impulse stub, reset/clear JointStress.
   - Print: [Kalsiyum] Limb DROPPED (RightArm).
   - Attack gating stub ONLY via a bool/query the melee side can read later — do NOT delete TriggerLight/Heavy. Example: expose bHasRightArm; optional soft print if attack pressed without arm. Full attack-set restrict is [CU].

4) Pick up / reattach stub
   - BP_DetachedLimb: overlap or Interact (E) from player when close → destroy limb actor, set bHasRightArm=true, print [Kalsiyum] Limb REATTACHED.
   - Keep Character Interact graph intact; prefer limb actor overlap+key OR a small function on AC_LimbSocket called from a thin character forwarder. Do not gut Faz 1 LineTrace Interact.

5) Update Docs/Kalsiyum/AGENT_HANDOFF.md
   - Current focus: Faz 3 [AG] done items + note parallel CU anim pass
   - Exact asset names + IA_Block key
   - How to test PIE (block → stress → arm drops → pick up)
6) Stop. Do not start Faz 4 DataAssets. Leave one-line TODOs for [CU]: missing-arm attack restrict, bone density HUD bar, block feel.

## Out of scope

Attack montage / dynamic slot fix, hit-stop retune, dodge i-frame numbers, Viking/Ninja DA_Limb_*, mood/flame, campfire, story, camera polish.

## Finish line

Compile clean. PIE: take hits → BoneDensity prints down; hold block → JointStress rises → arm drops and spawns BP_DetachedLimb; walk to limb + reattach works. Then update handoff and stop.
```
