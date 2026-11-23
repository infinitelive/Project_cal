"""Set BP_Blade_* StaticMesh mobility to Movable so AttachTo CharacterMesh works."""
import unreal

LOG = "[FixBladeMobility]"
PATHS = (
    "/Game/Weapons/BP_Blade_Viking",
    "/Game/Weapons/BP_Blade_Ninja",
    "/Game/Weapons/BP_HandWeapon",
)


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
    return found


def set_movable(comp) -> str:
    before = str(comp.get_editor_property("mobility"))
    comp.modify()
    comp.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    after = str(comp.get_editor_property("mobility"))
    return f"{comp.get_name()}: {before} -> {after}"


def fix_bp(path: str) -> None:
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        log(f"SKIP missing {path}")
        return
    bp = unreal.EditorAssetLibrary.load_asset(path)
    assert bp is not None, f"load failed: {path}"
    meshes = find_static_meshes(bp)
    if not meshes:
        # Fallback: CDO root / components
        gen = bp.generated_class()
        cdo = unreal.get_default_object(gen) if gen else None
        if cdo is not None:
            root = cdo.get_editor_property("root_component")
            if isinstance(root, unreal.StaticMeshComponent):
                meshes = [root]
            else:
                meshes = list(cdo.get_components_by_class(unreal.StaticMeshComponent) or [])
    assert meshes, f"no StaticMeshComponent on {path}"
    for m in meshes:
        log(f"{path} {set_movable(m)}")
    compiled = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert compiled, f"compile failed: {path}"
    # Re-read after compile
    for m in find_static_meshes(bp):
        mob = m.get_editor_property("mobility")
        assert mob == unreal.ComponentMobility.MOVABLE, f"{path} still {mob}"
        log(f"VERIFY {path} {m.get_name()}={mob}")
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"SAVED {path}")


def main() -> None:
    log("=== start ===")
    for p in PATHS:
        fix_bp(p)
    log("DONE BLADE MOBILITY FIX OK")


if __name__ == "__main__":
    main()
