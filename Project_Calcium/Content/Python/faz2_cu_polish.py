"""Faz 2 [CU] — retune AC_MeleeCombat + hit-stop/punch + startup/montage attacks."""
import unreal

LOG = "[Faz2CU]"
COMP = "/Game/ThirdPerson/Blueprints/AC_MeleeCombat"
CHAR = "/Game/ThirdPerson/Blueprints/BP_TP_Kalsiyum"
MM_LIGHT = "/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_01"
MM_HEAVY = "/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_ChargedAttack"


def log(msg: str) -> None:
    unreal.log(f"{LOG} {msg}")


def connect(out_pin, in_pin, label: str) -> None:
    assert out_pin is not None and out_pin.is_valid() and in_pin is not None and in_pin.is_valid(), label
    assert out_pin.try_create_connection(in_pin), label


def set_val(pin, value: str, label: str) -> None:
    assert pin is not None and pin.is_valid(), label
    assert pin.set_pin_value(value), label


def ensure_var(bp, ge, name, pin_type, default_val, editable=True, category="Combat|Tuning"):
    existing = list(bp.list_member_variable_names(False))
    if name not in existing:
        assert ge.add_member_variable(name, pin_type, default_val), name
        log(f"Added var {name}={default_val}")
    else:
        log(f"Keep existing var {name} (wanted default {default_val})")
    if editable:
        bp.set_blueprint_variable_instance_editable(name, True)
    if category:
        bp.set_blueprint_variable_category(name, unreal.Text(category))


def retune_defaults(bp, ge) -> None:
    t_real = unreal.BlueprintEditorLibrary.get_basic_type_by_name("real")
    for name, val in (
        ("LightStartup", "0.07"),
        ("HeavyStartup", "0.16"),
        ("HitStopDilation", "0.12"),
        ("HitStopDuration", "0.055"),
        ("CameraPunchZ", "6.0"),
    ):
        ensure_var(bp, ge, name, t_real, val, editable=True, category="Combat|Tuning")


def clear_attack_event_nodes(ge) -> None:
    markers = (
        "TriggerLightAttack",
        "TriggerHeavyAttack",
        "LightDamage",
        "HeavyDamage",
        "LightCooldown",
        "HeavyCooldown",
        "LightStartup",
        "HeavyStartup",
        "bIsAttacking",
        "PerformMeleeTrace",
        "Perform Melee Trace",
        "MeleeTrace",
        "MM_Attack",
        "PlayAnimMontage",
        "Play Anim Montage",
        "attack stub",
        "[Kalsiyum] Light",
        "[Kalsiyum] Heavy",
        "startup→montage",
        "Light attack",
        "Heavy attack",
    )
    protect = (
        "TriggerDodge",
        "ToggleLockOn",
        "ReceiveTick",
        "Olay Tick",
        "FaceLocked",
        "LockedTarget",
        "GetAllActors",
        "FindNearest",
        "LaunchCharacter",
        "bIsDodging",
        "bIsInvulnerable",
        "DodgeImpulse",
        "DodgeIFrame",
        "DodgeRecovery",
        "LockOnRadius",
        "Get Player Character",
        "GetPlayerCharacter",
    )
    to_remove = []
    for n in list(ge.list_all_nodes()):
        title = n.get_node_title()
        if any(p in title for p in protect):
            continue
        if any(m in title for m in markers):
            to_remove.append(n)
    if to_remove:
        ge.remove_nodes(to_remove)
        log(f"Removed {len(to_remove)} attack-related EventGraph nodes")


def purge_trace_graphs(comp_bp) -> None:
    bel = unreal.BlueprintEditorLibrary
    for name in (
        "PerformMeleeTrace",
        "PerformMeleeTrace_0",
        "PerformMeleeTrace_1",
        "PerformMeleeTrace_2",
    ):
        g = bel.find_graph(comp_bp, name)
        if g is not None:
            bel.remove_graph(comp_bp, g)
            log(f"Removed graph {name}")


def force_graph_name(te, wanted: str) -> str:
    g = te.get_graph()
    got = g.get_name() if g else "?"
    if got == wanted:
        return got
    # After remove+recreate UE often names it PerformMeleeTrace_0 — rename back.
    for args in ((wanted,), (unreal.Name(wanted),)):
        try:
            te.rename(*args)
            got2 = te.get_graph().get_name()
            log(f"Renamed graph {got} -> {got2}")
            return got2
        except Exception as e:
            log(f"rename{args} failed: {e}")
    # Fallback: rename via graph object if exposed
    try:
        g.rename(wanted)
        log(f"graph.rename -> {g.get_name()}")
        return g.get_name()
    except Exception as e:
        log(f"graph.rename failed: {e}")
    return te.get_graph().get_name()


def rebuild_trace_with_hitstop(comp_bp) -> None:
    """No latent Delay inside the function — UE forbids latent nodes in BP functions."""
    purge_trace_graphs(comp_bp)

    t_real = unreal.BlueprintEditorLibrary.get_basic_type_by_name("real")
    t_str = unreal.BlueprintEditorLibrary.get_basic_type_by_name("string")
    te = unreal.BlueprintGraphEditor.create_and_edit_function_graph(comp_bp, "PerformMeleeTrace")
    assert te is not None, "create PerformMeleeTrace failed"
    final_name = force_graph_name(te, "PerformMeleeTrace")
    log(f"Trace graph name={final_name}")

    pin_dmg = te.add_graph_input_parameter("DamageAmount", t_real, "25.0")
    pin_lbl = te.add_graph_input_parameter("AttackLabel", t_str, "Light")
    t_entry = te.find_graph_entry_pin()

    t_owner = te.add_call_function_node("/Script/Engine.ActorComponent.GetOwner")
    t_loc = te.add_call_function_node("/Script/Engine.Actor.K2_GetActorLocation")
    t_fwd = te.add_call_function_node("/Script/Engine.Actor.GetActorForwardVector")
    t_range = te.add_get_member_variable_node("AttackRange")
    t_rad = te.add_get_member_variable_node("AttackRadius")
    mul_start = te.add_call_function_node("/Script/Engine.KismetMathLibrary.Multiply_VectorFloat")
    add_start = te.add_call_function_node("/Script/Engine.KismetMathLibrary.Add_VectorVector")
    mul_end = te.add_call_function_node("/Script/Engine.KismetMathLibrary.Multiply_VectorFloat")
    add_end = te.add_call_function_node("/Script/Engine.KismetMathLibrary.Add_VectorVector")
    trace = te.add_call_function_node("/Script/Engine.KismetSystemLibrary.SphereTraceSingle")
    br_hit = te.add_branch_node()
    brk_hit = te.add_call_function_node("/Script/Engine.GameplayStatics.BreakHitResult")
    apply_dmg = te.add_call_function_node("/Script/Engine.GameplayStatics.ApplyDamage")
    g_dil = te.add_get_member_variable_node("HitStopDilation")
    set_dil = te.add_call_function_node("/Script/Engine.GameplayStatics.SetGlobalTimeDilation")
    g_punch = te.add_get_member_variable_node("CameraPunchZ")
    mk_off = te.add_call_function_node("/Script/Engine.KismetMathLibrary.MakeVector")
    add_off = te.add_call_function_node("/Script/Engine.Actor.K2_AddActorWorldOffset")
    concat_hit = te.add_call_function_node("/Script/Engine.KismetStringLibrary.Concat_StrStr")
    print_hit = te.add_call_function_node("/Script/Engine.KismetSystemLibrary.PrintString")
    concat_miss = te.add_call_function_node("/Script/Engine.KismetStringLibrary.Concat_StrStr")
    print_miss = te.add_call_function_node("/Script/Engine.KismetSystemLibrary.PrintString")

    connect(t_entry, trace.find_execute_pin(), "entry->trace")
    connect(t_owner.find_result_pin(), t_loc.find_self_pin(), "own->loc")
    connect(t_owner.find_result_pin(), t_fwd.find_self_pin(), "own->fwd")
    connect(t_fwd.find_result_pin(), mul_start.find_input_pin("A"), "fwd->ms")
    set_val(mul_start.find_input_pin("B"), "60.0", "ms.B")
    connect(t_loc.find_result_pin(), add_start.find_input_pin("A"), "loc->as")
    connect(mul_start.find_result_pin(), add_start.find_input_pin("B"), "ms->as")
    connect(t_fwd.find_result_pin(), mul_end.find_input_pin("A"), "fwd->me")
    connect(t_range.find_result_pin(), mul_end.find_input_pin("B"), "range->me")
    connect(t_loc.find_result_pin(), add_end.find_input_pin("A"), "loc->ae")
    connect(mul_end.find_result_pin(), add_end.find_input_pin("B"), "me->ae")
    connect(add_start.find_result_pin(), trace.find_input_pin("Start"), "start")
    connect(add_end.find_result_pin(), trace.find_input_pin("End"), "end")
    connect(t_rad.find_result_pin(), trace.find_input_pin("Radius"), "rad")
    set_val(trace.find_input_pin("DrawDebugType"), "ForDuration", "dbg")
    set_val(trace.find_input_pin("DrawTime"), "0.28", "dbgT")
    set_val(trace.find_input_pin("bIgnoreSelf"), "true", "ign")

    connect(trace.find_then_pin(), br_hit.find_execute_pin(), "tr->br")
    connect(trace.find_output_pin("ReturnValue"), br_hit.find_condition_pin(), "hit?")
    connect(trace.find_output_pin("OutHit"), brk_hit.find_input_pin("Hit"), "outhit")

    connect(br_hit.find_then_pin(), apply_dmg.find_execute_pin(), "hit->dmg")
    connect(brk_hit.find_output_pin("HitActor"), apply_dmg.find_input_pin("DamagedActor"), "actor")
    connect(pin_dmg, apply_dmg.find_input_pin("BaseDamage"), "dmg")
    connect(t_owner.find_result_pin(), apply_dmg.find_input_pin("DamageCauser"), "causer")
    connect(apply_dmg.find_then_pin(), add_off.find_execute_pin(), "dmg->punch")
    connect(t_owner.find_result_pin(), add_off.find_self_pin(), "own->punch")
    connect(g_punch.find_result_pin(), mk_off.find_input_pin("Z"), "punchZ")
    set_val(mk_off.find_input_pin("X"), "0.0", "px")
    set_val(mk_off.find_input_pin("Y"), "0.0", "py")
    connect(mk_off.find_result_pin(), add_off.find_input_pin("DeltaLocation"), "delta")
    set_val(add_off.find_input_pin("bSweep"), "false", "sweep")
    connect(add_off.find_then_pin(), set_dil.find_execute_pin(), "punch->dil")
    connect(g_dil.find_result_pin(), set_dil.find_input_pin("TimeDilation"), "dil")
    connect(set_dil.find_then_pin(), print_hit.find_execute_pin(), "dil->print")
    connect(pin_lbl, concat_hit.find_input_pin("A"), "lbl")
    set_val(concat_hit.find_input_pin("B"), " HIT (+hitstop)", "hb")
    connect(concat_hit.find_result_pin(), print_hit.find_input_pin("InString"), "cstr")

    connect(br_hit.find_else_pin(), print_miss.find_execute_pin(), "miss")
    connect(pin_lbl, concat_miss.find_input_pin("A"), "lblm")
    set_val(concat_miss.find_input_pin("B"), " swing (miss)", "mb")
    connect(concat_miss.find_result_pin(), print_miss.find_input_pin("InString"), "cstrm")
    log("PerformMeleeTrace rebuilt (punch + dilation; restore on EventGraph)")
    return final_name


def resolve_callable_name(comp_bp, preferred: str, fallback: str) -> str:
    bel = unreal.BlueprintEditorLibrary
    if bel.find_graph(comp_bp, preferred) is not None:
        return preferred
    if bel.find_graph(comp_bp, fallback) is not None:
        return fallback
    raise AssertionError(f"missing callable graph {preferred}/{fallback}")


def patch_attacks_with_startup_and_montage(ge, trace_fn: str) -> None:
    face_fn = "FaceLockedTarget"
    mm_light = unreal.EditorAssetLibrary.load_asset(MM_LIGHT)
    mm_heavy = unreal.EditorAssetLibrary.load_asset(MM_HEAVY)
    assert mm_light is not None and mm_heavy is not None, "missing attack montages"

    def wire_attack(event_name, dmg_var, cd_var, startup_var, label, montage, y_off):
        ev = ge.add_custom_event_node(event_name)
        g_atk = ge.add_get_member_variable_node("bIsAttacking")
        g_ddg = ge.add_get_member_variable_node("bIsDodging")
        or_busy = ge.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanOR")
        br = ge.add_branch_node()
        s_atk1 = ge.add_set_member_variable_node("bIsAttacking")
        g_start = ge.add_get_member_variable_node(startup_var)
        delay_s = ge.add_call_function_node("/Script/Engine.KismetSystemLibrary.Delay")
        get_char = ge.add_call_function_node("/Script/Engine.GameplayStatics.GetPlayerCharacter")
        play_m = ge.add_call_function_node("/Script/Engine.Character.PlayAnimMontage")
        call_face = ge.add_call_function_node(face_fn)
        assert call_face is not None, f"FaceLockedTarget call failed for {event_name}"
        g_dmg = ge.add_get_member_variable_node(dmg_var)
        call_tr = ge.add_call_function_node(trace_fn)
        assert call_tr is not None, f"{trace_fn} call failed for {event_name}"
        g_hs = ge.add_get_member_variable_node("HitStopDuration")
        delay_hs = ge.add_call_function_node("/Script/Engine.KismetSystemLibrary.Delay")
        set_dil1 = ge.add_call_function_node("/Script/Engine.GameplayStatics.SetGlobalTimeDilation")
        g_cd = ge.add_get_member_variable_node(cd_var)
        delay_cd = ge.add_call_function_node("/Script/Engine.KismetSystemLibrary.Delay")
        s_atk0 = ge.add_set_member_variable_node("bIsAttacking")

        for node, x in (
            (ev, 0),
            (br, 320),
            (s_atk1, 520),
            (delay_s, 720),
            (play_m, 960),
            (call_face, 1200),
            (call_tr, 1440),
            (delay_hs, 1680),
            (set_dil1, 1900),
            (delay_cd, 2140),
            (s_atk0, 2380),
        ):
            node.set_node_pos(unreal.IntPoint(x, y_off))

        connect(ev.find_then_pin(), br.find_execute_pin(), "ev->br")
        connect(g_atk.find_result_pin(), or_busy.find_input_pin("A"), "atk")
        connect(g_ddg.find_result_pin(), or_busy.find_input_pin("B"), "ddg")
        connect(or_busy.find_result_pin(), br.find_condition_pin(), "or")
        connect(br.find_else_pin(), s_atk1.find_execute_pin(), "go")
        set_val(s_atk1.find_input_pin("bIsAttacking"), "true", "atk1")
        connect(s_atk1.find_then_pin(), delay_s.find_execute_pin(), "startup")
        connect(g_start.find_result_pin(), delay_s.find_input_pin("Duration"), "sturdur")
        connect(delay_s.find_then_pin(), play_m.find_execute_pin(), "->montage")
        set_val(get_char.find_input_pin("PlayerIndex"), "0", "pc")
        connect(get_char.find_result_pin(), play_m.find_self_pin(), "char->play")
        mont_pin = play_m.find_input_pin("AnimMontage")
        if mont_pin.is_valid():
            set_val(mont_pin, montage.get_path_name(), "montage")
        connect(play_m.find_then_pin(), call_face.find_execute_pin(), "face")
        connect(call_face.find_then_pin(), call_tr.find_execute_pin(), "trace")
        connect(g_dmg.find_result_pin(), call_tr.find_input_pin("DamageAmount"), "dmg")
        set_val(call_tr.find_input_pin("AttackLabel"), f"[Kalsiyum] {label}", "lbl")
        connect(call_tr.find_then_pin(), delay_hs.find_execute_pin(), "hs")
        connect(g_hs.find_result_pin(), delay_hs.find_input_pin("Duration"), "hsdur")
        connect(delay_hs.find_then_pin(), set_dil1.find_execute_pin(), "->dil1")
        set_val(set_dil1.find_input_pin("TimeDilation"), "1.0", "dil1")
        connect(set_dil1.find_then_pin(), delay_cd.find_execute_pin(), "cd")
        connect(g_cd.find_result_pin(), delay_cd.find_input_pin("Duration"), "cddur")
        connect(delay_cd.find_then_pin(), s_atk0.find_execute_pin(), "done")
        set_val(s_atk0.find_input_pin("bIsAttacking"), "false", "atk0")
        ge.add_comment_to_nodes(
            f"Faz 2 [CU] {label}: startup→montage→trace→hitstop restore→recovery",
            [ev, br, delay_s, play_m, call_tr, delay_hs, delay_cd],
            40,
        )
        log(f"Rewired {event_name}")

    wire_attack("TriggerLightAttack", "LightDamage", "LightCooldown", "LightStartup", "Light", mm_light, 0)
    wire_attack("TriggerHeavyAttack", "HeavyDamage", "HeavyCooldown", "HeavyStartup", "Heavy", mm_heavy, 420)


def main() -> None:
    log("=== Faz 2 [CU] polish ===")
    bp = unreal.EditorAssetLibrary.load_asset(COMP)
    assert bp is not None
    ge = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(bp)
    )

    retune_defaults(bp, ge)

    # 1) Drop dangling light/heavy calls so helper rebuild can compile.
    clear_attack_event_nodes(ge)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)

    # 2) Rebuild helper (non-latent). Rename if UE suffix-stamped it.
    graph_name = rebuild_trace_with_hitstop(bp)
    compiled_helpers = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    log(f"helpers compiled={compiled_helpers} graph={graph_name}")
    trace_fn = resolve_callable_name(bp, "PerformMeleeTrace", graph_name)
    assert unreal.BlueprintEditorLibrary.find_graph(bp, "FaceLockedTarget") is not None, "face graph missing"
    log(f"Using callable trace_fn={trace_fn}")

    # 3) Rewire attacks against compiled helpers.
    ge = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(bp)
    )
    clear_attack_event_nodes(ge)
    patch_attacks_with_startup_and_montage(ge, trace_fn)

    compiled = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    errs = ge.list_nodes_with_errors()
    log(f"compiled={compiled} errors={len(errs)}")
    for e in errs:
        log(f"ERR {e.get_node_title()}")
    assert compiled and len(errs) == 0, "compile failed"
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)

    char = unreal.EditorAssetLibrary.load_asset(CHAR)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for h in sds.k2_gather_subobject_data_for_blueprint(char):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, char)
        if isinstance(obj, unreal.SpringArmComponent):
            log(
                f"Faz1 SpringArm preserved Arm={obj.get_editor_property('target_arm_length')} "
                f"Lag={obj.get_editor_property('camera_lag_speed')}"
            )
    log("DONE ALL CU VERIFICATIONS PASSED")


if __name__ == "__main__":
    main()
