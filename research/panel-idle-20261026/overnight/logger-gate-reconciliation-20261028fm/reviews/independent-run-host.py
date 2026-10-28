#!/usr/bin/env python3
import pathlib,sys
sys.dont_write_bytecode=True
p=pathlib.Path(__file__).resolve().parent.parent
s=(p/'verify-host.py').read_text().replace("dir=P/'host-environment/tmp'","dir=P/'reviews/independent-private'")
exec(compile(s,str(p/'verify-host.py'),'exec'),{'__name__':'__main__','__file__':str(p/'verify-host.py')})
