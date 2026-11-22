# Antigravity — hazır promptlar

Her görevin başına `ANTIGRAVITY.md` + handoff okut.

## Oturum açılışı

```
UE root: D:\Project Cal\Project_Calcium
Docs: D:\Project Cal\Docs\Kalsiyum
Read: ANTIGRAVITY.md, docs/SCOPE.md, AGENT_HANDOFF.md, docs/WORKFLOW.md
You own scaffolding. Do not write story. Do not polish mouse feel.
Single goal from AGENT_HANDOFF Current focus [AG].
When done: update AGENT_HANDOFF.md with How to test.
```

## Faz 1 (current) — full paste

Prefer the dedicated file (copy whole fenced block):

`docs/superpowers/plans/2026-11-22-antigravity-faz1-brief.md`

Short form:

```
UE root: D:\Project Cal\Project_Calcium
Stock TP already present (BP_ThirdPersonCharacter, IMC_Default, Lvl_ThirdPerson).
Path toward BP_TP_Kalsiyum; add Interact (+ optional Sprint); SpringArm baseline.
Document IMC/IA names + PIE steps in AGENT_HANDOFF. No combat. Do not use ue-project/ for a new .uproject.
```
## Faz 2 (current) — full paste

Prefer: `docs/superpowers/plans/2026-11-22-antigravity-faz2-brief.md`

Short form:

```
UE root: D:\Project Cal\Project_Calcium
Faz 1 done (PIE OK). Create BP_EnemyDummy + health.
IA_LightAttack / IA_HeavyAttack / IA_Dodge. Prefer AC_MeleeCombat on BP_TP_Kalsiyum.
Weapon trace stub + lock-on nearest dummy. Do not tune feel — Cursor later. No Faz 3.
Update AGENT_HANDOFF with PIE steps; stop.
```

## Faz 3 — limb drop (current parallel)

Prefer the dedicated file (copy whole fenced block):

`docs/superpowers/plans/2026-11-22-antigravity-faz3-brief.md`

**Parallel:** Cursor owns `AC_MeleeCombat` attack anim (Approach A). AG must NOT edit light/heavy/trace/hit-stop chains.

Short form:

```
UE root: D:\Project Cal\Project_Calcium
Faz 3 scaffold: AC_BoneDensity + risky block (IA_Block) + JointStress → limb drop + BP_DetachedLimb reattach.
NEW components only. Do not edit AC_MeleeCombat attack graphs (CU parallel).
Update AGENT_HANDOFF How to test; stop before Faz 4.
```

## Faz 4 — two limbs

```
DA_Limb_VikingArm and DA_Limb_NinjaArm: damage, attack speed multipliers.
Socket applies DA when attached. Placeholder meshes fine.
```

## Faz 5 — mood

```
AC_MoodFlame: enum Blue/Red/Green, apply modifiers to movement/damage/crit.
Simple triggers. Expose color for Niagara. No gold mood.
```

## Faz 6 — campfire

```
BP_Campfire interact → rest: save player transform, bone density, limbs, mood.
On death load last camp. Persistent world — no run wipe.
Minimal rest menu widget OK.
```

## Bitirme cümlesi (zorunlu)

```
Update AGENT_HANDOFF.md. List exact PIE steps. Mark owner table. Do not start next phase.
```
