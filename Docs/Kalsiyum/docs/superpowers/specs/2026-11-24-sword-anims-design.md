# Design: Sword combat animations (1→3→2)

Date: 2026-11-24  
Status: approved — implementing via `Content/Python/faz_sword_plan_123.py` (1→3→2 + scale/grip)

Note: KinemIQ sword FBX uses foreign skeleton; v1 uses mannequin melee duplicates as `AS_Sword_*` (compatible with Approach A). Real FBX retarget = follow-up.

## Intent

Replace unarmed attack clips with sword-looking swings; then limb-specific sets; then keep/enrich unarmed as fallback. Fix hand grip offset so the blade sits in the palm.

## Order

1. **Import sword clips** (CC0) → retarget to mannequin → wire light/heavy on `AC_MeleeCombat` + grip polish  
2. **Limb sets** — Ninja fast/light clips; Viking heavy/slow; swap with `R`  
3. **Unarmed enrich** — `MM_Attack_02/03` as fallback when arm detached / no weapon  

## Non-goals

- Full AnimBP combat state machine rewrite  
- Root-motion locomotion combat  
- Custom authored mocap  

## Constraints

- Keep Approach A: `PlaySlotAnimationAsDynamicMontage`  
- Do not break SpringArm / blade `NoCollision` / arm gate  
- PIE-safe scripts; user runs `py` (no unsolicited desktop control)  
