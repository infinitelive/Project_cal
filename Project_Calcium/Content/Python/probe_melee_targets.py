"""List AC_MeleeCombat nodes with unbound Target/self pins (Actor/Character errors)."""
import unreal

BP = "/Game/ThirdPerson/Blueprints/AC_MeleeCombat"
LOG = "[ProbeMelee]"


def log(m):
    unreal.log(f"{LOG} {m}")


def pin_connected(pin) -> bool:
    if not pin or not pin.is_valid():
        return False
    try:
        if hasattr(pin, "is_connected"):
            return bool(pin.is_connected())
        if hasattr(pin, "has_any_connections"):
            return bool(pin.has_any_connections())
        links = pin.get_linked_pins() if hasattr(pin, "get_linked_pins") else None
        if links is not None:
            return len(list(links)) > 0
    except Exception as e:
        return f"err:{e}"
    return False


def main():
    bel = unreal.BlueprintEditorLibrary
    bp = unreal.EditorAssetLibrary.load_asset(BP)
    assert bp
    graphs = []
    # Event graph
    eg = bel.find_event_graph(bp)
    if eg:
        graphs.append(("EventGraph", eg))
    # All graphs by common names + scan
    for name in (
        "FaceLockedTarget",
        "PerformMeleeTrace",
        "PerformMeleeTrace_0",
        "PerformMeleeTrace_1",
        "GetDamageMult",
        "GetAttackSpeedMult",
        "NotifyArmDetached",
        "NotifyArmAttached",
        "ApplyAnimSet_Viking",
        "ApplyAnimSet_Ninja",
        "ApplyAnimSet_Unarmed",
    ):
        g = bel.find_graph(bp, name)
        if g:
            graphs.append((name, g))

    # Also try list_graphs if available
    try:
        for g in bel.get_all_graphs(bp) or []:
            n = g.get_name() if hasattr(g, "get_name") else str(g)
            if not any(n == a or n in a for a, _ in graphs):
                graphs.append((n, g))
    except Exception as e:
        log(f"get_all_graphs skip {e}")

    for gname, g in graphs:
        ge = unreal.BlueprintGraphEditor.get_graph_editor(g)
        nodes = list(ge.list_all_nodes())
        log(f"=== {gname} nodes={len(nodes)} ===")
        for n in nodes:
            title = n.get_node_title() or "?"
            # Check self / Target pins
            pins = []
            try:
                pins = list(n.get_pins()) if hasattr(n, "get_pins") else []
            except Exception:
                pins = []
            self_pin = None
            try:
                self_pin = n.find_self_pin()
            except Exception:
                pass
            if self_pin and self_pin.is_valid():
                conn = pin_connected(self_pin)
                # Pure/static may not need connection if default self works for component
                log(f"  SELF title='{title}' connected={conn}")
            for p in pins:
                try:
                    pname = p.get_name() if hasattr(p, "get_name") else str(p)
                except Exception:
                    pname = "?"
                if pname not in ("self", "Target", "execute", "then", "Output_Get"):
                    # also check type for Actor/Character
                    pass
                if pname in ("self", "Target"):
                    log(f"  PIN '{pname}' on '{title}' connected={pin_connected(p)}")

    # Compile and dump status
    ok = bel.compile_blueprint(bp)
    log(f"compile={ok}")
    try:
        for e in list(bel.get_blueprint_compile_error_messages(bp) or []):
            log(f"ERR {e}")
    except Exception:
        pass
    log("DONE PROBE")


if __name__ == "__main__":
    main()
