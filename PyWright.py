import sys,pickle,os
abspath = os.path.abspath(os.curdir)
while "PyWright.app" in abspath:
    abspath = os.path.split(abspath)[0]
os.chdir(abspath)
f = open("logfile.txt","a")
f.write("changed to:"+abspath+"\n")
f.close()
#sys.stderr = f
#sys.stdout = f
sys.path.insert(0,"")
from core import libengine
libengine.run()
#~ import profile
#~ profile.run("libengine.run()")
