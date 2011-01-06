import os,sys
abspath = os.path.abspath(os.curdir)
f = open("logfile.txt","a")
sys.stderr = f
sys.stdout = f

sys.path.insert(0,"")

from core import libupdate
libupdate.run()
