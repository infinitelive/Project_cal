# Çift AI İş Akışı — Cursor + Antigravity

## Altın kurallar

1. **Kaynak gerçek = Git + bu repo dosyaları.** Chat hafıza değil.
2. **Aynı anda aynı dosyaya iki AI dokunmaz.** Feature branch veya “şu an kim” kuralı.
3. **Her oturum sonunda `AGENT_HANDOFF.md` güncellenir** (5–10 satır).
4. **Hikâye yazılmaz** ta ki sen açıkça “hikâye sprinti” demeden.
5. **Playtest olmadan “bitti” yok.** Sen 2 dk oynayıp not düş.

---

## Kim ne yapar

| | Antigravity | Cursor | Sen |
|--|-------------|--------|-----|
| Güçlü | Uzun otonom, paralel iskelet, büyük scaffold | İnce edit, bug, hissiyat, refactor | Karar, ton, merge, “bu alaycı mı?” |
| Tipik görev | Yeni sistem iskeleti, level blokout, çok dosyalı feature | Anim/timing, input feel, Niagara param, UI | Playtest, scope kes, branch merge |
| Kaçınsın | Pixel-perfect polish, “son %10 his” | 3 gündür süren boş scaffold | İkisini aynı BP’ye salmak |

### Görev etiketi (handoff’ta kullan)

- `[AG]` Antigravity owns
- `[CU]` Cursor owns
- `[HU]` Sadece insan
- `[ANY]` Kim müsaitse (küçük iş)

---

## Günlük döngü (önerilen)

```text
1. AGENT_HANDOFF.md oku
2. docs/SCOPE.md — hâlâ v0.1 mi?
3. Tek hedef seç (1 cümle)
4. Branch: feat/<kısa-ad>
5. Araç seç (AG veya CU) — diğerine “dokunma” yaz
6. Çalış → playtest
7. Handoff güncelle + commit
```

Commit mesajı örneği: `feat(limbs): drop and reattach right arm socket`

---

## Faz planı (Unreal + 3. şahıs)

### Faz 0 — Repo iskeleti `[HU]` + `[ANY]` ✅
- [x] UE5 Third Person projesi: `D:\Project Cal\Project_Calcium` (stock template)
- [ ] `.gitignore` (Binaries, Intermediate, DerivedDataCache, Saved…) — repo setup when Git init’d
- [ ] İlk commit: template + docs
- [x] Cursor + Antigravity path truth: UE = `Project_Calcium`, docs = `Docs\Kalsiyum`

**Çıkış:** Editor açılıyor, TP pawn sahnede yürüyor. (stock `Lvl_ThirdPerson`)

### Faz 1 — TP hareket + kamera temeli `[AG]` → polish `[CU]`
- [x] `[AG]` Input Mapping Context (WASD, camera orbit, interact)
- [x] `[AG]` Sprint / crouch (opsiyonel)
- [x] `[AG]` SpringArm + follow camera (omuz / sırt mesafesi)
- [ ] `[CU]` Kamera lag, collision, target arm length hissi
- [ ] `[CU]` Interaction trace (kamp / yerdeki uzuv)

**Çıkış:** Temiz 3. şahıs locomotion; kamera karaktere yapışık değil, okunaklı.

### Faz 2 — Melee combat çekirdeği `[AG]` → `[CU]`
3. şahıs kılıç = karakter yönü + (sonra) lock-on; weapon trace / anim notify.

- [x] `[AG]` Light / Heavy montaj (placeholder anim OK)
- [x] `[AG]` Weapon trace veya collision window
- [x] `[AG]` Basit lock-on stub (tek hedef; polish sonra)
- [x] `[AG]` Dummy enemy (`BP_EnemyDummy`) + health
- [x] `[CU]` Startup/active/recovery timing (+ placeholder montages)
- [ ] `[CU]` Dodge i-frame süresi (deferred — AG values)
- [x] `[CU]` Hit stop / camera punch (hafif; aşırı shake yok)

**Çıkış:** Dummy’yi öldürebiliyorsun; dodge kaçırıyor.

### Faz 3 — Kemik Yoğunluğu + riskli blok `[AG]` → `[CU]`
- [x] `[AG]` Health = Bone Density attribute
- [x] `[AG]` Block = stamina/stres biriktirir (perfect block yok)
- [x] `[AG]` Stres dolunca kol socket boşalır + limb actor spawn
- [ ] `[CU]` Eksik kolla attack set kısıtı
- [ ] `[CU]` Pick up + reattach interaction

**Çıkış:** Blok riskli; kol düşüyor; yerden takıyorsun.

### Faz 4 — Protez kollar ×2 `[AG]` → `[CU]`
- [x] `[AG]` `DA_Limb_VikingArm`, `DA_Limb_NinjaArm`
- [x] `[AG]` Socket component okur DataAsset → damage/speed
- [ ] `[CU]` Görsel mesh swap (placeholder static mesh OK)
- [ ] `[CU]` Ağır vs çevik hissedilir fark

**Çıkış:** İki kol, iki farklı dövüş temposu.

### Faz 5 — Alev mood ×3 `[AG]` → `[CU]`
- [ ] `[AG]` `AC_MoodFlame` + enum + modifiers
- [ ] `[AG]` Tetik kuralları (basit timer/event)
- [ ] `[CU]` Niagara renk param (kafa üstü / görüş kenarı)
- [ ] `[CU]` HUD’da mood rengi ipucu

**Çıkış:** Renk değişince sayılar değişiyor; VFX okunuyor.

### Faz 6 — Kamp ateşi checkpoint `[AG]` → `[CU]`
GoT mantığı: kalıcı dünya, kampta dinlen.

- [ ] `[AG]` `BP_Campfire` + interact
- [ ] `[AG]` Save game (transform, bone density, limbs, mood)
- [ ] `[AG]` Ölüm → son kamp
- [ ] `[CU]` Rest UI (minimal: “Dinlen” / “Ayrıl”)
- [ ] `[CU]` Rest = can doldur + (opsiyonel) düşman reset bayrağı

**Çıkış:** Öl → kampta uyan; progress silinmemiş.

### Faz 7 — İlik / yağ (hafif) `[CU]` veya `[AG]`
- [ ] Kemik pickup
- [ ] Kampta kazan progress → yağ charge
- [ ] Yağ = bone density heal

**Çıkış:** Savaş → loot → kamp → heal döngüsü.

### Faz 8 — Birleşik dilim + alaycı ton dokunuşu `[HU]` + `[CU]`
- [ ] 1 blokout harabe
- [ ] Placeholder alaycı interact metinleri (“Başka bir ‘efsane’ kemiği. Harika.”)
- [ ] 15 dk playtest checklist (aşağıda)

**Çıkış:** v0.1 demo.

---

## Playtest checklist (her faz sonu)

- [ ] 60 FPS hedefi rahat mı? (PC, development)
- [ ] Kamera duvara giriyor / karakteri kapatıyor mu?
- [ ] Blok “güvenli” hissettiriyor mu? (hayır olmalı)
- [ ] Protez farkı gözle anlaşılıyor mu?
- [ ] Kamp kayıt güvenilir mi?
- [ ] Bir satır alay var mı, yoksa steril mi?

---

## Branch / çakışma önleme

```text
main
 └── feat/tp-movement     [AG] sonra [CU]
 └── feat/melee-core      [AG] sonra [CU]
 └── feat/limbs           [AG] sonra [CU]
 └── feat/mood-flame      [AG] sonra [CU]
 └── feat/campfire        [AG] sonra [CU]
```

Aynı anda max **iki** aktif feature; farklı sistemler (örn. mood + campfire) — aynı Character BP’ye ikisi birden yazmasın. Character değişiklikleri sıra ile merge.

---

## Antigravity oturum şablonu (kopyala-yapıştır)

```text
UE root: D:\Project Cal\Project_Calcium
Docs: D:\Project Cal\Docs\Kalsiyum
Oku: ANTIGRAVITY.md, docs/SCOPE.md, AGENT_HANDOFF.md, docs/WORKFLOW.md
Görev: [FAZ X — tek cümle]
Yapma: hikâye, yeni sistem icat etme, SCOPE dışı feature
Bitince: AGENT_HANDOFF.md güncelle, neyi nasıl test edeceğimi yaz
```

## Cursor oturum şablonu

```text
@docs/SCOPE.md @AGENT_HANDOFF.md
Şu an polish/bug fazındayım. Antigravity’nin iskeletini bozma.
Görev: [tek cümle]
Kabul: [playtest kriteri]
```

---

## Riskler (bilerek)

| Risk | Ne yap |
|------|--------|
| TP kamera + lock-on hissi | Erken playtest; anim placeholder OK |
| Blueprint spaghetti | Sistem başı Actor Component; God-BP yok |
| İki AI Character’ı parçalar | Character edit = tek owner / sırayla |
| Kapsam şişmesi | SCOPE “YOK” listesi kutsal |
