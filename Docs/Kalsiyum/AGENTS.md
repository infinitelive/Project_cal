# Kalsiyum — agent stack

Shared for **Cursor** and **Antigravity**. Source of truth remains Git + the files in this folder.

**Unreal root:** `D:\Project Cal\Project_Calcium` (`Project_Calcium.uproject`). Docs live here under `Docs\Kalsiyum` — do not create a second project in `ue-project/`.

## Required reading each session

1. `docs/SCOPE.md`
2. `AGENT_HANDOFF.md`
3. `docs/WORKFLOW.md`

## Plugins / skills (both IDEs)

| Tool | Use for |
|------|---------|
| **Superpowers** | Brainstorm before features; write/execute plans; TDD; systematic debugging; verify before claiming done |
| **Ponytail** | Smallest complete change; `/ponytail-review` / `/ponytail-audit` on big diffs |
| **Graphify** | Project map in `../../graphify-out/` — query before inventing architecture |

Roles: Antigravity = scaffold `[AG]`; Cursor = polish/bugs `[CU]`; human = merge/playtest `[HU]`. Do not both edit the same Blueprint event graph in one session.
