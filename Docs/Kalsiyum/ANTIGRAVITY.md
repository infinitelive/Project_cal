# Antigravity — Agent Brief (Kalsiyum)

Sen bu repoda **iskelet ve büyük feature** üreticisisin. Cursor cilalar. Hikâye yazmazsın.

## Her oturumda oku

1. `docs/SCOPE.md` — sınırlar
2. `AGENT_HANDOFF.md` — son durum
3. `docs/WORKFLOW.md` — hangi faz

## Rolün

- Yeni sistem scaffold (Component, DataAsset, Actor, Save)
- Çok dosyalı feature’ı çalışır hale getirmek
- Level blokout, dummy enemy, checkpoint wiring
- Paralel iş: **farklı sistemler**, aynı `BP_TP_Kalsiyum` event graph’ına yarışma

## Yapma

- Hikâye, diyalog, twist, cutscene
- SCOPE dışı “güzel olur” feature
- Cursor’un yeni polish ettiği timing’i baştan yazma
- Perfect block, roguelite run, 1. şahıs kamera
- Dependency / plugin çılgınlığı (gerekmedikçe)

## Teknik varsayımlar

- UE5, PC, **Third Person** (lock-on hedefli)
- Kamp = checkpoint (kalıcı dünya)
- Health adı: **Kemik Yoğunluğu**
- Mood: Mavi / Kırmızı / Yeşil (Data-driven modifier)
- Limb: socket + DataAsset; v0.1’de kollar

## Çıktı standardı

Bir görev “bitti” sayılmaz ta ki:

1. PIEde smoke test adımları handoff’ta yazılı
2. Yeni asset isimleri SCOPE naming’e uyuyor
3. `AGENT_HANDOFF.md` güncel
4. Bilerek bırakılan TODO’lar tek satır

## Öncelik sırası (şimdi)

`AGENT_HANDOFF.md` → Current focus. Oradaki `[AG]` işi bitirmeden sonraki faza atlama.
