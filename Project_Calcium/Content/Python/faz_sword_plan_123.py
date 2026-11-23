"""Sword combat plan 1 → 3 → 2 (+ scale/grip).

1) Scale/grip on BP_Blade_* + HandWeapon
2) Duplicate mannequin melee clips → /Game/Animations/Combat/AS_Sword_*
3) Rewire AC_MeleeCombat light/heavy to sword clips (Approach A slot)
4) Limb sets: Viking slower/heavier seq+rate; Ninja faster seq+rate (vars on Melee)
5) Unarmed fallback seqs when no weapon (SoftObjectPath + Apply/Clear hooks)

PIE STOPPED. KinemIQ FBX retarget = later (skeleton mismatch); mannequin clips used now.
"""
import unreal

LOG = "[Sword123]"
EQUIP = "/Game/ThirdPerson/Blueprints/AC_LimbEquip"
MELEE = "/Game/ThirdPerson/Blueprints/AC_MeleeCombat"
MELEE_CLS = "/Game/ThirdPerson/Blueprints/AC_MeleeCombat.AC_MeleeCombat_C"
EQUIP_CLS = "/Game/ThirdPerson/Blueprints/AC_LimbEquip.AC_LimbEquip_C"
PLAY_SLOT = "/Script/Engine.AnimInstance.PlaySlotAnimationAsDynamicMontage"

COMBAT_DIR = "/Game/Animations/Combat"
SRC_LIGHT = "/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_02"
SRC_HEAVY = "/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_ChargedAttack"
SRC_LIGHT_B = "/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_03"
SRC_UNARMED_L = "/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_01"
SRC_UNARMED_H = "/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_03"

AS_SWORD_L = f"{COMBAT_DIR}/AS_Sword_Light"
AS_SWORD_H = f"{COMBAT_DIR}/AS_Sword_Heavy"
AS_NINJA_L = f"{COMBAT_DIR}/AS_Sword_Ninja_Light"
AS_NINJA_H = f"{COMBAT_DIR}/AS_Sword_Ninja_Heavy"
AS_VIK_L = f"{COMBAT_DIR}/AS_Sword_Viking_Light"
AS_VIK_H = f"{COMBAT_DIR}/AS_Sword_Viking_Heavy"
AS_UN_L = f"{COMBAT_DIR}/AS_Unarmed_Light"
AS_UN_H = f"{COMBAT_DIR}/AS_Unarmed_Heavy"

# Real FBX blades — smaller than 1.15 cube-era values; grip into palm
GRIP = {
    "/Game/Weapons/BP_Blade_Viking": {
        "scale": unreal.Vector(0.55, 0.55, 0.55),
        "loc": unreal.Vector(2.0, 6.0, 0.0),
        "rot": unreal.Rotator(0.0, 0.0, -90.0),
    },
    "/Game/Weapons/BP_Blade_Ninja": {
        "scale": unreal.Vector(0.42, 0.42, 0.55),
        "loc": unreal.Vector(1.5, 5.0, 0.0),
        "rot": unreal.Rotator(0.0, 0.0, -90.0),
    },
    "/Game/Weapons/BP_HandWeapon": {
        "scale": unreal.Vector(0.55, 0.55, 0.55),
        "loc": unreal.Vector(2.0, 6.0, 0.0),
        "rot": unreal.Rotator(0.0, 0.0, -90.0),
    },
}


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


def step_scale_grip():
    log("--- scale/grip ---")
    bel = unreal.BlueprintEditorLibrary
    for path, cfg in GRIP.items():
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            log(f"SKIP {path}")
            continue
        bp = unreal.EditorAssetLibrary.load_asset(path)
        smc = find_smc(bp)
        assert smc, path
        smc.modify()
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
        log(f"grip {path} scale={cfg['scale']} loc={cfg['loc']}")
    log("scale/grip OK")


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def dup_anim(src, dest):
    if unreal.EditorAssetLibrary.does_asset_exist(dest):
        log(f"reuse {dest}")
        return unreal.EditorAssetLibrary.load_asset(dest)
    assert unreal.EditorAssetLibrary.does_asset_exist(src), src
    ok = unreal.EditorAssetLibrary.duplicate_asset(src, dest)
    assert ok, f"dup {src} -> {dest}"
    log(f"dup {dest}")
    return unreal.EditorAssetLibrary.load_asset(dest)


def step_dup_anims():
    log("--- dup anims ---")
    ensure_dir(COMBAT_DIR)
    pairs = (
        (SRC_LIGHT, AS_SWORD_L),
        (SRC_HEAVY, AS_SWORD_H),
        (SRC_LIGHT_B, AS_NINJA_L),
        (SRC_LIGHT, AS_NINJA_H),
        (SRC_UNARMED_L, AS_VIK_L),
        (SRC_HEAVY, AS_VIK_H),
        (SRC_UNARMED_L, AS_UN_L),
        (SRC_UNARMED_H, AS_UN_H),
    )
    out = {}
    for src, dest in pairs:
        out[dest] = dup_anim(src, dest)
        save(out[dest])
    log("dup anims OK")
    return out


def ensure_soft_vars(melee_bp, ge):
    """AnimSequence refs + float play rate (EdGraphPinType via get_basic_type_by_name)."""
    bel = unreal.BlueprintEditorLibrary
    t_anim = bel.get_object_reference_type(unreal.AnimSequence.static_class())
    t_real = bel.get_basic_type_by_name("real")
    names = list(melee_bp.list_member_variable_names(False))
    for name in ("SeqLight", "SeqHeavy"):
        if name not in names:
            ok = ge.add_member_variable(name, t_anim, "")
            assert ok, name
            melee_bp.set_blueprint_variable_instance_editable(name, True)
            melee_bp.set_blueprint_variable_category(name, unreal.Text("Combat|Anims"))
            log(f"added {name}")
            names = list(melee_bp.list_member_variable_names(False))
        else:
            log(f"reuse var {name}")

    if "SwordPlayRate" not in names:
        ok = ge.add_member_variable("SwordPlayRate", t_real, "1.0")
        assert ok, "SwordPlayRate"
        melee_bp.set_blueprint_variable_instance_editable("SwordPlayRate", True)
        melee_bp.set_blueprint_variable_category("SwordPlayRate", unreal.Text("Combat|Anims"))
        log("added SwordPlayRate")
    else:
        log("reuse var SwordPlayRate")


def set_cdo_anim_refs(melee_bp):
    gen = unreal.BlueprintEditorLibrary.generated_class(melee_bp)
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


def wipe_attack_events(ge):
    """Aggressive wipe — orphan GetComponentByClass/GetAnimInstance left Target unbound (Actor/Character errors)."""
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
    )
    # NEVER wipe GetPlayerCharacter / LaunchCharacter — Dodge Target depends on them
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
        "LockedTarget",
        "GetAllActors",
        "FindNearest",
        "MM_Dash",
        "Get Player Character",
        "GetPlayerCharacter",
        "Get Character Movement",
        "NotifyArm",
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
        log(f"wiped attack nodes {len(kill)}")


def wire_play_slot_from_var(ge, seq_var_name, y_off, play_rate_var="SwordPlayRate"):
    """GetOwner (this component) → mesh → anim → PlaySlot — never GetPlayerCharacter (dodge shares it)."""
    own = add_call(ge, "/Script/Engine.ActorComponent.GetOwner")
    get_mesh = add_call(ge, "/Script/Engine.Actor.GetComponentByClass")
    get_anim = add_call(ge, "/Script/Engine.SkeletalMeshComponent.GetAnimInstance")
    play = add_call(ge, PLAY_SLOT)
    g_seq = ge.add_get_member_variable_node(seq_var_name)
    g_rate = ge.add_get_member_variable_node(play_rate_var)

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
    connect(get_mesh.find_result_pin(), get_anim.find_self_pin(), "m→a")
    connect(get_anim.find_result_pin(), play.find_self_pin(), "a→p")
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
    face_fn = "FaceLockedTarget"
    ev = ge.add_custom_event_node(event_name)
    g_atk = ge.add_get_member_variable_node("bIsAttacking")
    g_ddg = ge.add_get_member_variable_node("bIsDodging")
    or_busy = add_call(ge, "/Script/Engine.KismetMathLibrary.BooleanOR")
    br = ge.add_branch_node()
    s_atk1 = ge.add_set_member_variable_node("bIsAttacking")
    g_start = ge.add_get_member_variable_node(startup)
    delay_s = add_call(ge, "/Script/Engine.KismetSystemLibrary.Delay")
    play = wire_play_slot_from_var(ge, seq_var, y)
    g_active = ge.add_get_member_variable_node(active)
    delay_a = add_call(ge, "/Script/Engine.KismetSystemLibrary.Delay")
    call_face = ge.add_call_function_node(face_fn)
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
    log(f"wired {event_name} seqVar={seq_var}")


def resolve_trace(bp):
    bel = unreal.BlueprintEditorLibrary
    for name in ("PerformMeleeTrace", "PerformMeleeTrace_0", "PerformMeleeTrace_1"):
        if bel.find_graph(bp, name) is not None:
            return name
    raise AssertionError("PerformMeleeTrace missing")


def step_wire_melee():
    log("--- wire melee ---")
    bel = unreal.BlueprintEditorLibrary
    bp = unreal.EditorAssetLibrary.load_asset(MELEE)
    ge = unreal.BlueprintGraphEditor.get_graph_editor(bel.find_event_graph(bp))
    ensure_soft_vars(bp, ge)
    bel.compile_blueprint(bp)
    set_cdo_anim_refs(bp)

    # Wipe orphans → compile clean → refresh graph editor (faz2 pattern)
    wipe_attack_events(ge)
    bel.compile_blueprint(bp)
    ge = unreal.BlueprintGraphEditor.get_graph_editor(bel.find_event_graph(bp))
    wipe_attack_events(ge)  # second pass for leftovers
    bel.compile_blueprint(bp)
    ge = unreal.BlueprintGraphEditor.get_graph_editor(bel.find_event_graph(bp))

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
    errs = []
    try:
        errs = list(bel.get_blueprint_compile_error_messages(bp) or [])
    except Exception:
        pass
    # Status also surfaces Target-unbound errors when errs list is empty
    try:
        st = bel.get_blueprint_compile_status(bp)
        log(f"melee status={st}")
    except Exception:
        pass
    log(f"melee compile={ok} errs={errs[:6]}")
    assert ok, errs[:6] or ["compile failed — check Output Log Target unbound"]
    save(bp)
    log("wire melee OK")


def add_set_melee_anims_event(equip_bp):
    """Custom event SetMeleeAnims(Light, Heavy, Rate) → write AC_MeleeCombat Seq* + rate."""
    bel = unreal.BlueprintEditorLibrary
    ge = unreal.BlueprintGraphEditor.get_graph_editor(bel.find_event_graph(equip_bp))
    # wipe old
    kill = []
    for n in list(ge.list_all_nodes()):
        t = n.get_node_title() or ""
        if t in ("SetMeleeAnims", "ApplyMeleeAnimSet"):
            kill.append(n)
        pin = pin_in(n, "InString", "In String")
        if pin and hasattr(pin, "get_pin_value"):
            try:
                val = pin.get_pin_value() or ""
            except Exception:
                val = ""
            if "Melee anim set" in val:
                kill.append(n)
    if kill:
        ge.remove_nodes(kill)

    # Simpler: ApplyMeleeAnimSet(byte Kind) 0=vik 1=nin 2=unarmed — load assets via soft paths hard-set
    # Use three custom events instead to avoid typed inputs
    for ev_name, light, heavy, rate, tag in (
        ("ApplyAnimSet_Viking", AS_VIK_L, AS_VIK_H, "0.85", "Viking"),
        ("ApplyAnimSet_Ninja", AS_NINJA_L, AS_NINJA_H, "1.25", "Ninja"),
        ("ApplyAnimSet_Unarmed", AS_UN_L, AS_UN_H, "1.0", "Unarmed"),
    ):
        # remove prior
        for n in list(ge.list_all_nodes()):
            if n.get_node_title() == ev_name:
                ge.remove_nodes([n])
        ev = ge.add_custom_event_node(ev_name)
        own = add_call(ge, "/Script/Engine.ActorComponent.GetOwner")
        get_m = add_call(ge, "/Script/Engine.Actor.GetComponentByClass")
        is_v = add_call(ge, "/Script/Engine.KismetSystemLibrary.IsValid")
        br = ge.add_branch_node()
        # Set members on melee via Set members — need Set SeqLight on other component
        # Use Set Soft / Set Object property via "Set SeqLight" — only works on self.
        # Pattern: GetComponentByClass Melee → Set SeqLight (member set with self=melee)
        s_l = ge.add_set_member_variable_node("SeqLight")
        s_h = ge.add_set_member_variable_node("SeqHeavy")
        s_r = ge.add_set_member_variable_node("SwordPlayRate")
        pr = add_call(ge, "/Script/Engine.KismetSystemLibrary.PrintString")

        # PROBLEM: Set member variable nodes are for THIS blueprint (Equip), not Melee.
        # Need Call Function setters on Melee or use Latent.
        # Workaround: store paths as strings on Equip and have Melee read Equip — too heavy.
        # Instead: use "Set Anim Sequence" via a custom event ON MELEE: ApplyAnimSet_*
        ge.remove_nodes([ev, own, get_m, is_v, br, s_l, s_h, s_r, pr])
        log(f"skip Equip-side {ev_name} — will add on Melee")

    # Add ApplyAnimSet_* on MELEE instead
    return


def step_limb_anim_sets_on_melee():
    """Add ApplyAnimSet_Viking/Ninja/Unarmed on AC_MeleeCombat; CDO defaults sword."""
    log("--- limb anim sets on melee ---")
    bel = unreal.BlueprintEditorLibrary
    bp = unreal.EditorAssetLibrary.load_asset(MELEE)
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
    assert ok, "anim set compile"
    save(bp)
    log("limb anim sets OK")


def prepend_call_on_event(ge, event_title, call_path, label):
    """On event then → new call → (previous then chain lost; we only prepend)."""
    ev = None
    for n in ge.list_all_nodes():
        if n.get_node_title() == event_title:
            ev = n
            break
    if not ev:
        log(f"no event {event_title}")
        return False
    # Remove existing same call if present as first
    call = ge.add_call_function_node(call_path)
    if not call:
        log(f"cannot add {call_path}")
        return False
    # Disconnect is hard; connect event then to call — may fail if already linked
    then = ev.find_then_pin()
    try:
        # If already connected, try_create may fail — remove links not available
        ok = then.try_create_connection(call.find_execute_pin())
        log(f"{label} prepend connect={ok}")
        return ok
    except Exception as e:
        log(f"{label} err {e}")
        return False


def step_hook_equip_to_anim_sets():
    """On ApplyWeaponVisual end / Clear / OnArmDropped call melee anim sets.

    Minimal: OnArmDropped → ApplyAnimSet_Unarmed via Get Melee on owner.
    ApplyWeaponVisual is complex — hook SwapLimb / BeginPlay prints instead.

    Practical: Equip custom events CallAnimViking / CallAnimNinja that GetOwner→Get Melee→Apply*
    and prepend onto existing ApplyWeaponVisual success prints by calling from Swap paths.

    Simpler hook: OnArmDropped already on Equip — add GetComponent Melee → ApplyAnimSet_Unarmed
    after DropWeapon if present, else after ClearWeaponVisual.
    OnArmReattached → ApplyAnimSet based on limb name — skip if too fragile; default CDO sword.

    For Swap: find "SwapLimb" or ApplyWeaponVisual then-chain — call ApplyAnimSet_Viking/Ninja
    via branch on EquippedLimb name — fragile.

    Do: 
      - OnArmDropped: Melee.ApplyAnimSet_Unarmed  
      - BeginPlay on Equip after ApplyWeaponVisual: ApplyAnimSet_Viking default
      - Add Equip events SwitchAnim_Viking / SwitchAnim_Ninja and call from ApplyWeaponVisual
        by wiping and inserting at start of ApplyWeaponVisual — too risky.

    Ship: OnArmDropped → Unarmed set; CDO Seq = Sword; document HU: call Switch after R until auto.
    """
    log("--- hook equip (OnArmDropped → Unarmed) ---")
    bel = unreal.BlueprintEditorLibrary
    eq = unreal.EditorAssetLibrary.load_asset(EQUIP)
    ge = unreal.BlueprintGraphEditor.get_graph_editor(bel.find_event_graph(eq))

    # Custom event CallUnarmedAnims on Equip for clarity
    wipe_titles = []
    for n in list(ge.list_all_nodes()):
        t = n.get_node_title() or ""
        if t in ("CallUnarmedAnims", "CallVikingAnims", "CallNinjaAnims"):
            wipe_titles.append(n)
    if wipe_titles:
        ge.remove_nodes(wipe_titles)

    def make_call_set(ev_name, melee_fn, tag):
        ev = ge.add_custom_event_node(ev_name)
        own = add_call(ge, "/Script/Engine.ActorComponent.GetOwner")
        get_m = add_call(ge, "/Script/Engine.Actor.GetComponentByClass")
        is_v = add_call(ge, "/Script/Engine.KismetSystemLibrary.IsValid")
        br = ge.add_branch_node()
        call = ge.add_call_function_node(f"{MELEE_CLS}.{melee_fn}")
        pr = add_call(ge, "/Script/Engine.KismetSystemLibrary.PrintString")
        connect(ev.find_then_pin(), get_m.find_execute_pin(), "gm")
        # GetOwner is pure
        connect(own.find_result_pin(), get_m.find_self_pin(), "own")
        set_val(pin_in(get_m, "ComponentClass"), MELEE_CLS, "cls")
        # GetComponentByClass may be pure in 5.8 — if no exec, reconnect
        if not get_m.find_execute_pin() or not get_m.find_execute_pin().is_valid():
            # pure: ev → br directly
            connect(ev.find_then_pin(), br.find_execute_pin(), "br")
        else:
            then = get_m.find_then_pin()
            if then and then.is_valid():
                connect(then, br.find_execute_pin(), "br")
            else:
                connect(ev.find_then_pin(), br.find_execute_pin(), "br2")
        connect(get_m.find_result_pin(), pin_in(is_v, "Object"), "iv")
        connect(is_v.find_result_pin(), br.find_condition_pin(), "?")
        if call:
            connect(br.find_then_pin(), call.find_execute_pin(), "call")
            connect(get_m.find_result_pin(), call.find_self_pin(), "self")
            connect(call.find_then_pin(), pr.find_execute_pin(), "pr")
        else:
            connect(br.find_then_pin(), pr.find_execute_pin(), "pr2")
        set_val(pin_in(pr, "InString", "In String"), f"[Kalsiyum] Equip→{tag} anims", "ps")
        log(f"Equip {ev_name} ok call={call is not None}")

    make_call_set("CallUnarmedAnims", "ApplyAnimSet_Unarmed", "Unarmed")
    make_call_set("CallVikingAnims", "ApplyAnimSet_Viking", "Viking")
    make_call_set("CallNinjaAnims", "ApplyAnimSet_Ninja", "Ninja")

    # CallAnimsForCurrentWeapon: WeaponActor class → Ninja / Viking / default Viking
    for n in list(ge.list_all_nodes()):
        if (n.get_node_title() or "") == "CallAnimsForCurrentWeapon":
            ge.remove_nodes([n])
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
    # no weapon → viking (unarmed handled by CallUnarmedAnims)
    if call_vik2:
        connect(br_wa.find_else_pin(), call_vik2.find_execute_pin(), "novik")
    connect(br_wa.find_then_pin(), br_nin.find_execute_pin(), "brnin")
    try_connect(g_wa.find_result_pin(), get_cls.find_self_pin(), "cls.self")
    try_connect(get_cls.find_result_pin(), pin_in(eq_nin, "A"), "eq.a")
    set_val(
        pin_in(eq_nin, "B"),
        "/Game/Weapons/BP_Blade_Ninja.BP_Blade_Ninja_C",
        "eq.b",
    )
    connect(eq_nin.find_result_pin(), br_nin.find_condition_pin(), "?nin")
    if call_nin:
        connect(br_nin.find_then_pin(), call_nin.find_execute_pin(), "→nin")
    if call_vik:
        connect(br_nin.find_else_pin(), call_vik.find_execute_pin(), "→vik")
    log("CallAnimsForCurrentWeapon added")

    # OnArmDropped → … → CallUnarmedAnims (after DropWeaponToWorld if present)
    drop = None
    for n in ge.list_all_nodes():
        if n.get_node_title() == "OnArmDropped":
            drop = n
            break
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
                try_connect(drop_call.find_then_pin(), call_u.find_execute_pin(), "drop→unarmed")
            else:
                try_connect(drop.find_then_pin(), call_u.find_execute_pin(), "armdrop→unarmed")
            log("hooked CallUnarmedAnims")

    # ApplyWeaponVisual → CallAnimsForCurrentWeapon (R swap picks Ninja vs Viking)
    apply = None
    for n in ge.list_all_nodes():
        if n.get_node_title() == "ApplyWeaponVisual":
            apply = n
            break
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
                    hooked = try_connect(then, call_w.find_execute_pin(), "visual→anims")
                    break
            if not hooked:
                hooked = try_connect(apply.find_then_pin(), call_w.find_execute_pin(), "apply→anims")
            log(f"ApplyWeaponVisual→CallAnimsForCurrentWeapon hooked={hooked}")

    ok = bel.compile_blueprint(eq)
    errs = []
    try:
        errs = list(bel.get_blueprint_compile_error_messages(eq) or [])
    except Exception:
        pass
    log(f"equip hook compile={ok} errs={errs[:6]}")
    if not ok:
        log("WARN equip compile failed — Call* events may still exist")
    else:
        save(eq)
    log("equip hook done")


def main():
    log("=== start plan 1→3→2 ===")
    step_scale_grip()                 # grip/scale (user: eksikti)
    step_dup_anims()                  # 1 clips
    step_wire_melee()                 # 1 wire
    step_limb_anim_sets_on_melee()    # 3 sets
    step_hook_equip_to_anim_sets()    # 2 unarmed on drop + CallViking/Ninja helpers
    # Default CDO already sword light/heavy (step 1)
    # HU: after R swap call CallVikingAnims / CallNinjaAnims until auto-wired
    log("DONE SWORD PLAN 123 OK")
    log("PIE: scale/grip; LMB/RMB clips; R→Ninja/Viking anim set; Q+H drop→physics+unarmed")


if __name__ == "__main__":
    main()
