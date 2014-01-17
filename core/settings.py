import pygame,sys,os

import gui


def wini(assets):
    f = open("settings.ini","w")
    f.write(""";standard width is 256
;standard height is 192
width=%s
height=%s
scale2x=%s
smoothscale=%s
fullscreen=%s
screens=%s
show_fps=%s
sound_format=%s
sound_bits=%s
sound_buffer=%s
sound_volume=%s
music_volume=%s
screen_compress=%s
autosave=%s
autosave_interval=%s
autosave_keep=%s
tool_path=%s"""%(assets.swidth,assets.sheight,assets.filter,assets.smoothscale,
assets.fullscreen,assets.num_screens,
int(assets.show_fps),
assets.sound_format,assets.sound_bits,assets.sound_buffer,int(assets.sound_volume),int(assets.music_volume),
int(assets.screen_compress),int(assets.autosave),int(assets.autosave_interval),int(assets.autosave_keep),
assets.tool_path))
    f.close()
    
def load(assets):
    assets.fullscreen = 0
    assets.swidth = 256
    assets.sheight = 192*2
    assets.filter = 0
    assets.num_screens = 2
    assets.screen_compress = 0  #Whether to move objects on screen 2 to screen 1 if num_screens is 1
    assets.autosave = 1
    assets.autosave_interval = 5 #minutes between autosaves
    assets.autosave_keep = 2 #how many saves to keep
    assets.show_fps = 0
    assets.smoothscale = 0
    if os.path.exists("display.ini"):
        f = open("display.ini")
        t = f.read()
        f.close()
        os.remove("display.ini")
        f = open("settings.ini","w")
        f.write(t)
        f.close()
    if os.path.exists("settings.ini"):
        f = open("settings.ini","r")
        i_fl_val = {"width":"swidth","height":"sheight","scale2x":"filter",
                "fullscreen":"fullscreen","screens":"num_screens",
                "screen_compress":"screen_compress","autosave":"autosave",
                "autosave_keep":"autosave_keep", 
                "sound_format":"sound_format","sound_bits":"sound_bits",
                "sound_buffer":"sound_buffer","show_fps":"show_fps",
                "smoothscale":"smoothscale"}
        fl_val = {"sound_volume":"sound_volume","music_volume":"music_volume"
                }
        s_val = {"tool_path":"tool_path"}

        for line in f.readlines():
            spl = line.split("=")
            if len(spl)!=2: continue
            if spl[0] in i_fl_val:
                setattr(assets,i_fl_val[spl[0]],int(float(spl[1])))
            elif spl[0] in fl_val:
                setattr(assets,fl_val[spl[0]],float(spl[1]))
            elif spl[0] in s_val:
                setattr(assets,s_val[spl[0]],spl[1].strip())

def get_screen_mode(assets):
    mode="two_screens"
    if assets.num_screens == 1:
        mode = "squished"
        if assets.screen_compress:
            mode = "show_one"
    return mode
def get_screen_dim(assets,mode,aspect=True):
    raspect = assets.swidth/float(assets.sheight)
    if mode == "two_screens":
        aspect = float(assets.sw)/(float(assets.sh)*2)
        top_pos = [0,0]
        top_size = [1,0.5]
        bottom_pos = [0,0.5]
        bottom_size = [1,0.5]
        if aspect:
            top_size[0]*=min(aspect/raspect,1)
            bottom_size[0]=top_size[0]
            top_pos[0]=(1-top_size[0])/2.0
            bottom_pos[0]=(1-bottom_size[0])/2.0
    if mode == "horizontal":
        top_pos = [0,0]
        top_size = [0.5,0.75]
        bottom_pos = [0.5,0.25]
        bottom_size = [0.5,0.75]
    if mode == "squished":
        top_pos = [0,0]
        top_size = [1,1]
        bottom_pos = None
    if mode == "show_one":
        if assets.cur_screen == 0:
            top_pos = [0,0]
            top_size = [1,1]
            bottom_pos = None
        else:
            top_pos = None
            bottom_pos = [0,0]
            bottom_size = [1,1]
    d = {"top":None,"bottom":None}
    if top_pos:
        top_pos_t = [top_pos[0]*assets.swidth,top_pos[1]*assets.sheight]
        top_size_t = [top_size[0]*assets.swidth,top_size[1]*assets.sheight]
        d["top"] = [top_pos,top_size,top_pos_t,top_size_t]
    if bottom_pos:
        bottom_pos_t = [bottom_pos[0]*assets.swidth,bottom_pos[1]*assets.sheight]
        bottom_size_t = [bottom_size[0]*assets.swidth,bottom_size[1]*assets.sheight]
        d["bottom"] = [bottom_pos,bottom_size,bottom_pos_t,bottom_size_t]
    return d
def screen_format(assets):
    mode = get_screen_mode(assets)
    dim = get_screen_dim(assets,mode)
    return mode,dim

class settings_menu(gui.pane):
    firstpane = "display"
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
        if self.firstpane == "debug" and not assets.vtrue("_debug"):
            settings_menu.firstpane = "display"
        self.reses = []
            
        self.sheight = assets.sheight
        self.swidth = assets.swidth
        getattr(self,self.firstpane)()
    def make_button(self,text,pos):
        b = gui.button(self,text,pos)
        if settings_menu.firstpane == text:
            b.bgcolor = [50,50,50]
            b.highlightcolor = [50,50,50]
            b.textcolor = [255,255,255]
            print "changed settings for",text
        self.children.append(b)
        return b
    def base(self):
        assets = self.assets
        sw,sh = self.sw,self.sh
        sh = assets.sh*assets.num_screens
        self.children[:] = []
        self.make_button("close",[225,0])
        self.make_button("quit game",[0,sh-17])
        self.make_button("reset game",[74,sh-17])
        self.make_button("quit pywright",[sw-74,sh-17])
        self.make_button("saves",[0,0])
        self.make_button("display",[35,0])
        self.make_button("sound",[94,0])
        if assets.vtrue("_debug"):
            self.make_button("debug",[132,0])
    def debug(self):
        assets = self.assets
        sw,sh = self.sw,self.sh
        settings_menu.firstpane = "debug"
        self.base()
        line = gui.pane([0,30],[sw,20])
        line.align = "horiz"
        self.children.append(line)
        self.go_script = ""
        line.children.append(gui.editbox(self,"go_script"))
        class myb(gui.button):
            def click_down_over(s,*args):
                assets.cur_script.safe_exec(assets.cur_script.execute_line,self.go_script)
                self.close()
        line.children.append(myb(None,"execute"))
        
        line = gui.pane([0,50],[sw,20])
        line.align = "horiz"
        self.children.append(line)
        class myb(gui.button):
            def click_down_over(s,*args):
                print "debugging game"
                s = assets.DebugScript()
                s.debug_game("current","run")
                print "finished"
        line.children.append(myb(None,"Debug current script"))
        
        line = gui.pane([0,70],[sw,20])
        line.align = "horiz"
        self.children.append(line)
        class myb(gui.button):
            def click_down_over(s,*args):
                print "debugging game"
                s = assets.DebugScript()
                s.debug_game("all","run")
                print "finished"
        line.children.append(myb(None,"Debug entire game (slow)"))
        
        line = gui.pane([0,90],[sw,20])
        line.align = "horiz"
        self.children.append(line)
        class myb(gui.button):
            def click_down_over(s,*args):
                print "debugging game"
                s = assets.DebugScript()
                s.debug_game("all","quote")
                print "finished"
        line.children.append(myb(None,"Find quote errors"))
    def saves(self):
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
        
        line = gui.pane([0,90],[sw,20])
        line.align = "horiz"
        self.children.append(line)
        if not assets.variables.get("_allow_saveload","true"):
            line.children.append(gui.label("Save/Load currently disabled by game"))
        else:
            line.children.append(gui.label("Save/Load"))
            line.children.append(gui.button(self,"save_game"))
            line.children.append(gui.button(self,"load_game"))
        
        #Create debug mode option if we aren't running a game
        if assets.game == "games":
            line = gui.pane([0,90],[sw,20])
            line.align = "horiz"
            self.children.append(line)
            line.children.append(gui.label("Debug mode?"))
            class myb(gui.checkbox):
                def click_down_over(self,*args):
                    super(myb,self).click_down_over(*args)
                    if self.checked:
                        assets.debug_mode = True
                    else:
                        assets.debug_mode = False
            line.children.append(myb("debug_mode"))
            cb = line.children[-1]
            if assets.debug_mode: cb.checked = True
    def load_game(self):
        self.assets.load_game_menu()
        self.delete()
    def save_game(self):
        self.assets.save_game()
        self.delete()
    def sound(self):
        assets = self.assets
        sw,sh = self.sw,self.sh
        settings_menu.firstpane = "sound"
        self.base()
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
                    wini(assets)
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
                    wini(assets)
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
                    wini(assets)
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
                    wini(assets)
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
    def display(self):
        assets = self.assets
        sw,sh = self.sw,self.sh
        settings_menu.firstpane = "display"
        self.base()
        res_box = gui.scrollpane([10,20])
        res_box.width = 200
        res_box.height = 120
        self.res_box = res_box
        self.children.append(res_box)
        
        res_box.add_child(gui.button(self,"Change resolution (%sx%s)"%(assets.swidth,assets.sheight)))
        res = res_box.pane.children[-1]

        res.checked = True
        res.click_down_over = self.popup_resolution
        
        res_box.add_child(gui.checkbox("smoothscale"))
        self.smoothscale = res_box.pane.children[-1]
        
        res_box.add_child(gui.checkbox("fullscreen"))
        self.fs = res_box.pane.children[-1]
        res_box.add_child(gui.checkbox("dualscreen"))
        ds = self.ds = res_box.pane.children[-1]
        
        res_box.add_child(gui.checkbox("virtual dualscreen"))
        self.vds = res_box.pane.children[-1]
        self.vds.visible = 0
        
        res_box.add_child(gui.checkbox("show fps"))
        self.show_fps = res_box.pane.children[-1]
        s_c = self.show_fps.set_checked
        def set_checked(val):
            s_c(val)
            assets.show_fps = val
            wini(assets)
        self.show_fps.set_checked = set_checked

        #self.reses = gui.radiobutton.groups["resopt"]
        if assets.fullscreen:
            self.fs.checked = True
        if assets.num_screens==2:
            self.ds.checked = True
        if not assets.screen_compress:
            self.vds.checked = True
        if assets.show_fps:
            self.show_fps.checked = True
        if assets.smoothscale:
            self.smoothscale.checked = True
                
        self.children.append(gui.button(self,"apply",[10,140]))
    def popup_resolution(self,mp):
        assets = self.assets
        sw,sh = self.sw,self.sh
        self.res_box.pane.children[:] = []
        h = 192
        if get_screen_mode(assets)=="two_screens":
            h*=2
        h2 = h*2
        self.res_box.add_child(gui.radiobutton("(%sx%s)"%(assets.swidth,assets.sheight),"resopt"))
        self.res_box.pane.children[-1].checked = True
        self.res_box.add_child(gui.radiobutton("DS Res (256x%s)"%h,"resopt"))
        self.res_box.add_child(gui.radiobutton("Double scale (512x%s)"%h2,"resopt"))
        for mode in sorted(pygame.display.list_modes()):
            self.res_box.add_child(gui.radiobutton("(%sx%s)"%mode,"resopt"))
        self.reses = gui.radiobutton.groups["resopt"]
        for r in self.reses:
            if str(assets.swidth)+"x" in r.text and "x"+str(assets.sheight) in r.text:
                r.checked = True
        self.res_box.updatescroll()
    def setdl(self,v):
        self.dislis.checked = 1-self.dislis.checked
        pygame.DISPLAY_LIST = self.dislis.checked
        wini(assets)
    def apply(self):
        assets = self.assets
        sw,sh = self.sw,self.sh
        for r in self.reses: 
            if r.checked:
                self.oldwidth,self.oldheight = assets.swidth,assets.sheight
                self.timer = 5.0
                self.really_applyb = gui.pane()
                self.really_applyb.is_applyb = True
                self.really_applyb.width = 1000
                self.really_applyb.height = 1000
                self.really_applyb.pri = -1002
                self.really_applyb.z = 11002
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
        assets.screen_compress = 1
        if self.vds.checked:
            assets.screen_compress = 0
        assets.smoothscale = 0
        if self.smoothscale.checked:
            assets.smoothscale = 1
        assets.make_screen()
        self.display()
        wini(assets)
    def save_resolution(self):
        assets = self.assets
        sw,sh = self.sw,self.sh
        for o in assets.cur_script.obs:
            if hasattr(o,"is_applyb"):
                assets.cur_script.world.remove(o)
        self.really_applyb = None
        self.timer = 0
        wini(assets)
        self.display()
    def reset_res(self):
        assets = self.assets
        assets.swidth,assets.sheight = self.oldwidth,self.oldheight
        assets.fullscreen = self.old_fullscreen
        assets.num_screens = self.old_num_screens
        assets.make_screen()
    def update(self,*args):
        assets = self.assets
        self.rpos = [0,0]
        self.pos = self.rpos
        if getattr(self,"timer",0)>0:
            self.timer -= .02
            self.really_applyb.timer.text = "Resetting view in: %.02f seconds"%self.timer
        else:
            if getattr(self,"really_applyb",None):
                assets.cur_script.world.remove(self.really_applyb)
                self.really_applyb = None
                self.reset_res()
        for x in self.children:
            x.update()
        return True
    def quit_game(self):
        self.assets.quit_game()
    def reset_game(self):
        self.assets.reset_game()
    def quit_pywright(self):
        sys.exit()
    def close(self):
        self.delete()
    def k_space(self):
        self.close()
    def delete(self):
        self.kill = 1
