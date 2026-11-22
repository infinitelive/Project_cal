"""Faz3 CU: DropRightArm HideBoneByName(upperarm_r); Reattach UnHide. Save after each step."""
import unreal

LOG = "[HideArm]"
LIMB = "/Game/ThirdPerson/Blueprints/AC_LimbSocket"
DETACHED = "/Game/ThirdPerson/Blueprints/BP_DetachedLimb"
CHAR = "/Game/ThirdPerson/Blueprints/BP_TP_Kalsiyum"
LIMB_ACTOR = "/Game/ThirdPerson/Blueprints/BP_DetachedLimb.BP_DetachedLimb_C"
HIDE = "/Script/Engine.SkinnedMeshComponent.HideBoneByName"
UNHIDE = "/Script/Engine.SkinnedMeshComponent.UnHideBoneByName"
RE = "/Game/ThirdPerson/Blueprints/AC_LimbSocket.AC_LimbSocket_C.ReattachRightArm"
BONE = "upperarm_r"


def log(m):
    unreal.log(f"{LOG} {m}")


def connect(a, b, label):
    assert a and a.is_valid() and b and b.is_valid(), label
    assert a.try_create_connection(b), label


def set_val(pin, value, label):
    assert pin and pin.is_valid(), label
    assert pin.set_pin_value(value), f"{label}={value}"


def add_call(te, path):
    n = te.add_call_function_node(path)
    assert n, path
    return n


def clear_body(te, keep):
    kill = [n for n in list(te.list_all_nodes()) if n.get_node_title() not in keep]
    if kill:
        te.remove_nodes(kill)


def save(bp):
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp), "save failed"
    log(f"saved {bp.get_path_name()}")


def rebuild_drop(bp):
    g = unreal.BlueprintEditorLibrary.find_graph(bp, "DropRightArm")
    assert g, "DropRightArm missing"
    te = unreal.BlueprintGraphEditor.get_graph_editor(g)
    clear_body(te, ("DropRightArm",))
    entry = te.find_graph_entry_pin()

    g_arm = te.add_get_member_variable_node("bHasRightArm")
    br = te.add_branch_node()
    s_arm = te.add_set_member_variable_node("bHasRightArm")
    s_blk = te.add_set_member_variable_node("bIsBlocking")
    s_js = te.add_set_member_variable_node("JointStress")
    own_m = add_call(te, "/Script/Engine.ActorComponent.GetOwner")
    get_mesh = add_call(te, "/Script/Engine.Actor.GetComponentByClass")
    hide = add_call(te, HIDE)
    own = add_call(te, "/Script/Engine.ActorComponent.GetOwner")
    get_loc = add_call(te, "/Script/Engine.Actor.K2_GetActorLocation")
    get_right = add_call(te, "/Script/Engine.Actor.GetActorRightVector")
    mul = add_call(te, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat")
    addv = add_call(te, "/Script/Engine.KismetMathLibrary.Add_VectorVector")
    add_up = add_call(te, "/Script/Engine.KismetMathLibrary.Add_VectorVector")
    make_tf = add_call(te, "/Script/Engine.KismetMathLibrary.MakeTransform")
    spawn = add_call(te, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass")
    finish = add_call(te, "/Script/Engine.GameplayStatics.FinishSpawningActor")
    pr = add_call(te, "/Script/Engine.KismetSystemLibrary.PrintString")

    connect(entry, br.find_execute_pin(), "entry")
    connect(g_arm.find_result_pin(), br.find_condition_pin(), "has?")
    connect(br.find_then_pin(), s_arm.find_execute_pin(), "drop")
    set_val(s_arm.find_input_pin("bHasRightArm"), "false", "armF")
    connect(s_arm.find_then_pin(), s_blk.find_execute_pin(), "blk")
    set_val(s_blk.find_input_pin("bIsBlocking"), "false", "blkF")
    connect(s_blk.find_then_pin(), s_js.find_execute_pin(), "js")
    set_val(s_js.find_input_pin("JointStress"), "0.0", "js0")

    connect(own_m.find_result_pin(), get_mesh.find_self_pin(), "own->mesh")
    set_val(get_mesh.find_input_pin("ComponentClass"), "/Script/Engine.SkeletalMeshComponent", "meshcls")
    connect(s_js.find_then_pin(), hide.find_execute_pin(), "->hide")
    connect(get_mesh.find_result_pin(), hide.find_self_pin(), "mesh->hide")
    set_val(hide.find_input_pin("BoneName"), BONE, "bone")
    set_val(hide.find_input_pin("PhysBodyOption"), "PHT_HideBone", "phys")

    connect(own.find_result_pin(), get_loc.find_self_pin(), "loc")
    connect(own.find_result_pin(), get_right.find_self_pin(), "right")
    connect(get_right.find_result_pin(), mul.find_input_pin("A"), "r*")
    set_val(mul.find_input_pin("B"), "60.0", "60")
    connect(get_loc.find_result_pin(), addv.find_input_pin("A"), "a")
    connect(mul.find_result_pin(), addv.find_input_pin("B"), "b")
    connect(addv.find_result_pin(), add_up.find_input_pin("A"), "upA")
    set_val(add_up.find_input_pin("B"), "(X=0.000000,Y=0.000000,Z=80.000000)", "upB")
    loc_pin = make_tf.find_input_pin("Location")
    if not (loc_pin and loc_pin.is_valid()):
        loc_pin = make_tf.find_input_pin("Translation")
    connect(add_up.find_result_pin(), loc_pin, "tf")

    connect(hide.find_then_pin(), spawn.find_execute_pin(), "spawn")
    set_val(spawn.find_input_pin("ActorClass"), LIMB_ACTOR, "cls")
    connect(make_tf.find_result_pin(), spawn.find_input_pin("SpawnTransform"), "st")
    # WorldContext may be auto; CollisionHandling optional
    ch = spawn.find_input_pin("CollisionHandlingOverride")
    if ch and ch.is_valid():
        try:
            ch.set_pin_value("AlwaysSpawn")
        except Exception:
            pass

    connect(spawn.find_then_pin(), finish.find_execute_pin(), "fin")
    connect(spawn.find_result_pin(), finish.find_input_pin("Actor"), "actor")
    ft = finish.find_input_pin("SpawnTransform")
    if ft and ft.is_valid():
        connect(make_tf.find_result_pin(), ft, "ft")
    connect(finish.find_then_pin(), pr.find_execute_pin(), "pr")
    set_val(pr.find_input_pin("InString"), "[Kalsiyum] Limb DROPPED (RightArm)", "str")

    ok = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    titles = [n.get_node_title() for n in te.list_all_nodes()]
    log(f"Drop compiled={ok} titles={titles}")
    assert ok and any("HideBone" in t for t in titles)
    save(bp)


def rebuild_reattach(bp):
    g = unreal.BlueprintEditorLibrary.find_graph(bp, "ReattachRightArm")
    assert g, "ReattachRightArm missing"
    te = unreal.BlueprintGraphEditor.get_graph_editor(g)
    clear_body(te, ("ReattachRightArm",))
    entry = te.find_graph_entry_pin()
    g_arm = te.add_get_member_variable_node("bHasRightArm")
    br = te.add_branch_node()
    s_arm = te.add_set_member_variable_node("bHasRightArm")
    s_js = te.add_set_member_variable_node("JointStress")
    own = add_call(te, "/Script/Engine.ActorComponent.GetOwner")
    get_mesh = add_call(te, "/Script/Engine.Actor.GetComponentByClass")
    unhide = add_call(te, UNHIDE)
    pr = add_call(te, "/Script/Engine.KismetSystemLibrary.PrintString")

    connect(entry, br.find_execute_pin(), "entry")
    connect(g_arm.find_result_pin(), br.find_condition_pin(), "has?")
    connect(br.find_else_pin(), s_arm.find_execute_pin(), "miss")
    set_val(s_arm.find_input_pin("bHasRightArm"), "true", "armT")
    connect(s_arm.find_then_pin(), s_js.find_execute_pin(), "js")
    set_val(s_js.find_input_pin("JointStress"), "0.0", "js0")
    connect(own.find_result_pin(), get_mesh.find_self_pin(), "own")
    set_val(get_mesh.find_input_pin("ComponentClass"), "/Script/Engine.SkeletalMeshComponent", "meshcls")
    connect(s_js.find_then_pin(), unhide.find_execute_pin(), "show")
    connect(get_mesh.find_result_pin(), unhide.find_self_pin(), "mesh")
    set_val(unhide.find_input_pin("BoneName"), BONE, "bone")
    connect(unhide.find_then_pin(), pr.find_execute_pin(), "pr")
    set_val(pr.find_input_pin("InString"), "[Kalsiyum] Limb REATTACHED", "str")

    ok = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    titles = [n.get_node_title() for n in te.list_all_nodes()]
    log(f"Reattach compiled={ok} titles={titles}")
    assert ok and any("UnHide" in t for t in titles)
    save(bp)


def fix_detached():
    bp = unreal.EditorAssetLibrary.load_asset(DETACHED)
    ge = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(bp)
    )
    nodes = list(ge.list_all_nodes())
    log(f"Detached before: {[n.get_node_title() for n in nodes]}")
    # If already has working Reattach + overlap, leave it
    titles = [n.get_node_title() for n in nodes]
    has_re = any("Reattach" in t for t in titles)
    has_ov = any("Overlap" in t or "Bitişik" in t for t in titles)
    if has_re and has_ov and not ge.list_nodes_with_errors():
        log("Detached OK — skip")
        return

    # wipe non-comments
    kill = [n for n in nodes if "Comment" not in n.get_node_title() and "Yorum" not in n.get_node_title()]
    if kill:
        ge.remove_nodes(kill)

    # Prefer component/actor overlap; fallback custom event + player
    overlap = None
    for meth, arg in (
        ("add_event_node", "ReceiveActorBeginOverlap"),
        ("add_override_event_node", "ReceiveActorBeginOverlap"),
        ("add_custom_event_node", "OnLimbPickup"),
    ):
        if hasattr(ge, meth):
            try:
                overlap = getattr(ge, meth)(arg)
                log(f"{meth} -> {overlap is not None}")
                if overlap:
                    break
            except Exception as e:
                log(f"{meth} {e}")
    assert overlap, "no overlap/event"

    get_limb = add_call(ge, "/Script/Engine.Actor.GetComponentByClass")
    call_re = add_call(ge, RE)
    destroy = add_call(ge, "/Script/Engine.Actor.K2_DestroyActor")
    then = overlap.find_then_pin()

    other = None
    if hasattr(overlap, "find_output_pin"):
        for pn in ("OtherActor", "Other Actor"):
            p = overlap.find_output_pin(pn)
            if p and p.is_valid():
                other = p
                break

    if other:
        connect(then, call_re.find_execute_pin(), "ov")
        connect(other, get_limb.find_self_pin(), "other")
    else:
        # custom event: use player character
        pc = add_call(ge, "/Script/Engine.GameplayStatics.GetPlayerCharacter")
        set_val(pc.find_input_pin("PlayerIndex"), "0", "pi")
        connect(then, call_re.find_execute_pin(), "ev")
        connect(pc.find_result_pin(), get_limb.find_self_pin(), "pc")

    set_val(
        get_limb.find_input_pin("ComponentClass"),
        "/Game/ThirdPerson/Blueprints/AC_LimbSocket.AC_LimbSocket_C",
        "cls",
    )
    connect(get_limb.find_result_pin(), call_re.find_self_pin(), "limb")
    connect(call_re.find_then_pin(), destroy.find_execute_pin(), "des")

    ok = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    errs = [e.get_node_title() for e in ge.list_nodes_with_errors()]
    log(f"Detached compiled={ok} errs={errs}")
    assert ok and not errs, errs
    save(bp)


def main():
    bp = unreal.EditorAssetLibrary.load_asset(LIMB)
    rebuild_drop(bp)
    rebuild_reattach(bp)
    fix_detached()
    char = unreal.EditorAssetLibrary.load_asset(CHAR)
    unreal.BlueprintEditorLibrary.compile_blueprint(char)
    save(char)

    # final verify from disk reload
    bp2 = unreal.EditorAssetLibrary.load_asset(LIMB)
    g = unreal.BlueprintEditorLibrary.find_graph(bp2, "DropRightArm")
    titles = [
        n.get_node_title()
        for n in unreal.BlueprintGraphEditor.get_graph_editor(g).list_all_nodes()
    ]
    assert any("HideBone" in t for t in titles), f"persist fail {titles}"
    log("DONE ARM VISUAL HIDE")


if __name__ == "__main__":
    main()
