"""Restore attack anims: fail-open arm gate + play slot immediately (before delays)."""
import unreal

LOG = "[AnimRestore]"
MELEE = "/Game/ThirdPerson/Blueprints/AC_MeleeCombat"
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
    assert pin.set_pin_value(value), label


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
        "startup→", "no RightArm", "Attack blocked",
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


def wire_play_slot(ge, seq, y):
    get_char = ge.add_call_function_node("/Script/Engine.GameplayStatics.GetPlayerCharacter")
    get_mesh = ge.add_call_function_node("/Script/Engine.Actor.GetComponentByClass")
    get_anim = ge.add_call_function_node("/Script/Engine.SkeletalMeshComponent.GetAnimInstance")
    play = ge.add_call_function_node(PLAY_SLOT)
    assert play and get_mesh and get_anim
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
    play.set_node_pos(unreal.IntPoint(900, y))
    return play


def main():
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

        # Soft arm gate: only block if LimbSocket IS valid AND HasRightArm == false
        own = ge.add_call_function_node("/Script/Engine.ActorComponent.GetOwner")
        get_limb = ge.add_call_function_node("/Script/Engine.Actor.GetComponentByClass")
        is_valid = ge.add_call_function_node("/Script/Engine.KismetSystemLibrary.IsValid")
        br_valid = ge.add_branch_node()
        has = ge.add_call_function_node(HAS_ARM)
        br_arm = ge.add_branch_node()
        print_no = ge.add_call_function_node("/Script/Engine.KismetSystemLibrary.PrintString")

        g_atk = ge.add_get_member_variable_node("bIsAttacking")
        g_ddg = ge.add_get_member_variable_node("bIsDodging")
        or_busy = ge.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanOR")
        br_busy = ge.add_branch_node()
        s_atk1 = ge.add_set_member_variable_node("bIsAttacking")
        play = wire_play_slot(ge, seq, y)
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

        # Layout
        for node, x in (
            (ev, 0), (br_valid, 220), (br_arm, 420), (br_busy, 640), (s_atk1, 840),
            (play, 1040), (delay_s, 1280), (delay_a, 1500), (call_face, 1720),
            (call_tr, 1940), (delay_hs, 2160), (set_dil, 2380), (delay_cd, 2600), (s_atk0, 2820),
        ):
            node.set_node_pos(unreal.IntPoint(x, y))

        # Soft gate
        connect(ev.find_then_pin(), br_valid.find_execute_pin(), "ev")
        connect(own.find_result_pin(), get_limb.find_self_pin(), "own")
        set_val(get_limb.find_input_pin("ComponentClass"), LIMB_CLS, "limbcls")
        connect(get_limb.find_result_pin(), is_valid.find_input_pin("Object"), "limb->iv")
        connect(is_valid.find_result_pin(), br_valid.find_condition_pin(), "iv?")
        # limb INVALID → skip arm check, go busy (fail-open — anims work)
        connect(br_valid.find_else_pin(), br_busy.find_execute_pin(), "noLimb->busy")
        # limb VALID → HasRightArm
        connect(br_valid.find_then_pin(), br_arm.find_execute_pin(), "hasLimb")
        connect(get_limb.find_result_pin(), has.find_self_pin(), "limb->has")
        connect(has.find_result_pin(), br_arm.find_condition_pin(), "arm?")
        connect(br_arm.find_then_pin(), br_busy.find_execute_pin(), "armOK->busy")
        connect(br_arm.find_else_pin(), print_no.find_execute_pin(), "noarm")
        set_val(print_no.find_input_pin("InString"), "[Kalsiyum] Attack blocked: no RightArm", "noarmstr")

        # Busy / attack — PLAY ANIM FIRST, then startup+active delays, then trace
        connect(g_atk.find_result_pin(), or_busy.find_input_pin("A"), "atk")
        connect(g_ddg.find_result_pin(), or_busy.find_input_pin("B"), "ddg")
        connect(or_busy.find_result_pin(), br_busy.find_condition_pin(), "or")
        connect(br_busy.find_else_pin(), s_atk1.find_execute_pin(), "go")
        set_val(s_atk1.find_input_pin("bIsAttacking"), "true", "atk1")
        connect(s_atk1.find_then_pin(), play.find_execute_pin(), "->play NOW")
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

        ge.add_comment_to_nodes(
            f"AnimRestore {label}: play slot FIRST → delays → trace (arm fail-open)",
            [ev, play, call_tr],
            40,
        )
        log(f"rewired {event_name}")

    wire("TriggerLightAttack", "LightDamage", "LightCooldown", "LightStartup", "LightActive", "Light", seq_l, 0)
    wire("TriggerHeavyAttack", "HeavyDamage", "HeavyCooldown", "HeavyStartup", "HeavyActive", "Heavy", seq_h, 520)

    ok = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    errs = ge.list_nodes_with_errors()
    log(f"compiled={ok} errs={len(errs)}")
    for e in errs:
        log(f"ERR {e.get_node_title()}")
    assert ok and len(errs) == 0
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)

    char = unreal.EditorAssetLibrary.load_asset("/Game/ThirdPerson/Blueprints/BP_TP_Kalsiyum")
    okc = unreal.BlueprintEditorLibrary.compile_blueprint(char)
    log(f"char compiled={okc}")
    assert okc
    unreal.EditorAssetLibrary.save_loaded_asset(char, only_if_is_dirty=False)
    log("DONE ANIM RESTORED")


if __name__ == "__main__":
    main()
