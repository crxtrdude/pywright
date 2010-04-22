
from errors import script_error



import pickle
import zlib
import os,sys
if sys.platform=="win32":
    os.environ['SDL_VIDEODRIVER']='windib'
import random
from core import *
import gui
import save
import load
from pwvlib import *

d = get_data_from_folder(".")
__version__ = cver_s(d["version"])
VERSION = "Version "+cver_s(d["version"])

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
class DOCTYPE():
    def __init__(self,name,description="",default=None):
        self.name = name
        self.description = description
        self.default = default
    def __repr__(self):
        s = self.__class__.__name__+" ( "+self.name+":"+self.description+" ) "
        if self.default is not None:
            s+="default:"+repr(self.default)
        return s
class COMBINED(DOCTYPE):
    """Set of arguments joined as text"""
class KEYWORD(DOCTYPE):
    """A value assigned by name"""
class TOKEN(DOCTYPE):
    """This exact token string may be present"""
class VALUE(DOCTYPE):
    """A named value, assigned by position"""
class CHOICE():
    """One of these options should be present here"""
    def __init__(self,options):
        self.options = options
    def __repr__(self):
        return self.__class__.__name__+" ["+" ".join(repr(o) for o in self.options)+"]"

    
delete_on_menu = [evidence,portrait,fg]
only_one = [textbox,testimony_blink,evidence_menu]
def addob(ob):
    if [1 for x in only_one if isinstance(ob,x)]:
        for o2 in assets.cur_script.obs[:]:
            if isinstance(o2,ob.__class__):
                o2.kill = 1
    assets.cur_script.obs.append(ob)
def addevmenu():
    em = evidence_menu(assets.items)
    addob(em)
    return em
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
        if assets.variables.get("_layering_method","zorder") == "zorder":
            argsort(n,"z")
        else:
            pass
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
assets.World = World


def EVAL(stuff):
    stuff = stuff.split(" ",2)
    if len(stuff)==1:
        return vtrue(assets.variables.get(stuff[0],""))
    if len(stuff)==2:
        stuff = stuff[0],"=",stuff[1]
    current,op,check = stuff
    if op not in ["<",">","=","<=",">="]:
        check = op+" "+check
        op = "="
    current = assets.variables.get(current)
    if op=="=":op="=="
    if op!="==":
        current = int(current)
        check = int(check)
    if op == ">":
        return current > check
    elif op == "<":
        return current < check
    elif op == "==":
        return current == check
    elif op == "<=":
        return current <= check
    elif op == ">=":
        return current >= check
def OR(stuff):
    for line in stuff:
        if EVAL(line):
            return True
    return False

class Script(gui.widget):
    save_me = True
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
        props = {}
        save.cp(["scene","si","cross","statement","instatement","lastline","pri","viewed"],self,props)
        if self.parent:
            props["_parent_index"] = assets.stack.index(self.parent)
        obs = []
        for ob in self.world.all:
            save_state = save.save(ob)
            if save_state:
                obs.append(save_state)
        props["_objects"] = obs
        props["_world_id"] = id(self.world)
        return ["assets.Script",[],props,["stack",assets.stack.index(self)]]
    def after_load(self):
        p = {}
        for k in ["si","cross","statement","instatement","lastline","pri","viewed"]:
            p[k] = getattr(self,k,"")
        self.init(self.scene)
        for k in p:
            setattr(self,k,p[k])
        if hasattr(self,"_parent_index"):
            try:
                self.parent = assets.stack[self._parent_index]
            except IndexError:
                pass
        obs = []
        after_after = []
        if not hasattr(self,"_world_id"):
            self._world_id = id(self)
        if self._world_id in assets.loading_cache:
            self.world = assets.loading_cache[self._world_id]
            return
        assets.loading_cache[self._world_id] = self.world
        for o in getattr(self,"_objects",[]):
            print "try to load",o
            try:
                o,later = load.load(self,o)
            except:
                continue
            if o:
                obs.append(o)
            if later:
                after_after.append(later)
        self.world.all = obs
        for of in after_after:
            of()
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
            try:
                self.scriptlines = assets.open_script(scene,macros,ext)
            except Exception,e:
                self.obs.append(error_msg(e.value,self.lastline_value,self.si,self))
                import traceback
                traceback.print_exc()
                return
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
        return True
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
            if args[0] not in ["bg","char","fg","ev"]: continue
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
                if vtrue(assets.variables.get("_cr_button","true")):
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
    @category([])
    def _draw_on(self,*args):
        """Turns engine drawing on."""
        assets.variables["render"] = 1
    @category([])
    def _draw_off(self,*args):
        """Turns engine drawing off."""
        assets.variables["render"] = 0
    @category([COMBINED("text","Some text to print")])
    def _print(self,*args):
        """Prints some text to the logfile. Only useful for debugging purposes."""
        print " ".join(args[1:])
    @category([])
    def _endscript(self,*args):
        """Ends the currently running script and pops it off the stack. Multiple scripts
        may be running in PyWright, in which case the next script on the stack will
        resume running."""
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
    @category([CHOICE([TOKEN("true","turns on debug mode"),TOKEN("false","turns off debug mode")])])
    def _debug(self,command,value):
        """Used to turn debug mode on or off. Debug mode will print more errors to the screen,
        and allow you to skip through any text."""
        if value.lower() in ["on","1","true"]:
            assets.variables["_debug"] = "on"
        else:
            assets.variables["_debug"] = "off"
    @category([COMBINED("label text","The name of this section of code")])
    def _label(self,command,*name):
        """Used to mark a spot in a wrightscript file. Other code can then refer to this spot,
        specifically for making the code reader "goto" this spot."""
        assets.variables["_lastlabel"] = " ".join(name)
    @category([VALUE("game","Path to game. Should be from the root, i.e. games/mygame or games/mygame/mycase"),
                    VALUE("script","Script to look for in the game folder to run first","intro")])
    def _game(self,command,game,script="intro"):
        """Can be used to start a new game or case."""
        for o in self.obs[:]:
            o.kill = 1
        assets.clear()
        assets.game = game
        self.held = []
        print "load script",script
        scene = script
        #assets.addscene(scene)
        self.init(scene)
    @category([COMBINED("destination","The destination label to move to"),
                    KEYWORD("fail","A label to jump to if the destination can't be found")])
    def _goto(self,command,place,*args):
        """Makes the script go to a different section, based on the label name."""
        fail = None
        for x in args:
            if "=" in x:
                k,v = x.split("=",1)
                if k == "fail":
                    fail = v
        self.goto_result(place,wrap=True,backup=fail)
    @category([COMBINED("flag expression","list of flag names joined with AND or OR"),
                    CHOICE([
                    TOKEN("?"),VALUE("label","label to jump to if the evaluation is true")
                    ]),KEYWORD("fail","label to jump to if evaluation is false","none")])
    def flag_logic(self,value,*args):
        fail=None
        args = list(args)
        label = args.pop(-1)
        if label.startswith("fail="):
            fail=label.split("=",1)[1]
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
        if not eval(sentance)==value: return self.fail(label,fail)
        self.succeed(label)
    @category(flag_logic.cat)
    def _noflag(self,command,*args):
        """Evaluates an expression with flag names. If the expression
        is not true, jumps to the listed label. Otherwise, will
        jump to the fail keyword if that was given. If the line ends
        with a '?', it will execute the next line and the next line only
        when the flag expression is false."""
        self.flag_logic(False,*args)
    @category(flag_logic.cat)
    def _flag(self,command,*args):
        """Evaluates an expression with flag names. If the expression
        is true, jumps to the listed label. Otherwise, will
        jump to the fail keyword if that was given. If the line ends
        with a '?', it will execute the next line and the next line only
        when the flag expression is true."""
        self.flag_logic(True,*args)
    @category([VALUE('flag name','flag to set')])
    def _setflag(self,command,flag):
        """Sets a flag. Shorthand for setting a variable equal to true. Flags
        will remain set for the remainder of the game, and can be used to
        track what a player has done."""
        if flag not in assets.variables: assets.variables[flag]="true"
    @category([VALUE('flag name','flag to unset')])
    def _delflag(self,command,flag):
        """Deletes a flag. Flags will remain set for the remainder of the game, but
        can be forgotten with delflag."""
        if flag in assets.variables: del assets.variables[flag]
    @category([VALUE("variable","variable name to set"),COMBINED("value","Text to assign to the variable. Can include $x to replace words of the text with the value of other variables.")])
    def _set(self,command,variable,*args):
        """Sets a variable to some value."""
        value = " ".join(args)
        assets.variables[variable]=value
    @category([VALUE("destination variable","The variable to save the value into"),COMBINED("source variable","The variable to get the value from. Can use $x to use another variable to point to which variable to copy from, like a signpost.")])
    def _getvar(self,command,variable,*args):
        """Copies the value of one variable into another."""
        value = "".join(args)
        assets.variables[variable]=assets.variables.get(value,"")
    _setvar = _set
    @category([VALUE("variable","variable name to save random value to"),VALUE("start","smallest number to generate"),VALUE("end","largest number to generate")])
    def _random(self,command,variable,start,end):
        """Generates a random integer with a minimum
        value of START, a maximum value of END, and
        stores that value to VARIABLE"""
        random.seed(pygame.time.get_ticks()+random.random())
        value = random.randint(int(start),int(end))
        assets.variables[variable]=str(value)
    @category([VALUE("variable","variable to save value to"),COMBINED("words","words to join together")])
    def _joinvar(self,command,variable,*args):
        """Takes a series of words and joins them together, save the joined
        string to a variable. For instance 
        {{{setvar hour 3
        setvar minut 15
        joinvar time $hour : $minute
        "{$time}"}}}
        will output "3:15"
        """
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
    @category("blah")
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
    @category("blah")
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
    @category("blah")
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
    @category("blah")
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
    @category("blah")
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
    @category([VALUE("path","path, relative to game's directory, to save the screenshot, including file extension (.png or .jpg)"),
                    KEYWORD("width","shrink screenshot to this width"),
                    KEYWORD("height","shrink screenshot to this height"),
                    KEYWORD("x","x-value of region to screenshot"),
                    KEYWORD("y","y-value of region to screenshot"),
                    KEYWORD("rwidth","width of region to screenshot"),
                    KEYWORD("rheight","height of region to screenshot")])
    def _screenshot(self,command,path,*args):
        root = assets.game.replace("\\","/").rsplit("/",1)[0]
        if root == "games" or root == "games":
            root = assets.game
        image = pygame.screen.convert()
        self.draw(image)
        resize = list(image.get_size())
        subrect = image.get_rect()
        for a in args:
            if a.startswith("width="):
                resize[0] = int(a.split("=")[1])
            if a.startswith("height="):
                resize[1] = int(a.split("=")[1])
            if a.startswith("x="):
                subrect.x = int(a.split("=")[1])
            if a.startswith("y="):
                subrect.y = int(a.split("=")[1])
            if a.startswith("rwidth="):
                subrect.width = int(a.split("=")[1])
                print "set width",subrect.width
            if a.startswith("rheight="):
                subrect.height = int(a.split("=")[1])
                print "set height",subrect.height
        print subrect.x,subrect.y,subrect.width,subrect.height
        image = image.subsurface(subrect)
        if resize:
            image = pygame.transform.scale(image,resize)
        pygame.image.save(image,root+"/"+path+".png")
        image = pygame.transform.scale(image,[50,50])
        pygame.real_screen.blit(image,[0,0])
        pygame.display.flip()
    @category("control")
    def _is(self,command,*args):
        fail = None
        args = list(args)
        label = args.pop(-1)
        if label.startswith("fail="):
            fail = label.split("=",1)[1]
            label = args.pop(-1)
        if label.endswith("?"):
            args.append(label[:-1])
            label = "?"
        args = " ".join(args).split(" AND ")
        args = [x.split(" OR ") for x in args]
        args = [OR(x) for x in args]
        if False in args: return self.fail(label,fail)
        self.succeed(label)
    @category([COMBINED('expression'),
                    KEYWORD('fail','label to jump to if expression fails'),
                    CHOICE([VALUE('label'),TOKEN('?')])])
    def _isnot(self,command,*args):
        """If the expression is false, will jump to the success label.
        Otherwise, it will either continue to the next line, or jump to
        the label set by the fail keyword"""
        fail = None
        args = list(args)
        label = args.pop(-1)
        if label.startswith("fail="):
            fail = label.split("=",1)[1]
            label = args.pop(-1)
        if label.endswith("?"):
            args.append(label[:-1])
            label = "?"
        args = " ".join(args).split(" AND ")
        args = [x.split(" OR ") for x in args]
        args = [OR(x) for x in args]
        if False in args: return self.succeed(label)
        self.fail(label,fail)
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
    def succeed(self,label=None,dest=None):
        """What happens when a test succeeds?"""
        if label == "?": label = None
        if label:
            self._goto(None,label)
        else:
            pass
    def fail(self,label=None,dest=None):
        if label == "?": label = None
        if dest:
            return self.goto_result(dest)
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
    def _nopenalty(self,command,*args):
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
    @category("blah")
    def _timer(self,command,ticks,run):
        self.obs.append(timer(int(ticks),run))
    @category("control")
    def _waitenter(self,command):
        self.buildmode = False
        self.obs.append(waitenter())
    @category("control")
    def _exit(self,command):
        del assets.stack[-1]
    @category("control")
    def _menu(self,command,ascene,*args):
        self.buildmode = False
        for o in self.obs:
            if o.__class__ in delete_on_menu:
                o.kill = 1
        m = menu()
        m.scene = ascene
        for scr in assets.list_casedir():
            if scr.startswith(m.scene+".") and scr not in [m.scene+".script.txt"]:
                m.addm(scr[scr.find(".")+1:scr.rfind(".")])
        for a in args:
            if "=" in a:
                arg,val = a.split("=")
                if arg=="fail":
                    m.fail = val
                elif not vtrue(val):
                    m.delm(arg)
        self.scriptlines = []
        self.si = 0
        self.obs.append(m)
    @category("control")
    def _localmenu(self,command,*args):
        self.buildmode = False
        for o in self.obs:
            if o.__class__ in delete_on_menu:
                o.kill = 1
        m = menu()
        for a in args:
            if "=" in a:
                arg,val = a.split("=")
                if arg=="fail":
                    m.fail = val
                elif vtrue(val):
                    m.addm(arg)
        m.open_script = False
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
        label = None
        for a in args:
            if a.startswith("label="):
                label = a.split("=",1)[1]
        if "noclear" not in args:
            for o in self.obs:
                o.kill = 1
        name = scriptname+".script"
        try:
            assets.open_script(name,False,".txt")
        except file_error:
            name = scriptname
        if "stack" in args:
            assets.addscene(name+".script")
        else:
            p = self.parent
            self.init(name)
            self.parent = p
        while assets.cur_script.parent:
            parent = assets.cur_script.parent
            assets.cur_script.parent = parent.parent
            assets.stack.remove(parent)
        if label:
            self.goto_result(label,backup=None)
        self.execute_macro("defaults")
    @category("control")
    def _top(self,command):
        self.si = 0
    @category("blah")
    def _globaldelay(self,command,spd,*args):
        name = None
        for a in args:
            if a.startswith("name="):
                name = a.split("=",1)[1]
        for o in self.world.all:
            if name and getattr(o,"id_name",None)!=name:
                continue
            if isinstance(o,portrait):
                if "b" in args:
                    o = o.blink_sprite
                if "t" in args:
                    o = o.talk_sprite
            if hasattr(o,"spd"):
                o.spd = float(spd)
    @category("blah")
    def _controlanim(self,command,*args):
        start = None
        end = None
        name = None
        loop = None
        jumpto = None
        b = None
        t = None
        for a in args:
            if a.startswith("name="):
                name = a.split("=",1)[1]
            if a == "loop":
                loop = True
            if a == "noloop":
                loop = False
            if a.startswith("start="):
                start = int(a.split("=",1)[1])
            if a.startswith("end="):
                end = int(a.split("=",1)[1])
            if a.startswith("jumpto="):
                jumpto = int(a.split("=",1)[1])
            if a == "b":
                b = True
            elif a == "t":
                t = True
        for o in self.world.all:
            if not name or getattr(o,"id_name",None)==name:
                if isinstance(o,portrait):
                    if b:
                        o = o.blink_sprite
                    elif t:
                        o = o.talk_sprite
                if start is not None:
                    o.start = start
                    if o.x<start:
                        o.x = start
                if end is not None:
                    o.end = end
                if loop is not None:
                    if loop:
                        o.loops = 1
                    else:
                        o.loops = 0
                        o.loopmode = "stop"
                if jumpto is not None:
                    o.x = jumpto
    @category("graphics")
    def _obj(self,command,*args):
        func = {"bg":bg,"fg":fg,"ev":evidence,"obj":graphic}[command]
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
    @category("blah")
    def _movie(self,command,file,sound=None):
        self.buildmode = False
        m = movie(file,sound)
        self.obs.append(m)
    @category("graphics")
    def _bg(self,command,*args):
        self._obj(command,*args)
    @category("graphics")
    def _fg(self,command,*args):
        self._obj(command,*args)
    @category("graphics")
    def _ev(self,command,*args):
        self._obj(command,*args)
    @category("graphics")
    def _gui(self,command,guitype,*args):
        args = list(args)
        x=None
        y=None
        z=None
        width=None
        height=None
        name=""
        if guitype=="Back":
            while args:
                a = args.pop(0)
                if a.startswith("x="): x=int(a[2:])
                elif a.startswith("y="): y=int(a[2:])
                elif a.startswith("z="): z=int(a[2:])
                elif a.startswith("width="): width=int(a[6:])
                elif a.startswith("height="): height=int(a[7:])
                elif a.startswith("name="): name=a[5:]
            print x,y,z
            self.obs.append(guiBack(x=x,y=y,z=z,name=name))
            self.buildmode = False
        if guitype=="Button":
            print "make button",args
            macroname=args[0]; del args[0]
            print macroname
            graphic = None
            width = None
            while args:
                a = args[0]
                print a
                if a.startswith("x="): x=int(a[2:])
                elif a.startswith("y="): y=int(a[2:])
                elif a.startswith("z="): z=int(a[2:])
                elif a.startswith("width="): width=int(a[6:])
                elif a.startswith("height="): height=int(a[7:])
                elif a.startswith("name="): name=a[5:]
                elif a.startswith("graphic="): graphic = a[8:]
                else:
                    break
                del args[0]
            text = ""
            text = " ".join(args)
            btn = gui.button(None,text)
            btn.s_text = text
            if graphic:
                btn.s_graphic = graphic
                graphic = assets.open_art(graphic)[0]
            btn.graphic = graphic
            btn.rpos = [x,y]
            btn.z = int(assets.variables["_layer_gui"])
            if z is not None: btn.z = z
            btn.pri = 0
            btn.s_macroname = macroname
            def func(*args):
                print "go to",macroname
                self.goto_result(macroname)
            setattr(btn,text.replace(" ","_"),func)
            self.obs.append(btn)
            if name: btn.id_name = name
            else: btn.id_name = "$$"+str(id(btn))+"$$"
        if guitype=="Input":
            print "make inputbox",args
            varname=args[0]; del args[0]
            varvalue = assets.variables.get(varname,"")
            assets.variables[varname] = varvalue
            #graphic = None
            type = "normal"
            while args:
                a = args.pop(0)
                if a.startswith("x="): x=int(a[2:])
                elif a.startswith("y="): y=int(a[2:])
                elif a.startswith("z="): z=int(a[2:])
                elif a.startswith("name="): name=a[5:]
                elif a.startswith("width="): width=int(a[6:])
                elif a.startswith("height="): height=int(a[7:])
                #elif a.startswith("graphic="): graphic = args[0][8:]
                elif a == "password":
                    type = "password"
            eb = gui.editbox(assets.variables,varname,is_dict=True)
            #~ if graphic:
                #~ btn.s_graphic = graphic
                #~ graphic = assets.open_art(graphic)[0]
            #~ btn.graphic = graphic
            eb.rpos = [x,y]
            if width:
                eb.force_width = width
            print eb.width
            eb.z = int(assets.variables["_layer_gui"])
            if z is not None: eb.z = z
            eb.pri = 0
            if name: eb.id_name = name
            else: eb.id_name = "$$"+str(id(eb))+"$$"
            self.obs.append(eb)
        if guitype=="Wait":
            run = ""
            if args and args[0].startswith("run="): run = args[0].replace("run=","",1)
            self.obs.append(guiWait(run=run))
            self.buildmode = False
    @category("graphics")
    def _textblock(self,command,x,y,width,height,*text):
        id_name = None
        color = None
        if text and text[0].startswith("color="):
            color = color_str(text[0][6:])
            text = text[1:]
        if text and text[0].startswith("name="): 
            id_name = text[0].replace("name=","",1)
            text = text[1:]
        tb = textblock(" ".join(text),[int(x),int(y)],[int(width),int(height)],surf=pygame.screen)
        self.obs.append(tb)
        if id_name: tb.id_name = id_name
        else: tb.id_name = "$$"+str(id(tb))+"$$"
        if color:
            tb.color = color
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
    def _notguilty(self,command,*args):
        self.obs.append(notguilty())
        self.buildmode = False
    @category("event")
    def _guilty(self,command,*args):
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
    def _shake(self,command,*args):
        args = list(args)
        ttl = 30
        offset = 15
        wait = True
        if "nowait" in args:
            wait = False
            args.remove("nowait")
        if len(args)>0:
            ttl = int(args[0])
        if len(args)>1:
            offset = int(args[1])
        sh = shake()
        sh.ttl = ttl
        sh.offset = offset
        sh.wait = wait
        self.obs.append(sh)
    @category("blah")
    def _zoom(self,command,*args):
        mag = 1
        frames = 1
        wait = 1
        last = 0
        name = None
        filter = "top"
        for a in args:
            if a.startswith("mag="):
                mag=float(a[4:])
            if a.startswith("frames="):
                frames=int(a[7:])
            if a.startswith("last"):
                last = 1
            if a.startswith("nowait"):
                wait = 0
            if a.startswith("name="):
                name = a[5:]
        zzzooom = zoomanim(mag,frames,wait)
        if last:
            zzzooom.control_last()
        if name:
            zzzooom.control(name)
        self.obs.append(zzzooom)
        if wait: self.buildmode = False
    @category("event")
    def _scroll(self,command,*args):
        x=0
        y=0
        speed = 1
        last = 0
        wait = 1
        name = None
        filter = "top"
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
            if a.startswith("filter="):
                filter=a[7:]
        scr = scroll(x,y,speed,wait,filter)
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
        be = ""
        x = 0
        y = 0
        pri = None
        name = None
        nametag = character+"\n"
        for a in args:
            if a.startswith("z="): z = int(a[2:])
            if a.startswith("e="): e = a[2:]+"(blink)"
            if a.startswith("be="): be = a[3:]
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
        if be:
            p.set_blink_emotion(be)
    @category("blah")
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
    @category("blah")
    def _bemo(self,command,emotion,name=None):
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
                char.set_blink_emotion(emotion)
            except (script_error,art_error),e:
                err = e
            char.nametag = nametag
            assets.variables["_speaking_name"] = nametag
            if err:
                assets.cur_script.obs.append(error_msg(e.value,assets.cur_script.lastline_value,assets.cur_script.si,assets.cur_script))
                import traceback
                traceback.print_exc()
    @category("init")
    def _addev(self,command,ev,page=None):
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
    def _showlist(self,command,*args):
        fail = None
        for a in args:
            if "=" in a:
                k,v = a.split("=",1)
                if k == "fail":
                    fail = v
        for o in self.obs:
            if isinstance(o,listmenu):
                o.hidden = False
                if fail:
                    o.fail = fail
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
    def _present(self,command,*args):
        self.statement = ""
        self.cross = "proceed"
        ob = evidence_menu(assets.items)
        for a in args:
            if "=" in a:
                k,v = a.split("=",1)
                if k == "fail":
                    ob.fail = v
        addob(ob)
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
        for a in args:
            if "=" in a:
                k,v = a.split("=",1)
                if k == "fail":
                    em.fail = v
    @category("cross")
    def _cross(self,command,*args):
        assets.variables["_court_fail_label"] = "none"
        self.statement = ""
        for a in args:
            if a=="start":
                self.cross = "proceed"
            if "=" in a:
                k,v = a.split("=",1)
                if k == "fail":
                    assets.variables["_court_fail_label"] = v
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
    @category("blah")
    def _cross_restart(self,command,*args):
        if assets.variables.get("currentcross",None) is not None:
            self.si = assets.variables.get("currentcross",None)
    @category("blah")
    def _next_statement(self,command,*args):
        self.next_statement()
    @category("blah")
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
    @category("blah")
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
            self.cross = "proceed"
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

        self.snd_line = gui.label("SoundVolume: %d"%assets.sound_volume)
        def mod(amt,min,max,var,play):
            def modit():
                ermsg.text = ""
                if not assets.init_sound(): 
                    ermsg.text = "Sound not initialized"
                else:
                    n = getattr(assets,var) + amt
                    if n>max:
                        n = max
                    if n<min:
                        n=min
                    setattr(assets,var,n)
                    self.snd_line.text = "SoundVolume: %d"%assets.sound_volume
                    self.mv_line.text = "MusicVolume: %d"%assets.music_volume
                    play()
                    wini()
            return modit
        line.children.append(self.snd_line)
        line.children.append(gui.button(None,"less"))
        line.children[-1].less = mod(-10,0,100,"sound_volume",lambda:assets.play_sound("phoenix/objection.ogg"))
        line.children.append(gui.button(None,"more"))
        line.children[-1].more = mod(10,0,100,"sound_volume",lambda:assets.play_sound("phoenix/objection.ogg"))
                
        line = gui.pane([0,110],[sw,20])
        line.align = "horiz"
        self.children.append(line)
        
        self.mv_line = gui.label("MusicVolume: %d"%assets.music_volume)
        line.children.append(self.mv_line)
        line.children.append(gui.button(None,"less"))
        line.children[-1].less = mod(-10,0,100,"music_volume",lambda:assets.play_music("Ding.ogg",loop=1,pre="sfx/",reset_track=False))
        line.children.append(gui.button(None,"more"))
        line.children[-1].more = mod(10,0,100,"music_volume",lambda:assets.play_music("Ding.ogg",loop=1,pre="sfx/",reset_track=False))

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
                self.timer = 5.0
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
            self.really_applyb.timer.text = "Resetting view in: %.02f seconds"%self.timer
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
        return True
        
def make_start_script(logo=True):
    root = choose_game()
    root.pri = -1000
    root.z = 0
    bottomscript = Script()
    introlines = []
    try:
        import urllib2
        online_script = urllib2.urlopen("http://pywright.dawnsoft.org/updates3/stream/intro.txt",timeout=2)
        introlines = online_script.read().split("\n")
        online_script.close()
    except:
        pass
    bottomscript.init(scriptlines=["fg ../general/logosmall y=-15 name=logo",
                                            "zoom mag=-0.25 frames=30 nowait"] + introlines + ["add_root","gui Wait"])
    assets.stack = [bottomscript]  #So that the root object gets tagged as in bottomscript
    def add_root(command,*args):
        bottomscript.obs.append(root)
    bottomscript._add_root = add_root
    root.width,root.height = [1000,1000]
    
    list = gui.scrollpane([0,other_screen(0)])
    list.width,list.height = [sw,sh]
    root.add_child(list)
    
    title = gui.editbox(None,"Choose a game to run:")
    title.draw_back = False
    list.add_child(title)

    def run_updater(*args):
        import libupdate
        reload(libupdate)
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
        d = get_data_from_folder("games/"+f)
        if d.get("icon",""):
            graphic = pygame.image.load("games/"+f+"/"+d["icon"])
        else:
            graphic = pygame.Surface([1,1])
        title = d.get("title",f)
        if d.get("author",""):
            title += " by "+d["author"]
        txt = item.font.render(title,1,[0,0,0])
        image = pygame.Surface([max(graphic.get_width(),txt.get_width()),graphic.get_height()+txt.get_height()])
        image.fill([200,200,255])
        image.blit(graphic,[0,0])
        image.blit(txt,[0,graphic.get_height()])
        item.graphic = image
        list.add_child(item)
        def _play_game(func=f):
            gamedir = os.path.join("games",func)
            assets.game = gamedir
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
            SCREEN=pygame.real_screen = pygame.display.set_mode([assets.swidth,assets.sheight*assets.num_screens],pygame.RESIZABLE|pygame.HWSURFACE|pygame.DOUBLEBUF|pygame.FULLSCREEN*assets.fullscreen)
        except:
            SCREEN=pygame.real_screen = pygame.display.set_mode([assets.swidth,assets.sheight*assets.num_screens],pygame.RESIZABLE|pygame.FULLSCREEN*assets.fullscreen|pygame.DOUBLEBUF)
        pygame.screen = pygame.Surface([sw,sh*assets.num_screens]).convert()
        pygame.blank = pygame.screen.convert()
        pygame.blank.fill([0,0,0])
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
        pygame.real_screen.blit(scaled,[0,0])
        pygame.display.flip()
    if assets.num_screens==2:
        if not hasattr(assets,"grey_bottom"):
            assets.grey_bottom = assets.Surface([256,192])
            assets.grey_bottom.fill([0,0,0])
        pygame.screen.blit(assets.grey_bottom,[0,192])
assets.make_screen = make_screen
assets.draw_screen = draw_screen

def run(checkupdate=False):
    import sys,os
    

    #Check for updates!
    newengine = None
    if checkupdate:
        import libupdate
        eng = libupdate.Engine()
        libupdate.screen.blit(arial14.render("Checking for Updates...",1,[255,255,255]),[0,0])
        pygame.display.flip()
        libupdate.root.start_index = 0
        try:
            assets.threads = [eng.Update_PyWright(thread=True)]
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
            for pane in libupdate.list.children[2:]:
                c = pane.children[1].children[0]
                if isinstance(c,gui.checkbox):
                    c.checked = True
                    libupdate.Engine.quit_threads = 0
                    libupdate.screen.blit(arial14.render("Doing update to "+c.text,1,[255,255,255]),[0,20])
                    pygame.display.flip()
                    eng.do_update(output=True)
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
            if spl[0]=='width': assets.swidth = int(float(spl[1]))
            if spl[0]=='height': assets.sheight = int(float(spl[1]))
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
        for o in assets.cur_script.world.all[:]:
            if getattr(o,"kill",0):
                assets.cur_script.world.all.remove(o)
        pygame.screen.blit(pygame.blank,[0,0])
        assets.cur_script.draw(pygame.screen)
        if assets.flash:
            fl = flash()
            assets.cur_script.obs.append(fl)
            fl.ttl = assets.flash
            if hasattr(assets,"flashcolor"):
                fl.color = assets.flashcolor
                assets.flashcolor = [255,255,255]
            assets.flash = 0
        if assets.shakeargs:
            assets.cur_script._shake(*assets.shakeargs)
            assets.shakeargs = 0
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
                    if assets.variables.get("_music_loop",None):
                        assets.play_music(assets.variables["_music_loop"])
                if e.type==pygame.VIDEORESIZE:
                    w,h = e.w,e.h
                    if assets.num_screens == 2:
                        h = h//2
                    w = (256/192.0)*h
                    assets.swidth = w
                    assets.sheight = h
                    make_screen()
                    wini()
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
                    assets.load_game(assets.game)
                assets.cur_script.handle_events([e])
        except script_error, e:
            assets.cur_script.obs.append(error_msg(e.value,assets.cur_script.lastline_value,assets.cur_script.si,assets.cur_script))
            import traceback
            traceback.print_exc()
    if hasattr(assets, "threads"):
        while [1 for thread in assets.threads if thread and thread.isAlive()]:
            print "waiting"
            pass
if __name__=="__main__":
    run()
