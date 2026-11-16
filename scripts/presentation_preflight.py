"""Read-only dependency check for the selected research-presentation route."""
import argparse,importlib.util,json,sys,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--mode',choices=['wps','svg','all'],default='wps')
args=parser.parse_args()
modules=['pptx','PIL']
files=['scripts/research_deck.py','scripts/wps_manifest.py','scripts/visual_review.py','references/visible-authoring.md']
if args.mode in ('svg','all'):
    modules+=['xlsxwriter','yaml','lxml','numpy','matplotlib','pandas','seaborn','requests','bs4','flask','pathops','uharfbuzz']
    files+=['scripts/ppt_backend.py','scripts/research_chart.py','vendor/ppt-master/UPSTREAM_COMMIT','vendor/ppt-master/scripts/svg_to_pptx.py','vendor/ppt-master/scripts/svg_quality_checker.py']
checks={name:importlib.util.find_spec(name) is not None for name in modules}
checks.update({name:(root/name).is_file() for name in files})
if args.mode in ('wps','all'):
    py=root.parents[1]/'tools/harness-anything/.venv/Scripts/python.exe'
    checks['wps_python']=py.is_file()
    if py.is_file():
        probe=subprocess.run([str(py),'-c','import win32com.client,win32gui'],capture_output=True)
        checks['wps_com_modules']=probe.returncode==0
print(json.dumps({'mode':args.mode,'python':sys.executable,'checks':checks,'passed':all(checks.values()),'network_and_target_application':'checked during actual use; no application opened by this check'},indent=2))
sys.exit(0 if all(checks.values()) else 1)
