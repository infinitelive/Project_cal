"""Restore missing hand blade + original attack anims.

Root cause: CallAnims hooked onto ApplyWeaponVisual then-pin and stole spawn chain
→ no 'Weapon visual applied'. Scale/grip also shrank blades.

1) Restore BP_Blade_* mesh + import-era scale/loc/rot
2) Rebuild ApplyWeaponVisual (v6 pattern) with SM_*_Mesh BPs
3) OnArmDropped → DropWeaponToWorld (if present) else ClearWeaponVisual
4) SeqLight/Heavy CDO → original MM_Attack_01 / MM_ChargedAttack

PIE STOPPED.
  py "C:/kalsiyum_ue/Content/Python/fix_restore_weapon.py"
"""
import unreal

LOG = "[RestoreWpn]"
EQUIP = "/Game/ThirdPerson/Blueprints/AC_LimbEquip"
EQUIP_CLS = "/Game/ThirdPerson/Blueprints/AC_LimbEquip.AC_LimbEquip_C"
MELEE = "/Game/ThirdPerson/Blueprints/AC_MeleeCombat"
VIK_BP = "/Game/Weapons/BP_Blade_Viking"
VIK_CLS = "/Game/Weapons/BP_Blade_Viking.BP_Blade_Viking_C"
NIN_BP = "/Game/Weapons/BP_Blade_Ninja"
NIN_CLS = "/Game/Weapons/BP_Blade_Ninja.BP_Blade_Ninja_C"
HAND_BP = "/Game/Weapons/BP_HandWeapon"
SM_VIK = "/Game/Weapons/SM_Blade_Viking_Mesh"
SM_NIN = "/Game/Weapons/SM_Blade_Ninja_Mesh"
SM_VIK_FALLBACK = "/Game/Weapons/SM_Blade_Viking"
SM_NIN_FALLBACK = "/Game/Weapons/SM_Blade_Ninja"

# Working import-era transforms (pre broken grip)
GRIP = {
    VIK_BP: {
        "mesh": SM_VIK,
        "fallback": SM_VIK_FALLBACK,
        "scale": unreal.Vector(1.15, 1.15, 1.15),
        "loc": unreal.Vector(8.0, 0.0, 0.0),
        "rot": unreal.Rotator(0.0, 0.0, 90.0),
    },
    NIN_BP: {
        "mesh": SM_NIN,
        "fallback": SM_NIN_FALLBACK,
        "scale": unreal.Vector(0.85, 0.85, 1.05),
        "loc": unreal.Vector(6.0, 0.0, 0.0),
        "rot": unreal.Rotator(0.0, 0.0, 90.0),
    },
    HAND_BP: {
        "mesh": SM_VIK,
        "fallback": SM_VIK_FALLBACK,
        "scale": unreal.Vector(1.15, 1.15, 1.15),
        "loc": unreal.Vector(8.0, 0.0, 0.0),
        "rot": unreal.Rotator(0.0, 0.0, 90.0),
    },
}

SEQ_LIGHT = "/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_01"
SEQ_HEAVY = "/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_ChargedAttack"


def log(m):
    unreal.log(f"{LOG} {m}")


def connect(a, b, label):
    assert a and a.is_valid() and b and b.is_valid(), label
    assert a.try_create_connection(b), label


def try_connect(a, b, label):
    if not (a and a.is_valid() and b and b.is_valid()):
        return False
    return bool(a.try_create_connection(b))


def set_val(pin, value, label):
    assert pin and pin.is_valid(), label
    assert pin.set_pin_value(value), f"{label}={value}"


def pin_in(node, *names):
    for n in names:
        p = node.find_input_pin(n)
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


def find_smc(bp):
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if obj is not None and isinstance(obj, unreal.StaticMeshComponent):
            return obj
    gen = bp.generated_class()
    cdo = unreal.get_default_object(gen) if gen else None
    if not cdo:
        return None
    try:
        return cdo.get_editor_property("static_mesh_component")
    except Exception:
        root = cdo.get_editor_property("root_component")
        return root if isinstance(root, unreal.StaticMeshComponent) else None


def restore_blade_meshes():
    bel = unreal.BlueprintEditorLibrary
    log("--- blade mesh/scale ---")
    for path, cfg in GRIP.items():
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            log(f"SKIP {path}")
            continue
        bp = unreal.EditorAssetLibrary.load_asset(path)
        smc = find_smc(bp)
        assert smc, path
        mesh_path = cfg["mesh"] if unreal.EditorAssetLibrary.does_asset_exist(cfg["mesh"]) else cfg["fallback"]
        mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
        assert mesh, mesh_path
        smc.modify()
        smc.set_editor_property("static_mesh", mesh)
        smc.set_editor_property("relative_scale3d", cfg["scale"])
        smc.set_editor_property("relative_location", cfg["loc"])
        smc.set_editor_property("relative_rotation", cfg["rot"])
        try:
            smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            smc.set_collision_profile_name("NoCollision")
        except Exception:
            pass
        assert bel.compile_blueprint(bp), path
        save(bp)
        log(f"restored {path} mesh={mesh_path} scale={cfg['scale']}")


def wipe_named(ge, titles=(), substrs=()):
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


def arm_spawn(ge, then_pin, cls_path, tag):
    clr = add_call(ge, f"{EQUIP_CLS}.ClearWeaponVisual")
    own = add_call(ge, "/Script/Engine.ActorComponent.GetOwner")
    spawn = add_call(ge, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass")
    finish = add_call(ge, "/Script/Engine.GameplayStatics.FinishSpawningActor")
    make_xf = add_call(ge, "/Script/Engine.KismetMathLibrary.MakeTransform")
    s_wa = ge.add_set_member_variable_node("WeaponActor")
    get_mesh = add_call(ge, "/Script/Engine.Actor.GetComponentByClass")
    get_root = add_call(ge, "/Script/Engine.Actor.K2_GetRootComponent")
    attach = add_call(ge, "/Script/Engine.SceneComponent.K2_AttachToComponent")
    show = add_call(ge, "/Script/Engine.Actor.SetActorHiddenInGame")
    set_sc = add_call(ge, "/Script/Engine.Actor.SetActorScale3D")
    make_v = add_call(ge, "/Script/Engine.KismetMathLibrary.MakeVector")

    connect(then_pin, clr.find_execute_pin(), f"{tag}-clr")
    connect(clr.find_then_pin(), spawn.find_execute_pin(), f"{tag}-sp")
    connect(own.find_result_pin(), pin_in(spawn, "Owner"), f"{tag}-own")
    set_val(pin_in(spawn, "ActorClass"), cls_path, f"{tag}-cls")
    pcol = pin_in(spawn, "CollisionHandlingOverride")
    if pcol:
        try:
            set_val(pcol, "AlwaysSpawn", f"{tag}-col")
        except Exception:
            pass
    connect(make_xf.find_result_pin(), pin_in(spawn, "SpawnTransform"), f"{tag}-xf")
    connect(spawn.find_then_pin(), finish.find_execute_pin(), f"{tag}-fin")
    connect(spawn.find_result_pin(), pin_in(finish, "Actor"), f"{tag}-act")
    fxf = pin_in(finish, "SpawnTransform")
    if fxf:
        connect(make_xf.find_result_pin(), fxf, f"{tag}-fxf")
    connect(finish.find_then_pin(), s_wa.find_execute_pin(), f"{tag}-set")
    connect(finish.find_result_pin(), pin_in(s_wa, "WeaponActor"), f"{tag}-sv")
    connect(s_wa.find_then_pin(), attach.find_execute_pin(), f"{tag}-att")
    connect(own.find_result_pin(), get_mesh.find_self_pin(), f"{tag}-gm")
    set_val(pin_in(get_mesh, "ComponentClass"), "/Script/Engine.SkeletalMeshComponent", f"{tag}-smc")
    connect(ge.add_get_member_variable_node("WeaponActor").find_result_pin(), get_root.find_self_pin(), f"{tag}-rs")
    connect(get_root.find_result_pin(), attach.find_self_pin(), f"{tag}-as")
    connect(get_mesh.find_result_pin(), pin_in(attach, "Parent"), f"{tag}-par")
    sock = pin_in(attach, "SocketName")
    if sock:
        set_val(sock, "hand_r", f"{tag}-sock")
    for pname, pval in (
        ("LocationRule", "SnapToTarget"),
        ("RotationRule", "SnapToTarget"),
        ("ScaleRule", "KeepWorld"),
    ):
        p = pin_in(attach, pname)
        if p:
            try:
                set_val(p, pval, f"{tag}-{pname}")
            except Exception:
                pass
    connect(attach.find_then_pin(), show.find_execute_pin(), f"{tag}-sh")
    connect(ge.add_get_member_variable_node("WeaponActor").find_result_pin(), show.find_self_pin(), f"{tag}-ss")
    set_val(pin_in(show, "bNewHidden"), "false", f"{tag}-hf")
    connect(show.find_then_pin(), set_sc.find_execute_pin(), f"{tag}-sc")
    connect(ge.add_get_member_variable_node("WeaponActor").find_result_pin(), set_sc.find_self_pin(), f"{tag}-scs")
    set_val(pin_in(make_v, "X"), "1.2", f"{tag}-sx")
    set_val(pin_in(make_v, "Y"), "1.2", f"{tag}-sy")
    set_val(pin_in(make_v, "Z"), "1.2", f"{tag}-sz")
    connect(make_v.find_result_pin(), pin_in(set_sc, "NewScale3D"), f"{tag}-scv")
    return set_sc


def rebuild_apply():
    bel = unreal.BlueprintEditorLibrary
    eq = unreal.EditorAssetLibrary.load_asset(EQUIP)
    ge = unreal.BlueprintGraphEditor.get_graph_editor(bel.find_event_graph(eq))

    # Ensure ClearWeaponVisual still callable
    probe = ge.add_call_function_node(f"{EQUIP_CLS}.ClearWeaponVisual")
    assert probe, "ClearWeaponVisual missing — need full v6 rebuild"
    ge.remove_nodes([probe])

    wipe_named(
        ge,
        titles=("ApplyWeaponVisual", "CallAnimsForCurrentWeapon"),
        substrs=("Weapon visual applied", "Equip→", "Melee anim set"),
    )
    # Also remove orphan Call* anim helpers that steal exec
    for t in ("CallUnarmedAnims", "CallVikingAnims", "CallNinjaAnims", "CallAnimsForCurrentWeapon"):
        kill = []
        for n in list(ge.list_all_nodes()):
            if (n.get_node_title() or "") != t:
                continue
            # keep custom event defs; remove only if we're wiping apply — wipe all Call* events to unblock
            kill.append(n)
        if kill:
            ge.remove_nodes(kill)
            log(f"removed {t} x{len(kill)}")

    bel.compile_blueprint(eq)
    save(eq)
    eq = unreal.EditorAssetLibrary.load_asset(EQUIP)
    ge = unreal.BlueprintGraphEditor.get_graph_editor(bel.find_event_graph(eq))

    eva = ge.add_custom_event_node("ApplyWeaponVisual")
    g_eq = ge.add_get_member_variable_node("EquippedLimb")
    is_eq = add_call(ge, "/Script/Engine.KismetSystemLibrary.IsValid")
    br_eq = ge.add_branch_node()
    clr = add_call(ge, f"{EQUIP_CLS}.ClearWeaponVisual")
    g_eq2 = ge.add_get_member_variable_node("EquippedLimb")
    g_vik = ge.add_get_member_variable_node("VikingLimbAsset")
    eqo = add_call(ge, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject")
    br_v = ge.add_branch_node()

    connect(eva.find_then_pin(), br_eq.find_execute_pin(), "a-b")
    connect(g_eq.find_result_pin(), pin_in(is_eq, "Object"), "a-i")
    connect(is_eq.find_result_pin(), br_eq.find_condition_pin(), "a-?")
    connect(br_eq.find_else_pin(), clr.find_execute_pin(), "a-c")
    connect(br_eq.find_then_pin(), br_v.find_execute_pin(), "a-v")
    connect(g_eq2.find_result_pin(), pin_in(eqo, "A"), "A")
    connect(g_vik.find_result_pin(), pin_in(eqo, "B"), "B")
    connect(eqo.find_result_pin(), br_v.find_condition_pin(), "v?")

    cv = arm_spawn(ge, br_v.find_then_pin(), VIK_CLS, "v")
    cn = arm_spawn(ge, br_v.find_else_pin(), NIN_CLS, "n")
    pra = add_call(ge, "/Script/Engine.KismetSystemLibrary.PrintString")
    connect(cv.find_then_pin(), pra.find_execute_pin(), "pv")
    connect(cn.find_then_pin(), pra.find_execute_pin(), "pn")
    set_val(pin_in(pra, "InString", "In String"), "[Kalsiyum] Weapon visual applied", "ps")

    ok = bel.compile_blueprint(eq)
    errs = []
    try:
        errs = [e.get_node_title() for e in ge.list_nodes_with_errors()]
    except Exception:
        pass
    log(f"Apply compile={ok} errs={errs}")
    assert ok and not errs, errs
    save(eq)
    return unreal.EditorAssetLibrary.load_asset(EQUIP)


def rehook_drop_and_swap(eq):
    """OnArmDropped → DropWeaponToWorld if exists else Clear; OnArmReattached → Apply; Swap print → Apply."""
    bel = unreal.BlueprintEditorLibrary
    ge = unreal.BlueprintGraphEditor.get_graph_editor(bel.find_event_graph(eq))

    drop_fn = "DropWeaponToWorld"
    # probe
    probe = ge.add_call_function_node(f"{EQUIP_CLS}.{drop_fn}")
    if not probe:
        drop_fn = "ClearWeaponVisual"
        log("DropWeaponToWorld missing — use ClearWeaponVisual")
    else:
        ge.remove_nodes([probe])
        log("using DropWeaponToWorld on arm drop")

    def prepend_event(ename, fn):
        ev = next((n for n in ge.list_all_nodes() if n.get_node_title() == ename), None)
        if not ev:
            log(f"no {ename}")
            return
        # Remove existing call nodes of Clear/Drop/Apply on this event's immediate then
        then_p = ev.find_then_pin()
        old = None
        try:
            if hasattr(then_p, "get_linked_pins"):
                links = list(then_p.get_linked_pins() or [])
                if links:
                    old = links[0]
            then_p.break_all_pin_links()
        except Exception:
            pass
        c = add_call(ge, f"{EQUIP_CLS}.{fn}")
        connect(then_p, c.find_execute_pin(), f"{ename}→{fn}")
        if old and old.is_valid():
            # if old was a call we're replacing (Clear/Drop/Apply), skip chaining into it
            ot = old.get_node().get_node_title() if hasattr(old, "get_node") else ""
            if ot not in ("ClearWeaponVisual", "DropWeaponToWorld", "ApplyWeaponVisual", "CallUnarmedAnims"):
                try_connect(c.find_then_pin(), old, "chain-old")
        log(f"{ename}→{fn}")

    prepend_event("OnArmDropped", drop_fn)
    prepend_event("OnArmReattached", "ApplyWeaponVisual")

    # SwapLimb graph → Apply after success print
    g = bel.find_graph(eq, "SwapLimb")
    if g:
        te = unreal.BlueprintGraphEditor.get_graph_editor(g)
        kill = []
        for n in list(te.list_all_nodes()):
            if (n.get_node_title() or "") != "ApplyWeaponVisual":
                continue
            try:
                if n.find_self_pin() and n.find_self_pin().is_valid():
                    kill.append(n)
            except Exception:
                pass
        if kill:
            te.remove_nodes(kill)
        for prn in te.list_all_nodes():
            if "Print" not in (prn.get_node_title() or "") and "Yazdır" not in (prn.get_node_title() or ""):
                continue
            pin = pin_in(prn, "InString", "In String")
            val = ""
            try:
                val = pin.get_pin_value() if pin and hasattr(pin, "get_pin_value") else ""
            except Exception:
                val = ""
            if val and "Cannot" in val:
                continue
            then_p = prn.find_then_pin()
            try:
                then_p.break_all_pin_links()
            except Exception:
                pass
            c = add_call(te, f"{EQUIP_CLS}.ApplyWeaponVisual")
            connect(then_p, c.find_execute_pin(), "sw→apply")
            log("SwapLimb→ApplyWeaponVisual")
            break

    ok = bel.compile_blueprint(eq)
    assert ok, "hook compile"
    save(eq)


def restore_anims():
    """Put CDO Seq* back to stock mannequin attacks (user: anim changed)."""
    bel = unreal.BlueprintEditorLibrary
    bp = unreal.EditorAssetLibrary.load_asset(MELEE)
    if not bp:
        log("no melee")
        return
    names = list(bp.list_member_variable_names(False))
    if "SeqLight" not in names or "SeqHeavy" not in names:
        log("no SeqLight/Heavy — skip CDO (faz2 hardpaths may apply)")
        return
    gen = bel.generated_class(bp)
    cdo = unreal.get_default_object(gen)
    for prop, path in (("SeqLight", SEQ_LIGHT), ("SeqHeavy", SEQ_HEAVY)):
        asset = unreal.EditorAssetLibrary.load_asset(path)
        for pname in (prop, prop[0].lower() + prop[1:]):
            try:
                cdo.set_editor_property(pname, asset)
                log(f"CDO {prop}={path}")
                break
            except Exception:
                continue
    for pname in ("SwordPlayRate", "sword_play_rate"):
        try:
            cdo.set_editor_property(pname, 1.0)
            break
        except Exception:
            continue
    ok = bel.compile_blueprint(bp)
    log(f"melee anim CDO compile={ok}")
    if ok:
        save(bp)


def main():
    log("=== restore weapon + anims ===")
    restore_blade_meshes()
    eq = rebuild_apply()
    rehook_drop_and_swap(eq)
    restore_anims()
    log("DONE RESTORE WEAPON OK")
    log("PIE: expect [Kalsiyum] Weapon visual applied + visible blade; LMB stock attack anim")


if __name__ == "__main__":
    main()
