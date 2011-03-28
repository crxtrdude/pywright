import pygame

if __name__=="__main__":
    pygame.init()
    screen = pygame.display.set_mode([640,480])


textures = {}
def loadtexture(key,filename):
    filename = filename.replace("\\","/")
    textures[key] = pygame.image.load(loadtexture.path+"/"+filename.replace("characters/","")).convert_alpha()
loadtexture.comm = 1
loadtexture.path = ""
    
anims = {}

class Anim(object):
    def __init__(self):
        self.frames = {}
        self.width = 0
        self.height = 0
        self.blink = False
        self.talk = False
    def getframes(self):
        keys = self.frames.keys()
        keys.sort()
        frames = []
        for f in keys:
            frame = self.frames[f]
            if frame.img:
                frames.append(frame.img)
        return frames
class Frame(object):
    def __init__(self,texture,delay,anim):
        self.anim = anim
        self.texture = texture
        self.delay = delay
        self.img = None
def createanimation(name,x):
    anims[name]=Anim()
createanimation.comm = 1
def insertanimationframe(name,index,texture,delay):
    l = delay//50
    if l==0: l+=1
    anim = anims[name]
    texture = textures[texture]
    for i in range(l):
        frame = Frame(texture,delay,anim)
        anim.frames[index]=frame
        index+=.01
insertanimationframe.comm = 1
def setanimationframetexturecoordinates(name,index,x,y,width,height):
    anim = anims[name]
    while 1:
        if not anim.frames.has_key(index): break
        frame = anim.frames[index]
        frame.coord = [[x,y],[width,height]]
        frame.img = frame.texture.subsurface(frame.coord)
        anim.width+=frame.img.get_width()
        h = frame.img.get_height()
        if h>anim.height:
            anim.height=h
        index+=.01
setanimationframetexturecoordinates.comm = 1
def setcharacterlipsyncsilent(text,anim):
    anims[anim].blink = True
setcharacterlipsyncsilent.comm = 1
def setcharacterlipsynctalking(text,anim):
    anims[anim].talk = True
setcharacterlipsynctalking.comm = 1

funcs = dir()

def open_char(pwlib_script):
    pwlib_script = pwlib_script.replace("\\","/")
    loadtexture.path = pwlib_script.rsplit("/",1)[0]
    f = open(pwlib_script)
    for line in f.readlines():
        line = line.strip()
        if line.startswith("["): continue
        if line.startswith("//"): continue
        line = line.split("//",1)[0]
        for funcn in funcs:
            func = eval(funcn)
            if hasattr(func,'comm'):
                if line.startswith(funcn+"("):
                    line = line.replace(funcn+"(","")
                    line = line.replace(");","")
                    func(*[eval(x) for x in line.split(",")])
    f.close()