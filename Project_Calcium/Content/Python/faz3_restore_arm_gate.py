"""Restore HasRightArm attack gate + ensure arm starts true on BeginPlay."""
import unreal

LOG = "[ArmGate]"
MELEE = "/Game/ThirdPerson/Blueprints/AC_MeleeCombat"
LIMB = "/Game/ThirdPerson/Blueprints/AC_LimbSocket"
CHAR = "/Game/ThirdPerson/Blueprints/BP_TP_Kalsiyum"
HAS_ARM = "/Game/ThirdPerson/Blueprints/AC_LimbSocket.AC_LimbSocket_C.HasRightArm"
LIMB_CLS = "/Game/ThirdPerson/Blueprints/AC_LimbSocket.AC_LimbSocket_C"
SEQ_LIGHT = "/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_01"
SEQ_HEAVY = "/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_ChargedAttack"
PLAY_SLOT = "/Script/Engine.AnimInstance.PlaySlotAnimationAsDynamicMontage"


def log(m):
    unreal.log(f"{LOG} {m}")


def connect(a, b, label):
    assert a and a.is_valid() and b and b.is_valid(), label
    assert a.try_create_connection(b), label


def set_val(pin, value, label):
    assert pin and pin.is_valid(), label
    assert pin.set_pin_value(value), f"{label}={value}"


def resolve_trace(bp):
    for n in ("PerformMeleeTrace_0", "PerformMeleeTrace", "PerformMeleeTrace_1"):
        if unreal.BlueprintEditorLibrary.find_graph(bp, n):
            return n
    raise AssertionError("no trace")


def clear_attacks(ge):
    markers = (
        "TriggerLightAttack", "TriggerHeavyAttack", "LightDamage", "HeavyDamage",
        "LightCooldown", "HeavyCooldown", "LightStartup", "HeavyStartup", "LightActive",
        "HeavyActive", "bIsAttacking", "PerformMeleeTrace", "Perform Melee Trace",
        "PlaySlotAnimation", "Play Slot Animation", "PlayAnimMontage", "MM_Attack",
        "ChargedAttack", "HasRightArm", "Faz 2 [CU]", "Faz 3 [CU]", "AnimRestore",
        "startup→", "no RightArm", "Attack blocked", "StartPunch", "ArmGate",
    )
    protect = (
        "TriggerDodge", "ToggleLockOn", "ReceiveTick", "Olay Tick", "FaceLocked",
        "LockedTarget", "LaunchCharacter", "bIsDodging", "bIsInvulnerable",
        "DodgeImpulse", "DodgeIFrame", "DodgeRecovery", "LockOnRadius",
        "Get Player Character", "GetPlayerCharacter",
    )
    kill = []
    for n in list(ge.list_all_nodes()):
        t = n.get_node_title()
        if any(p in t for p in protect):
            continue
        if any(m in t for m in markers):
            kill.append(n)
    if kill:
        ge.remove_nodes(kill)
        log(f"removed {len(kill)}")


def wire_play(ge, seq, y):
    get_char = ge.add_call_function_node("/Script/Engine.GameplayStatics.GetPlayerCharacter")
    get_mesh = ge.add_call_function_node("/Script/Engine.Actor.GetComponentByClass")
    get_anim = ge.add_call_function_node("/Script/Engine.SkeletalMeshComponent.GetAnimInstance")
    play = ge.add_call_function_node(PLAY_SLOT)
    set_val(get_char.find_input_pin("PlayerIndex"), "0", "pc")
    connect(get_char.find_result_pin(), get_mesh.find_self_pin(), "c->m")
    set_val(get_mesh.find_input_pin("ComponentClass"), "/Script/Engine.SkeletalMeshComponent", "cls")
    connect(get_mesh.find_result_pin(), get_anim.find_self_pin(), "m->a")
    connect(get_anim.find_result_pin(), play.find_self_pin(), "a->p")
    set_val(play.find_input_pin("Asset"), seq.get_path_name(), "asset")
    set_val(play.find_input_pin("SlotNodeName"), "DefaultSlot", "slot")
    for pn, pv in (("BlendInTime", "0.05"), ("BlendOutTime", "0.15"), ("InPlayRate", "1.0"), ("LoopCount", "1")):
        p = play.find_input_pin(pn)
        if p and p.is_valid():
            try:
                set_val(p, pv, pn)
            except Exception:
                pass
    play.set_node_pos(unreal.IntPoint(1100, y))
    return play


def rebuild_melee():
    bp = unreal.EditorAssetLibrary.load_asset(MELEE)
    ge = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(bp)
    )
    clear_attacks(ge)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    ge = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(bp)
    )
    clear_attacks(ge)

    trace_fn = resolve_trace(bp)
    face_fn = "FaceLockedTarget"
    seq_l = unreal.EditorAssetLibrary.load_asset(SEQ_LIGHT)
    seq_h = unreal.EditorAssetLibrary.load_asset(SEQ_HEAVY)

    def wire(event_name, dmg, cd, startup, active, label, seq, y):
        ev = ge.add_custom_event_node(event_name)

        # Gate: no LimbSocket → fail-open (punch). LimbSocket + !HasRightArm → block.
        # Root fix for first PIE: also treat "HasRightArm call fails" as open via IsValid only on component.
        own = ge.add_call_function_node("/Script/Engine.ActorComponent.GetOwner")
        get_limb = ge.add_call_function_node("/Script/Engine.Actor.GetComponentByClass")
        is_valid = ge.add_call_function_node("/Script/Engine.KismetSystemLibrary.IsValid")
        br_valid = ge.add_branch_node()
        # Read bool DIRECTLY via get member on cast — HasRightArm function can be flaky;
        # use HasRightArm call which returns bHasRightArm (default true on CDO).
        has = ge.add_call_function_node(HAS_ARM)
        br_arm = ge.add_branch_node()
        print_no = ge.add_call_function_node("/Script/Engine.KismetSystemLibrary.PrintString")

        g_atk = ge.add_get_member_variable_node("bIsAttacking")
        g_ddg = ge.add_get_member_variable_node("bIsDodging")
        or_busy = ge.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanOR")
        br_busy = ge.add_branch_node()
        s_atk1 = ge.add_set_member_variable_node("bIsAttacking")
        play = wire_play(ge, seq, y)
        g_start = ge.add_get_member_variable_node(startup)
        delay_s = ge.add_call_function_node("/Script/Engine.KismetSystemLibrary.Delay")
        g_act = ge.add_get_member_variable_node(active)
        delay_a = ge.add_call_function_node("/Script/Engine.KismetSystemLibrary.Delay")
        call_face = ge.add_call_function_node(face_fn)
        g_dmg = ge.add_get_member_variable_node(dmg)
        call_tr = ge.add_call_function_node(trace_fn)
        g_hs = ge.add_get_member_variable_node("HitStopDuration")
        delay_hs = ge.add_call_function_node("/Script/Engine.KismetSystemLibrary.Delay")
        set_dil = ge.add_call_function_node("/Script/Engine.GameplayStatics.SetGlobalTimeDilation")
        g_cd = ge.add_get_member_variable_node(cd)
        delay_cd = ge.add_call_function_node("/Script/Engine.KismetSystemLibrary.Delay")
        s_atk0 = ge.add_set_member_variable_node("bIsAttacking")

        for node, x in (
            (ev, 0), (br_valid, 200), (br_arm, 400), (br_busy, 600), (s_atk1, 800),
            (play, 1000), (delay_s, 1250), (delay_a, 1450), (call_face, 1650),
            (call_tr, 1850), (delay_hs, 2050), (set_dil, 2250), (delay_cd, 2450), (s_atk0, 2650),
        ):
            node.set_node_pos(unreal.IntPoint(x, y))

        connect(ev.find_then_pin(), br_valid.find_execute_pin(), "ev")
        connect(own.find_result_pin(), get_limb.find_self_pin(), "own")
        set_val(get_limb.find_input_pin("ComponentClass"), LIMB_CLS, "limbcls")
        connect(get_limb.find_result_pin(), is_valid.find_input_pin("Object"), "limb->iv")
        connect(is_valid.find_result_pin(), br_valid.find_condition_pin(), "iv?")
        # no limb → punch (fail-open)
        connect(br_valid.find_else_pin(), br_busy.find_execute_pin(), "noLimb")
        # has limb → check arm
        connect(br_valid.find_then_pin(), br_arm.find_execute_pin(), "hasLimb")
        connect(get_limb.find_result_pin(), has.find_self_pin(), "limb->has")
        connect(has.find_result_pin(), br_arm.find_condition_pin(), "arm?")
        connect(br_arm.find_then_pin(), br_busy.find_execute_pin(), "armOK")
        connect(br_arm.find_else_pin(), print_no.find_execute_pin(), "noarm")
        set_val(print_no.find_input_pin("InString"), "[Kalsiyum] Attack blocked: no RightArm", "msg")

        connect(g_atk.find_result_pin(), or_busy.find_input_pin("A"), "atk")
        connect(g_ddg.find_result_pin(), or_busy.find_input_pin("B"), "ddg")
        connect(or_busy.find_result_pin(), br_busy.find_condition_pin(), "or")
        connect(br_busy.find_else_pin(), s_atk1.find_execute_pin(), "go")
        set_val(s_atk1.find_input_pin("bIsAttacking"), "true", "atk1")
        connect(s_atk1.find_then_pin(), play.find_execute_pin(), "play")
        connect(play.find_then_pin(), delay_s.find_execute_pin(), "startup")
        connect(g_start.find_result_pin(), delay_s.find_input_pin("Duration"), "sd")
        connect(delay_s.find_then_pin(), delay_a.find_execute_pin(), "active")
        connect(g_act.find_result_pin(), delay_a.find_input_pin("Duration"), "ad")
        connect(delay_a.find_then_pin(), call_face.find_execute_pin(), "face")
        connect(call_face.find_then_pin(), call_tr.find_execute_pin(), "tr")
        connect(g_dmg.find_result_pin(), call_tr.find_input_pin("DamageAmount"), "dmg")
        set_val(call_tr.find_input_pin("AttackLabel"), f"[Kalsiyum] {label}", "lbl")
        connect(call_tr.find_then_pin(), delay_hs.find_execute_pin(), "hs")
        connect(g_hs.find_result_pin(), delay_hs.find_input_pin("Duration"), "hsd")
        connect(delay_hs.find_then_pin(), set_dil.find_execute_pin(), "dil")
        set_val(set_dil.find_input_pin("TimeDilation"), "1.0", "dil1")
        connect(set_dil.find_then_pin(), delay_cd.find_execute_pin(), "cd")
        connect(g_cd.find_result_pin(), delay_cd.find_input_pin("Duration"), "cdd")
        connect(delay_cd.find_then_pin(), s_atk0.find_execute_pin(), "done")
        set_val(s_atk0.find_input_pin("bIsAttacking"), "false", "atk0")
        log(f"rewired {event_name} WITH arm gate")

    wire("TriggerLightAttack", "LightDamage", "LightCooldown", "LightStartup", "LightActive", "Light", seq_l, 0)
    wire("TriggerHeavyAttack", "HeavyDamage", "HeavyCooldown", "HeavyStartup", "HeavyActive", "Heavy", seq_h, 520)

    ok = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    errs = list(ge.list_nodes_with_errors())
    log(f"melee compiled={ok} errs={[e.get_node_title() for e in errs]}")
    assert ok and not errs
    unreal.EditorAssetLibrary.save_loaded_asset(bp)


def ensure_limb_begin_play_arm_true():
    """On LimbSocket BeginPlay: force bHasRightArm=true so first PIE can punch."""
    bp = unreal.EditorAssetLibrary.load_asset(LIMB)
    # Event graph may be empty — add ReceiveBeginPlay if possible
    eg = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    ge = unreal.BlueprintGraphEditor.get_graph_editor(eg)

    # Remove prior ArmGate beginplay nodes
    kill = []
    for n in list(ge.list_all_nodes()):
        t = n.get_node_title()
        if "ArmGate" in t or "BeginPlay" in t or "Olay BeginPlay" in t or "bHasRightArm" in t:
            kill.append(n)
    # Only kill if we're rebuilding beginplay — be careful with empty graph
    # For component BP, use add_event_node / add_override
    begin = None
    for meth, arg in (
        ("add_event_node", "ReceiveBeginPlay"),
        ("add_override_event_node", "ReceiveBeginPlay"),
        ("add_custom_event_node", "ArmGate_BeginPlay"),
    ):
        if hasattr(ge, meth):
            try:
                begin = getattr(ge, meth)(arg)
                if begin:
                    log(f"begin via {meth}")
                    break
            except Exception as e:
                log(f"{meth} {e}")

    if not begin:
        # Event graph empty and no API — set CDO only
        cdo = unreal.get_default_object(bp.generated_class())
        cdo.set_editor_property("bHasRightArm", True)
        log("no BeginPlay API — CDO forced true")
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_loaded_asset(bp)
        return

    # clear other non-begin nodes we may have created earlier? keep simple
    s_arm = ge.add_set_member_variable_node("bHasRightArm")
    connect(begin.find_then_pin(), s_arm.find_execute_pin(), "bp->arm")
    set_val(s_arm.find_input_pin("bHasRightArm"), "true", "armT")
    cdo = unreal.get_default_object(bp.generated_class())
    cdo.set_editor_property("bHasRightArm", True)
    ok = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    log(f"limb beginplay compiled={ok} CDO={cdo.get_editor_property('bHasRightArm')}")
    unreal.EditorAssetLibrary.save_loaded_asset(bp)


def fix_char_calls():
    """Ensure TriggerLight/Heavy still wired from IA_."""
    mbp = unreal.EditorAssetLibrary.load_asset(MELEE)
    unreal.BlueprintEditorLibrary.compile_blueprint(mbp)
    bp = unreal.EditorAssetLibrary.load_asset(CHAR)
    ge = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(bp)
    )
    # if already has Trigger calls without errors, done
    errs = list(ge.list_nodes_with_errors())
    if not errs:
        titles = [n.get_node_title() for n in ge.list_all_nodes()]
        if "TriggerLightAttack" in titles and "TriggerHeavyAttack" in titles:
            log("char calls OK")
            unreal.BlueprintEditorLibrary.compile_blueprint(bp)
            unreal.EditorAssetLibrary.save_loaded_asset(bp)
            return

    # minimal refresh: remove error trigger nodes, re-add
    kill = [e for e in errs]
    for n in list(ge.list_all_nodes()):
        t = n.get_node_title()
        if t in ("TriggerLightAttack", "TriggerHeavyAttack"):
            kill.append(n)
    if kill:
        ge.remove_nodes(list(set(kill)))

    light_ia = heavy_ia = None
    melee_get = None
    for n in ge.list_all_nodes():
        t = n.get_node_title()
        if "IA_LightAttack" in t:
            light_ia = n
        if "IA_HeavyAttack" in t:
            heavy_ia = n
        if "AC_MeleeCombat" in t and melee_get is None:
            melee_get = n

    def wire_ia(ia, fn, y):
        call = ge.add_call_function_node(
            f"/Game/ThirdPerson/Blueprints/AC_MeleeCombat.AC_MeleeCombat_C.{fn}"
        )
        assert call and ia and melee_get
        then = None
        if hasattr(ia, "find_output_pin"):
            for pn in ("Triggered", "Started"):
                p = ia.find_output_pin(pn)
                if p and p.is_valid():
                    then = p
                    break
        if not then:
            then = ia.find_then_pin()
        connect(then, call.find_execute_pin(), fn)
        connect(melee_get.find_result_pin(), call.find_self_pin(), f"{fn}self")
        call.set_node_pos(unreal.IntPoint(600, y))

    wire_ia(light_ia, "TriggerLightAttack", 0)
    wire_ia(heavy_ia, "TriggerHeavyAttack", 400)
    ok = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    errs2 = [e.get_node_title() for e in ge.list_nodes_with_errors()]
    log(f"char compiled={ok} errs={errs2}")
    assert ok and not errs2
    unreal.EditorAssetLibrary.save_loaded_asset(mbp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp)


def main():
    rebuild_melee()
    ensure_limb_begin_play_arm_true()
    fix_char_calls()
    log("DONE ARM GATE RESTORED")


if __name__ == "__main__":
    main()
