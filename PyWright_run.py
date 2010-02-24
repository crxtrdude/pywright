#!/usr/bin/python
import sys,os
abspath = os.path.abspath(os.curdir)
print abspath
while "PyWright_run.app" in abspath:
    abspath = os.path.split(abspath)[0]
os.chdir(abspath)
f = open("logfile.txt","a")
f.write("running from:"+abspath+"\n")
sys.stderr = f
sys.stdout = f
sys.path.insert(0,"")
if len(sys.argv)>1:
    if sys.argv[1] == "editor":
        from core import libedit
    elif sys.argv[1] == "updater":
        from core import libupdate
        libupdate.run()
else:
    from core import libengine
    libengine.run()
