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
import re

def write_cat(c):
    s = ""
    if isinstance(c,libengine.VALUE):
        s = c.name
    if isinstance(c,libengine.COMBINED):
        s = "["+c.name+"]"
    if isinstance(c,libengine.KEYWORD):
        s = c.name+"=VALUE"
    if isinstance(c,libengine.TOKEN):
        s = "<i>"+c.name+"</i>"
    if isinstance(c,libengine.ETC):
        s = "("+c.name+")"
    if isinstance(c,libengine.CHOICE):
        s = "&lt;"+" OR ".join([write_cat(c) for c in c.options])+"&gt;"
    s += " "
    return s
    
def expand_cat(cats):
    options = []
    for c in cats:
        if isinstance(c,libengine.CHOICE):
            options.extend(expand_cat(c.options))
        else:
            options.append(c)
    return options
    
def make_doc(txt):
    txt = txt.replace("{{{","<br><pre>")
    txt = txt.replace("}}}","</pre>")
    txt = re.sub("\n *\n","<br><br>",txt)
    s = "<p>"
    s+=txt
    s += "</p>"
    return s
    
def make_func_block(func):
    s = ""
    if not func.__doc__:
        return
    s = """<p>
    <b>%(fname)s</b> %(cats)s
    </p>"""%{"fname":func.name[0],"cats":"".join([write_cat(c) for c in func.cat])}
    if func.cat:
        s+="<table border=1><tr><td>Name</td><td>Description</td><td>Default value</td></tr>"
        for c in expand_cat(func.cat):
            if not hasattr(c,"name"):
                continue
            s+="<tr><td>"+c.name+"</td><td>"+c.description+"</td>"
            if c.default is not None:
                s+="<td>"+str(c.default)+"</td></tr>"
        s+="</table>"
    s+=make_doc(func.__doc__)
    s+="<br><br>"
    return s
        
commands = {}

f = open("docs/index.html","w")
f.write("<html><body>")

funcs = {}

#First, get all commands. This is relatively easy. Relatively...
scr = libengine.Script
for fname in dir(scr):
    if not fname.startswith("_"):
        continue
    if fname.startswith("__"):
        continue
    if fname == "_gchildren":
        continue
    func = getattr(scr,fname)
    if hasattr(func,"ftype") and func.__doc__:
        list = funcs.get(func.ftype,[])
        list.append(func)
        func.name[0] = fname[1:]
        funcs[func.ftype] = list

f.write("<div style=''>")
for group in funcs:
    f.write("<a href=#"+group+">"+group+"</a><br>")
f.write("</div><div style=''>")
        
for group in funcs:
    f.write("<a name='"+group+"'>")
    f.write("<h2>"+group+"</h2>")
    for func in funcs[group]:
        f.write(make_func_block(func))
f.write("</div>")
f.write("</body></html>")