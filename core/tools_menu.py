import pygame,sys,os

import core

import gui

class msg(gui.pane):
    def __init__(self,m,assets):
        gui.pane.__init__(self)
        self.width = 256
        self.height = 100
        self.pri = -1001
        self.z = 11001
        self.rpos = [0,100]
        self.align = "vert"
        
        for line in core.wrap_text([m],assets.get_image_font("block_arial"),300):
            print line
            text = gui.label(line)
            self.children.append(text)
    def click_down_over(self,*args):
        self.delete()
    def delete(self):
        self.kill = 1
        super(msg,self).delete()

class tools_menu(gui.pane):
    def __init__(self,*args,**kwargs):
        self.sw=kwargs["sw"]
        self.sh=kwargs["sh"]
        self.assets=assets=kwargs["assets"]
        gui.widget.__init__(self)
        self.width = 1000
        self.height = 1000
        self.pri = -1001
        self.z = 11001
        self.align = False
            
        self.sheight = assets.sheight
        self.swidth = assets.swidth
        self.base()
    def make_button(self,text,pos):
        b = gui.button(self,text,pos)
        self.children.append(b)
        return b
    def base(self):
        assets = self.assets
        sw,sh = self.sw,self.sh
        sh = assets.sh*assets.num_screens
        self.children[:] = []
        self.make_button("gif2strip",[0,10])
        #self.make_button("aao2pywright",[0,30])
        self.make_button("close tools",[0,40])
    def gif2strip(self):
        assets = self.assets
        sw,sh = self.sw,self.sh
        self.files_dir = gui.directory([0,0])
        self.files_dir.populate(".",self,"giffile",lambda x: x.endswith(".gif"),False)
        self.children.append(self.files_dir)
    def aao2pywright(self):
        assets = self.assets
        sw,sh = self.sw,self.sh
        settings_menu.firstpane = "saves"
        self.base()
        line = gui.pane([0,30],[sw,20])
        line.align = "horiz"
        self.children.append(line)
        line.children.append(gui.label("Autosave?"))
        class myb(gui.checkbox):
            def click_down_over(self,*args):
                super(myb,self).click_down_over(*args)
                if self.checked:
                    assets.autosave = 1
                else:
                    assets.autosave = 0
                wini(assets)
        line.children.append(myb("autosave"))
        cb = line.children[-1]
        if assets.autosave: cb.checked = True
            
        line = gui.pane([0,50],[sw,20])
        line.align = "horiz"
        self.children.append(line)
        line.children.append(gui.label("Minutes between autosave"))
        class mymin(gui.editbox):
            def insert(self,val):
                if val not in u"0123456789":
                    return
                super(mymin,self).insert(val)
            def set(self,val):
                super(mymin,self).set(val)
                if not val:
                    val = 0
                assets.autosave_interval = int(val)
                wini(assets)
        self.autosave_interval = str(assets.autosave_interval)
        line.children.append(mymin(self,"autosave_interval"))
            
        line = gui.pane([0,70],[sw,20])
        line.align = "horiz"
        self.children.append(line)
        line.children.append(gui.label("Autosave backups"))
        class mye(gui.editbox):
            def insert(self,val):
                if val not in u"0123456789":
                    return
                super(mye,self).insert(val)
            def set(self,val):
                super(mye,self).set(val)
                if not val:
                    val = 0
                assets.autosave_keep = int(val)
                wini(assets)
        self.autosave_keep = str(assets.autosave_keep)
        line.children.append(mye(self,"autosave_keep"))
    def update(self,*args):
        assets = self.assets
        self.rpos = [0,0]
        self.pos = self.rpos
        self.children[:] = [x for x in self.children if not getattr(x,"kill",0)]
        for x in self.children:
            x.update()
        if getattr(self,"giffile",""):
            sys.path.append("tools")
            import gif2strip
            try:
                path = gif2strip.go(self.giffile)
                m = msg("Converted "+path.rsplit("/",1)[1]+".png",self.assets)
                self.children.append(m)
                graphic = pygame.transform.rotozoom(pygame.image.load(path+".png"),0,0.25)
                m.children.append(gui.button(None,"x"))
                m.children[-1].graphic = graphic
                setattr(m.children[-1],"x",m.click_down_over)
            except Exception:
                import traceback
                traceback.print_exc()
                self.children.append(msg("File could not be converted.",self.assets))
            self.giffile = ""
        return True
    def close_tools(self):
        self.delete()
    def delete(self):
        self.kill = 1
