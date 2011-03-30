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
    while 1:
        m = re.search("<\w*?>",txt)
        if not m:
            break
        ot = txt[m.start():m.end()]
        nt = '<a href="#%(x)s">%(x)s</a>'%{"x":ot[1:-1]}
        txt = txt.replace(ot,nt)
    txt = txt.replace("{{{","<br><pre style='background-color:#eeeeff;padding:5px;border-width:1px;border-style:solid'>")
    txt = txt.replace("}}}","</pre>")
    txt = re.sub("\n *\n","<br><br>",txt)
    s = "<p>"
    s+=txt
    s += "</p>"
    return s
    
def make_func_block(func):
    s = "<div style='background-color:#eeeeee;padding:10px'>"
    if not func.__doc__:
        return
    s += """<a name="%(fname)s"><p>
    <b>%(fname)s</b> %(cats)s
    </p>"""%{"fname":func.name[0],"cats":"".join([write_cat(c) for c in func.cat])}
    if func.cat:
        s+="<table><tr><th>Name</th><th>Description</th><th>Default value</th></tr>"
        for c in expand_cat(func.cat):
            if not hasattr(c,"name"):
                continue
            s+="<tr><td>"+c.name+"</td><td>"+c.description+"</td>"
            if c.default is not None:
                s+="<td>"+str(c.default)+"</td></tr>"
            #~ else:
                #~ s+="<td style='background-color:#bababa'></td>"
        s+="</table>"
    s+=make_doc(func.__doc__)
    s+="</div>"
    s+="<br><br>"
    return s
        
commands = {}


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

def desig(line):
    code = "{%s}"%line[5:].strip() 
    d = eval(code)
    if d.get('args',None):
        d['args'] = [libengine.VALUE(*x) for x in d['args']]
    return d
def addmfunc(d):
    class x:
        pass
    fu = x()
    fu.name = [d['name']]
    fu.type = d['type']
    fu.__doc__ = d['desc']
    fu.cat = d['args']
    list = funcs.get(d['type'],[])
    list.append(fu)
    funcs[d['type']] = list
for macro in os.listdir("core/macros/"):
    d = {}
    mf = open("core/macros/"+macro)
    for line in mf.read().split("\n"):
        if d:
            d["name"] = line.split(" ")[1]
            addmfunc(d)
            d = {}
        if line.startswith("#@sig"):
            d = desig(line)

f = open("docs/index.html","w")
f.write("<html>")
f.write("""<style type='text/css'>
table
{
border-collapse:collapse;
}
table, th, td
{
border: 1px solid black;
font-size: 12px;
}
th
{
background-color:#88ff88;
}</style>""")
f.write("<body style='width:640px;background-color:#cccccc'>")
f.write("<div style=''>")
f.write("<h2>Command Categories</h2>")
for group in funcs:
    f.write("<a href=#"+group+">"+group+"</a><br>")
f.write("</div><br><br><br><br><br><hr><h3>Commands</h3><div style=''>")
        
for group in funcs:
    f.write("<a name='"+group+"'>")
    f.write("<h2>Category: "+group+"</h2>")
    for func in funcs[group]:
        f.write(make_func_block(func))
f.write("</div>")
f.write("</body></html>")


def find_variables():
    variables = {}
    classes = {}
    for fn in ["core/core.py","core/libengine.py"]:
        cur_class = ""
        class_tab_level = 0
        cur_func = ""
        func_tab_level = 0
        f = open(fn)
        lines = f.read().split("\n")
        f.close()
        tab_level = 0
        for si,l in enumerate(lines):
            if l.strip().startswith("#"):
                continue
            tab_level = l.rsplit(" ",1)[0].count(" ")
            if l.strip().startswith("class "):
                cur_class = re.findall("class \w*",l)[0]
                print cur_class
                class_tab_level = tab_level
            else:
                if cur_class and tab_level <= class_tab_level:
                    cur_class = ""
            if l.strip().startswith("def "):
                cur_func = l.strip().split(" ",1)[1].split("(",1)[0]
                func_tab_level = tab_level
            else:
                if cur_func and tab_level <= func_tab_level:
                    cur_func = ""
            if 'variables.get("' in l or 'variables["' in l:
                variable = l.strip()
                variable = re.findall('\"(.*?)\"',l)
                if not variable:
                    continue
                variable = variable[0]
                li = variables.get(variable,[])
                li.append((cur_class,cur_func,fn,si))
                variables[variable] = li
                li = classes.get(cur_class,[])
                li.append((variable,cur_func,fn,si))
                classes[cur_class] = li
    return variables,classes

variables,classes = find_variables()

f = open("docs/variables.txt","w")
for c in classes.items():
    f.write("%s:\n"%c[0])
    for var in c[1]:
        f.write("   %s - %s (%s %s)\n"%var)
f.close()

f = open("docs/variables2.txt","w")
for c in variables.items():
    f.write("%s:\n"%c[0])
    for var in c[1]:
        f.write("   %s - %s (%s %s)\n"%var)
f.close()
