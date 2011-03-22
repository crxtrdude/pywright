import pygame,sys,os

import gui

class directory(gui.pane):
    def populate(self,dir,variabledest,variablename):
        self.children[:] = []
        self.width=256
        self.height=192
        self.files = gui.scrollpane([10,20])
        self.files.width = 240
        self.files.height = 140
        self.children.append(self.files)
        
        for file in os.listdir(dir):
            if os.path.isdir(dir+"/"+file) or file.endswith(".gif"):
                class myb(gui.button):
                    def click_down_over(s,*args):
                        if os.path.isdir(s.path):
                            self.populate(s.path,variabledest,variablename)
                        else:
                            self.chosen_file = s.path
                b = myb(None,file)
                b.path = dir+"/"+file
                self.files.add_child(b)
        
        self.chosen_file = dir
        self.file = gui.editbox(self,"chosen_file")
        self.file.force_width = 250
        self.children.append(self.file)
        
        class myb(gui.button):
            def click_down_over(s,*args):
                setattr(variabledest,variablename,self.chosen_file)
                self.delete()
        b = myb(None,"Choose")
        self.children.append(b)
    def delete(self):
        print "kill self"
        self.kill = 1
        super(directory,self).delete()

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
        self.make_button("gif2strip",[0,0])
        self.make_button("aao2pywright",[0,20])
        self.make_button("close tools",[0,40])
    def gif2strip(self):
        assets = self.assets
        sw,sh = self.sw,self.sh
        self.files_dir = directory([0,0])
        self.files_dir.populate(".",self,"giffile")
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
            gif2strip.go(self.giffile)
            self.giffile = ""
        return True
    def close_tools(self):
        self.delete()
    def delete(self):
        self.kill = 1
