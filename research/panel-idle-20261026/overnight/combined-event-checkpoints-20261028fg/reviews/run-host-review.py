#!/usr/bin/env python3
"""Run the frozen FG mock suite with its temporary output redirected to reviews only."""
import pathlib,sys
sys.dont_write_bytecode=True
P=pathlib.Path(__file__).resolve().parent.parent
source=(P/'test-host.py').read_text()
old="dir=P/'host-environment/tmp'"
if source.count(old)!=1:raise ValueError('exact single temporary-directory relocation')
source=source.replace(old,"dir=P/'reviews/private'")
exec(compile(source,str(P/'test-host.py'),'exec'),{'__name__':'__main__','__file__':str(P/'test-host.py')})
