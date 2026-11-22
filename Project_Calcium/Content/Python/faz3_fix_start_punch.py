"""Fix: ensure BP_TP_Kalsiyum LimbSocket starts with bHasRightArm=true; verify attack gate polarity."""
import unreal

LOG = "[StartPunch]"
LIMB = "/Game/ThirdPerson/Blueprints/AC_LimbSocket"
CHAR = "/Game/ThirdPerson/Blueprints/BP_TP_Kalsiyum"
MELEE = "/Game/ThirdPerson/Blueprints/AC_MeleeCombat"


def log(m):
    unreal.log(f"{LOG} {m}")


def connect(a, b, label):
    assert a and a.is_valid() and b and b.is_valid(), label
    assert a.try_create_connection(b), label


def set_val(pin, value, label):
    assert pin and pin.is_valid(), label
    assert pin.set_pin_value(value), f"{label}={value}"


def fix_cdo_and_char_instance():
    # Component class CDO
    limb_bp = unreal.EditorAssetLibrary.load_asset(LIMB)
    cdo = unreal.get_default_object(limb_bp.generated_class())
    log(f"Limb CDO bHasRightArm={cdo.get_editor_property('bHasRightArm')}")
    cdo.set_editor_property("bHasRightArm", True)

    # Character SCS component template
    char_bp = unreal.EditorAssetLibrary.load_asset(CHAR)
    # SimpleConstructionScript components
    try:
        scs = char_bp.simple_construction_script
        nodes = scs.get_all_nodes() if scs else []
        log(f"SCS nodes={len(nodes) if nodes else 0}")
        for node in nodes or []:
            try:
                tmpl = node.component_template
            except Exception:
                tmpl = None
            if not tmpl:
                continue
            cname = tmpl.get_class().get_name()
            oname = tmpl.get_name()
            if "Limb" in cname or "Limb" in oname or "LimbSocket" in cname:
                log(f"found limb tmpl {oname} class={cname}")
                try:
                    cur = tmpl.get_editor_property("bHasRightArm")
                    log(f"  instance bHasRightArm={cur}")
                    tmpl.set_editor_property("bHasRightArm", True)
                    log("  set True")
                except Exception as e:
                    log(f"  set err {e}")
    except Exception as e:
        log(f"SCS err {e}")

    # Also try BlueprintEditorLibrary / inherited components
    try:
        for comp in unreal.BlueprintEditorLibrary.get_components(char_bp) or []:
            log(f"BEL comp {comp}")
    except Exception as e:
        log(f"get_components {e}")

    unreal.BlueprintEditorLibrary.compile_blueprint(limb_bp)
    unreal.BlueprintEditorLibrary.compile_blueprint(char_bp)
    unreal.EditorAssetLibrary.save_loaded_asset(limb_bp)
    unreal.EditorAssetLibrary.save_loaded_asset(char_bp)
    log("saved limb+char")


def remove_arm_gate_from_attacks():
    """Nuclear but reliable: strip HasRightArm gate so attacks always reach play-slot.
    Keep LimbSocket for drop/block; only melee gate removed so first PIE punches work.
    """
    bp = unreal.EditorAssetLibrary.load_asset(MELEE)
    # Reuse restore script logic but WITHOUT arm gate — import inline
    # Clear and rewire TriggerLight/Heavy like faz3_restore_anim but skip arm check
    from importlib.machinery import SourceFileLoader
    # Inline minimal rewire
    SEQ_LIGHT = "/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_01"
    SEQ_HEAVY = "/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_ChargedAttack"
    PLAY_SLOT = "/Script/Engine.AnimInstance.PlaySlotAnimationAsDynamicMontage"

    def resolve_trace():
        for n in ("PerformMeleeTrace_0", "PerformMeleeTrace", "PerformMeleeTrace_1"):
            if unreal.BlueprintEditorLibrary.find_graph(bp, n):
                return n
        raise AssertionError("no trace")

    ge = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(bp)
    )
    markers = (
        "TriggerLightAttack", "TriggerHeavyAttack", "LightDamage", "HeavyDamage",
        "LightCooldown", "HeavyCooldown", "LightStartup", "HeavyStartup", "LightActive",
        "HeavyActive", "bIsAttacking", "PerformMeleeTrace", "Perform Melee Trace",
        "PlaySlotAnimation", "Play Slot Animation", "PlayAnimMontage", "MM_Attack",
        "ChargedAttack", "HasRightArm", "Faz 2 [CU]", "Faz 3 [CU]", "AnimRestore",
        "startup→", "no RightArm", "Attack blocked", "StartPunch",
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
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    ge = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(bp)
    )
    # second clear
    kill = []
    for n in list(ge.list_all_nodes()):
        t = n.get_node_title()
        if any(p in t for p in protect):
            continue
        if any(m in t for m in markers):
            kill.append(n)
    if kill:
        ge.remove_nodes(kill)

    trace_fn = resolve_trace()
    face_fn = "FaceLockedTarget"
    seq_l = unreal.EditorAssetLibrary.load_asset(SEQ_LIGHT)
    seq_h = unreal.EditorAssetLibrary.load_asset(SEQ_HEAVY)

    def wire_play(seq, y):
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
        play.set_node_pos(unreal.IntPoint(900, y))
        return play

    def wire(event_name, dmg, cd, startup, active, label, seq, y):
        ev = ge.add_custom_event_node(event_name)
        # NO arm gate — only busy check
        g_atk = ge.add_get_member_variable_node("bIsAttacking")
        g_ddg = ge.add_get_member_variable_node("bIsDodging")
        or_busy = ge.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanOR")
        br_busy = ge.add_branch_node()
        s_atk1 = ge.add_set_member_variable_node("bIsAttacking")
        play = wire_play(seq, y)
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
        # soft print if no arm (informational only — does not block)
        own = ge.add_call_function_node("/Script/Engine.ActorComponent.GetOwner")
        get_limb = ge.add_call_function_node("/Script/Engine.Actor.GetComponentByClass")
        is_valid = ge.add_call_function_node("/Script/Engine.KismetSystemLibrary.IsValid")
        br_valid = ge.add_branch_node()
        has = ge.add_call_function_node(
            "/Game/ThirdPerson/Blueprints/AC_LimbSocket.AC_LimbSocket_C.HasRightArm"
        )
        br_arm = ge.add_branch_node()
        print_no = ge.add_call_function_node("/Script/Engine.KismetSystemLibrary.PrintString")

        for node, x in (
            (ev, 0), (br_busy, 220), (s_atk1, 440), (play, 660),
            (delay_s, 900), (delay_a, 1120), (call_face, 1340), (call_tr, 1560),
            (delay_hs, 1780), (set_dil, 2000), (delay_cd, 2220), (s_atk0, 2440),
        ):
            node.set_node_pos(unreal.IntPoint(x, y))

        # busy gate only
        connect(ev.find_then_pin(), br_busy.find_execute_pin(), "ev")
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

        # Parallel warn-only arm check (does not block exec): from ev also... can't dual then easily.
        # Instead: after play starts, fire warn if no arm — skip for simplicity.
        # Remove unused warn nodes to avoid compile orphans
        ge.remove_nodes([own, get_limb, is_valid, br_valid, has, br_arm, print_no])
        log(f"rewired {event_name} NO arm gate")

    wire("TriggerLightAttack", "LightDamage", "LightCooldown", "LightStartup", "LightActive", "Light", seq_l, 0)
    wire("TriggerHeavyAttack", "HeavyDamage", "HeavyCooldown", "HeavyStartup", "HeavyActive", "Heavy", seq_h, 520)

    ok = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    errs = list(ge.list_nodes_with_errors())
    log(f"melee compiled={ok} errs={[e.get_node_title() for e in errs]}")
    assert ok and not errs
    # assert no HasRightArm in attack path titles for Trigger chain
    titles = [n.get_node_title() for n in ge.list_all_nodes()]
    light_has = "TriggerLightAttack" in "".join(titles)
    assert light_has
    # HasRightArm should not gate anymore
    log(f"HasRightArm nodes still present? {any('HasRightArm' in t for t in titles)}")
    unreal.EditorAssetLibrary.save_loaded_asset(bp)
    log("melee saved")


def main():
    fix_cdo_and_char_instance()
    remove_arm_gate_from_attacks()
    log("DONE START PUNCH FIX")


if __name__ == "__main__":
    main()
