#!/usr/bin/env python3
import pathlib,subprocess,sys,json,os
os.umask(0o077)
p=pathlib.Path(__file__).resolve().parent
allowed={"restore-streaming-shortcuts","restore-streaming-activation"}
if len(sys.argv)!=2 or sys.argv[1] not in allowed:raise SystemExit("Select a documented restore step")
name=sys.argv[1];out=p/(name+".json")
if out.exists():raise SystemExit("Evidence already exists; review before another execution")
r=subprocess.run(["python3",str(p.parent/"root-access/s95f-access.py"),"root","--timeout","30","--command",(p/(name+".sh")).read_text()],capture_output=True,text=True)
out.write_text(r.stdout);(p/(name+".stderr")).write_text(r.stderr)
if r.returncode:print(r.stderr,file=sys.stderr);raise SystemExit(r.returncode)
c=json.loads(r.stdout)["commands"][0];print(c["stdout"]);print(c["stderr"],file=sys.stderr);raise SystemExit(c["exit_code"])
