import pygame
import sys,os
import core

pygame.font.init()
ft = pygame.font.Font(os.path.join("fonts","Vera.ttf"),10)

class Window(object):
    _focused = None
    def sf(self,v):
        self._focused = v
    focused = property(lambda s: s._focused,sf)
    move = []
    over = None
window = Window()

class widget(object):
    visible = 1
    def __init__(self,pos=[0,0],size=[0,0],parent=None):
        try:
            self.rpos = pos[:]
        except AttributeError:
            pass
        self.font = ft
        self.parent = parent
        self._width = size[0]
        self._height = size[1]
        self.visible = True
        self.children = []
        self.padding = {"top":3,"bottom":3,"left":2,"right":2}
    def setlayout(self,v):
        self.nolayout = not v
        return self
    def focus(self):
        window.focused = self
    def gw(self):
        if not self.visible: return 0
        return self._width
    def sw(self,w):
        self._width = w
    def gh(self):
        if not self.visible: return 0
        return self._height
    def sh(self,h):
        self._height = h
    width = property(gw,sw)
    height = property(gh,sh)
    def add_child(self,win):
        if win not in self.children: self.children.append(win)
        win.parent = self
        return win
    def remove_child(self,win):
        if win in self.children: self.children.remove(win)
        win.parent = None
        return win
    #~ def mouseover(mp):
        #~ return mp[0]>=pos[0] and mp[0]<=pos[0]+self.width and mp[1]>=pos[1] and mp[1]<=pos[1]+self.height
    def draw(self,dest):
        if self.visible: 
            [x.draw(dest) for x in self.children]
    def event(self,name,pos,*args):
        if pos[0]>=self.rpos[0] and pos[0]<=self.rpos[0]+self.width and pos[1]>=self.rpos[1] and pos[1]<=self.rpos[1]+self.height:
            p2 = [pos[0]-self.rpos[0],pos[1]-self.rpos[1]]
            window.over = self
            for w in self.children:
                if not hasattr(w,"event"): continue
                done = w.event(name,p2,*args)
                if done:
                    return True
            func = getattr(self,name,None)
            if func: 
                args = [pos]+list(args)
                func(*args)
                return True
    def click_down_over(self,pos):
        window.focused = self
    def click_up(self,pos):
        if window.focused == self:
            window.focused = None
    def handle_events(self,evts):
        quit = False
        for evt in evts:
            if evt.type == pygame.KEYUP and evt.key == pygame.K_ESCAPE:
                quit = True
            elif evt.type == pygame.QUIT:
                quit = True
            elif evt.type == pygame.MOUSEMOTION:
                window.over = None
                self.event("move_over",evt.pos,evt.rel,evt.buttons)
                for f in window.move:
                    f(evt.pos,evt.rel)
            elif evt.type == pygame.MOUSEBUTTONDOWN and evt.button == 1:
                window.focused = None
                self.event("click_down_over",evt.pos)
            elif evt.type == pygame.MOUSEBUTTONDOWN and evt.button == 3:
                self.event("rclick_down_over",evt.pos)
            elif evt.type == pygame.MOUSEBUTTONDOWN and evt.button == 4:
                self.event("scroll_up_over",evt.pos)
            elif evt.type == pygame.MOUSEBUTTONDOWN and evt.button == 5:
                self.event("scroll_down_over",evt.pos)
            elif evt.type == pygame.MOUSEBUTTONUP and evt.button == 1:
                self.event("click_up_over",evt.pos)
                if window.focused:
                    window.focused.click_up(evt.pos)
            #~ elif evt.type == pygame.MOUSEBUTTONUP and evt.button == 3:
                #~ if window.over:
                    #~ for i,l in enumerate(self):
                        #~ if over in l.obs:
                            #~ f = open("turnabout_zzztrial/tmp.txt","w")
                            #~ f.writelines([str(l).replace("\n","")+"\n" for l in lines[i:]])
                            #~ f.close()
                            #~ os.system("c:/python25/python PyWright.py turnabout_zzztrial tmp")
            elif evt.type == pygame.KEYDOWN and evt.key == pygame.K_LEFT:
                if window.focused and hasattr(window.focused,"carat_left"):
                    window.focused.carat_left()
            elif evt.type == pygame.KEYDOWN and evt.key == pygame.K_RIGHT:
                if window.focused and hasattr(window.focused,"carat_right"):
                    window.focused.carat_right()
            elif evt.type == pygame.KEYDOWN and evt.key == pygame.K_UP:
                if window.focused and hasattr(window.focused,"carat_up"):
                    window.focused.carat_up()
            elif evt.type == pygame.KEYDOWN and evt.key == pygame.K_DOWN:
                if window.focused and hasattr(window.focused,"carat_down"):
                    window.focused.carat_down()
            elif evt.type == pygame.KEYDOWN and evt.key == pygame.K_BACKSPACE and window.focused:
                if hasattr(window.focused,"backspace"):
                    window.focused.backspace()
            elif evt.type == pygame.KEYDOWN and evt.key == pygame.K_DELETE and window.focused:
                if hasattr(window.focused,"delete"):
                    window.focused.delete()
            elif evt.type == pygame.KEYDOWN and evt.key == pygame.K_RETURN and window.focused:
                if window.focused and hasattr(window.focused,"enter_pressed"):
                    win,window.focused = window.focused,None
                    win.enter_pressed()
            elif evt.type == pygame.KEYDOWN:
                if evt.key not in [pygame.K_LSHIFT,pygame.K_RSHIFT,pygame.K_ESCAPE] and window.focused:
                    if hasattr(window.focused,"insert") and hasattr(evt,"unicode"):
                        window.focused.insert(evt.unicode)
        return quit
    def update(self):
        return False

class editbox(widget):
    def __init__(self,target_ob,target_attr,is_dict=False):
        print "init editbox"
        super(editbox,self).__init__()
        self.is_dict = is_dict
        if target_ob is None:
            self.target_ob = self
            self.target_attr = "text"
            self.text = target_attr
        else:
            self.target_ob = target_ob
            self.target_attr = target_attr
        self.height = self.font.render("TEST",1,[0,0,0]).get_height()
        self.draw_back = True
        self.carat = 0
        self.force_width = None
    def click_up(self,pos):
        pass
    def click_down_over(self,mp):
        mp[0]-=self.rpos[0]
        txt = self.val()
        metrics = self.font.metrics(txt)
        w = 0
        i = 0
        while metrics and w<mp[0] and i<len(metrics):
            w+=metrics[i][4]
            i += 1
        if metrics and mp[0]>2 and mp[0]<sum([x[4] for x in metrics])-2:
            i -= 1
        self.carat = i
        window.focused = self
        return True
    def click_up_over(self,mp):
        pass
    def carat_left(self):
        self.carat -= 1
        if self.carat<0: self.carat = 0
    def carat_right(self):
        self.carat += 1
        l = len(self.val())
        if self.carat>l: self.carat = l
    def val(self):
        if self.is_dict:
            return self.target_ob.get(self.target_attr,"").replace("\n","")
        else:
            return getattr(self.target_ob,self.target_attr).replace("\n","")
    def insert(self,unicode):
        try:
            u = str(unicode)
        except:
            return
        if not u:
            return
        if ord(u)<32 or ord(u)>165:
            return
        v = self.val()
        if self.carat == 0:
            v = str(unicode)+v
        elif self.carat == len(v):
            v = v+str(unicode)
        else:
            v = v[:self.carat]+str(unicode)+v[self.carat:]
        self.set(v)
        self.carat += 1
    def backspace(self):
        v = self.val()
        if self.carat == 0:
            return
        elif self.carat == len(v):
            v = v[:-1]
        else:
            v = v[:self.carat-1]+v[self.carat:]
        self.set(v)
        self.carat -= 1
    def delete(self):
        v = self.val()
        if self.carat == 0:
            v = v[1:]
        elif self.carat == len(v):
            return
        else:
            v = v[:self.carat]+v[self.carat+1:]
        self.set(v)
    def set(self,v):
        if not self.is_dict:
            setattr(self.target_ob,self.target_attr,v)
        else:
            self.target_ob[self.target_attr] = v
    bgcol = [210,210,210]
    bgcol2 = [180,180,200]
    bgfocus = [180,180,220]
    textcol = [0,0,0]
    def draw(self,dest):
        if not self.visible: return
        pos = self.rpos
        val = self.val()
        col = self.textcol
        bgcol = self.bgcol
        bgcol2 = self.bgcol2
        if not bgcol: bgcol = [0,0,0,0]
        if not bgcol2: bgcol2 = [0,0,0,0]
        if self == window.focused:
            bgcol = self.bgfocus
        if not getattr(self,"txtrender",None)==val:
            self.txtrender = self.font.render(val,1,col)
            if hasattr(self,"bg"): del self.bg
        txt = self.txtrender
        ts = list(txt.get_size())
        if self.force_width is not None:
            ts[0] = self.force_width
        if not hasattr(self,"bg"): 
            self.bg = pygame.Surface([ts[0]+4,ts[1]+4]).convert_alpha()
            if hasattr(self,"lastbgcol"): del self.lastbgcol
        bg = self.bg
        if not getattr(self,"lastbgcol",None)==bgcol: 
            bg.fill(bgcol)
            self.lastbgcol = bgcol
            if hasattr(self,"lastbgcol2"): del self.lastbgcol2
        if not getattr(self,"lastbgcol2",None)==bgcol2: 
            pygame.draw.rect(bg,bgcol2,bg.get_rect(),1)
            self.lastbgcol2 = bgcol2
        bg.blit(txt,[2,2])
        if self == window.focused:
            metrics = self.font.metrics(val)
            if metrics:
                x = sum([w[4] for w in metrics][:self.carat])+1
            else:
                x = 0
            pygame.draw.line(bg,[0,0,0],[x,0],[x,ts[1]+4])
        if self.draw_back:
            dest.blit(bg,pos)
        else:
            dest.blit(txt,[pos[0]+2,pos[1]+2])
        self.width = bg.get_width()+4
        super(editbox,self).draw(dest)
        
class label(editbox):
    def __init__(self,text="",rpos=None):
        editbox.__init__(self,None,text)
        if rpos: self.rpos = rpos
        self.draw_back = False
        self.width = 0

class checkbox(widget):
    lastclicked = None
    lastoperation = True
    def __init__(self,text,**kwargs):
        widget.__init__(self,**kwargs)
        self.text = text
        self.editbox = editbox(self,"text")
        self.editbox.draw_back = False
        self.height = self.editbox.height
        self.checked = False
    def draw(self,dest):
        if not self.visible: return
        bgcol = [210,210,210]
        bgcol2 = [140,140,180]
        pygame.draw.rect(dest,bgcol,[self.rpos,[14,self.editbox.height]])
        pygame.draw.rect(dest,[0,0,0],[self.rpos,[14,self.editbox.height]],1)
        if self.checked:
            pygame.draw.rect(dest,bgcol2,[[self.rpos[0]+1,self.rpos[1]+1],[12,self.editbox.height-2]])
            pygame.draw.rect(dest,[0,0,0],[[self.rpos[0]+4,self.rpos[1]+4],[14-8,self.editbox.height-8]])
        self.editbox.rpos[0]=self.rpos[0]+16
        self.editbox.rpos[1]=self.rpos[1]
        self.editbox.draw(dest)
        self.width = self.editbox.width+16
        if window.over == self:
            pygame.draw.line(dest,[0,0,0],[self.rpos[0],self.rpos[1]+self.height-1],[self.rpos[0]+self.width,self.rpos[1]+self.height-1])
    def click_up(self,pos):
        pass
    def click_down_over(self,mp):
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
            if checkbox.lastclicked:
                go = 0
                for x in self.parent.children:
                    if x==checkbox.lastclicked:
                        x.checked = checkbox.lastoperation
                        if not go:
                            go = 1
                        else:
                            checkbox.lastoperation = not checkbox.lastoperation
                            return
                    elif x==self:
                        x.checked = checkbox.lastoperation
                        if not go:
                            go = 1
                        else:
                            checkbox.lastoperation = not checkbox.lastoperation
                            return
                    elif go:
                        x.checked = checkbox.lastoperation
        self.checked = not self.checked
        checkbox.lastclicked = self
        checkbox.lastoperation = self.checked
    def click_up_over(self,mp):
        pass
        
class radiobutton(checkbox):
    groups = {}
    def __init__(self,text,group):
        bin = radiobutton.groups.get(group,[])
        bin.append(self)
        radiobutton.groups[group] = bin
        self.group = radiobutton.groups[group]
        checkbox.__init__(self,text)
    def draw(self,dest):
        if not self.visible: return
        bgcol = [210,210,210]
        bgcol2 = [140,140,180]
        pygame.draw.circle(dest,bgcol,[self.rpos[0]+7,self.rpos[1]+7],7)
        pygame.draw.circle(dest,[0,0,0],[self.rpos[0]+7,self.rpos[1]+7],7,1)
        if self.checked:
            pygame.draw.circle(dest,bgcol2,[self.rpos[0]+7,self.rpos[1]+7],3)
            pygame.draw.circle(dest,[0,0,0],[self.rpos[0]+7,self.rpos[1]+7],3,1)
        self.editbox.rpos[0]=self.rpos[0]+16
        self.editbox.rpos[1]=self.rpos[1]
        self.editbox.draw(dest)
        self.width = self.editbox.width+16
    def click_down_over(self,mp):
        for cb in self.group:
            cb.checked = False
        self.checked = True
        
class progress(widget):
    def __init__(self):
        widget.__init__(self)
        self.progress = 0
        self.text = ""
        self.editbox = editbox(self,"text")
        self.editbox.draw_back = False
    def draw(self,dest):
        if not self.visible: return
        bgcol = [210,210,210]
        bgcol2 = [140,140,180]
        pygame.draw.rect(dest,bgcol,[self.rpos,[self.width,self.height]])
        pygame.draw.rect(dest,[0,0,0],[self.rpos,[self.width,self.height]],1)
        pygame.draw.rect(dest,bgcol2,[[self.rpos[0]+1,self.rpos[1]+1],[(self.width-2)*self.progress,self.height-2]])
        self.editbox.rpos = self.rpos
        self.editbox.draw(dest)
    def click_up(self,pos):
        pass
    def click_down_over(self,mp):
        pass
    def click_up_over(self,mp):
        pass
        
class button(widget):
    def __init__(self,target_ob,target_func,*args,**kwargs):
        super(button,self).__init__(*args,**kwargs)
        self.target_ob = target_ob
        self.target_func = target_func
        self.text = self.target_func.replace("\n","")
        self.height = self.font.render("TEST",1,[0,0,0]).get_height()+2
        self.bgcolor = [200,200,200]
        self.bordercolor = [30,30,30]
        self.textcolor = [0,0,0]
        self.highlightcolor = [255,255,255]
        self.graphic = None
    def click_down_over(self,mp):
        f = self.target_func.replace(" ","_")
        tob = getattr(self,"target_ob",self)
        if not self.target_ob: tob = self
        getattr(tob,f)()
    def draw(self,dest):
        if not self.visible: return
        pos = self.rpos
        bg = self.graphic
        if not bg:
            txt = self.font.render(self.text,1,self.textcolor)
            ts = txt.get_size()
            bg = pygame.Surface([ts[0]+4,ts[1]+4])
            bgcolor = self.bgcolor
            if window.over == self: bgcolor = self.highlightcolor
            bg.fill(bgcolor)
            pygame.draw.rect(bg,self.bordercolor,[0,0,bg.get_width(),bg.get_height()],1)
            bg.blit(txt,[2,2])
        self.width = bg.get_width()+1
        self.height = bg.get_height()
        dest.blit(bg,pos)
        super(button,self).draw(dest)

class pane(widget):
    align = "vert"
    bgcolor = [255,255,255]
    bordercolor = [200,200,200]
    border = True
    background = True
    def __init__(self,*args,**kwargs):
        super(pane,self).__init__(*args,**kwargs)
        self.in_height = 0
    def render(self):
        if not self.visible: return
        if not hasattr(self,"offset"):
            self.offset = [0,0]
        surf = pygame.Surface([self.width,self.height])
        if self.background:
            surf.fill(self.bgcolor)
        else:
            surf = surf.convert_alpha()
            surf.fill([0,0,0,0])
        x = self.offset[0]
        yoff = self.offset[1]
        y = yoff
        for w in self.children:
            if self.align and not getattr(w,"nolayout",False):
                w.rpos = [x+w.padding["left"],y+w.padding["top"]]
            if y+w.height>0 and y<self.height or not self.align or getattr(w,"nolayout",False):
                w.draw(surf)
            if self.align == "vert" and not getattr(w,"nolayout",False):
                #if not w.height: continue
                y += w.height+w.padding["bottom"]+w.padding["top"]
            elif self.align == "horiz" and not getattr(w,"nolayout",False):
                #if not w.width: continue
                x += w.width+w.padding["right"]+w.padding["left"]
        self.in_height = y-yoff
        if self.border:
            pygame.draw.rect(surf,self.bordercolor,surf.get_rect(),1)
        return surf
    def draw(self,dest):
        dest.blit(self.render(),self.rpos)
        
class scrollbutton(widget):
    def __init__(self,rpos=[0,0]):
        super(scrollbutton,self).__init__(rpos)
        window.move.append(self.move)
    def draw(self,dest):
        if not self.visible: return
        x,y = self.rpos
        pygame.draw.rect(dest,[150,150,150],[[x,y],[self.width,self.height]])
        pygame.draw.rect(dest,[200,220,200],[[x+1,y+1],[self.width-2,self.height-2]])
    def move(self,pos,rel):
        if window.focused==self:
            self.scroll(rel)
    def scroll(self,rel):
            self.rpos[1]+=rel[1]
            if self.rpos[1]+self.height>self.parent.height-2:
                self.rpos[1] = self.parent.height-self.height-2
            if self.rpos[1]<2:
                self.rpos[1] = 2
class scrollbar(widget):
    def __init__(self,rpos=[0,0]):
        super(scrollbar,self).__init__(rpos)
        self.scbut = scrollbutton([2,2])
        self.add_child(self.scbut)
    def draw(self,dest):
        if not self.visible: return
        x,y = self.rpos
        surf = pygame.Surface([self.width,self.height])
        pygame.draw.rect(surf,[150,150,150],[[0,0],[self.width,self.height]])
        pygame.draw.rect(surf,[220,240,240],[[1,1],[self.width-2,self.height-2]])
        
        self.scbut.width = self.width-4
        self.scbut.draw(surf)
        dest.blit(surf,self.rpos)
        
class scrollpane(pane):
    def __init__(self,*args,**kwargs):
        super(scrollpane,self).__init__(*args,**kwargs)
        self.scbar = scrollbar([0,0])
        self.scbar.nolayout = True
        self.add_child(self.scbar)
    def scroll_up_over(self,mp):
        self.scbar.scbut.scroll([0,-3])
        self.updatescroll()
    def scroll_down_over(self,mp):
        self.scbar.scbut.scroll([0,3])
        self.updatescroll()
    def updatescroll(self):
        surf = super(self.__class__,self).render()
        self.scbar.rpos = [self.width-15,0]
        self.scbar.width = 15
        self.scbar.height = self.height
        pages = self.in_height/float(self.height)
        try:
            self.scbar.scbut.height = int(self.scbar.height-4)/(pages)
        except ZeroDivisionError:
            self.scbar.scbut.height = int(self.scbar.height-4)
        if self.scbar.scbut.height > int(self.scbar.height-4):
            self.scbar.scbut.height = int(self.scbar.height-4)
        try:
            pix = float(self.in_height)/float(self.scbar.height-4)
        except ZeroDivisionError:
            pix = 0
        self.offset[1]=-int(pix*(self.scbar.scbut.rpos[1]-2))
        return surf
    def draw(self,dest):
        if not self.visible: return
        surf = self.updatescroll()
        self.scbar.draw(surf)
        dest.blit(surf,self.rpos)
