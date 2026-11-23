"""Run remaining pipeline in order: weapon drop physics → sword plan 1→3→2.

PIE STOPPED. In UE Output Log / Cmd:
  py "C:/kalsiyum_ue/Content/Python/faz_continue_all.py"
"""
import unreal

LOG = "[ContinueAll]"


def log(m):
    unreal.log(f"{LOG} {m}")


def run_script(path: str) -> None:
    log(f">>> {path}")
    # execfile-style so __name__ == "__main__" triggers
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()
    g = {"__name__": "__main__", "__file__": path}
    exec(compile(code, path, "exec"), g)


def main():
    log("=== start ===")
    base = unreal.Paths.project_content_dir() + "Python/"
    # Normalize for open()
    import os

    base = os.path.normpath(base)
    run_script(os.path.join(base, "fix_weapon_drop_physics.py"))
    run_script(os.path.join(base, "faz_sword_plan_123.py"))
    log("DONE CONTINUE ALL OK")


if __name__ == "__main__":
    main()
