"""Arm drop → blade falls with physics.

GetComponentByClass(StaticMeshComponent) returns typed SMC — no Cast.
Also keeps EnableDropPhysics on blade BPs as manual/fallback.

PIE STOPPED.
"""
import unreal

LOG = "[WpnDropPhys]"
EQUIP = "/Game/ThirdPerson/Blueprints/AC_LimbEquip"
EQUIP_CLS = "/Game/ThirdPerson/Blueprints/AC_LimbEquip.AC_LimbEquip_C"
BLADE_BPS = (
    "/Game/Weapons/BP_HandWeapon",
    "/Game/Weapons/BP_Blade_Viking",
    "/Game/Weapons/BP_Blade_Ninja",
)


def log(m):
    unreal.log(f"{LOG} {m}")


def connect(a, b, label):
    assert a and a.is_valid() and b and b.is_valid(), f"{label} pins"
    assert a.try_create_connection(b), label


def try_connect(a, b, label):
    if not (a and a.is_valid() and b and b.is_valid()):
        return False
    ok = bool(a.try_create_connection(b))
    if not ok:
        log(f"WARN connect fail {label}")
    return ok


def set_val(pin, value, label):
    if not (pin and pin.is_valid()):
        log(f"skip set {label}")
        return False
    return bool(pin.set_pin_value(value))


def pin_in(node, *names):
    for n in names:
        p = node.find_input_pin(n)
        if p and p.is_valid():
            return p
    return None


def pin_out(node, *names):
    for n in names:
        p = node.find_output_pin(n) if hasattr(node, "find_output_pin") else None
        if p and p.is_valid():
            return p
    return None


def add_call(ge, path):
    n = ge.add_call_function_node(path)
    assert n, path
    return n


def save(a):
    assert unreal.EditorAssetLibrary.save_loaded_asset(a, only_if_is_dirty=False)
    log(f"saved {a.get_name()}")


def wipe_titles(ge, titles=(), substrs=()):
    kill = []
    for n in list(ge.list_all_nodes()):
        t = n.get_node_title() or ""
        if t in titles:
            kill.append(n)
            continue
        pin = pin_in(n, "InString", "In String")
        if pin and hasattr(pin, "get_pin_value"):
            try:
                val = pin.get_pin_value() or ""
            except Exception:
                val = ""
            if any(s in val for s in substrs):
                kill.append(n)
    if kill:
        ge.remove_nodes(kill)
        log(f"wiped {len(kill)}")


def ensure_enable_drop_physics(bp_path: str) -> None:
    bel = unreal.BlueprintEditorLibrary
    bp = unreal.EditorAssetLibrary.load_asset(bp_path)
    assert bp, bp_path
    ge = unreal.BlueprintGraphEditor.get_graph_editor(bel.find_event_graph(bp))
    for n in ge.list_all_nodes():
        if n.get_node_title() == "EnableDropPhysics":
            log(f"keep EnableDropPhysics {bp.get_name()}")
            return

    wipe_titles(ge, titles=("EnableDropPhysics",), substrs=("[Kalsiyum] Blade physics ON",))
    ev = ge.add_custom_event_node("EnableDropPhysics")
    smc = None
    for name in ("StaticMeshComponent", "Static Mesh Component"):
        try:
            smc = ge.add_get_member_variable_node(name)
            if smc:
                break
        except Exception:
            continue
    assert smc, f"SMC member {bp_path}"

    set_prof = add_call(ge, "/Script/Engine.PrimitiveComponent.SetCollisionProfileName")
    set_col = add_call(ge, "/Script/Engine.PrimitiveComponent.SetCollisionEnabled")
    set_sim = add_call(ge, "/Script/Engine.PrimitiveComponent.SetSimulatePhysics")
    add_imp = add_call(ge, "/Script/Engine.PrimitiveComponent.AddImpulse")
    mk = add_call(ge, "/Script/Engine.KismetMathLibrary.MakeVector")
    pr = add_call(ge, "/Script/Engine.KismetSystemLibrary.PrintString")
    out = smc.find_result_pin()

    connect(ev.find_then_pin(), set_prof.find_execute_pin(), "p")
    connect(out, set_prof.find_self_pin(), "ps")
    set_val(pin_in(set_prof, "InCollisionProfileName", "CollisionProfileName"), "PhysicsActor", "pv")
    connect(set_prof.find_then_pin(), set_col.find_execute_pin(), "c")
    connect(out, set_col.find_self_pin(), "cs")
    set_val(pin_in(set_col, "NewType"), "QueryAndPhysics", "cv")
    connect(set_col.find_then_pin(), set_sim.find_execute_pin(), "s")
    connect(out, set_sim.find_self_pin(), "ss")
    set_val(pin_in(set_sim, "bSimulate"), "true", "sv")
    set_val(pin_in(mk, "X"), "120.0", "x")
    set_val(pin_in(mk, "Y"), "40.0", "y")
    set_val(pin_in(mk, "Z"), "280.0", "z")
    connect(set_sim.find_then_pin(), add_imp.find_execute_pin(), "i")
    connect(out, add_imp.find_self_pin(), "is")
    connect(mk.find_result_pin(), pin_in(add_imp, "Impulse"), "iv")
    set_val(pin_in(add_imp, "bVelChange"), "true", "vel")
    connect(add_imp.find_then_pin(), pr.find_execute_pin(), "pr")
    set_val(pin_in(pr, "InString", "In String"), "[Kalsiyum] Blade physics ON", "prs")

    ok = bel.compile_blueprint(bp)
    assert ok, bp_path
    save(bp)


def build_drop_weapon_to_world(eq):
    bel = unreal.BlueprintEditorLibrary
    ge = unreal.BlueprintGraphEditor.get_graph_editor(bel.find_event_graph(eq))
    wipe_titles(
        ge,
        titles=("DropWeaponToWorld",),
        substrs=("Weapon dropped to world", "Weapon drop skip", "Weapon drop no SMC"),
    )

    ev = ge.add_custom_event_node("DropWeaponToWorld")
    g_wa = ge.add_get_member_variable_node("WeaponActor")
    is_v = add_call(ge, "/Script/Engine.KismetSystemLibrary.IsValid")
    br = ge.add_branch_node()
    detach = add_call(ge, "/Script/Engine.Actor.K2_DetachFromActor")
    # GetComponentByClass with StaticMeshComponent → typed SMC
    get_comp = add_call(ge, "/Script/Engine.Actor.GetComponentByClass")
    is_smc = add_call(ge, "/Script/Engine.KismetSystemLibrary.IsValid")
    br_smc = ge.add_branch_node()
    set_prof = add_call(ge, "/Script/Engine.PrimitiveComponent.SetCollisionProfileName")
    set_col = add_call(ge, "/Script/Engine.PrimitiveComponent.SetCollisionEnabled")
    set_sim = add_call(ge, "/Script/Engine.PrimitiveComponent.SetSimulatePhysics")
    add_imp = add_call(ge, "/Script/Engine.PrimitiveComponent.AddImpulse")
    mk = add_call(ge, "/Script/Engine.KismetMathLibrary.MakeVector")
    s_none = ge.add_set_member_variable_node("WeaponActor")
    pr_skip = add_call(ge, "/Script/Engine.KismetSystemLibrary.PrintString")
    pr_nosmc = add_call(ge, "/Script/Engine.KismetSystemLibrary.PrintString")
    pr_ok = add_call(ge, "/Script/Engine.KismetSystemLibrary.PrintString")

    # Class pin: StaticMeshComponent
    set_val(
        pin_in(get_comp, "ComponentClass", "Class"),
        "/Script/Engine.StaticMeshComponent",
        "compclass",
    )

    connect(ev.find_then_pin(), br.find_execute_pin(), "br")
    connect(g_wa.find_result_pin(), pin_in(is_v, "Object"), "iv")
    connect(is_v.find_result_pin(), br.find_condition_pin(), "?")
    connect(br.find_else_pin(), pr_skip.find_execute_pin(), "skip")
    set_val(pin_in(pr_skip, "InString", "In String"), "[Kalsiyum] Weapon drop skip (none)", "sks")

    # Detach — keep WeaponActor ref until after physics
    connect(br.find_then_pin(), detach.find_execute_pin(), "det")
    g_wa2 = ge.add_get_member_variable_node("WeaponActor")
    connect(g_wa2.find_result_pin(), detach.find_self_pin(), "dets")
    for name, val in (
        ("LocationRule", "KeepWorld"),
        ("RotationRule", "KeepWorld"),
        ("ScaleRule", "KeepWorld"),
    ):
        set_val(pin_in(detach, name), val, name)

    connect(detach.find_then_pin(), get_comp.find_execute_pin() if get_comp.find_execute_pin() and get_comp.find_execute_pin().is_valid() else br_smc.find_execute_pin(), "gc")
    g_wa3 = ge.add_get_member_variable_node("WeaponActor")
    connect(g_wa3.find_result_pin(), get_comp.find_self_pin(), "gcs")

    # GetComponentByClass may be pure — then wire exec detach→br_smc
    smc_out = get_comp.find_result_pin() or pin_out(get_comp, "ReturnValue", "Return Value")
    assert smc_out, "GetComponentByClass result"

    # If get_comp has no exec, reconnect:
    if not (get_comp.find_execute_pin() and get_comp.find_execute_pin().is_valid()):
        # already tried connect detach→br_smc via fallback above; ensure:
        try_connect(detach.find_then_pin(), br_smc.find_execute_pin(), "det→brsmc")
    else:
        then_gc = get_comp.find_then_pin()
        if then_gc and then_gc.is_valid():
            connect(then_gc, br_smc.find_execute_pin(), "gc→br")
        else:
            try_connect(detach.find_then_pin(), br_smc.find_execute_pin(), "det→brsmc2")

    connect(smc_out, pin_in(is_smc, "Object"), "ismc")
    connect(is_smc.find_result_pin(), br_smc.find_condition_pin(), "?smc")
    connect(br_smc.find_else_pin(), pr_nosmc.find_execute_pin(), "nosmc")
    set_val(pin_in(pr_nosmc, "InString", "In String"), "[Kalsiyum] Weapon drop no SMC", "nosmcs")
    # still null weapon on no SMC
    try_connect(pr_nosmc.find_then_pin(), s_none.find_execute_pin(), "null-nosmc")

    connect(br_smc.find_then_pin(), set_prof.find_execute_pin(), "prof")
    connect(smc_out, set_prof.find_self_pin(), "profs")
    set_val(pin_in(set_prof, "InCollisionProfileName", "CollisionProfileName"), "PhysicsActor", "pv")

    connect(set_prof.find_then_pin(), set_col.find_execute_pin(), "col")
    connect(smc_out, set_col.find_self_pin(), "cols")
    set_val(pin_in(set_col, "NewType"), "QueryAndPhysics", "cv")

    connect(set_col.find_then_pin(), set_sim.find_execute_pin(), "sim")
    connect(smc_out, set_sim.find_self_pin(), "sims")
    set_val(pin_in(set_sim, "bSimulate"), "true", "sv")

    set_val(pin_in(mk, "X"), "120.0", "x")
    set_val(pin_in(mk, "Y"), "40.0", "y")
    set_val(pin_in(mk, "Z"), "280.0", "z")
    connect(set_sim.find_then_pin(), add_imp.find_execute_pin(), "imp")
    connect(smc_out, add_imp.find_self_pin(), "imps")
    connect(mk.find_result_pin(), pin_in(add_imp, "Impulse"), "impv")
    set_val(pin_in(add_imp, "bVelChange"), "true", "vel")

    # Second Set WeaponActor for success path (if first used for nosmc, create another)
    s_none2 = ge.add_set_member_variable_node("WeaponActor")
    connect(add_imp.find_then_pin(), s_none2.find_execute_pin(), "null")
    connect(s_none2.find_then_pin(), pr_ok.find_execute_pin(), "ok")
    set_val(pin_in(pr_ok, "InString", "In String"), "[Kalsiyum] Weapon dropped to world (physics)", "oks")

    ok = bel.compile_blueprint(eq)
    errs = []
    try:
        errs = list(bel.get_blueprint_compile_error_messages(eq) or [])
    except Exception:
        pass
    log(f"DropWeaponToWorld compile={ok} errs={errs[:10]}")
    assert ok, errs[:10]
    save(eq)
    return unreal.EditorAssetLibrary.load_asset(EQUIP)


def rewire_on_arm_dropped(eq):
    bel = unreal.BlueprintEditorLibrary
    ge = unreal.BlueprintGraphEditor.get_graph_editor(bel.find_event_graph(eq))

    for title in ("ClearWeaponVisual", "DropWeaponToWorld"):
        kill = []
        for n in list(ge.list_all_nodes()):
            if (n.get_node_title() or "") != title:
                continue
            try:
                if n.find_self_pin() and n.find_self_pin().is_valid():
                    kill.append(n)
            except Exception:
                pass
        if kill:
            ge.remove_nodes(kill)
            log(f"removed {title} calls {len(kill)}")

    drop_ev = None
    for n in ge.list_all_nodes():
        if n.get_node_title() == "OnArmDropped":
            drop_ev = n
            break
    assert drop_ev, "OnArmDropped missing"
    call = ge.add_call_function_node(f"{EQUIP_CLS}.DropWeaponToWorld")
    assert call, "DropWeaponToWorld call"
    connect(drop_ev.find_then_pin(), call.find_execute_pin(), "drop→call")

    for n in ge.list_all_nodes():
        if "NotifyArmDroppedMood" not in (n.get_node_title() or ""):
            continue
        try:
            if n.find_self_pin() and n.find_self_pin().is_valid():
                try_connect(call.find_then_pin(), n.find_execute_pin(), "mood")
                break
        except Exception:
            pass

    ok = bel.compile_blueprint(eq)
    errs = []
    try:
        errs = list(bel.get_blueprint_compile_error_messages(eq) or [])
    except Exception:
        pass
    log(f"rewire compile={ok} errs={errs[:6]}")
    assert ok, errs[:6]
    save(eq)


def main():
    log("=== start ===")
    for p in BLADE_BPS:
        ensure_enable_drop_physics(p)
    eq = unreal.EditorAssetLibrary.load_asset(EQUIP)
    eq = build_drop_weapon_to_world(eq)
    rewire_on_arm_dropped(eq)
    log("DONE WEAPON DROP PHYSICS OK")


if __name__ == "__main__":
    main()
