import sys,os
if sys.platform=="win32":
    os.environ['SDL_VIDEODRIVER']='windib'
import new
import core
assets = core.assets
def ap(self,*args,**kwargs):
    print "adding der portrait"
def se(self,*args):
    print "setting der emotion"
#assets.add_portrait = ap
assets.set_emotion = se

import libengine
from gui import *

import pygame
pygame.USE_GL = False

class source_pane(pane):
    def __init__(self,source):
        pane.__init__(self)
        self.source = pygame.image.load(source)
        self.selection = [[0,0],[256,192]]
    def draw(self,dest):
        self.source.blit(dest,self.rpos)
        p = self.selection[0]
        p[0]+=self.rpos[0]
        p[1]+=self.rpos[1]
        pygame.draw.rect(dest,[255,255,255],[p,self.selection[1]])

class line_editbox(editbox):
    def __init__(self,*args,**kwargs):
        editbox.__init__(self,*args,**kwargs)
        self.bgcol = None
        self.bgcol2 = None
    def replace(self,ob):
        ourpanel = self.parent
        ourcontainer = ourpanel.parent
        index = ourcontainer.children.index(ourpanel)
        newob = ourcontainer.children[index]=ob
        newob.parent = ourcontainer
    def remove(self):
        self.previous()
        self.parent.parent.children.remove(self.parent)
    def backspace(self):
        if not self.val():
            return self.remove()
        if self.carat == 0:
            return self.previous()
        editbox.backspace(self)
    def reparse(self):
        self.replace(makeob(self.parent.val()))
    def enter_pressed(self):
        ourpanel = self.parent
        ourcontainer = ourpanel.parent
        index = ourcontainer.children.index(ourpanel)
        nl = empty("")
        if self.carat>0: index+=1
        ourcontainer.children.insert(index,nl)
        nl.parent = ourcontainer
        if self.carat>0: 
            self.next()
        else:
            self.previous()
        #self.reparse()
    def previous(self):
        ourpanel = self.parent
        ourcontainer = ourpanel.parent
        index = ourcontainer.children.index(ourpanel)
        if index>1:
            ourcontainer.children[index-1].focus()
            while ourcontainer.children[index-1].rpos[1]<ourpanel.offset[1]:
                ourcontainer.scroll_up_over([0,0])
    def next(self):
        ourpanel = self.parent
        ourcontainer = ourpanel.parent
        index = ourcontainer.children.index(ourpanel)
        if index<len(ourcontainer.children)-1:
            ourcontainer.children[index+1].focus()
            while ourcontainer.children[index+1].rpos[1]>ourpanel.offset[1]+530:
                ourcontainer.scroll_down_over([0,0])
    def carat_up(self):
        self.previous()
    def carat_down(self):
        self.next()
    def focus(self):
        window.focused = self
class aline(pane):
    arrow = None
    def __init__(self,line):
        super(aline,self).__init__()
        self.line = line
        self.args = [x.strip() for x in line.split(" ")]
        #~ self.add_child(button(self,"X"))
        #~ self.add_child(button(self,"V"))
        #~ self.add_child(button(self,"N"))
        self.kill = 0
        self.add = 0
        self.align = "horiz"
        self.border = False
        if not aline.arrow:
            aline.arrow = pygame.image.load("art/general/arrow_right.png")
        self.offset = [15,0]
    def focus(self):
        window.focused = self
    def draw(self,dest):
        super(aline,self).draw(dest)
        if window.focused == self or window.focused in self.children:
            dest.blit(aline.arrow,self.rpos)
    def rclick_down_over(self,pos):
        index = self.parent.children.index(self)
        if isinstance(self,empty):
            newob = self.parent.children[index]=makeob(self.val())
            newob.parent = self.parent
            if isinstance(newob,gfxblock):
                i = index-1
                mode = "add"
                label = False
                while i>=0:
                    if hasattr(self.parent.children[i],"val"):
                        for v in self.parent.children[i].val().split("\n"):
                            if v.startswith("bg ") or v.startswith("fg ") or v.startswith("ev ") or v.startswith("char "):
                                if mode=="add":
                                    del self.parent.children[i]
                                    newob.addline(v,0)
                                else:
                                    newob.addline(v+" name=NOSAVE",0)
                            else:
                                mode = "remember"
                            if v.startswith("label "):
                                label = True
                                break
                    if label: break
                    i -= 1
                i = self.parent.children.index(newob)+1
                while i<len(self.parent.children):
                    if isinstance(self.parent.children[i],empty):
                        v = self.parent.children[i].val()
                        if v.startswith("bg ") or v.startswith("fg ") or v.startswith("ev ") or v.startswith("char "):
                            del self.parent.children[i]
                            newob.addline(v)
                            continue
                    break
        else:
            del self.parent.children[index]
            v = self.val()
            for l in v.strip().split("\n"):
                newob = empty(l)
                self.parent.children.insert(index,newob)
                newob.parent = self.parent
                index += 1
    def click_down_over(self,pos):
        self.focus()
    def click_up(self,mp):
        pass
    def click_up_over(self,mp):
        pass
    def gwidth(self):
        return sum([(x.width+5) for x in self.children])+self.offset[0]
    def gheight(self):
        if self.children:
            return max([x.height for x in self.children])+5+self.offset[1]
        return 0
    def s(self,h):
        pass
    height = property(gheight,s)
    width = property(gwidth,s)
    def X(self):
        self.kill = 1
    def V(self):
        self.add = 1
    def N(self):
        self.add = -1
    def val(self):
        return ""
    def write(self,f):
        f.write(self.val()+"\n")
class empty(aline):
    def __init__(self,line):
        super(empty,self).__init__(line)
        self.add_child(line_editbox(self,"line"))
    def focus(self):
        self.children[0].focus()
    def val(self):
        return self.children[-1].val()
class advancedline(aline):
    def __init__(self,line):
        super(advancedline,self).__init__(line)
        self.add_child(line_editbox(self,"line"))
    def focus(self):
        self.children[0].focus()
    def val(self):
        return self.children[-1].val()
class textbox(widget):
    def __init__(self,line):
        super(textbox,self).__init__()
        self.line = line
        assets.variables["_speaking"] = None
        self.tb = core.textbox(line.replace("{n}","\n"),rightp=False)
        self.tb.go = 1
        self.draw(pygame.Surface([10,10]))
    def backspace(self):
        self.editline.remove()
    def carat_up(self):
        self.editline.previous()
    def carat_down(self):
        self.editline.next()
    def click_down_over(self,pos):
        self.focus()
    def click_up(self,mp):
        pass
    def click_up_over(self,mp):
        pass
    def draw(self,dest):
        s = pygame.Surface([256,192])
        self.tb.update()
        self.tb.draw(s)
        if not hasattr(self.tb,"rpos1"): return
        dest.blit(s.subsurface([self.tb.rpos1,[self.tb.width1,self.tb.height1]]),self.rpos)
        self.width,self.height = self.tb.width1,self.tb.height1
class texteditbox(line_editbox):
    def enter_pressed(self):
        self.tb.text = self.val().replace("{n}","\n")
        self.tb.written = ""
        self.tb.wlen = 0
        self.tb.next = 0
        self.tb.nextline = 0
        self.tb.next_char = 0
        self.tb.go = 1
        self.tb.num_lines = 4
    def click_down_over(self,pos):
        self.focus()
    def click_up(self,mp):
        pass
    def click_up_over(self,mp):
        pass
class textbox_line(aline):
    def __init__(self,line):
        super(textbox_line,self).__init__(line)
        self.line = line
        self.eb = texteditbox(self,"line")
        self.eb.visible = False
        self.tb = textbox(line)
        self.eb.tb = self.tb.tb
        self.tb.editline = self.eb
        self.add_child(self.eb)
        self.add_child(self.tb)
        self.align = "vert"
    def click_down_over(self,pos):
        self.focus()
    def focus(self):
        self.tb.focus()
    def draw(self,dest):
        assets.variables["_speaking"] = None
        nt = "\n"
        if self.parent:
            finished = 0
            for val in reversed(self.parent.children[0:self.parent.children.index(self)]):
                if hasattr(val,"val"):
                    for line in val.val().split("\n"):
                        if line.startswith("char"):
                            try:
                                nt = line.split(" ")[1]
                                finished = 1
                                break
                            except:
                                pass
                        elif line.startswith("set _speaking "):
                            nt = line.split(" ",2)[2]
                            finished = 1
                            break
                        elif line.startswith("label"):
                            finished = 1
                            break
                if finished:
                    break
        if self.tb.tb.nametag != nt+"\n":
            core.textbox.nametag = nt
            self.tb.tb.nametag = nt+"\n"
            self.eb.enter_pressed()
            self.tb.tb.draw(dest)
        super(textbox_line,self).draw(dest)
        self.width = self.eb.width+self.tb.width
        self.height = self.tb.height+self.eb.height+10
    def val(self):
        return '"'+self.children[0].val()+'"'
class gamescreen(widget):
    def __init__(self,parent):
        self.parent = parent
        super(gamescreen,self).__init__()
        self.width,self.height = [256,192]
    def render(self):
        surf = pygame.Surface([256,192]).convert()
        self.parent.script.update()
        self.parent.script.draw(surf)
        return surf
    def draw(self,dest):
        dest.blit(self.render(),self.rpos)
    def move_over(self,pos,rel,btn):
        if self.parent.target and btn[0]:
            self.parent.target.pos[0]+=rel[0]
            self.parent.target.pos[1]+=rel[1]
            self.parent.target.esx,self.parent.target.esy = [str(o) for o in self.parent.target.pos]
    def click_down_over(self,pos):
        self.parent.focus()
        self = self.parent
        def isalpha(s,p):
            ck = s.get_colorkey()
            try:
                c = s.get_at(p)
            except IndexError:
                return True
            if c[3]<30: return True
            if ck and c[:3] == ck[:3]: return True
        self.target = None
        for o in self.world.click_order():
            if getattr(o,"id_name",None)=="NOSAVE": continue
            if not hasattr(o,"rpos"): o.rpos = o.pos
            if not hasattr(o,"width"): o.width = o.img.get_width() if o.img else 0
            if not hasattr(o,"height"): o.height = o.img.get_height() if o.img else 0
            if pos[0]>=o.rpos[0] and pos[0]<=o.rpos[0]+o.width\
            and pos[1]>=o.rpos[1] and pos[1]<=o.rpos[1]+o.height\
            and not isalpha(o.img,(pos[0]-o.rpos[0],pos[1]-o.rpos[1]))\
            and getattr(o,"select",True):
                self.target = o
                break
class gfxblock(aline):
    def __init__(self,line):
        super(gfxblock,self).__init__(line)
        self.lines = [line]
        self.world = libengine.World()
        self.build()
        self._target = self.world.render_order()[0]
        self.add_child(gamescreen(self))
        #~ self.add_child(button(self,"add object"))
        self.l = label("Current Target: None",rpos=[275,20]).setlayout(False)
        self.add_child(self.l)
        self.wx=self.wy=self.wz=None
        self.width,self.height = [600,192]
        self.align = "horiz"
    def add_object(self):
        pass
    def set_target(self,val):
        self._target = val
        
        self.l.text = "Current Target: "+str(self.target)
        self.l.draw(screen)
        del self.children[self.children.index(self.l)+1:]
        self.wx=self.wy=self.wz=None
        
        if self.target:
            self.target.esx = repr(self.target.pos[0])
            self.wx = editbox(self.target,"esx").setlayout(False)
            self.wx.rpos = [295,40]
            def enter_pressed():
                self.target.pos[0] = int(self.wx.val())
            self.wx.enter_pressed = enter_pressed
            self.add_child(self.wx)
            self.add_child(label("X:",[275,40]).setlayout(False))

            self.target.esy = repr(self.target.pos[1])
            self.wy = editbox(self.target,"esy").setlayout(False)
            self.wy.rpos = [375,40]
            def enter_pressed():
                self.target.pos[1] = int(self.wy.val())
            self.wy.enter_pressed = enter_pressed
            self.add_child(self.wy)
            self.add_child(label("Y:",[355,40]).setlayout(False))
            
            def remove(t=self.target):
                self.world.all.remove(t)
                del self.children[self.children.index(self.l)+1:]
            btn = button(None,"remove",pos=[275,60]).setlayout(False)
            btn.remove = remove
            self.add_child(btn)
    target = property(lambda self:self._target,set_target)
    def click_down_over(self,p):
        self.target = None
        self.focus()
    def addline(self,line,pos=None):
        if pos is None:
            self.lines.append(line)
        else:
            self.lines.insert(pos,line)
        self.build()
    def build(self):
        self.script = s = libengine.Script()
        s.init(scriptlines=self.lines)
        assets.stack.append(s)
        while s.si<len(self.lines):
            s.interpret()
        bg = core.bg()
        surf = pygame.Surface([256,192])
        surf.fill([100,100,100])
        for x in xrange(200):
            pygame.draw.line(surf,[150,150,150],[(x-50)*3,0],[(x-50)*3+20,192])
        bg.img = surf
        bg.z = -1000
        bg.select = False
        s.world.append(bg)
        self.world = s.world
    def val(self):
        s=""
        for o in self.world.render_order():
            if getattr(o,"id_name",None)=="NOSAVE": continue
            if not hasattr(o,"makestr"): continue
            ms = o.makestr()
            if ms.strip():
                s+=ms+"\n"
        return s
    def write(self,f):
        f.write(self.val()+"\n")

def makeob(line,parent=None):
    if parent and not hasattr(parent,"curlines"):
        parent.curlines = []
    if line.startswith("bg ") or line.startswith("fg ") or line.startswith("char ") or line.startswith("ev "):
        if parent and isinstance(parent.lastmade,gfxblock):
            parent.lastmade.addline(line)
            parent.curlines += [line+" name=NOSAVE"]
            return parent.lastmade
        g = gfxblock(line)
        if parent:
            g.lines = parent.curlines+g.lines
            parent.curlines += [line+" name=NOSAVE"]
        g.build()
        return g
    if not line.strip() and parent and isinstance(parent.lastmade,gfxblock):
        parent.lastmade.addline(line)
        return None
    if line.startswith('"'):
        tbl = textbox_line(line.strip()[1:-1])
        tbl.rpos = [0,0]
        tbl.draw(pygame.Surface([1,1]))
        return tbl
    if line.startswith("label "):
        if parent: parent.curlines = []
        l = advancedline(line.split("label ",1)[1])
        def val(): return "label "+l.children[0].val()
        l.val = val
        l.padding["top"] = 30
        l.children[0].font = pygame.font.Font("fonts/Vera.ttf",14)
        l.children[0].bgcol = [220,255,255]
        l.children[0].bgfocus = [200,225,225]
        return l
    if line.rsplit("#",1)[0].strip() and not line.startswith("include ") and not getattr(assets.cur_script,"_"+line.split(" ")[0],None):
        l = empty(line)
        #l.padding["top"] = 30
        #l.children[0].font = pygame.font.Font("fonts/Vera.ttf",14)
        l.children[0].bgcol = [220,0,0]
        l.children[0].bgfocus = [200,0,0]
        return l
    l = empty(line)
    #~ l.children[0].bgcol = [255,255,255]
    #~ l.children[0].bordercolor = [0,255,255]
    #~ l.children[0].bgfocus = [200,225,225]
    return l
makeob.nt = "\n"

screen = pygame.display.set_mode([800,600])

root = widget([0,0],[800,600])

class bar(widget):
    def draw(self,surf):
        self.padding["top"]=0
        self.padding["bottom"]=0
        pygame.draw.line(surf,[0,100,50],self.rpos,[self.rpos[0]+1000,self.rpos[1]],5)

class script(scrollpane):
    def __init__(self,lines,*args,**kwargs):
        self.padding = 5
        scrollpane.__init__(self,*args,**kwargs)
        self.rpos = [2,20]#[50,100]
        self.width,self.height = [798,530]
        self.insert_bar = None
        self.lastmade = None
        for l in lines:
            o = makeob(l,self)
            self.lastmade = o
            if o:
                self.add_child(o)
class script_edit(widget):
    def __init__(self,script_name,*args,**kwargs):
        widget.__init__(self,*args,**kwargs)
        self.width,self.height = [800,600]
        self.script_name,ext = script_name.rsplit(".",1)
        self.script = libengine.Script()
        assets.stack = [self.script]
        self.script.init(self.script_name,macros=False,ext="."+ext)
        self.edit_pane = script(self.script.scriptlines)
        self.add_child(self.edit_pane)
        
        self.add_child(button(self,"back",[3,3]))
        self.add_child(button(self,"save",[50,3]))
        self.add_child(label("Right click to convert between code/object",[200,3]))
    def back(self):
        root.children = []
        root.add_child(script_menu())
    def save(self):
        print "saving"
        print self.script_name+".txt"
        f = open(assets.game+"/"+self.script_name+".txt","w")
        for o in self.edit_pane.children:
            if hasattr(o,"write"):
                o.write(f)
        f.close()
class script_menu(scrollpane):
    def __init__(self,*args,**kwargs):
        scrollpane.__init__(self,*args,**kwargs)
        self.width,self.height=[600,280]
        self.rpos = [100,50]
        self.add_child(button(self,"Change Case"))
        self.add_child(label("-----------------"))
        self.add_child(label("Current Game/Case:"+assets.game))
        self.children[-1].font = pygame.font.Font("fonts/Vera.ttf",14)
        self.add_child(label("Select a script to edit:"))
        for d in os.listdir(assets.game):
            if d in [".svn"]: continue
            if not d.endswith(".txt") and not d.endswith(".mcro"): continue
            b = button(self," "+d)
            self.add_child(b)
            def _choose_(d=d):
                self.lgame(d)
            setattr(self,"_"+d,_choose_)
        self.add_child(label("----------------"))
        self.add_child(button(self,"Add a script"))
    def lgame(self,s):
        root.children = []
        root.add_child(script_edit(s))
    def Change_Case(self):
        root.children = []
        assets.game = assets.game[:assets.game.rfind("/",2)]
        root.add_child(case_menu())
    def Add_a_script(self):
        root.add_child(new_script_menu())
        root.children[-1].lgame = self.lgame
class new_script_menu(pane):
    def __init__(self,*args,**kwargs):
        pane.__init__(self,*args,**kwargs)
        self.bgcolor = [200,230,200]
        self.align = None
        self.width,self.height = [300,150]
        self.rpos = [200,350]
        self.add_child(label("Please name new script (including the .txt extension)"))
        self.script_name = "newscript.txt"
        self.add_child(editbox(self,"script_name"))
        self.children[-1].rpos = [5,40]
        self.add_child(label(""))
        self.children[-1].rpos = [5,60]
        self.add_child(button(self,"Cancel"))
        self.children[-1].rpos = [5,self.height-20]
        self.add_child(button(self,"Create"))
        self.children[-1].rpos = [self.width-60,self.height-20]
    def Cancel(self):
        self.parent.remove_child(self)
    def Create(self):
        pth = assets.game+"/"+self.script_name
        if os.path.exists(pth):
            self.children[2].text = "Error: path already exists"
            return
        f = open(pth,"w")
        f.write("//WrightScript file\n")
        f.close()
        self.lgame(self.script_name)
class case_menu(scrollpane):
    def __init__(self,*args,**kwargs):
        scrollpane.__init__(self,*args,**kwargs)
        self.width,self.height=[600,280]
        self.rpos = [100,50]
        self.add_child(button(self,"Choose Different Game"))
        self.add_child(label("-------------------------"))
        self.add_child(label("                     Current Game: "+assets.game))
        self.children[-1].font = pygame.font.Font("fonts/Vera.ttf",14)
        self.add_child(label("Select case.  Green cases contain an intro.txt, grey cases do not, and might not in fact be cases at all:"))
        for d in os.listdir(assets.game):
            if d in [".svn"]: continue
            if not os.path.isdir(assets.game+"/"+d): continue
            if d in ["art","music","sfx","movies"]: continue
            b = button(self," "+d)
            if os.path.exists(assets.game+"/"+d+"/intro.txt"):
                b.bgcolor = [20,200,50]
            self.add_child(b)
            def _choose_(d=d):
                self.lgame(d)
            setattr(self,"_"+d.replace(" ","_"),_choose_)
        self.add_child(label("------------------"))
        self.add_child(button(self,"Create a new case"))
    def lgame(self,g):
        assets.game = assets.game+"/"+g
        root.children = []
        root.add_child(script_menu())
    def Choose_Different_Game(self):
        assets.game = ""
        root.children = []
        root.add_child(game_menu())
    def Create_a_new_case(self):
        root.add_child(new_case_menu())
        root.children[-1].lgame = self.lgame
class new_case_menu(pane):
    def __init__(self,*args,**kwargs):
        pane.__init__(self,*args,**kwargs)
        self.bgcolor = [200,230,200]
        self.align = None
        self.width,self.height = [300,150]
        self.rpos = [200,350]
        self.add_child(label("Please enter a name for your new case:"))
        self.case_name = "New Case"
        self.add_child(editbox(self,"case_name"))
        self.children[-1].rpos = [5,40]
        self.add_child(label(""))
        self.children[-1].rpos = [5,60]
        self.add_child(button(self,"Cancel"))
        self.children[-1].rpos = [5,self.height-20]
        self.add_child(button(self,"Create"))
        self.children[-1].rpos = [self.width-60,self.height-20]
    def Cancel(self):
        self.parent.remove_child(self)
    def Create(self):
        if [1 for x in self.case_name if x not in "abcdefghijklmnopqrstuvwxyz _-1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"]:
            self.children[2].text = "Name must contain only letters, numbers, or _/-"
            return
        pth = assets.game+"/"+self.case_name
        if os.path.exists(pth):
            self.children[2].text = "Error: path already exists"
            return
        os.mkdir(pth)
        os.mkdir(pth+"/art")
        for ad in os.listdir("art"):
            os.mkdir(pth+"/art/"+ad)
        os.mkdir(pth+"/music")
        os.mkdir(pth+"/sfx")
        os.mkdir(pth+"/movies")
        f = open(pth+"/intro.txt","w")
        f.write("bg black\n\"Welcome to your brand new case!\"\n")
        f.close()
        self.lgame(self.case_name)
class game_menu(scrollpane):
    def __init__(self,*args,**kwargs):
        scrollpane.__init__(self,*args,**kwargs)
        self.width,self.height=[600,280]
        self.rpos = [100,50]
        self.add_child(label("Choose a game to edit:"))
        for d in os.listdir("games"):
            if d in [".svn"]: continue
            b = button(self," "+d)
            self.add_child(b)
            def _choose_(d=d):
                self.lgame(d)
            setattr(self,"_"+d.replace(" ","_"),_choose_)
        self.add_child(label("-------------------------------"))
        self.add_child(button(self,"Create New Game"))
    def lgame(self,g):
        assets.game = "games/"+g
        root.children = []
        root.add_child(case_menu())
    def Create_New_Game(self):
        root.add_child(new_game_menu())
        root.children[-1].lgame = self.lgame
class new_game_menu(pane):
    def __init__(self,*args,**kwargs):
        pane.__init__(self,*args,**kwargs)
        self.bgcolor = [200,230,200]
        self.align = None
        self.width,self.height = [300,150]
        self.rpos = [200,350]
        self.add_child(label("Please enter a name for your new game:"))
        self.game_name = "New Game"
        self.add_child(editbox(self,"game_name"))
        self.children[-1].rpos = [5,40]
        self.add_child(label(""))
        self.children[-1].rpos = [5,60]
        self.add_child(button(self,"Cancel"))
        self.children[-1].rpos = [5,self.height-20]
        self.add_child(button(self,"Create"))
        self.children[-1].rpos = [self.width-60,self.height-20]
    def Cancel(self):
        self.parent.remove_child(self)
    def Create(self):
        if os.path.exists("games/"+self.game_name):
            self.children[2].text = "Error: path already exists"
            return
        if [1 for x in self.game_name if x not in "abcdefghijklmnopqrstuvwxyz _-1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"]:
            self.children[2].text = "Name must contain only letters, numbers, or _/-"
            return
        pth = "games/"+self.game_name
        os.mkdir(pth)
        os.mkdir(pth+"/art")
        for ad in os.listdir("art"):
            os.mkdir(pth+"/art/"+ad)
        os.mkdir(pth+"/music")
        os.mkdir(pth+"/sfx")
        os.mkdir(pth+"/movies")
        f = open(pth+"/readme.txt","w")
        f.write("Newly Created Game\nName: Enter games name\nAuthor: Enter your name\nDate: Date it was created/updated\n\nSome info about the game could go here.\nSome more paragraph about game etc.\n\n\nPlace any original art, music, or sound effects that you will use in more than one case in the art,music,sfx folders in this directory.  Each case should also be a unique directory in this folder.")
        f.close()
        self.lgame(self.game_name)
root.add_child(game_menu())


#~ class funcs:
    #~ def save(self):
        #~ f = open(script,"w")
        #~ f.writelines([str(l).replace("\n","")+"\n" for l in lines])
        #~ f.close()
        #~ print "saved"
#~ main = funcs()
#~ sbt = button(main,"save")
#~ sbt.rpos = [400,0]
#~ root.add_child(sbt)

clock = pygame.time.Clock()
running = True  
while running:
    mp = pygame.mouse.get_pos()
    clock.tick(60)
    screen.fill([225,225,225])
    root.draw(screen)
    pygame.display.flip()
    pygame.event.pump()
    quit = root.handle_events(pygame.event.get())
    if quit: running = False
    