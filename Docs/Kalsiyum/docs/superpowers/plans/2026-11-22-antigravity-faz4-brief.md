# Antigravity — Faz 4 brief (paste entire block)

Copy everything inside the fenced block into a **new** Antigravity chat.  
Only start after `[HU]` PIE confirms Faz 3 (block / limb drop / arm-gated attacks).

```
UE root: D:\Project Cal\Project_Calcium
Docs root: D:\Project Cal\Docs\Kalsiyum
CLI tip: C:\kalsiyum_ue junction; scripts in paths WITHOUT spaces.

Read first: ANTIGRAVITY.md, docs/SCOPE.md, AGENT_HANDOFF.md, docs/WORKFLOW.md (Faz 4)

You own scaffolding only. Do not polish combat feel / hit-stop / montages (Cursor).
Do not write story. Do not start Faz 5 (mood/flame).

## Do not break

- AC_MeleeCombat attack chains (HasRightArm gate + slot anim + PerformMeleeTrace_0)
- AC_LimbSocket SetBlocking_0 / DropRightArm / ReattachRightArm / HasRightArm
- AC_BoneDensity ApplyBoneDamage
- Faz 1 SpringArm + IA_Interact LineTrace
- Character Event Graph: keep THIN

## Deliver (Faz 4 scaffold)

1) DataAssets:
   - DA_Limb_VikingArm: higher damage multiplier, slower attack speed
   - DA_Limb_NinjaArm: lower damage, faster attack speed
   - Hardcoded floats OK; document defaults in handoff

2) AC_LimbSocket (or thin new AC_LimbEquip):
   - EquippedLimb DA reference (nullable)
   - When right arm attached + DA set → expose GetDamageMult / GetAttackSpeedMult for melee to read later [CU]
   - On DropRightArm clear equipped DA; on Reattach keep last DA or default Viking

3) PIE smoke:
   - Print which DA is equipped
   - Optional: swap DA via debug key (document) OR Details default only

4) Update AGENT_HANDOFF.md How to test; stop. No mesh swap polish (Cursor). No Faz 5.

## Out of scope

Mesh visual swap, attack-set redesign, mood/flame, campfire, story.
```
