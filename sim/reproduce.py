"""Re-run a saved run from its own copies of the inputs and code, and check the numbers match.

Usage:  python reproduce.py runs/<run_id>
"""
import json
import os
import subprocess
import sys
import tempfile

run_dir = os.path.abspath(sys.argv[1])
manifest = json.load(open(os.path.join(run_dir, "manifest.json"), encoding="utf-8"))
out = tempfile.mkdtemp(prefix="secret_onu_repro_")
env = dict(os.environ, SECRET_ONU_ROOT=os.path.join(run_dir, "inputs"), SECRET_ONU_OUT=out)
subprocess.run([sys.executable, os.path.join(run_dir, "code", "make_report.py"), str(manifest["games_per_cell"])],
               env=env, check=True, cwd=os.path.join(run_dir, "code"))
old = json.load(open(os.path.join(run_dir, "results.json")))
new = json.load(open(os.path.join(out, "results.json")))
if old == new:
    print(f"OK: run {manifest['run_id']} reproduced exactly.")
else:
    print(f"DIFFERENT: run {manifest['run_id']} did not reproduce. Compare {out} with {run_dir}.")
    sys.exit(1)
