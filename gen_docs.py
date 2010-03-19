"""
This is an attempt to generate an api for pywright. Old method of methodically
tracking everything just doesn't cut it!
"""


#import stuff to get started
import os,sys
engine = open("core/libengine.py").read().split("\n")
core = open("core/core.py").read().split("\n")
sys.path.insert(0,"core")
import libengine
import core
import inspect
        
commands = {}

#First, get all commands. This is relatively easy. Relatively...
scr = libengine.Script
for fname in dir(scr):
    if not fname.startswith("_"):
        continue
    if fname.startswith("__"):
        continue
    if fname == "_gchildren":
        continue
    f = getattr(scr,fname)
    if f.__doc__:
        print fname[1:]
        print f.cat
        print f.__doc__