# Cursor — hazır promptlar

Kopyala → Agent’a yapıştır. `@` ile dosya ekle.

## Oturum açılışı

```
@AGENT_HANDOFF.md @docs/SCOPE.md @docs/WORKFLOW.md
UE root: D:\Project Cal\Project_Calcium
Kalsiyum UE5 third-person. Hikâye yok. Antigravity iskeletini bozmadan polish/bug.
Şu anki hedef: AGENT_HANDOFF’taki Current focus ([CU] after AG Faz 1).
Kabul kriteri: PIE’de nasıl test edeceğimi handoff’a yazacağım.
```
## Faz 1 — hareket + kamera hissi

```
@AGENT_HANDOFF.md
SpringArm/follow camera + walk hissini düzelt. Karakteri kapatmasın, duvara girmesin.
Sprint varsa acceleration yumuşak olsun. Combat’a dokunma.
```

## Faz 2 — melee timing

```
Light/Heavy/Dodge pencerelerini sıkılaştır. Hit trace sadece active frame’de.
Dummy’de playtest: 10 light combo + 5 dodge. Hit stop abartma.
```

## Faz 3 — blok riski

```
Blok güvenli hissettirmesin. Stres dolunca sağ kol düşsün; eksik kolla attack set kısıtlı.
Yerden al → socket’e tak interaction’ı netleştir.
```

## Faz 5 — alev

```
Mood değişince sadece sayılar değil, Niagara/HUD rengi de değişsin.
Mavi/Kırmızı/Yeşil DataAsset değerlerini elle oynamama izin ver (designer-friendly).
```

## Faz 6 — kamp

```
Campfire: Dinlen = save + bone density full. Ölünce son kampa dön.
Roguelite reset yok. Rest UI minimal, bir satır alaycı metin OK.
```

## Bug tarama

```
Son değişiklikte regressyon ara: save, limb attach, mood reset kamp sonrası.
Minimal fix; yeni sistem ekleme.
```

## Handoff kapatış (her iş bitince söyle)

```
AGENT_HANDOFF.md güncelle: Done’a taşı, Current focus’u sonraki tek işe çek,
How to test’i 3 adım yaz, Owner tablosunu güncelle.
```
