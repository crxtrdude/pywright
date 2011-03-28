VERSION = "Beta 10.94"

from errors import script_error

import gc

# Recursively expand slist's objects
# into olist, using seen to track
# already processed objects.
def _getr(slist, olist, seen):
  for e in slist:
    if id(e) in seen:
      continue
    seen[id(e)] = None
    olist.append(e)
    tl = gc.get_referents(e)
    if tl:
      _getr(tl, olist, seen)

# The public function.
def get_all_objects():
  """Return a list of all live Python
  objects, not including the list itself."""
  gcl = gc.get_objects()
  olist = []
  seen = {}
  # Just in case:
  seen[id(gcl)] = None
  seen[id(olist)] = None
  seen[id(seen)] = None
  # _getr does the real work.
  _getr(gcl, olist, seen)
  return olist



import pickle
import zlib
import os,sys
if sys.platform=="win32":
    os.environ['SDL_VIDEODRIVER']='windib'
import random
from core import *
import gui


def pauseandquit():
    import time
    end = time.time()+5
    while time.time()<end:
        pass
    sys.exit()

#~ import psyco
#~ pscyo.full()
    
def category(cat):
    def _dec(f):
        f.cat = cat
        return f
    return _dec
    
delete_on_menu = [evidence,portrait,fg]
only_one = [textbox,testimony_blink,evidence_menu]
def addob(ob):
    if [1 for x in only_one if isinstance(ob,x)]:
        for o2 in assets.cur_script.obs[:]:
            if isinstance(o2,ob.__class__):
                o2.kill = 1
    assets.cur_script.obs.append(ob)
def addevmenu():
    addob(evidence_menu(assets.items))
def add_s(scene):
    s = Script()
    s.init(scene)
    assets.stack.append(s)
assets.addob = addob
assets.addevmenu = addevmenu
assets.addscene = add_s

def parseargs(arglist,intvals=[],defaults = {},setzero = {}):
    kwargs = {}
    kwargs.update(defaults)
    args = []
    for a in arglist:
        if "=" in a:
            a = a.split("=",1)
            if a[0] in intvals: 
                try:
                    kwargs[a[0]] = int(a[1])
                except:
                    kwargs[a[0]] = float(a[1])
            else: 
                kwargs[a[0]]=a[1]
        elif setzero.has_key(a):
            kwargs[setzero[a]]=0
        else:
            kwargs[a] = 1
    return kwargs,args
    
def argsort(list,arg="pri",get=getattr):
    def _cmp(a,b):
        return cmp(get(a,arg),get(b,arg))
    list.sort(_cmp)
def getz(ob,arg):
    v = getattr(ob,arg)
    if type(v)==type(""):
        v = assets.variables.get(v,0)
    return v

class World:
    """A collection of objects"""
    def __init__(self,obs=None):
        if not obs: obs = []
        self.all = obs[:]
        for o in self.all:
            o.cur_script = assets.cur_script
    def render_order(self):
        """Return a list of objects in the order they should
        be rendered"""
        class mylist(list): pass
        n = mylist(self.all[:])
        argsort(n,"z")
        oldapp = n.append
        def _app(ob):
            self.append(ob)
            oldapp(ob)
        n.append = _app
        return n
    def click_order(self):
        """Return a list of objects in the order they should
        be checked for clicks"""
        n = reversed(self.render_order())
        return n
    def update_order(self):
        """Return a list of objects in the order they
        should be updated"""
        n = self.all[:]
        argsort(n,"pri")
        return n
    def select(self):
        """Return a list of objects that match the query"""
    def append(self,ob):
        self.all.append(ob)
        ob.cur_script = assets.cur_script
    def extend(self,obs,unique=True):
        if unique:
            for o in obs:
                if o not in self.all:
                    self.all.append(o)
        else:
            self.all.extend(o)
    def remove(self,ob):
        self.all.remove(ob)

class Script(gui.widget):
    def __init__(self,parent=None):
        self.world = World()
        
        #widget stuff
        self.rpos = [0,0]
        self.parent = parent
        self.viewed = {}  #keeps track of viewed textboxes
        self.imgcache = {}  #Used to preload images
        self.lastline = ""  #Remember where we jumped from in a script so we can go back
        self.lastline_value = ""   #Remember last line we executed
        self.held = []
    obs = property(lambda self: self.world.render_order(),lambda self,val: setattr(self,"world",World(val)))
    upobs = property(lambda self: self.world.update_order())
    def _gchildren(self): return self.world.click_order()
    children = property(_gchildren)
    width = property(lambda x: sw)
    height = property(lambda x: sh*assets.num_screens)
    def handle_events(self,evts):
        n = []
        w = float(sw)/assets.swidth
        h = float(sh)/assets.sheight
        def dp(p):
            return [int(w*p[0]),int(h*p[1])]
        for e in evts:
            if e.type==pygame.MOUSEMOTION:
                d = {"rel":e.rel,"buttons":e.buttons}
                d["pos"] = dp(e.pos)
                e = pygame.event.Event(pygame.MOUSEMOTION,d)
            if e.type==pygame.MOUSEBUTTONUP:
                d = {"button":e.button}
                d["pos"] = dp(e.pos)
                e = pygame.event.Event(pygame.MOUSEBUTTONUP,d)
            if e.type==pygame.MOUSEBUTTONDOWN:
                d = {"button":e.button}
                d["pos"] = dp(e.pos)
                e = pygame.event.Event(pygame.MOUSEBUTTONDOWN,d)
            n.append(e)
        gui.widget.handle_events(self,n)
    def save(self):
        return pickle.dumps([self.scene,self.si,self.cross,self.statement,self.instatement,self.lastline,self.pri,self.viewed])
    def load(self,s):
        vals = pickle.loads(s)
        self.scene,self.si,self.cross,self.statement,self.instatement,self.lastline,self.pri = vals[:7]
        self.init(self.scene)
        self.scene,self.si,self.cross,self.statement,self.instatement,self.lastline,self.pri = vals[:7]
        if len(vals)>7:
            self.viewed = vals[7]
        self.si-=1
    def init(self,scene="",macros=True,ext=".txt",scriptlines=None):
        self.imgcache.clear()
        self.scene = scene
        self.scriptlines = []
        if scriptlines:
            self.scriptlines = scriptlines
        self.macros = {}
        if scene:
            self.scriptlines = assets.open_script(scene,macros,ext)
            self.macros = assets.macros
        self.labels = []
        for i,line in enumerate(self.scriptlines):
            if line.startswith("label ") or line.startswith("result "):
                rn = line.split(" ",1)[1].strip().replace(" ","_")
                if rn:
                    self.labels.append([rn,i])
            if line.startswith("list ") or line.startswith("cross ") or line.startswith("statement "):
                rn = line.split(" ",1)[1].strip().replace(" ","_")
                if rn:
                    self.labels.append([rn,i-1])
        self.si = 0

        self.cross = None
        self.statement = ""
        self.instatement = False
        self.lastline = 0
        self.pri = 0
        
        self.held = []
        #~ if vtrue(assets.variables.get("_preload","on")):
            #~ self.preload()
        
    def preload(self):
        old = self.obs[:]
        self.obs = []
        import time
        t = time.time()
        nt = time.time()
        for line in self.scriptlines:
            if line.strip().startswith("set _preload") and line[13:].strip() in ["0","off","false"]:
                return
            if line.strip()=="preload_cancel": return
            try:
                args = [x for x in line.split(" ")]
            except:
                pass
            if not args: continue
            if args[0] not in ["bg","char","fg","ev","mesh"]: continue
            func = getattr(self,"_"+args[0],None)
            if func:
                try:
                    func(*args)
                except:
                    pass
            nt = time.time()
            if nt-t>1.5:
                pygame.screen.blit(arial14.render("Loading Script...",1,[255,255,255]),[0,100])
                draw_screen()
        self.obs = old[:]
    def getline(self):
        try:
            line = self.scriptlines[self.si]
            line = line.replace("\t","    ")
            line = line.replace("\r","").replace("\n","")
            line = line.rsplit("#",1)[0]
            line = line.rsplit("//",1)[0]
            self.lastline_value = line.strip()
            return line.strip()
        except TypeError:
            return
        except IndexError:
            return
    def update_objects(self):
        for o in self.world.update_order():
            if o.update():
                if o.cur_script==self: return False
        return True
    def update(self):
        try:
            if self.update_objects():
                self.interpret()
        except script_error,e:
            self.obs.append(error_msg(e.value,self.lastline_value,self.si,self))
            import traceback
            traceback.print_exc()
            return
        except art_error,e:
            if vtrue(assets.variables.get("_debug","false")):
                self.obs.append(error_msg(e.value,self.lastline_value,self.si,self))
                import traceback
                traceback.print_exc()
                return
        except markup_error,e:
            self.obs.append(error_msg(e.value,self.lastline_value,self.si,self))
            import traceback
            traceback.print_exc()
            return
        except Exception,e:
            self.obs.append(error_msg("Undefined:"+e.message,self.lastline_value,self.si,self))
            import traceback
            traceback.print_exc()
            return
    def draw(self,screen):
        for o in self.obs:
            if not getattr(o,"hidden",False) and not getattr(o,"kill",False):
                o.draw(screen)
    def tboff(self):
        for o in self.obs:
            if isinstance(o,testimony_blink):
                self.world.remove(o)
                break
    def tbon(self):
        addob(testimony_blink("testimony"))
    def state_test_true(self,test):
        if test is None:
            return True
        return vtrue(assets.variables.get(test,"false"))
    def interpret(self):
        self.buildmode = True
        while self.buildmode:
            line = self.getline()
            while not line:
                if line is None: 
                    return self._endscript()
                self.si += 1
                line = self.getline()
            #print "exec(",repr(line),")"
            assets.variables["_currentline"] = str(self.si+1)
            if line.startswith('"') and len(line)>1:
                line = line[1:]
                if line.rstrip()[-1]=='"':
                    line = line[:-1]
                text = line.replace("{n}","\n")
                tbox = textbox(text)
                if not self.viewed.get(assets.game+self.scene+str(self.si)):
                    tbox.can_skip = False
                if vtrue(assets.variables.get("_debug","false")):
                    tbox.can_skip = True
                if vtrue(assets.variables.get("_textbox_allow_skip","false")):
                    tbox.can_skip = True
                self.viewed[assets.game+self.scene+str(self.si)] = True
                addob(tbox)
                arrows = [x for x in self.obs if isinstance(x,uglyarrow) and not getattr(x,"kill",0)]
                if vtrue(assets.variables.get("_textbox_show_button","true")):
                    if not arrows:
                        arrows = [uglyarrow()]
                        self.obs.append(arrows[0])
                    arrows[0].textbox = tbox
                    if assets.variables.get("_statements",[]):
                        statements = [x for x in assets.variables["_statements"] if self.state_test_true(x["test"])]
                        if statements and statements[0]["words"] == self.statement:
                            arrows[0].showleft = False
                        else:
                            arrows[0].showleft = True
                else:
                    [setattr(x,"kill",1) for x in arrows]
                self.tboff()
                if self.cross is not None and self.instatement:
                    self.tbon()
                    if self.cross == "proceed":
                        tbox.statement = self.statement
                        nt,t = tbox._text.split("\n",1)
                        tbox._text = nt+"\n{c283}"+t
                        #tbox.color = (20,200,40)
                self.si += 1
                return
            self.si += 1
            def repvar(x):
                if x.startswith("$") and not x[1].isdigit():
                    return assets.variables[x[1:]]
                elif x.startswith("$"):
                    return ""
                if "=" in x:
                    spl = x.split("=",1)
                    if spl[1].startswith("$"):
                        return spl[0]+"="+assets.variables[spl[1][1:]]
                return x
            args = []
            try:
                args = [repvar(x) for x in line.split(" ")]
            except KeyError:
                self.obs.append(error_msg("Variable not defined:",line,self.si,self))
                return
            if self.execute_macro(args[0]):
                return
            func = getattr(self,"_"+args[0],None)
            if func: 
                func(*args)
            elif vtrue(assets.variables.get("_debug","false")): 
                self.obs.append(error_msg("Invalid command",line,self.si,self))
                return
    def execute_macro(self,macroname,args="",obs=None):
        mlines = self.macros.get(macroname,None)
        if not mlines: return
        if args: args = " "+args
        nscript = Script(self)
        nscript.world = self.world
        scriptlines = ["{"+macroname+args+"}"]
        assets.replace_macros(scriptlines,self.macros)
        nscript.init(scriptlines=scriptlines)
        nscript.macros = self.macros
        assets.stack.append(nscript)
        self.buildmode = False
        return nscript
    def next_statement(self):
        if not assets.variables.get("_statements",[]):
            return
        which = None
        for s in assets.variables["_statements"]:
            if not self.state_test_true(s["test"]):
                continue
            #return
            if s["index"]>self.si and s["words"]!=self.statement:
                which = s["index"]
                break
        if which is not None:
            self.si = which
    def prev_statement(self):
        if not assets.variables.get("_statements",[]):
            return
        which = None
        for s in reversed(assets.variables["_statements"]):
            if not self.state_test_true(s["test"]):
                continue
            if s["index"]<self.si and s["words"]!=self.statement:
                which = s["index"]
                break
        if which is not None:
            self.si = which
        else:
            self.si -= 1
    def goto_result(self,name,wrap=False,backup="none"):
        for o in self.obs:
            if isinstance(o,guiWait): o.kill = 1
        if name.startswith("{") and name.endswith("}"):
            self.execute_macro(name[1:-1])
            return
        name = name.replace(" ","_")
        wrap=True
        first = None
        self.lastline = self.si
        self.instatement = False
        assets.variables["_lastline"] = str(self.si)
        for label,index in self.labels:
            if not first and label==name:
                first = index
                assets.variables["_currentlabel"] = label
            if label == name and index>=self.si:
                self.si = index+1
                assets.variables["_currentlabel"] = label
                return
            if label == backup and index>self.si:
                self.si = index+1
                assets.variables["_currentlabel"] = backup
                return
        if first is not None and wrap:
            self.si = first+1
            return
        try:
            name = int(name)-1
        except:
            print self.labels
            print name
            raise script_error,"no label \""+name+"\" to go to."
        if name>=len(self.scriptlines) or name<0:
            raise script_error,"Trying to go to invalid line number"
        self.si = name+1
    def _draw_on(self,*args):
        assets.variables["render"] = 1
    def _draw_off(self,*args):
        assets.variables["render"] = 0
    def _print(self,*args):
        print " ".join(args[1:])
    @category("control")
    def _endscript(self,*args):
        self.buildmode = False
        if self in assets.stack:
            assets.stack.remove(self)
            if "enter" in self.held: self.held.remove("enter")
            if self.parent:
                self.parent.held = []
                self.parent.world = self.world
        if not assets.stack:
            assets.variables.clear()
            assets.stop_music()
            assets.stack[:] = []
            make_start_script(False)
        return
    @category("control")
    def _debug(self,command,value):
        if value.lower() in ["on","1","true"]:
            assets.variables["_debug"] = "on"
        else:
            assets.variables["_debug"] = "off"
    @category("control")
    def _label(self,command,*name):
        assets.variables["_lastlabel"] = " ".join(name)
    @category("control")
    def _game(self,command,game,script="intro"):
        for o in self.obs[:]:
            o.kill = 1
        assets.clear()
        assets.game = game
        self.held = []
        scene = script
        #assets.addscene(scene)
        self.init(scene)
    @category("control")
    def _goto(self,command,place):
        self.goto_result(place,wrap=True,backup=None)
    def flag_logic(self,value,*args):
        args = list(args)
        label = args.pop(-1)
        if label.endswith("?"):
            args.append(label[:-1])
            label = "?"
        sentance = ""
        mode = 0
        for a in args:
            if mode == 0:
                sentance+="('"+a+"' in assets.variables)"
            elif mode == 1:
                if a=="AND": sentance+=" and "
                elif a=="OR": sentance+=" or "
                else: raise script_error("Logic must be AND or OR")
            mode = 1-mode
        if not eval(sentance)==value: return self.fail(label)
        self.succeed(label)
    @category("control")
    def _noflag(self,command,*args):
        self.flag_logic(False,*args)
    @category("control")
    def _flag(self,command,*args):
        self.flag_logic(True,*args)
    @category("control")
    def _setflag(self,command,flag):
        if flag not in assets.variables: assets.variables[flag]="true"
    @category("control")
    def _delflag(self,command,flag):
        if flag in assets.variables: del assets.variables[flag]
    @category("control")
    def _set(self,command,variable,*args):
        value = " ".join(args)
        assets.variables[variable]=value
    _setvar = _set
    def _random(self,command,variable,start,end):
        random.seed(pygame.time.get_ticks()+random.random())
        value = random.randint(int(start),int(end))
        assets.variables[variable]=str(value)
    @category("control")
    def _joinvar(self,command,variable,*args):
        value = "".join(args)
        assets.variables[variable]=value
    @category("control")
    def _addvar(self,command,variable,value):
        oldvalue = int(assets.variables.get(variable,0))
        oldvalue += int(value)
        assets.variables[variable] = str(oldvalue)
    @category("control")
    def _subvar(self,command,variable,value):
        oldvalue = int(assets.variables[variable])
        oldvalue -= int(value)
        assets.variables[variable] = str(oldvalue)
    @category("control")
    def _mulvar(self,command,variable,value):
        oldvalue = int(assets.variables[variable])
        oldvalue *= int(value)
        assets.variables[variable] = str(int(oldvalue))
    @category("control")
    def _divvar(self,command,variable,value):
        oldvalue = int(assets.variables[variable])
        oldvalue /= float(value)
        assets.variables[variable] = str(int(oldvalue))
    @category("control")
    def _absvar(self,command,variable):
        oldvalue = int(assets.variables.get(variable,0))
        oldvalue = abs(int(oldvalue))
        assets.variables[variable] = str(oldvalue)
    def _exportvars(self,command,filename,*vars):
        d = {}
        if not vars:
            vars = assets.variables.keys()
        for k in vars:
            d[k] = assets.variables.get(k,"")
        filename = filename.replace("..","").replace(":","")
        while filename.startswith("/"):
            filename = filename[1:]
        f = open(assets.game+"/"+filename,"w")
        f.write(repr(d))
        f.close()
    def _importvars(self,command,filename):
        filename = filename.replace("..","").replace(":","")
        while filename.startswith("/"):
            filename = filename[1:]
        try:
            f = open(assets.game+"/"+filename)
        except:
            return
        txt = f.read()
        f.close()
        if txt.strip():
            d = eval(txt)
            assets.variables.update(d)
    def _savegame(self,command,*args):
        filename = "save"
        hide = False
        args = list(args)
        if "hide" in args:
            hide = True
            args.remove("hide")
        if args:
            filename = args[0]
        self.si += 1
        assets.variables["_allow_saveload"] = "true"
        assets.save_game(filename,hide)
        self.si -= 1
    def _loadgame(self,command,*args):
        filename = "save"
        hide = False
        args = list(args)
        if "hide" in args:
            hide = True
            args.remove("hide")
        if args:
            filename = args[0]
        assets.variables["_allow_saveload"] = "true"
        assets.load_game(None,filename,hide)
        return self._endscript()
    def _deletegame(self,command,path):
        if "/" in path or "\\" in path:
            raise script_error("Invalid save file path:'%s'"%(path,))
        path = assets.game+"/"+path
        t = open(path,"r").read()
        try:
            print t[:10],t[-10:]
            assert t.startswith("(lp0..--..") and t.endswith("end\n")
        except AssertionError:
            raise script_error("Cannot delete non-save")
        try:
            os.remove(path)
        except:
            raise script_error("Could not delete save file, file in use or protected")
    @category("control")
    def _is(self,command,*args):
        args = list(args)
        label = args.pop(-1)
        if label.endswith("?"):
            args.append(label[:-1])
            label = "?"
        def EVAL(stuff):
            stuff = stuff.split(" ",2)
            if len(stuff)==2:
                stuff = stuff[0],"=",stuff[1]
            current,op,check = stuff
            if op not in ["<",">","=","<=",">=","="]:
                check = op+" "+check
                op = "="
            current = assets.variables.get(current)
            if op=="=":op="=="
            if op!="==":
                current = int(current)
                check = int(check)
            return eval(repr(current)+op+repr(check))
        def OR(stuff):
            for line in stuff:
                if EVAL(line):
                    return True
            return False
        args = " ".join(args).split(" AND ")
        args = [x.split(" OR ") for x in args]
        args = [OR(x) for x in args]
        if False in args: return self.fail(label)
        self.succeed(label)
    @category("control")
    def _isnot(self,command,*args):
        args = list(args)
        label = args.pop(-1)
        if label.endswith("?"):
            args.append(label[:-1])
            label = "?"
        def EVAL(stuff):
            stuff = stuff.split(" ",2)
            if len(stuff)==2:
                stuff = stuff[0],"=",stuff[1]
            current,op,check = stuff
            if op not in ["<",">","=","<=",">=","="]:
                check = op+" "+check
                op = "="
            current = assets.variables.get(current)
            if op=="=":op="=="
            if op!="==":
                current = int(current)
                check = int(check)
            return eval(repr(current)+op+repr(check))
        def OR(stuff):
            for line in stuff:
                if EVAL(line):
                    return True
            return False
        args = " ".join(args).split(" AND ")
        args = [x.split(" OR ") for x in args]
        args = [OR(x) for x in args]
        if False in args: return self.succeed(label)
        self.fail(label)
    @category("control")
    def _isempty(self,command,variable,label=None):
        if variable.endswith("?"):
            variable = variable[:-1]
            label = "?"
        if not assets.variables.get(variable,None): return self.succeed(label)
        self.fail(label)
    @category("control")
    def _isnotempty(self,command,variable,label=None):
        if variable.endswith("?"):
            variable = variable[:-1]
            label = "?"
        if assets.variables.get(variable,None): return self.succeed(label)
        self.fail(label)
    def succeed(self,label=None):
        """What happens when a test succeeds?"""
        if label == "?": label = None
        if label:
            self._goto(None,label)
        else:
            pass
    def fail(self,label=None):
        if label == "?": label = None
        if label:
            pass
        else:
            self.si += 1
    @category("control")
    def _isnumber(self,command,*args):
        args = list(args)
        label = args.pop(-1)
        if label.endswith("?"):
            args.append(label[:-1])
            label = "?"
        value = " ".join(args)
        if value.isdigit():
            return self.succeed(label)
        return self.fail(label)
    @category("control")
    def _nopenalty(self,*args):
        if assets.variables.get("penalty",100)<=0:
            self._goto(None,args[1])
    @category("control")
    def _pause(self,command,*args):
        self.buildmode = False
        ticks = None
        pri = 10000  #Will pause the script but nothing else
        for a in args:
            if a.startswith("priority="):
                pri = int(a[9:].strip())
            elif a=="all":
                pri = -1000
            elif a=="script":
                pri = 10000
            elif not ticks:
                ticks = float(a)
        if not ticks: ticks = 60
        do = delay(ticks)
        do.pri=pri
        self.obs.append(do)
    @category("control")
    def _waitenter(self,command):
        self.buildmode = False
        self.obs.append(waitenter())
    @category("control")
    def _exit(self,command):
        del assets.stack[-1]
    @category("control")
    def _menu(self,command,ascene):
        self.buildmode = False
        for o in self.obs:
            if o.__class__ in delete_on_menu:
                o.kill = 1
        m = menu()
        m.scene = ascene
        for scr in assets.list_casedir():
            if scr.startswith(m.scene+".") and scr not in [m.scene+".script.txt"]:
                m.addm(scr[scr.find(".")+1:scr.rfind(".")])
        self.scriptlines = []
        self.si = 0
        self.obs.append(m)
    @category("control")
    def _casemenu(self,command,*args):
        self.buildmode = False
        kwargs = {}
        pri = ([x[4:] for x in args if x.startswith("pri=")] or [None])[0]
        if pri is not None: kwargs["pri"] = pri
        self.obs.append(case_menu(assets.game,**kwargs))
    @category("control")
    def _script(self,command,scriptname,*args):
        if "noclear" not in args:
            for o in self.obs:
                o.kill = 1
        if "stack" in args:
            assets.addscene(scriptname+".script")
        else:
            self.init(scriptname+".script")
    @category("control")
    def _top(self,command):
        self.si = 0
    @category("graphics")
    def _obj(self,command,*args):
        func = {"bg":bg,"fg":fg,"ev":evidence,"mesh":mesh,"obj":graphic}[command]
        wait = {"fg":1}.get(command,0)
        clear = 1
        x = 0
        y = 0
        z = None
        loops = None
        fade = 0
        flipx = 0
        name = None
        more = {"rotx":0,"roty":0,"rotz":0}
        for a in args:
            if a.startswith("x="):
                x = int(a[2:])
            if a.startswith("y="):
                y = int(a[2:])
            if a.startswith("z="):
                z = int(a[2:])
            if a.startswith("loops="):
                loops = a[6:]
            if a=="flipx":
                flipx=1
            if a.startswith("name="):
                name = a[5:]
            if a.split("=")[0] in more.keys():
                more[a.split("=")[0]] = a.split("=")[1]
            if a=="stack":
                clear = 0
            if a=="nowait":
                wait = 0
        more["wait"] = wait
        if clear and func==bg:
            for o in self.obs[:]:
                if getattr(o,"autoclear",False):
                    o.kill = 1
                    self.world.remove(o)
        o = func(args[0],x=x,y=y,flipx=flipx,**more)
        if z is not None:
            o.z = z
        if not fade:
            o.setfade(255)
        if name:
            o.id_name = name
        else:
            o.id_name = args[0]
        self.obs.append(o)
        if "fade" in args: self._fade("fade","wait","name="+o.id_name,"speed=5")
        if loops is not None:
            o.loops = int(loops)
    def _movie(self,command,file,sound=None):
        self.buildmode = False
        m = movie(file,sound)
        self.obs.append(m)
    @category("graphics")
    def _bg(self,*args):
        self._obj(*args)
    @category("graphics")
    def _fg(self,*args):
        self._obj(*args)
    @category("graphics")
    def _ev(self,*args):
        self._obj(*args)
    @category("graphics")
    def _mesh(self,*args):
        self._obj(*args)
    @category("graphics")
    def _gui(self,command,guitype,*args):
        args = list(args)
        x=None
        y=None
        z=None
        name=""
        if guitype=="Back":
            while args:
                if args[0].startswith("x="): x=int(args[0][2:]); del args[0]; continue
                if args[0].startswith("y="): y=int(args[0][2:]); del args[0]; continue
                if args[0].startswith("z="): z=int(args[0][2:]); del args[0]; continue
                if args[0].startswith("name="): name=args[0][5:]; del args[0]; continue
                break
            print x,y,z
            self.obs.append(guiBack(x=x,y=y,z=z,name=name))
            self.buildmode = False
        if guitype=="Button":
            macroname=args[0]; del args[0]
            while args:
                if args[0].startswith("x="): x=int(args[0][2:]); del args[0]; continue
                if args[0].startswith("y="): y=int(args[0][2:]); del args[0]; continue
                if args[0].startswith("z="): z=int(args[0][2:]); del args[0]; continue
                if args[0].startswith("name="): name=args[0][5:]; del args[0]; continue
                break
            text = ""
            text = " ".join(args)
            btn = gui.button(None,text)
            btn.rpos = [x,y]
            btn.z = int(assets.variables["_layer_gui"])
            if z is not None: btn.z = z
            btn.pri = 0
            def func(*args):
                self.goto_result(macroname)
            setattr(btn,text.replace(" ","_"),func)
            self.obs.append(btn)
            if name: btn.id_name = name
            else: btn.id_name = "$$"+str(id(btn))+"$$"
        if guitype=="Wait":
            run = ""
            if args and args[0].startswith("run="): run = args[0].replace("run=","",1)
            self.obs.append(guiWait(run=run))
            self.buildmode = False
    @category("graphics")
    def _textblock(self,command,x,y,width,height,*text):
        id_name = None
        if text and text[0].startswith("name="): 
            id_name = text[0].replace("name=","",1)
            text = text[1:]
        tb = textblock(" ".join(text),[int(x),int(y)],[int(width),int(height)],surf=pygame.screen)
        self.obs.append(tb)
        if id_name: tb.id_name = id_name
        else: tb.id_name = "$$"+str(id(tb))+"$$"
    @category("event")
    def _penalty(self,command,amt,*args):
        var = "penalty"
        for a in args:
            if a.split("=")[0] == "variable":
                var = a.split("=",1)[1]
        if not amt.isdigit():
            end = int(assets.variables.get(var,100))+int(amt)
        else:
            end = int(amt)
        self.obs.append(penalty(end,var))
        self.buildmode = False
    @category("event")
    def _notguilty(self,*args):
        self.obs.append(notguilty())
        self.buildmode = False
    @category("event")
    def _guilty(self,*args):
        self.obs.append(guilty())
        self.buildmode = False
    @category("event")
    def _rotate(self,command,*args):
        kwargs,args = parseargs(args,intvals=["degrees","speed","wait"],
                                                defaults={"axis":"z",'wait':1},
                                                setzero={"nowait":"wait"})
        self.obs.append(rotateanim(obs=self.obs,**kwargs))
        if kwargs['wait']: self.buildmode = False
    @category("event")
    def _fade(self,command,*args):
        kwargs,args = parseargs(args,intvals=["start","end","speed","wait"],
                                                defaults={"start":0,"end":100,"speed":1,"wait":1},
                                                setzero={"nowait":"wait"})
        self.obs.append(fadeanim(obs=self.obs,**kwargs))
        if kwargs['wait']: self.buildmode = False
    @category("event")
    def _scroll(self,command,*args):
        x=0
        y=0
        speed = 1
        last = 0
        wait = 1
        name = None
        for a in args:
            if a.startswith("x="):
                x=int(a[2:])
            if a.startswith("y="):
                y=int(a[2:])
            if a.startswith("speed="):
                speed=int(a[6:])
            if a.startswith("last"):
                last = 1
            if a.startswith("nowait"):
                wait = 0
            if a.startswith("name="):
                name = a[5:]
        scr = scroll(x,y,speed,wait)
        self.obs.append(scr)
        if last:
            scr.control_last()
        if name:
            scr.control(name)
        if wait: self.buildmode = False
    @category("event")
    def _mus(self,command,*song):
        track = " ".join(song)
        if not track:
            assets.stop_music()
        else:
            assets.play_music(track)
    @category("event")
    def _sfx(self,command,*sound):
        after = 0
        if sound and sound[0].startswith("after="):
            after = float(sound[0].replace("after=","",1))
            sound = sound[1:]
        sound = " ".join(sound)
        self.obs.append(SoundEvent(sound,after))
    @category("text")
    def _nt(self,command,*name):
        nametag = " ".join(name)+"\n"
        assets.variables["_speaking"] = ""
        assets.variables["_speaking_name"] = nametag
    @category("text")
    def _char(self,command,character="",*args):
        assets.character = character
        #first arg is z value (or top for highest z)
        z = None
        e = "normal(blink)"
        x = 0
        y = 0
        pri = None
        name = None
        nametag = character+"\n"
        for a in args:
            if a.startswith("z="): z = int(a[2:])
            if a.startswith("e="): e = a[2:]+"(blink)"
            if a.startswith("x="): x = int(a[2:])
            if a.startswith("y="): y = int(a[2:])
            if a.startswith("priority="): pri = int(a[9:])
            if a.startswith("name="): name = a[5:]
            if a.startswith("nametag="): nametag = a[8:]+"\n"
        assets.px = x
        assets.py = y
        assets.pz = z
        p = assets.add_portrait(character+"/"+e,fade=("fade" in args),stack=("stack" in args),hide=("hide" in args))
        if pri:
            p.pri = pri
        if name:
            p.id_name = name
        else:
            p.id_name = character
        p.nametag = nametag
        if "fade" in args: 
            self._fade("fade","wait","name="+p.id_name,"speed=5")
            p.extrastr = " fade"
        assets.variables["_speaking_name"] = nametag
    def _emo(self,command,emotion,name=None):
        char = None
        if not name:
            char = assets.variables.get("_speaking", None)
        if name:
            for c in self.obs:
                if isinstance(c,portrait) and getattr(c,"id_name",None)==name.split("=",1)[1]:
                    char = c
                    break
        if char:
            nametag = char.nametag
            err = None
            try:
                char.set_emotion(emotion)
            except (script_error,art_error),e:
                err = e
            char.nametag = nametag
            assets.variables["_speaking_name"] = nametag
            if err:
                assets.cur_script.obs.append(error_msg(e.value,assets.cur_script.lastline_value,assets.cur_script.si,assets.cur_script))
                import traceback
                traceback.print_exc()
    @category("init")
    def _addev(self,command,ev,page="evidence"):
        evob = evidence(ev,page=page)
        if ev not in [x.id for x in assets.items]: assets.items.append(evob)
    @category("init")
    def _delev(self,command,ev):
        ids = [x.id for x in assets.items]
        if ev in ids: del assets.items[ids.index(ev)]
    @category("list")
    def _list(self,command,tag=None):
        if tag:
            assets.lists[tag] = assets.lists.get(tag,{})
        self.obs.append(listmenu(tag))
    @category("list")
    def _li(self,command,*label):
        if label[-1].startswith("result="):
            result = label[-1][7:]
            label = " ".join(label[:-1])
        else:
            label=result=" ".join(label)
        for o in self.obs:
            if isinstance(o,listmenu):
                o.options.append([label,result])
    @category("list")
    def _showlist(self,command):
        for o in self.obs:
            if isinstance(o,listmenu):
                o.hidden = False
        self.buildmode = False
    @category("list")
    def _forgetlist(self,command,tag):
        if tag in assets.lists:
            del assets.lists[tag]
    @category("list")
    def _forgetlistitem(self,command,tag,item):
        if tag in assets.lists:
            if item in assets.lists[tag]:
                del assets.lists[tag][item]
    @category("event")
    def _clear(self,command):
        for o in self.obs:
            o.kill = 1
        pygame.screen.fill([0,0,0])
    @category("event")
    def _delete(self,command,*args):
        name = None
        for a in args:
            if a.startswith("name="):
                name = a[5:]
        for o in reversed(self.obs):
            if getattr(o,"id_name",None)==name:
                o.kill = 1
                break
    @category("present")
    def _present(self,command):
        self.statement = ""
        self.cross = "proceed"
        addob(evidence_menu(assets.items))
        self.buildmode = False
    @category("examine")
    def _examine(self,command,*args):
        em = examine_menu(hide=("hide" in args))
        self.obs.append(em)
        while self.si<len(self.scriptlines):
            line = self.getline()
            if line is None: return
            if not line.strip(): 
                self.si+=1
                continue
            if not line.startswith("region "):
                self.si+=1
                break
            em.addregion(*line.replace("region ","").strip().split(" "))
            self.si+=1
        self.si-=1
        self.buildmode = False
    @category("cross")
    def _cross(self,command,*args):
        self.statement = ""
        for a in args:
            if a=="start":
                self.cross = "proceed"
        if self.cross is None:
            self.cross = self.si
        else:
            if self.cross != "proceed":
                self.cross = "proceed"
        assets.variables["currentcross"] = self.si
        assets.variables["_statements"] = []
        for ni,line in enumerate(self.scriptlines[self.si:]):
            if line.startswith("statement "):
                statement,test = self.parse_statement(line.split(" ")[1:])
                assets.variables["_statements"].append({"words":statement,"test":test,"index":self.si+ni})
            if line.startswith("endcross"):
                #Add a dummy last statement so that next_statement can exit the cross/endcross section
                assets.variables["_statements"].append({"words":"$$$","test":None,"index":self.si+ni})
                break
    def _cross_restart(self,command,*args):
        if assets.variables.get("currentcross",None) is not None:
            self.si = assets.variables.get("currentcross",None)
    def _next_statement(self,command,*args):
        self.next_statement()
    def _prev_statement(self,command,*args):
        self.prev_statement()
    @category("cross")
    def _endcross(self,command):
        self.statement = ""
        if self.cross!="proceed" and self.cross is not None:
            self.goto_result("First")
        else:
            self.cross = None
    def parse_statement(self,statement):
        test = None
        statement = list(statement)
        if statement[-1].startswith("test="):
            test = statement.pop(-1)[5:]
        statement = " ".join(statement)
        return statement,test
    def _statement(self,command,*statement):
        statement,test = self.parse_statement(statement)
        if not self.state_test_true(test):
            self.next_statement()
            return
        self.instatement = True
        self.statement = statement
        self.cross = "proceed"
    @category("cross")
    def _resume(self,command):
        if self.statement:
            for x in assets.variables["_statements"]:
                if x["words"]==self.statement:
                    self.si = x["index"]
                    self.next_statement()
            return
        self.si = self.lastline
    @category("cross")
    def _clearcross(self,command):
        self.cross = None
        self.lastline = 0
        self.statement = ""
        self.instatement = False
assets.Script = Script

def wini():
    f = open("display.ini","w")
    f.write(""";standard width is 256
;standard height is 192
width=%s
height=%s
scale2x=%s
fullscreen=%s
gbamode=%s
opengl=%s
displaylists=%s
screens=%s
sound_format=%s
sound_bits=%s
sound_buffer=%s
sound_volume=%s
music_volume=%s"""%(assets.swidth,assets.sheight,assets.filter,assets.fullscreen,
assets.gbamode,int(pygame.USE_GL),pygame.DISPLAY_LIST,assets.num_screens,
assets.sound_format,assets.sound_bits,assets.sound_buffer,int(assets.sound_volume),int(assets.music_volume)))
    f.close()

class screen_settings(gui.pane):
    firstpane = "resolution"
    def __init__(self,*args,**kwargs):
        gui.widget.__init__(self,*args,**kwargs)
        self.width = 1000
        self.height = 1000
        self.pri = -1001
        self.z = 1001
        self.align = False
        getattr(self,self.firstpane)()
    def base(self):
        self.children = []
        self.children.append(gui.button(self,"close",[0,sh-17]))
        self.children.append(gui.button(self,"quit game",[100,sh-17]))
        self.children.append(gui.button(self,"quit pywright",[sw-74,sh-17]))
        self.children.append(gui.button(self,"view",[0,0]))
        if pygame.USE_GL:
            self.children.append(gui.button(self,"opengl",[40,0]))
        else:
            self.children.append(gui.label("no opengl",[30,0]))
        self.children.append(gui.button(self,"resolution",[100,0]))
        self.children.append(gui.button(self,"sound",[170,0]))
    def sound(self):
        self.base()
        screen_settings.firstpane = "sound"
        ermsg = gui.label("")
        ermsg.rpos = [0,140]
        ermsg.textcol = [255,0,0]
        
        line = gui.pane([0,30],[sw,20])
        line.align = "horiz"
        self.children.append(line)
        class newr(gui.radiobutton):
            def click_down_over(s,*args):
                ermsg.text = ""
                gui.radiobutton.click_down_over(s,*args)
                assets.sound_format = int(s.text)
                if not assets.init_sound(True): 
                    ermsg.text = "Sound not initialized"
                else:
                    assets.play_sound("phoenix/objection.ogg")
                    wini()
        line.children.append(gui.label("Format:"))
        line.children.append(newr("11025","formchoice"))
        line.children.append(newr("22050","formchoice"))
        line.children.append(newr("44100","formchoice"))
        for t in line.children:
            if t.text==str(assets.sound_format):
                t.checked = True
                
        line = gui.pane([0,50],[sw,20])
        line.align = "horiz"
        self.children.append(line)
        class newr(gui.radiobutton):
            def click_down_over(s,*args):
                ermsg.text = ""
                gui.radiobutton.click_down_over(s,*args)
                assets.sound_bits = int(s.text)
                if not assets.init_sound(True): 
                    ermsg.text = "Sound not initialized"
                else:
                    assets.play_sound("phoenix/objection.ogg")
                    wini()
        line.children.append(gui.label("Bits:"))
        line.children.append(newr("8","bitschoice"))
        line.children.append(newr("16","bitschoice"))
        for t in line.children:
            if t.text==str(assets.sound_bits):
                t.checked = True
                
        line = gui.pane([0,70],[sw,20])
        line.align = "horiz"
        self.children.append(line)
        class newr(gui.radiobutton):
            def click_down_over(s,*args):
                ermsg.text = ""
                gui.radiobutton.click_down_over(s,*args)
                assets.sound_buffer = int(s.text)
                if not assets.init_sound(True): 
                    ermsg.text = "Sound not initialized"
                else:
                    assets.play_sound("phoenix/objection.ogg")
                    wini()
        line.children.append(gui.label("Buffer:"))
        line.children.append(newr("512","bufchoice"))
        line.children.append(newr("1024","bufchoice"))
        line.children.append(newr("2048","bufchoice"))
        line.children.append(newr("4096","bufchoice"))
        for t in line.children:
            if t.text==str(assets.sound_buffer):
                t.checked = True
                
        line = gui.pane([0,90],[sw,20])
        line.align = "horiz"
        self.children.append(line)
        class newr(gui.radiobutton):
            def click_down_over(s,*args):
                ermsg.text = ""
                gui.radiobutton.click_down_over(s,*args)
                if not assets.init_sound(): 
                    ermsg.text = "Sound not initialized"
                else:
                    assets.sound_volume = int(s.text)
                    assets.play_sound("phoenix/objection.ogg")
                    wini()
        line.children.append(gui.label("SoundVolume:"))
        line.children.append(newr("0","sndvol"))
        line.children.append(newr("25","sndvol"))
        line.children.append(newr("50","sndvol"))
        line.children.append(newr("100","sndvol"))
        for t in line.children:
            if t.text==str(int(assets.sound_volume)):
                t.checked = True
                
        line = gui.pane([0,110],[sw,20])
        line.align = "horiz"
        self.children.append(line)
        class newr(gui.radiobutton):
            def click_down_over(s,*args):
                ermsg.text = ""
                gui.radiobutton.click_down_over(s,*args)
                if not assets.init_sound(): 
                    ermsg.text = "Sound not initialized"
                else:
                    assets.music_volume = int(s.text)
                    assets.play_music("Ding.ogg",loop=0,pre="sfx/")
                    wini()
        line.children.append(gui.label("MusicVolume:"))
        line.children.append(newr("0","musvol"))
        line.children.append(newr("25","musvol"))
        line.children.append(newr("50","musvol"))
        line.children.append(newr("100","musvol"))
        for t in line.children:
            if t.text==str(int(assets.music_volume)):
                t.checked = True
                
        self.children.append(ermsg)
    def view(self):
        self.base()
        screen_settings.firstpane = "view"
        guiline = gui.pane([0,30],[sw,20])
        guiline.align = "horiz"
        self.children.append(guiline)
        guiline.children.append(gui.label("GUI:"))
        class newr(gui.radiobutton):
            def click_down_over(s,*args):
                gui.radiobutton.click_down_over(s,*args)
                self.setgui(s.text)
        guiline.children.append(newr("DS","guichoice"))
        guiline.children.append(newr("GBA","guichoice"))
        if assets.gbamode==0:
            guiline.children[-2].checked = True
        elif assets.gbamode==1:
            guiline.children[-1].checked = True
    def opengl(self):
        self.base()
        screen_settings.firstpane = "opengl"
        glLine = gui.pane([0,30],[sw,20])
        glLine.align = "horiz"
        self.children.append(glLine)
        glLine.children.append(gui.label("Might affect fps"))
        glLine.children.append(gui.checkbox("displaylists"))
        glLine.children[-1].click_down_over = self.setdl
        self.dislis = glLine.children[-1]
        if pygame.DISPLAY_LIST:
            self.dislis.checked = True
    def resolution(self):
        self.base()
        screen_settings.firstpane = "resolution"
        res_box = gui.scrollpane([10,20])
        res_box.width = 200
        res_box.height = 120
        self.children.append(res_box)
        
        res_box.children.append(gui.radiobutton("DS Res (256x192)","resopt"))
        res_box.children.append(gui.radiobutton("Double scale (512x384)","resopt"))
        res_box.children.append(gui.radiobutton("(320x240)","resopt"))
        res_box.children.append(gui.radiobutton("(640x480)","resopt"))
        res_box.children.append(gui.checkbox("fullscreen"))
        self.fs = res_box.children[-1]
        res_box.children.append(gui.checkbox("dualscreen"))
        self.ds = res_box.children[-1]
        self.reses = gui.radiobutton.groups["resopt"]
        for r in self.reses:
            if str(assets.swidth) in r.text:
                r.checked = True
        if assets.fullscreen:
            self.fs.checked = True
        if assets.num_screens==2:
            self.ds.checked = True
                
        self.children.append(gui.button(self,"apply",[10,140]))
    def setgui(self,v):
        v = {"DS":0,"GBA":1}[v]
        assets.gbamode = v
        wini()
    def setdl(self,v):
        self.dislis.checked = 1-self.dislis.checked
        pygame.DISPLAY_LIST = self.dislis.checked
        wini()
    def apply(self):
        for r in self.reses: 
            if r.checked:
                self.oldwidth,self.oldheight = assets.swidth,assets.sheight
                self.timer = 2.0
                self.really_applyb = gui.pane()
                self.really_applyb.width = 1000
                self.really_applyb.height = 1000
                self.really_applyb.pri = -1002
                self.really_applyb.z = 1002
                #self.really_applyb.align = False
                e = gui.editbox(None,"")
                e.draw_back = False
                self.really_applyb.children.append(e)
                self.really_applyb.timer = e
                b = gui.button(self,"save_resolution",[0,0])
                self.really_applyb.children.append(b)
                assets.cur_script.obs.append(self.really_applyb)
                assets.swidth,assets.sheight = [int(x) for x in (r.text[r.text.find("(")+1:r.text.find(")")]).split("x")]
        self.old_fullscreen = assets.fullscreen
        assets.fullscreen = 0
        if self.fs.checked:
            assets.fullscreen = 1
        self.old_num_screens = assets.num_screens
        assets.num_screens = 1
        if self.ds.checked:
            assets.num_screens = 2
        make_screen()
    def save_resolution(self):
        assets.cur_script.world.remove(self.really_applyb)
        self.really_applyb = None
        self.timer = 0
        wini()
    def reset_res(self):
        assets.swidth,assets.sheight = self.oldwidth,self.oldheight
        assets.fullscreen = self.old_fullscreen
        assets.num_screens = self.old_num_screens
        make_screen()
    def update(self,*args):
        self.rpos = [0,other_screen(0)]
        self.pos = self.rpos
        if getattr(self,"timer",0)>0:
            self.timer -= .02
            self.really_applyb.timer.text = "Resetting view in:" + str(self.timer)
        else:
            if getattr(self,"really_applyb",None):
                assets.cur_script.world.remove(self.really_applyb)
                self.really_applyb = None
                self.reset_res()
        return True
    def quit_game(self):
        assets.variables.clear()
        assets.stop_music()
        assets.stack[:] = []
        make_start_script(False)
    def quit_pywright(self):
        sys.exit()
    def close(self):
        self.kill = 1
        
class choose_game(gui.widget):
    def update(self,*args):
        if not hasattr(self,"d"):
            self.d = [1,1,1]
        self.children[1].pos[0]+=self.d[0]*0.5
        self.children[1].pos[1]+=self.d[1]*0.5
        #self.children[1].setfade(self.children[1].fade+self.d[2]*5)
        if self.children[1].fade>=500:
            self.d[2] = -1
        if self.children[1].fade<=0:
            self.d[2] = 1
        if self.children[1].pos[1]<0:
            self.d[1] = 1
        if self.children[1].pos[1]>50:
            self.d[1] = -1
        if self.children[1].pos[0]<0:
            self.d[0] = 1
        if self.children[1].pos[0]>80:
            self.d[0] = -1
        return True
        
def make_start_script(logo=True):
    root = choose_game()
    root.pri = -1000
    root.z = 0
    bottomscript = Script()
    bottomscript.init()
    assets.stack = [bottomscript]  #So that the root object gets tagged as in bottomscript
    bottomscript.obs = [root]
    root.width,root.height = [1000,1000]
    
    root.add_child(sprite(0,0).load("bg/black.png"))
    s = fadesprite(0,0).load("general/logo.png")
    s.img = s.base[0] = pygame.transform.rotozoom(s.base[0],0,0.5)
    s.setfade(0)
    root.add_child(s)
    root.children[-1].width = 0
    root.children[-2].width = 0
    
    list = gui.scrollpane([0,other_screen(0)])
    list.width,list.height = [sw,sh]
    root.add_child(list)
    
    title = gui.editbox(None,"Choose a game to run:")
    title.draw_back = False
    list.add_child(title)

    def run_updater(*args):
        import libupdate
        libupdate.run()
        make_screen()
        make_start_script()
    setattr(make_start_script,"DOWNLOAD_GAMES_AND_CONTENT",run_updater)
    item = gui.button(make_start_script,"DOWNLOAD GAMES AND CONTENT")
    item.bgcolor = [0, 0, 0]
    item.textcolor = [255,255,255]
    item.highlightcolor = [50,75,50]
    list.add_child(item)
    
    for f in os.listdir("games"):
        if f in [".svn"]: continue
        item = gui.button(make_start_script,f)
        list.add_child(item)
        def _play_game(func=f):
            #~ item.rpos = [0,other_screen(0)]
            #~ item.text = "LOADING..."
            #~ item.draw(pygame.screen)
            #~ draw_screen()
            gamedir = os.path.join("games",func)
            #~ chars = assets.get_char_list(gamedir)
            #~ def dchar():
                #~ return None
                #~ import libupdate
                #~ e = libupdate.Engine()
                #~ e.Download_Characters()
                #~ while 1:
                    #~ if libupdate.list.status_box.text.startswith("No new"): return
                    #~ if libupdate.list.status_box.text.startswith("Download"): break
                    #~ pygame.display.flip()
                #~ for child in libupdate.list.children[2:]:
                    #~ if child.text in chars:
                        #~ child.checked = 1
                #~ def draw():
                    #~ if len(libupdate.list.children)>2:
                        #~ pygame.screen.blit(arial10.render("Downloading "+libupdate.list.children[2].text,1,[255,255,255]),[0,16])
                    #~ draw_screen()
                #~ e.do_downloads(output=(pygame.screen,draw))
            #~ dchar()
            scr = Script()
            scr.init()
            scr.obs = []
            assets.stack = [scr]
            scr.obs.append(bg("main"))
            scr.obs.append(bg("main",screen=2))
            case_select = case_menu(gamedir)
            case_select.reload = True
            scr.obs.append(case_select)
        setattr(make_start_script,f.replace(" ","_"),_play_game)

def make_screen():
    if pygame.USE_GL:
        try:
            import gl
            gl.init([assets.swidth,assets.sheight*assets.num_screens],assets.fullscreen)
            SCREEN= pygame.real_screen = pygame.display.get_surface()
            pygame.screen = gl.surface([assets.swidth,assets.sheight*assets.num_screens],[sw,sh*assets.num_screens])
        except:
            import traceback
            traceback.print_exc()
            print "NO OPENGL!  Switching to software rendering."
            pygame.USE_GL = False
    if not pygame.USE_GL:
        try:
            SCREEN=pygame.real_screen = pygame.display.set_mode([assets.swidth,assets.sheight*assets.num_screens],pygame.HWSURFACE|pygame.DOUBLEBUF|pygame.FULLSCREEN*assets.fullscreen)
        except:
            SCREEN=pygame.real_screen = pygame.display.set_mode([assets.swidth,assets.sheight*assets.num_screens],pygame.FULLSCREEN*assets.fullscreen|pygame.DOUBLEBUF)
        pygame.screen = pygame.Surface([sw,sh*assets.num_screens]).convert()
        pygame.blank = pygame.screen.convert()
    pygame.display.set_caption("PyWright "+VERSION)
    pygame.display.set_icon(pygame.image.load("art/general/bb.png"))

    
def draw_screen():
    scale = 0
    if assets.sheight!=sh or assets.swidth!=sw: scale = 1
    if pygame.USE_GL:
        import gl
        gl.draw([pygame.screen])
    else:
        sc = float(assets.sheight)/sh
        sc = float(assets.sheight)/sh
        scaled = pygame.screen
        if scale:
            scaled = pygame.transform.rotozoom(pygame.screen,0,sc)
        #scaled = pygame.transform.scale(scaled,[assets.swidth,assets.sheight])
        pygame.real_screen.blit(scaled,[0,0])
        pygame.display.flip()
        scaled.blit(pygame.blank,[0,0])
    if assets.num_screens==2:
        if not hasattr(assets,"grey_bottom"):
            assets.grey_bottom = assets.Surface([256,192])
            assets.grey_bottom.fill([0,0,0])
        pygame.screen.blit(assets.grey_bottom,[0,192])
assets.make_screen = make_screen
assets.draw_screen = draw_screen

def run(checkupdate=True):
    import sys,os
    

    #Check for updates!
    newengine = None
    if checkupdate:
        import libupdate
        e = libupdate.Engine()
        libupdate.screen.blit(arial14.render("Checking for Updates...",1,[255,255,255]),[0,0])
        pygame.display.flip()
        libupdate.root.start_index = 0
        try:
            assets.threads = [e.Update_PyWright(thread=True)]
            pygame.event.clear()
            pygame.event.pump()
            while libupdate.list.status_box.text=="Fetching data from server...":
                libupdate.screen.fill([0,0,0])
                libupdate.screen.blit(arial14.render("Checking for Updates... (Click to cancel)",1,[255,255,255]),[0,0])
                pygame.display.flip()
                for e in pygame.event.get():
                    if e.type == pygame.MOUSEBUTTONDOWN:
                        libupdate.list.status_box.text = "cancelled"
            libupdate.screen.fill([0,0,0])
            if libupdate.list.status_box.text == "cancelled":
                libupdate.screen.blit(arial14.render("Cancelled checking for updates",1,[255,255,255]),[0,0])
            else:
                libupdate.screen.blit(arial14.render("Finished checking for updates",1,[255,255,255]),[0,0])
            pygame.display.flip()
            for c in libupdate.list.children:
                if isinstance(c,gui.checkbox):
                    c.checked = True
                    libupdate.Engine.quit_threads = 0
                    libupdate.screen.blit(arial14.render("Doing update to "+c.text,1,[255,255,255]),[0,20])
                    pygame.display.flip()
                    e.do_update(output=True)
                    goodkeys = "copy_reg,sre_compile,locale,_sre,__main__,site,__builtin__,\
operator,encodings,os.path,encodings.encodings,encodings.cp437,errno,\
encodings.codecs,sre_constants,re,ntpath,UserDict,nt,stat,zipimport,warnings,\
encodings.types,_codecs,encodings.cp1252,sys,codecs,types,_types,_locale,signal,\
linecache,encodings.aliases,exceptions,sre_parse,os,goodkeys,k,core,libengine".split(",")
                    for k in sys.modules.keys():
                        if k not in goodkeys:
                            del sys.modules[k]
                    import core as core2
                    reload(core2)
                    import libengine as le2
                    reload(le2)
                    newengine = le2.run
                    break
        except SystemExit:
            sys.exit()
        #~ except:
            #~ pass
    if newengine:
        newengine()
        sys.exit()
    
    assets.init_sound()
    assets.fullscreen = 0
    assets.swidth = 256
    assets.sheight = 192
    assets.filter = 0
    assets.gbamode = 0
    assets.num_screens = 2
    pygame.USE_GL=1
    pygame.DISPLAY_LIST=1
    pygame.TEXTURE_CACHE=0
    if os.path.exists("display.ini"):
        f = open("display.ini","r")
        for line in f.readlines():
            spl = line.split("=")
            if len(spl)!=2: continue
            if spl[0]=='width': assets.swidth = int(spl[1])
            if spl[0]=='height': assets.sheight = int(spl[1])
            if spl[0]=='scale2x': assets.filter = int(spl[1])
            if spl[0]=='fullscreen': assets.fullscreen = int(spl[1])
            if spl[0]=="gbamode": assets.gbamode = int(spl[1])
            if spl[0]=="opengl": pygame.USE_GL = int(spl[1])
            if spl[0]=="screens": assets.num_screens = int(spl[1])
            if spl[0]=="displaylists": pygame.DISPLAY_LIST = int(spl[1])
            if spl[0]=="sound_format": assets.sound_format = int(spl[1])
            if spl[0]=="sound_bits": assets.sound_bits = int(spl[1])
            if spl[0]=="sound_buffer": assets.sound_buffer = int(spl[1])
            if spl[0]=="sound_volume": assets.sound_volume = float(spl[1])
            if spl[0]=="music_volume": assets.music_volume = float(spl[1])
    wini()
    
    pygame.USE_GL=0
    make_screen()

    #assets.master_volume = 0.0
        

    game = "menu"
    scene = "intro"
    if sys.argv[1:] and sys.argv[2:]:
        game = sys.argv[1]
        scene = sys.argv[2]
    assets.game = game
    assets.items = []

    running = True

    showfps = False
    clock = pygame.time.Clock()

    make_start_script()
    import time
    lt = time.time()
    ticks = 0
    fr = 0
    #~ import time
    #~ end = time.time()+5
    #~ while time.time()<end:
        #~ pass
    #~ sys.exit()

    while running:
        #~ ticks = time.time()-lt
        #~ lt = time.time()
        #~ while ticks<(1/(float(assets.variables.get("_framerate",60))+20.0)):
            #~ if ticks: time.sleep(0.02)
            #~ ticks += time.time()-lt
            #~ lt = time.time()
        #~ dt = ticks*1000.0
        dt = clock.tick(60)
        assets.cur_script.update()
        if not assets.cur_script: break
        [o.unadd() for o in assets.cur_script.obs if getattr(o,"kill",0) and hasattr(o,"unadd")]
        deleted = 0
        for o in assets.cur_script.obs[:]:
            if getattr(o,"kill",0): assets.cur_script.world.all.remove(o)
        assets.cur_script.draw(pygame.screen)
        if assets.flash:
            fl = flash()
            assets.cur_script.obs.append(fl)
            fl.ttl = assets.flash
            if hasattr(assets,"flashcolor"):
                fl.color = assets.flashcolor
                assets.flashcolor = [255,255,255]
            assets.flash = 0
        if assets.shake:
            fl = shake()
            assets.cur_script.obs.append(fl)
            fl.ttl = assets.shake
            fl.offset = assets.shakeoffset
            assets.shake = 0
        if showfps:
            pygame.screen.blit(font.render(str(1/(dt/1000.0)),[100,180,200]),[0,0])
            #~ y = 12
            #~ for s in assets.stack:
                #~ for i in range(len(s.obs)):
                    #~ pygame.screen.blit(arial10.render(str(s.obs[i]),1,[100,180,200]),[0,y])
                    #~ y+=10
                #~ y+=2
        if assets.variables.get("render",1):
            draw_screen()
        #pygame.image.save(pygame.real_screen,"capture/img%.04d.jpg"%fr)
        #fr+=1
        pygame.event.pump()
        try:
            assets.cur_script.handle_events(pygame.event.get([pygame.MOUSEMOTION,pygame.MOUSEBUTTONUP,pygame.MOUSEBUTTONDOWN]))
            if "enter" in assets.cur_script.held:
                for o in assets.cur_script.upobs:
                    if hasattr(o,"enter_hold"):
                        o.enter_hold()
            for e in pygame.event.get():
                if e.type==150:
                    if assets.variables["_music_loop"]:
                        assets.play_music(assets.variables["_music_loop"])
                if e.type==pygame.KEYDOWN and \
                e.key==pygame.K_ESCAPE:
                    ss = [x for x in assets.cur_script.obs if isinstance(x,screen_settings)]
                    if ss:
                        ss[0].kill = 1
                    else:
                        assets.cur_script.obs.append(screen_settings())
                        #print [o.z for o in assets.cur_script.obs]
                if e.type == pygame.QUIT:
                    running = False
                if e.type==pygame.KEYDOWN and\
                e.key==pygame.K_d:
                    showfps = not showfps
                    if showfps:
                        clses = {}
                        ol = get_all_objects()
                        for o in ol:
                            if not hasattr(o,"__class__"): continue
                            n = clses.get(o.__class__.__name__,0)+1
                            clses[o.__class__.__name__]=n
                        del clses
                        del ol
                if e.type==pygame.KEYUP and\
                e.key==pygame.K_RETURN:
                    if "enter" in assets.cur_script.held: assets.cur_script.held.remove("enter")
                    for o in assets.cur_script.upobs:
                        if hasattr(o,"enter_up"):
                            o.enter_up()
                            break
                if e.type==pygame.KEYDOWN and\
                e.key==pygame.K_RETURN and pygame.key.get_mods() & pygame.KMOD_ALT:
                    assets.fullscreen = 1-assets.fullscreen
                    make_screen()
                    wini()
                elif e.type==pygame.KEYDOWN and\
                e.key==pygame.K_RETURN:
                    if "enter" not in assets.cur_script.held: assets.cur_script.held.append("enter")
                    for o in assets.cur_script.upobs:
                        if hasattr(o,"enter_down") and not getattr(o,"kill",0) and not getattr(o,"hidden",0):
                            o.enter_down()
                            if isinstance(o,evidence_menu):
                                if "enter" in assets.cur_script.held:
                                    assets.cur_script.held.remove("enter")
                            if isinstance(o,examine_menu):
                                if "enter" in assets.cur_script.held:
                                    assets.cur_script.held.remove("enter")
                            break
                if e.type==pygame.KEYDOWN and\
                e.key==pygame.K_RIGHT:
                    for o in assets.cur_script.upobs:
                        if hasattr(o,"statement") and not o.statement:
                            continue
                        if hasattr(o,"k_right") and not getattr(o,"kill",0) and not getattr(o,"hidden",0):
                            o.k_right()
                            break
                if e.type==pygame.KEYDOWN and\
                e.key==pygame.K_LEFT:
                    for o in assets.cur_script.upobs:
                        if hasattr(o,"statement") and not o.statement:
                            continue
                        if hasattr(o,"k_left") and not getattr(o,"kill",0) and not getattr(o,"hidden",0):
                            o.k_left()
                            break
                if e.type==pygame.KEYDOWN and\
                e.key==pygame.K_UP:
                    for o in assets.cur_script.upobs:
                        if hasattr(o,"k_up") and not getattr(o,"kill",0) and not getattr(o,"hidden",0):
                            o.k_up()
                            break
                if e.type==pygame.KEYDOWN and\
                e.key==pygame.K_DOWN:
                    for o in assets.cur_script.upobs:
                        if hasattr(o,"k_down") and not getattr(o,"kill",0) and not getattr(o,"hidden",0):
                            o.k_down()
                            break
                if e.type==pygame.KEYDOWN and\
                e.key==pygame.K_SPACE:
                    for o in assets.cur_script.upobs:
                        if hasattr(o,"k_space") and not getattr(o,"kill",0) and not getattr(o,"hidden",0):
                            o.k_space()
                            break
                if e.type==pygame.KEYDOWN and \
                    e.key == pygame.K_TAB:
                    for o in assets.cur_script.upobs:
                        if hasattr(o,"k_tab") and not getattr(o,"kill",0) and not getattr(o,"hidden",0):
                            o.k_tab()
                            break
                if e.type==pygame.KEYDOWN and\
                e.key==pygame.K_z:
                    for o in assets.cur_script.upobs:
                        if hasattr(o,"k_z") and not getattr(o,"kill",0) and not getattr(o,"hidden",0):
                            o.k_z()
                            break
                if e.type==pygame.KEYDOWN and\
                e.key==pygame.K_x:
                    for o in assets.cur_script.upobs:
                        if hasattr(o,"k_x") and not getattr(o,"kill",0) and not getattr(o,"hidden",0):
                            o.k_x()
                            break
                #~ if e.type==pygame.KEYDOWN and\
                #~ e.key==pygame.K_BACKSPACE:
                    #~ ex = [x.split("_") for x in sorted(os.listdir("")) if x.startswith("screen_")]
                    #~ if not ex: name = "screen_001_.png"
                    #~ else: name = "screen_"+("00"+str(int(ex[-1][1])+1))[-3:]+"_.png"
                    #~ pygame.image.save(pygame.screen,name)
                if e.type==pygame.KEYDOWN and\
                e.key==pygame.K_F5 and assets.game!="menu":
                    assets.save_game()
                if e.type==pygame.KEYDOWN and\
                e.key == pygame.K_F7 and assets.game!="menu":
                    assets.load_game()
        except script_error, e:
            assets.cur_script.obs.append(error_msg(e.value,assets.cur_script.lastline_value,assets.cur_script.si,assets.cur_script))
            import traceback
            traceback.print_exc()
    if hasattr(assets, "threads"):
        while [1 for thread in assets.threads if thread.isAlive()]:
            print "waiting"
            pass
if __name__=="__main__":
    run()
