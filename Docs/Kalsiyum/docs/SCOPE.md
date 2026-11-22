# Kalsiyum — Kapsam Kilidi

Son güncelleme: 2026-11-22

## Sabit kararlar

| Konu | Karar |
|------|--------|
| Motor | Unreal Engine 5 |
| Perspektif | **3. şahıs** (lock-on hedefli, Souls / GoT tarzı) |
| Yapı | Tek uzun hikâye (roguelite yok) |
| Checkpoint | Kamp ateşi — Ghost of Tsushima tarzı |
| Ton | Alaycı komedi + iç melankoli |
| Platform | PC |
| Hikâye | **Şimdilik yok** — beat’ler sonra |

## Üç sütun (her feature bunlardan birine hizmet eder)

1. **Kırılganlık** — güç = risk (osteoporoz, uzuv kopması)
2. **Kimlik yaması** — protez/zırh “kiralık kimlik”, aidiyet yok
3. **Alaycı tragikomedi** — absürt görüntü, iğneleyici alt metin; slapstick değil

Uymayan feature → backlog, v0.1’e girmez.

## v0.1 Dikey dilim (hedef)

Oynanır 10–15 dk:

- [ ] 3. şahıs hareket + kamera + etkileşim
- [ ] Light / Heavy saldırı + dodge
- [ ] Riskli blok → eklem stresi → **tek kol düşer** → yerden al/tak
- [ ] 2 protez kol: Ağır (Viking) / Çevik (Ninja)
- [ ] Alev mood ×3: Mavi / Kırmızı / Yeşil (stat + Niagara rengi)
- [ ] Kamp ateşi: dinlen = checkpoint + kaynak yenile + (opsiyonel) yağ sür
- [ ] 1 harabe alanı + 1 dummy/basit düşman
- [ ] UI: “Kemik Yoğunluğu” can barı

## v0.1’de YOK

- Hikâye / diyalog / twist
- 7 kültür kimliği
- Altın alev (final stub bile şart değil)
- Bacak protezleri (kol yeter)
- 1. şahıs kamera
- Online, crafting ağacı, yüzlerce silah
- Konsol / mobile

## Kamp checkpoint (GoT referansı)

- Dünya kalıcı; ölüm = son kampa dönüş (veya yakındaki güvenli nokta) — **run silinmez**
- Kampta: kayıt, Kemik Yoğunluğu doldur, yağ/ilik craft, ekipman düzenle
- Fast travel: sonra; v0.1’de tek kamp yeter

## Alev (oynanış sayıları — v0.1 taslak)

| Mood | Tetik (basit) | Etki |
|------|----------------|------|
| Mavi | Savaş dışı / uzuv eksik | −%20 hareket, düşman algı mesafesi − |
| Kırmızı | Ağır hasar alındı | +%35 hasar & atk hız; kırılma şansı ↑ |
| Yeşil | Yeni keşif / ilk encounter | Crit şansı ↑ (kısa süre) |

Sayılar playtest ile oynanır; kodda data-driven tut (`DataAsset` / Data Table).

## Naming (UE)

```
BP_TP_Kalsiyum          Character
BP_Campfire             Checkpoint actor
DA_Limb_*               Protez tanımları
DA_Mood_*               Mood modifier
AC_LimbSocket           Uzuv component
AC_MoodFlame            Alev/mood component
UI_BoneDensity          HUD
```
