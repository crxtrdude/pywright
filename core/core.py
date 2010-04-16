from errors import *

import gui
import zlib
import os
import pygame
pygame.font.init()
import random
import pickle
import pygame.movie
try:
    import audiere
    aud = audiere.open_device()
except:
    audiere = None

try:
    from numpy import array
    pygame.sndarray.use_arraytype("numpy")
except:
    array = None
sw,sh = 256,192
#sw,sh = 640,480
spd = 6

#from GifImagePlugin import getheader, getdata

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

def load_gif_anim(file,fc):
    import Image
    frames = []
    pil_image = Image.open(file)
    try:
        time_between_frames = pil_image.info['duration']
    except:
        time_between_frames = 1
    palette = to_triplets(pil_image.getpalette())
    last = None
    fullframes = []
    size = pil_image.size
    size = (0,0,size[0],size[1])
    blit_over = False
    framecompress = 0
    i = 0
    try:
        while 1:
            if len(pil_image.tile) > 0:
                (x0, y0, x1, y1) = pil_image.tile[0][1]
                if (x0,y0,x1,y1)!=size:
                    blit_over = True
            else:
                (x0, y0, x1, y1) = size
            try:
                thestr = pil_image.tostring()
            except IOError:
                continue
            image = pygame.image.fromstring(thestr, [size[2],size[3]], 'P')
            image.set_palette(palette)
            try:
                image.set_colorkey(pil_image.info['transparency'])
            except:
                pass
            new_image = pygame.Surface([size[2],size[3]]).convert_alpha()
            new_image.fill([0,0,0,0])
            new_image.blit(image, (x0, y0), (x0, y0, x1 - x0, y1 - y0))
            if fc and fc[0]==i:
                framecompress = fc[1]
                del fc[0]
                del fc[0]
            if not framecompress and last and blit_over:
                last.blit(new_image,[0,0])
                frames.append(last)
                last = last.copy()
            else:
                frames.append(new_image)
                last = new_image.copy()
            pil_image.seek(pil_image.tell() + 1)
            i+=1
    except EOFError:
        pass # end of sequence
    if not os.path.exists(file.replace(".gif",".txt")):
        f = open(file.replace(".gif",".txt"),"w")
        f.write("length %s\nloops 1\n"%len(frames))
        f.close()
    return frames,meta().load_from(open(file.replace(".gif",".txt")))
    
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
        lines = f.read().replace("\r\n","\n").split("\n")
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
        del x[0]
        while not x[0]: del x[0]
        if sortmode == "z":
            zlayers[zi]=x
            zi += 1
        elif sortmode == "pri":
            ulayers[ui]=x
            ui += 1
        
class Variables(dict):
    def __getitem__(self,key,*args):
        if key.startswith("_layer_"):
            layer = zlayers.index(key[7:])
            if layer is not None:
                return str(layer)
        return dict.__getitem__(self,key,*args)
    def __setitem__(self,key,value,*args):
        if key=="_speaking":
            dict.__setitem__(self,key,value,*args)
            try:
                self["_speaking_name"] = assets.gportrait().nametag.strip(" \n")
            except:
                pass
        return dict.__setitem__(self,key,value,*args)
        
class ImgFrames(list):
    pass

class Assets(object):
    lists = {}
    snds = {}
    art_cache = {}
    variables = Variables()
    gbamode = False
    num_screens = 2
    sound_format = 44100
    sound_bits = 16
    sound_sign = -1
    sound_buffer = 4096
    sound_init = 0
    sound_volume = 100
    _music_vol = 100
    def smus(self,v):
        try:
            self._music_vol = v
            pygame.mixer.music.set_volume(v/100.0)
        except:
            pass
    def gmus(self):
        try:
            return pygame.mixer.music.get_volume()*100
        except:
            return self._music_vol
    music_volume = property(gmus,smus)
    def _appendgba(self):
        if not self.gbamode: return ""
        return "_gba"
    appendgba = property(_appendgba)
    def raw_lines(self,name,ext=".txt",start="game"):
        if start=="game":
            start = self.game
        try:
            return open(start+"/"+name+ext).read().replace("\r\n","\n").split("\n")
        except IOError:
            raise file_error("File named "+start+"/"+name+ext+" could not be read.")
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
                    newlines = newlines.replace("$0",str(i))
                    for i2 in range(len(args)):
                        newlines = newlines.replace("$%s"%(i2+1),args[i2])
                    newlines = newlines.split("\n")
                    for l in reversed(newlines):
                        lines.insert(i+1,l)
            i += 1
    def get_char_list(self,pth=None):
        if pth is None: pth = self.game
        def getscripts(pth):
            s = [(pth+"/"+o) for o in os.listdir(pth) if o.endswith(".txt")]
            for o in os.listdir(pth):
                if os.path.isdir(pth+"/"+o) and not o==".svn":
                    s+=getscripts(pth+"/"+o)
            return s
        scripts = getscripts(pth.replace("\\","/"))
        chars = set()
        def getchars(pth):
            f = open(pth)
            for l in f:
                if l.startswith("char "):
                    cname = l.strip().split(" ")[1]
                    chars.add(cname)
        [getchars(pth) for pth in scripts]
        return chars
    def open_script(self,name,macros=True,ext=".txt"):
        lines = self.raw_lines(name,ext)
        reallines = []
        block_comment = False
        for line in lines:
            line = line.strip()
            if line.startswith("###"):
                if block_comment:
                    block_comment = False
                else:
                    block_comment = True
                continue
            if block_comment:
                continue
            if macros and line.startswith("include "):
                reallines.extend(self.open_script(line[8:].strip(),False))
            else:
                reallines.append(line)
        lines = reallines
        the_macros = {}
        for f in os.listdir("core/macros"):
            if f.endswith(".mcro"):
                mlines = open("core/macros/"+f).read().replace("\r\n","\n").split("\n")
                parse = self.parse_macros(mlines)
                the_macros.update(parse)
        self.game = self.game.replace("\\","/")
        case = self.game
        game = self.game.rsplit("/",1)[0]
        for pth in [game,case]:
            print pth
            if os.path.exists(pth+"/macros.txt"):
                the_macros.update(self.parse_macros(self.raw_lines("macros.txt","",start=pth)))
            for f in os.listdir(pth):
                if f.endswith(".mcro"):
                    the_macros.update(self.parse_macros(self.raw_lines(f,"",start=pth)))
        if macros:
            the_macros.update(self.parse_macros(lines))
            self.replace_macros(lines,the_macros)
        self.macros = the_macros
        return lines
    def open_font(self,name,size):
        return pygame.font.Font("fonts/"+name,size)
    def Surface(self,size,flags=0):
        if pygame.USE_GL:
            import gl
            return gl.TexQuad([0,0],cache=False)
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
        self.game = self.game.replace("\\","/")
        case = self.game
        game = self.game.rsplit("/",1)[0]
        if os.path.exists(game+"/art/"+name):
            pre = game+"/art/"
        if os.path.exists(case+"/art/"+name):
            pre = case+"/art/"
        if os.path.exists(pre+name[:-4]+".txt"):
            try:
                f = open(pre+name[:-4]+".txt")
                self.meta.load_from(f)
            except:
                import traceback
                traceback.print_exc()
                raise art_error("Art textfile corrupt:"+pre+name[:-4]+".txt")
        if name.endswith(".gif"):
            img,self.meta = load_gif_anim(pre+name,self.meta.framecompress)
        else:
            texture = pygame.image.load(pre+name)
            if texture.get_flags()&pygame.SRCALPHA: texture = texture.convert_alpha()
            else: texture = texture.convert()
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
        if getattr(pygame,"USE_GL",False):
            import gl
            img = [gl.TexQuad([0,0],surface=x) for x in img]
        img = ImgFrames(img)
        img._meta = self.meta
        img.real_path = self.real_path = pre+name
        if self.cur_script:
            self.cur_script.imgcache[name] = img
        return img
    def open_art(self,name,key=None):
        """Try to open an art file.  Name has no extension.
        Will open gif, then png, then jpg.  Returns list of 
        frame images"""
        self.real_path = None
        s = None
        try:
            return self._open_art_(name+".png",key)
        except (IOError,pygame.error):
            pass
        try:
            return self._open_art_(name+".jpg",key)
        except (IOError,pygame.error):
            pass
        try:
            return self._open_art_(name+".gif",key)
        except (IOError,ImportError,pygame.error):
            pass
        raise art_error("Art file corrupt or missing:"+name)
    def init_sound(self,reset=False):
        if reset or not self.sound_init:
            self.snds = {}
            try:
                pygame.mixer.stop()
                pygame.mixer.quit()
            except:
                pass
            try:
                pygame.mixer.pre_init(self.sound_format, self.sound_sign*self.sound_bits, 2, self.sound_buffer)
                pygame.mixer.init()
                self.sound_init = 1
                pygame.mixer.music.set_volume(self._music_vol/100.0)
                return True
            except:
                self.sound_init = -1
        if self.sound_init==1: return True
        return False
    def get_music_path(self,track,pre=None):
        if pre is None: pre = "music/"
        game = self.game.replace("\\","/").rsplit("/",1)[0]
        if os.path.exists(game+"/music/"+track):
            pre = game+"/music/"
        if os.path.exists(self.game+"/music/"+track):
            pre = self.game+"/music/"
        return pre+track
    def open_music(self,track,pre=None):
        path = self.get_music_path(track,pre)
        try:
            pygame.mixer.music.load(path)
        except:
            pass
    def open_movie(self,movie):
        game = self.game.replace("\\","/").rsplit("/",1)[0]
        for folder in [self.game+"/",game+"/",""]:
            for ext in [".mpeg",".mpg"]:
                name = folder+"movies/"+movie+ext
                if os.path.exists(name):
                    mov = pygame.movie.Movie(name)
                    return mov
        raise art_error("Movie is missing or corrupt:"+movie)
    def list_casedir(self):
        return os.listdir(self.game)
    def play_sound(self,name,wait=False,volume=1.0,offset=0,frequency=1):
        #self.init_sound()
        if self.sound_init == -1: return
        pre = "sfx/"
        game = self.game.replace("\\","/").rsplit("/",1)[0]
        if os.path.exists(game+"/"+name):
            pre = game+"/"
        if os.path.exists(game+"/sfx/"+name):
            pre = game+"/sfx/"
        if os.path.exists(self.game+"/sfx/"+name):
            pre = self.game+"/sfx/"
        if self.snds.get(name,None):
            snd = self.snds[name]
        else:
            try:
                if name.endswith(".mp3") and audiere:
                    snd = aud.open_file(pre+name)
                else:
                    snd = pygame.mixer.Sound(pre+name)
            except:
                import traceback
                traceback.print_exc()
            self.snds[name] = snd
        snd.stop()
        try:
            snd.set_volume(float(self.sound_volume/100.0)*volume)
        except:
            snd.volume = (self.sound_volume/100.0)*volume
        channel = snd.play()
        return channel
    def play_music(self,track=None,loop=0,pre=None,reset_track=True):
        if reset_track:
            assets.variables["_music_loop"] = track
        self.init_sound()
        if self.sound_init == -1: return
        self._track=track
        self._loop=loop
        if track:
            self.open_music(track,pre)
        try:
            pygame.mixer.music.play(loop)
        except:
            import traceback
            traceback.print_exc()
        pygame.mixer.music.set_endevent(150)
    def stop_music(self):
        if self.sound_init == -1: return
        self._track = None
        self._loop = 0
        try:
            pygame.mixer.music.stop()
        except:
            pass
    def set_emotion(self,e):
        """Sets the emotion of the current portrait"""
        if not self.portrait:
            self.add_portrait(self.character+"/"+e+"(blink)")
        if self.portrait:
            self.portrait.set_emotion(e)
    flash = 0  #Tells main to add a flash object
    flashcolor = [255,255,255]
    shake = 0  #Tell main to add a shake object
    shakeoffset = 15
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
        id_name = self.variables.get("_speaking",None)
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
        assets.variables["_speaking"] = p
        if stack: p.was_stacked = True
        return p
    def clear(self):
        if not hasattr(self,"variables"):
            self.variables = {}
        self.variables.clear()
        while assets.items:
            assets.items.pop(0)
        assets.stop_music()
        assets.lists = {}
    def save(self):
        props = {}
        for reg in ["character","_track","_loop","lists"]:
            if hasattr(self,reg):
                props[reg] = getattr(self,reg)
        #save items
        items = []
        for x in self.items:
            items.append(x.id)
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
        self.items = [evidence(x) for x in self.items]
        v = self.variables
        self.variables = Variables()
        self.variables.update(v)
        if getattr(self,"_track",None):
            self.play_music(self._track,self._loop)
    def load(self,s):
        self._track,self._loop,self.character,self.px,self.py,self.pz,\
        self.items,self.variables,self.lists = pickle.loads(s)
        if self._track:
            self.play_music(self._track,self._loop,reset_track=False)
    def show_load(self):
        self.make_screen()
        txt = assets.open_font("arial.ttf",16).render("LOADING",1,[200,100,100])
        pygame.screen.blit(txt,[50,50])
        self.draw_screen()
    def load_game_new(self,path=None,filename="save",hide=False):
        self.loading_cache = {}
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
            self.cur_script.obs.append(saved(text="You have not yet saved, no game to load.",ticks=240))
            return
        assets.clear()
        stack = {}
        things = eval(f.read())
        f.close()
        loaded = []
        for cls,args,props,dest in things:
            if cls == "Assets":
                ob = self
            else:
                ob = eval(cls)(*args)
            for k in props:
                print k,props[k]
                setattr(ob,k,props[k])
            if dest:
                cont,index = dest
                if cont == "stack":
                    stack[index] = ob
                else:
                    stack[index].obs.append(ob)
            loaded.append(ob)
        for ob in loaded:
            ob.after_load()
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
            print stack[k]
            print stack[k].si
            assets.stack.append(stack[k])
        self.cur_script.obs.append(saved(text="Game restored",block=False))
    def save_game(self,filename="save",hide=False):
        if not vtrue(self.variables.get("_allow_saveload","true")):
            return
        if "\\" in filename or "/" in filename:
            raise script_error("Invalid save file path:'%s'"%(filename,))
        filename = filename.replace("/","_").replace("\\","_")+".ns"
        #Collect *things* to save
        stuff = [self.save()]
        for script in self.stack:
            if script.save_me:
                stuff.append(script.save())
        f = open(self.game+"/"+filename,"w")
        f.write(repr(stuff))
        f.close()
        if not hide:
            self.cur_script.obs.append(saved())
    def load_game(self,path=None,filename="save",hide=False):
        self.cur_script.imgcache.clear()
        chkpath=""
        if path is not None:
            chkpath=path+"/"
        if not os.path.exists(chkpath+filename+".ns"):
            self.load_game_old(path,filename,hide)
        else:
            self.load_game_new(path,filename,hide)
    def load_game_old(self,path=None,filename="save",hide=False):
        if not vtrue(self.variables.get("_allow_saveload","true")):
            return
        if "\\" in filename or "/" in filename:
            raise script_error("Invalid save file path:'%s'"%(filename,))
        if not hide:
            self.show_load()
        if path:
            self.game = path
        try:
            f = open(self.game+"/"+filename)
        except:
            self.cur_script.obs.append(saved(text="You have not yet saved, no game to load.",ticks=240))
            return
        self.stack = []
        self.load(f.readline()[:-1].replace("..--..","\n"))
        mode = 0
        for line in f.readlines():
            if mode==0:
                s = assets.Script()
                s.load(line[:-1].replace("..--..","\n"))
                self.stack.append(s)
                mode += 1
            elif mode==1:
                if line=="end\n":
                    mode = 0
                else:
                    o,rest = line.split(";",1)
                    o = eval(o)()
                    try:
                        o.restore(rest.replace("..--..","\n"))
                    except:
                        continue
                    s.obs.append(o)
        f.close()
        self.cur_script.obs.append(saved(text="Game restored",block=False))

        
def vtrue(variable):
    if variable.lower() in ["on","1","true"]:
        return True
    return False
    
assets = Assets()

class SoundEvent(object):
    kill = 0
    pri = -1000000
    def __init__(self,name,after=0):
        self.name = name
        self.wait = after
        self.z = zlayers.index(self.__class__.__name__)
    def update(self):
        self.wait-=1
        if self.wait<=0:
            assets.play_sound(self.name)
            self.kill = 1
        return False
    def draw(self,*args):
        pass
        
pwinternational = pygame.font.Font("fonts/pwinternational.ttf",10)

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
class ImgFont(object):
    lastcolor = [255,255,255]
    prevcolor = [255,255,255]
    def __init__(self,img):
        self.img = pygame.image.load(img)
        self.img.set_colorkey([255,255,255])
        self.colors = {}
        self.chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ "+\
         "abcdefghijklmnopqrstuvwxyz"+\
         "!?.;[](){}\"\"@#:+,/*'_\t\r%\b~<>&`^-"
        self.width = {"":0}
        self.start = {}
        self.quote = 0
    def get_char(self,t,color=[255,255,255]):
        if not self.colors.get(tuple(color),None):
            self.colors[tuple(color)] = pygame.Surface(self.img.get_size())
            self.colors[tuple(color)].fill(color)
            self.colors[tuple(color)].blit(self.img,[0,0])
        surf = None
        if t not in self.chars:
            if (t,tuple(color)) in self.colors:
                return self.colors[(t,tuple(color))]
            surf = pwinternational.render(t,0,color)
            start = 0
            edge = 0
            starty = 0
            for y in xrange(surf.get_height()):
                for x in xrange(surf.get_width()):
                    if surf.get_at((x,y)) != (0,0,0,255):
                        if not starty:
                            starty = y-2
                            break
            for x in xrange(surf.get_width()):
                for y in xrange(surf.get_height()):
                    if surf.get_at((x,y)) != (0,0,0,255):
                        edge = x
                        if not start:
                            start = x
            edge += 3
            self.width[t] = edge-start
            self.start[t] = start
            print surf.get_rect()
            print [[start,starty],[edge-start-1,surf.get_height()-starty-1]]
            surf = surf.subsurface([[start,starty],[edge-start-1,surf.get_height()-starty-1]])
            self.colors[t,tuple(color)] = surf
            return surf
        i = self.chars.find(t)
        if t=='"':
            i += self.quote
            self.quote = 1-self.quote
        y = i//8
        x = i-y*8
        w,h = [16,16]
        if not self.width.get(t,None):
            surf = self.img.subsurface([[x*17+1,y*17+1],[16,16]])
            start = 0
            edge = 0
            for x in xrange(surf.get_width()):
                for y in xrange(surf.get_height()):
                    if surf.get_at((x,y)) != (0,0,0,255):
                        edge = x
                        if not start:
                            start = x
            edge += 3
            self.width[t] = edge-start
            self.start[t] = start
        y = i//8
        x = i-y*8
        w,h = [16,16]
        start = self.start[t]
        color = self.colors[tuple(color)].subsurface([[x*17+1+start,y*17+1],[self.width[t]-2,h]])
        return color
    def split_line(self,text,max_width):
        """Returns the line split at the point to equal a desired width"""
        left = [""]
        right = [""]
        which = left
        width = 0
        parse = True
        wb = 0
        for i,c in enumerate(text):
            
            if c not in self.width:
                self.get_char(c)
                
            if c == "{":
                parse = False
            if parse:
                if which == left and width+self.width[c]>max_width:
                    r = which.pop(-1)
                    which = right
                    right.insert(0,r[1:])
                elif c == " ":
                    if not which[-1] or which[-1][-1]!=" ":
                        which.append("")
                width+=self.width[c]
            if c== "}":
                parse = True
            which[-1]+=c
        print left,right
        return "".join(left),"".join(right)
    def render(self,text,color=[255,255,255],return_size=False):
        """return a surface with rendered text
        color = the starting color"""
        self.quote = 0
        chars = []
        width = 0
        parse = True
        for c in text:
            char = self.get_char(c,color)
            chars.append([c,char])
            if c == "{":
                parse = False
            if parse:
                width+=self.width.get(c,8)
            if c == "}":
                parse = True
        if return_size:
            return width
        surf = pygame.Surface([width,20])
        x = 0
        mode = "std"
        command = ""
        for c,img in chars:
            if mode == "std":
                if c == "{":
                    mode = "find"
                else:
                    surf.blit(self.get_char(c,color),[x,0])
                    x += self.width.get(c,8)
            elif mode == "find":
                if c == "}":
                    mode = "std"
                else:
                    command+=c
            if command and mode == "std":
                try:
                    if command[0]=="c" and (len(command)==1 or command[1].isdigit() or command[1]==" "):
                        if len(command)==1:
                            ImgFont.prevcolor,color = color,ImgFont.prevcolor
                        else:
                            newcolor = color_str(command[1:])
                            if newcolor != color:
                                ImgFont.prevcolor = color
                                color = newcolor
                except:
                    import traceback
                    traceback.print_exc()
                    raise markup_error(command+" is invalid text markup")
                command = ""
            ImgFont.lastcolor = color
        surf.set_colorkey([0,0,0])
        return surf
    def size(self,text):
        """return the size of the text if it were rendered"""
        return self.render(text,[0,0,0],return_size=True)
    def get_linesize(self):
        """return hieght in pixels for a line of text"""
    def get_height(self):
        """return height in pixels of rendered text - average for each glyph"""
    def get_ascent(self):
        """return hieght in pixels from font baseline to top"""
    def get_descent(self):
        """return number of pixels from font baseline to bottom"""

font = ImgFont("fonts/p.png")
verase8 = pygame.font.Font("fonts/VeraSe.ttf",8)
arial10 = pygame.font.Font("fonts/arial.ttf",10)
arial14 = pygame.font.Font("fonts/arial.ttf",14)

class sprite(gui.button):
    blinkspeed = [100,200]
    autoclear = False
    pri = 0
    #widget stuff
    def _g_rpos(self):
        if not hasattr(self,"pos"): return [0,0]
        return self.pos
    rpos = property(_g_rpos)
    width,height = [sw,sh]
    children = []
    spd = 6
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
        elif assets.variables.get("_blinkspeed_global",""):
            self.blinkspeed = [int(x) for x in assets.variables["_blinkspeed_global"].split(" ")]
    def load(self,name,key=[255,0,255]):
        self.key = key
        if type(name)==type(""):
            path = ""
            if name[-4:] in [".jpg",".gif",".png"]:
                name = name[:-4]
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
        self.base = []
        self.delays = {}
        self.start = 0
        self.end = None
    def save(self):
        if not hasattr(self,"name"): self.name = ""
        id_name = getattr(self,"id_name",None)
        return pickle.dumps([self.name,self.key,self.scale,self.loopmode,self.z,self.next,self.pos,self.sounds,id_name,self.delays,self.x])
    def restore(self,s):
        vars = pickle.loads(s)
        self.name,self.key,self.scale,self.loopmode,self.z,self.next,self.pos,self.sounds = vars[:8]
        self.load(self.name,self.key,self.scale)
        if len(vars)>8:
            if vars[8]:
                self.id_name = vars[8]
        if len(vars)>9:
            if vars[9]:
                self.delays = vars[9]
        if len(vars)>10:
            if vars[10]:
                self.x = vars[10]
    def draw(self,dest):
        if not getattr(self,"img",None): return
        img = self.img
        if self.flipx:
            img = pygame.transform.flip(img,1,0)
        pos = self.pos[:]
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
            self.next-=1
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
        
class fadesprite(sprite):
    real_path=None
    def setfade(self,val=255):
        if getattr(self,"fade",None) is None: self.fade = 255
        self.lastfade = self.fade
        self.fade = val
        return self
    def draw(self,dest):
        if getattr(self,"fade",None) is None: self.fade = 255
        if self.fade == 0:
            return
        if self.fade == 255:
            return sprite.draw(self, dest)
        if getattr(self,"img",None) and not getattr(self,"mockimg",None):
            self.draw_func = self.mockdraw
            nn = self.name.replace("/","sl")
            exists = os.path.exists("core/cache/"+nn+".mock.png")
            if exists and self.real_path:
                cache_t = os.stat("core/cache/"+nn+".mock.png").st_mtime
                content_t = os.stat(self.real_path).st_mtime
                if content_t>cache_t:
                    exists = False
            if not exists:
                self.mockimg = self.img.convert()
                #self.tenpercent = self.img.convert_alpha()
                invis = [255,0,255]
                for y in range(self.img.get_height()):
                    for x in range(self.img.get_width()):
                        rgba = self.img.get_at([x,y])
                        if rgba[3]==0:
                            self.mockimg.set_at([x,y],invis)
                        rgba=rgba[0],rgba[1],rgba[2],int(0.1*rgba[3])
                        #self.tenpercent.set_at([x,y],rgba)
                        #~ if [rgba[0],rgba[1],rgba[2]] == [255,0,255]:
                            #~ self.draw_func = self.layerdraw
                pygame.image.save(self.mockimg,"core/cache/"+nn+".mock.png")
                self.mockimg.set_colorkey(invis)
            else:
                self.draw_func = self.mockdraw
                self.mockimg = pygame.image.load("core/cache/"+nn+".mock.png").convert()
                self.mockimg.set_colorkey([255,0,255])
        self.draw_func(dest)
    def mockdraw(self, dest):
        self.mockimg.set_alpha(self.fade)
        img = self.img
        self.img = self.mockimg
        sprite.draw(self,dest)
        self.img = img
    #~ def layerdraw(self, dest):
        #~ percent = self.fade/255.0
        #~ per_tens = int(percent*10)
        #~ if per_tens>=9:
            #~ return sprite.draw(self,dest)
        #~ img = self.img
        #~ for i in range(per_tens):
            #~ self.img = self.tenpercent
            #~ sprite.draw(self, dest)
        #~ self.img = img
    def restore(self,s):
        sprite.restore(self,s)
    def update(self):
        sprite.update(self)

class graphic(fadesprite):
    def __init__(self,name,*args,**kwargs):
        fadesprite.__init__(self,*args,**kwargs)
        self.load(name)

class portrait(object):
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
        self.init(name,hide)
    def init(self,name=None,hide=False,blinkname=None):
        if not name: return
        self.z = zlayers.index(self.__class__.__name__)
        self.clicksound = "blipmale.ogg"
        self.pri = 20
        self.pos = [0,0]
        self.rot = [0,0,0]
        self.name = name
        super(portrait,self).__init__()
        charname,rest = name.split("/",1)
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
        if charname in self.female:
            self.clicksound = "blipfemale.ogg"
        self.charname = charname
        self.emoname = emo
        self.blinkemo = blinkemo
        self.modename = mode
        self.nametag = charname+"\n"
        
        if not self.emoname: hide = "wait"
        self.hide = hide
        if self.hide: return
        
        self.talk_sprite = fadesprite()
        self.blink_sprite = fadesprite()
        self.cur_sprite = self.talk_sprite
        self.combined = fadesprite()
        def shrink(t):
            if not t.startswith("/"):
                t = "/"+t
            return t[t.rfind("/art/")+5:-4]
            
        def loadfrom(path):
            if not path.endswith("/"):path+="/"

            def noext(x):
                return x.rsplit(".",1)[0]
            available = [x for x in os.listdir(path) if (noext(x)==blinkemo+"(blink)")]
            if available and not hasattr(self.blink_sprite,"img"):
                self.blink_sprite.load(shrink(path+available[0]))
                
            available = [x for x in os.listdir(path) if (noext(x)==emo+"(talk)")]
            if available and not hasattr(self.talk_sprite,"img"):
                self.talk_sprite.load(shrink(path+available[0]))
                
            available = [x for x in os.listdir(path) if (noext(x)==emo+"(combined)")]
            if available and not hasattr(self.combined,"img"):
                self.combined.load(shrink(path+available[0]))
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
            available = [x for x in os.listdir(path) if (emo+"." in x)]
            if available and not hasattr(self.blink_sprite,"img"):
                self.blink_sprite.load(shrink(path+available[0]))
                if self.blink_sprite.blinkmode=="blinknoset": self.blink_sprite.blinkmode = "stop"

        game = assets.game.replace("\\","/").rsplit("/",1)[0]
        if os.path.exists(assets.game+"/art/port/"+charname):
            loadfrom(assets.game+"/art/port/"+charname)
        elif os.path.exists(game+"/art/port/"+charname):
            loadfrom(game+"/art/port/"+charname)
        elif os.path.exists("art/port/"+charname):
            loadfrom("art/port/"+charname)
        else:
            raise art_error("Character folder %s not found"%charname)
        
        if hasattr(self.talk_sprite,"img") and not hasattr(self.blink_sprite,"img"):
            self.blink_sprite.img = self.talk_sprite.img
            self.blink_sprite.blinkmode = "stop"
            #self.blink_sprite.load(self.talk_sprite.base[:])
            #self.blink_sprite.base = [self.blink_sprite.base[0]]
        if hasattr(self.blink_sprite,"img") and not hasattr(self.talk_sprite,"img"):
            self.talk_sprite.img = self.blink_sprite.img
            #self.talk_sprite.load(self.blink_sprite.base[:])
            #self.talk_sprite.base = [self.talk_sprite.base[0]]
        self.blink_sprite.loopmode = self.blink_sprite.blinkmode
        if getattr(self.talk_sprite,"blipsound",None):
            self.clicksound = self.talk_sprite.blipsound
        self.blink_sprite.spd = int(assets.variables.get("_default_port_frame_delay",self.talk_sprite.spd))
        self.talk_sprite.spd = int(assets.variables.get("_default_port_frame_delay",self.talk_sprite.spd))
        if hasattr(self.talk_sprite,"img") and hasattr(self.blink_sprite,"img"):
            if mode=="blink":self.set_blinking()
            #if mode=="talk":self.set_talking()
        else:
            raise art_error("Can't load '"+charname+"' '"+emo+"' '"+mode+"'")
        self.blinkspeed = self.blink_sprite.blinkspeed
    def save(self):
        return pickle.dumps([self.charname,self.emoname,self.modename,self.hide,self.pos,self.nametag,
            getattr(self,"id_name",None)])
    def restore(self,s):
        vals = pickle.loads(s)
        self.charname,self.emoname,self.modename,self.hide = vals[:4]
        nametag = self.charname
        self.__init__(self.charname+"/"+self.emoname+"("+self.modename+")",self.hide)
        if len(vals)>4:
            self.pos = vals[4]
            print "LOADED POS",self.pos
        if len(vals)>5:
            self.nametag = vals[5]
            print "LOADED NT",self.nametag
        if len(vals)>6:
            self.id_name = vals[6]
            print "LOADED ID",self.id_name
    def draw(self,dest):
        if not self.hide and getattr(self.cur_sprite,"img",None):
            pos = self.pos[:]
            pos[0] += (sw-(self.cur_sprite.offsetx+self.cur_sprite.img.get_width()))//2
            pos[1] += (sh-(self.cur_sprite.img.get_height()-self.cur_sprite.offsety))
            self.cur_sprite.pos = pos
            self.cur_sprite.rot = self.rot[:]
            self.cur_sprite.draw(dest)
    def update(self):
        if not self.hide and getattr(self.cur_sprite,"img",None):
            return self.cur_sprite.update()
    def set_emotion(self,emo):
        if self.hide and self.hide != "wait": return
        if not emo: return
        self.hide = False
        p = self.pos[:]
        self.init(self.charname+"/"+emo+"("+self.modename+")")
        self.pos = p
    def set_blink_emotion(self,emo):
        if self.hide and self.hide != "wait": return
        if not emo: return
        self.hide = False
        p = self.pos[:]
        self.init(self.charname+"/"+self.emoname+"("+self.modename+")",blinkname=emo)
        self.pos = p
    def set_talking(self):
        if self.hide: return
        self.cur_sprite = self.talk_sprite
        self.modename = "talk"
    def set_blinking(self):
        if self.hide: return
        self.cur_sprite = self.blink_sprite
        self.modename = "blink"
    def setfade(self,*args):
        self.blink_sprite.setfade(*args)
        self.talk_sprite.setfade(*args)
        
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
        self.small = pygame.transform.scale(self.img,[35,35])
        self.scaled = pygame.transform.scale(self.img,[70,70])
        self.setfade()
        self.name = assets.variables.get(self.id+"_name",self.id.replace("$",""))
        self.desc = assets.variables.get(self.id+"_desc",self.id.replace("$",""))
        
class penalty(fadesprite):
    def __init__(self,end=100,var="penalty"):
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
    def save(self):
        return ""
    def restore(self,s):
        pass
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
        self.sv(v)
    def update(self):
        v = self.gv()
        if self.end<v:
            v -= 1
            if v<0: v = 0
        elif self.end>v:
            v += 1
            if v>100: v = 100
        else:
            self.delay -= 1
            if self.delay<0:
                self.die()
                self.kill = 1
        self.sv(v)
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
        if self.next!=-1 and self.wait:
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
    def save(self):
        return ""
    def restore(self,s):
        pass
    
class press_button(fadesprite,gui.widget):
    def __init__(self,parent):
        self.normal = assets.open_art("general/crossex")[0]
        self.high = assets.open_art("general/crossex_high")[0]
        self.rect = [[0,0],[64,16]]
        self.highlight = False
        self.pos = [0,0]
        gui.widget.__init__(self,self.pos,[64,16],parent)
        self.width,self.height = 64,16
    def draw(self,dest):
        surf = {False:self.normal,True:self.high}[self.highlight is True]
        dest.blit(surf.subsurface(self.rect),self.pos)
    def click_down_over(self,mp):
        self.parent.k_z()

class present_button(fadesprite,gui.widget):
    def __init__(self,parent):
        self.normal = assets.open_art("general/crossex")[0]
        self.high = assets.open_art("general/crossex_high")[0]
        self.rect = [[0,16],[64,16]]
        self.highlight = False
        self.pos = [sw-64,0]
        gui.widget.__init__(self,self.pos,[64,16],parent)
        self.width,self.height = 64,16
    def draw(self,dest):
        surf = {False:self.normal,True:self.high}[self.highlight is True]
        dest.blit(surf.subsurface(self.rect),self.pos)
    def click_down_over(self,mp):
        self.parent.k_x()

class record_button(fadesprite,gui.widget):
    z = 7
    def __init__(self,parent):
        self.normal = assets.open_art("general/record")[0]
        self.high = assets.open_art("general/record_high")[0]
        self.highlight = False
        self.pos = [sw-self.normal.get_width(),other_screen(0)]
        gui.widget.__init__(self,self.pos,self.normal.get_size(),parent)
        #self.width = 40
        self.height = 17
    def draw(self,dest):
        if not vtrue(assets.variables.get("_cr_button","on")):
            return
        surf = {False:self.normal,True:self.high}[self.highlight is True]
        dest.blit(surf,self.pos)
    def click_down_over(self,mp):
        if not vtrue(assets.variables.get("_cr_button","on")):
            return
        if mp[0]>=self.pos[0] and mp[0]<=self.pos[0]+self.normal.get_width() and\
            mp[1]>=self.pos[1] and mp[1]<=self.pos[1]+self.height:
            if mp[0]>self.pos[0]+38:
                self.showmenu()
                return True
            elif mp[0]>self.pos[0]+21 and vtrue(assets.variables.get("_allow_click_save","true")):
                assets.save_game()
                return True
            elif mp[0]<=self.pos[0]+21 and vtrue(assets.variables.get("_allow_click_load","true")):
                assets.load_game()
                return True
    def showmenu(self):
        if not vtrue(assets.variables.get("_cr_button","on")):
            return
        assets.addevmenu()
        
class textbox(gui.widget):
    pri = 30
    def click_down_over(self,pos):
        if not hasattr(self,"rpos1"): return
        if getattr(self,"kill",0) or getattr(self,"hidden",0): return
        if self.statement:
            if pos[1]>=self.rpos[1] and pos[1]<=self.rpos1[1]+self.height1:
                if pos[0]>=self.rpos1[0] and pos[0]<=self.rpos1[0]+self.width/2:
                    self.k_left()
                if pos[0]>=self.rpos1[0]+self.width/2 and pos[0]<=self.rpos1[0]+self.width:
                    self.k_right()
        if pos[0]>=self.rpos1[0] and pos[0]<=self.rpos1[0]+self.width1 and pos[1]>=self.rpos1[1] and pos[1]<=self.rpos1[1]+self.height1:
            self.enter_down()
    def set_text(self,text):
        nt = text.split("{")
        for i,x in enumerate(nt[1:]):
            if x.startswith("$"):
                if not "}" in x:
                    raise "markup error"
                varname = x[:x.find("}")][1:]
                try:
                    t = "}"+assets.variables.get(varname,"").replace("{","(").replace("}",")")
                    t = t+x[x.find("}")+1:]
                    nt[i+1]=t
                except TypeError:
                    pass
        text = "{".join(nt)
        lines = text.split("\n")
        wrap = vtrue(assets.variables.get("_textbox_wrap","true"))
        if vtrue(assets.variables.get("_textbox_wrap_avoid_controlled","true")):
            if len(lines)>1:
                wrap = False
        pages = []
        page = []
        while lines:
            line = lines.pop(0)
            if wrap:
                left,right = font.split_line(line,250)
            else:
                left,right = line,""
            page.append(left)
            if right.strip():
                if not lines: lines.append("")
                lines[0]=right+" "+lines[0]
            if len(page)==3:
                pages.append(self.nametag+"\n".join(page))
                page = []
        if [1 for x in page if x]:
            pages.append(self.nametag+"\n".join(page))
        self._text = "\n".join(pages)
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
        self.written = ""
        self.wlen = 0  #text actually written to textbox
        self.num_lines = 4
        self.next = self.num_lines
        self.nextline = 0
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
        self.skipping = False
        self.statement = None
        self.wait = "auto"
        
        self.pressb = press_button(self)
        self.presentb = present_button(self)
        self.recordb = record_button(self)
        self.pressing = 0
        self.presenting = 0
        self.can_skip = True
        self.blocking = not vtrue(assets.variables.get("_textbox_skipupdate","0"))
    def gsound(self):
        if hasattr(self,"_clicksound"): return self._clicksound
        if assets.portrait:
            return assets.portrait.clicksound
        return "blipmale.ogg"
    def ssound(self,v):
        self._clicksound = v
    clicksound = property(gsound,ssound)
    def save(self):
        return ""
    def restore(self,s):
        pass
    def can_continue(self):
        if not self.blocking: return
        if not self.can_skip:
            if not self.nextline:
                return
        return True
    def enter_down(self):
        if not self.can_continue(): return
        if not self.nextline:
            self.written = self.text
        else:
            self.forward()
    #~ def enter_hold(self):
        #~ if self.can_skip:
            #~ self.skipping = 1
        #~ self.enter_down()
    def enter_up(self):
        self.skipping = 0
    def k_left(self):
        if self.statement:
            assets.cur_script.prev_statement()
            self.forward()
    def k_right(self):
        if self.statement:
            self.forward()
    def k_z(self):
        if self.statement and not self.pressing:
            self.pressb.highlight = True
            self.pressing = 15
    def k_x(self):
        if self.statement and not self.presenting:
            self.presentb.highlight = True
            self.presenting = 15
    def k_tab(self):
        self.recordb.showmenu()
    def forward(self,sound=True):
        assets.cur_script.tboff()
        lines = self.text.split("\n")
        lines = lines[4:]
        self._text = "\n".join(lines)
        self.written = ""
        self.wlen = 0
        self.next = self.num_lines
        self.img = self.base.copy()
        if not self.text.strip():
            self.kill = 1
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
        if self.rightp and self.nextline:
            dest.blit(self.rpi.img,[self.rpos1[0]+self.width1-16,
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
        if self.statement:
            self.pressb.draw(dest)
            self.presentb.draw(dest)
            self.children+=[self.pressb,self.presentb]
        self.recordb.draw(dest)
        self.children+=[self.recordb]
    def update(self):
        #assets.play_sound(self.clicksound)
        if self.statement:
            if self.pressing:
                self.pressing -= 1
                if self.pressing == 0:
                    self.pressb.highlight = False
                    assets.cur_script.cross = "pressed"
                    assets.cur_script.goto_result("press "+self.statement,backup=assets.variables.get("_court_fail_label",None))
                    #self.forward()
                    self.kill = 1
            if self.presenting:
                self.presenting -= 1
                if self.presenting == 0:
                    self.presentb.highlight = False
                    em = assets.addevmenu()
                    em.fail = assets.variables.get("_court_fail_label",None)
        self.rpi.update()
        self.nextline = 0
        if self.kill: return
        addchar = False
        if self.text:
            while "\n" not in self.written and len(self.written)<len(self.text):
                self.written+=self.text[len(self.written)]
        num_chars = 0
        if self.next_char==0:
            num_chars = self.speed
        if self.skipping:
            num_chars = 3
        for cnum in range(num_chars):
            if (len(self.written)<len(self.text) and 
                    len(self.written.replace("\r\n","\n").split("\n"))<\
                    self.num_lines+1):
                addchar = True
            if not addchar:
                self.nextline = 1
            self.next_char = 1
            command = None
            while addchar:
                char = self.text[len(self.written)]
                self.written+=char
                if char == "{":
                    addchar = "getcolor"
                    command = ""
                elif char == "}":
                    if command:
                        macroargs = command.split(" ",1)
                        if len(macroargs)==1: macroargs+=[""]
                        macro,args = macroargs
                        if assets.cur_script.macros.get(macro,None):
                            assets.variables["_return"] = ""
                            this = assets.cur_script
                            ns = assets.cur_script.execute_macro(macro,args)
                            old = ns._endscript
                            def back():
                                old()
                                s = len(self.written)
                                self._text = self.text[:s]+assets.variables.get("_return","")+self.text[s:]
                            ns._endscript = back
                        elif command.startswith("sfx"):
                            assets.play_sound(command[3:].strip())
                        elif command.startswith("sound"):
                            self.clicksound = command[5:].strip()
                        elif command.startswith("delay"):
                            self.delay = int(command[5:].strip())
                            self.wait = "manual"
                        elif command.startswith("spd"):
                            self.speed = int(command[3:].strip())
                        elif command.startswith("wait"):
                            self.wait = command[4:].strip()
                        elif command == "center":
                            pass
                        elif command == "type":
                            self.clicksound = "typewriter.ogg"
                            self.delay = 2
                            self.wait = "manual"
                        elif command == "next":
                            if assets.portrait:
                                assets.portrait.set_blinking()
                            self.forward(False)
                        elif command[0]=="e":
                            try:
                                assets.set_emotion(command[1:].strip())
                            except:
                                import traceback
                                traceback.print_exc()
                                raise markup_error("No character to apply emotion to")
                        elif command[0]=="f":
                            assets.flash = 3
                            assets.flashcolor = [255,255,255]
                            command = command.split(" ")
                            if len(command)>1:
                                assets.flash = int(command[1])
                            if len(command)>2:
                                assets.flashcolor = color_str(command[2])
                        elif command[0]=="s":
                            assets.shake = 30
                            assets.shakeoffset = 15
                            command = command.split(" ")
                            if len(command)>1:
                                assets.shake = int(command[1])
                            if len(command)>2:
                                assets.shakeoffset = int(command[2])
                        elif command[0]=="p":
                            self.next_char = int(command[1:].strip())
                        elif command[0]=="c":
                            pass
                        elif command=="tbon":
                            assets.cur_script.tbon()
                        elif command=="tboff":
                            assets.cur_script.tboff()
                        else:
                            raise markup_error("No macro or markup command valid for:"+command)
                    addchar = False
                elif command != None:
                    command += char
                elif addchar == True:
                    if not hasattr(self,"_lc"):
                        self._lc = ""
                    self.go = 1
                    if self._lc in ".?" and char == " ":
                        self.next_char = 6
                    if self._lc in "!" and char == " ":
                        self.next_char = 8
                    if self._lc in "," and char == " ":
                        self.next_char = 4
                    if self._lc in "-" and (char.isalpha() or char.isdigit()):
                        self.next_char = 4
                    #if char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                    #    self.next_char = 1
                    if char in "(":
                        self.in_paren = 1
                    if char in ")":
                        self.in_paren = 0
                    if assets.portrait:
                        if not self.in_paren and char in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ":
                            assets.portrait.set_talking()
                        if self.in_paren:
                            assets.portrait.set_blinking()
                    if char.strip():
                        assets.play_sound(self.clicksound,volume=random.uniform(0.65,1.0))
                    addchar = False
                    self.next_char = int(self.next_char*self.delay)
                    if self.wait=="manual":
                        if char.strip():
                            self.next_char = 5*self.delay
                        else:
                            self.next_char = 2
                    self._lc = char
        else:
            self.next_char -= 1
        if assets.portrait:
            if self.next_char>10 or self.nextline:
                assets.portrait.set_blinking()
        title = True
        self.next = 0
        if self.next==0 and len(self.written)>self.wlen:
            self.wlen = len(self.written)
            self.img = self.base.copy()
            y, stx, inc = 6, 6, 18
            x = stx
            color = self.color
            center = False
            lines = self.written.split("\n")
            for i,line in enumerate(lines):
                if title:
                    if line.strip():
                        ncolor = assets.variables.get("_nt_text_color","")
                        if ncolor:
                            ncolor = color_str(ncolor)
                        else:
                            ncolor = color
                        nt_image = arial10.render(line.capitalize().replace("_"," "),1,ncolor)
                        self.nt_text_image = nt_image
                    title = False
                else:
                    img = font.render(line,color)
                    color = font.lastcolor
                    if "{center}" in line:
                        center = not center
                    if center:
                        x = (sw-img.get_width())//2
                    self.img.blit(img,[x,y])
                    y+=inc
                    x = stx
            self.next = self.num_lines
        if self.nextline:
            pass
        if self.blocking: return True
        return
        
class uglyarrow(fadesprite):
    def __init__(self):
        fadesprite.__init__(self,x=0,y=sh)
        self.load("bg/main")
        self.arrow = sprite(0,0).load("general/arrow_big.png")
        self.button = None
        self.double = None
        self.textbox = None
        self.pri = -1000
        self.width = self.iwidth = sw
        self.height = self.iheight = sh
        self.high = False
        self.showleft = True
    def update(self):
        self.pos[1] = sh
        low = assets.variables.get("_bigbutton_img","general/buttonpress.png")
        high = low.rsplit(".")
        high[0]+="_high"
        high = high[0]+"."+high[1]
        if self.textbox and self.textbox.statement:
            if not self.double:
                self.double = sprite(0,0).load("general/cross_exam_buttons.png")
                self.button = None
        else:
            self.double = None
        if not self.double and (not self.button or self.button.name not in [low.rsplit(".")[0],high.rsplit(".")[0]]):
            self.button = sprite(0,0).load(assets.variables.get("_bigbutton_img","general/buttonpress.png"))
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
            return
        if self.double:
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
                self.arrow.pos[0] = (sw-self.arrow.img.get_width())//2+75
                self.arrow.pos[1] = (sh-self.arrow.img.get_height())//2+sh
                self.arrow.img = pygame.transform.flip(self.arrow.img,1,0)
                self.arrow.draw(dest)
            return
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
                self.high = False
                self.button = sprite(0,0).load(assets.variables.get("_bigbutton_img","general/buttonpress.png"))
    def click_down_over(self,mp):
        #BAD - send clicks to record button
        for widget in assets.cur_script.obs:
            if hasattr(widget,"recordb"):
                if widget.recordb.click_down_over(mp):
                    return
        gui.window.focused = self
        over = self.over(mp)
        if over == True and not self.high and self.can_click():
            self.high = True
            high = assets.variables.get("_bigbutton_img","general/buttonpress.png")
            high = high.rsplit(".")
            high[0]+="_high"
            high = high[0]+"."+high[1]
            self.button = sprite(0,0).load(high)
        if over == "left" and self.can_click() and self.showleft:
            self.textbox.k_left()
        if over == "right" and self.can_click():
            self.textbox.k_right()
    def click_up_over(self,mp):
        if self.high:
            self.high = False
            self.button = sprite(0,0).load(assets.variables.get("_bigbutton_img","general/buttonpress.png"))
            if self.can_click():
                self.textbox.enter_down()
    def can_click(self):
        return self.textbox and not getattr(self.textbox,"kill",0) and self.textbox.can_continue()
            
class menu(fadesprite,gui.widget):
    z = 5
    fail = "none"
    id_name = "invest_menu"
    def over(self,mp):
        oy = other_screen(0)
        for o in self.options:
            p2 = self.opos[o]
            w,h = self.opt.get_width()//2,self.opt.get_height()//2
            if mp[0]>=p2[0] and mp[0]<=p2[0]+w and mp[1]>=p2[1] and mp[1]<=p2[1]+h:
                return o
    def move_over(self,pos,rel,buttons):
        if buttons[0]:
            self.click_down_over(pos)
    def click_down_over(self,mp):
        gui.window.focused = self
        if self.recordb.click_down_over(mp):
            return
        o = self.over(mp)
        if o is not None:
            self.selected = o
    def click_up(self,mp):
        o = self.over(mp)
        if self.selected==o and o is not None:
            self.enter_down()
    def save(self):
        return pickle.dumps([self.z,self.pri,self.options,self.selected,self.scene])
    def restore(self,s):
        self.z,self.pri,self.options,self.selected,self.scene = pickle.loads(s)
    def __init__(self):
        self.bg = None
        oy = other_screen(0)
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
        self.opos = {"examine":[stx,sty+oy],"move":[stx+self.opt.get_width()/2,sty+oy],
            "talk":[stx,sty+self.opt.get_height()/2+oy],"present":[stx+self.opt.get_width()/2,sty+self.opt.get_height()/2+oy]}
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
        self.recordb = record_button(assets.cur_script)
        self.open_script = True
    def k_tab(self):
        self.recordb.click_down_over([256,0])
    def update(self):
        if not self.options:
            self.kill = 1
        fadesprite.update(self)
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
    def k_left(self):
        coord = self.get_coord()
        coord[0]-=1
        if coord[0]<0:
            coord[0] = 1
        sel = self.opos_l[coord[1]][coord[0]]
        if sel in self.options:
            self.selected = sel
    def k_up(self):
        coord = self.get_coord()
        coord[1]-=1
        if coord[1]<0:
            coord[1] = 1
        sel = self.opos_l[coord[1]][coord[0]]
        if sel in self.options:
            self.selected = sel
    def k_down(self):
        coord = self.get_coord()
        coord[1]+=1
        if coord[1]>1:
            coord[1] = 0
        sel = self.opos_l[coord[1]][coord[0]]
        if sel in self.options:
            self.selected = sel
    def enter_down(self):
        if self.open_script:
            print "INITIALIZE MENU SCENE"
            assets.cur_script.init(self.scene+"."+self.selected)
        else:
            print "TRY TO JUMP TO LABEL"
            assets.cur_script.goto_result(self.selected,backup=self.fail)
        self.kill = 1
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
        if self.bg:
            dest.blit(self.bg,self.pos)
        self.pos = [0,other_screen(0)]
        fadesprite.draw(self,dest)
        if not hasattr(self,"fade") or self.fade>=self.max_fade:
            for o in self.options:
                if self.selected == o:
                    dest.blit(self.oimgshigh[o],self.opos[o])
                else:
                    dest.blit(self.oimgs[o],self.opos[o])
        self.recordb.draw(dest)

class listmenu(fadesprite,gui.widget):
    fail = "none"
    id_name = "list_menu_id"
    def over(self,mp):
        if getattr(self,"kill",0):
            return False
        x = (sw-self.choice.img.get_width())/2
        y = other_screen(30)
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
        if self.recordb.click_down_over(mp):
            return
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
    def __init__(self,tag=None):
        self.pri = ulayers.index(self.__class__.__name__)
        x,y = 0,other_screen(0)
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
        self.recordb = record_button(assets.cur_script)
    def k_tab(self):
        if getattr(self,"kill",0):
            return False
        self.recordb.click_down_over([256,0])
    def save(self):
        return pickle.dumps([self.options,self.si,self.selected,self.hidden,self.tag])
    def restore(self,s):
        self.options,self.si,self.selected,self.hidden,self.tag = pickle.loads(s)
    def update(self):
        if getattr(self,"kill",0):
            return False
        fadesprite.update(self)
        if self.hidden:
            return False
        if not hasattr(self,"bck") and vtrue(assets.variables.get("_list_back_button","true")):
            self.bck = guiBack()
            self.bck.pos[1] = other_screen(self.bck.pos[1])
            self.bck.pri = 1000
            def k_space(b=self.bck):
                b.kill = 1
                self.kill = 1
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
    def k_down(self):
        if getattr(self,"kill",0):
            return False
        self.si += 1
        if self.si>=len(self.options):
            self.si = 0
        self.selected = self.options[self.si]
    def enter_down(self):
        if getattr(self,"kill",0):
            return False
        if self.tag:
            assets.lists[self.tag][self.selected[0]] = 1
        self.kill = 1
        if hasattr(self,"bck"):
            self.bck.kill = 1
        if self.selected[1] != "Back":
            assets.variables["_selected"] = self.selected[1]
            assets.cur_script.goto_result(self.selected[1],backup=self.fail)
        else:
            assets.variables["_selected"] = "Back"
    def draw(self,dest):
        if getattr(self,"kill",0):
            return False
        if not self.selected and self.options:
            self.selected = self.options[self.si]
        fadesprite.draw(self,dest)
        x = (sw-self.choice.img.get_width())/2
        y = other_screen(30)
        #self.choice.setfade(200)
        #self.choice_high.setfade(200)
        try:
            checkmark = sprite().load(assets.variables.get("_list_checked_img","general/checkmark"))
        except:
            checkmark = None
        for c in self.options:
            if 0:#self.selected == c:
                img = self.choice_high.img.copy()
            else:
                img = self.choice.img.copy()
            rt = c[0]
            if (not (checkmark and checkmark.width)) and self.tag and assets.lists[self.tag].get(rt,None):
                rt = "("+rt+")"
            txt = font.render(rt,[110,20,20])
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
                cx = int(assets.variables.get("_list_checked_x","-10"))
                cy = int(assets.variables.get("_list_checked_y","-10"))
                dest.blit(checkmark.base[0],[x+cx,y+cy])
            y+=self.choice.img.get_height()+5
        self.recordb.draw(dest)
    def k_space(self):
        if getattr(self,"kill",0):
            return False
        if hasattr(self,"bck") or "Back" in self.options:
            if hasattr(self,"bck"):
                self.bck.kill = 1
            self.kill = 1

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
                assets.load_game(self.path+"/"+self.options[self.choice])
    def get_script(self,fullpath):
        dname = os.path.split(fullpath)[1]
        for test in [[fullpath+"/intro.txt","intro"],[fullpath+"/"+dname+".txt",dname]]:
            if os.path.exists(test[0]):
                return test[1]
    def __init__(self,path="games",**kwargs):
        if getattr(self,"reload",None):
            intro = os.path.join(self.path,"intro")
            if os.path.exists(intro+".txt"):
                assets.game = self.path
                scr = assets.Script()
                scr.init("intro")
                assets.stack = [scr]
                return
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
                word = assets.open_font("arial.ttf",16).render(word,1,[200,100,100])
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
            #txt = assets.open_font("arial.ttf",16).render(o.replace("_"," "),1,[200,100,100])
            #spr.blit(txt,[(spr.get_width()-txt.get_width())/2,(spr.get_height()-txt.get_height())/2])
            self.option_imgs.append([spr,[x,y]])
            
            txt = assets.open_font("arial.ttf",14).render("New game",1,[200,100,100])
            spr = pygame.transform.scale(base,[base.get_width(),base.get_height()//2])
            spr.blit(txt,[(spr.get_width()-txt.get_width())/2,(spr.get_height()-txt.get_height())/2])
            self.option_imgs.append([spr,[x,y+60]])
            if os.path.exists(self.path+"/"+o+"/save.ns"):
                txt = assets.open_font("arial.ttf",14).render("Resume Game",1,[200,100,100])
                spr = pygame.transform.scale(base,[base.get_width(),base.get_height()//2])
                spr.blit(txt,[(spr.get_width()-txt.get_width())/2,(spr.get_height()-txt.get_height())/2])
                self.option_imgs.append([spr,[x,y+90]])
            elif os.path.exists(self.path+"/"+o+"/save"):
                txt = assets.open_font("arial.ttf",14).render("Resume Game",1,[200,100,100])
                spr = pygame.transform.scale(base,[base.get_width(),base.get_height()//2])
                spr.blit(txt,[(spr.get_width()-txt.get_width())/2,(spr.get_height()-txt.get_height())/2])
                self.option_imgs.append([spr,[x,y+90]])
            else:
                self.option_imgs.append([None,None])
            x+=sw
        self.children = self.option_imgs
    def save(self):
        return pickle.dumps([self.path,self.options,self.width,self.height,self.choice])
    def restore(self,s):
        self.path,self.options,self.width,self.height,self.choice = pickle.loads(s)
        self.init_options()
    def update(self):
        if self.reload:
            self.option_imgs = []
            self.__init__(self.path)
        if self.x<self.choice*sw:
            self.x+=20
            if self.x>self.choice*sw:
                self.x=self.choice*sw
        if self.x>self.choice*sw:
            self.x-=20
            if self.x<self.choice*sw:
                self.x=self.choice*sw
        return True
    def k_right(self):
        if self.choice<len(self.options)-1:
            self.choice += 1
        self.case_screen()
    def k_left(self):
        if self.choice>0:
            self.choice -= 1
        self.case_screen()
    def case_screen(self):
        if os.path.exists(os.path.join(self.path,self.options[self.choice],"case_screen.txt")):
            scr = assets.Script()
            scr.parent = assets.cur_script
            assets.stack.append(scr)
            assets.cur_script.init()
            assets.cur_script._game("",os.path.join(self.path,self.options[self.choice]),script="case_screen")
            assets.cur_script.world = scr.parent.world
    def enter_down(self):
        f = open(os.path.join(self.path,"last"),"w")
        f.write(str(self.choice))
        f.close()
        assets.show_load()
        assets.clear()
        assets.stack.append(assets.Script())
        assets.cur_script.init()
        path = os.path.join(self.path,self.options[self.choice])
        assets.cur_script._game("",path,script=self.get_script(path))
        self.reload = True
    def draw(self,dest):
        if self.reload:
            return
        if not self.tried_case:
            self.case_screen()
            self.tried_case = 1
        for s,p in self.option_imgs:
            if not s: continue
            #~ for k in s.texture.names:
                #~ if s.texture.names[k]>1:
                    #~ print k,s.texture.names[k]
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
            self.mx,self.my = [pos[0],pos[1]-other_screen(0)]
            if self.mx>sw-81 and self.my>sh-33 and self.selected and self.selected[0] != 'none':
                self.enter_down()
            self.highlight()
    def click_down_over(self,mp):
        gui.window.focused = self
        if self.hide or self.selected == ["none"] or mp[0]<175 or mp[1]-other_screen(0)<159:
            self.move_over(mp,None,None)
    def click_up(self,mp):
        if gui.window.focused == self:
            self.enter_down()
            gui.window.over = None
            gui.window.focused = None
    def __init__(self,hide=False):
        self.pri = -2000
        sprite.__init__(self)
        self.pos = [0,other_screen(0)]
        self.width = sw
        self.height = sh
        gui.widget.__init__(self,[0,other_screen(0)],[sw,sh])
        self.img = assets.Surface([64,64])
        self.regions = []
        self.mouse = pygame.Surface([10,10])
        self.mouse.fill([100,100,100])
        self.selected = ["none"]
        self.mx,self.my = sw/2,sh/2
        self.check = assets.open_art("general/check"+assets.appendgba,key=[255,0,255])[0]
        self.hide = hide
        self.bg = []
        if not assets.variables.get("_examine_use",None):
            self.bg = [x for x in assets.cur_script.obs if isinstance(x,bg)]
        else:
            self.bg = [x for x in assets.cur_script.obs if getattr(x,"id_name",None) == assets.variables["_examine_use"]]
            print self.bg
        self.fg = assets.open_art("general/examinefg")[0]
        self.xscroll = 0
        self.xscrolling = 0
        self.blocking = not vtrue(assets.variables.get("_examine_skipupdate","0"))
        #self.recordb = record_button(assets.cur_script)
    #~ def k_tab(self):
        #~ self.recordb.click_down_over([256,0])
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
    def save(self):
        return pickle.dumps([self.regions,self.hide])
    def restore(self,s):
        self.regions,self.hide = pickle.loads(s)
    def addregion(self,x,y,width,height,label):
        reg = [int(x),int(y),int(width),int(height),label]
        self.regions.append(reg)
        self.highlight()
    def highlight(self):
        self.selected = ["none"]
        for reg in self.regions:
            if self.mx>reg[0]+self.getoffset() and self.my>reg[1] and \
            self.mx<reg[0]+self.getoffset()+reg[2] and self.my<reg[1]+reg[3]:
                self.selected = reg
                return
    def draw(self,dest):
        self.highlight()
        if not assets.variables.get("_examine_use",None):
            [dest.blit(o.img,[o.pos[0],other_screen(o.pos[1])]) for o in self.bg]
        my = other_screen(self.my)
        if vtrue(assets.variables.get("_examine_showcursor", "true")):
            pygame.draw.line(dest,[255,255,255],[0,my],[self.mx-5,my])
            pygame.draw.line(dest,[255,255,255],[self.mx+5,my],[sw,my])
            pygame.draw.line(dest,[255,255,255],[self.mx,other_screen(0)],[self.mx,my-5])
            pygame.draw.line(dest,[255,255,255],[self.mx,my+5],[self.mx,other_screen(sh)])
            pygame.draw.rect(dest,[255,255,255],[[self.mx-5,my-5],[10,10]],1)
        if vtrue(assets.variables.get("_examine_showbars", "true")):
            dest.blit(self.fg,[0,other_screen(0)])
        if self.selected != ["none"] and not self.hide:
            dest.blit(self.check,[sw-self.check.get_width()+3,other_screen(sh-self.check.get_height())])
        if vtrue(assets.variables.get("_debug","false")):
            x = int(assets.variables.get("_examine_offsetx",0))
            y = int(assets.variables.get("_examine_offsety",0))
            tb = textblock("offsetx:%s offsety%s"%(x,y),[0,192],[256,20],[255,255,255])
            tb.draw(dest)
        #self.recordb.draw(dest)
    def update(self,*args):
        if self.xscrolling:
            assets.cur_script.obs.append(scroll(-self.xscrolling,0,16))
            self.xscrolling = 0
            if hasattr(self,"scrollbut"):
                self.scrollbut.kill = 1
                del self.scrollbut
            return
        keys = pygame.key.get_pressed()
        spd = 3
        d = [0,0]
        if keys[pygame.K_LEFT]:
            d[0]-=3
        if keys[pygame.K_RIGHT]:
            d[0]+=3
        if keys[pygame.K_UP]:
            d[1]-=3
        if keys[pygame.K_DOWN]:
            d[1]+=3
        self.mx+=d[0]
        self.my+=d[1]
        if self.mx-5<0: self.mx=5
        if self.mx+5>sw: self.mx=sw-5
        if self.my-5<0: self.my=5
        if self.my+5>sh: self.my=sh-5
        if assets.variables.get("_examine_scrolling",None)=="perceive":
            def add(p):
                x.pos[0]-=d[0]
                x.pos[1]-=d[1]
            [add(x) for x in self.bg]
            x = int(assets.variables.get("_examine_offsetx",0))
            y = int(assets.variables.get("_examine_offsety",0))
            x-=d[0]
            y-=d[1]
            assets.variables["_examine_offsetx"] = str(x)
            assets.variables["_examine_offsety"] = str(y)
            self.highlight()
            return False
        self.highlight()
        if not hasattr(self,"bck") and not self.hide:
            self.bck = guiBack()
            self.bck.pos = [0,other_screen(sh-self.bck.img.get_height())]
            self.bck.pri = 1000
            def k_space(b=self.bck):
                b.kill = 1
                self.kill = 1
                if hasattr(self,"scrollbut"): self.scrollbut.kill = 1
            self.bck.k_space = k_space
            assets.cur_script.obs.append(self.bck)
        scrn = (-self.getoffset()//sw)+1
        self.xscroll = None
        if scrn<self.screens():
            self.xscroll = 1
        elif scrn>1:
            self.xscroll = -1
        if not self.xscroll and hasattr(self,"scrollbut"): 
            self.scrollbut.kill = 1
            del self.scrollbut
        if self.xscroll and not hasattr(self,"scrollbut"):
            self.scrollbut = guiScroll(self.xscroll)
            self.scrollbut.parent = self
            assets.cur_script.obs.append(self.scrollbut)
        return self.blocking
    def enter_down(self):
        print self.selected,self.regions,self.mx,self.my
        assets.variables["_examine_clickx"] = str(self.mx)
        assets.variables["_examine_clicky"] = str(self.my)
        assets.cur_script.goto_result(self.selected[-1],backup=self.fail)
        self.die()
        self.kill = 1
    def k_space(self):
        if not self.hide:
            self.die()
    def die(self):
        self.kill = 1
        if hasattr(self,"bck"):
            self.bck.kill = 1
        if hasattr(self,"scrollbut"):
            self.scrollbut.kill = 1

class evidence_menu(fadesprite,gui.widget):
    fail = "none"
    #~ def move_over(self,pos,rel,buttons):
        #~ self.mx,self.my = pos
        #~ self.highlight()
    def click_down_over(self,mp):
        gui.window.focused = self
    def click_up(self,mp):
        mp[1]-=other_screen(0)
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
            if self.mode=="zoomed":
                self.k_left()
        if mp[0]>=238 and mp[1]>=56 and mp[1]<=149:
            if self.mode=="overview" and len(self.pages)>1:
                self.page_next()
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
        if self.can_present():
            mp[1]+=other_screen(0)
            self.present_button.draw(assets.Surface([64,64]))
            sb = self.present_button
            if mp[0]>=sb.pos[0] and mp[0]<=sb.pos[0]+sb.width and mp[1]>=sb.pos[1] and mp[1]<=sb.pos[1]+sb.height:
                self.k_x()
        #~ self.enter_down()
        #~ gui.window.over = None
        #~ gui.window.focused = None
    def load(self,*args,**kwargs):
        fadesprite.load(self,*args,**kwargs)
    def init_vars(self):
        defs = {"ev_present_x":90, "ev_present_y":0, #Where present button placed
        "ev_show_mode_text":"true", #Show the text describing the mode
        "ev_mode_bg_evidence":"general/evidence", #Background image in evidence mode
        "ev_mode_bg_profiles":"general/evidence", #Background image in profile mode
        "ev_mode_x":4,
        "ev_mode_y":20,
        "ev_cursor_img":"general/cursor_ev",
        "ev_currentname_x":40,"ev_currentname_y":39,
        "ev_modebutton_x":196,"ev_modebutton_y":7,
        "ev_items_x":38,
        "ev_items_y":63,
        "ev_spacing_x":48,
        "ev_spacing_y":46,
        "ev_larrow_x":2,
        "ev_larrow_y":90,
        "ev_rarrow_x":240,
        "ev_rarrow_y":90,
        "ev_arrow_img":"general/arrow_right",
        "ev_zarrow_img":"general/arrow_right",
        "ev_zlarrow_x":2,
        "ev_zlarrow_y":90,
        "ev_zrarrow_x":240,
        "ev_zrarrow_y":90,
        "ev_check_img":"general/check",
        "ev_z_textbox_x": 100,
        "ev_z_textbox_y": 70,
        "ev_z_textbox_w": 130,
        "ev_z_textbox_h": 100,
        "ev_z_icon_x": 25,
        "ev_z_icon_y": 60,
        "ev_z_bg": "general/evidence_zoom",
        "ev_z_bg_x": 0,
        "ev_z_bg_y": 0,
        }
        for k in defs:
            if not k in assets.variables:
                assets.variables[k] = defs[k]
    def __init__(self,items=[],gba=True):
        self.init_vars()
        x,y = 0,other_screen(0)
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
        self.back_button.pos[1] = other_screen(self.back_button.pos[1])
        self.back_button.pri = 1000
        def k_space(b=self.back_button):
            b.kill = 1
            self.kill = 1
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

        self.item_set = "evidence"
        
        self.present_button = present_button(self)
        self.present_button.pos = [int(assets.variables["ev_present_x"]),
                    other_screen(int(assets.variables["ev_present_y"]))]
        if not (vtrue(assets.variables.get("_profiles_enabled","true")) or vtrue(assets.variables.get("_evidence_enabled","true"))):
            self.kill = 1
        if not vtrue(assets.variables.get("_profiles_enabled","true")):
            self.item_set = "evidence"
        if not vtrue(assets.variables.get("_evidence_enabled","true")):
            self.item_set = "profiles"
        self.layout()
    def save(self):
        return ""
    def restore(self,s):
        return
    def update(self):
        self.choose()
        if not getattr(self,"kill",None) and not getattr(self,"hidden",None):
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
    def page_prev(self):
        self.page-=1
        if self.page<0:
            self.page = len(self.pages)-1
        page = self.pages[self.page]
        self.sy = len(page)-1
        self.sx = len(page[self.sy])-1
    def page_next(self):
        self.page += 1
        if self.page>len(self.pages)-1:
            self.page = 0
        self.sx = 0
        page = self.pages[self.page]
        if self.sy>len(page)-1:
            self.sy = 0
    def k_left(self):
        if self.page>=len(self.pages): return
        self.load(assets.variables["ev_mode_bg_"+self.item_set]+assets.appendgba)
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
        self.choose()
    def k_right(self):
        if self.page>=len(self.pages): return
        self.load(assets.variables["ev_mode_bg_"+self.item_set]+assets.appendgba)
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
        self.choose()
    def k_up(self):
        self.load(assets.variables["ev_mode_bg_"+self.item_set]+assets.appendgba)
        if self.mode == "overview":
            if self.sy == 0:
                self.switch = True
            elif self.sy==1:
                self.sy = 0
            if self.back:
                self.sy = 1
            if self.page>=len(self.pages) or self.sy>len(self.pages[self.page])-1:
                self.sy = 0
        elif not self.back:
            self.switch = True
        self.back = False
        self.back_button.unhighlight()
        self.choose()
    def k_down(self):
        if self.mode == "overview":
            self.back = False
            self.back_button.unhighlight()
            if not self.switch:
                self.sy+=1
            self.switch = False
            if self.page>=len(self.pages) or self.sy>=len(self.pages[self.page]) and self.canback():
                self.back = True
                self.back_button.highlight()
        elif self.mode == "zoomed":
            if self.switch == False and self.canback():
                self.back = True
                self.back_button.highlight()
            self.switch = False
        self.choose()
    def choose(self):
        if self.back and self.canback():
            self.load(assets.variables["ev_mode_bg_"+self.item_set]+"_back"+assets.appendgba)
        elif self.switch:
            self.load(assets.variables["ev_mode_bg_"+self.item_set]+"_profile"+assets.appendgba)
        else:
            self.load(assets.variables["ev_mode_bg_"+self.item_set]+assets.appendgba)
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
    def enter_down(self):
        if self.switch:
            self.k_z()
        elif self.back and self.canback():
            if self.mode == "overview":
                self.kill = 1
            elif self.mode == "zoomed":
                if assets.gbamode: self.kill = 1
                else: self.mode = "overview"
            elif self.mode == "check":
                self.mode = "overview"
        else:
            if self.mode == "overview":
                self.mode = "zoomed"
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
        assets.cur_script.goto_result((self.chosen+" "+assets.cur_script.statement).strip(),backup=self.fail)
        self.kill = 1
        for o in assets.cur_script.obs:
            if isinstance(o,textbox):
                o.kill = 1
    def k_z(self):
        if not vtrue(assets.variables.get("_evidence_enabled","true")):
            return
        if not vtrue(assets.variables.get("_profiles_enabled","true")):
            return
        self.chosen = None
        modes = {"evidence":"profiles","profiles":"evidence"}
        self.item_set = modes[self.item_set]
        self.layout()
        #if not self.pages: self.item_set = modes[self.item_set]
        #self.layout()
        self.switch = False
    def k_space(self):
        if self.mode=="zoomed":
            if assets.gbamode: self.kill = 1
            else: self.mode = "overview"
        elif self.mode=="overview" and vtrue(assets.variables.get("_cr_back_button", "true")):
            self.kill = 1
        #assets.cur_script.cross = ""
        #assets.cur_script.instatement = False
    def canback(self):
        show_back = vtrue(assets.variables.get("_cr_back_button", "true"))
        if self.mode!="overview" or show_back:
            return True
        return False
    def draw(self,dest):
        if assets.gbamode: self.mode = "zoomed"
        dest.blit(self.img,self.pos)
        x,y=self.pos
        if not assets.gbamode:
            if vtrue(assets.variables["ev_show_mode_text"]):
                dest.blit(font.render(self.item_set.capitalize(),[255,255,255]),
                [x+assets.variables["ev_mode_x"],y+assets.variables["ev_mode_y"]])
        name = ""
        if self.chosen:
            name = assets.variables.get(self.chosen+"_name",self.chosen).replace("$","")
        if not assets.gbamode or self.mode != "zoomed":
            dest.blit(font.render(name,[255,255,255]),
            [x+int(assets.variables["ev_currentname_x"]),y+int(assets.variables["ev_currentname_y"])])
        if vtrue(assets.variables.get("_evidence_enabled","true")) and vtrue(assets.variables.get("_profiles_enabled","true")):
            dest.blit(arial14.render(
                {"evidence":"profiles","profiles":"evidence"}[self.item_set],1,[255,255,255]),
                [x+int(assets.variables["ev_modebutton_x"]),y+int(assets.variables["ev_modebutton_y"])])
        if self.can_present():
            self.present_button.draw(dest)
        page = []
        if self.pages:
            page = self.pages[self.page]
        if self.mode != "zoomed":
            cx,cy=0,0
            sx = self.pos[0]+int(assets.variables["ev_items_x"])
            sy = self.pos[1]+int(assets.variables["ev_items_y"])
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
                dest.blit(arr,[self.pos[0]+int(assets.variables["ev_rarrow_x"]),
                            self.pos[1]+int(assets.variables["ev_rarrow_y"])])
                dest.blit(pygame.transform.flip(arr,1,0),
                    [self.pos[0]+int(assets.variables["ev_larrow_x"]),
                    self.pos[1]+int(assets.variables["ev_larrow_y"])])
        if self.mode == "zoomed":
            showarrow = 0
            for p in self.pages:
                for line in p:
                    for icon in line:
                        showarrow += 1
            if showarrow>1:
                if not getattr(self,"arr",None):
                    self.arr = assets.open_art(assets.variables["ev_zarrow_img"])[0]
                dest.blit(self.arr,[self.pos[0]+int(assets.variables["ev_zrarrow_x"]),
                                self.pos[1]+int(assets.variables["ev_zrarrow_y"])])
                dest.blit(pygame.transform.flip(self.arr,1,0),
                    [self.pos[0]+int(assets.variables["ev_zlarrow_x"]),
                    self.pos[1]+int(assets.variables["ev_zlarrow_y"])])
            if getattr(self,"chosen_icon",None) and getattr(self,"chosen",None):
                if self.scroll:
                    self.scroll -= 16
                    self.draw_ev_zoom(self.lastchoose,[(256-self.scroll+self.pos[0])*self.scroll_dir,self.pos[1]],dest)
                    self.draw_ev_zoom(self.chosen_icon,[256*(-self.scroll_dir)+(256-self.scroll+self.pos[0])*self.scroll_dir,self.pos[1]],dest)
                else:
                    self.draw_ev_zoom(self.chosen_icon,self.pos[:],dest)
                chk = assets.variables.get(self.chosen+"_check",None)
                if chk:
                    check = assets.open_art(assets.variables["ev_check_img"]+assets.appendgba)[0]
                    dest.blit(check,[self.pos[0]+sw-check.get_width(),self.pos[1]+sh-check.get_height()])
            else:
                self.mode = "overview"
        if self.canback():
            self.back_button.draw(dest)
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
                newsurf.blit(font.render(name,[255,255,0]),[103,65])
            tb = textblock(icon.desc,[tbpos[0],tbpos[1]],tbsize,[1,1,1])
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
    def save(self):
        return pickle.dumps([self.text,self.lines,self.pos,self.size,self.color])
    def restore(self,s):
        self.text,self.lines,self.pos,self.size,self.color = pickle.loads(s)
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
                    wordi = arial10.render(word,1,self.color)
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
        self.pri = -1000
    def save(self):
        return ""
    def restore(self,s):
        pass
    def draw(self,dest): pass
    def update(self):
        return True
    def enter_down(self):
        self.kill = 1
                
class delay(sprite):
    def __init__(self,ticks=1):
        super(delay,self).__init__()
        self.ticks = abs(ticks)
        self.pri = 10000
    def save(self):
        return ""
    def restore(self,s):
        pass
    def draw(self,dest): pass
    def update(self):
        if self.ticks<=0:
            self.kill = 1
            return False
        self.ticks-=1
        return True
        
class timer(sprite):
    def __init__(self,ticks=1,run=None):
        sprite.__init__(self)
        self.ticks = abs(ticks)
        self.pri = 0
        self.run = run
        self.script = assets.cur_script
    def update(self):
        if self.ticks<=0:
            self.kill = 1
            if self.run:
                ns = self.script.execute_macro(self.run)
        self.ticks-=1
        assets.variables["_timer_value_"+self.run] = str(self.ticks)
        
class effect(object):
    def __init__(self):
        self.z = zlayers.index(self.__class__.__name__)
                
class scroll(effect):
    def __init__(self,amtx=1,amty=1,speed=1,wait=1,filter="top"):
        super(scroll,self).__init__()
        self.amtx = abs(amtx)
        self.amty = abs(amty)
        self.dx=self.dy=0
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
        self.dx*=speed
        self.dy*=speed
        self.pri = -3000
        self.speed = speed
        self.obs = assets.cur_script.obs
        self.filter = filter
        self.wait = wait
    def save(self):
        return ""
    def restore(self,s):
        pass
    def draw(self,dest): pass
    def update(self):
        if self.amtx<=0 and self.amty<=0:
            self.kill = 1
            return False
        ndx,ndy = self.dx,self.dy
        self.amtx-=abs(self.dx)
        if self.amtx<0: 
            ndx+=self.amtx
            self.amtx=0
        self.amty-=abs(self.dy)
        if self.amty<0:
            ndy+=self.amty
            self.amty=0
        for o in self.obs:
            if getattr(o,"kill",0): continue
            if hasattr(o,"pos") and (not self.filter or self.filter=="top" and o.pos[1]<192 or self.filter=="bottom" and o.pos[1]>=192):
                o.pos[0]+=ndx
                o.pos[1]+=ndy
        if self.wait:
            return True
    def control_last(self):
        for o in reversed(assets.cur_script.obs):
            if hasattr(o,"pos") and not getattr(o,"kill",0):
                self.obs = [o]
                return
    def control(self,name):
        self.filter = None
        for o in reversed(assets.cur_script.obs):
            if getattr(o,"id_name",None)==name:
                self.obs = [o]
                return
                
class zoomanim(effect):
    def __init__(self,mag=1,frames=1,wait=1,name=None):
        super(zoomanim,self).__init__()
        self.mag=mag
        self.pri = -1000
        self.frames = frames
        self.obs = assets.cur_script.obs
        self.mag_per_frame = float(self.mag)/float(self.frames)
        self.wait = wait
        self.kill = 0
        if name:
            self.obs = [o for o in self.obs if getattr(o,"id_name",None)==name]
    def save(self):
        return ""
    def restore(self,s):
        pass
    def draw(self,dest): pass
    def update(self):
        if self.kill: return False
        self.frames -= 1
        if self.frames <= 0:
            self.kill = 1
        for o in self.obs:
            if getattr(o,"kill",0): continue
            if hasattr(o,"dim"):
                o.dim += self.mag_per_frame
        if self.wait:
            return True
    def control_last(self):
        for o in reversed(assets.cur_script.obs):
            if hasattr(o,"pos") and not getattr(o,"kill",0):
                self.obs = [o]
                return
    def control(self,name):
        self.filter = None
        for o in reversed(assets.cur_script.obs):
            if getattr(o,"id_name",None)==name:
                self.obs = [o]
                return

class rotateanim(effect):
    def __init__(self,axis="z",degrees=90,speed=1,wait=1,name=None,obs=[]):
        super(rotateanim,self).__init__()
        self.axis = {"x":0,"y":1,"z":2,0:0,1:1,2:2}[axis]
        self.degrees = degrees
        self.pri = -1000
        self.speed = speed
        self.obs = obs
        self.wait = wait
        self.kill = 0
        if name:
            self.obs = [o for o in self.obs if getattr(o,"id_name",None)==name]
    def save(self):
        return ""
    def restore(self,s):
        pass
    def draw(self,dest): pass
    def update(self):
        if self.kill: return False
        amt = self.speed
        if self.degrees>0:
            self.degrees-=amt
            if self.degrees<=0:
                self.kill = 1
                amt+=self.degrees
            amt = -amt
        elif self.degrees<0:
            self.degrees+=amt
            if self.degrees>=0:
                self.kill = 1
                amt-=self.degrees
        else:
            self.kill = 1
        for o in self.obs:
            if getattr(o,"kill",0): continue
            if hasattr(o,"rot"):
                o.rot[self.axis] += amt
        if self.wait:
            return True

class fadeanim(effect):
    def __init__(self,start=0,end=100,speed=1,wait=1,name=None,obs=[]):
        super(fadeanim,self).__init__()
        self.start = start
        self.end = end
        self.pri = -1000
        self.speed = speed
        self.obs = obs
        self.wait = wait
        self.kill = 0
        if name:
            self.obs = [o for o in self.obs if getattr(o,"id_name",None)==name]
        self.update()
    def save(self):
        return ""
    def restore(self,s):
        pass
    def draw(self,dest): pass
    def update(self):
        if self.kill: return False
        amt = self.speed
        if self.start<self.end:
            self.start+=amt
            if self.start>self.end:
                amt -= (self.start-self.end)
                self.kill = 1
        elif self.start>self.end:
            self.start-=amt
            if self.start<self.end:
                amt-=(self.end-self.start)
                self.kill=1
        else:
            self.kill=1
        for o in self.obs:
            if getattr(o,"kill",0): continue
            if hasattr(o,"setfade"):
                o.setfade(int((self.start/100.0)*255.0))
        if self.wait:
            return True

class flash(effect):
    pri = -1000
    def __init__(self):
        super(flash,self).__init__()
        self.ttl = 5
        self.color = [255,255,255]
        self.surf = pygame.Surface(pygame.screen.get_size())
        if vtrue(assets.variables.get("_flash_sound","false")):
            assets.play_sound("Slash.ogg")
    def save(self):
        return ""
    def restore(self,s):
        pass
    def draw(self,dest):
        self.surf.fill(self.color)
        dest.blit(self.surf,[0,0])
    def update(self):
        self.ttl -= 1
        if self.ttl<=0: self.kill = 1
        return True
    
class shake(effect):
    pri = -1000
    def __init__(self):
        super(shake,self).__init__()
        self.ttl = 15
        self.offset = 15
        if vtrue(assets.variables.get("_shake_sound","false")):
            assets.play_sound("Shock.ogg")
    def save(self):
        return ""
    def restore(self,s):
        pass
    def draw(self,dest):
        if not hasattr(self,"scr_surf"): self.scr_surf = dest.copy()
        dest.blit(self.scr_surf,[random.randint(-self.offset,self.offset),random.randint(-self.offset,self.offset)])
    def update(self):
        self.ttl -= 1
        if self.ttl<=0: self.kill = 1
        return True
    
class notguilty(sprite):
    def __init__(self):
        sprite.__init__(self)
        self.ttl = 120
        self.pri = 1000
        self.obs = []
    def save(self):
        return ""
    def restore(self,s):
        pass
    def draw(self,dest):
        if self.ttl == 100:
            img = pygame.transform.scale(assets.open_art("general/Not")[0],[70,40])
            self.obs.append([img,[0,60]])
            assets.play_sound("Whaaa.ogg")
        if self.ttl == 50:
            img = pygame.transform.scale(assets.open_art("general/guilty")[0],[176,40])
            self.obs.append([img,[80,60]])
            assets.play_sound("Whaaa.ogg")
        [dest.blit(o[0],o[1]) for o in self.obs]
    def update(self):
        self.ttl -= 1
        if self.ttl<=0: self.kill = 1
        return True
    
class guilty(sprite):
    def __init__(self):
        sprite.__init__(self)
        self.ttl = 5*60
        self.pri = 1000
        self.i = 0
        self.img = assets.open_art("general/guilty")[0]
        self.xes = [0,41,79,104,129,160,197]
        self.obs = []
    def save(self):
        return ""
    def restore(self,s):
        pass
    def draw(self,dest):
        amt = [0,]
        if self.ttl%30==0 and self.i<len(self.xes)-1:
            img = self.img.subsurface([[self.xes[self.i],0],[self.xes[self.i+1]-self.xes[self.i],63]])
            self.obs.append([img,[self.xes[self.i]+30,60]])
            self.i += 1
            assets.play_sound("Whaaa.ogg")
        if self.ttl == 60:
            assets.play_sound("Owned.ogg")
        [dest.blit(o[0],o[1]) for o in self.obs]
    def update(self):
        self.ttl -= 1
        if self.ttl<=0: self.kill = 1
        return True
        
class guiBack(sprite,gui.widget):
    def click_down_over(self,mp):
        self.k_space()
    def __init__(self,image=None,x=None,y=None,z=None,name=None):
        sprite.__init__(self)
        gui.widget.__init__(self)
        self.pri = -1000
        if not image:
            image = "general/back"
        self.image = image
        self.unhighlight()
        self.pos = [0,sh-self.img.get_height()]
        if x is not None:
            self.pos[0] = x
        if y is not None:
            self.pos[1] = y
        if z is not None:
            self.z = z
        if name is not None:
            self.id_name = name
        gui.widget.__init__(self,self.pos,self.img.get_size())
    def highlight(self):
        self.load(self.image+"_high"+assets.appendgba)
    def unhighlight(self):
        self.load(self.image+assets.appendgba)
    def save(self):
        return ""
    def restore(self,s):
        pass
    def k_space(self):
        self.kill = 1
        print "only kill back button"
    def update(self):
        return True
        
class guiScroll(sprite,gui.widget):
    def click_down_over(self,mp):
        self.k_z()
    def __init__(self,direction):
        sprite.__init__(self,flipx=direction+1)
        gui.widget.__init__(self)
        self.pri = -1000
        self.load("general/examine_scroll")
        self.pos = [sw//2-self.img.get_width()//2,other_screen(sh-self.img.get_height())]
        gui.widget.__init__(self,self.pos,self.img.get_size())
        self.direction = direction
    def save(self):
        return ""
    def restore(self,s):
        pass
    def k_z(self):
        self.kill = 1
        self.parent.xscrolling = self.direction*sw
        #del self.parent.scrollbut
    def update(self):
        return True
        
class guiWait(sprite):
    def __init__(self,run=None):
        sprite.__init__(self)
        gui.widget.__init__(self)
        self.width = 0
        self.height = 0
        self.pri = 31
        self.pos = [0,0]
        self.run = run
        self.script = assets.cur_script
    def save(self):
        return ""
    def restore(self,s):
        pass
    def update(self):
        if self.run:
            ns = self.script.execute_macro(self.run)
        return True
        
class saved(sprite):
    def __init__(self,ticks=120,text="Game Saved!",block=True):
        super(saved,self).__init__()
        self.text = text
        self.ticks = abs(ticks)
        self.pri = -5000
        self.pos[0]=sw
        self.pos[1]=30
        self.block = block
    def save(self):
        return ""
    def restore(self,s):
        self.kill = 1
    def draw(self,dest):
        txt1 = arial14.render(self.text,1,[230,230,230])
        txt2 = arial14.render(self.text,1,[30,30,30])
        txt2 = pygame.transform.scale(txt2,[txt2.get_width()-4,txt2.get_height()-4])
        dest.blit(txt1,self.pos)
        dest.blit(txt2,[self.pos[0]+2,self.pos[1]+2])
    def update(self):
        self.pos[0]-=3
        if self.ticks<=0:
            self.kill = 1
            return False
        self.ticks-=1
        return self.block
        
class error_msg(gui.pane):
    def click_down_over(self,mp):
        self.kill = 1
    def __init__(self,msg,line,lineno,script):
        self.pri = -10000
        self.z = zlayers.index(self.__class__.__name__)
        gui.pane.__init__(self)
        msg_lines = [""]
        for c in msg:
            msg_lines[-1]+=c
            if len(msg_lines[-1])>45 or c == "\n":
                msg_lines.append("")
        for msg_line in msg_lines:
            msg = gui.editbox(None,msg_line)
            msg.draw(assets.Surface([64,64]))
            msg.draw_back=False
            self.children.append(msg)
        lineno = gui.editbox(None,assets.game+"/"+script.scene+" : line "+str(lineno))
        lineno.draw(assets.Surface([64,64]))
        lineno.draw_back=False
        self.children.append(lineno)
        self.line = '"'+line+'"'
        self.editline = gui.editbox(self,"line")
        self.editline.draw(assets.Surface([64,64]))
        self.editline.draw_back = False
        self.children.append(self.editline)
        b = gui.editbox(None,"(click to skip line)")
        b.draw(assets.Surface([64,64]))
        b.draw_back = False
        self.children.append(b)
        self.lineno = lineno
        self.script = script
        self.width=256
        self.height=100
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
        self.pri = 0
        self.z = zlayers.index(self.__class__.__name__)
        self.paused = 0
        self.id_name = name
    def update(self):
        self.paused = 0
        self.movie.play()
        if self.sound:
            self.sound.unpause()
        if self.movie.get_busy(): return True
        del self.movie
        self.kill = 1
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
