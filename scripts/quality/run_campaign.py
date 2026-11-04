"""Run explicit campaign-owned tests using a caller-selected private environment."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil
import tempfile
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
selection=json.loads((Path(__file__).with_name("campaign-selection.json")).read_text())
groups=sorted({str(Path(path).parent) for path in selection})
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output-dir",type=Path,required=True)
parser.add_argument("--extra-path",action="append",type=Path,default=[])
parser.add_argument("--group",action="append",choices=groups,help="Choose existing campaign directory groups; default all")
parser.add_argument("--select",action="append",default=[],help="One campaign file or file::test identifier; repeat for a changed subset")
args=parser.parse_args()
chosen=[path for path in selection if not args.group or str(Path(path).parent) in args.group]
if args.select:
    if any(value.split('::')[0] not in chosen for value in args.select):parser.error("--select must name a selected campaign file")
    chosen=args.select
if not chosen:parser.error("No campaign test files selected")
out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
# Preserve prior evidence, but never parse it as this invocation's result.
previous = [p for p in out.iterdir() if not p.name.startswith('previous-')]
if previous:
    history = Path(tempfile.mkdtemp(prefix='previous-', dir=out))
    for artifact in previous:
        shutil.move(str(artifact), history / artifact.name)

(out/"tmp").mkdir(exist_ok=True)
(out/"mpl").mkdir(exist_ok=True)
extra=list(args.extra_path)+[Path(path) for path in os.environ.get("FILE50_TEST_DEP_PATHS","").split(os.pathsep) if path]
env={"PATH":"/usr/bin:/bin","LANG":os.environ.get("LANG","C.UTF-8")}
env.update(PYTHONPATH=os.pathsep.join([*(str(path.resolve()) for path in extra),str(ROOT/"scripts/quality"),str(ROOT/"scripts/offline"),str(ROOT),str(ROOT/"app")]),PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",PYTHONDONTWRITEBYTECODE="1",OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",PROJ_NETWORK="OFF",AWS_EC2_METADATA_DISABLED="true",AWS_CONFIG_FILE=os.devnull,AWS_SHARED_CREDENTIALS_FILE=os.devnull,BOTO_CONFIG=os.devnull,AWS_ACCESS_KEY_ID="offline",AWS_SECRET_ACCESS_KEY="offline",AWS_DEFAULT_REGION="us-east-1",OFFLINE_OUTPUT=str(out),GIT_NO_LAZY_FETCH="1",TMPDIR=str(out/"tmp"),MPLCONFIGDIR=str(out/"mpl"),MPLBACKEND="Agg",COVERAGE_FILE=str(out/".coverage"))
records=[]
commands=[]
returncodes=[]
combined=ET.Element("testsuites")
# Bare helper module names belong to each campaign directory. A fresh process
# prevents one directory's support.py and fixture modules leaking into another.
for number,group in enumerate(sorted({str(Path(path.split("::")[0]).parent) for path in chosen})):
 group_files=[path for path in chosen if str(Path(path.split("::")[0]).parent)==group]
 group_out=out/("group-"+str(number));group_out.mkdir(exist_ok=True)
 group_env=dict(env)
 group_env["PYTHONPATH"]=str(ROOT/group)+os.pathsep+env["PYTHONPATH"]
 group_env["COVERAGE_FILE"]=str(group_out/".coverage")
 command=[sys.executable,"-m","coverage","run","--branch","--source=.","-m","pytest","-c",os.devnull,"--rootdir="+str(ROOT),"-p","quality_boundary","-p","pytest_mock","--import-mode=importlib","-q","--junitxml="+str(group_out/"junit.xml"),*group_files]
 for plugin in ["offline_guard","offline_sdk"]:
  if (ROOT/"scripts/offline"/(plugin+".py")).exists():command[command.index("-p"):command.index("-p")]=["-p",plugin]
 result=subprocess.run(command,cwd=ROOT,env=group_env,text=True,capture_output=True)
 commands.append({"group":group,"command":command});returncodes.append(result.returncode)
 (group_out/"execution.log").write_text(result.stdout+"\n"+result.stderr)
 report=subprocess.run([sys.executable,"-m","coverage","json","-o",str(group_out/"coverage.json")],cwd=ROOT,env=group_env,text=True,capture_output=True)
 (group_out/"coverage-report.log").write_text(report.stdout+report.stderr)
 if (group_out/"junit.xml").exists():
  xml=ET.parse(group_out/"junit.xml").getroot()
  for suite in ([xml] if xml.tag=="testsuite" else list(xml)):combined.append(suite)
  for case in xml.findall(".//testcase"):
   records.append({"id":case.get("classname","")+"::"+case.get("name",""),"group":group,"result":"failed" if case.find("failure") is not None else "error" if case.find("error") is not None else "skipped" if case.find("skipped") is not None else "passed"})
ET.ElementTree(combined).write(out/"junit.xml",encoding="unicode")
returncode=max(returncodes,default=2)
counts={"total":len(records),"passed":sum(r["result"]=="passed" for r in records),"failed":sum(r["result"]=="failed" for r in records),"errors":sum(r["result"]=="error" for r in records),"skipped":sum(r["result"]=="skipped" for r in records)}
(out/"cases.json").write_text(json.dumps({**counts,"records":records,"returncode":returncode,"commands":commands,"selected_files":chosen,"extra_paths":[str(p.resolve()) for p in extra]},indent=2)+"\n")
print(json.dumps({**counts,"returncode":returncode}))
raise SystemExit(returncode or (0 if records else 2))
