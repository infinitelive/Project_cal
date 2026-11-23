"""Restore AC_MeleeCombat compile + sword attacks with GetOwner (not GetPlayerCharacter).

Root cause: wipe deleted GetPlayerCharacter used by Dodge → Character/Actor Target unbound.
Wire attacks via ActorComponent.GetOwner → SkeletalMesh → AnimInstance → PlaySlot(Seq*).

Also recompiles BP_TP_Kalsiyum. Then limb anim sets + equip hooks.

PIE STOPPED.
  py "C:/kalsiyum_ue/Content/Python/fix_melee_compile.py"
"""
import unreal

LOG = "[FixMelee]"
MELEE = "/Game/ThirdPerson/Blueprints/AC_MeleeCombat"
CHAR = "/Game/ThirdPerson/Blueprints/BP_TP_Kalsiyum"
MELEE_CLS = "/Game/ThirdPerson/Blueprints/AC_MeleeCombat.AC_MeleeCombat_C"
EQUIP = "/Game/ThirdPerson/Blueprints/AC_LimbEquip"
EQUIP_CLS = "/Game/ThirdPerson/Blueprints/AC_LimbEquip.AC_LimbEquip_C"
PLAY_SLOT = "/Script/Engine.AnimInstance.PlaySlotAnimationAsDynamicMontage"

AS_SWORD_L = "/Game/Animations/Combat/AS_Sword_Light"
AS_SWORD_H = "/Game/Animations/Combat/AS_Sword_Heavy"
AS_NINJA_L = "/Game/Animations/Combat/AS_Sword_Ninja_Light"
AS_NINJA_H = "/Game/Animations/Combat/AS_Sword_Ninja_Heavy"
AS_VIK_L = "/Game/Animations/Combat/AS_Sword_Viking_Light"
AS_VIK_H = "/Game/Animations/Combat/AS_Sword_Viking_Heavy"
AS_UN_L = "/Game/Animations/Combat/AS_Unarmed_Light"
AS_UN_H = "/Game/Animations/Combat/AS_Unarmed_Heavy"


def log(m):
    unreal.log(f"{LOG} {m}")


def connect(a, b, label):
    assert a and a.is_valid() and b and b.is_valid(), f"{label} pins"
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


def resolve_trace(bp):
    bel = unreal.BlueprintEditorLibrary
    for name in ("PerformMeleeTrace", "PerformMeleeTrace_0", "PerformMeleeTrace_1"):
        if bel.find_graph(bp, name) is not None:
            return name
    raise AssertionError("PerformMeleeTrace missing")


def remove_error_nodes(ge):
    try:
        errs = list(ge.list_nodes_with_errors() or [])
    except Exception:
        errs = []
    if errs:
        titles = [n.get_node_title() for n in errs]
        log(f"error nodes: {titles[:20]}")
        # Prefer repair LaunchCharacter / GetComponentByClass over delete (dodge)
        keep = []
        drop = []
        for n in errs:
            t = n.get_node_title() or ""
            if any(x in t for x in ("LaunchCharacter", "Launch Character", "Get Character Movement", "Character Movement")):
                keep.append(n)
            else:
                drop.append(n)
        if drop:
            ge.remove_nodes(drop)
            log(f"removed error nodes {len(drop)}")
        if keep:
            repair_character_targets(ge, keep)


def repair_character_targets(ge, bad_nodes):
    """Reattach GetPlayerCharacter → Character Target on dodge nodes."""
    get_char = add_call(ge, "/Script/Engine.GameplayStatics.GetPlayerCharacter")
    set_val(pin_in(get_char, "PlayerIndex"), "0", "pc")
    for n in bad_nodes:
        self_pin = None
        try:
            self_pin = n.find_self_pin()
        except Exception:
            pass
        if self_pin and self_pin.is_valid():
            ok = try_connect(get_char.find_result_pin(), self_pin, f"repair→{n.get_node_title()}")
            log(f"repair Character Target on '{n.get_node_title()}' ok={ok}")
        # Also Actor GetComponentByClass if present among bad
        if "Component" in (n.get_node_title() or ""):
            try_connect(get_char.find_result_pin(), n.find_self_pin(), "repair→comp")


def clear_attack_only(ge):
    """Wipe attack chains only — PROTECT dodge/lock GetPlayerCharacter/LaunchCharacter."""
    markers = (
        "TriggerLightAttack",
        "TriggerHeavyAttack",
        "PlaySlotAnimationAsDynamicMontage",
        "Play Slot Animation",
        "SeqLight",
        "SeqHeavy",
        "SwordPlayRate",
        "LightStartup",
        "HeavyStartup",
        "LightActive",
        "HeavyActive",
        "LightDamage",
        "HeavyDamage",
        "LightCooldown",
        "HeavyCooldown",
        "HitStopDuration",
        "bIsAttacking",
        "SetGlobalTimeDilation",
        "Set Global Time Dilation",
        "PerformMeleeTrace",
        "Perform Melee Trace",
        "FaceLockedTarget",
        "[Kalsiyum] Light",
        "[Kalsiyum] Heavy",
        "[Kalsiyum] Melee anim set",
        "ApplyAnimSet_Viking",
        "ApplyAnimSet_Ninja",
        "ApplyAnimSet_Unarmed",
        "BooleanOR",
        "Boolean OR",
        "Approach A",
        "startup→",
    )
    protect = (
        "TriggerDodge",
        "ToggleLockOn",
        "ReceiveTick",
        "Olay Tick",
        "BeginPlay",
        "ReceiveBeginPlay",
        "LaunchCharacter",
        "bIsDodging",
        "DodgeImpulse",
        "DodgeIFrame",
        "DodgeRecovery",
        "LockedTarget",
        "GetAllActors",
        "FindNearest",
        "MM_Dash",
        "Get Player Character",
        "GetPlayerCharacter",
        "Get Character Movement",
        "Character Movement",
        "NotifyArm",
        "bArmDetached",
        "GetDamageMult",
        "GetAttackSpeedMult",
        "Mood",
    )
    kill = []
    for n in list(ge.list_all_nodes()):
        t = n.get_node_title() or ""
        if any(p in t for p in protect):
            continue
        if any(m in t for m in markers):
            kill.append(n)
    if kill:
        ge.remove_nodes(kill)
        log(f"wiped attack-only {len(kill)}")


def ensure_seq_vars(bp, ge):
    bel = unreal.BlueprintEditorLibrary
    t_anim = bel.get_object_reference_type(unreal.AnimSequence.static_class())
    t_real = bel.get_basic_type_by_name("real")
    names = list(bp.list_member_variable_names(False))
    for name, typ, default in (
        ("SeqLight", t_anim, ""),
        ("SeqHeavy", t_anim, ""),
        ("SwordPlayRate", t_real, "1.0"),
    ):
        if name not in names:
            assert ge.add_member_variable(name, typ, default), name
            bp.set_blueprint_variable_instance_editable(name, True)
            bp.set_blueprint_variable_category(name, unreal.Text("Combat|Anims"))
            log(f"added {name}")
        else:
            log(f"reuse {name}")


def set_cdo_seqs(bp):
    gen = unreal.BlueprintEditorLibrary.generated_class(bp)
    cdo = unreal.get_default_object(gen)
    for prop, path in (("SeqLight", AS_SWORD_L), ("SeqHeavy", AS_SWORD_H)):
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


def wire_play_slot(ge, seq_var, y_off):
    """GetOwner (component) → GetComponentByClass(SKM) → GetAnimInstance → PlaySlot."""
    own = add_call(ge, "/Script/Engine.ActorComponent.GetOwner")
    get_mesh = add_call(ge, "/Script/Engine.Actor.GetComponentByClass")
    get_anim = add_call(ge, "/Script/Engine.SkeletalMeshComponent.GetAnimInstance")
    play = add_call(ge, PLAY_SLOT)
    g_seq = ge.add_get_member_variable_node(seq_var)
    g_rate = ge.add_get_member_variable_node("SwordPlayRate")

    connect(own.find_result_pin(), get_mesh.find_self_pin(), "own→mesh")
    cls_pin = pin_in(get_mesh, "ComponentClass")
    ok_cls = False
    for cand in (
        "/Script/Engine.SkeletalMeshComponent",
        "SkeletalMeshComponent",
        "Class'/Script/Engine.SkeletalMeshComponent'",
    ):
        try:
            if cls_pin and cls_pin.set_pin_value(cand):
                ok_cls = True
                break
        except Exception:
            pass
    assert ok_cls, "ComponentClass"
    connect(get_mesh.find_result_pin(), get_anim.find_self_pin(), "mesh→anim")
    connect(get_anim.find_result_pin(), play.find_self_pin(), "anim→play")
    connect(g_seq.find_result_pin(), pin_in(play, "Asset"), "seq")
    set_val(pin_in(play, "SlotNodeName"), "DefaultSlot", "slot")
    rate_pin = pin_in(play, "InPlayRate", "PlayRate")
    if rate_pin and g_rate:
        if not g_rate.find_result_pin().try_create_connection(rate_pin):
            set_val(rate_pin, "1.0", "rate")
    for pname, pval in (
        ("BlendInTime", "0.1"),
        ("BlendOutTime", "0.2"),
        ("LoopCount", "1"),
        ("BlendOutTriggerTime", "-1.0"),
    ):
        p = pin_in(play, pname)
        if p:
            try:
                set_val(p, pval, pname)
            except Exception:
                pass
    try:
        own.set_node_pos(unreal.IntPoint(700, y_off + 180))
        get_mesh.set_node_pos(unreal.IntPoint(920, y_off + 180))
        play.set_node_pos(unreal.IntPoint(960, y_off))
    except Exception:
        pass
    return play


def wire_attack(ge, trace_fn, event_name, dmg, cd, startup, active, label, seq_var, y):
    ev = ge.add_custom_event_node(event_name)
    g_atk = ge.add_get_member_variable_node("bIsAttacking")
    g_ddg = ge.add_get_member_variable_node("bIsDodging")
    or_busy = add_call(ge, "/Script/Engine.KismetMathLibrary.BooleanOR")
    br = ge.add_branch_node()
    s_atk1 = ge.add_set_member_variable_node("bIsAttacking")
    g_start = ge.add_get_member_variable_node(startup)
    delay_s = add_call(ge, "/Script/Engine.KismetSystemLibrary.Delay")
    play = wire_play_slot(ge, seq_var, y)
    g_active = ge.add_get_member_variable_node(active)
    delay_a = add_call(ge, "/Script/Engine.KismetSystemLibrary.Delay")
    call_face = ge.add_call_function_node("FaceLockedTarget")
    assert call_face, "FaceLockedTarget"
    g_dmg = ge.add_get_member_variable_node(dmg)
    call_tr = ge.add_call_function_node(trace_fn)
    assert call_tr, trace_fn
    g_hs = ge.add_get_member_variable_node("HitStopDuration")
    delay_hs = add_call(ge, "/Script/Engine.KismetSystemLibrary.Delay")
    set_dil1 = add_call(ge, "/Script/Engine.GameplayStatics.SetGlobalTimeDilation")
    g_cd = ge.add_get_member_variable_node(cd)
    delay_cd = add_call(ge, "/Script/Engine.KismetSystemLibrary.Delay")
    s_atk0 = ge.add_set_member_variable_node("bIsAttacking")

    connect(ev.find_then_pin(), br.find_execute_pin(), "ev")
    connect(g_atk.find_result_pin(), pin_in(or_busy, "A"), "atk")
    connect(g_ddg.find_result_pin(), pin_in(or_busy, "B"), "ddg")
    connect(or_busy.find_result_pin(), br.find_condition_pin(), "or")
    connect(br.find_else_pin(), s_atk1.find_execute_pin(), "go")
    set_val(pin_in(s_atk1, "bIsAttacking"), "true", "a1")
    connect(s_atk1.find_then_pin(), delay_s.find_execute_pin(), "st")
    connect(g_start.find_result_pin(), pin_in(delay_s, "Duration"), "sd")
    connect(delay_s.find_then_pin(), play.find_execute_pin(), "play")
    then_pin = play.find_then_pin()
    assert then_pin and then_pin.is_valid(), "play then"
    connect(then_pin, delay_a.find_execute_pin(), "act")
    connect(g_active.find_result_pin(), pin_in(delay_a, "Duration"), "ad")
    connect(delay_a.find_then_pin(), call_face.find_execute_pin(), "face")
    connect(call_face.find_then_pin(), call_tr.find_execute_pin(), "tr")
    connect(g_dmg.find_result_pin(), pin_in(call_tr, "DamageAmount"), "dmg")
    set_val(pin_in(call_tr, "AttackLabel"), f"[Kalsiyum] {label}", "lbl")
    connect(call_tr.find_then_pin(), delay_hs.find_execute_pin(), "hs")
    connect(g_hs.find_result_pin(), pin_in(delay_hs, "Duration"), "hsd")
    connect(delay_hs.find_then_pin(), set_dil1.find_execute_pin(), "dil")
    set_val(pin_in(set_dil1, "TimeDilation"), "1.0", "dilv")
    connect(set_dil1.find_then_pin(), delay_cd.find_execute_pin(), "cd")
    connect(g_cd.find_result_pin(), pin_in(delay_cd, "Duration"), "cdd")
    connect(delay_cd.find_then_pin(), s_atk0.find_execute_pin(), "done")
    set_val(pin_in(s_atk0, "bIsAttacking"), "false", "a0")
    log(f"wired {event_name}")


def add_anim_sets(bp):
    bel = unreal.BlueprintEditorLibrary
    ge = unreal.BlueprintGraphEditor.get_graph_editor(bel.find_event_graph(bp))
    for ev_name, light, heavy, rate, tag in (
        ("ApplyAnimSet_Viking", AS_VIK_L, AS_VIK_H, "0.85", "Viking"),
        ("ApplyAnimSet_Ninja", AS_NINJA_L, AS_NINJA_H, "1.25", "Ninja"),
        ("ApplyAnimSet_Unarmed", AS_UN_L, AS_UN_H, "1.0", "Unarmed"),
    ):
        kill = [n for n in list(ge.list_all_nodes()) if (n.get_node_title() or "") == ev_name]
        if kill:
            ge.remove_nodes(kill)
        ev = ge.add_custom_event_node(ev_name)
        s_l = ge.add_set_member_variable_node("SeqLight")
        s_h = ge.add_set_member_variable_node("SeqHeavy")
        s_r = ge.add_set_member_variable_node("SwordPlayRate")
        pr = add_call(ge, "/Script/Engine.KismetSystemLibrary.PrintString")
        connect(ev.find_then_pin(), s_l.find_execute_pin(), "l")
        set_val(pin_in(s_l, "SeqLight"), light, "lv")
        connect(s_l.find_then_pin(), s_h.find_execute_pin(), "h")
        set_val(pin_in(s_h, "SeqHeavy"), heavy, "hv")
        connect(s_h.find_then_pin(), s_r.find_execute_pin(), "r")
        set_val(pin_in(s_r, "SwordPlayRate"), rate, "rv")
        connect(s_r.find_then_pin(), pr.find_execute_pin(), "p")
        set_val(pin_in(pr, "InString", "In String"), f"[Kalsiyum] Melee anim set {tag}", "ps")
        log(f"added {ev_name}")
    ok = bel.compile_blueprint(bp)
    assert ok, "anim sets compile"
    save(bp)


def hook_equip():
    """CallUnarmed/Viking/Ninja + CallAnimsForCurrentWeapon; chain OnArmDropped / ApplyWeaponVisual."""
    bel = unreal.BlueprintEditorLibrary
    eq = unreal.EditorAssetLibrary.load_asset(EQUIP)
    ge = unreal.BlueprintGraphEditor.get_graph_editor(bel.find_event_graph(eq))

    for t in ("CallUnarmedAnims", "CallVikingAnims", "CallNinjaAnims", "CallAnimsForCurrentWeapon"):
        kill = [n for n in list(ge.list_all_nodes()) if (n.get_node_title() or "") == t]
        if kill:
            ge.remove_nodes(kill)

    def make_call_set(ev_name, melee_fn, tag):
        ev = ge.add_custom_event_node(ev_name)
        own = add_call(ge, "/Script/Engine.ActorComponent.GetOwner")
        get_m = add_call(ge, "/Script/Engine.Actor.GetComponentByClass")
        is_v = add_call(ge, "/Script/Engine.KismetSystemLibrary.IsValid")
        br = ge.add_branch_node()
        call = ge.add_call_function_node(f"{MELEE_CLS}.{melee_fn}")
        pr = add_call(ge, "/Script/Engine.KismetSystemLibrary.PrintString")
        connect(own.find_result_pin(), get_m.find_self_pin(), "own")
        set_val(pin_in(get_m, "ComponentClass"), MELEE_CLS, "cls")
        if get_m.find_execute_pin() and get_m.find_execute_pin().is_valid():
            connect(ev.find_then_pin(), get_m.find_execute_pin(), "gm")
            then = get_m.find_then_pin()
            if then and then.is_valid():
                connect(then, br.find_execute_pin(), "br")
            else:
                connect(ev.find_then_pin(), br.find_execute_pin(), "br2")
        else:
            connect(ev.find_then_pin(), br.find_execute_pin(), "br")
        connect(get_m.find_result_pin(), pin_in(is_v, "Object"), "iv")
        connect(is_v.find_result_pin(), br.find_condition_pin(), "?")
        if call:
            connect(br.find_then_pin(), call.find_execute_pin(), "call")
            connect(get_m.find_result_pin(), call.find_self_pin(), "self")
            connect(call.find_then_pin(), pr.find_execute_pin(), "pr")
        else:
            connect(br.find_then_pin(), pr.find_execute_pin(), "pr2")
        set_val(pin_in(pr, "InString", "In String"), f"[Kalsiyum] Equip→{tag} anims", "ps")
        log(f"Equip {ev_name}")

    make_call_set("CallUnarmedAnims", "ApplyAnimSet_Unarmed", "Unarmed")
    make_call_set("CallVikingAnims", "ApplyAnimSet_Viking", "Viking")
    make_call_set("CallNinjaAnims", "ApplyAnimSet_Ninja", "Ninja")

    # CallAnimsForCurrentWeapon
    ev_w = ge.add_custom_event_node("CallAnimsForCurrentWeapon")
    g_wa = ge.add_get_member_variable_node("WeaponActor")
    is_wa = add_call(ge, "/Script/Engine.KismetSystemLibrary.IsValid")
    br_wa = ge.add_branch_node()
    get_cls = add_call(ge, "/Script/CoreUObject.Object.GetClass")
    eq_nin = add_call(ge, "/Script/Engine.KismetMathLibrary.EqualEqual_ClassClass")
    br_nin = ge.add_branch_node()
    call_nin = ge.add_call_function_node(f"{EQUIP_CLS}.CallNinjaAnims")
    call_vik = ge.add_call_function_node(f"{EQUIP_CLS}.CallVikingAnims")
    call_vik2 = ge.add_call_function_node(f"{EQUIP_CLS}.CallVikingAnims")
    connect(ev_w.find_then_pin(), br_wa.find_execute_pin(), "brwa")
    connect(g_wa.find_result_pin(), pin_in(is_wa, "Object"), "iswa")
    connect(is_wa.find_result_pin(), br_wa.find_condition_pin(), "?wa")
    if call_vik2:
        connect(br_wa.find_else_pin(), call_vik2.find_execute_pin(), "novik")
    connect(br_wa.find_then_pin(), br_nin.find_execute_pin(), "brnin")
    try_connect(g_wa.find_result_pin(), get_cls.find_self_pin(), "cls.self")
    try_connect(get_cls.find_result_pin(), pin_in(eq_nin, "A"), "eq.a")
    set_val(pin_in(eq_nin, "B"), "/Game/Weapons/BP_Blade_Ninja.BP_Blade_Ninja_C", "eq.b")
    connect(eq_nin.find_result_pin(), br_nin.find_condition_pin(), "?nin")
    if call_nin:
        connect(br_nin.find_then_pin(), call_nin.find_execute_pin(), "→nin")
    if call_vik:
        connect(br_nin.find_else_pin(), call_vik.find_execute_pin(), "→vik")

    # Hook OnArmDropped → CallUnarmed after DropWeaponToWorld
    drop = next((n for n in ge.list_all_nodes() if n.get_node_title() == "OnArmDropped"), None)
    if drop:
        call_u = ge.add_call_function_node(f"{EQUIP_CLS}.CallUnarmedAnims")
        if call_u:
            drop_call = None
            for n in ge.list_all_nodes():
                if (n.get_node_title() or "") != "DropWeaponToWorld":
                    continue
                try:
                    if n.find_self_pin() and n.find_self_pin().is_valid():
                        drop_call = n
                except Exception:
                    pass
            if drop_call and drop_call.find_then_pin():
                try_connect(drop_call.find_then_pin(), call_u.find_execute_pin(), "drop→u")
            else:
                try_connect(drop.find_then_pin(), call_u.find_execute_pin(), "arm→u")

    apply = next((n for n in ge.list_all_nodes() if n.get_node_title() == "ApplyWeaponVisual"), None)
    if apply:
        call_w = ge.add_call_function_node(f"{EQUIP_CLS}.CallAnimsForCurrentWeapon")
        if call_w:
            hooked = False
            for n in ge.list_all_nodes():
                pin = pin_in(n, "InString", "In String")
                if not pin:
                    continue
                try:
                    val = pin.get_pin_value() or ""
                except Exception:
                    val = ""
                if "Weapon visual" not in val:
                    continue
                then = n.find_then_pin()
                if then and then.is_valid():
                    hooked = try_connect(then, call_w.find_execute_pin(), "vis→anim")
                    break
            if not hooked:
                try_connect(apply.find_then_pin(), call_w.find_execute_pin(), "app→anim")

    ok = bel.compile_blueprint(eq)
    errs = []
    try:
        errs = list(bel.get_blueprint_compile_error_messages(eq) or [])
    except Exception:
        pass
    log(f"equip compile={ok} errs={errs[:6]}")
    if ok:
        save(eq)


def main():
    log("=== restore melee (GetOwner) + hooks ===")
    bel = unreal.BlueprintEditorLibrary
    bp = unreal.EditorAssetLibrary.load_asset(MELEE)
    ge = unreal.BlueprintGraphEditor.get_graph_editor(bel.find_event_graph(bp))

    ensure_seq_vars(bp, ge)
    bel.compile_blueprint(bp)
    set_cdo_seqs(bp)

    # Remove compiler-flagged nodes first (broken Target leftovers)
    remove_error_nodes(ge)
    clear_attack_only(ge)
    bel.compile_blueprint(bp)
    ge = unreal.BlueprintGraphEditor.get_graph_editor(bel.find_event_graph(bp))
    remove_error_nodes(ge)
    clear_attack_only(ge)

    # If still errors, log them
    try:
        for n in list(ge.list_nodes_with_errors() or []):
            log(f"STILL ERR: {n.get_node_title()}")
    except Exception:
        pass

    bel.compile_blueprint(bp)
    ge = unreal.BlueprintGraphEditor.get_graph_editor(bel.find_event_graph(bp))
    remove_error_nodes(ge)

    trace = resolve_trace(bp)
    wire_attack(
        ge, trace, "TriggerLightAttack", "LightDamage", "LightCooldown",
        "LightStartup", "LightActive", "Light", "SeqLight", 0,
    )
    wire_attack(
        ge, trace, "TriggerHeavyAttack", "HeavyDamage", "HeavyCooldown",
        "HeavyStartup", "HeavyActive", "Heavy", "SeqHeavy", 400,
    )

    ok = bel.compile_blueprint(bp)
    try:
        for n in list(ge.list_nodes_with_errors() or []):
            log(f"POST ERR: {n.get_node_title()}")
    except Exception:
        pass
    log(f"melee compile={ok}")
    assert ok, "melee still broken — check POST ERR titles"
    save(bp)

    # Character must refresh TriggerLight/Heavy call sites
    char = unreal.EditorAssetLibrary.load_asset(CHAR)
    ok_c = bel.compile_blueprint(char)
    log(f"char compile={ok_c}")
    if ok_c:
        save(char)

    add_anim_sets(bp)
    hook_equip()
    log("DONE FIX MELEE COMPILE OK")


if __name__ == "__main__":
    main()
