
from errors import script_error



import pickle
import zlib
import os,sys
sys.path.append("core/include")
sys.path.append("include")
if sys.platform=="win32":
    os.environ['SDL_VIDEODRIVER']='windib'
import random
from core import *
import gui
import save
from pwvlib import *
import settings
import tools_menu

try:
    import android
except:
    android = None

d = get_data_from_folder(".")
__version__ = d["version"]
VERSION = "Version "+cver_s(d["version"])
clock = pygame.time.Clock()

#FIXME - these are temporary until moved
from engine import script,screen,debug_script
Script = script.Script
assets.Script = Script
assets.clock = clock
assets.DebugScript = debug_script.DebugScript
        
class choose_game(gui.widget):
    id_name = "_choose_game_"
    def __init__(self,*args,**kwargs):
        gui.widget.__init__(self,*args,**kwargs)
        self.rpos[1] = other_screen(0)
        self.width,self.height = [1000,1000]
        self.z = 1000
        self.pri = -1000
        
        self.list = gui.scrollpane([0,10])
        self.list.width,self.list.height = [assets.sw,assets.sh-10]
        self.add_child(self.list)
        self.jump_when_close = None
        self.sort = "played"
    def update(self,*args):
        self.rpos[1] = other_screen(0)
        [x.update() for x in self.children]
        self.list.updatescroll()
        return False
    def delete(self):
        self.kill = 1
    def close(self):
        self.delete()
        if self.jump_when_close:
            assets.cur_script.goto_result("close")
    def k_space(self):
        self.close()
    def close_button(self,jump=False):
        self.has_close = True
        self.cb = ws_button(self,"close")
        self.cb.rpos[0]=224
        self.cb.z = 1005
        self.cb.pri = -1005
        self.children.append(self.cb)
        self.jump_when_close = jump
        self.list.scbar_y=self.cb.height-7
        self.list.scbar_height=-self.cb.height

        self.sort_played_btn = ws_button(self,"played")
        self.sort_played_btn.rpos[0]=2
        self.sort_played_btn.z = 1005
        self.sort_played_btn.pri = -1005
        self.children.append(self.sort_played_btn)

        self.sort_az_btn = ws_button(self,"A to Z")
        self.sort_az_btn.rpos[0]=40
        self.sort_az_btn.z = 1005
        self.sort_az_btn.pri = -1005
        self.children.append(self.sort_az_btn)
    def A_to_Z(self,*args):
        self.sort = "az"
        self.list.children[1].children[:] = []
        self.list_games(self.path)
    def played(self,*args):
        self.sort = "played"
        self.list.children[1].children[:] = []
        self.list_games(self.path)
    def list_games(self,path):
        self.path = path
        games = []
        for f in os.listdir(path):
            if f.startswith("."): continue
            if f in ["art","music","sfx","fonts"]:
                continue
            if not os.path.isdir(path+"/"+f) and not ".zip" in path+"/"+f:
                continue
            games.append(f)
        try:
            f = open("lastgame")
            assets.played = eval(f.read())
            f.close()
        except:
            assets.played = []
        games.sort(key=lambda x: x.lower())
        if self.sort == "played":
            for i in reversed(assets.played):
                if i in games:
                    games.remove(i)
                    games.insert(0,i)
        for f in games:
            item = ws_button(self,f)
            d = get_data_from_folder(self.path+"/"+f)
            graphic = pygame.Surface([1,1])
            if d.get("icon",""):
                try:
                    graphic = pygame.image.load(self.path+"/"+f+"/"+d["icon"])
                except:
                    pass
            title = d.get("title",f)
            if d.get("author",""):
                title += " by "+d["author"]
            lines = [l.text() for l in textutil.wrap_text([title],assets.get_image_font("nt"),190)]
            req = d.get("min_pywright_version","0")
            reqs = cver_s(req)
            if __version__ < req:
                lines.append("Requires PyWright "+reqs)
            height = graphic.get_height()
            width = 200
            times_played = assets.played.count(f)
            if times_played:
                lines.append("played: %s"%times_played)
            for i in range(len(lines)):
                txt = assets.get_font("nt").render(lines[i],1,[0,0,0])
                lines[i] = txt
                w,h = txt.get_size()
                height += h
            image = pygame.Surface([width+2,height+2])
            image.fill([0,0,0])
            pygame.draw.rect(image,gui.defcol["gamebg"],[[1,1],[width,height]])
            image.blit(graphic,[0,0])
            y = graphic.get_height()
            for txt in lines:
                image.blit(txt,[2,y])
                y+=txt.get_height()
            item.graphic = image
            self.list.add_child(item)
            def _play_game(func=f):
                assets.played.insert(0,func)
                sf = open("lastgame","w")
                sf.write(repr(assets.played))
                sf.close()
                gamedir = self.path+"/"+func
                assets.start_game(gamedir)
            if __version__ >= req:
                setattr(self,f.replace(" ","_"),_play_game)
            else:
                setattr(self,f.replace(" ","_"),lambda: 1)
#FIXME: out of place
assets.choose_game = choose_game
        
def load_game_menu():
    if [1 for o in assets.cur_script.obs if isinstance(o,choose_game)]:
        return
    root = choose_game()
    root.pri = -1000
    root.z = 5000
    root.width,root.height = [assets.sw,assets.sh]
    list = gui.scrollpane([0,0])
    list.width,list.height = [assets.sw,assets.sh]
    root.add_child(list)
    title = gui.editbox(None,"Choose save to load")
    title.draw_back = False
    list.add_child(title)
    list.add_child(ws_button(root,"cancel",pos=[200,0]))
    cb = list.children[-1]
    def cancel(*args):
        print "canceling"
        root.delete()
    setattr(root,"cancel",cancel)
    cb.bgcolor = [0, 0, 0]
    cb.textcolor = [255,255,255]
    cb.highlightcolor = [50,75,50]
    assets.cur_script.obs.append(root)
    saves = []
    for p in os.listdir(assets.game+"/"):
        if not p.endswith(".ns"):
            continue
        fp = assets.game+"/"+p
        if os.path.exists(fp):
            saves.append((fp,os.path.getmtime(fp)))
    if os.path.isdir(assets.game+"/save_backup"):
        for f in os.listdir(assets.game+"/save_backup"):
            p = f
            fp = assets.game+"/save_backup/"+p
            saves.append((fp,float(fp.rsplit("_",1)[1])))
    saves.sort(key=lambda a: -a[1])
    i = len(saves)
    for s in saves:
        lt = time.localtime(s[1])
        fn = s[0].rsplit("/",1)[1].split(".",1)[0]
        t = str(i)+") "+fn+" %s/%s/%s %s:%s"%(lt.tm_mon,lt.tm_mday,lt.tm_year,lt.tm_hour,lt.tm_min)
        i -= 1
        item = ws_button(root,t)
        list.add_child(item)
        filename=s[0].replace(assets.game,"")[1:]
        fullpath=s[0]
        def do_load(filename=filename,fullpath=fullpath):
            root.delete()
            print "loading",filename,fullpath
            assets.clear()
            assets.show_load()
            assets.load_game_from_string(open(fullpath).read())
        setattr(root,t.replace(" ","_"),do_load)
assets.load_game_menu = load_game_menu
        
def make_start_script(logo=True):
    assets.init()
    assets.game = "games"
    bottomscript = assets.Script()
    introlines = []
    scenename = "local://builtin"
    assets.dt = 1
    assets.variables["_allow_saveload"] = "false"
    bottomscript.init(scriptlines=['print test','textblock 0 0 256 192 Loading menu...','gui Wait'])
    bottomscript.scene = scenename
    assets.stack = [bottomscript]
    assets.cur_script.update()
    assets.cur_script.draw(pygame.screen)
    assets.draw_screen(False)
    try:
        import urllib2
        online_script = urllib2.urlopen("http://pywright.dawnsoft.org/updates3/stream/intro_0977.txt",timeout=2)
        introlines = online_script.read().split("\n")
        online_script.close()
        scenename = "web://intro_0977.txt"
    except:
        import traceback
        traceback.print_exc()
    bottomscript = assets.Script()
    bottomscript.init(scriptlines=["fg ../general/logosmall y=-15 x=-35 name=logo",
                                            "zoom mag=-0.25 frames=30 nowait"] + introlines + ["gui Wait"])
    bottomscript.scene = scenename
    assets.stack = [bottomscript]  #So that the root object gets tagged as in bottomscript

    def run_updater(*args):
        import libupdate
        reload(libupdate)
        assets.cur_script.world.all.append(libupdate.run(pygame.screen))
        #assets.make_start_script()
    setattr(make_start_script,"UPDATES",run_updater)
    item = ws_button(make_start_script,"UPDATES")
    item.bordercolor = [255,255,255]
    item.rpos = [190,10]
    item.z = 999
    item.pri = -1001
    bottomscript.obs.append(item)
    
    def pl(*args):
        [x.delete() for x in bottomscript.obs if isinstance(x,choose_game)]
        cg = choose_game()
        cg.list_games("games")
        cg.close_button()
        bottomscript.obs.append(cg)
    setattr(make_start_script,"GAMES",pl)
    item = ws_button(make_start_script,"GAMES")
    item.bordercolor = [255,255,255]
    item.rpos = [190,30]
    item.z = 999
    item.pri = -1001
    bottomscript.obs.append(item)
    
    def pl(*args):
        gamedir = "examples"
        assets.start_game(gamedir)
        #~ [x.delete() for x in bottomscript.obs if isinstance(x,choose_game)]
        #~ cg = choose_game()
        #~ cg.list_games("examples")
        #~ cg.close_button()
        #~ bottomscript.obs.append(cg)
    setattr(make_start_script,"EXAMPLES",pl)
    item = ws_button(make_start_script,"EXAMPLES")
    item.bordercolor = [255,255,255]
    item.rpos = [190,50]
    item.z = 999
    item.pri = -1001
    bottomscript.obs.append(item)
    
    def pl(*args):
        [x.close() for x in assets.cur_script.obs if isinstance(x,settings.settings_menu)]
        assets.cur_script.obs.append(settings.settings_menu(sw=assets.sw,sh=assets.sh,assets=assets))
    setattr(make_start_script,"SETTINGS",pl)
    item = ws_button(make_start_script,"SETTINGS")
    item.bordercolor = [255,255,255]
    item.rpos = [190,70]
    item.z = 999
    item.pri = -1001
    bottomscript.obs.append(item)
    
    if not android:
        def pl(*args):
            [x.close() for x in assets.cur_script.obs if isinstance(x,tools_menu.tools_menu)]
            assets.cur_script.obs.append(tools_menu.tools_menu(sw=assets.sw,sh=assets.sh,assets=assets))
        setattr(make_start_script,"TOOLS",pl)
        item = ws_button(make_start_script,"TOOLS")
        item.bordercolor = [255,255,255]
        item.rpos = [190,90]
        item.z = 999
        item.pri = -1001
        if os.path.isdir("tools"):
            bottomscript.obs.append(item)

assets.make_start_script = make_start_script
            
assets.make_screen = screen.make_screen
assets.draw_screen = screen.draw_screen

def run(checkupdate=False):
    import sys,os

    if "--help" in sys.argv or "-h" in sys.argv or "-?" in sys.argv or "/?" in sys.argv:
        print "%s -run 'path/to/game'  :  run a game directly"%(sys.argv[0],)
        print "%s -text : text mode, no graphics created, must use -run"%(sys.argv[0],)
        sys.exit()
    
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
    pygame.display.init()
    settings.load(assets)

    game = "menu"
    scene = "intro"
    if sys.argv[1:] and sys.argv[2:]:
        game = sys.argv[1]
        scene = sys.argv[2]
    assets.game = game
    assets.items = []

    running = True

    text_only = False
    if "-text" in sys.argv:
        text_only = True
        assets.Script = debug_script.TextScript
        os.environ["SDL_VIDEODRIVER"] = "dummy"

    assets.make_screen()
    assets.make_start_script()

    if "-run" in sys.argv:
        def ms(*args):
            print "make_start_script to exit"
            sys.exit()
        assets.make_start_script = ms
        assets.stack = []
        assets.start_game(sys.argv[sys.argv.index("-run")+1])

    import time
    lt = time.time()
    ticks = 0
    fr = 0
    #~ import time
    #~ end = time.time()+5
    #~ while time.time()<end:
        #~ pass
    #~ sys.exit()
    laststack = []
    if android:
        android.map_key(android.KEYCODE_MENU, pygame.K_ESCAPE)
        android.map_key(android.KEYCODE_BACK, pygame.K_SPACE)
    def androidpause():
        if android:
            if android.check_pause():
                assets.save_game("android_pause",True)
                android.wait_for_resume()
    assets.next_screen = assets.screen_refresh
    while running:
        androidpause()
        #~ ticks = time.time()-lt
        #~ lt = time.time()
        #~ while ticks<(1/(float(assets.variables.get("_framerate",60))+20.0)):
            #~ if ticks: time.sleep(0.02)
            #~ ticks += time.time()-lt
            #~ lt = time.time()
        #~ dt = ticks*1000.0
        assets.dt = clock.tick(getattr(assets,"framerate",60))
        assets.dt = min(assets.dt*.001*60,10.0)*assets.game_speed
        pygame.display.set_caption("PyWright "+VERSION)
        assets.cur_script.update()
        script.interpret_scripts()
                
        #~ if vtrue(assets.variables.get("_debug","false")):
            #~ ns = assets.get_stack()
            #~ if ns != laststack:
                #~ laststack = ns
                #~ print "^^^^^^^^^^^^^^^^^^^"
                #~ for s in ns:
                    #~ print s
                #~ print "vvvvvvvvvvvvvvvvvvvvvvv"
                #~ print [[x,x.pri] for x in assets.cur_script.obs]
        if not assets.cur_script: break
        assets.next_screen -= assets.dt
        [o.unadd() for o in assets.cur_script.obs if getattr(o,"kill",0) and hasattr(o,"unadd")]
        for o in assets.cur_script.world.all[:]:
            if getattr(o,"kill",0):
                assets.cur_script.world.all.remove(o)
        if assets.next_screen < 0:
            pygame.screen.blit(pygame.blank,[0,0])
            try:
                assets.cur_script.draw(pygame.screen)
            except (art_error,script_error),e:
                import traceback
                traceback.print_exc()
                assets.cur_script.obs.append(error_msg(e.value,assets.cur_script.lastline_value,assets.cur_script.si,assets.cur_script))
            if assets.flash:
                try:
                    fl = flash()
                    assets.cur_script.obs.append(fl)
                    fl.ttl = assets.flash
                    if hasattr(assets,"flashcolor"):
                        fl.color = assets.flashcolor
                except (art_error,script_error),e:
                    import traceback
                    traceback.print_exc()
                    assets.cur_script.obs.append(error_msg(e.value,assets.cur_script.lastline_value,assets.cur_script.si,assets.cur_script))
                assets.flash = 0
                assets.flashcolor = [255,255,255]
            if assets.shakeargs != 0:
                try:
                    assets.cur_script._shake("shake",*assets.shakeargs)
                except (art_error,script_error),e:
                    import traceback
                    traceback.print_exc()
                    assets.cur_script.obs.append(error_msg(e.value,assets.cur_script.lastline_value,assets.cur_script.si,assets.cur_script))
                assets.shakeargs = 0

            if assets.variables.get("render",1):
                assets.draw_screen(assets.show_fps)
            assets.next_screen = assets.screen_refresh
        #pygame.image.save(pygame.real_screen,"capture/img%.04d.jpg"%fr)
        #fr+=1
        pygame.event.pump()
        try:
            assets.music_update()
            assets.cur_script.handle_events(pygame.event.get([pygame.MOUSEMOTION,pygame.MOUSEBUTTONUP,pygame.MOUSEBUTTONDOWN]))
            if "enter" in assets.cur_script.held:
                for o in assets.cur_script.upobs:
                    if hasattr(o,"enter_hold"):
                        o.enter_hold()
            keybinds = {"keydown":{},"keyup":{},"keyhold":{},"joybuttonup":{},"joybuttondown":{},"joyhatmotion":{}}
            keybinds["keydown"][pygame.K_ESCAPE] = "toggle_settings"
            #keybinds["keydown"][pygame.K_m] = "toggle_settings"
            keybinds["keyup"][pygame.K_RETURN] = "enter_up"
            keybinds["joybuttonup"][0] = "enter_up"
            keybinds["keydown"][pygame.K_RETURN] = "enter_down"
            keybinds["joybuttondown"][0] = "enter_down"
            keybinds["keydown"][pygame.K_RIGHT] = "k_right"
            keybinds["joyhatmotion"][(1,0)] = "k_right"
            keybinds["keydown"][pygame.K_LEFT] = "k_left"
            keybinds["keyhold"][pygame.K_LEFT] = "k_hold_left"
            keybinds["joyhatmotion"][(-1,0)] = "k_left"
            keybinds["keydown"][pygame.K_UP] = "k_up"
            keybinds["joyhatmotion"][(0,1)] = "k_up"
            keybinds["keydown"][pygame.K_DOWN] = "k_down"
            keybinds["joyhatmotion"][(0,-1)] = "k_down"
            keybinds["keydown"][pygame.K_SPACE] = "k_cancel"
            keybinds["joybuttondown"][1] = "k_cancel"
            keybinds["keydown"][pygame.K_TAB] = "k_switch"
            keybinds["joybuttondown"][3] = "k_switch"
            keybinds["keydown"][pygame.K_z] = "press"
            keybinds["joybuttondown"][4] = "press"
            keybinds["keydown"][pygame.K_x] = "present"
            keybinds["joybuttondown"][5] = "present"
            for k in keybinds["keydown"]:
                if pygame.key.get_pressed()[k]:
                    evt = keybinds["keydown"][k]+"_hold"
                    for o in assets.cur_script.upobs:
                        if hasattr(o,evt):
                            getattr(o,evt)()
            for e in pygame.event.get():
                if e.type==pygame.ACTIVEEVENT:
                    if e.gain==0 and (e.state==6 or e.state==2 or e.state==4):
                        print "minimize"
                        gw = guiWait(mute=True)
                        gw.pri = -1000
                        gw.minimized = True
                        assets.cur_script.obs.append(gw)
                    if e.gain==1 and (e.state==6 or e.state==2 or e.state==4):
                        print "maximize"
                        for ob in assets.cur_script.obs:
                            if hasattr(ob,"minimized"):
                                ob.delete()
                if e.type==pygame.VIDEORESIZE:
                    w,h = e.w,e.h
                    assets.swidth = w
                    assets.sheight = h
                    assets.make_screen()
                    settings.wini(assets)
                if e.type == pygame.QUIT:
                    running = False
                if e.type==pygame.KEYDOWN and\
                e.key==pygame.K_RETURN and pygame.key.get_mods() & pygame.KMOD_ALT:
                    assets.fullscreen = 1-assets.fullscreen
                    assets.make_screen()
                    settings.wini(assets)

                def toggle_settings():
                    ss = [x for x in assets.cur_script.obs if isinstance(x,settings.settings_menu)]
                    if ss:
                        ss[0].close()
                    else:
                        assets.cur_script.obs.append(settings.settings_menu(sw=assets.sw,sh=assets.sh,assets=assets))
                def enter_up():
                    if "enter" in assets.cur_script.held: assets.cur_script.held.remove("enter")
                    for o in assets.cur_script.upobs:
                        if hasattr(o,"enter_up"):
                            o.enter_up()
                            break
                def enter_down():
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
                def k_right():
                    for o in assets.cur_script.upobs:
                        if hasattr(o,"statement") and not o.statement:
                            continue
                        if hasattr(o,"k_right") and not getattr(o,"kill",0) and not getattr(o,"hidden",0):
                            o.k_right()
                            break
                def k_left():
                    for o in assets.cur_script.upobs:
                        if hasattr(o,"statement") and not o.statement:
                            continue
                        if hasattr(o,"k_left") and not getattr(o,"kill",0) and not getattr(o,"hidden",0):
                            o.k_left()
                            break
                def k_up():
                    for o in assets.cur_script.upobs:
                        if hasattr(o,"k_up") and not getattr(o,"kill",0) and not getattr(o,"hidden",0):
                            o.k_up()
                            break
                def k_down():
                    for o in assets.cur_script.upobs:
                        if hasattr(o,"k_down") and not getattr(o,"kill",0) and not getattr(o,"hidden",0):
                            o.k_down()
                            break
                def k_cancel():
                    for o in assets.cur_script.upobs:
                        if hasattr(o,"k_space") and not getattr(o,"kill",0) and not getattr(o,"hidden",0):
                            o.k_space()
                            return
                    game = assets.game
                    assets.cur_script.quit()
                    if game == 'games':
                        sys.exit()
                def k_switch():
                    for o in assets.cur_script.upobs:
                        if hasattr(o,"k_tab") and not getattr(o,"kill",0) and not getattr(o,"hidden",0):
                            print "tab on",o
                            o.k_tab()
                            break
                def press():
                    for o in assets.cur_script.upobs:
                        if hasattr(o,"k_z") and not getattr(o,"kill",0) and not getattr(o,"hidden",0):
                            o.k_z()
                            break
                def present():
                    for o in assets.cur_script.upobs:
                        if hasattr(o,"k_x") and not getattr(o,"kill",0) and not getattr(o,"hidden",0):
                            o.k_x()
                            break
                if e.type==pygame.KEYDOWN:
                    if e.key in keybinds["keydown"]:
                        eval(keybinds["keydown"][e.key])()
                elif e.type==pygame.KEYUP:
                    if e.key in keybinds["keyup"]:
                        eval(keybinds["keyup"][e.key])()
                elif e.type==pygame.JOYBUTTONUP:
                    if e.button in keybinds["joybuttonup"]:
                        eval(keybinds["joybuttonup"][e.button])()
                elif e.type==pygame.KEYDOWN:
                    if e.key in keybinds["keydown"]:
                        eval(keybinds["keydown"][e.key])()
                elif e.type==pygame.JOYBUTTONDOWN:
                    if e.button in keybinds["joybuttondown"]:
                        eval(keybinds["joybuttondown"][e.button])()
                elif e.type==pygame.JOYHATMOTION:
                    if e.value in keybinds["joyhatmotion"]:
                        eval(keybinds["joyhatmotion"][e.value])()
                if e.type==pygame.KEYDOWN and e.key==pygame.K_d and e.mod&pygame.K_LCTRL:
                    assets.variables["_debug"] = "true"
                if e.type==pygame.KEYDOWN and\
                e.key==pygame.K_F5 and assets.game!="menu":
                    assets.save_game()
                if e.type==pygame.KEYDOWN and\
                e.key == pygame.K_F7 and assets.game!="menu":
                    load_game_menu()
                    #assets.load_game(assets.game)
                if e.type==pygame.KEYDOWN and e.key == pygame.K_F3 and vtrue(assets.variables.get("_debug","false")):
                    assets.cur_script.obs.append(script_code(assets.cur_script))
                if e.type==pygame.KEYDOWN and e.key == pygame.K_F4:
                    assets.cur_screen = 1-assets.cur_screen
                assets.cur_script.handle_events([e])
            #~ if pygame.js1:
                #~ print pygame.js1.get_button(0)
        except (art_error,script_error,markup_error), e:
            assets.cur_script.obs.append(error_msg(e.value,assets.cur_script.lastline_value,assets.cur_script.si,assets.cur_script))
            import traceback
            traceback.print_exc()
    if hasattr(assets, "threads"):
        while [1 for thread in assets.threads if thread and thread.isAlive()]:
            print "waiting"
            pass
if __name__=="__main__":
    run()
