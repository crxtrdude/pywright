from errors import *
import sys
sys.path.append("core/include")
sys.path.append("include")
import time
import gui
import os
import pygame
pygame.font.init()
import random
import pickle
import re
import textutil
import registry
import zipfile
import simplejson as json
ImgFont = textutil.ImgFont
try:
    import pygame.movie as pymovie
except:
    pymovie = None
try:
    import audiere
    aud = audiere.open_device()
except:
    audiere = None
try:
    import android
except:
    android = None
if android:
    import android.mixer as mixer
else:
    import pygame.mixer as mixer
    
from pwvlib import *

d = get_data_from_folder(".")
__version__ = cver_s(d["version"])
VERSION = "Version "+cver_s(d["version"])

try:
    import numpy
    pygame.sndarray.use_arraytype("numpy")
    pygame.use_numpy = True
except:
    numpy = None
    pygame.use_numpy = False
sw,sh = 256,192
#sw,sh = 640,480
spd = 6

ext_map = {"image":["png","jpg"],
"script":["txt"],
"music":["wav","mid","mod","ogg","s3m","it","xm"],
"sound":["wav","ogg"],
"movie":["mpeg","mpg"]}
def ext_for(types=["image","script","music","sound"]):
    for et in types:
        for e in ext_map[et]:
            yield "."+e
def noext(p,types=["image","script","music","sound"]):
    """Path without the extension, if extension is in known types"""
    for ext in ext_for(types):
        if p.endswith(ext):
            return p.rsplit(".",1)[0]
    return p
def onlyext(p,types=["image","script","music","sound"]):
    """Returns the extension of the path"""
    for ext in ext_for(types):
        if p.endswith(ext):
            return ext
    return ""
assert noext("something.png",["image"])=="something"
assert noext("something.png",["music"])=="something.png"
assert onlyext("something.png")==".png"

def to_triplets(li):
    new = []
    now = []
    for x in li:
        now.append(x)
        if len(now)==3:
            new.append(now)
            now = []
    return new

def other_screen(y):
    return y+(assets.num_screens-1)*sh

class meta:
    def __init__(self):
        self.horizontal = 1
        self.vertical = 1
        self.length = 1
        self.loops = False
        self.sounds = {}
        self.split = None
        self.framecompress = [0,0]
        self.blinkmode = "blinknoset"
        self.offsetx = 0
        self.offsety = 0
        self.blipsound = None
        self.frameoffset = {}
        self.delays = {}
        self.speed = 6
        self.blinkspeed = [100,200]
    def load_from(self,f):
        text = f.read()
        text = text.decode("utf8","ignore")
        text = text.replace(u'\ufeff',u'')
        lines = text.replace("\r\n","\n").split("\n")
        setlength = False
        for l in lines:
            spl = l.split(" ")
            if l.startswith("horizontal "): self.horizontal = int(spl[1])
            if l.startswith("vertical "): self.vertical = int(spl[1])
            if l.startswith("length "):
                self.length = int(spl[1])
                setlength = True
            if l.startswith("loops "): self.loops = int(spl[1])
            if l.startswith("sfx "):
                self.sounds[int(spl[1])] = " ".join(spl[2:])
            if l.startswith("offsetx "): self.offsetx = int(spl[1])
            if l.startswith("offsety "): self.offsety = int(spl[1])
            if l.startswith("framecompress "):
                fc = l.replace("framecompress ","").split(",")
                if len(fc)==1:
                    self.framecompress = [0,int(fc[0])]
                else:
                    self.framecompress = [int(x) for x in fc]
            if l.startswith("blinksplit "):
                self.split = int(l.replace("blinksplit ",""))
            if l.startswith("blinkmode "):
                self.blinkmode = l.replace("blinkmode ","")
            if l.startswith("blipsound "):
                self.blipsound = l.replace("blipsound ","").strip()
            if l.startswith("framedelay "):
                frame,delay = l.split(" ")[1:]
                self.delays[int(frame)] = int(delay)
            if l.startswith("globaldelay "):
                self.speed = float(l.split(" ",1)[1])
            if l.startswith("blinkspeed "):
                self.blinkspeed = [int(x) for x in l.split(" ")[1:]]
        f.close()
        if not setlength:
            if self.vertical==1:
                self.length = self.horizontal
            else:
                self.length = self.horizontal*self.vertical
        return self
        
class layer(dict):
    def index(self,ob):
        for i in self.keys():
            if ob in self[i]:
                return i
zlayers = layer()
zi = 0
ulayers = layer()
ui = 0
sort = open("core/sorting.txt")
sortmode = None
for line in sort.readlines():
    line = line.strip().split("#")[0].replace("\t"," ")
    if line=="[z]":
        sortmode = "z"
    elif line=="[pri]":
        sortmode = "pri"
    elif line:
        x = line.split(" ")
        level = int(x[0])
        del x[0]
        while not x[0]: del x[0]
        if sortmode == "z":
            zlayers[zi]=x
            zi += 1
        elif sortmode == "pri":
            ulayers[level]=x
        
class Variables(dict):
    def __getitem__(self,key):
        return self.get(key)
    def get(self,key,*args):
        if key.startswith("_layer_"):
            layer = zlayers.index(key[7:])
            if layer is not None:
                return str(layer)
        if key=="_version":
            return __version__
        if key=="_num_screens":
            return str(assets.num_screens)
        if key=="_debug":
            return {True:"on",False:"off"}[assets.debug_mode]
        return dict.get(self,key,*args)
    def __setitem__(self,key,value,*args):
        if key=="_speaking":
            dict.__setitem__(self,key,value,*args)
            try:
                self["_speaking_name"] = assets.gportrait().nametag.split("\n")
            except:
                pass
        if key=="_music_fade":
            dict.__setitem__(self,key,value,*args)
            assets.smus(assets.gmus())
            return
        if key=="_debug":
            return
        return dict.__setitem__(self,key,value,*args)
    def set(self,key,value):
        return self.__setitem__(key,value)

assert Variables().get("_version",None)
        
class ImgFrames(list):
    pass

class Assets(object):
    lists = {}
    snds = {}
    art_cache = {}
    variables = Variables()
    gbamode = False
    num_screens = 2
    screen_refresh = 1
    if android:
        screen_refresh = 3
    sound_format = 44100
    sound_bits = 16
    sound_sign = -1
    sound_buffer = 4096
    sound_init = 0
    sound_volume = 100
    _music_vol = 100
    mute_sound = 0
    sw = sw
    sh = sh
    last_autosave = 0
    autosave_interval = 0
    path = ""
    tool_path = ""
    debug_mode = False
    debugging = "SEARCH"  #debugging mode. SEARCH for stop, STEP each line, or blank
    registry = registry.Registry(".")
    def init(self):
        self.registry = registry.Registry(".")
    def get_stack(self):
        stack = []
        for s in self.stack:
            def gp(s,i):
                si = s.si+i
                if si<0:
                    return "PRE"
                if si>=len(s.scriptlines):
                    return "END"
                if not s.scriptlines:
                    return "NOSCRIPT"
                return s.scriptlines[si]
            p0 = gp(s,-1)
            p1 = gp(s,0)
            p2 = gp(s,1)
            stack.append([p0,p1,p2])
        return stack
    def smus(self,v):
        self._music_vol = v
        try:
            mixer.music.set_volume(v/100.0*(int(assets.variables.get("_music_fade","100"))/100.0))
        except:
            pass
    def gmus(self):
        return self._music_vol
    music_volume = property(gmus,smus)
    def set_mute_sound(self,value):
        self.mute_sound = value
        if android and self.mute_sound:
            self.stop_music()
    def _appendgba(self):
        if not self.gbamode: return ""
        return "_gba"
    appendgba = property(_appendgba)
    def raw_lines(self,name,ext=".txt",start="game",use_unicode=False):
        if start=="game":
            start = self.game
        if start:
            start = start+"/"
        if name.endswith(".txt"):
            ext = ""
        try:
            file = open(start+name+ext,"rU")
        except IOError:
            raise file_error("File named "+start+name+ext+" could not be read. Make sure you spelled it properly and check case.")
        text = file.read()
        if use_unicode:
            text = text.decode("utf8","ignore")
            #Replace the BOM
            text = text.replace(u'\ufeff',u'')
        return text.split("\n")
    def parse_macros(self,lines):
        """Alters lines to not include macro definitions, and returns macros"""
        macros = {}
        mode = "normal"
        i = 0
        while i<len(lines):
            line = lines[i]
            if line.startswith("macro "):
                del lines[i]
                i -= 1
                mode = "macro"
                macroname = line[6:].strip()
                macrolines = []
            elif mode == "macro":
                del lines[i]
                i -= 1
                if line=="endmacro":
                    mode = "normal"
                    macros[macroname] = macrolines
                else:
                    macrolines.append(line)
            i+=1
        return macros
    def replace_macros(self,lines,macros):
        """Applies macros to lines"""
        i = 0
        while i<len(lines):
            line = lines[i]
            if line.startswith("{"):
                del lines[i]
                i -= 1
                args = line[1:-1].split(" ")
                if macros.get(args[0],None):
                    newlines = "\n".join(macros[args[0]])
                    args = args[1:]
                    kwargs = {}
                    for a in args[:]:
                        if a.count("=")==1:
                            args.remove(a)
                            k,v = a.split("=",1)
                            kwargs[k] = v
                    newlines = newlines.replace("$0",str(i))
                    for i2 in range(len(args)):
                        newlines = newlines.replace("$%s"%(i2+1),args[i2])
                    for k in kwargs:
                        newlines = newlines.replace("$%s"%k,kwargs[k])
                    newlines = newlines.split("\n")
                    for l in reversed(newlines):
                        lines.insert(i+1,l)
            i += 1
    def open_script(self,name,macros=True,ext=".txt"):
        lines = self.raw_lines(name,ext,use_unicode=True)
        reallines = []
        block_comment = False
        for line in lines:
            line = line.strip()
            #~ if line.startswith("###"):
                #~ if block_comment:
                    #~ block_comment = False
                #~ else:
                    #~ block_comment = True
                #~ continue
            #~ if block_comment:
                #~ continue
            if macros and line.startswith("include "):
                reallines.extend(self.open_script(line[8:].strip(),False))
            else:
                reallines.append(line)
        lines = reallines
        the_macros = {}
        for f in os.listdir("core/macros"):
            if f.endswith(".mcro"):
                mlines = self.raw_lines("core/macros/"+f,"","",True)
                parse = self.parse_macros(mlines)
                the_macros.update(parse)
        self.game = self.game.replace("\\","/")
        case = self.game
        game = self.game.rsplit("/",1)[0]
        for pth in [game,case]:
            if os.path.exists(pth+"/macros.txt"):
                the_macros.update(self.parse_macros(self.raw_lines("macros.txt","",start=pth,use_unicode=True)))
            for f in os.listdir(pth):
                if f.endswith(".mcro"):
                    the_macros.update(self.parse_macros(self.raw_lines(f,"",start=pth,use_unicode=True)))
        if macros:
            the_macros.update(self.parse_macros(lines))
            self.replace_macros(lines,the_macros)
        self.macros = the_macros
        return lines
    def open_font(self,name,size):
        pth = self.search_locations("fonts",name)
        return pygame.font.Font(pth,size)
    fonts = {}
    deffonts = {}
    for line in """set _font_tb pwinternational.ttf
set _font_update Vera.ttf
set _font_update_size 8
set _font_tb_size 10
set _font_block arial.ttf
set _font_block_size 10
set _font_nt arial.ttf
set _font_nt_size 10
set _font_list pwinternational.ttf
set _font_list_size 10
set _font_itemset pwinternational.ttf
set _font_itemset_size 10
set _font_itemset_big arial.ttf
set _font_itemset_big_size 14
set _font_itemname pwinternational.ttf
set _font_itemname_size 10
set _font_loading arial.ttf
set _font_loading_size 16
set _font_gametitle arial.ttf
set _font_gametitle_size 16
set _font_new_resume arial.ttf
set _font_new_resume_size 14""".split("\n"):
        args = line.split(" ")
        deffonts[args[1]] = args[2]
    def get_font(self,name):
        defs = {}
        defs.update(self.deffonts)
        defs.update(self.variables)
        fn = defs.get("_font_%s"%name,"pwinternational.ttf")
        size = defs.get("_font_%s_size"%name,"10")
        full = fn+"."+size
        if full in self.fonts:
            return self.fonts[full]
        font = self.open_font(fn,int(size))
        self.fonts[full] = font
        return font
    def get_image_font(self,name):
        fn = self.variables.get("_font_%s"%name,"pwinternational.ttf")
        size = self.variables.get("_font_%s_size"%name,"10")
        full = fn+"."+size+".i"
        if full in self.fonts:
            return self.fonts[full]
        font = self.get_font(name)
        imgfont = ImgFont("fonts/p.png",font)
        self.fonts[full] = imgfont
        return imgfont
    def Surface(self,size,flags=0):
        return pygame.Surface(size,flags)
    def search_locations(self,search_path,name):
        self.game = self.game.replace("\\","/")
        case = self.game
        game = self.game.rsplit("/",1)[0]
        
        if os.path.exists(case+"/"+search_path+"/"+name):
            return case+"/"+search_path+"/"+name

        if os.path.exists(game+"/"+search_path+"/"+name):
            return game+"/"+search_path+"/"+name

        if os.path.exists(search_path+"/"+name):
            return search_path+"/"+name
    def _open_art_(self,name,key=None):
        """Returns list of frame images"""
        if self.cur_script and self.cur_script.imgcache.has_key(name):
            img = self.cur_script.imgcache[name]
            self.meta = img._meta
            self.real_path = img.real_path
            return img
        self.meta = meta()
        pre = "art/"
        textpath = self.registry.lookup(pre+name+".txt",True)
        if not textpath:
            textpath = self.registry.lookup(pre+name.rsplit(".",1)[0]+".txt",True)
        print "lookup",pre+name
        artpath = self.registry.lookup((pre+name).replace(".zip/","/"))
        print pre+name+".txt",artpath,textpath
        if textpath:
            try:
                f = self.registry.open(textpath)
                self.meta.load_from(f)
            except:
                import traceback
                traceback.print_exc()
                raise art_error("Art textfile corrupt:"+pre+name[:-4]+".txt")
        print self.registry.open(artpath)
        texture = pygame.image.load(self.registry.open(artpath),artpath)
        if texture.get_flags()&pygame.SRCALPHA:
            texture = texture.convert_alpha()
        else:
            texture = texture.convert()
        if key:
            texture.set_colorkey(key)
        img = []
        x = 0
        y = 0
        width,height = texture.get_size()
        incx = width//self.meta.horizontal
        incy = height//self.meta.vertical
        for frame in range(self.meta.length):
            img.append(texture.subsurface([[x,y],[incx,incy]]))
            x+=incx
            if x>=width:
                x=0
                y+=incy
        img = ImgFrames(img)
        img._meta = self.meta
        img.real_path = self.real_path = artpath
        if self.cur_script:
            self.cur_script.imgcache[name] = img
        return img
    def open_art(self,name,key=None):
        """Try to open an art file.  Name has no extension.
        Will open gif, then png, then jpg.  Returns list of 
        frame images"""
        self.real_path = None
        tries = [name]
        for ext in ext_for(["image"]):
            tries.append(name+ext)
        for t in tries:
            try:
                return self._open_art_(t,key)
            except (IOError,ImportError,pygame.error,TypeError):
                print "there was a typeerror"
                pass
        import traceback
        traceback.print_exc()
        print "raising corrupt or missing art file"
        raise art_error("Art file corrupt or missing:"+name)
    def init_sound(self,reset=False):
        self.sound_repeat_timer = {}
        self.min_sound_time = 0.01
        if android:
            self.min_sound_time = 0.1
        if reset or not self.sound_init:
            self.snds = {}
            try:
                mixer.stop()
                mixer.quit()
            except:
                pass
            try:
                mixer.pre_init(self.sound_format, self.sound_sign*self.sound_bits, 2, self.sound_buffer)
                mixer.init()
                self.sound_init = 1
                self.music_volume = self._music_vol
                return True
            except:
                self.sound_init = -1
        if self.sound_init==1: return True
        return False
    def get_path(self,track,type,pre=""):
        tries = [track]
        #Unknown extension, make sure to check all extension types
        if noext(track)==track:
            for ext in ext_for([type]):
                tries.insert(0,track+ext)
        #Get parent game folder, in case we are in a case folder
        game = self.game.replace("\\","/").rsplit("/",1)[0]
        if pre: pre = "/"+pre+"/"
        else: pre = "/"
        for t in tries:
            if os.path.exists(self.game+pre+t):
                return self.game+pre+t
            if os.path.exists(game+pre+t):
                return game+pre+t
            if os.path.exists(pre[1:]+t):
                return pre[1:]+t
        return pre+track
    def open_music(self,track,pre="music"):
        p = self.get_path(track,"music",pre)
        if not p:
            return False
        try:
            mixer.music.load(p)
            return True
        except:
            import traceback
            traceback.print_exc()
            return False
    def open_movie(self,movie):
        if not pymovie:
            raise script_error("No movie player component in this pywright")
        movie = self.get_path(movie,"movie","movies")
        try:
            mov = pymovie.Movie(movie)
            return mov
        except:
            import traceback
            traceback.print_exc()
            raise art_error("Movie is missing or corrupt:"+movie)
    def list_casedir(self):
        return os.listdir(self.game)
    def play_sound(self,name,wait=False,volume=1.0,offset=0,frequency=1,layer=0):
        #self.init_sound()
        if self.sound_init == -1 or not self.sound_volume or self.mute_sound: return
        if name in self.sound_repeat_timer:
            if time.time()-self.sound_repeat_timer[name]<self.min_sound_time:
                return
        self.sound_repeat_timer[name] = time.time()
        path = self.get_path(name,"sound","sfx")
        if self.snds.get(path,None):
            snd = self.snds[path]
        else:
            try:
                if path.endswith(".mp3") and audiere:
                    snd = aud.open_file(path)
                else:
                    snd = mixer.Sound(path)
            except:
                import traceback
                traceback.print_exc()
                return
            self.snds[path] = snd
        if not layer:
            snd.stop()
        try:
            snd.set_volume(float(self.sound_volume/100.0)*volume)
        except:
            snd.volume = (self.sound_volume/100.0)*volume
        channel = snd.play()
        return channel
    def play_music(self,track=None,loop=0,pre="music",reset_track=True):
        print self.music_volume,self.variables.get("_music_fade",None)
        if reset_track:
            assets.variables["_music_loop"] = track
        self.init_sound()
        if self.sound_init == -1 or self.mute_sound: return
        self._track=track
        self._loop=loop
        if track:
            track = self.open_music(track,pre)
        if track:
            try:
                mixer.music.play()
            except:
                import traceback
                traceback.print_exc()
        else:
            self.stop_music()
    def stop_music(self):
        if self.sound_init == -1: return
        self._track = None
        self._loop = 0
        try:
            mixer.music.stop()
        except:
            pass
    def music_update(self):
        mcb = mixer.music.get_busy
        if android:
            mcb = mixer.music_channel.get_busy
        if getattr(self,"_track",None) and not mcb():
            if assets.variables.get("_music_loop",None):
                self.play_music(assets.variables["_music_loop"],self._loop)
    def pause_sound(self):
        mixer.pause()
        mixer.music.pause()
    def resume_sound(self):
        mixer.unpause()
        mixer.music.unpause()
    def set_emotion(self,e):
        """Sets the emotion of the current portrait"""
        if not self.portrait:
            self.add_portrait(self.character+"/"+e+"(blink)")
        if self.portrait:
            self.portrait.set_emotion(e)
    flash = 0  #Tells main to add a flash object
    flashcolor = [255,255,255]
    shakeargs = 0  #Tell main to add a shake object
    def get_stack_top(self):
        try:
            return self.stack[-1]
        except:
            return None
    cur_script = property(get_stack_top)
    px = 0
    py = 0
    pz = None
    def gportrait(self):
        id_name = self.variables.get("_speaking","")
        if isinstance(id_name,portrait) or not id_name:
            return id_name
        ports = []
        for p in self.cur_script.obs:
            if isinstance(p,portrait) and not getattr(p,"kill",0):
                ports.append(p)
                if getattr(p,"id_name",None)==id_name: return p
        for p in self.cur_script.obs:
            if isinstance(p,portrait) and not getattr(p,"kill",0):
                ports.append(p)
                if getattr(p,"charname",None)==id_name: return p
        if ports: return ports[0]
        return None
    portrait = property(gportrait)
    def add_portrait(self,name,fade=False,stack=False,hide=False):
        if hide: stack = True
        assets = self
        self = self.cur_script
        if not stack: [(lambda o:setattr(o,"kill",1))(o) for o in self.obs if isinstance(o,portrait)]
        assets.variables["_speaking"] = None
        p = portrait(name,hide)
        p.pos[0] += assets.px
        p.pos[1] += assets.py
        if fade:
            p.fade = 0
        if assets.pz is not None:
            p.z = assets.pz
            assets.pz = None
        self.obs.append(p)
        assets.variables["_speaking"] = p.id_name
        if stack: p.was_stacked = True
        return p
    def clear(self):
        if not hasattr(self,"variables"):
            self.variables = Variables()
        self.variables.clear()
        while assets.items:
            assets.items.pop(0)
        assets.stop_music()
        assets.lists = {}
        self.fonts = {}
    def save(self):
        self.last_autosave = time.time()
        props = {}
        for reg in ["character","_track","_loop","lists"]:
            if hasattr(self,reg):
                props[reg] = getattr(self,reg)
        #save items
        items = []
        for x in self.items:
            items.append({"id":x.id,"page":x.page})
        props["items"] = items
        #save variables
        vars = {}
        for x in self.variables:
            v = self.variables[x]
            if x == "_speaking" and hasattr(v,"id_name"):
                vars[x] = v.id_name
            else:
                vars[x] = v
        props["variables"] = vars
        return ["Assets",[],props,None]
    def after_load(self):
        self.registry = registry.combine_registries("./"+self.game,self.show_load)
        self.last_autosave = time.time()
        itemobs = []
        for x in self.items:
            if isinstance(x,dict):
                itemobs.append(evidence(x["id"],page=x["page"]))
            else:
                itemobs.append(evidence(x))
        self.items = itemobs
        v = self.variables
        self.variables = Variables()
        self.variables.update(v)
        if getattr(self,"_track",None):
            self.play_music(self._track,self._loop,reset_track=False)
    def show_load(self):
        self.make_screen()
        txt = "LOADING " + random.choice(["/","\\","-","|"])
        txt = assets.get_font("loading").render(txt,1,[200,100,100])
        pygame.screen.blit(txt,[50,50])
        self.draw_screen(0)
        time.sleep(0.05)
    def load_game_new(self,path=None,filename="save",hide=False):
        if not vtrue(self.variables.get("_allow_saveload","true")):
            return
        if "\\" in filename or "/" in filename:
            raise script_error("Invalid save file path:'%s'"%(filename,))
        if not hide:
            self.show_load()
        if path:
            self.game = path
        try:
            f = open(self.game+"/"+filename+".ns")
        except:
            self.cur_script.obs.append(saved(text="No game to load.",ticks=240))
            return
        save_text = f.read()
        f.close()
        self.load_game_from_string(save_text)
    def convert_save_string_to_ob(self,text):
        def read_oldsave(s):
            return eval(s)
        def read_newsave(s):
            return json.loads(s)
        def read_save(s):
            try:
                return read_newsave(s)
            except:
                return read_oldsave(s)
        return read_save(text)
    def load_game_from_string(self,save_text):
        self.loading_cache = {}
        things = self.convert_save_string_to_ob(save_text)
        assets.clear()
        stack = {}
        loaded = []
        for cls,args,props,dest in things:
            if cls == "Assets":
                ob = self
            else:
                ob = eval(cls)(*args)
            for k in props:
                setattr(ob,k,props[k])
            if dest:
                cont,index = dest
                if cont == "stack":
                    stack[index] = ob
                else:
                    stack[index].obs.append(ob)
            loaded.append(ob)
        keys = stack.keys()
        keys.sort()
        for s in assets.stack[:]:
            d = 1
            for o in s.obs:
                if isinstance(o,case_menu):
                    d = 0
                    break
            if d:
                assets.stack.remove(s)
        for k in keys:
            assets.stack.append(stack[k])
        for ob in loaded:
            ob.after_load()
        self.cur_script.obs.append(saved(text="Game restored",block=False))
        self.cur_script.execute_macro("load_defaults")
        self.cur_script.execute_macro("init_court_record_settings")
    def backup(self,path,save):
        if not os.path.exists(path+"/"+save):
            return
        if not os.path.exists(path+"/save_backup"):
            os.mkdir(path+"/save_backup")
        f = open(path+"/"+save)
        t = f.read()
        f.close()
        f = open(path+"/save_backup/"+save+"_"+repr(os.path.getmtime(path+"/"+save)),"w")
        f.write(t)
        f.close()
        if save!="autosave.ns":
            return
        autosaves = []
        for f in os.listdir(path+"/save_backup"):
            if f.startswith(save):
                autosaves.append((f,float(f.split("_")[1])))
        autosaves.sort(key=lambda s:s[1])
        print len(autosaves)+1,self.autosave_keep
        while len(autosaves)+1>self.autosave_keep:
            p,t = autosaves.pop(0)
            print "delete",p
            os.remove(path+"/save_backup/"+p)
        print "autosaves",autosaves
    def save_game(self,filename="save",hide=False):
        if not vtrue(self.variables.get("_allow_saveload","true")) and not vtrue(self.variables.get("_debug","false")):
            return
        if "\\" in filename or "/" in filename:
            raise script_error("Invalid save file path:'%s'"%(filename,))
        filename = filename.replace("/","_").replace("\\","_")+".ns"
        #Collect *things* to save
        stuff = [self.save()]
        for script in self.stack:
            if script.save_me:
                stuff.append(script.save())
        self.backup(self.game,filename)
        f = open(self.game+"/"+filename,"w")
        f.write(json.dumps(stuff,indent=4))
        f.close()
        if not hide:
            self.cur_script.obs.append(saved(block=False))
    def load_game(self,path=None,filename="save",hide=False):
        self.cur_script.imgcache.clear()
        chkpath=""
        if path is not None:
            chkpath=path+"/"
        if filename == "save":
            filename = self.check_autosave(chkpath)
        self.load_game_new(path,filename,hide)
    def check_autosave(self,path):
        if not os.path.exists(path+"/autosave.ns"):
            return "save"
        if not os.path.exists(path+"/save.ns"):
            return "autosave"
        mt1 = os.path.getmtime(path+"/autosave.ns")
        mt2 = os.path.getmtime(path+"/save.ns")
        if mt1>mt2:
            return 'autosave'
        return "save"
    def vdefault(self,var):
        """Return default value for a variable"""
        if var == "_debug":
            return "off"
        return None
    def v(self,var,default="_NOT GIVEN_"):
        """Return a variable value, or it's default value"""
        if default == "_NOT_GIVEN_":
            default = self.vdefault(var)
        v = self.variables.get(var,default)
        return v
    def vtrue(self,var,default="_NOT_GIVEN_"):
        v = self.v(var,default)
        return vtrue(v)
    def reset_state(self):
        self.variables.clear()
        self.stop_music()
        self.stack[:] = []
    def quit_game(self):
        self.reset_state()
        self.make_start_script(False)
    def reset_game(self):
        game = self.game
        self.reset_state()
        self.start_game(game)
    def start_game(self,game,script=None,mode="casemenu"):
        assets.show_load()
        gamename = game
        if "/" in game:
            gamename = game.rsplit("/",1)[1]
        print "starting game",game,gamename,script,mode
        if not script:
            print "not script",game+"/"+gamename+".txt"
            if os.path.exists(game+"/"+gamename+".txt"):
                script = gamename
            else:
                script = "intro"
        print "starting game",game,script,mode
        game = os.path.normpath(game).replace("\\","/")
        self.last_autosave = time.time()
        self.clear()
        self.game = game
        self.registry = registry.combine_registries("./"+self.game,self.show_load)
        self.stack.append(self.Script())
        if mode == "casemenu" and not os.path.exists(game+"/"+script+".txt"):
            self.cur_script.obs = [bg("main"),bg("main"),case_menu(game)]
            self.cur_script.obs[1].pos = [0,192]
            return
        print "set game to",assets.game
        self.cur_script.init(script)
        self.cur_script.execute_macro("init_defaults")
        self.cur_script.execute_macro("font_defaults")
        self.cur_script.execute_macro("load_defaults")
        self.cur_script.execute_macro("init_court_record_settings")
    def addevmenu(self):
        try:
            em = evidence_menu(self.items)
            self.cur_script.add_object(em,True)
        except art_error,e:
            self.cur_script.obs.append(error_msg(e.value,"",0,self.cur_script))
            import traceback
            traceback.print_exc()
            return
        return em
    def addscene(self,scene):
        #FIXME - assets.Script should be script.Script
        s = self.Script()
        s.init(scene)
        self.stack.append(s)
        
def vtrue(variable):
    if variable.lower() in ["on","1","true"]:
        return True
    return False
    
assets = Assets()

assets.subscripts = {}
def subscript(macro,execute=False):
    """Runs a macro all the way through"""
    #FIXME - limit recursion for subscripts. kind of a hack
    if macro in assets.subscripts:
        return
    script = assets.cur_script.execute_macro(macro)
    print "start subscript",macro,getattr(script,"scene","(no scene)")
    assets.subscripts[macro] = 1
    while script in assets.stack:
        if execute:
            e = script.interpret()
        else:
            e = script.update()
        if e:
            break
    print "end subscript",macro,getattr(script,"scene","(no scene)")
    del assets.subscripts[macro]
    

class SoundEvent(object):
    kill = 0
    pri = -1000000
    def __init__(self,name,after=0,volume=1.0):
        self.name = name
        self.wait = after
        self.volume = volume
        self.z = zlayers.index(self.__class__.__name__)
    def delete(self):
        self.kill = 1
    def update(self):
        self.wait-=assets.dt
        if self.wait<=0:
            assets.play_sound(self.name,volume=self.volume)
            self.delete()
        return False
    def draw(self,*args):
        pass

def color_str(rgbstring):
    if rgbstring.startswith(" "):
        rgbstring = rgbstring[1:]
    cv = assets.variables.get("color_"+rgbstring,None)
    if cv is not None:
        rgbstring = cv
    if len(rgbstring)==3:
        return [int((int(colchar)/9.0)*255) for colchar in rgbstring]
    elif len(rgbstring)==6:
        v = [int(rgbstring[:2],16),int(rgbstring[2:4],16),int(rgbstring[4:6],16)]
        return v
        
def trans_y(y):
    """Alter y value to place us in the proper screen"""
    if assets.num_screens==1:
        y-=192
    return y
        
class ws_button(gui.button):
    """A button created from wrightscript"""
    screen_setting = ""
    id_name = "_ws_button_"
    def delete(self):
        print "deleting ws_button"
        self.kill = 1
    def getrpos(self):
        rpos = self.rpos[:]
        if self.screen_setting == "try_bottom":
            rpos[1] = trans_y(rpos[1])
        return rpos
    def event(self,name,pos,*args):
        orpos = self.rpos[:]
        self.rpos = self.getrpos()
        ret = super(ws_button,self).event(name,pos,*args)
        self.rpos = orpos
        return ret
    def draw(self,dest):
        orpos = self.rpos[:]
        self.rpos = self.getrpos()
        super(ws_button,self).draw(dest)
        self.rpos = orpos
        
class ws_editbox(gui.editbox):
    """An editbox created from wrightscript"""
    screen_setting = ""
    id_name = "_ws_button_"
    def delete(self):
        print "deleting ws_button"
        self.kill = 1
    def getrpos(self):
        rpos = self.rpos[:]
        if self.screen_setting == "try_bottom":
            rpos[1] = trans_y(rpos[1])
        return rpos
    def event(self,name,pos,*args):
        orpos = self.rpos[:]
        self.rpos = self.getrpos()
        ret = super(ws_editbox,self).event(name,pos,*args)
        self.rpos = orpos
        return ret
    def draw(self,dest):
        orpos = self.rpos[:]
        self.rpos = self.getrpos()
        super(ws_editbox,self).draw(dest)
        self.rpos = orpos

class sprite(gui.button):
    blinkspeed = [100,200]
    autoclear = False
    pri = 0
    #widget stuff
    def _g_rpos(self):
        if not hasattr(self,"pos"): return [0,0]
        return self.getpos()
    rpos = property(_g_rpos)
    width,height = [sw,sh]
    children = []
    spd = 6
    def getpos(self):
        pos = self.pos[:]
        if self.screen_setting == "try_bottom":
            pos[1] = trans_y(pos[1])
        return pos
    def getprop(self,p):
        if p in "xy":
            return self.pos["xy".index(p)]
        if p == "frame":
            return self.x
	if p == "screen_setting":
	    return self.screen_setting
        return getattr(self,p,"")
    def setprop(self,p,v):
        if p in "xy":
            self.pos["xy".index(p)] = float(v)
        if p in "z":
            self.z = int(v)
        if p == "frame":
            self.x = int(v)
	if p == "screen_setting":
	    self.screen_setting = v
    def delete(self):
        self.kill = 1
    def makestr(self):
        """A wrightscript string to recreate the object"""
        if not getattr(self,"name",None): return ""
        xs = ""
        ys = ""
        zs = ""
        id = ""
        if self.pos[0]: xs = "x="+str(self.pos[0])+" "
        if self.pos[1]: ys = "y="+str(self.pos[1])+" "
        #Make this better (maybe only allow layer name for z?)
        if type(self.z)==type(""):
            if zlayers.index(self.__class__.__name__)!=zlayers.index(self.z.remove("_layer_")):
                zs = "z="+self.z
        else:
            if self.z != zlayers.index(self.__class__.__name__):
                zs = "z=_layer_"+zlayers[self.z][0]
        if not getattr(self,"id_name","$$").startswith("$$"): id = "name="+self.id_name+" "
        try:
            comm = {"bg":"bg","fg":"fg","evidence":"ev"}[self.__class__.__name__]
        except KeyError:
            return ""
        return (comm+" "+self.name.split("/",1)[1]+" "+xs+ys+zs+id).strip()
    def click_down_over(self,mp):
        pass
    def load_extra(self,m):
        self.sounds = m.sounds
        self.loops = m.loops
        self.split = m.split
        self.blinkmode = m.blinkmode
        self.offsetx = m.offsetx
        self.offsety = m.offsety
        self.blipsound = m.blipsound
        self.delays = m.delays
        self.spd = m.speed
        self.blinkspeed = m.blinkspeed
        if assets.variables.get("_blinkspeed_next",""):
            self.blinkspeed = [int(x) for x in assets.variables["_blinkspeed_next"].split(" ")]
            assets.variables["_blinkspeed_next"] = ""
        elif assets.variables.get("_blinkspeed_global","default")!="default":
            self.blinkspeed = [int(x) for x in assets.variables["_blinkspeed_global"].split(" ")]
    def load(self,name,key=[255,0,255]):
        self.key = key
        if type(name)==type("") or type(name)==type(u""):
            path = ""
            self.base = assets.open_art(name,key)
            self.load_extra(assets.meta)
        else:
            self.base = name
            self.load_extra(meta())
        self.real_path = assets.real_path
        if self.base:
            self.width,self.height = self.base[0].get_size()
        else:
            self.width,self.height = [0,0]
            self.name = name
            self.x = 0
            self.next = self.spd
            return self
        self.img = self.base[0]
        self.name = name
        self.x = 0
        self.next = self.delays.get(0,self.spd)
        return self
    def __init__(self,x=0,y=0,flipx=0,**kwargs):
        self.spd = int(assets.variables.get("_default_frame_delay",self.spd))
        self.loopmode = ""
        self.next = self.spd
        self.pos = [x,y]
        self.dim = 1
        self.z = zlayers.index(self.__class__.__name__)
        self.rot = [0,0,0]
        if kwargs.get("rotx",None): self.rot[0]=int(kwargs.get("rotx"))
        if kwargs.get("roty",None): self.rot[1]=int(kwargs.get("roty"))
        if kwargs.get("rotz",None): self.rot[2]=int(kwargs.get("rotz"))
        self.sounds = {}
        self.x = 0
        self.offsetx = 0
        self.offsety = 0
        self.loops = 0
        self.loopmode = 0
        self.flipx=flipx
        self.blinkmode = "blinknoset"
        if kwargs.get("screen",None)==2:
            self.pos[1]=other_screen(self.pos[1])
        self.screen_setting=""
        self.base = []
        self.delays = {}
        self.start = 0
        self.end = None
    def draw(self,dest):
        if not getattr(self,"img",None): return
        img = self.img
        if self.flipx:
            img = pygame.transform.flip(img,1,0)
        pos = self.getpos()
        if hasattr(self,"offsetx"): pos[0]+=self.offsetx
        if hasattr(self,"offsety"): pos[1]+=self.offsety
        if hasattr(self,"rot"):
            if hasattr(img,"ori"):
                img.ori = self.rot
            elif self.rot[2]:
                pos[0]+=img.get_width()//2
                pos[1]+=img.get_height()//2
                img = pygame.transform.rotate(img,self.rot[2]).convert_alpha()
                pos[0]-=img.get_width()//2
                pos[1]-=img.get_height()//2
        if self.dim != 1:
            os = img.get_size()
            img = pygame.transform.rotozoom(img,0,self.dim)
            ns = img.get_size()
            pos[0]+=os[0]//2-ns[0]//2
            pos[1]+=os[1]//2-ns[1]//2
        dest.blit(img,pos)
    def update(self):
        if self.next>0:
            self.next-=assets.dt
        if self.next<=0:
            if self.sounds.get(self.x,None):
                assets.play_sound(self.sounds[self.x])
            self.x += 1
            self.next += self.delays.get(self.x,self.spd)
            end = len(self.base)
            if self.end is not None:
                end = self.end
            if self.x>=end:
                if self.loops and (not self.loopmode or self.loopmode=="loop"):
                    self.x = 0
                    if self.loops>1:
                        self.loops -= 1
                        if self.loops == 1:
                            self.loops = 0
                elif self.loopmode in ["blink","blinknoset"]:
                    self.x = self.start
                    self.next = random.randint(self.blinkspeed[0],self.blinkspeed[1])
                else:
                    self.next = -1
                    self.x-=1
                    #self.x = 0
        if self.loopmode == "stop":
            self.loops = 0
        if self.base:
            if self.x<len(self.base):
                self.img = self.base[self.x]

from soft3d import context

class surf3d(sprite):
    def __init__(self,pos,sw,sh,rw,rh):
        self.id_name = "surf3d"
        self.pos = pos
        self.sw,self.sh=sw,sh
        self.z = 2
        self.pri = -1000
        self.width,self.height = rw,rh
        self.context = context.SoftContext(sw,sh,rw,rh)
        self.surf = self.context.draw()
        self.next = 5
        self.screen_setting = ""
    def click_down_over(self,pos):
        print "click",pos
        if pos[0]>=self.pos[0] and pos[0]<=self.pos[0]+self.width and pos[1]>=self.pos[1] and pos[1]<=self.pos[1]+self.height:
            for o in assets.cur_script.obs:
                if isinstance(o,mesh):
                    o.click(pos)
    def draw(self,dest):
        dest.blit(self.surf,self.getpos())
    def update(self):
        self.next -= assets.dt
        if self.next>0:
            return
        if [x for x in self.context.objects if x.changed]:
            self.surf = self.context.draw().convert()
        [setattr(x,"changed",0) for x in self.context.objects]
        self.next = 2

class mesh(sprite):
    def __init__(self,meshfile,pos=[0,0],rot=[0,0,0],name="surf3d"):
        self.pos = pos
        self.z = 0
        self.pri = 0
        self.id_name = "mesh"
        self.regions = []
        self.fail = "none"
        self.examine = False
        self.dz = 0
        self.rot = [0,0,0]
        self.maxz=0
        self.minz=-150
        self.meshfile=meshfile
        self.surfname = name
        self.changed = 1
        self.screen_setting = ""
    def load(self,script=None):
        if not script:
            script = assets.cur_script
        con = None
        for o in assets.cur_script.world.all:
            if getattr(o,"id_name",None)==self.surfname:
                con = o
                break
        if not con:
            return
        self.con = con
        path = assets.game+"/art/models/"
        self.ob = ob = con.context.load_object(self.meshfile,path)
        ob.trans(z=-100)
        ob.rot(90,0,0)
        ob.changed = 1
    def trans(self,x=0,y=0,z=0):
        if self.dz+z>self.maxz:
            z = self.maxz-self.dz
        elif self.dz+z<self.minz:
            z = self.minz-self.dz
        self.dz+=z
        self.ob.trans(x,y,z)
        self.ob.changed = 1
    def click(self,pos):
        if not self.examine:
            return
        x,y = pos
        x=int((x-self.con.pos[0])*(self.con.context.s_w/float(self.con.context.r_w)))
        y=int((y-self.con.pos[1])*(self.con.context.s_h/float(self.con.context.r_h)))
        i = y*self.con.context.s_w+x
        if i>=len(pygame.depth) or i<0:
            return
        point = pygame.depth[i][1]
        if point:
            u,v = point
            for rect in self.regions:
                if u>=rect[0] and u<=rect[0]+rect[2] and v>=rect[1] and v<=rect[1]+rect[3]:
                    label = rect[4]
                    self.goto(u,v,label)
                    return
            return self.goto(u,v,self.fail)
    def goto(self,u,v,label):
        self.examine = False
        assets.variables["_examine_clickx3d"] = str(u)
        assets.variables["_examine_clicky3d"] = str(v)
        self.regions[:] = []
        assets.cur_script.goto_result(label,backup=self.fail)
    def rotate(self,axis,amount):
        r = [0,0,0]
        r[axis] = amount
        self.ob.rot(*r)
        self.ob.changed = 1
    def draw(self,dest):
        pass
    def update(self):
        pass
        
class fadesprite(sprite):
    real_path=None
    invert = 0
    tint = None
    greyscale = 0
    def setfade(self,val=255):
        if val<0: val = 0
        if val>255: val = 255
        if getattr(self,"fade",None) is None: self.fade = 255
        self.lastfade = self.fade
        self.fade = val
        return self
    def draw(self,dest):
        if getattr(self,"fade",None) is None: self.fade = 255
        if self.fade == 0:
            return
        if self.fade == 255 and not self.invert and not self.tint and not self.greyscale:
            return sprite.draw(self, dest)
        if getattr(self,"img",None) and not getattr(self,"mockimg",None):
            if pygame.use_numpy:
                self.mockimg = self.img.convert_alpha()
                self.mockimg_base = [x.convert_alpha() for x in self.base]
                self.origa_base = [pygame.surfarray.array_alpha(x) for x in self.mockimg_base]
                self.draw_func = self.numpydraw
            else:
                self.draw_func = self.mockdraw
                ximg = pygame.Surface(self.img.get_size())
                ximg.fill([255,0,255])
                ximg.blit(self.img,[0,0])
                ximg = ximg.convert()
                ximg.set_colorkey([255,0,255])
                self.mockimg = ximg
        if (getattr(self,"tint",None) or getattr(self,"invert",None)) and not getattr(self,"origc_base",None) and pygame.use_numpy:
            self.origc_base = [pygame.surfarray.array3d(x) for x in self.mockimg_base]
            print "set base foo",self.origc_base
        try:
            self.draw_func(dest)
        except Exception:
            if pygame.use_numpy:
                pygame.use_numpy = False
                self.mockimg = None
                import traceback
                traceback.print_exc()
                raise art_error("Problem with fading code, switching to older fade technology")
    def numpydraw(self,dest):
        if not self.mockimg_base:
            return
        px = pygame.surfarray.pixels_alpha(self.mockimg_base[self.x])
        px[:] = self.origa_base[self.x][:]*(self.fade/255.0)
        del px
        px = pygame.surfarray.pixels3d(self.mockimg_base[self.x])
        if getattr(self,"origc_base",None):
            px[:] = self.origc_base[self.x]
            if self.invert:
                px[:] = 255-px[:]
            self.linvert = self.invert
            if self.tint:
                px*=self.tint
            self.lt = self.tint
        del px
        img = self.img
        self.img = self.mockimg_base[self.x]
        if self.greyscale:
            self.lgs = self.greyscale
            ximg = pygame.Surface(self.img.get_size())
            ximg.fill([255,0,255])
            ximg.blit(self.img,[0,0])
            ximg = ximg.convert(8)
            pal = ximg.get_palette()
            gpal = []
            for col in pal:
                if col == (255,0,255):
                    gpal.append(col)
                    continue
                avg = (col[0]+col[1]+col[2])//3
                gpal.append([avg,avg,avg])
            ximg.set_palette(gpal)
            ximg = ximg.convert()
            ximg.set_colorkey([255,0,255])
            yimg = pygame.Surface(self.img.get_size()).convert_alpha()
            yimg.fill([0,0,0,0])
            yimg.blit(ximg,[0,0])
            self.img = yimg
        sprite.draw(self,dest)
        self.img = img
    def mockdraw(self, dest):
        self.mockimg.set_alpha(self.fade)
        img = self.img
        self.img = self.mockimg
        sprite.draw(self,dest)
        self.img = img
    def update(self):
        sprite.update(self)

class graphic(fadesprite):
    def __init__(self,name,*args,**kwargs):
        fadesprite.__init__(self,*args,**kwargs)
        self.load(name)

class portrait(sprite):
    autoclear = True
    def get_self_image(self):
        if hasattr(self,"img"):
            return self.cur_sprite.img
    img = property(get_self_image)
    def makestr(self):
        """A wrightscript string to recreate the object"""
        xs = ""
        ys = ""
        zs = ""
        id = ""
        emo = ""
        if self.emoname != "normal": emo = "e="+self.emoname+" "
        nt = ""
        if self.pos[0]: xs = "x="+str(self.pos[0])+" "
        if self.pos[1]: ys = "y="+str(self.pos[1])+" "
        if type(self.z)==type(""):
            if zlayers.index(self.__class__.__name__)!=zlayers.index(self.z.remove("_layer_")):
                zs = "z="+self.z
        else:
            if self.z != zlayers.index(self.__class__.__name__):
                zs = "z=_layer_"+zlayers[self.z][0]
        if not getattr(self,"id_name","$$").startswith("$$"): id = "name="+self.id_name+" "
        if getattr(self,"nametag",self.charname).strip("\n")!=self.charname: nt = "nametag="+self.nametag+" "
        hide = {True: " hide", False: ""}[bool(self.hide)]
        stack = {True: " stack", False: ""}[bool(getattr(self,"was_stacked",False))]
        return ("char "+self.charname+" "+xs+ys+zs+id+emo+nt+hide+stack+getattr(self,"extrastr","")).strip()
    f = open("core/blipsounds.txt")
    bliplines = f.readlines()
    f.close()
    male  = bliplines[1].strip().split(" ")
    female = bliplines[4].strip().split(" ")
    def __init__(self,name=None,hide=False):
        self.talk_sprite = fadesprite()
        self.blink_sprite = fadesprite()
        self.combined = fadesprite()
        super(portrait,self).__init__()
        self.init(name,hide)
    def init_sounds(self):
        self.clicksound = assets.variables.get("char_defsound","blipmale.ogg")
        if self.charname in self.female:
            self.clicksound = "blipfemale.ogg"
        if self.charname in self.male:
            self.clicksound = "blipmale.ogg"
        if hasattr(self,"talk_sprite"):
            if getattr(self.talk_sprite,"blipsound",None):
                self.clicksound = self.talk_sprite.blipsound
        if "char_"+self.charname+"_defsound" in assets.variables:
            self.clicksound = assets.variables["char_"+self.charname+"_defsound"]
    def init(self,name=None,hide=False,blinkname=None,init_basic=True):
        if not name: return self.init_sounds()
        charname,rest = name.split("/",1)
        if init_basic:
            self.z = zlayers.index(self.__class__.__name__)
            self.pri = ulayers.index(self.__class__.__name__)
            self.pos = [0,0]
            self.rot = [0,0,0]
            self.name = name
            self.id_name = charname
            self.nametag = assets.variables.get("char_"+charname+"_name",charname.capitalize())+"\n"
        #super(portrait,self).__init__()
        
        emo = rest
        mode = ""
        if emo.endswith("(combined)"):
            emo,mode = emo.rsplit("(combined)",1)[0],"combined)"
        elif emo.endswith("(blink)"):
            emo,mode = emo.rsplit("(blink)",1)[0],"blink)"
        elif emo.endswith("(talk)"):
            emo,mode = emo.rsplit("(talk)",1)[0],"talk)"
        blinkemo = emo
        blinkmode = mode
        if blinkname:
            blinkemo = blinkname
            blinkmode = "blink"
        
        mode = mode[:-1]
        self.charname = charname
        self.emoname = emo
        self.blinkemo = blinkemo
        self.modename = mode
        self.supermode = "lipsync"
        
        if not self.emoname: hide = "wait"
        self.hide = hide
        if self.hide: return self.init_sounds()
        self.talk_sprite = fadesprite()
        self.blink_sprite = fadesprite()
        self.combined = fadesprite()
        def shrink(t):
            if not t.startswith("/"):
                t = "/"+t
            return t[t.rfind("/art/")+5:-4]
            
        def loadfrom(path):
            if not path.endswith("/"):path+="/"

            print ">",blinkemo
            print path+blinkemo+"(blink)"
            blink = assets.registry.lookup(path+blinkemo+"(blink)")
            if blink and not hasattr(self.blink_sprite,"img"):
                self.blink_sprite.load(blink.rsplit("art/",1)[1][:-4])
                
            talk = assets.registry.lookup(path+emo+"(talk)")
            if talk and not hasattr(self.talk_sprite,"img"):
                self.talk_sprite.load(talk.rsplit("art/",1)[1][:-4])
                
            combined = assets.registry.lookup(path+emo+"(combined)")
            if combined and not hasattr(self.combined,"img"):
                self.combined.load(combined.rsplit("art/",1)[1][:-4])
                if not self.combined.split:
                    self.combined.split = len(self.combined.base)//2
                self.talk_sprite.load(self.combined.base[:self.combined.split])
                self.talk_sprite.name = self.combined.name+"_talk"
                self.blink_sprite.load(self.combined.base[self.combined.split:])
                self.blink_sprite.name = self.combined.name+"_blink"
                self.talk_sprite.loops = 1
                self.blink_sprite.loops = 1
                self.talk_sprite.delays = self.combined.delays
                self.blink_sprite.delays = self.combined.delays
                self.blink_sprite.blinkmode = self.combined.blinkmode
                self.blink_sprite.blinkspeed = self.combined.blinkspeed
                self.talk_sprite.offsetx = self.combined.offsetx
                self.talk_sprite.offsety = self.combined.offsety
                self.blink_sprite.offsetx = self.combined.offsetx
                self.blink_sprite.offsety = self.combined.offsety
            
            available = assets.registry.lookup(path+emo)
            if available and not hasattr(self.blink_sprite,"img"):
                self.blink_sprite.load(available.rsplit("art/",1)[1][:-4])
                if self.blink_sprite.blinkmode=="blinknoset": self.blink_sprite.blinkmode = "stop"
            
            print blink,talk,combined,available
            if blink or talk or combined or available:
                return True
            raise art_error("Character folder %s not found"%charname)

        loadfrom("art/port/"+charname)
        if hasattr(self.talk_sprite,"img") and not hasattr(self.blink_sprite,"img"):
            self.blink_sprite.img = i = self.talk_sprite.img
            self.blink_sprite.base = [i]
            self.blink_sprite.blinkmode = "stop"
            #self.blink_sprite.load(self.talk_sprite.base[:])
            #self.blink_sprite.base = [self.blink_sprite.base[0]]
        if hasattr(self.blink_sprite,"img") and not hasattr(self.talk_sprite,"img"):
            self.talk_sprite.img = i = self.blink_sprite.img
            self.talk_sprite.base = [i]
            #self.talk_sprite.load(self.blink_sprite.base[:])
            #self.talk_sprite.base = [self.talk_sprite.base[0]]
        self.blink_sprite.loopmode = self.blink_sprite.blinkmode
        self.blink_sprite.spd = int(assets.variables.get("_default_port_frame_delay",self.talk_sprite.spd))
        self.talk_sprite.spd = int(assets.variables.get("_default_port_frame_delay",self.talk_sprite.spd))
        if hasattr(self.talk_sprite,"img") and hasattr(self.blink_sprite,"img"):
            if mode=="blink":self.set_blinking()
            #if mode=="talk":self.set_talking()
        else:
            raise art_error("Can't load character "+charname+"/"+emo+"("+mode+")")
        self.blinkspeed = self.blink_sprite.blinkspeed
        #if init_basic:
        self.init_sounds()
    def setprop(self,p,v):
        if p in "xy":
            self.pos["xy".index(p)] = float(v)
        if p in "z":
            self.z = int(v)
        if p in ["supermode","mode"]:
            setattr(self,p,v)
    def set_dim(self,amt):
        self.blink_sprite.dim = amt
        self.talk_sprite.dim = amt
    def get_dim(self):
        return self.blink_sprite.dim
    dim = property(get_dim,set_dim)
    def draw(self,dest):
        if not self.hide and getattr(self.cur_sprite,"img",None):
            self.cur_sprite.tint = self.tint
            self.cur_sprite.greyscale = self.greyscale
            self.cur_sprite.invert = self.invert
            pos = self.pos[:]
            pos[0] += (sw-(self.cur_sprite.offsetx+self.cur_sprite.img.get_width()))//2
            pos[1] += (sh-(self.cur_sprite.img.get_height()-self.cur_sprite.offsety))
            self.cur_sprite.pos = pos
            self.cur_sprite.rot = self.rot[:]
            self.cur_sprite.draw(dest)
    def delete(self):
        self.kill = 1
    def update(self):
        if not self.hide and getattr(self.cur_sprite,"img",None):
            return self.cur_sprite.update()
    def set_emotion(self,emo):
        if self.hide and self.hide != "wait": return
        if not emo: return
        self.hide = False
        self.init(self.charname+"/"+emo+"("+self.modename+")",init_basic=False)
    def set_blink_emotion(self,emo):
        if self.hide and self.hide != "wait": return
        if not emo: return
        self.hide = False
        self.init(self.charname+"/"+self.emoname+"("+self.modename+")",blinkname=emo,init_basic=False)
    def set_talking(self):
        self.modename = "talk"
    def set_blinking(self):
        self.modename = "blink"
    def set_single(self):
        self.modename = "blink"
        self.supermode = "blink"
    def set_lipsync(self):
        self.supermode = "lipsync"
        self.modename = "blink"
    def get_current_sprite(self):
        if self.supermode == "lipsync":
            mode = self.modename
        else:
            mode = self.supermode
        if mode == "blink":
            return self.blink_sprite
        if mode == "talk":
            return self.talk_sprite
        if mode == "loop":
            self.blink_sprite.loopmode = "loop"
            return self.blink_sprite
        return self.blink_sprite
    cur_sprite = property(get_current_sprite)
    def setfade(self,*args):
        self.blink_sprite.setfade(*args)
        self.talk_sprite.setfade(*args)
    invert = 0
    tint = None
    greyscale = 0
        
class evidence(fadesprite):
    autoclear = True
    def __init__(self,name="ev",**kwargs):
        if not kwargs.has_key("x"): kwargs["x"]=5
        if not kwargs.has_key("y"): kwargs["y"]=5
        if not kwargs.has_key("pri"): kwargs["pri"]=50
        if not kwargs.get("page",None):
            pages = assets.variables.get("_ev_pages","evidence profiles").split(" ")
            if len(pages)==1:
                pages = pages + pages
            if name.endswith("$"):
                kwargs["page"] = pages[1]
            else:
                kwargs["page"] = pages[0]
        self.page = kwargs["page"]
        super(evidence,self).__init__(**kwargs)
        self.id = name
        self.reload()
    def reload(self):
        artname = assets.variables.get(self.id+"_pic",self.id.replace("$",""))
        try:
            self.load("ev/"+artname)
        except:
            import traceback
            traceback.print_exc()
            self.img = assets.Surface([16,16])
            self.img.fill([255,255,255])
        self.small = pygame.transform.smoothscale(self.img,[35,35])
        self.scaled = pygame.transform.smoothscale(self.img,[70,70])
        self.setfade()
        self.name = assets.variables.get(self.id+"_name",self.id.replace("$",""))
        self.desc = assets.variables.get(self.id+"_desc",self.id.replace("$",""))
        
class penalty(fadesprite):
    def __init__(self,end=100,var="penalty",flash_amount=None):
        self.id_name = "penalty"
        self.var = var
        super(penalty,self).__init__()
        self.gfx = assets.open_art("general/healthbar",key=[255,0,255])[0]
        self.left = self.gfx.subsurface([[0,0],[2,14]])
        self.right = self.gfx.subsurface([[82,0],[2,14]])
        self.good = self.gfx.subsurface([[2,0],[1,14]])
        self.bad = self.gfx.subsurface([[66,0],[1,14]])
        self.pos = [0,0]
        if end<0: end = 0
        self.end = end
        self.delay = 50
        self.flash_amount = flash_amount
        self.flash_color = [255,242,129,150]
        self.flash_dir = 1
        self.change = 0
    def gv(self):
        v = assets.variables.get(self.var,100)
        try:
            v = int(v)
        except:
            v = 100
        return v
    def sv(self,val):
        assets.variables[self.var] = str(val)
    def draw(self,dest):
        v = self.gv()
        x = sw-110
        dest.blit(self.left,[x,2]); x+=2
        if v<0: v=0
        for i in range(v):
            dest.blit(self.good,[x,2]); x+=1
        for i in range(100-v):
            dest.blit(self.bad,[x,2]); x += 1
        dest.blit(self.right,[x,2])
        if self.flash_amount:
            fx = sw-108+v-self.flash_amount
            fw = self.flash_amount
            fy = 4
            fh = 10
            surf = pygame.Surface([fw,fh]).convert_alpha()
            surf.fill(self.flash_color)
            dest.blit(surf,[fx,fy])
            self.flash_color[3]+=self.flash_dir*8
            if self.flash_color[3]>200 or self.flash_color[3]<100:
                self.flash_dir = -self.flash_dir
        self.sv(v)
    def update(self):
        self.change += assets.dt
        while self.change>1:
            self.change -= 1
            v = self.gv()
            if self.end<v:
                v -= 1
                if v<0: v = 0
            elif self.end>v:
                v += 1
                if v>100: v = 100
            elif self.delay:
                self.delay -= 1
                if self.delay==0:
                    self.die()
                    self.delete()
            self.sv(v)
        if self.delay:
            return True
    def die(self):
        if self.gv()<=0:
            print "bad penalty about to die"
            ps = assets.variables.get("_penalty_script","")
            if ps:
                args = []
                if " " in ps:
                    ps,label = ps.split(" ",1)
                    args.append("label="+label)
                assets.cur_script._script("script",ps,*args)
        
class bg(fadesprite):
    autoclear = True
    def __init__(self,name="",**kwargs):
        super(bg,self).__init__(**kwargs)
        if name:
            self.load("bg/"+name)
        
class fg(fadesprite):
    autoclear = True
    def __init__(self,name="",**kwargs):
        super(fg,self).__init__(**kwargs)
        if name:
            self.load("fg/"+name)
            self.pos = [(sw-self.img.get_width())/2+self.pos[0],(sh-self.img.get_height())/2+self.pos[1]]
        self.wait = kwargs.get("wait",1)
        self.spd = int(assets.variables.get("_default_fg_frame_delay",self.spd))
    def update(self):
        super(fg,self).update()
        if self.next>=0 and self.wait:
            return True
        
class testimony_blink(fg):
    def draw(self,dest):
        self.pos[0] = 0
        self.pos[1] = 22
        self.fade = 255
        if not hasattr(self,"time"):
            self.time = 80
        self.time -= 1
        if self.time == 0:
            self.time = 80
        if self.time>20 and vtrue(assets.variables.get("_testimony_blinker", "true")):
            w,h = self.img.get_size()
            dest.blit(pygame.transform.scale(self.img,[int(w//1.5),int(h//1.5)]),self.pos)

class textbox(gui.widget):
    pri = 30
    def click_down_over(self,pos):
        if not hasattr(self,"rpos1"): return
        if getattr(self,"hidden",0): return
        if self.statement:
            if pos[1]>=self.rpos[1] and pos[1]<=self.rpos1[1]+self.height1:
                if pos[0]>=self.rpos1[0] and pos[0]<=self.rpos1[0]+self.width/2:
                    self.k_left()
                if pos[0]>=self.rpos1[0]+self.width/2 and pos[0]<=self.rpos1[0]+self.width:
                    self.k_right()
        if pos[0]>=self.rpos1[0] and pos[0]<=self.rpos1[0]+self.width1 and pos[1]>=self.rpos1[1] and pos[1]<=self.rpos1[1]+self.height1:
            self.enter_down()
    def set_text(self,text):
        #print "SETTING TEXT:",repr(text)
        text = textutil.markup_text(text)
        #print "marked up text:",repr(text)
        text.m_replace(lambda c:hasattr(c,"variable"),lambda c:assets.variables[c.variable])
        lines = text.fulltext().split(u"\n")
        wrap = vtrue(assets.variables.get("_textbox_wrap","true"))
        if vtrue(assets.variables.get("_textbox_wrap_avoid_controlled","true")):
            if len(lines)>1:
                wrap = False
        lines = textutil.wrap_text(lines,assets.get_image_font("tb"),250,wrap)
        self.pages = [lines[i:i+3] for i in xrange(0, len(lines), 3)]
        self._text = u"\n"
        self._markup = textutil.markup_text("")
        for page in self.pages:
            for line in page:
                self._text += line.fulltext()
                self._text+="\n"
                self._markup._text.extend(line.chars())
                self._markup._text.append("\n")
    text = property(lambda self: self._text,set_text)
    def __init__(self,text="",color=[255,255,255],delay=2,speed=1,rightp=True,leftp=False,nametag="\n"):
        self.nametag = nametag
        ImgFont.lastcolor = [255,255,255]
        gui.widget.__init__(self,[0,0],[sw,sh])
        self.z = zlayers.index(self.__class__.__name__)
        nametag = self.nametag
        if assets.portrait:
            nametag = getattr(assets.portrait,"nametag",nametag) or nametag
        self.nt_full = None
        self.nt_left = None
        self.nt_text_image = None
        self.base = assets.open_art(assets.variables.get("_textbox_bg","general/textbox_2"))[0].convert_alpha()
        nt_full_image = assets.variables.get("_nt_image","")
        if nt_full_image:
            self.nt_full = assets.open_art(nt_full_image)[0].convert_alpha()
        elif nametag.strip():
            self.nt_left = assets.open_art("general/nt_left")[0].convert_alpha()
            self.nt_middle = assets.open_art("general/nt_middle")[0].convert_alpha()
            self.nt_right = assets.open_art("general/nt_right")[0].convert_alpha()
        self.nametag = nametag
        self.img = self.base.copy()
        self.go = 0
        self.text = text
        self.mwritten = []
        self.num_lines = 4
        self.next = self.num_lines
        self.color = color
        self.delay = delay
        self.speed = speed
        self.next_char = 0
        self.in_paren = 0  #Record whether we are inside parenthesis or not
        #Show pointer left and right
        self.rightp = rightp
        self.leftp = leftp
        self.rpi = fg("pointer")
        self.kill = False
        self.statement = None
        self.wait = "auto"
        
        self.can_skip = True
        self.blocking = not vtrue(assets.variables.get("_textbox_skipupdate","0"))
        
        self.made_gui = False
        
        self.id_name = "_textbox_"
    def init_cross(self):
        subscript("show_press_button",execute=True)
        subscript("show_present_button",execute=True)
    def init_normal(self):
        subscript("show_court_record_button")
    def delete(self):
        self.kill = 1
        assets.cur_script.refresh_arrows(self)
        subscript("hide_court_record_button")
        subscript("hide_press_button")
        subscript("hide_present_button")
    def gsound(self):
        if hasattr(self,"_clicksound"): return self._clicksound
        if assets.portrait:
            return assets.portrait.clicksound
        return "blipmale.ogg"
    def ssound(self,v):
        self._clicksound = v
    clicksound = property(gsound,ssound)
    def can_continue(self):
        """If not blocking, player cannot make text continue
        If skip mode is on (_debug mode) we can just skip the text
        Otherwise, check to see if all the text has been written out"""
        if not self.blocking: 
            return
        if self.can_skip or self.nextline():
            return True
    def enter_down(self):
        if not self.can_continue(): return
        if not self.nextline():
            while not self.nextline():
                self.add_character()
            #self.mwritten = self._markup._text
        else:
            self.forward()
    def k_left(self):
        if self.statement:
            assets.cur_script.prev_statement()
            self.forward()
    def k_right(self):
        if self.statement:
            self.forward()
    def k_z(self):
        if self.statement:
            assets.cur_script.cross = "pressed"
            assets.cur_script.goto_result("press "+self.statement,backup=assets.variables.get("_court_fail_label",None))
            self.delete()
    def k_x(self):
        if self.statement:
            em = assets.addevmenu()
            em.fail = assets.variables.get("_court_fail_label",None)
    def forward(self,sound=True):
        """Set last written text to the contents of the textbox
        turn off testimony blinking
        scroll to next 3 lines of text if they exist
        if there is no more text, delete textbox
        play the bloop sound"""
        t = textutil.markup_text()
        t._text = self.mwritten
        assets.variables["_last_written_text"] = t.fulltext()
        assets.cur_script.tboff()
        lines = self.text.split("\n")
        lines = lines[4:]
        self.set_text("\n".join(lines))
        self.mwritten = []
        self.next = self.num_lines
        self.img = self.base.copy()
        if not self.text.strip():
            self.delete()
        if sound:
            assets.play_sound("bloop.ogg",volume=0.7)
    def draw(self,dest):
        self.children = []
        if not self.go or self.kill:
            return
        #For the widget
        x = assets.variables.get("_textbox_x","")
        y = assets.variables.get("_textbox_y","")
        self.rpos1 = [(sw-self.img.get_width())/2,
            sh-self.img.get_height()]
        if x!="":
            self.rpos1[0] = int(x)
        if y!="":
            self.rpos1[1] = int(y)
        self.width1 = self.img.get_width()
        self.height1 = self.img.get_height()
        dest.blit(self.img,
            self.rpos1)
        if self.rightp and self.nextline():
            dest.blit(self.rpi.img,[self.rpos1[0]+self.width1-16,
                self.rpos1[1]+self.height1-16])
        if getattr(self,"showleft",False) and self.nextline():
            dest.blit(pygame.transform.flip(self.rpi.img,1,0),[self.rpos1[0],
                self.rpos1[1]+self.height1-16])
        #End
        x = assets.variables.get("_nt_x","")
        y = assets.variables.get("_nt_y","")
        if self.nt_full:
            nx,ny = self.rpos1[0],(self.rpos1[1]-self.nt_full.get_height())
            if x!="":
                nx = int(x)
            if y!="":
                ny = int(y)
            dest.blit(self.nt_full,[nx,ny])
            if self.nt_text_image:
                if assets.variables.get("_nt_text_x","")!="":
                    nx += int(assets.variables.get("_nt_text_x",0))
                if assets.variables.get("_nt_text_y","")!="":
                    ny += int(assets.variables.get("_nt_text_y",0))
                dest.blit(self.nt_text_image,[nx+5,ny])
        elif self.nt_left and self.nt_text_image:
            nx,ny = self.rpos1[0],(self.rpos1[1]-self.nt_left.get_height())
            if x!="":
                nx = int(x)
            if y!="":
                ny = int(y)
            dest.blit(self.nt_left,[nx,ny])
            for ii in range(self.nt_text_image.get_width()+8):
                dest.blit(self.nt_middle,[nx+3+ii,ny])
            dest.blit(self.nt_right,[nx+3+ii+1,ny])
            if assets.variables.get("_nt_text_x","")!="":
                nx += int(assets.variables.get("_nt_text_x",0))
            if assets.variables.get("_nt_text_y","")!="":
                ny += int(assets.variables.get("_nt_text_y",0))
            dest.blit(self.nt_text_image,[nx+5,ny])
    def add_character(self):
        command = None
        next_char = 1
        char = self._markup._text[len(self.mwritten)]
        self.mwritten.append(char)
        if isinstance(char,textutil.markup_command):
            command,args = char.command,char.args
            if assets.cur_script.macros.get(command,None):
                print "RUNNING A MACRO"
                assets.variables["_return"] = ""
                this = assets.cur_script
                ns = assets.cur_script.execute_macro(command,args)
                old = ns._endscript
                s = len(self.mwritten)-1
                mt = self._markup._text
                self._markup._text = self.mwritten
                def back(*args):
                    old()
                    print "MWRIT",s,self.mwritten
                    t0=[]
                    t1=[]
                    for i,c in enumerate(mt):
                        if i<s and not isinstance(c,textutil.markup_command):
                            t0.append(c)
                        if i>s:
                            t1.append(c)
                    t2 = [textutil.markup_command("_fullspeed","")]+t0+[textutil.markup_command("_endfullspeed","")]+list(assets.variables["_return"])+t1[:-1]
                    print "t0","".join([str(x) for x in t0])
                    print "t1","".join([str(x) for x in t1])
                    t = textutil.markup_text()
                    t._text = t2
                    print repr(t.fulltext())
                    self.set_text(t.fulltext())
                    self.mwritten = []
                    self.next_char = 0
                ns._endscript = back
            else:
                print "no macro for",command
                commands = ["sfx","sound","delay","spd","_fullspeed","_endfullspeed",
                "wait","center","type","next",
                "tbon","tboff",
                "e","f","s","p","c"]
                commands.sort(key=lambda o:len(o))
                commands.reverse()
                for cm in commands:
                    if command.startswith(cm):
                        nargs = command.split(cm,1)[1]
                        if nargs and not nargs.startswith(" "):
                            command,args = cm,nargs
                        break
                print "new command:",command,args
                if command == "sfx":
                    assets.play_sound(args)
                elif command == "sound":
                    self.clicksound = args
                elif command == "delay":
                    self.delay = int(args)
                    self.wait = "manual"
                elif command == "spd":
                    self.speed = float(args)
                elif command == "_fullspeed":
                    self.last_speed = self.speed
                    self.speed = 0
                elif command == "_endfullspeed":
                    self.speed = self.last_speed
                elif command == "wait":
                    self.wait = args
                elif command == "center":
                    pass
                elif command == "type":
                    self.clicksound = "typewriter.ogg"
                    self.delay = 2
                    self.wait = "manual"
                elif command == "next":
                    if assets.portrait:
                        assets.portrait.set_blinking()
                    del self.mwritten[-1]
                    self.forward(False)
                    return 0
                elif command=="e":
                    try:
                        assets.set_emotion(args.strip())
                    except:
                        import traceback
                        traceback.print_exc()
                        raise markup_error("No character to apply emotion to")
                elif command=="f":
                    assets.flash = 3
                    assets.flashcolor = [255,255,255]
                    command = args.split(" ")
                    if len(command)>0 and command[0]:
                        assets.flash = int(command[0])
                    if len(command)>1:
                        assets.flashcolor = color_str(command[1])
                elif command=="s":
                    assets.shakeargs = [x for x in args.split(" ") if x.strip()]
                elif command=="p":
                    next_char = int(args.strip())
                elif command=="c":
                    pass
                elif command=="tbon":
                    assets.cur_script.tbon()
                elif command=="tboff":
                    assets.cur_script.tboff()
                else:
                    raise markup_error("No macro or markup command valid for:"+command)
        elif isinstance(char,textutil.markup):
            pass
        else:
            if not hasattr(self,"_lc"):
                self._lc = ""
            self.go = 1
            if self._lc in [".?"] and char == " ":
                next_char = 6
            if self._lc in ["!"] and char == " ":
                next_char = 8
            if self._lc in [","] and char == " ":
                next_char = 4
            if self._lc in ["-"] and (char.isalpha() or char.isdigit()):
                next_char = 4
            if char in ["("]:
                self.in_paren = 1
            if char in [")"]:
                self.in_paren = 0
            if assets.portrait:
                punctuation = [x for x in assets.variables.get("_punctuation",u".,?!")]
                if not self.in_paren and not char in punctuation:
                    assets.portrait.set_talking()
                if self.in_paren:
                    assets.portrait.set_blinking()
            if str(char).strip():
                assets.play_sound(self.clicksound,volume=random.uniform(0.65,1.0))
            next_char = int(next_char*self.delay)
            if self.wait=="manual":
                if char.strip():
                    next_char = 5*self.delay
                else:
                    next_char = 2
            self._lc = char
        if self.speed:
            self.next_char += next_char
        return next_char
    def nextline(self):
        """Returns true if all the text waiting to be written into the textbox has been written"""
        t = textutil.markup_text()
        t._text = self.mwritten
        return not len(self.mwritten)<len(self._markup._text) or len(t.fulltext().split("\n"))>=self.num_lines
    def update(self):
        #assets.play_sound(self.clicksound)
        self.rpi.update()
        if self.kill: return
        self.next_char -= assets.dt
        char_per_frame = 0
        while (not self.nextline()) and self.next_char<=0:
            #self.next_char += 1
            num_chars = max(int(self.speed),1)
            cnum = num_chars
            while (not self.nextline()) and ((not self.speed) or cnum>0):
                cnum -= 1
                self.add_character()
                char_per_frame += 1
        if assets.portrait:
            if self.next_char>10 or self.nextline():
                assets.portrait.set_blinking()
        title = True
        self.next = 0
        if self.next==0:
            self.img = self.base.copy()
            y, stx, inc = 6, 6, 18
            x = stx
            color = self.color
            center = False
            t = textutil.markup_text()
            t._text = self.mwritten
            lines = [self.nametag.replace("\n","")]+t.fulltext().split("\n")
            nlines = assets.variables["_textbox_lines"]
            if nlines == "auto":
                if len(lines)==4:
                    nlines = "3"
                else:
                    nlines = "2"
            if not nlines:
                nlines = "3"
            nlines = int(nlines)
            if nlines == 2:
                y,inc = 8,24
            for i,line in enumerate(lines[:nlines+1]):
                if title:
                    if line.strip():
                        ncolor = assets.variables.get("_nt_text_color","")
                        if ncolor:
                            ncolor = color_str(ncolor)
                        else:
                            ncolor = color
                        nt_image = assets.get_font("nt").render(line.capitalize().replace(u"_",u" "),1,ncolor)
                        self.nt_text_image = nt_image
                    title = False
                else:
                    img = assets.get_image_font("tb").render(line,color)
                    color = ImgFont.lastcolor
                    if "{center}" in line:
                        center = not center
                    if center:
                        x = (sw-img.get_width())//2
                    if x+img.get_width()>256:
                        if not getattr(self,"OVERAGE",None) and vtrue(assets.variables.get("_debug","false")):
                            self.OVERAGE = x+img.get_width()-256
                            raise offscreen_text('Text Overflow:"%s" over by %s'%(line,self.OVERAGE))
                    self.img.blit(img,[x,y])
                    y+=inc
                    x = stx
            self.next = self.num_lines
        if self.blocking: 
            return True
        return
        
class uglyarrow(fadesprite):
    def __init__(self):
        fadesprite.__init__(self,x=0,y=sh)
        self.load(assets.variables.get("_bigbutton_bg","bg/main"))
        self.arrow = sprite(0,0).load("general/arrow_big")
        self.scanlines = fadesprite(0,0).load("fg/scanlines")
        self.border_top = fadesprite(0,0).load(assets.variables.get("_screen2_letterbox_img","general/bigbutton/border"))
        self.border_bottom = fadesprite(0,0).load(assets.variables.get("_screen2_letterbox_img","general/bigbutton/border"))
        self.scanlines.fade = 50
        self.button = None
        self.double = None
        self.textbox = None
        self.pri = ulayers.index(self.__class__.__name__)
        self.width = self.iwidth = sw
        self.height = self.iheight = sh
        self.high = False
        self.showleft = True
        self.last = None
        self.id_name = "_uglyarrow_"
    def show_unclicked(self):
        p = assets.variables.get("_bigbutton_img","general/buttonpress")
        if self.last != p:
            self.last = p
            self.button = sprite(0,0).load(p)
    def show_clicked(self):
        p = assets.variables.get("_bigbutton_img","general/buttonpress")
        high = noext(p)+"_high"+onlyext(p)
        if self.last != high:
            self.last = high
            self.button = sprite(0,0).load(high)
    def show_cross(self):
        if not self.double:
            self.double = sprite(0,0).load(assets.variables.get("_bigbutton_cross","general/cross_exam_buttons"))
        self.button = None
    def update(self):
        self.pos[1] = sh
        if self.high:
            self.show_clicked()
        else:
            self.show_unclicked()
        if self.textbox and self.textbox.statement:
            self.show_cross()
        self.arrow.update()
        return False
    def draw(self,dest):
        fadesprite.draw(self,dest)
        if self.button:
            self.button.pos[0] = (sw-self.button.img.get_width())//2
            self.button.pos[1] = (sh-self.button.img.get_height())//2+sh
            self.button.draw(dest)
            self.iwidth = self.button.img.get_width()
            self.iheight = self.button.img.get_height()
            if self.can_click():
                self.arrow.pos[0] = (sw-self.arrow.img.get_width())//2
                self.arrow.pos[1] = (sh-self.arrow.img.get_height())//2+sh
                self.arrow.draw(dest)
        elif self.double:
            self.double.pos[0] = (sw-self.double.img.get_width())//2
            self.double.pos[1] = (sh-self.double.img.get_height())//2+sh
            self.double.draw(dest)
            self.iwidth = self.double.img.get_width()
            self.iheight = self.double.img.get_height()
            if self.can_click():
                self.arrow.pos[0] = (sw-self.arrow.img.get_width())//2-75
                self.arrow.pos[1] = (sh-self.arrow.img.get_height())//2+sh
                self.arrow.img = pygame.transform.flip(self.arrow.img,1,0)
                if self.showleft:
                    self.arrow.draw(dest)
                self.arrow.pos[0] = (sw-self.arrow.img.get_width())//2+70
                self.arrow.pos[1] = (sh-self.arrow.img.get_height())//2+sh
                self.arrow.img = pygame.transform.flip(self.arrow.img,1,0)
                self.arrow.draw(dest)
        if vtrue(assets.variables.get("_screen2_scanlines","off")):
            self.scanlines.pos = self.pos
            self.scanlines.draw(dest)
        if vtrue(assets.variables.get("_screen2_letterbox","on")):
            self.border_top.pos = self.pos
            self.border_top.draw(dest)
            self.border_bottom.pos[0] = self.pos[0]
            self.border_bottom.pos[1] = self.pos[1]+192-self.border_bottom.height
            self.border_bottom.draw(dest)
    def over(self,mp):
        if self.button:
            if mp[0]>=self.button.pos[0] and mp[1]>=self.button.pos[1]\
            and mp[0]<=self.button.pos[0]+self.iwidth\
            and mp[1]<=self.button.pos[1]+self.iheight:
                return True
        if self.double:
            if mp[0]>=self.double.pos[0] and mp[1]>=self.double.pos[1]\
            and mp[0]<=self.double.pos[0]+self.iwidth/2\
            and mp[1]<=self.double.pos[1]+self.iheight:
                return "left"
            if mp[0]>=self.double.pos[0]+self.iwidth/2 and mp[1]>=self.double.pos[1]\
            and mp[0]<=self.double.pos[0]+self.iwidth\
            and mp[1]<=self.double.pos[1]+self.iheight:
                return "right"
    def move_over(self,mp,rel,bt):
        if not self.over(mp):
            if self.high:
                self.high = None
        else:
            if self.high == None:
                self.high = True
    def click_down_over(self,mp):
        gui.window.focused = self
        over = self.over(mp)
        if over == True and not self.high and self.can_click():
            self.high = True
        if over == "left" and self.can_click() and self.showleft:
            self.textbox.k_left()
        if over == "right" and self.can_click():
            self.textbox.k_right()
    def click_up_over(self,mp):
        if self.high:
            self.high = False
            if self.can_click():
                self.textbox.enter_down()
    def can_click(self):
        return self.textbox and not getattr(self.textbox,"kill",0) and self.textbox.can_continue()
            
class menu(fadesprite,gui.widget):
    z = 5
    fail = "none"
    id_name = "invest_menu"
    def over(self,mp):
        oy = self.getpos()[1]
        for o in self.options:
            p2 = self.opos[o]
            w,h = self.opt.get_width()//2,self.opt.get_height()//2
            if mp[0]>=p2[0] and mp[0]<=p2[0]+w and mp[1]>=p2[1]+oy and mp[1]<=p2[1]+h+oy:
                return o
    def move_over(self,pos,rel,buttons):
        if buttons[0]:
            self.click_down_over(pos)
    def click_down_over(self,mp):
        gui.window.focused = self
        o = self.over(mp)
        if o is not None:
            self.selected = o
    def click_up(self,mp):
        o = self.over(mp)
        if self.selected==o and o is not None:
            self.enter_down()
    def __init__(self):
        self.bg = None
        oy = 192
        fadesprite.__init__(self,x=0,y=oy)
        gui.widget.__init__(self,[0,oy],[sw,sh])
        self.load("general/black")
        self.max_fade = int(float(assets.variables.get("_menu_fade_level",50)))
        self.fade = 0
        if self.max_fade == 0:
            self.setfade(0)
        else:
            assets.cur_script.obs.append(fadeanim(start=0,end=self.max_fade,speed=3,wait=1,name=None,obs=[self]))
        self.options = []
        self.selected = ""
        self.opt = assets.open_art("general/talkbuttons",key=[255,0,255])[0]
        stx,sty = (sw-self.opt.get_width())/2,(sh-self.opt.get_height())/2
        self.opos_c = {"examine":[0,0],"move":[1,0],
            "talk":[0,1],"present":[1,1]}
        self.opos_l = [["examine","move"],["talk","present"]]
        self.opos = {"examine":[stx,sty],"move":[stx+self.opt.get_width()/2,sty],
            "talk":[stx,sty+self.opt.get_height()/2],"present":[stx+self.opt.get_width()/2,sty+self.opt.get_height()/2]}
        imgs = []
        x=y=0
        while y<self.opt.get_height():
            while x<self.opt.get_width():
                imgs.append(self.opt.subsurface([[x,y],[self.opt.get_width()//2,self.opt.get_height()//2]]))
                x+=self.opt.get_width()//2
            y+=self.opt.get_height()//2+1
            x = 0
        self.oimgs = {"examine":imgs[0],"move":imgs[1],"talk":imgs[2],"present":imgs[3]}
        self.opthigh = assets.open_art("general/talkbuttons_high",key=[255,0,255])[0]
        imgs = []
        x=y=0
        while y<self.opthigh.get_height():
            while x<self.opthigh.get_width():
                imgs.append(self.opthigh.subsurface([[x,y],[self.opthigh.get_width()//2,self.opthigh.get_height()//2]]))
                x+=self.opthigh.get_width()//2
            y+=self.opthigh.get_height()//2+1
            x = 0
        self.oimgshigh = {"examine":imgs[0],"move":imgs[1],"talk":imgs[2],"present":imgs[3]}
        self.open_script = True
    def init_normal(self):
        subscript("show_court_record_button")
    def delete(self):
        super(menu,self).delete()
        subscript("hide_court_record_button")
    def update(self):
        if not self.options:
            self.delete()
        fadesprite.update(self)
        self.screen_setting = "try_bottom"
        return True
    def get_coord(self):
        try:
            return self.opos_c[self.selected][:]
        except:
            return [0,0]
    def k_right(self):
        coord = self.get_coord()
        coord[0]+=1
        if coord[0]>1:
            coord[0] = 0
        sel = self.opos_l[coord[1]][coord[0]]
        if sel in self.options:
            self.selected = sel
        subscript("sound_investigate_menu_select")
    def k_left(self):
        coord = self.get_coord()
        coord[0]-=1
        if coord[0]<0:
            coord[0] = 1
        sel = self.opos_l[coord[1]][coord[0]]
        if sel in self.options:
            self.selected = sel
        subscript("sound_investigate_menu_select")
    def k_up(self):
        coord = self.get_coord()
        coord[1]-=1
        if coord[1]<0:
            coord[1] = 1
        sel = self.opos_l[coord[1]][coord[0]]
        if sel in self.options:
            self.selected = sel
        subscript("sound_investigate_menu_select")
    def k_down(self):
        coord = self.get_coord()
        coord[1]+=1
        if coord[1]>1:
            coord[1] = 0
        sel = self.opos_l[coord[1]][coord[0]]
        if sel in self.options:
            self.selected = sel
        subscript("sound_investigate_menu_select")
    def enter_down(self):
        if self.open_script:
            print "INITIALIZE MENU SCENE"
            assets.cur_script.init(self.scene+"."+self.selected)
        else:
            print "TRY TO JUMP TO LABEL"
            assets.cur_script.goto_result(self.selected,backup=self.fail)
        self.delete()
        subscript("sound_investigate_menu_confirm")
    def addm(self,opt):
        if opt:
            self.options.append(opt)
        if not self.selected:
            self.selected = opt
    def delm(self,opt):
        if opt in self.options:
            self.options.remove(opt)
            if self.selected == opt:
                self.selected = None
    def draw(self,dest):
        if not self.bg:
            for o in reversed(assets.cur_script.obs):
                if isinstance(o,bg):
                    self.bg = o.img.copy()
                    break
        self.screen_setting = "try_bottom"
        if self.bg:
            dest.blit(self.bg,self.getpos())
        if not hasattr(self,"fade") or self.fade>=self.max_fade:
            for o in self.options:
                if self.selected == o:
                    dest.blit(self.oimgshigh[o],[self.opos[o][0],self.opos[o][1]+self.getpos()[1]])
                else:
                    dest.blit(self.oimgs[o],[self.opos[o][0],self.opos[o][1]+self.getpos()[1]])

class listmenu(fadesprite,gui.widget):
    fail = "none"
    id_name = "list_menu_id"
    def over(self,mp):
        if getattr(self,"kill",0):
            return False
        x = (sw-self.choice.img.get_width())/2
        y = self.getpos()[1]+30
        si = None
        i = 0
        for c in self.options:
            if mp[0]>=x and mp[1]>=y and mp[0]<=x+self.choice.width and mp[1]<=y+self.choice.height:
                si = i
            i+=1
            y+=self.choice.img.get_height()+5
        return si
    def move_over(self,pos,rel,buttons):
        if getattr(self,"kill",0):
            return False
        if buttons[0]:
            self.click_down_over(pos)
    def click_down_over(self,mp):
        if getattr(self,"kill",0):
            return False
        gui.window.focused = self
        si = self.over(mp)
        if si is not None:
            self.si = si
            self.selected = self.options[self.si]
    def click_up(self,mp):
        if getattr(self,"kill",0):
            return False
        si = self.over(mp)
        if self.si==si and si is not None:
            self.enter_down()
            subscript("sound_list_menu_confirm")
    def __init__(self,tag=None):
        self.pri = ulayers.index(self.__class__.__name__)
        x,y = 0,192
        gui.widget.__init__(self,[x,y],[sw,sh])
        fadesprite.__init__(self,x=x,y=y)
        self.load(assets.variables.get("_list_bg_image","general/black"))
        self.max_fade = int(float(assets.variables.get("_menu_fade_level",50)))
        self.fade = 0
        if assets.num_screens == 2 and not vtrue(assets.variables.get("_double_screen_list_fade","false")):
            self.setfade(255)
        elif self.max_fade == 0:
            self.setfade(0)
        else:
            assets.cur_script.obs.append(fadeanim(start=0,end=self.max_fade,speed=3,wait=1,name=None,obs=[self]))
        self.options = []
        self.si = 0
        self.selected = ""
        self.choice = fadesprite().load("general/talkchoice")
        self.choice_high = fadesprite().load("general/talkchoice_high")
        self.hidden = True
        self.tag = tag
    def init_normal(self):
        subscript("show_court_record_button")
    def delete(self):
        subscript("hide_court_record_button")
        self.kill = 1
        if hasattr(self,"bck"):
            self.bck.kill = 1
    def update(self):
        fadesprite.update(self)
        self.screen_setting = "try_bottom"
        if self.hidden:
            return False
        if not hasattr(self,"bck") and vtrue(assets.variables.get("_list_back_button","true")) and not getattr(self,"noback",False):
            self.bck = guiBack()
            self.bck.pri = 1000
            def k_space(b=self.bck):
                self.delete()
                subscript("sound_list_menu_cancel")
                print "kill back button and self"
                assets.variables["_selected"] = "Back"
            self.bck.k_space = k_space
            assets.cur_script.obs.append(self.bck)
        if not self.options:
            self.k_space()
        return True
    def k_up(self):
        if getattr(self,"kill",0):
            return False
        self.si -= 1
        if self.si<0:
            self.si = len(self.options)-1
        self.selected = self.options[self.si]
        self.change_selected()
        subscript("sound_list_menu_select")
    def k_down(self):
        if getattr(self,"kill",0):
            return False
        self.si += 1
        if self.si>=len(self.options):
            self.si = 0
        self.selected = self.options[self.si]
        self.change_selected()
        subscript("sound_list_menu_select")
    def enter_down(self):
        if getattr(self,"kill",0):
            return False
        if not self.selected:
            return
        if self.tag:
            assets.lists[self.tag][self.selected["label"]] = 1
        if self.selected["result"] != "Back":
            assets.variables["_selected"] = self.selected["result"]
            assets.cur_script.goto_result(self.selected["result"],backup=self.fail)
        else:
            assets.variables["_selected"] = "Back"
        self.delete()
    def change_selected(self):
        scr = self.options[self.si].get("on_select",None)
        if scr:
            assets.cur_script.execute_macro(scr)
            #subscript(scr)
    def draw(self,dest):
        if getattr(self,"kill",0):
            return False
        if not self.selected and self.options:
            self.selected = self.options[self.si]
            self.change_selected()
        fadesprite.draw(self,dest)
        x = (sw-self.choice.img.get_width())/2
        y = self.getpos()[1]+30
        #self.choice.setfade(200)
        #self.choice_high.setfade(200)
        for c in self.options:
            if 0:#self.selected == c:
                img = self.choice_high.img.copy()
            else:
                img = self.choice.img.copy()
            rt = c["label"]
            checkmark = assets.variables.get("_list_checked_img","general/checkmark")
            if "checkmark" in c:
                checkmark = c["checkmark"]
            try:
                checkmark = sprite().load(checkmark)
            except:
                checkmark = None
            if (not (checkmark and checkmark.width)) and self.tag and assets.lists[self.tag].get(rt,None):
                rt = "("+rt+")"
            txt = assets.get_image_font("list").render(rt,[110,20,20])
            img.blit(txt,[(img.get_width()-txt.get_width())/2,
                (img.get_height()-txt.get_height())/2])
            dest.blit(img,[x,y])
            if self.selected == c:
                lwi = 2
                color = color_str(assets.variables.get("_list_outline_color","ffaa45"))
                pygame.draw.line(dest,color,[x-1,y+8],[x-1,y+1],lwi)
                pygame.draw.line(dest,color,[x+1,y-2],[x+8,y-2],lwi)
                
                pygame.draw.line(dest,color,[x+img.get_width(),y+8],[x+img.get_width(),y+1],lwi)
                pygame.draw.line(dest,color,[x+img.get_width()-2,y-2],[x+img.get_width()-9,y-2],lwi)
                
                pygame.draw.line(dest,color,[x+img.get_width(),y+img.get_height()-2],[x+img.get_width(),y+img.get_height()-9],lwi)
                pygame.draw.line(dest,color,[x+img.get_width()-2,y+img.get_height()],[x+img.get_width()-9,y+img.get_height()],lwi)
                
                pygame.draw.line(dest,color,[x-1,y+img.get_height()-2],[x-1,y+img.get_height()-9],lwi)
                pygame.draw.line(dest,color,[x+1,y+img.get_height()],[x+8,y+img.get_height()],lwi)
            if checkmark and checkmark.width and self.tag and assets.lists[self.tag].get(rt,None):
                if "check_x" in c:
                    cx = int(c["check_x"])
                else:
                    cx = int(assets.variables.get("_list_checked_x","-10"))
                if "check_y" in c:
                    cy = int(c["check_y"])
                else:
                    cy = int(assets.variables.get("_list_checked_y","-10"))
                dest.blit(checkmark.base[0],[x+cx,y+cy])
            y+=self.choice.img.get_height()+5
    def k_space(self):
        if getattr(self,"kill",0):
            return False
        if hasattr(self,"bck") or "Back" in self.options:
            self.delete()
            subscript("sound_list_menu_cancel")

class case_menu(fadesprite,gui.widget):
    children = []
    parent = None
    def click_down_over(self,mp):
        surf,pos = self.option_imgs[self.choice*3]
        new,npos = self.option_imgs[self.choice*3+1]
        save,spos = self.option_imgs[self.choice*3+2]
        pos = pos[:]
        pos[0]-=self.x
        if mp[0]<pos[0]:
            self.k_left()
        elif mp[0]>pos[0]+surf.get_width():
            self.k_right()
        else:
            if new and mp[1]>=npos[1] and mp[1]<=npos[1]+new.get_height():
                self.enter_down()
            elif save and mp[1]>=spos[1] and mp[1]<=spos[1]+save.get_height():
                assets.game = self.path+"/"+self.options[self.choice]
                assets.load_game_menu()
                #assets.load_game(self.path+"/"+self.options[self.choice])
    def get_script(self,fullpath):
        dname = os.path.split(fullpath)[1]
        for test in [[fullpath+"/intro.txt","intro"],[fullpath+"/"+dname+".txt",dname]]:
            if os.path.exists(test[0]):
                return test[1]
    def __init__(self,path="games",**kwargs):
        self.pri = kwargs.get("pri",ulayers.index(self.__class__.__name__))
        self.reload=False
        self.path = path
        fadesprite.__init__(self,screen=2)
        self.base = self.img = assets.Surface([64,64])
        self.max_fade = 150
        self.next = 0
        self.width = sw
        self.height = sh
        self.options = []
        order = assets.variables.get("_order_cases","alphabetical")
        if order=="alphabetical":
            for d in os.listdir(path):
                full = os.path.join(path,d)
                if os.path.isdir(full):
                    if self.get_script(full):
                        self.options.append(d)
            self.options.sort()
        elif order=="variable":
            opts = {}
            for v in assets.variables.keys():
                if v.startswith("_case_"):
                    try:
                        num = int(v[6:])
                        opts[num] = assets.variables[v]
                    except:
                        continue
            self.options = []
            keys = opts.keys()
            keys.sort()
            for k in keys:
                self.options.append(opts[k])
        else:
            raise script_error("_order_cases set to '%s',"%(order,)+\
                                    "only valid values are 'alphabetical' or "+\
                                    "'variable'")
        self.init_options()
        self.choice = 0
        self.x = 0
        try:
            f = open(path+"/last")
            self.choice = int(f.readlines()[0].strip())
            f.close()
        except:
            pass
        if self.choice>=len(self.options):
            self.choice = 0
        self.scrolling = False
        self.arr = assets.open_art("general/arrow_right")[0]
        self.tried_case = False
    def init_options(self):
        self.option_imgs = []
        base = assets.open_art("general/selection_chapter")[0].convert()
        x = self.pos[0]+sw/2-base.get_width()/2
        y = self.pos[1]+sh/2-base.get_height()/2
        for o in self.options:
            spr = base.copy()
            
            title = o.replace("_"," ")
            lines = [[]]
            wd_sp = 2
            for word in title.split(" "):
                word = assets.get_font("gametitle").render(word,1,[200,100,100])
                if sum([wd.get_width() for wd in lines[-1]])+wd_sp*len(lines[-1])+word.get_width()>160:
                    lines.append([])
                lines[-1].append(word)
            wd_y = spr.get_height()//2-(len(lines)*16)//2
            for line in lines:
                w = sum([wd.get_width() for wd in line])+wd_sp*len(line)
                wd_x = (spr.get_width()-w)/2
                for word in line:
                    spr.blit(word,[wd_x,wd_y])
                    wd_x += word.get_width()+wd_sp
                wd_y += 16
            self.option_imgs.append([spr,[x,y]])
            
            fnt = assets.get_font("new_resume")
            txt = fnt.render("New game",1,[200,100,100])
            spr = pygame.transform.scale(base,[base.get_width(),base.get_height()//2])
            spr.blit(txt,[(spr.get_width()-txt.get_width())/2,(spr.get_height()-txt.get_height())/2])
            self.option_imgs.append([spr,[x,y+60]])
            if os.path.exists(self.path+"/"+o+"/save.ns"):
                txt = fnt.render("Resume Game",1,[200,100,100])
                spr = pygame.transform.scale(base,[base.get_width(),base.get_height()//2])
                spr.blit(txt,[(spr.get_width()-txt.get_width())/2,(spr.get_height()-txt.get_height())/2])
                self.option_imgs.append([spr,[x,y+90]])
            elif os.path.exists(self.path+"/"+o+"/save"):
                txt = fnt.render("Resume Game",1,[200,100,100])
                spr = pygame.transform.scale(base,[base.get_width(),base.get_height()//2])
                spr.blit(txt,[(spr.get_width()-txt.get_width())/2,(spr.get_height()-txt.get_height())/2])
                self.option_imgs.append([spr,[x,y+90]])
            elif os.path.exists(self.path+"/"+o+"/autosave.ns"):
                txt = fnt.render("Resume Game",1,[200,100,100])
                spr = pygame.transform.scale(base,[base.get_width(),base.get_height()//2])
                spr.blit(txt,[(spr.get_width()-txt.get_width())/2,(spr.get_height()-txt.get_height())/2])
                self.option_imgs.append([spr,[x,y+90]])
            else:
                self.option_imgs.append([None,None])
            x+=sw
        self.children = self.option_imgs
    def update(self):
        if self.reload:
            self.option_imgs = []
            self.__init__(self.path)
        spd = (self.choice*256-self.x)/25.0
        if abs(spd)>0 and abs(spd)<10:
            spd = 10*abs(spd)/spd
        spd *= assets.dt
        if self.x<self.choice*sw:
            self.x+=spd
            if self.x>self.choice*sw:
                self.x=self.choice*sw
        if self.x>self.choice*sw:
            self.x+=spd
            if self.x<self.choice*sw:
                self.x=self.choice*sw
        return True
    def k_right(self):
        if self.choice<len(self.options)-1:
            self.choice += 1
        self.case_screen()
        subscript("sound_case_menu_select")
    def k_left(self):
        if self.choice>0:
            self.choice -= 1
        self.case_screen()
        subscript("sound_case_menu_select")
    def case_screen(self):
        if not self.options:
            return
        if not hasattr(self,"curgame"):
            self.curgame = assets.game
        if os.path.exists(os.path.join(self.path,self.options[self.choice],"case_screen.txt")):
            scr = assets.Script()
            scr.parent = assets.cur_script
            assets.stack.append(scr)
            assets.game=self.curgame+"/"+self.options[self.choice]
            assets.registry = registry.combine_registries("./"+assets.game,assets.show_load)
            print "init: g:%s choice:%s"%(assets.game,self.options[self.choice])
            assets.cur_script.init("case_screen")
            assets.cur_script.world = scr.parent.world
    def enter_down(self):
        f = open(os.path.join(self.path,"last"),"w")
        f.write(str(self.choice))
        f.close()
        assets.start_game(self.path+"/"+self.options[self.choice],mode="nomenu")
    def draw(self,dest):
        if self.reload:
            return
        if not self.tried_case:
            self.case_screen()
            self.tried_case = 1
        for s,p in self.option_imgs:
            if not s: continue
            dest.blit(s,[p[0]-self.x,p[1]])
        if self.x==self.choice*sw:
            if self.choice<len(self.options)-1:
                dest.blit(self.arr,[self.pos[0]+240,self.pos[1]+80])
            if self.choice>0:
                dest.blit(pygame.transform.flip(self.arr,1,0),[self.pos[0],self.pos[1]+80])
            
class examine_menu(sprite,gui.widget):
    fail = "none"
    def move_over(self,pos,rel,buttons):
        if gui.window.focused == self:
            self.mx,self.my = [pos[0],pos[1]-self.getpos()[1]]
            self.highlight()
    def click_down_over(self,mp):
        gui.window.focused = self
        if self.hide or self.selected == ["none"] or mp[0]<175 or mp[1]<159+self.getpos()[1]:
            self.move_over(mp,None,None)
    def click_up(self,mp):
        if gui.window.focused == self:
            self.enter_down()
            gui.window.over = None
            gui.window.focused = None
    def __init__(self,hide=False,name="blah"):
        self.name = name
        self.pri = ulayers.index(self.__class__.__name__)
        sprite.__init__(self)
        self.pos = [0,192]
        self.z = zlayers.index(self.__class__.__name__)
        self.width = sw
        self.height = sh
        gui.widget.__init__(self,self.pos,[sw,sh])
        self.img = assets.Surface([64,64])
        self.regions = []
        self.mouse = pygame.Surface([10,10])
        self.mouse.fill([100,100,100])
        self.selected = [None]
        self.mx,self.my = sw/2,sh/2
        self.check = assets.open_art("general/check"+assets.appendgba,key=[255,0,255])[0]
        self.hide = hide
        self.bg = []
        if not assets.variables.get("_examine_use",None):
            self.bg = [x for x in assets.cur_script.obs if isinstance(x,bg)]
        else:
            self.bg = [x for x in assets.cur_script.obs if getattr(x,"id_name",None) == assets.variables["_examine_use"]]
        self.fg = assets.open_art("general/examinefg")[0]
        self.xscroll = 0
        self.xscrolling = 0
        scroll_amt = assets.variables.get("_xscroll_"+self.name,0)
        if scroll_amt==-1:
            self.xscroll = -1
            if self.getoffset()!=-256:
                assets.cur_script.obs.append(scroll(amtx=-256,amty=0,speed=256))
        self.blocking = not vtrue(assets.variables.get("_examine_skipupdate","0"))
        self.screen_setting = "try_bottom"
    def init_normal(self):
        subscript("show_court_record_button")
    def delete(self):
        self.kill = 1
        if hasattr(self,"bck"):
            self.bck.delete()
        if hasattr(self,"scrollbut"):
            self.scrollbut.delete()
        subscript("hide_court_record_button")
    def getoffset(self):
        x = [o.pos[0] for o in self.bg]
        if not x:
            return 0
        x.sort()
        return x[0]
    def screens(self):
        screens = 1
        xes = [o.pos[0] for o in self.bg]
        xes.sort()
        smallest = 0
        if xes:
            smallest = xes[0]
        for mx in xes:
            x = mx-smallest
            if x>=sw and screens<2:
                screens = 2
            if x>=sw*2 and screens<3:
                screens = 3
        xes = [o[0] for o in self.regions]
        xes.sort()
        smallest = 0
        if xes:
            smallest = xes[0]
        for mx in xes:
            x = mx-smallest
            if x>=sw and screens<2:
                screens = 2
            if x>=sw*2 and screens<3:
                screens = 3
        self.width = screens*sw
        return screens
    def addregion(self,x,y,width,height,label):
        reg = [int(x),int(y),int(width),int(height),label]
        self.regions.append(reg)
        self.highlight()
    def highlight(self):
        self.selected = [None]
        for reg in self.regions:
            if self.mx>reg[0]+self.getoffset() and self.my>reg[1] and \
            self.mx<reg[0]+self.getoffset()+reg[2] and self.my<reg[1]+reg[3]:
                self.selected = reg
                return
    def draw(self,dest):
        self.highlight()
        if not assets.variables.get("_examine_use",None):
            [dest.blit(o.img,[o.pos[0],o.pos[1]+self.getpos()[1]]) for o in self.bg]
        my = self.my+self.getpos()[1]
        if vtrue(assets.variables.get("_examine_showcursor", "true")):
            if assets.variables.get("_examine_cursor_img","").strip():
                spr = sprite(0,0)
                spr.load(assets.variables.get("_examine_cursor_img",""))
                spr.pos[0] = self.mx-spr.width//2
                spr.pos[1] = my-spr.height//2
                spr.draw(dest)
            else:
                col = color_str(assets.variables.get("_examine_cursor_col","FFFFFF"))
                pygame.draw.line(dest,col,[0,my],[self.mx-5,my])
                pygame.draw.line(dest,col,[self.mx+5,my],[sw,my])
                pygame.draw.line(dest,col,[self.mx,self.getpos()[1]],[self.mx,my-5])
                pygame.draw.line(dest,col,[self.mx,my+5],[self.mx,self.getpos()[1]+sh])
                pygame.draw.rect(dest,col,[[self.mx-5,my-5],[10,10]],1)
        if vtrue(assets.variables.get("_examine_showbars", "true")):
            dest.blit(self.fg,[0,self.getpos()[1]])
        if self.selected != [None] and not self.hide:
            dest.blit(self.check,[sw-self.check.get_width()+3,self.getpos()[1]+sh-self.check.get_height()])
        #~ if vtrue(assets.variables.get("_debug","false")):
            #~ x = int(assets.variables.get("_examine_offsetx",0))
            #~ y = int(assets.variables.get("_examine_offsety",0))
            #~ tb = textblock("offsetx:%s offsety%s"%(x,y),[0,192],[256,20],[255,255,255])
            #~ tb.draw(dest)
    def update(self,*args):
        if self.xscrolling:
            assets.cur_script.obs.append(scroll(-self.xscrolling,0,speed=16))
            self.xscrolling = 0
            if hasattr(self,"scrollbut"):
                self.scrollbut.delete()
                del self.scrollbut
            return self.blocking
        keys = pygame.key.get_pressed()
        spd = 3*assets.dt
        d = [0,0]
        if keys[pygame.K_LEFT] or pygame.jsleft():
            d[0]-=spd
        if keys[pygame.K_RIGHT] or pygame.jsright():
            d[0]+=spd
        if keys[pygame.K_UP] or pygame.jsup():
            d[1]-=spd
        if keys[pygame.K_DOWN] or pygame.jsdown():
            d[1]+=spd
        self.mx+=d[0]
        self.my+=d[1]
        if self.mx-5<0: self.mx=5
        if self.mx+5>sw: self.mx=sw-5
        if self.my-5<0: self.my=5
        if self.my+5>sh: self.my=sh-5
        if assets.variables.get("_examine_scrolling",None)=="perceive":
            def add(x):
                x.pos[0]-=d[0]
                x.pos[1]-=d[1]
            [add(x) for x in self.bg]
            x = float(assets.variables.get("_examine_offsetx",0))
            y = float(assets.variables.get("_examine_offsety",0))
            x-=d[0]
            y-=d[1]
            assets.variables["_examine_offsetx"] = str(x)
            assets.variables["_examine_offsety"] = str(y)
            self.highlight()
            return False
        self.highlight()
        if not hasattr(self,"bck") and not self.hide:
            self.bck = guiBack()
            self.bck.pri = 1000
            def k_space(b=self.bck):
                self.k_space()
            self.bck.k_space = k_space
            self.bck.update = lambda *x: False
            assets.cur_script.obs.append(self.bck)
        scrn = (-self.getoffset()//sw)+1
        self.xscroll = None
        if scrn<self.screens():
            self.xscroll = 1
        elif scrn>1:
            self.xscroll = -1
        if not self.xscroll and hasattr(self,"scrollbut"): 
            self.scrollbut.delete()
            del self.scrollbut
        if self.xscroll and not hasattr(self,"scrollbut"):
            self.scrollbut = guiScroll(self.xscroll)
            self.scrollbut.parent = self
            assets.cur_script.obs.append(self.scrollbut)
        assets.variables["_xscroll_"+self.name] = self.xscroll
        return self.blocking
    def enter_down(self):
        print self.selected,self.regions,self.mx,self.my
        assets.variables["_examine_clickx"] = str(self.mx)
        assets.variables["_examine_clicky"] = str(self.my)
        print "FAIL ",self.fail
        go = self.selected[-1]
        if go == None:
            go = self.fail
        print assets.cur_script,"goto",go
        assets.cur_script.goto_result(go,backup=self.fail)
        self.delete()
    def k_space(self):
        if not self.hide:
            self.delete()
            subscript("sound_examine_menu_cancel")

class evidence_menu(fadesprite,gui.widget):
    fail = "none"
    def click_down_over(self,mp):
        gui.window.focused = self
    def hold_down_over(self,mp):
        pass
    def move_over(self,mp,rel,buttons):
        pass
    def click_up(self,mp):
        mp[1]-=self.getpos()[1]
        if self.mode == "overview" and mp[0]>=36 and mp[1]>=62 and mp[0]<=218 and mp[1]<=145:
            rx = (218-36)//4
            ry = (145-62)//2
            sx,sy = self.sx,self.sy
            self.sx = (mp[0]-36)/rx
            self.sy = (mp[1]-62)/ry
            try:
                self.choose()
            except:
                self.sx,self.sy = sx,sy
                return
            self.back = False
            self.back_button.unhighlight()
            self.enter_down()
        if mp[0]>=0 and mp[0]<=78 and mp[1]>=162 and mp[1]<=192:
            if self.canback():
                self.back = True
                self.enter_down()
                self.back = False
                self.back_button.unhighlight()
            #self.sx,self.sy = [0,0]
        if mp[0]>=0 and mp[1]>=56 and mp[0]<=16 and mp[1]<=149:
            if self.mode=="overview" and len(self.pages)>1:
                self.page_prev()
                subscript("sound_court_record_scroll")
            if self.mode=="zoomed":
                self.k_left()
        if mp[0]>=238 and mp[1]>=56 and mp[1]<=149:
            if self.mode=="overview" and len(self.pages)>1:
                self.page_next()
                subscript("sound_court_record_scroll")
            if self.mode=="zoomed":
                self.k_right()
        if mp[0]>=177 and mp[1]<=29:
            self.switch = True
            self.enter_down()
            self.switch = False
        check = assets.open_art("general/check"+assets.appendgba)[0]
        chk = [sw-check.get_width(),sh-check.get_height()]
        if mp[0]>=chk[0] and mp[1]>=chk[1]:
            self.do_check()
        #~ self.enter_down()
        #~ gui.window.over = None
        #~ gui.window.focused = None
    def load(self,*args,**kwargs):
        fadesprite.load(self,*args,**kwargs)
    def __init__(self,items=[],gba=True):
        subscript("sound_court_record_display")
        self.pri = ulayers.index(self.__class__.__name__)
        x,y = 0,192
        self.z = zlayers.index(self.__class__.__name__)
        print "evidence z",self.z
        fadesprite.__init__(self,x=x,y=y)
        gui.widget.__init__(self,[x,y],[sw,sh])
        self.items = items
        self.load(assets.variables["ev_mode_bg_evidence"]+assets.appendgba)
        self.cursor = assets.open_art(assets.variables["ev_cursor_img"])[0]
        self.page = 0
        self.sx,self.sy = [0,0]
        self.examine = None
        self.present = None
        
        self.back_button = guiBack()
        self.back_button.pri = 1000
        def k_space(b=self.back_button):
            b.delete()
            self.delete()
            assets.variables["_selected"] = "Back"
        self.back_button.k_space = k_space
        
        self.back = False
        self.switch = False
        self.chosen = None
        self.mode = "overview"  #overview, zoomed, check
        if assets.gbamode: self.mode = "zoomed"
        self.checking = None
        self.ev_zoom = assets.open_art(assets.variables["ev_z_bg"]+assets.appendgba)[0]
        self.scroll = 0
        self.scroll_dir = 0
        
        self.pages_set = assets.variables.get("_ev_pages","evidence profiles").split(" ")
        for p in self.pages_set[:]:
            if not vtrue(assets.variables.get("_%s_enabled"%p,"true")):
                self.pages_set.remove(p)
        if not self.pages_set:
            self.delete()
            
        #Loading saved position
        self.item_set = assets.variables.get("_cr_current_item_set",self.pages_set[0])
        self.layout()
        if not self.pages:
            self.item_set = self.pages_set[0]
            self.layout()
        self.page = int(assets.variables.get("_cr_current_page",0))
        self.sx = int(assets.variables.get("_cr_current_selected_x",0))
        self.sy = int(assets.variables.get("_cr_current_selected_y",0))
        
        self.screen_setting = "try_bottom"
    def delete(self):
        super(evidence_menu,self).delete()
        subscript("hide_present_button2")
    def update(self):
        self.choose()
        if not getattr(self,"hidden",None):
            return True #Don't update anything else
    def layout(self):
        self.pages = []
        lines = []
        line = []
        for icon in self.items:
            icon.reload()
            if self.item_set != icon.page:
                continue
            line.append(icon)
            if len(line)==4:
                lines.append(line)
                line = []
                if len(lines)==2:
                    self.pages.append(lines)
                    lines = []
        if line:
            lines.append(line)
        if lines:
            self.pages.append(lines)
        self.page = 0
        self.sx = 0
        self.sy = 0
    def remember_vars(self):
        assets.variables.set("_cr_current_item_set",self.item_set)
        assets.variables.set("_cr_current_page",self.page)
        assets.variables.set("_cr_current_selected_x",self.sx)
        assets.variables.set("_cr_current_selected_y",self.sy)
    def page_prev(self):
        self.page-=1
        if self.page<0:
            self.page = len(self.pages)-1
        page = self.pages[self.page]
        self.sy = len(page)-1
        self.sx = len(page[self.sy])-1
        self.remember_vars()
    def page_next(self):
        self.page += 1
        if self.page>len(self.pages)-1:
            self.page = 0
        self.sx = 0
        page = self.pages[self.page]
        if self.sy>len(page)-1:
            self.sy = 0
        self.remember_vars()
    def set_bg(self):
        defbg = assets.variables["ev_mode_bg_evidence"]
        bg = assets.variables.get("ev_mode_bg_"+self.item_set,defbg)
        self.load(bg+assets.appendgba)
    def k_left(self):
        if self.page>=len(self.pages): return
        self.set_bg()
        self.back = False
        self.back_button.unhighlight()
        self.sx-=1
        if self.mode == "overview":
            if self.sx<0:
                self.page_prev()
            page = self.pages[self.page]
            if self.sy>len(page)-1:
                self.sy = 0
            while self.sx>len(page[self.sy])-1 and self.sx>0:
                self.sx -= 1
            subscript("sound_court_record_scroll")
        elif self.mode == "zoomed":
            if self.sx<0 and self.sy>0:
                self.sx = 3
                self.sy -= 1
            if self.sx<0 and self.sy==0:
                self.page_prev()
            self.lastchoose = self.chosen_icon
            scroll = 0
            for p in self.pages:
                for line in p:
                    for icon in line:
                        scroll += 1
            if scroll>1:
                self.scroll = 256
                self.scroll_dir = 1
            subscript("sound_court_record_scroll_zoomed")
        self.choose()
    def k_right(self):
        if self.page>=len(self.pages): return
        self.set_bg()
        self.back = False
        self.back_button.unhighlight()
        self.sx+=1
        if self.mode == "overview":
            page = self.pages[self.page]
            if self.sy>len(page)-1 or self.sx>len(page[self.sy])-1:
                self.page += 1
                if self.page>len(self.pages)-1:
                    self.page = 0
                self.sx = 0
            page = self.pages[self.page]
            if self.sy>len(page)-1:
                self.sy = 0
            subscript("sound_court_record_scroll")
        elif self.mode == "zoomed":
            page = self.pages[self.page]
            if self.sx>len(page[self.sy])-1:
                self.sy += 1
                self.sx = 0
            if self.sy>len(page)-1:
                self.sx = 0
                self.sy = 0
                self.page+=1
                if self.page>=len(self.pages):
                    self.page= 0
            self.lastchoose = self.chosen_icon
            scroll = 0
            for p in self.pages:
                for line in p:
                    for icon in line:
                        scroll += 1
            if scroll>1:
                self.scroll = 256
                self.scroll_dir = -1
            subscript("sound_court_record_scroll_zoomed")
        self.choose()
    def k_up(self):
        self.set_bg()
        if self.mode == "overview":
            if self.sy == 0:
                self.switch = True
            elif self.sy==1:
                self.sy = 0
            if self.back:
                self.sy = 1
            if self.page>=len(self.pages) or self.sy>len(self.pages[self.page])-1:
                self.sy = 0
            subscript("sound_court_record_scroll")
        elif not self.back:
            self.switch = True
        self.back = False
        self.back_button.unhighlight()
        self.choose()
    def k_down(self):
        self.set_bg()
        if self.mode == "overview":
            self.back = False
            self.back_button.unhighlight()
            if not self.switch:
                self.sy+=1
            self.switch = False
            if self.page>=len(self.pages) or self.sy>=len(self.pages[self.page]) and self.canback():
                self.back = True
                self.back_button.highlight()
            subscript("sound_court_record_scroll")
        elif self.mode == "zoomed":
            if self.switch == False and self.canback():
                self.back = True
                self.back_button.highlight()
            self.switch = False
        self.choose()
    def choose(self):
        itback = assets.variables.get("ev_mode_bg_"+self.item_set,None)
        if not itback:
            itback = assets.variables.get("ev_mode_bg_evidence",None)
        if self.back and self.canback():
            self.load(itback+"_back"+assets.appendgba)
        elif self.switch:
            self.load(itback+"_profile"+assets.appendgba)
        else:
            self.load(itback+assets.appendgba)
        if self.back or self.switch or self.page>=len(self.pages):
            pass
        else:
            if self.sy>=len(self.pages[self.page]): self.sy = 0
            if self.sx>len(self.pages[self.page][self.sy]): self.sx = len(self.pages[self.page][self.sy])-1
            page = self.pages[self.page]
            row = page[self.sy]
            if self.sx>=len(row): self.sx = len(row)-1
            col = row[self.sx]
            self.chosen = col.id
            self.chosen_icon = col
        self.remember_vars()
    def enter_down(self):
        if self.switch:
            self.k_z()
        elif self.back and self.canback():
            subscript("sound_court_record_cancel")
            if self.mode == "overview":
                self.delete()
            elif self.mode == "zoomed":
                if assets.gbamode: self.delete()
                else: self.mode = "overview"
            elif self.mode == "check":
                self.mode = "overview"
        else:
            if self.mode == "overview":
                self.mode = "zoomed"
                subscript("sound_court_record_zoom")
            elif self.mode == "zoomed":
                #make sure we can check first
                #self.mode = "check"
                #self.mode = "overview"
                self.do_check()
    def do_check(self):
        if not self.chosen: return
        assets.variables["_selected"] = self.chosen
        chk = assets.variables.get(self.chosen+"_check",None)
        if chk:
            assets.addscene(chk)
            subscript("sound_court_record_check")
    def can_present(self):
        if not vtrue(assets.variables.get("_"+self.item_set+"_present","true")):
            #print "_"+self.item_set+"_present","is false"
            return
        if not self.chosen: 
            #print "nothing chosen"
            return
        if self.back or self.switch: 
            #print "have back or switch",self.back,self.switch
            return
        if not assets.cur_script.cross=="proceed":
            #print "no cur_script.cross"
            return
        if not vtrue(assets.variables.get("_allow_present_"+self.item_set,"true")):
            #print "_allow_present_"+self.item_set,"is false"
            return
        if not vtrue(assets.variables.get(self.chosen+"_presentable","true")):
            #print self.chosen+"_presentable","is false"
            return
        return True
    def k_x(self):
        if not self.can_present(): return
        assets.variables["_selected"] = self.chosen
        assets.cur_script.cross = "presenting"
        self.delete()
        for o in assets.cur_script.obs:
            if isinstance(o,textbox):
                o.delete()
            if isinstance(o,uglyarrow):
                o.delete()
        assets.cur_script.goto_result((self.chosen+" "+assets.cur_script.statement).strip(),backup=self.fail)
    def next_screen(self):
        if len(self.pages_set)==1:
            return ""
        cur = self.pages_set.index(self.item_set)
        cur += 1
        if cur>=len(self.pages_set):
            cur = 0
        return self.pages_set[cur]
    def k_z(self):
        if len(self.pages_set)==1:
            return
        self.chosen = None
        self.item_set = self.next_screen()
        self.layout()
        self.remember_vars()
        #if not self.pages: self.item_set = modes[self.item_set]
        #self.layout()
        self.switch = False
        subscript("sound_court_record_switch")
    def k_space(self):
        subscript("sound_court_record_cancel")
        if self.mode=="zoomed":
            if assets.gbamode: self.delete()
            else: self.mode = "overview"
        elif self.canback():
            self.delete()
        #assets.cur_script.cross = ""
        #assets.cur_script.instatement = False
    def canback(self):
        show_back = vtrue(assets.variables.get("_cr_back_button", "true")) and not getattr(self,"noback",False)
        if self.mode!="overview" or show_back:
            return True
        return False
    def draw(self,dest):
        if assets.gbamode: self.mode = "zoomed"
        pos = self.getpos()
        dest.blit(self.img,pos)
        x,y=pos
        if not assets.gbamode:
            if vtrue(assets.variables["ev_show_mode_text"]):
                dest.blit(assets.get_image_font("itemset").render(self.item_set.capitalize(),[255,255,255]),
                [x+int(assets.variables["ev_mode_x"]),y+int(assets.variables["ev_mode_y"])])
        name = ""
        if self.chosen:
            name = assets.variables.get(self.chosen+"_name",self.chosen).replace("$","")
        if not assets.gbamode or self.mode != "zoomed":
            dest.blit(assets.get_image_font("itemname").render(name,[255,255,255]),
            [x+int(assets.variables["ev_currentname_x"]),y+int(assets.variables["ev_currentname_y"])])
        if vtrue(assets.variables.get("_evidence_enabled","true")) and vtrue(assets.variables.get("_profiles_enabled","true")):
            dest.blit(assets.get_font("itemset_big").render(
                self.next_screen().capitalize(),1,[255,255,255]),
                [x+int(assets.variables["ev_modebutton_x"]),y+int(assets.variables["ev_modebutton_y"])])
        page = []
        if self.pages:
            page = self.pages[self.page]
        if self.mode != "zoomed":
            cx,cy=0,0
            sx = pos[0]+int(assets.variables["ev_items_x"])
            sy = pos[1]+int(assets.variables["ev_items_y"])
            x,y = sx,sy
            w = int(assets.variables["ev_spacing_x"])
            h = int(assets.variables["ev_spacing_y"])
            for line in page:
                for icon in line:
                    icon.reload()
                    if not icon.small:
                        continue
                    dest.blit(icon.small,[x,y])
                    if not self.back and not self.switch and self.sx == cx and self.sy == cy:
                        dest.blit(self.cursor,[x-4,y-4])
                    x+=w
                    cx+=1
                x=sx
                cx=0
                y+=h
                cy+=1
            if len(self.pages)>1:
                arr = assets.open_art(assets.variables["ev_arrow_img"])[0]
                dest.blit(arr,[pos[0]+int(assets.variables["ev_rarrow_x"]),
                            pos[1]+int(assets.variables["ev_rarrow_y"])])
                dest.blit(pygame.transform.flip(arr,1,0),
                    [pos[0]+int(assets.variables["ev_larrow_x"]),
                    pos[1]+int(assets.variables["ev_larrow_y"])])
        if self.mode == "zoomed":
            showarrow = 0
            for p in self.pages:
                for line in p:
                    for icon in line:
                        showarrow += 1
            if showarrow>1:
                if not getattr(self,"arr",None):
                    self.arr = assets.open_art(assets.variables["ev_zarrow_img"])[0]
                dest.blit(self.arr,[pos[0]+int(assets.variables["ev_zrarrow_x"]),
                                pos[1]+int(assets.variables["ev_zrarrow_y"])])
                dest.blit(pygame.transform.flip(self.arr,1,0),
                    [pos[0]+int(assets.variables["ev_zlarrow_x"]),
                    pos[1]+int(assets.variables["ev_zlarrow_y"])])
            if getattr(self,"chosen_icon",None) and getattr(self,"chosen",None):
                if self.scroll:
                    self.scroll -= 16*assets.dt
                    if self.scroll<0:
                        self.scroll=0
                    self.draw_ev_zoom(self.lastchoose,[(256-self.scroll+pos[0])*self.scroll_dir,pos[1]],dest)
                    self.draw_ev_zoom(self.chosen_icon,[256*(-self.scroll_dir)+(256-self.scroll+pos[0])*self.scroll_dir,pos[1]],dest)
                else:
                    self.draw_ev_zoom(self.chosen_icon,pos[:],dest)
                chk = assets.variables.get(self.chosen+"_check",None)
                if chk:
                    check = assets.open_art(assets.variables["ev_check_img"]+assets.appendgba)[0]
                    dest.blit(check,[pos[0]+sw-check.get_width(),pos[1]+sh-check.get_height()])
            else:
                self.mode = "overview"
        if self.canback():
            self.back_button.draw(dest)
        #present button
        if not hasattr(self,"present_button"):
            self.present_button = False
        if self.can_present():
            if not self.present_button:
                subscript("show_present_button2")
                self.present_button = True
        else:
            if self.present_button:
                subscript("hide_present_button2")
                self.present_button = False
    def draw_ev_zoom(self,icon,pos,surf):
        if not hasattr(self,icon.id+"_zoom_"+str(assets.gbamode)):
            if assets.gbamode:
                back_pos = [28,62]; tbpos = [106,78]; tbsize = [120,50]
            else:
                back_pos = [int(assets.variables["ev_z_icon_x"]),
                    int(assets.variables["ev_z_icon_y"])];
                tbpos = [int(assets.variables["ev_z_textbox_x"]),
                    int(assets.variables["ev_z_textbox_y"])];
                tbsize = [int(assets.variables["ev_z_textbox_w"]),
                    int(assets.variables["ev_z_textbox_h"])]
            newsurf = assets.Surface([sw,sh]).convert_alpha()
            newsurf.fill([0,0,0,0])
            if assets.gbamode:
                pos[1]-=10
            newsurf.blit(self.ev_zoom,[int(assets.variables["ev_z_bg_x"]),
                                    int(assets.variables["ev_z_bg_y"])])
            name = icon.name
            if assets.gbamode:
                newsurf.blit(assets.get_image_font("itemname").render(name,[255,255,0]),[103,65])
            tb = textblock(icon.desc,[tbpos[0],tbpos[1]],tbsize,color_str(assets.variables["ev_z_text_col"]))
            newsurf.blit(icon.scaled,[back_pos[0],back_pos[1]])
            tb.pos = [tbpos[0],tbpos[1]]
            tb.draw(newsurf)
            setattr(self,icon.id+"_zoom_"+str(assets.gbamode),newsurf)
        else:
            newsurf = getattr(self,icon.id+"_zoom_"+str(assets.gbamode))
        surf.blit(newsurf,pos)
        
class textblock(sprite):
    autoclear = True
    def __init__(self,text="",pos=[0,0],size=[100,100],color=[255,255,255],surf=None):
        super(textblock,self).__init__()
        self.text = text
        self.lines = [x.split(" ") for x in text.split("{n}")]
        self.pos = pos
        self.size = size
        self.surf = surf
        self.color = color
        self.width,self.height = self.size
    def update(self):
        pass
    def draw(self,dest):
        x = self.pos[0]
        y = self.pos[1]
        i = 0
        for line in self.lines:
            for word in line:
                nl = False
                if word.strip():
                    wordi = assets.get_font("block").render(word,1,self.color)
                else:
                    wordi = pygame.Surface([4,10]).convert_alpha()
                    wordi.fill([0,0,0,0])
                if wordi.get_width()+x>self.pos[0]+self.size[0] or nl:
                    x = self.pos[0]
                    y += 10
                if y>self.pos[1]+self.size[1]:
                    break
                dest.blit(wordi,[x,y])
                x += wordi.get_width()+4
                i += 1
            x = self.pos[0]
            y += 10
            
class waitenter(sprite):
    def __init__(self):
        super(waitenter,self).__init__()
        self.pri = ulayers.index(self.__class__.__name__)
    def draw(self,dest): pass
    def update(self):
        return True
    def enter_down(self):
        self.delete()
                
class delay(sprite):
    def __init__(self,ticks=1):
        super(delay,self).__init__()
        self.ticks = abs(ticks)
        self.pri = ulayers.index(self.__class__.__name__)
    def draw(self,dest): pass
    def update(self):
        if self.ticks<=0:
            self.delete()
            return False
        self.ticks-=assets.dt
        return True
        
class timer(sprite):
    def __init__(self,ticks=1,run=None):
        sprite.__init__(self)
        self.ticks = abs(ticks)
        self.pri = ulayers.index(self.__class__.__name__)
        self.run = run
        self.script = assets.cur_script
    def update(self):
        self.ticks-=assets.dt
        assets.variables["_timer_value_"+self.run] = str(self.ticks)
        if self.ticks<=0:
            self.delete()
            if self.run:
                ns = self.script.execute_macro(self.run)
        
class effect(object):
    id_name = "_effect_"
    def __init__(self):
        self.z = zlayers.index(self.__class__.__name__)
    def delete(self):
        self.kill = 1
                
class scroll(effect):
    def __init__(self,amtx=1,amty=1,amtz=1,speed=1,wait=1,filter="top",ramp=-.005):
        super(scroll,self).__init__()
        self.aamtx,self.aamty,self.aamtz = amtx,amty,amtz
        self.amtx = abs(amtx)
        self.amty = abs(amty)
        self.amtz = abs(amtz)
        self.ramp = ramp
        self.dx=self.dy=self.dz=0
        if amtx==0 and amty: 
            self.dy=amty/abs(amty)
        elif amty==0 and amtx:
            self.dx = amtx/abs(amtx)
        elif amty==amtx==0:
            pass
        else:
            slope = amty/float(amtx)
            if abs(amtx)>abs(amty):
                self.dx = amtx/abs(amtx)
                self.dy = amty/float(abs(amtx))
            elif abs(amty)>abs(amtx):
                self.dx = amtx/float(abs(amty))
                self.dy = amty/abs(amty)
            else:
                self.dx=amtx/abs(amtx)
                self.dy=amty/abs(amty)
        if amtz:
            self.dz = (amtz)/abs(amtz)*speed
        self.dx*=speed
        self.dy*=speed
        self.pri = ulayers.index(self.__class__.__name__)
        self.speed = speed
        self.obs = assets.cur_script.obs
        self.filter = filter
        self.wait = wait
        self.initialized = False
    def draw(self,dest): pass
    def init_scroll(self):
        if self.initialized:
            return
        self.initialized = True
        self.stuff = []
        for o in self.obs:
            if not hasattr(o,"pos"):
                continue
            if self.filter=="top" and o.pos[1]>=192:
                continue
            if self.filter=="bottom" and o.pos[1]<192:
                continue
            d = {"ob":o,"start":None,"end":None}
            if hasattr(o,"pos"):
                d["start"] = o.pos[:]
                d["end"] = [int(o.pos[0]+self.aamtx),int(o.pos[1]+self.aamty)]
            self.stuff.append(d)
    def update(self):
        self.init_scroll()
        ndx,ndy,ndz = self.dx*assets.dt,self.dy*assets.dt,self.dz*assets.dt
        #print "before - ndx:",ndx,"self.amtx:",self.amtx
        self.amtx-=abs(ndx)
        #print "after self.amtx:",self.amtx
        if self.amtx<0:
            ndx+=self.amtx*(self.dx/abs(self.dx))
            print "self.amtx<0 ndx:",ndx
            self.amtx=0
        self.amty-=abs(ndy)
        if self.amty<0:
            ndy+=self.amty*(self.dy/abs(self.dy))
            self.amty=0
        self.amtz-=abs(ndz)
        if self.amtz<0:
            ndz+=self.amtz*(self.dz/abs(self.dz))
            self.amtz=0
        for d in self.stuff:
            if getattr(d["ob"],"kill",0): continue
            if d["start"]:
                d["ob"].pos[0]+=ndx
                d["ob"].pos[1]+=ndy
            if isinstance(d["ob"],mesh):
                d["ob"].trans(z=ndz)
        #Ramp not really working here
        #self.dx+=self.ramp*ndx
        #self.dy+=self.ramp*ndy
        #self.dz+=self.ramp*ndz
        if self.amtx<=0 and self.amty<=0 and self.amtz<=0:
            for d in self.stuff:
                if d["end"]:
                    d["ob"].pos[:] = d["end"]
            self.delete()
            return False
        if self.wait:
            return True
    def control_last(self):
        for o in reversed(assets.cur_script.obs):
            if hasattr(o,"pos") and not getattr(o,"kill",0):
                self.obs = [o]
                return
        if vtrue(assets.variables.get("_debug","false")):
            raise missing_object("Scroll: no objects found to scroll")
    def control(self,name):
        self.filter = None
        for o in reversed(assets.cur_script.obs):
            if getattr(o,"id_name",None)==name:
                self.obs = [o]
                return
        if vtrue(assets.variables.get("_debug","false")):
            raise missing_object("Scroll: no object named "+str(name)+" found")
                
class zoomanim(effect):
    def __init__(self,mag=1,frames=1,wait=1,name=None):
        super(zoomanim,self).__init__()
        self.mag=mag
        self.pri = ulayers.index(self.__class__.__name__)
        self.frames = frames
        self.obs = assets.cur_script.obs
        self.mag_per_frame = float(self.mag)/float(self.frames)
        self.wait = wait
        self.kill = 0
    def draw(self,dest): pass
    def update(self):
        if self.kill: return False
        self.frames -= assets.dt
        if self.frames <= 0:
            self.delete()
        for o in self.obs:
            if getattr(o,"kill",0): continue
            if hasattr(o,"dim"):
                o.dim += self.mag_per_frame*assets.dt
        if self.wait:
            return True
    def control_last(self):
        for o in reversed(assets.cur_script.obs):
            if hasattr(o,"pos") and not getattr(o,"kill",0):
                self.obs = [o]
                return
        if vtrue(assets.variables.get("_debug","false")):
            raise missing_object("zoom: no objects found to zoom")
    def control(self,name):
        self.filter = None
        for o in reversed(assets.cur_script.obs):
            if getattr(o,"id_name",None)==name:
                self.obs = [o]
                return
        if vtrue(assets.variables.get("_debug","false")):
            raise missing_object("zoom: no object named "+str(name)+" found")

class rotateanim(effect):
    def __init__(self,axis="z",degrees=90,speed=1,wait=1,name=None,obs=[]):
        super(rotateanim,self).__init__()
        self.axis = {"x":0,"y":1,"z":2,0:0,1:1,2:2}[axis]
        self.degrees = degrees
        self.pri = ulayers.index(self.__class__.__name__)
        self.speed = speed
        self.obs = obs
        self.wait = wait
        self.kill = 0
        if name:
            self.obs = [o for o in self.obs if getattr(o,"id_name",None)==name]
            if not self.obs and vtrue(assets.variables.get("_debug","false")):
                raise missing_object("rotate: no object named "+str(name)+" found")
    def draw(self,dest): pass
    def update(self):
        if self.kill: return False
        amt = self.speed*assets.dt
        if self.degrees>0:
            self.degrees-=amt
            if self.degrees<=0:
                self.delete()
                amt+=self.degrees
            amt = -amt
        elif self.degrees<0:
            self.degrees+=amt
            if self.degrees>=0:
                self.delete()
                amt-=self.degrees
        else:
            self.delete()
        for o in self.obs:
            if getattr(o,"kill",0): continue
            if hasattr(o,"rot"):
                o.rot[self.axis] += amt
            if hasattr(o,"rotate"):
                o.rotate(self.axis,amt)
        if self.wait:
            return True

class fadeanim(effect):
    def __init__(self,start=0,end=100,speed=1,wait=1,name=None,obs=[]):
        super(fadeanim,self).__init__()
        self.start = start
        self.end = end
        self.pri = ulayers.index(self.__class__.__name__)
        self.speed = speed
        self.obs = obs
        self.wait = wait
        self.kill = 0
        if name:
            self.obs = [o for o in self.obs if getattr(o,"id_name",None)==name]
            if not self.obs and vtrue(assets.variables.get("_debug","false")):
                raise missing_object("fade: no object named "+str(name)+" found")
        self.update()
    def draw(self,dest): pass
    def update(self):
        if self.kill: return False
        amt = self.speed*assets.dt
        if self.start<self.end:
            self.start+=amt
            if self.start>self.end:
                amt -= (self.start-self.end)
                self.delete()
        elif self.start>self.end:
            self.start-=amt
            if self.start<self.end:
                amt-=(self.end-self.start)
                self.delete()
        else:
            self.delete()
        for o in self.obs:
            if getattr(o,"kill",0): continue
            if hasattr(o,"setfade"):
                o.setfade(int((self.start/100.0)*255.0))
        if self.wait:
            return True
            
    #~ invert = 0
    #~ tint = None
    #~ greyscale = 1

class tintanim(effect):
    def __init__(self,start="ffffff",end="000000",speed=1,wait=1,name=None,obs=[]):
        super(tintanim,self).__init__()
        self.start = color_str(start)
        self.end = color_str(end)
        self.pri = ulayers.index(self.__class__.__name__)
        self.speed = speed
        self.obs = obs
        self.wait = wait
        self.kill = 0
        if name:
            print name
            self.obs = [o for o in self.obs if getattr(o,"id_name",None)==name]
            print self.obs
            if not self.obs and vtrue(assets.variables.get("_debug","false")):
                raise missing_object("tint: no object named "+str(name)+" found")
        self.update()
    def draw(self,dest): pass
    def update(self):
        if self.kill: return False
        amt = self.speed*assets.dt
        col = self.start
        done = 0
        for r in range(3):
            if col[r]<self.end[r]:
                col[r]+=amt
                if col[r]>self.end[r]:
                    amt -= (col[r]-self.end[r])
                    done+=1
            elif col[r]>self.end[r]:
                col[r]-=amt
                if col[r]<self.end[r]:
                    amt-=(self.end[r]-col[r])
                    done+=1
            else:
                done+=1
        if done==3:
            self.delete()
        for o in self.obs:
            if getattr(o,"kill",0): continue
            if hasattr(o,"setfade"):
                o.tint = [x/255.0 for x in col]
        if self.wait:
            return True
    
class invertanim(effect):
    def __init__(self,start=0,end=1,speed=1,wait=0,name=None,obs=[],**kw):
        super(invertanim,self).__init__()
        self.start = start
        self.end = end
        self.pri = ulayers.index("fadeanim")
        self.speed = speed
        self.obs = obs
        self.wait = wait
        self.kill = 0
        if name:
            self.obs = [o for o in self.obs if getattr(o,"id_name",None)==name]
            if not self.obs and vtrue(assets.variables.get("_debug","false")):
                raise missing_object("invert: no object named "+str(name)+" found")
        self.update()
    def draw(self,dest): pass
    def update(self):
        if self.kill: return False
        amt = self.speed
        if self.start<self.end:
            self.start+=amt
            if self.start>self.end:
                amt -= (self.start-self.end)
                self.delete()
        elif self.start>self.end:
            self.start-=amt
            if self.start<self.end:
                amt-=(self.end-self.start)
                self.delete()
        else:
            self.delete()
        for o in self.obs:
            if getattr(o,"kill",0): continue
            if hasattr(o,"setfade"):
                o.invert = self.start
        if self.wait:
            return True
            
class greyscaleanim(effect):
    def __init__(self,start=0,end=1,speed=1,wait=0,name=None,obs=[],**kw):
        super(greyscaleanim,self).__init__()
        self.start = start
        self.end = end
        self.pri = ulayers.index("fadeanim")
        self.speed = speed
        self.obs = obs
        self.wait = wait
        self.kill = 0
        if name:
            self.obs = [o for o in self.obs if getattr(o,"id_name",None)==name]
            if not self.obs and vtrue(assets.variables.get("_debug","false")):
                raise missing_object("greyscale: no object named "+str(name)+" found")
        self.update()
    def draw(self,dest): pass
    def update(self):
        if self.kill: return False
        amt = self.speed
        if self.start<self.end:
            self.start+=amt
            if self.start>self.end:
                amt -= (self.start-self.end)
                self.delete()
        elif self.start>self.end:
            self.start-=amt
            if self.start<self.end:
                amt-=(self.end-self.start)
                self.delete()
        else:
            self.delete()
        for o in self.obs:
            if getattr(o,"kill",0): continue
            if hasattr(o,"setfade"):
                o.greyscale = self.start
        if self.wait:
            return True

class flash(effect):
    def __init__(self):
        super(flash,self).__init__()
        self.pri = ulayers.index(self.__class__.__name__)
        self.ttl = 5
        self.color = [255,255,255]
        self.surf = pygame.Surface(pygame.screen.get_size())
        if vtrue(assets.variables.get("_flash_sound","false")):
            assets.play_sound("Slash.ogg")
    def draw(self,dest):
        self.surf.fill(self.color)
        dest.blit(self.surf,[0,0])
    def update(self):
        self.ttl -= assets.dt
        if self.ttl<=0: self.delete()
        return True
    
class shake(effect):
    def __init__(self,screen_setting="top"):
        super(shake,self).__init__()
        self.pri = ulayers.index(self.__class__.__name__)
        self.ttl = 15
        self.offset = 15
        if vtrue(assets.variables.get("_shake_sound","false")):
            assets.play_sound("Shock.ogg")
        self.wait = True
        self.screen_setting = screen_setting
    def draw(self,dest):
        o = int(self.offset)
        if self.screen_setting == "top":
            dest.subsurface([[0,0],[256,192]]).blit(dest.subsurface([[0,0],[256,192]]).copy(),[random.randint(-o,o),random.randint(-o,o)])
        elif self.screen_setting == "both":
            dest.blit(dest.copy(),[random.randint(-o,o),random.randint(-o,o)])
    def update(self):
        self.offset -= abs(self.offset / self.ttl)
        if self.offset < 1: self.offset = 1
        self.ttl -= assets.dt
        if self.ttl<=0: self.delete()
        return self.wait
        
class guiBack(sprite,gui.widget):
    def click_down_over(self,mp):
        self.k_space()
    def __init__(self,image=None,x=None,y=None,z=None,name=None):
        sprite.__init__(self)
        gui.widget.__init__(self)
        self.pri = ulayers.index(self.__class__.__name__)
        if not image:
            image = "general/back"
        self.image = image
        self.unhighlight()
        self.pos = [0,192+sh-self.img.get_height()]
        if x is not None:
            self.pos[0] = x
        if y is not None:
            self.pos[1] = y
        if z is not None:
            self.z = z
        if name is not None:
            self.id_name = name
        gui.widget.__init__(self,self.pos,self.img.get_size())
        self.screen_setting = "try_bottom"
    def highlight(self):
        self.load(self.image+"_high"+assets.appendgba)
    def unhighlight(self):
        self.load(self.image+assets.appendgba)
    def k_space(self):
        self.delete()
        subscript("sound_back_button_cancel")
    def update(self):
        return True
        
class guiScroll(sprite,gui.widget):
    def click_down_over(self,mp):
        self.k_z()
    def __init__(self,direction):
        sprite.__init__(self,flipx=direction+1)
        gui.widget.__init__(self)
        self.pri = ulayers.index(self.__class__.__name__)
        self.load("general/examine_scroll")
        self.pos = [sw//2-self.img.get_width()//2,sh*2-self.img.get_height()]
        gui.widget.__init__(self,self.pos,self.img.get_size())
        self.direction = direction
        self.screen_setting = "try_bottom"
    def k_z(self):
        self.delete()
        self.parent.xscrolling = self.direction*sw
        subscript("sound_examine_scroll")
        #del self.parent.scrollbut
    def update(self):
        return True
        
class guiWait(sprite):
    id_name = "_guiWait_"
    def __init__(self,run=None, mute=False):
        sprite.__init__(self)
        gui.widget.__init__(self)
        self.width = 0
        self.height = 0
        self.pri = ulayers.index(self.__class__.__name__)
        self.pos = [0,0]
        self.run = run
        self.script = assets.cur_script
        self.mute = mute  #Mute sound while waiting
        if self.mute:
            assets.pause_sound()
    def delete(self):
        self.kill = 1
        if self.mute:
            assets.resume_sound()
    def update(self):
        if self.run:
            ns = self.script.execute_macro(self.run)
        return True
        
class saved(fadesprite):
    def __init__(self,ticks=150,text="Saving...",block=True):
        super(saved,self).__init__()
        self.id_name = "_saved_"
        self.text = text
        self.ticks = abs(ticks)
        self.start = self.ticks
        self.pri = ulayers.index(self.__class__.__name__)
        self.pos[0]=0
        self.pos[1]=0
        self.block = block
        self.width=0
        self.height=0
    def draw(self,dest):
        txt1 = assets.get_font("itemset_big").render(self.text,1,[230,230,230])
        txt2 = assets.get_font("itemset_big").render(self.text,1,[30,30,30])
        txt2 = pygame.transform.scale(txt2,[txt2.get_width()-4,txt2.get_height()-4])
        dest.blit(txt1,self.pos)
        dest.blit(txt2,[self.pos[0]+2,self.pos[1]+2])
    def update(self):
        if self.ticks<=0:
            self.delete()
            return False
        self.ticks-=assets.dt
        return self.block
        
class error_msg(gui.pane):
    def __repr__(self):
        return self.msg
    def delete(self):
        self.kill = 1
    def click_down_over(self,mp):
        self.delete()
    def __init__(self,msg,line,lineno,script):
        self.id_name = "_error_msg_"
        self.pri = ulayers.index(self.__class__.__name__)
        self.z = zlayers.index(self.__class__.__name__)
        gui.pane.__init__(self)
        msg+="\nscene:'"+script.scene+"', line '"+str(lineno)+"'"
        msg+="\ncurrent game:"+assets.game
        self.msg = msg
        msg_lines = [""]
        for c in msg:
            msg_lines[-1]+=c
            if (len(msg_lines[-1])>35 or c == "\n") and msg_lines[-1].strip():
                if len(msg_lines[-1])>35:
                    msg_lines[-1]+=" - "
                msg_lines.append("")
        msg_lines.append("       Click to continue  ")
        for msg_line in msg_lines:
            msg = gui.editbox(None,msg_line)
            msg.draw(assets.Surface([64,64]))
            msg.draw_back=False
            def click_down_over(self,*args):
                pass
            msg.click_down_over = click_down_over
            msg.event = click_down_over
            msg.width = 0
            self.children.append(msg)
        self.lineno = lineno
        self.script = script
        self.width=256
        self.height=len(msg_lines)*20
        if vtrue(assets.variables.get("_production","false")):
            self.delete()
    def update(self):
        return True

class script_code(gui.pane):
    def __repr__(self):
        return self.msg
    def delete(self):
        self.kill = 1
    def __init__(self,script):
        gui.pane.__init__(self)
        self.rpos = [0,0]
        self.width = 256
        self.height = 192
        self.pri = -10000
        self.z = 10000
        self.children.append(gui.label(script.scene))
        self.lines = gui.scrollpane([10,20])
        self.lines.rpos = [0,40]
        self.lines.width = 240
        self.lines.height = 140
        self.children.append(self.lines)
        scroll_i = None
        for i,line in enumerate(script.scriptlines+["END OF SCRIPT"]):
            color = [0,0,0]
            text = line
            if i==script.si:
                color = [255,0,0]
                text = "> "+line
            line = gui.label(text)
            line.textcol = color
            if i==script.si:
                scroll_i = line
            self.lines.pane.children.append(line)
        if scroll_i:
            self.lines.updatescroll()
            self.lines.scroll_to_object(scroll_i)
        self.children.append(gui.button(self,"delete"))
    def update(self):
        return True
        
class movie:
    def __init__(self,name,sound=None):
        self.movie = assets.open_movie(name)
        self.movie.set_volume(0)
        self.size = self.movie.get_size()
        self.surf = pygame.Surface(self.size).convert()
        self.movie.set_display(self.surf)
        self.sound = sound
        if sound:
            self.sound = assets.play_sound(sound)
        self.pri = ulayers.index(self.__class__.__name__)
        self.z = zlayers.index(self.__class__.__name__)
        self.paused = 0
        self.id_name = name
    def delete(self):
        self.kill = 1
    def update(self):
        self.paused = 0
        self.movie.play()
        if self.sound:
            self.sound.unpause()
        if self.movie.get_busy(): return True
        del self.movie
        self.delete()
        if self.sound:
            self.sound.stop()
    def draw(self,dest):
        dest.blit(self.surf,[0,0])
        if not self.paused:
            self.paused = 1
        elif self.paused == 1:
            if self.movie.get_busy():
                self.movie.pause()
            if self.sound:
                self.sound.pause()
