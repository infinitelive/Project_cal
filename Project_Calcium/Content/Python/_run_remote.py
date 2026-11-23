"""Send fix_blade_collision.py to a running Unreal Editor via remote execution."""
import sys
import time
from pathlib import Path

ENGINE_REMOTE = Path(r"D:\Unreal Engine\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
sys.path.insert(0, str(ENGINE_REMOTE))

from remote_execution import RemoteExecution, MODE_EXEC_FILE  # noqa: E402

SCRIPT = Path(r"C:\kalsiyum_ue\Content\Python\fix_blade_collision.py")


def main() -> int:
    if not SCRIPT.is_file():
        print(f"MISSING {SCRIPT}")
        return 2
    remote = RemoteExecution()
    remote.start()
    try:
        deadline = time.time() + 8.0
        nodes = []
        while time.time() < deadline:
            nodes = remote.remote_nodes
            if nodes:
                break
            time.sleep(0.5)
        if not nodes:
            print("NO_REMOTE_NODES — enable Editor Preferences > Python > Remote Execution")
            return 1
        node_id = nodes[0]["node_id"]
        print(f"NODE {node_id} data={nodes[0]}")
        remote.open_command_connection(node_id)
        result = remote.run_command(str(SCRIPT), exec_mode=MODE_EXEC_FILE, unattended=False)
        print(f"RESULT {result}")
        ok = bool(result.get("success")) if isinstance(result, dict) else False
        return 0 if ok else 3
    finally:
        remote.stop()


if __name__ == "__main__":
    raise SystemExit(main())
