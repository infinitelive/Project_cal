"""Disable Block collision on hand blades so CMC/SpringArm stop penetrating."""
import unreal

LOG = "[FixBladeCol]"
PATHS = (
    "/Game/Weapons/BP_Blade_Viking",
    "/Game/Weapons/BP_Blade_Ninja",
    "/Game/Weapons/BP_HandWeapon",
)
CHAR = "/Game/ThirdPerson/Blueprints/BP_TP_Kalsiyum"


def log(msg: str) -> None:
    unreal.log(f"{LOG} {msg}")


def find_static_meshes(bp):
    found = []
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if obj is not None and isinstance(obj, unreal.StaticMeshComponent):
            found.append(obj)
    if found:
        return found
    gen = bp.generated_class()
    cdo = unreal.get_default_object(gen) if gen else None
    if cdo is None:
        return found
    root = cdo.get_editor_property("root_component")
    if isinstance(root, unreal.StaticMeshComponent):
        found.append(root)
    else:
        found.extend(list(cdo.get_components_by_class(unreal.StaticMeshComponent) or []))
    return found


def read_collision(comp) -> str:
    for getter in (
        lambda: str(comp.get_collision_enabled()),
        lambda: str(comp.get_editor_property("CollisionEnabled")),
        lambda: str(comp.body_instance.get_editor_property("collision_enabled")),
    ):
        try:
            return getter()
        except Exception:
            continue
    return "?"


def set_no_collision(comp) -> str:
    name = comp.get_name()
    before = read_collision(comp)
    comp.modify()
    # Prefer instance methods (editor_property name varies by UE version)
    ok = False
    try:
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        ok = True
    except Exception as e:
        log(f"set_collision_enabled fail {name}: {e}")
    if not ok:
        for prop in ("CollisionEnabled", "collision_enabled"):
            try:
                comp.set_editor_property(prop, unreal.CollisionEnabled.NO_COLLISION)
                ok = True
                break
            except Exception:
                continue
    try:
        comp.set_collision_profile_name("NoCollision")
    except Exception as e:
        log(f"profile warn {name}: {e}")
    for prop, val in (
        ("simulate_physics", False),
        ("SimulatePhysics", False),
        ("generate_overlap_events", False),
        ("GenerateOverlapEvents", False),
    ):
        try:
            comp.set_editor_property(prop, val)
        except Exception:
            pass
    after = read_collision(comp)
    assert ok, f"{name} could not set NoCollision ({before}->{after})"
    return f"{name}: {before} -> {after}"


def fix_bp(path: str) -> None:
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        log(f"SKIP missing {path}")
        return
    bp = unreal.EditorAssetLibrary.load_asset(path)
    assert bp is not None, f"load failed: {path}"
    meshes = find_static_meshes(bp)
    assert meshes, f"no StaticMeshComponent on {path}"
    for m in meshes:
        log(f"{path} {set_no_collision(m)}")
    compiled = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert compiled, f"compile failed: {path}"
    for m in find_static_meshes(bp):
        en = read_collision(m)
        assert "NO_COLLISION" in en.upper() or en.upper().endswith("NOCOLLISION") or "0" == en, (
            f"{path} still {en}"
        )
        log(f"VERIFY {path} {m.get_name()}={en}")
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"SAVED {path}")


def verify_spring_arm() -> None:
    if not unreal.EditorAssetLibrary.does_asset_exist(CHAR):
        log("SKIP SpringArm — char missing")
        return
    bp = unreal.EditorAssetLibrary.load_asset(CHAR)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    boom = None
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if obj is not None and isinstance(obj, unreal.SpringArmComponent):
            boom = obj
            break
    assert boom, "SpringArm missing on BP_TP_Kalsiyum"
    arm = float(boom.get_editor_property("target_arm_length"))
    offset = boom.get_editor_property("socket_offset")
    log(f"SpringArm arm={arm} offset={offset}")
    if abs(arm - 300.0) > 0.5:
        boom.modify()
        boom.set_editor_property("target_arm_length", 300.0)
        boom.set_editor_property("socket_offset", unreal.Vector(0.0, 50.0, 60.0))
        for name, val in (
            ("use_pawn_control_rotation", True),
            ("b_use_pawn_control_rotation", True),
            ("do_collision_test", True),
            ("b_do_collision_test", True),
            ("probe_size", 12.0),
            ("enable_camera_lag", True),
            ("b_enable_camera_lag", True),
            ("camera_lag_speed", 9.0),
            ("enable_camera_rotation_lag", True),
            ("b_enable_camera_rotation_lag", True),
            ("camera_rotation_lag_speed", 10.0),
        ):
            try:
                boom.set_editor_property(name, val)
            except Exception:
                pass
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
        log("SpringArm restored to Faz1 baseline")
    else:
        log("SpringArm already ~300 — leave")


def main() -> None:
    log("=== start ===")
    for p in PATHS:
        fix_bp(p)
    verify_spring_arm()
    log("DONE BLADE COLLISION FIX OK")


if __name__ == "__main__":
    main()
