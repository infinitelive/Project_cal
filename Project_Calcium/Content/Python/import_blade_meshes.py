"""Import distinct Viking/Ninja FBX blades and rewire BP_Blade_* (different scales).

Run with PIE STOPPED. Imports new mesh assets (does not fight locked Cube SM).
"""
import unreal

LOG = "[ImportBlade]"
RAW = r"C:\kalsiyum_ue\RawImports\Weapons"
VIK_FBX = RAW + r"\Blade_Viking_Source.fbx"
NIN_FBX = RAW + r"\Blade_Ninja_Source.fbx"
DEST = "/Game/Weapons"
# New asset names — leave old Cube SM_* in place; BP points here
SM_VIK = "/Game/Weapons/SM_Blade_Viking_Mesh"
SM_NIN = "/Game/Weapons/SM_Blade_Ninja_Mesh"
BP_VIK = "/Game/Weapons/BP_Blade_Viking"
BP_NIN = "/Game/Weapons/BP_Blade_Ninja"
BP_HAND = "/Game/Weapons/BP_HandWeapon"
MAT_VIK = "/Game/Materials/M_Blade_Viking"
MAT_NIN = "/Game/Materials/M_Blade_Ninja"

SCALE_VIK = unreal.Vector(1.15, 1.15, 1.15)
SCALE_NIN = unreal.Vector(0.85, 0.85, 1.05)
LOC_VIK = unreal.Vector(8.0, 0.0, 0.0)
LOC_NIN = unreal.Vector(6.0, 0.0, 0.0)
ROT = unreal.Rotator(0.0, 0.0, 90.0)


def log(m):
    unreal.log(f"{LOG} {m}")


def assert_not_pie():
    # EditorAssetLibrary / import is unreliable in PIE
    try:
        pie = unreal.EditorLevelLibrary.get_editor_world()
        # Prefer play-world check
        if unreal.GameplayStatics.get_game_mode(pie) is not None:
            # may be false positive in editor; also check PIE worlds
            pass
    except Exception:
        pass
    worlds = []
    try:
        worlds = list(unreal.EditorLevelLibrary.get_pie_worlds(True) or [])
    except Exception:
        try:
            worlds = list(unreal.UnrealEditorSubsystem().get_editor_world() and [])
        except Exception:
            worlds = []
    # Hard check used by UE logs: "currently in a play mode"
    try:
        if unreal.EditorUtilityLibrary.get_editor_property:  # noqa — probe only
            pass
    except Exception:
        pass
    try:
        from unreal import EditorLevelLibrary as ELL  # noqa
        pie_worlds = ELL.get_pie_worlds(False)
        if pie_worlds and len(list(pie_worlds)) > 0:
            raise RuntimeError("STOP PIE first, then re-run import_blade_meshes.py")
    except RuntimeError:
        raise
    except Exception:
        pass


def import_fbx(src_path: str, dest_name: str) -> str:
    assert unreal.Paths.file_exists(src_path), f"missing {src_path}"
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", src_path)
    task.set_editor_property("destination_path", DEST)
    task.set_editor_property("destination_name", dest_name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)

    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("import_animations", False)
    static_data = options.get_editor_property("static_mesh_import_data")
    if static_data:
        for prop, val in (
            ("combine_meshes", True),
            ("auto_generate_collision", False),
            ("generate_lightmap_u_vs", False),
        ):
            try:
                static_data.set_editor_property(prop, val)
            except Exception:
                pass
    task.set_editor_property("options", options)

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    tools.import_asset_tasks([task])
    imported = list(task.get_editor_property("imported_object_paths") or [])
    log(f"import {dest_name} paths={imported}")

    path = f"{DEST}/{dest_name}"
    if imported:
        # Prefer first imported path (strip .ObjectName)
        raw = imported[0]
        path = raw.split(".", 1)[0] if "." in raw else raw

    unreal.EditorAssetLibrary.sync_browser_to_objects([path])
    # Registry can lag one tick after Interchange
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        # Fallback: load via soft path from imported list
        if not imported:
            raise RuntimeError(f"import produced no paths for {dest_name}")
        path = imported[0].split(".", 1)[0]
        asset = unreal.EditorAssetLibrary.load_asset(path)
        assert asset is not None, f"import failed load {path}"
        unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
        log(f"saved via load fallback {path}")
    return path


def apply_material(sm_path: str, mat_path: str) -> None:
    sm = unreal.EditorAssetLibrary.load_asset(sm_path)
    mat = (
        unreal.EditorAssetLibrary.load_asset(mat_path)
        if unreal.EditorAssetLibrary.does_asset_exist(mat_path)
        else None
    )
    if not sm:
        return
    if mat:
        try:
            sm.set_material(0, mat)
        except Exception as e:
            log(f"set_material warn {sm_path}: {e}")
    # NoCollision on mesh asset default
    try:
        body = sm.get_editor_property("body_setup")
        if body:
            body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
    except Exception:
        pass
    unreal.EditorAssetLibrary.save_loaded_asset(sm, only_if_is_dirty=False)
    log(f"material {sm_path} <- {mat_path if mat else 'none'}")


def find_smc(bp):
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if obj is not None and isinstance(obj, unreal.StaticMeshComponent):
            return obj
    gen = bp.generated_class()
    cdo = unreal.get_default_object(gen) if gen else None
    if cdo is None:
        return None
    try:
        smc = cdo.get_editor_property("static_mesh_component")
        if smc:
            return smc
    except Exception:
        pass
    root = cdo.get_editor_property("root_component")
    if isinstance(root, unreal.StaticMeshComponent):
        return root
    return None


def set_no_collision(comp) -> None:
    comp.modify()
    try:
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    except Exception:
        pass
    try:
        comp.set_collision_profile_name("NoCollision")
    except Exception:
        pass


def wire_blade_bp(bp_path: str, sm_path: str, scale, loc) -> None:
    bp = unreal.EditorAssetLibrary.load_asset(bp_path)
    assert bp, bp_path
    mesh = unreal.EditorAssetLibrary.load_asset(sm_path)
    assert mesh, sm_path
    smc = find_smc(bp)
    assert smc, f"no SMC on {bp_path}"
    smc.modify()
    smc.set_editor_property("static_mesh", mesh)
    smc.set_editor_property("relative_scale3d", scale)
    smc.set_editor_property("relative_location", loc)
    smc.set_editor_property("relative_rotation", ROT)
    try:
        smc.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    except Exception:
        pass
    set_no_collision(smc)
    ok = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert ok, f"compile {bp_path}"
    unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"wired {bp_path} mesh={sm_path} scale={scale}")


def patch_da_weapon_mesh(da_hint: str, sm_path: str) -> None:
    mesh = unreal.EditorAssetLibrary.load_asset(sm_path)
    for a in unreal.EditorAssetLibrary.list_assets("/Game/Data", recursive=True, include_folder=False):
        if da_hint.lower() not in a.lower():
            continue
        path = a.split(".")[0]
        da = unreal.EditorAssetLibrary.load_asset(path)
        if not da:
            continue
        for prop in ("WeaponMesh", "weapon_mesh"):
            try:
                da.set_editor_property(prop, mesh)
                unreal.EditorAssetLibrary.save_loaded_asset(da, only_if_is_dirty=False)
                log(f"DA {path} {prop} set")
                return
            except Exception:
                continue


def main() -> None:
    log("=== start ===")
    assert_not_pie()
    imported_vik = import_fbx(VIK_FBX, "SM_Blade_Viking_Mesh")
    imported_nin = import_fbx(NIN_FBX, "SM_Blade_Ninja_Mesh")
    apply_material(imported_vik, MAT_VIK)
    apply_material(imported_nin, MAT_NIN)
    wire_blade_bp(BP_VIK, imported_vik, SCALE_VIK, LOC_VIK)
    wire_blade_bp(BP_NIN, imported_nin, SCALE_NIN, LOC_NIN)
    patch_da_weapon_mesh("viking", imported_vik)
    patch_da_weapon_mesh("ninja", imported_nin)
    if unreal.EditorAssetLibrary.does_asset_exist(BP_HAND):
        wire_blade_bp(BP_HAND, imported_vik, SCALE_VIK, LOC_VIK)
    log("DONE IMPORT BLADE MESHES OK")
    log("Content Browser: SM_Blade_Viking_Mesh + SM_Blade_Ninja_Mesh (not the old Cube SM_*)")


if __name__ == "__main__":
    main()

