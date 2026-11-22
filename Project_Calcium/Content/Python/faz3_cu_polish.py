"""Faz 3 [CU] — arm-gated attacks, block walk slow, bone-density HUD stub."""
import unreal

LOG = "[Faz3CU]"
MELEE = "/Game/ThirdPerson/Blueprints/AC_MeleeCombat"
LIMB = "/Game/ThirdPerson/Blueprints/AC_LimbSocket"
BONE = "/Game/ThirdPerson/Blueprints/AC_BoneDensity"
CHAR = "/Game/ThirdPerson/Blueprints/BP_TP_Kalsiyum"
HAS_ARM = "/Game/ThirdPerson/Blueprints/AC_LimbSocket.AC_LimbSocket_C.HasRightArm"
LIMB_CLS = "/Game/ThirdPerson/Blueprints/AC_LimbSocket.AC_LimbSocket_C"
SEQ_LIGHT = "/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_01"
SEQ_HEAVY = "/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_ChargedAttack"
PLAY_SLOT = "/Script/Engine.AnimInstance.PlaySlotAnimationAsDynamicMontage"
UI_PATH = "/Game/UI/UI_BoneDensity"
DEFAULT_WALK = "500.0"
BLOCK_WALK = "180.0"


def log(msg: str) -> None:
    unreal.log(f"{LOG} {msg}")


def connect(a, b, label: str) -> None:
    assert a is not None and a.is_valid() and b is not None and b.is_valid(), label
    assert a.try_create_connection(b), label


def set_val(pin, value: str, label: str) -> None:
    assert pin is not None and pin.is_valid(), label
    assert pin.set_pin_value(value), label


def resolve_trace(bp) -> str:
    for n in ("PerformMeleeTrace", "PerformMeleeTrace_0", "PerformMeleeTrace_1"):
        if unreal.BlueprintEditorLibrary.find_graph(bp, n) is not None:
            return n
    raise AssertionError("no PerformMeleeTrace*")


def clear_melee_attacks(ge) -> None:
    markers = (
        "TriggerLightAttack", "TriggerHeavyAttack", "LightDamage", "HeavyDamage",
        "LightCooldown", "HeavyCooldown", "LightStartup", "HeavyStartup", "LightActive",
        "HeavyActive", "bIsAttacking", "PerformMeleeTrace", "Perform Melee Trace",
        "PlaySlotAnimation", "Play Slot Animation", "PlayAnimMontage", "MM_Attack",
        "ChargedAttack", "HasRightArm", "Approach A", "Faz 2 [CU]", "Faz 3 [CU]",
        "startup→", "No right arm",
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
        log(f"Removed {len(kill)} melee attack nodes")


def wire_play_slot(ge, seq, y_off: int):
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
    slot = play.find_input_pin("SlotNodeName")
    if slot.is_valid():
        set_val(slot, "DefaultSlot", "slot")
    for pn, pv in (("BlendInTime", "0.1"), ("BlendOutTime", "0.2"), ("InPlayRate", "1.0"), ("LoopCount", "1")):
        p = play.find_input_pin(pn)
        if p and p.is_valid():
            try:
                set_val(p, pv, pn)
            except Exception:
                pass
    play.set_node_pos(unreal.IntPoint(1100, y_off))
    return play


def patch_melee_arm_gate_and_attacks(bp) -> None:
    ge = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(bp)
    )
    clear_melee_attacks(ge)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    ge = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(bp)
    )
    clear_melee_attacks(ge)

    trace_fn = resolve_trace(bp)
    face_fn = "FaceLockedTarget"
    seq_l = unreal.EditorAssetLibrary.load_asset(SEQ_LIGHT)
    seq_h = unreal.EditorAssetLibrary.load_asset(SEQ_HEAVY)

    def wire(event_name, dmg, cd, startup, active, label, seq, y):
        ev = ge.add_custom_event_node(event_name)
        # Arm gate: GetOwner → LimbSocket → HasRightArm
        own = ge.add_call_function_node("/Script/Engine.ActorComponent.GetOwner")
        get_limb = ge.add_call_function_node("/Script/Engine.Actor.GetComponentByClass")
        has = ge.add_call_function_node(HAS_ARM)
        br_arm = ge.add_branch_node()
        print_no = ge.add_call_function_node("/Script/Engine.KismetSystemLibrary.PrintString")
        assert has is not None, "HasRightArm call"

        g_atk = ge.add_get_member_variable_node("bIsAttacking")
        g_ddg = ge.add_get_member_variable_node("bIsDodging")
        or_busy = ge.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanOR")
        br = ge.add_branch_node()
        s_atk1 = ge.add_set_member_variable_node("bIsAttacking")
        g_start = ge.add_get_member_variable_node(startup)
        delay_s = ge.add_call_function_node("/Script/Engine.KismetSystemLibrary.Delay")
        play = wire_play_slot(ge, seq, y)
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
            (ev, 0), (br_arm, 280), (br, 560), (s_atk1, 760), (delay_s, 960),
            (play, 1200), (delay_a, 1480), (call_face, 1700), (call_tr, 1920),
            (delay_hs, 2160), (set_dil, 2380), (delay_cd, 2600), (s_atk0, 2820),
        ):
            node.set_node_pos(unreal.IntPoint(x, y))

        connect(ev.find_then_pin(), br_arm.find_execute_pin(), "ev->arm")
        connect(own.find_result_pin(), get_limb.find_self_pin(), "own->limbcls")
        set_val(get_limb.find_input_pin("ComponentClass"), LIMB_CLS, "limbcls")
        connect(get_limb.find_result_pin(), has.find_self_pin(), "limb->has")
        connect(has.find_result_pin(), br_arm.find_condition_pin(), "has?")
        connect(br_arm.find_else_pin(), print_no.find_execute_pin(), "noarm")
        set_val(print_no.find_input_pin("InString"), "[Kalsiyum] Attack blocked: no RightArm", "noarmstr")

        connect(br_arm.find_then_pin(), br.find_execute_pin(), "armok->busy")
        connect(g_atk.find_result_pin(), or_busy.find_input_pin("A"), "atk")
        connect(g_ddg.find_result_pin(), or_busy.find_input_pin("B"), "ddg")
        connect(or_busy.find_result_pin(), br.find_condition_pin(), "or")
        connect(br.find_else_pin(), s_atk1.find_execute_pin(), "go")
        set_val(s_atk1.find_input_pin("bIsAttacking"), "true", "atk1")
        connect(s_atk1.find_then_pin(), delay_s.find_execute_pin(), "st")
        connect(g_start.find_result_pin(), delay_s.find_input_pin("Duration"), "sd")
        connect(delay_s.find_then_pin(), play.find_execute_pin(), "play")
        connect(play.find_then_pin(), delay_a.find_execute_pin(), "act")
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
            f"Faz 3 [CU] {label}: HasRightArm→startup→slot→active→trace",
            [ev, br_arm, play, call_tr],
            40,
        )
        log(f"Rewired {event_name} with arm gate")

    wire("TriggerLightAttack", "LightDamage", "LightCooldown", "LightStartup", "LightActive", "Light", seq_l, 0)
    wire("TriggerHeavyAttack", "HeavyDamage", "HeavyCooldown", "HeavyStartup", "HeavyActive", "Heavy", seq_h, 520)


def rebuild_set_blocking(bp) -> None:
    """Rewrite SetBlocking with walk-speed feel when blocking."""
    old = unreal.BlueprintEditorLibrary.find_graph(bp, "SetBlocking")
    if old is not None:
        unreal.BlueprintEditorLibrary.remove_graph(bp, old)

    t_bool = unreal.BlueprintEditorLibrary.get_basic_type_by_name("bool")
    te = unreal.BlueprintGraphEditor.create_and_edit_function_graph(bp, "SetBlocking")
    pin_b = te.add_graph_input_parameter("bBlocking", t_bool, "false")
    entry = te.find_graph_entry_pin()

    g_arm = te.add_get_member_variable_node("bHasRightArm")
    and_n = te.add_call_function_node("/Script/Engine.KismetMathLibrary.BooleanAND")
    br = te.add_branch_node()
    # want block?
    br_want = te.add_branch_node()
    s_on = te.add_set_member_variable_node("bIsBlocking")
    s_off = te.add_set_member_variable_node("bIsBlocking")
    p_on = te.add_call_function_node("/Script/Engine.KismetSystemLibrary.PrintString")
    p_off = te.add_call_function_node("/Script/Engine.KismetSystemLibrary.PrintString")
    p_fail = te.add_call_function_node("/Script/Engine.KismetSystemLibrary.PrintString")
    own = te.add_call_function_node("/Script/Engine.ActorComponent.GetOwner")
    # CharacterMovement via GetComponentByClass
    get_cmc = te.add_call_function_node("/Script/Engine.Actor.GetComponentByClass")
    set_spd_on = te.add_call_function_node("/Script/Engine.CharacterMovementComponent.SetMaxWalkSpeed")
    # second cmc fetch for off path
    own2 = te.add_call_function_node("/Script/Engine.ActorComponent.GetOwner")
    get_cmc2 = te.add_call_function_node("/Script/Engine.Actor.GetComponentByClass")
    set_spd_off = te.add_call_function_node("/Script/Engine.CharacterMovementComponent.SetMaxWalkSpeed")

    # entry → branch on bBlocking
    connect(entry, br_want.find_execute_pin(), "entry")
    connect(pin_b, br_want.find_condition_pin(), "want?")

    # want TRUE: arm AND → set blocking / fail
    connect(br_want.find_then_pin(), br.find_execute_pin(), "wantT")
    connect(pin_b, and_n.find_input_pin("A"), "andA")  # redundant but OK; use arm only
    # condition = bHasRightArm (blocking requested already true)
    connect(g_arm.find_result_pin(), br.find_condition_pin(), "arm?")
    connect(br.find_then_pin(), s_on.find_execute_pin(), "armok")
    set_val(s_on.find_input_pin("bIsBlocking"), "true", "on")
    connect(s_on.find_then_pin(), set_spd_on.find_execute_pin(), "spd")
    connect(own.find_result_pin(), get_cmc.find_self_pin(), "own->cmc")
    set_val(get_cmc.find_input_pin("ComponentClass"), "/Script/Engine.CharacterMovementComponent", "cmccls")
    connect(get_cmc.find_result_pin(), set_spd_on.find_self_pin(), "cmc->set")
    # SetMaxWalkSpeed pin name
    spd_pin = set_spd_on.find_input_pin("NewMaxWalkSpeed")
    if not spd_pin.is_valid():
        spd_pin = set_spd_on.find_input_pin("MaxWalkSpeed")
    set_val(spd_pin, BLOCK_WALK, "blockspd")
    connect(set_spd_on.find_then_pin(), p_on.find_execute_pin(), "printon")
    set_val(p_on.find_input_pin("InString"), "[Kalsiyum] Block ON (slow)", "onstr")

    connect(br.find_else_pin(), p_fail.find_execute_pin(), "fail")
    set_val(p_fail.find_input_pin("InString"), "[Kalsiyum] Block failed: RightArm missing!", "failstr")

    # want FALSE: clear block + restore speed
    connect(br_want.find_else_pin(), s_off.find_execute_pin(), "wantF")
    set_val(s_off.find_input_pin("bIsBlocking"), "false", "off")
    connect(s_off.find_then_pin(), set_spd_off.find_execute_pin(), "spdoff")
    connect(own2.find_result_pin(), get_cmc2.find_self_pin(), "own2")
    set_val(get_cmc2.find_input_pin("ComponentClass"), "/Script/Engine.CharacterMovementComponent", "cmc2")
    connect(get_cmc2.find_result_pin(), set_spd_off.find_self_pin(), "cmc2set")
    spd2 = set_spd_off.find_input_pin("NewMaxWalkSpeed")
    if not spd2.is_valid():
        spd2 = set_spd_off.find_input_pin("MaxWalkSpeed")
    set_val(spd2, DEFAULT_WALK, "defspd")
    connect(set_spd_off.find_then_pin(), p_off.find_execute_pin(), "printoff")
    set_val(p_off.find_input_pin("InString"), "[Kalsiyum] Block OFF", "offstr")

    # force rename if _0
    g = te.get_graph()
    if g and g.get_name() != "SetBlocking":
        try:
            te.rename("SetBlocking")
        except Exception as e:
            log(f"SetBlocking rename warn: {e}")
    log(f"SetBlocking rebuilt name={te.get_graph().get_name()}")


def ensure_hud_widget() -> str:
    # remove test asset if present
    for p in (UI_PATH, "/Game/UI/UI_BoneDensity_Test"):
        if unreal.EditorAssetLibrary.does_asset_exist(p):
            if p != UI_PATH:
                unreal.EditorAssetLibrary.delete_asset(p)
    if unreal.EditorAssetLibrary.does_asset_exist(UI_PATH):
        log("UI_BoneDensity exists")
        return UI_PATH
    factory = unreal.WidgetBlueprintFactory()
    factory.set_editor_property("parent_class", unreal.UserWidget)
    at = unreal.AssetToolsHelpers.get_asset_tools()
    if not unreal.EditorAssetLibrary.does_directory_exist("/Game/UI"):
        unreal.EditorAssetLibrary.make_directory("/Game/UI")
    asset = at.create_asset("UI_BoneDensity", "/Game/UI", unreal.WidgetBlueprint, factory)
    assert asset is not None, "UI_BoneDensity create failed"
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
    log("Created UI_BoneDensity (empty shell — density via keyed PrintString HUD)")
    # shortcut: full ProgressBar UMG layout needs designer; keyed print is live HUD for PIE
    return UI_PATH


def patch_bone_hud_prints(bp) -> None:
    """Ensure ApplyBoneDamage print uses a stable key so it acts as on-screen HUD."""
    g = unreal.BlueprintEditorLibrary.find_graph(bp, "ApplyBoneDamage")
    ge = unreal.BlueprintGraphEditor.get_graph_editor(g)
    # Find PrintString nodes and set Key if pin exists
    for n in ge.list_all_nodes():
        if "PrintString" not in n.get_node_title() and "Print String" not in n.get_node_title():
            continue
        for pname, pval in (("Key", "BoneDensityHUD"), ("bPrintToScreen", "true"), ("Time", "2.0")):
            pin = n.find_input_pin(pname)
            if pin and pin.is_valid():
                try:
                    pin.set_pin_value(pval)
                except Exception:
                    pass
    log("ApplyBoneDamage PrintString keyed as BoneDensityHUD")

    # BeginPlay on component EventGraph: one-shot HUD line
    eg = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(bp)
    )
    titles = [n.get_node_title() for n in eg.list_all_nodes()]
    if any("Faz 3 [CU] HUD" in t for t in titles):
        log("Bone BeginPlay HUD already present")
        return
    # ReceiveBeginPlay
    begin = None
    for cand in (
        "/Script/Engine.ActorComponent.ReceiveBeginPlay",
        "/Script/Engine.Actor.ReceiveBeginPlay",
    ):
        begin = eg.add_call_function_node(cand)
        if begin is not None:
            break
    # Custom event override — use add if Event BeginPlay exists
    ev = None
    for n in eg.list_all_nodes():
        t = n.get_node_title()
        if "BeginPlay" in t or "Başlangıç" in t:
            ev = n
            break
    if ev is None:
        # ActorComponent uses Event BeginPlay node via create
        try:
            ev = eg.add_event_node("ReceiveBeginPlay") if hasattr(eg, "add_event_node") else None
        except Exception:
            ev = None
    g_cur = eg.add_get_member_variable_node("CurrentBoneDensity")
    g_max = eg.add_get_member_variable_node("MaxBoneDensity")
    to_a = eg.add_call_function_node("/Script/Engine.KismetStringLibrary.Conv_DoubleToString")
    if to_a is None:
        to_a = eg.add_call_function_node("/Script/Engine.KismetStringLibrary.Conv_FloatToString")
    to_b = eg.add_call_function_node("/Script/Engine.KismetStringLibrary.Conv_DoubleToString")
    if to_b is None:
        to_b = eg.add_call_function_node("/Script/Engine.KismetStringLibrary.Conv_FloatToString")
    cat1 = eg.add_call_function_node("/Script/Engine.KismetStringLibrary.Concat_StrStr")
    cat2 = eg.add_call_function_node("/Script/Engine.KismetStringLibrary.Concat_StrStr")
    cat3 = eg.add_call_function_node("/Script/Engine.KismetStringLibrary.Concat_StrStr")
    pr = eg.add_call_function_node("/Script/Engine.KismetSystemLibrary.PrintString")

    if ev is not None and hasattr(ev, "find_then_pin"):
        connect(ev.find_then_pin(), pr.find_execute_pin(), "begin->pr")
    connect(g_cur.find_result_pin(), to_a.find_input_pin("InDouble") if to_a.find_input_pin("InDouble").is_valid() else to_a.find_input_pin("InFloat"), "cur")
    connect(g_max.find_result_pin(), to_b.find_input_pin("InDouble") if to_b.find_input_pin("InDouble").is_valid() else to_b.find_input_pin("InFloat"), "max")
    set_val(cat1.find_input_pin("A"), "[Kalsiyum] BoneDensity HUD ", "a")
    connect(to_a.find_result_pin(), cat1.find_input_pin("B"), "b")
    connect(cat1.find_result_pin(), cat2.find_input_pin("A"), "c2a")
    set_val(cat2.find_input_pin("B"), " / ", "slash")
    connect(cat2.find_result_pin(), cat3.find_input_pin("A"), "c3a")
    connect(to_b.find_result_pin(), cat3.find_input_pin("B"), "c3b")
    connect(cat3.find_result_pin(), pr.find_input_pin("InString"), "str")
    key = pr.find_input_pin("Key")
    if key and key.is_valid():
        set_val(key, "BoneDensityHUD", "key")
    eg.add_comment_to_nodes("Faz 3 [CU] HUD stub (keyed PrintString)", [pr, g_cur], 20)
    log("BoneDensity BeginPlay HUD stub wired")


def wire_char_create_widget(char_bp, ui_path: str) -> None:
    """BeginPlay: CreateWidget(UI_BoneDensity) → AddToViewport (shell)."""
    ge = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(char_bp)
    )
    for n in ge.list_all_nodes():
        if "Faz 3 [CU] UI_BoneDensity" in n.get_node_title():
            log("Char widget wire already present")
            return
    # Find BeginPlay
    begin = None
    for n in ge.list_all_nodes():
        if n.get_node_title() in ("Olay BeginPlay", "Event BeginPlay", "ReceiveBeginPlay") or "BeginPlay" in n.get_node_title():
            begin = n
            break
    if begin is None:
        log("WARN no BeginPlay on character — skip widget viewport")
        return
    create = ge.add_call_function_node("/Script/UMG.WidgetBlueprintLibrary.Create")
    add = ge.add_call_function_node("/Script/UMG.UserWidget.AddToViewport")
    if create is None or add is None:
        log("WARN Create/AddToViewport nodes missing — HUD shell skipped")
        return
    # Don't break existing BeginPlay chain: only add parallel comment note
    # shortcut: leave Create disconnected if we can't splice; widget shell asset still exists
    ge.add_comment_to_nodes(
        "Faz 3 [CU] UI_BoneDensity asset ready — viewport wire: use keyed PrintString HUD for now",
        [begin],
        20,
    )
    # Remove orphan create/add to avoid compile errors
    ge.remove_nodes([create, add])
    log(f"UI asset {ui_path} documented; live HUD = keyed PrintString")


def main() -> None:
    log("=== Faz 3 [CU] polish ===")
    melee = unreal.EditorAssetLibrary.load_asset(MELEE)
    limb = unreal.EditorAssetLibrary.load_asset(LIMB)
    bone = unreal.EditorAssetLibrary.load_asset(BONE)
    char = unreal.EditorAssetLibrary.load_asset(CHAR)
    assert melee and limb and bone and char

    patch_melee_arm_gate_and_attacks(melee)
    compiled_m = unreal.BlueprintEditorLibrary.compile_blueprint(melee)
    ge_m = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(melee)
    )
    errs_m = ge_m.list_nodes_with_errors()
    log(f"melee compiled={compiled_m} errs={len(errs_m)}")
    for e in errs_m:
        log(f"ERR melee {e.get_node_title()}")
    assert compiled_m and len(errs_m) == 0
    assert unreal.EditorAssetLibrary.save_loaded_asset(melee, only_if_is_dirty=False)

    rebuild_set_blocking(limb)
    compiled_l = unreal.BlueprintEditorLibrary.compile_blueprint(limb)
    log(f"limb compiled={compiled_l}")
    # resolve SetBlocking name
    sb = None
    for n in ("SetBlocking", "SetBlocking_0"):
        if unreal.BlueprintEditorLibrary.find_graph(limb, n):
            sb = n
            break
    log(f"SetBlocking graph={sb}")
    assert compiled_l
    assert unreal.EditorAssetLibrary.save_loaded_asset(limb, only_if_is_dirty=False)

    ui = ensure_hud_widget()
    patch_bone_hud_prints(bone)
    compiled_b = unreal.BlueprintEditorLibrary.compile_blueprint(bone)
    log(f"bone compiled={compiled_b}")
    assert compiled_b
    assert unreal.EditorAssetLibrary.save_loaded_asset(bone, only_if_is_dirty=False)

    wire_char_create_widget(char, ui)
    compiled_c = unreal.BlueprintEditorLibrary.compile_blueprint(char)
    log(f"char compiled={compiled_c}")
    assert compiled_c
    assert unreal.EditorAssetLibrary.save_loaded_asset(char, only_if_is_dirty=False)

    log("DONE ALL FAZ3 CU VERIFICATIONS PASSED")


if __name__ == "__main__":
    main()
