"""Faz 1 [CU] — camera + interact LineTrace -> Print (no Branch pins)."""
import unreal

LOG_PREFIX = "[Faz1CU]"
BP_PATH = "/Game/ThirdPerson/Blueprints/BP_TP_Kalsiyum"


def log(msg: str) -> None:
    unreal.log(f"{LOG_PREFIX} {msg}")


def find_subobject_by_class(bp, comp_class):
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if obj is not None and isinstance(obj, comp_class):
            return obj
    return None


def set_prop(obj, names, value) -> bool:
    for name in names:
        try:
            obj.set_editor_property(name, value)
            return True
        except Exception:
            continue
    return False


def polish_camera_and_move(bp) -> None:
    boom = find_subobject_by_class(bp, unreal.SpringArmComponent)
    assert boom is not None
    boom.modify()
    assert set_prop(boom, ["target_arm_length"], 300.0)
    assert set_prop(boom, ["socket_offset"], unreal.Vector(0.0, 50.0, 60.0))
    assert set_prop(boom, ["use_pawn_control_rotation", "b_use_pawn_control_rotation"], True)
    assert set_prop(boom, ["do_collision_test", "b_do_collision_test"], True)
    assert set_prop(boom, ["probe_size"], 12.0)
    assert set_prop(boom, ["enable_camera_lag", "b_enable_camera_lag"], True)
    assert set_prop(boom, ["camera_lag_speed"], 9.0)
    assert set_prop(boom, ["camera_lag_max_distance"], 60.0)
    assert set_prop(boom, ["enable_camera_rotation_lag", "b_enable_camera_rotation_lag"], True)
    assert set_prop(boom, ["camera_rotation_lag_speed"], 10.0)
    move = find_subobject_by_class(bp, unreal.CharacterMovementComponent)
    assert move is not None
    move.modify()
    assert set_prop(move, ["max_acceleration"], 1400.0)
    assert set_prop(move, ["braking_deceleration_walking"], 1600.0)
    assert set_prop(move, ["ground_friction"], 6.0)
    log("SpringArm+Movement polish applied")


def replace_interact_stub(ge) -> None:
    nodes = list(ge.list_all_nodes())
    interact = None
    to_remove = []
    has_good_trace = False
    for n in nodes:
        t = n.get_node_title()
        if "IA_Interact" in t:
            interact = n
        # cleanup prior failed attempts
        if any(
            k in t
            for k in (
                "Print String",
                "PrintString",
                "Branch",
                "Line Trace",
                "Get Actor Location",
                "Get Control Rotation",
                "Get Forward Vector",
                "vector * float",
                "vector + vector",
                "CloseSelfOnly",
                "ToolMenu",
                "IfThenElse",
            )
        ):
            # keep IA_Interact / IA_Sprint / CharacterMovement sprint wiring
            if "IA_Interact" in t or "IA_Sprint" in t or "MaxWalkSpeed" in t or "CharacterMovement" in t:
                continue
            # Only strip nodes clearly from CU interact attempts / AG print stub
            if "Print" in t or "Line Trace" in t or "Branch" in t or "IfThenElse" in t or "CloseSelf" in t:
                to_remove.append(n)
            elif "Get Actor Location" in t or "Get Control Rotation" in t or "Get Forward Vector" in t:
                to_remove.append(n)
            elif "vector" in t.lower():
                to_remove.append(n)

    assert interact is not None

    # Detect if already fully wired from a good prior run
    titles = [n.get_node_title() for n in nodes]
    if any("Line Trace" in t for t in titles) and any("Interact HIT" in str(getattr(n, "", "")) for n in nodes):
        pass

    if to_remove:
        ge.remove_nodes(to_remove)
        log(f"Cleaned {len(to_remove)} prior interact attempt node(s)")

    # Re-check after clean
    if any("Line Trace" in n.get_node_title() for n in ge.list_all_nodes()):
        log("LineTrace still present after clean — skip")
        return

    get_loc = ge.add_call_function_node("/Script/Engine.Actor.K2_GetActorLocation")
    get_loc.set_node_pos(unreal.IntPoint(40, 140))
    get_ctrl = ge.add_call_function_node("/Script/Engine.Pawn.GetControlRotation")
    get_ctrl.set_node_pos(unreal.IntPoint(40, 260))
    get_fwd = ge.add_call_function_node("/Script/Engine.KismetMathLibrary.GetForwardVector")
    get_fwd.set_node_pos(unreal.IntPoint(40, 380))
    rot_in = get_fwd.find_input_pin("InRot")
    if rot_in is None or not rot_in.is_valid():
        rot_in = get_fwd.find_input_pin("A")
    assert get_ctrl.find_output_pin("ReturnValue").try_create_connection(rot_in)

    mul = ge.add_call_function_node("/Script/Engine.KismetMathLibrary.Multiply_VectorFloat")
    mul.set_node_pos(unreal.IntPoint(40, 500))
    assert get_fwd.find_output_pin("ReturnValue").try_create_connection(mul.find_input_pin("A"))
    assert mul.find_input_pin("B").set_pin_value("250.0")

    add = ge.add_call_function_node("/Script/Engine.KismetMathLibrary.Add_VectorVector")
    add.set_node_pos(unreal.IntPoint(40, 620))
    assert get_loc.find_output_pin("ReturnValue").try_create_connection(add.find_input_pin("A"))
    assert mul.find_output_pin("ReturnValue").try_create_connection(add.find_input_pin("B"))

    trace = ge.add_call_function_node("/Script/Engine.KismetSystemLibrary.LineTraceSingle")
    assert trace is not None
    trace.set_node_pos(unreal.IntPoint(400, 0))
    assert get_loc.find_output_pin("ReturnValue").try_create_connection(trace.find_input_pin("Start"))
    assert add.find_output_pin("ReturnValue").try_create_connection(trace.find_input_pin("End"))
    chan = trace.find_input_pin("TraceChannel")
    if chan is not None and chan.is_valid():
        chan.set_pin_value("Visibility")
    draw = trace.find_input_pin("DrawDebugType")
    if draw is not None and draw.is_valid():
        try:
            draw.set_pin_value("ForDuration")
        except Exception:
            pass

    trig = interact.find_output_pin("Triggered")
    assert trig.is_valid()
    assert trig.try_create_connection(trace.find_execute_pin())

    print_n = ge.add_call_function_node("/Script/Engine.KismetSystemLibrary.PrintString")
    print_n.set_node_pos(unreal.IntPoint(720, 0))
    print_n.find_input_pin("InString").set_pin_value(
        "[Kalsiyum] Interact trace (debug line = hit/miss)"
    )
    assert trace.find_output_pin("then").try_create_connection(print_n.find_execute_pin())

    ge.add_comment_to_nodes(
        "Faz 1 [CU] Interact line trace 250uu Visibility",
        [interact, trace, print_n],
        50,
    )
    log("Interact rewired: Triggered -> LineTrace -> Print")


def main() -> None:
    log("=== Starting Faz 1 [CU] polish ===")
    bp = unreal.EditorAssetLibrary.load_asset(BP_PATH)
    assert bp is not None
    polish_camera_and_move(bp)
    ge = unreal.BlueprintGraphEditor.get_graph_editor(
        unreal.BlueprintEditorLibrary.find_event_graph(bp)
    )
    replace_interact_stub(ge)
    compiled = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    errs = ge.list_nodes_with_errors()
    log(f"compiled={compiled} errors={len(errs)}")
    for e in errs:
        log(f"ERR: {e}")
    assert compiled and len(errs) == 0, f"Compile failed: {errs}"
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
    titles = [n.get_node_title() for n in ge.list_all_nodes()]
    log(f"VERIFY nodes: {titles}")
    assert any("Line Trace" in t for t in titles)
    boom = find_subobject_by_class(bp, unreal.SpringArmComponent)
    assert float(boom.get_editor_property("target_arm_length")) == 300.0
    log("DONE ALL CU VERIFICATIONS PASSED")


if __name__ == "__main__":
    main()
