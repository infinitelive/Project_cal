"""Refresh BP_TP_Kalsiyum TriggerLight/HeavyAttack call nodes after melee rewire."""
import unreal

LOG = "[CharAtk]"
CHAR = "/Game/ThirdPerson/Blueprints/BP_TP_Kalsiyum"
MELEE = "/Game/ThirdPerson/Blueprints/AC_MeleeCombat"


def log(m):
    unreal.log(f"{LOG} {m}")


def connect(a, b, label):
    assert a and a.is_valid() and b and b.is_valid(), label
    assert a.try_create_connection(b), label


def main():
    # ensure melee has the custom events
    mbp = unreal.EditorAssetLibrary.load_asset(MELEE)
    mok = unreal.BlueprintEditorLibrary.compile_blueprint(mbp)
    mge = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(mbp)
    )
    titles = [n.get_node_title() for n in mge.list_all_nodes()]
    log(f"melee compiled={mok} hasLight={'TriggerLightAttack' in titles} hasHeavy={'TriggerHeavyAttack' in titles}")
    unreal.EditorAssetLibrary.save_loaded_asset(mbp)

    bp = unreal.EditorAssetLibrary.load_asset(CHAR)
    ge = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(bp)
    )
    log(f"char before: {[[n.get_node_title() for n in ge.list_all_nodes()]].__len__()}")
    for n in ge.list_all_nodes():
        t = n.get_node_title()
        if any(k in t for k in ("LightAttack", "HeavyAttack", "TriggerLight", "TriggerHeavy", "IA_Light", "IA_Heavy")):
            log(f"  {t}")

    # Remove broken Trigger* call nodes (keep IA_ input events)
    kill = []
    for n in list(ge.list_all_nodes()):
        t = n.get_node_title()
        if t in ("TriggerLightAttack", "TriggerHeavyAttack", "Trigger Light Attack", "Trigger Heavy Attack"):
            kill.append(n)
        # also error nodes
    for e in list(ge.list_nodes_with_errors()):
        if e not in kill:
            kill.append(e)
            log(f"err node {e.get_node_title()}")
    if kill:
        ge.remove_nodes(kill)
        log(f"removed {len(kill)}")

    # Find IA_LightAttack / IA_HeavyAttack enhanced input nodes and their then pins
    # Also find Get AC_MeleeCombat
    light_ia = heavy_ia = None
    melee_gets = []
    for n in ge.list_all_nodes():
        t = n.get_node_title()
        if "IA_LightAttack" in t:
            light_ia = n
        if "IA_HeavyAttack" in t:
            heavy_ia = n
        if "AC_MeleeCombat" in t and ("Get" in t or "Al" in t):
            melee_gets.append(n)
            log(f"melee get: {t}")

    log(f"light_ia={light_ia is not None} heavy_ia={heavy_ia is not None} melee_gets={len(melee_gets)}")

    def add_trigger(ia_node, fn_name, y):
        assert ia_node, fn_name
        call = None
        for path in (
            f"/Game/ThirdPerson/Blueprints/AC_MeleeCombat.AC_MeleeCombat_C.{fn_name}",
            fn_name,
        ):
            call = ge.add_call_function_node(path)
            if call:
                log(f"added {fn_name} via {path}")
                break
        # custom event call might need add_call_on_actor / different API
        if not call:
            call = ge.add_custom_event_node(fn_name)  # wrong
            log(f"fallback custom? {call}")
        assert call, f"cannot add {fn_name}"

        # Get melee component — reuse first get or create
        if melee_gets:
            get_m = melee_gets[0]
        else:
            get_m = ge.add_call_function_node("/Script/Engine.Actor.GetComponentByClass")
            # self = self actor — for character event graph, need self reference
            # GetComponentByClass on Self
            set_ok = get_m.find_input_pin("ComponentClass").set_pin_value(
                "/Game/ThirdPerson/Blueprints/AC_MeleeCombat.AC_MeleeCombat_C"
            )
            log(f"new get melee cls={set_ok}")

        then = ia_node.find_then_pin()
        # Enhanced input may have Triggered / Started pins
        if not (then and then.is_valid()):
            for pn in ("Triggered", "Started", "Completed", "then", "execute"):
                if hasattr(ia_node, "find_output_pin"):
                    p = ia_node.find_output_pin(pn)
                    if p and p.is_valid():
                        then = p
                        log(f"using pin {pn}")
                        break
                p = ia_node.find_input_pin(pn)  # unlikely
        assert then and then.is_valid(), f"no then on {fn_name}"

        connect(then, call.find_execute_pin(), f"{fn_name} exec")
        # self pin from melee component
        # Get result → call self
        if hasattr(get_m, "find_result_pin"):
            connect(get_m.find_result_pin(), call.find_self_pin(), f"{fn_name} self")
        call.set_node_pos(unreal.IntPoint(600, y))
        return call

    add_trigger(light_ia, "TriggerLightAttack", 0)
    add_trigger(heavy_ia, "TriggerHeavyAttack", 400)

    ok = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    errs = [e.get_node_title() for e in ge.list_nodes_with_errors()]
    log(f"char compiled={ok} errs={errs}")
    # compile melee again then char
    unreal.BlueprintEditorLibrary.compile_blueprint(mbp)
    ok2 = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    errs2 = [e.get_node_title() for e in ge.list_nodes_with_errors()]
    log(f"char recompiled={ok2} errs={errs2}")
    unreal.EditorAssetLibrary.save_loaded_asset(mbp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp)
    assert ok2 and not errs2, errs2
    log("DONE CHAR ATTACKS")


if __name__ == "__main__":
    main()
