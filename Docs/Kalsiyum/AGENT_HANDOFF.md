# Agent Handoff

> Her oturum sonunda güncelle. Eski maddeleri silme; “Done” bölümüne taşı.

## Current focus

**PARALLEL (2026-11-22):** `[CU]` Approach A + `[AG]` Faz 3 (Approach C) aynı anda

UE root: `D:\Project Cal\Project_Calcium`

### `[AG]` Faz 3 — iskelet ✅ (tamam — `[HU]` PIE + `[CU]` polish sıradaki)
`docs/superpowers/plans/2026-11-22-antigravity-faz3-brief.md`

- [x] `AC_BoneDensity` (`/Game/ThirdPerson/Blueprints/AC_BoneDensity`: `CurrentBoneDensity`/`MaxBoneDensity=100`, `bIsShattered`, `ApplyBoneDamage` → `[Kalsiyum] BoneDensity: X`)
- [x] `IA_Block` (`Q`, hold: `Started`/`Completed`/`Canceled`) + `IA_TestHit` (`H`, PIE debug self-damage `25`) on `IMC_Default`; `AC_LimbSocket` (`/Game/ThirdPerson/Blueprints/AC_LimbSocket`: `bIsBlocking`, `JointStress`, `MaxJointStress=100`, `StressPerBlockedHit=35`, `BlockDamageMultiplier=0.3` — risky block, no i-frame, no perfect parry)
- [x] Limb break → `bHasRightArm=false` + `HasRightArm()` pure query hook, `BP_DetachedLimb` (`/Game/ThirdPerson/Blueprints/BP_DetachedLimb`, `SM_ChamferCube` physics + `PickupTrigger` sphere `R=120`, `0.6s` grace → walk-over overlap `ReattachRightArm` + destroy)
- [x] Handoff How to test + **stopped before Faz 4** (`AC_MeleeCombat` LOCK korundu, hiç dokunulmadı)

### `[CU]` Approach A — anim feel ✅
- [x] Root cause: `MM_Attack_*` = **AnimSequence** (not AnimMontage)
- [x] Fix: `GetPlayerCharacter` → `GetComponentByClass(SkeletalMesh)` → `GetAnimInstance` → `PlaySlotAnimationAsDynamicMontage` (`DefaultSlot`)
- [x] Timing: `LightStartup`/`HeavyStartup` → play slot → `LightActive=0.18` / `HeavyActive=0.28` → face → `PerformMeleeTrace_0` → hit-stop restore → CD
- [x] Headless: `DONE ALL CU ANIM VERIFICATIONS PASSED` (script `faz2_cu_anim_fix.py`)
- [ ] Dodge `MM_Dash` splice skipped (no safe pin-walk) — optional later

### `[CU]` Faz 3 polish ✅ (VERIFY CLEAN)
- [x] Attack gate: `HasRightArm` before light/heavy (no arm → print, no swing)
- [x] `IA_Block` → `SetBlocking_0` (UE rename quirk; function lives as `_0`)
- [x] HUD: `UI_BoneDensity` shell + keyed `PrintString` (`BoneDensityHUD`) on damage
- [ ] Block walk-speed slow skipped (CMC setter not exposed to Python) — print-only feel
- [ ] Full UMG progress bar later

### Shared do-not-break
- Faz 1 SpringArm `300 / (0,50,60) / Lag 9/10 / Probe 12`; `IA_Interact` LineTrace
- `BP_EnemyDummy_Faz2` PIE target

## Owner şimdi

| Alan | Owner |
|------|--------|
| Character BP | thin — `BP_TP_Kalsiyum` yeni input/AnyDamage forwarder’ları (`IA_Block`, `IA_TestHit`, `ReceiveAnyDamage`); `AC_MeleeCombat` dokunulmadı |
| Combat anim / hit-stop | `[CU]` (`AC_MeleeCombat` attack chains — Approach A ✅) |
| Bone density / block / limb | `[CU]` Faz 3 polish (`AC_BoneDensity`, `AC_LimbSocket`, `BP_DetachedLimb` iskeleti hazır) |
| Mood / Flame | — |
| Campfire | — |
| UI | — (BoneDensity HUD sonra `[CU]`) |

## Done

- [x] Kararlar kilitlendi (TP, tek hikâye, kamp CP, alaycı ton, PC, hikâye ertelendi)
- [x] Perspektif düzeltmesi: 1. şahıs → 3. şahıs
- [x] Çift AI workflow + SCOPE yazıldı
- [x] Faz 0 — `Project_Calcium` UE 5.8 stock TP
- [x] Docs path truth → `Project_Calcium`
- [x] Faz 1 `[AG]` iskelet: `BP_TP_Kalsiyum`, Interact/Sprint, SpringArm baseline
- [x] Faz 1 `[CU]` polish: Arm=300, lag 9/10, probe 12, Interact LineTrace
- [x] Faz 1 **[HU] PIE OK** (2026-11-22): oynanıyor; duvar collision OK; `E` → Interact print geliyor
- [x] Faz 2 `[AG]` iskelet: `IA_LightAttack`/`IA_HeavyAttack`/`IA_Dodge`/`IA_LockOn` on `IMC_Default`, `BP_EnemyDummy` (`Lvl_ThirdPerson` yerleşimli), `AC_MeleeCombat` (light/heavy SphereTrace + dodge stub + lock-on stub), sıfır hata derleme + soğuk yükleme doğrulaması
- [x] Faz 2 `[CU]` polish: startup→montage→trace, hit-stop + camera punch, CU tuning vars (`Combat|Tuning`); headless `DONE ALL CU VERIFICATIONS PASSED`
- [x] Faz 3 `[AG]` iskelet: `IA_Block (Q)` + `IA_TestHit (H)` on `IMC_Default`, `AC_BoneDensity`, `AC_LimbSocket` (risky block + `JointStress` + `DropRightArm`/`ReattachRightArm`/`HasRightArm`), `BP_DetachedLimb` (physics pop + overlap reattach), thin `BP_TP_Kalsiyum` wiring; sıfır hata derleme + soğuk yükleme doğrulaması

## Blocked / risks

- **Canlı PIE smoke** insan (`[HU]`) onayı bekliyor (hem `[CU]` Approach A anim hem `[AG]` Faz 3)
- İki AI aynı BP graph’a yazmasın
- CLI: `C:\kalsiyum_ue` junction; script path’lerinde boşluk yok
- `PerformMeleeTrace_0` adı garip ama derleniyor; yeniden adlandırma API’si no-op kaldı — elle rename edilebilir
- Dodge i-frame / AG damage-CD defaults Python’da değiştirilemedi (`set_blueprint_variable_default_value` yok)
- TODO `[CU]` (tek satır): eksik kolda (`AC_LimbSocket.HasRightArm() == false`) attack set kısıtı, `UI_BoneDensity` HUD barı, block hissi/anim + opsiyonel `E` tuşuyla uzuv toplama ve gerçek düşman saldırısı gelince `IA_TestHit (H)` kaldırma

## How to test (son değişen — Faz 2 `[CU]` anim + Faz 3 `[AG]` iskelet)

1. `D:\Project Cal\Project_Calcium\Project_Calcium.uproject` → `Lvl_ThirdPerson` → **Play (PIE)**.
2. **Faz 2 `[CU]` anim testi:** `BP_EnemyDummy_Faz2` önünde `MMB`/`Tab` lock-on, `LMB` (yumruk slot dynamic montage + hitstop) ve `RMB` (charged anim + hitstop) ile dummy’yi vur/öldür; `LCtrl` dodge ve `E` Interact kontrol et.
3. **Faz 3 — Kemik Yoğunluğu (bloksuz):** **`H`** (`IA_TestHit`) bas → `[Kalsiyum] BoneDensity: 75` (her basışta `-25`, `0`’da `SHATTERED` print).
4. **Faz 3 — Riskli blok + kol düşmesi:** **`Q`** (`IA_Block`) basılı tut (`Block ON`), basılıyken 3 kez **`H`** bas → her darbede `%30` (`-7.5`) BoneDensity + `JointStress` `35 → 70 → 105` artar; 3. darbede `[Kalsiyum] Limb DROPPED (RightArm)` + mesh’te `upperarm_r` **HideBone** (sağ kol görünmez) + yerde `BP_DetachedLimb` (kol yokken saldırı/blok kesilir).
5. **Faz 3 — Yerden al / tak:** Yerdeki `BP_DetachedLimb` parçasına doğru yürü (`0.6s` sonra pickup aktif) → `UnHideBone` + `[Kalsiyum] Limb REATTACHED` → kol geri gelir.

## Notes for next agent

- Hikâyeye dokunma. Ton alaycı.
- Faz 1 CU SpringArm / Interact’e dokunma.
- Faz 3’e geçmeden `[HU]` PIE onayı al.
- İstersen `PerformMeleeTrace_0` → `PerformMeleeTrace` Editor’de rename + callers güncelle.
