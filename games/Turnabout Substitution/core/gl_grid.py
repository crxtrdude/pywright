import pygame
import OpenGL.GL as og
import time
import math
import collada

class transformGL:
    def scale(self,ob,new_size):
        ob = ob.copy()
        newsc = [0,0,1]
        csize = [ob.width*ob.sc[0],ob.height*ob.sc[1]]
        if csize[0]!=0: newsc[0]=new_size[0]/float(csize[0])
        if csize[1]!=0: newsc[1]=new_size[1]/float(csize[1])
        ob.sc = newsc[:]
        return ob
    def rotozoom(self,ob,rot,zoom):
        ob = ob.copy()
        ob.sc[0]*=zoom
        ob.sc[1]*=zoom
        return ob
    def flip(self,ob,x=0,y=0):
        ob = ob.copy()
        if x:
            ob.sc[0] = -ob.sc[0]
        if y:
            ob.sc[1] = -ob.sc[1]
        return ob
        
def nextPowerOf2 (num):
    """ If num isn't a power of 2, will return the next higher power of two """
    rval = 1
    while (rval<num):
        rval <<= 1
    return rval

class texture(object):
    textures = {}
    def __init__(self,surf,cache=True):
        self.name = int(og.glGenTextures(1))
        self.cache = cache
        self.die = time.time()+5
        if cache: texture.textures[self.name] = self
        self.update(surf)
    def newname(self):
        if self.textures.get(self.name,None):
            del self.textures[self.name]
        self.name = og.glGenTextures(1)
        if self.cache: self.textures[self.name] = self
    def update(self,surf):
        self.width,self.height = surf.get_size()
        surfstr = pygame.image.tostring(surf,"RGBA",True)
        self.rebind_string(surfstr)
    def rebind_string(self,surfstr):
        og.glBindTexture(og.GL_TEXTURE_2D,self.name)
        #og.glTexImage2D(og.GL_TEXTURE_2D,0,og.GL_COMPRESSED_RGBA_S3TC_DXT5_EXT,self.width,self.height,0,og.GL_RGBA,og.GL_UNSIGNED_BYTE,surfstr)
        og.glTexImage2D(og.GL_TEXTURE_2D,0,og.GL_RGBA,self.width,self.height,0,og.GL_RGBA,og.GL_UNSIGNED_BYTE,surfstr)
        og.glTexParameteri(og.GL_TEXTURE_2D,og.GL_TEXTURE_MIN_FILTER,og.GL_LINEAR)
        og.glTexParameteri(og.GL_TEXTURE_2D,og.GL_TEXTURE_MAG_FILTER,og.GL_LINEAR)
        og.glTexParameteri(og.GL_TEXTURE_2D,og.GL_TEXTURE_WRAP_S,og.GL_CLAMP)
        og.glTexParameteri(og.GL_TEXTURE_2D,og.GL_TEXTURE_WRAP_T,og.GL_CLAMP)
    def replace(self,surf):
        """Replaces the texture without modifying the size"""
        og.glDeleteTextures([self.name])
        self.__init__(surf)
    def use(self):
        og.glBindTexture(og.GL_TEXTURE_2D,self.name)
        self.die = time.time()+1
    def get_width(self):
        return self.width
    def get_height(self):
        return self.height
    def get_size(self):
        return self.width,self.height
    def __del__(self):
        try:
            og.glDeleteTextures([self.name])
        except:
            pass
        try:
            del self.textures[self.name]
        except:
            pass

def init(size,fs=0):
    dotex = []
    if not hasattr(pygame,"GL_INIT"):
        pygame.GL_INIT = True
        pygame.transformold = pygame.transform
        pygame.transform = transformGL()
        pygame.drawold = pygame.draw
        pygame.draw = drawGL()
    else:
        dotex = texture.textures.values()
    
    i = 0
    for tex in dotex:
        tex.use()
        tex.texdata = og.glGetTexImage(og.GL_TEXTURE_2D,0,og.GL_RGBA,og.GL_UNSIGNED_BYTE)
        #~ s = pygame.image.fromstring(tex.texdata,[tex.width,tex.height],"RGBA")
        #~ pygame.image.save(s,"%.4d.jpg"%i)
        #~ i+=1

    try:
        scr = pygame.display.set_mode(size,
            pygame.OPENGL|pygame.DOUBLEBUF|fs*pygame.FULLSCREEN|pygame.HWSURFACE)
    except:
        scr = pygame.display.set_mode(size,
            pygame.OPENGL|pygame.DOUBLEBUF|fs*pygame.FULLSCREEN)
            
    og.glClearColor(0.0, 0.0, 0.0, 0.0)
    
    og.glMatrixMode(og.GL_PROJECTION)
    og.glLoadIdentity()
    og.glOrtho(0,size[0],0,size[1],-1000,1000)
    og.glViewport(0,0,size[0],size[1])
    
    og.glEnable(og.GL_TEXTURE_2D)
    og.glBlendFunc(og.GL_SRC_ALPHA,og.GL_ONE_MINUS_SRC_ALPHA)
    og.glEnable(og.GL_BLEND)
    og.glDisable(og.GL_DEPTH_TEST)
    
    og.glCullFace(og.GL_BACK)
    
    og.max_texture_size = min(2056,og.glGetIntegerv(og.GL_MAX_TEXTURE_SIZE))
    og.max_texture_size = 256

    for tex in dotex:
        tex.newname()
        tex.rebind_string(tex.texdata)
        del tex.texdata

class shape(object):
    def __init__(self,pos=None,*args,**kwargs):
        self.pos = pos
        if not self.pos:
            self.pos = [0,0]
        self.ori = [0,0,0]
        self.color = [1,1,1,1]
        self.sc = [1,1,1]
        self._init(*args,**kwargs)
    def _init(self):
        pass
    def draw(self):
        pos = self.pos[:]
        if self.sc[0]<0 and hasattr(self,"width"):
            pos[0]+=self.width
        if self.sc[1]<0 and hasattr(self,"height"):
            pos[1]+=self.height
        while len(pos)<3:
            pos.append(0)
        og.glPushMatrix()
        w = float(getattr(self,"width",0))
        h = float(getattr(self,"height",0))
        og.glTranslate(w/2,-h/2,0)
        og.glRotate(self.ori[0],1,0,0)
        og.glRotate(self.ori[1],0,1,0)
        og.glRotate(self.ori[2],0,0,1)
        og.glTranslate(-w/2,h/2,0)
        og.glTranslate(pos[0],-pos[1],pos[2])
        og.glScale(*self.sc)
        self._draw()
        og.glPopMatrix()

class Tri(shape):
    def _draw(self):
        og.glBindTexture(og.GL_TEXTURE_2D,og.GL_NONE)
        og.glBegin(og.GL_TRIANGLES)
        og.glColor4f(*self.color)
        og.glVertex3f(0,-10,0)
        og.glVertex3f(10,-10,0)
        og.glVertex3f(10,0,0)
        og.glEnd()

class Quad(shape):
    def _draw(self):
        og.glBindTexture(og.GL_TEXTURE_2D,og.GL_NONE)
        og.glBegin(og.GL_QUADS)
        og.glColor4f(*self.color)
        og.glVertex3f(0,-192,0)
        og.glVertex3f(256,-192,0)
        og.glVertex3f(256,0,0)
        og.glVertex3f(0,0,0)
        og.glEnd()
        
class Collada(shape):
    def _init(self,path,meshes=None):
        if path:
            self.meshes = collada.read(path)
        else:
            self.meshes = meshes
    def _draw(self):
        og.glClear(og.GL_DEPTH_BUFFER_BIT)
        og.glScalef(20,20,20)
        og.glEnable(og.GL_DEPTH_TEST)
        [x.draw() for x in self.meshes]
        og.glDisable(og.GL_DEPTH_TEST)
    def copy(self):
        c = Collada(self.pos,None,self.meshes)
        c.ori = self.ori[:]
        return c
        
class lineGL:
    def __init__(self,color,pt1,pt2,width):
        self.color = color
        self.pt1 = pt1
        self.pt2 = pt2
        self.width = width
    def draw(self):
        og.glBegin(og.GL_LINES)
        og.glColor3f(*self.color)
        pt1 = self.pt1[:]
        pt2 = self.pt2[:]
        pt1[1]=-pt1[1]
        pt2[1]=-pt2[1]
        og.glVertex2f(*pt1)
        og.glVertex2f(*pt2)
        og.glEnd()
    def copy(self):
        return self
        
class rectGL:
    def __init__(self,color,rect,width):
        self.color = color
        self.rect = rect
        self.width = width
    def draw(self):
        pos,size = self.rect
        og.glBegin(og.GL_QUADS)
        og.glColor3f(*self.color)
        og.glVertex3f(pos[0],pos[1]-size[1],0)
        og.glVertex3f(pos[0]+size[0],pos[1]-size[1],0)
        og.glVertex3f(pos[0]+size[0],pos[1],0)
        og.glVertex3f(pos[0],pos[1],0)
        og.glEnd()
    def copy(self):
        return self
        
class drawGL:
    def line(self,surf,color,pt1,pt2,width=1):
        if isinstance(surf,pygame.Surface): return pygame.drawold.line(surf,color,pt1,pt2,width)
        surf.blit(lineGL(color,pt1,pt2,width),[0,0])
    def rect(self,surf,color,rect,width=0):
        if isinstance(surf,pygame.Surface): return pygame.drawold.rect(surf,color,rect,width)
        surf.blit(rectGL(color,rect,width),[0,0])
    def __getattr__(self,val):
        return getattr(pygame.drawold,val)

class TexQuad(Quad):
    def _init(self,path=None,surface=None,rect=None,cache=True):
        print path,surface
        if not hasattr(TexQuad,"bigalpha"):
            TexQuad.bigalpha = pygame.Surface([8000,8000]).convert_alpha()
            TexQuad.bigalpha.fill([0,0,0,0])
        self.width = 0
        self.height = 0
        self.grid = {}  #Grid of textures to be displayed
        if path:
            surface = pygame.image.load(path)
        if surface:
            self.load(surface,cache)
        self.obs = []  #objects to be displayed on top of us
        if not rect:
            rect = [[0,0],[self.width,self.height]]
        print "self.rect",rect
        self.rect = rect
    def load(self,surf,cache):
        self.width = surf.get_width()
        self.height = surf.get_height()
        print "loaded surf",self.width,self.height
        #First, make sure surface is power of 2
        width = nextPowerOf2(surf.get_width())
        height = nextPowerOf2(surf.get_height())
        if width!=surf.get_width() or height!=surf.get_height():
            ns = TexQuad.bigalpha.subsurface([[0,0],[width,height]])
            ns.blit(surf,[0,0])
            surf = ns
        #pygame.image.save(surf,"test.png")
        size = max(width,height)
        tw=th=min(og.max_texture_size,size)
        for x in range(width//tw):
            for y in range(height//th):
                self.grid[(x,y)] = texture(surf.subsurface([[x*tw,y*th],[tw,th]]),cache)
                #pygame.image.save(surf.subsurface([[x*tw,y*th],[tw,th]]),"%sx%s.png"%(x,y))
    def __del__(self):
        del self.grid
    def _draw(self):
        og.glEnable(og.GL_TEXTURE_2D)
        for tile in self.grid.keys():
            #if tile!=(0,0): continue
            texture = self.grid[tile]
            texture.use()
            sp = [tile[0]*texture.width,tile[1]*texture.height]
            ep = [sp[0]+texture.width,sp[1]+texture.height]
            ts = [0,0]
            te = [1,1]
            if tile[0]==0:
                ts[0]=self.rect[0][0]/float(texture.width)
            if tile[1]==0:
                ts[1]=self.rect[0][1]/float(texture.height)
            if sp[0]>self.rect[0][0]+self.rect[1][0]: continue
            if sp[1]>self.rect[0][1]+self.rect[1][1]: continue
            if ep[0]>self.rect[0][0]+self.rect[1][0]:
                ep[0] = self.rect[0][0]+self.rect[1][0]
                ts[0] = 1-float(ep[0]-sp[0])/texture.width
            if ep[1]>self.rect[0][1]+self.rect[1][1]:
                ep[1] = self.rect[0][1]+self.rect[1][1]
                ts[1] = 1-float(ep[1]-sp[1])/texture.height
            #print self.pos,sp
            og.glBegin(og.GL_QUADS)
            og.glColor4f(*self.color)
            og.glTexCoord2f(ts[0],ts[1])
            og.glVertex3f(sp[0],-ep[1],0)
            og.glTexCoord2f(te[0],ts[1])
            og.glVertex3f(ep[0],-ep[1],0)
            og.glTexCoord2f(te[0],te[1])
            og.glVertex3f(ep[0],-sp[1],0)
            og.glTexCoord2f(ts[0],te[1])
            og.glVertex3f(sp[0],-sp[1],0)
            og.glEnd()
        og.glDisable(og.GL_TEXTURE_2D)
        [o.draw() for o in self.obs]
        #self.obs = []
    def set_alpha(self,val):
        if type(val)==type(0):
            self.color[3] = val/float(255)
        else:
            self.color[3] = val
    def get_width(self):
        return self.width
    def get_height(self):
        return self.height
    def get_size(self):
        return [self.width,self.height]
    def convert(self):
        o = TexQuad(self.pos)
        o.grid = self.grid
        o.rect = self.rect
        o.obs = [x.copy() for x in self.obs]
        o.sc = self.sc[:]
        o.color = self.color[:]
        o.ori = self.ori[:]
        return o
    convert_alpha = copy = convert
    def blit(self,surf,pos):
        if isinstance(surf,pygame.Surface):
            ob = TexQuad(pos,surface=surf,cache=False)
        else:
            ob = surf.copy()
            ob.pos = pos
        ob.pos = [float(ob.pos[i])/ob.sc[i] for i in range(2)]
        #ob.pos = [0,0]
        self.obs.append(ob)
    def subsurface(self,rect):
        copy = self.copy()
        copy.rect = rect
        return copy
    def fill(self,color):
        s = pygame.Surface([self.width,self.height]).convert_alpha()
        s.fill(color)
        self.texture = texture(s,True)

class surface:
    def __init__(self,scalesize,sourcesize):
        self.obs = []
        self.scalesize = scalesize
        self.sourcesize=sourcesize
        self.scale = [float(scalesize[0])/sourcesize[0],float(scalesize[1])/(sourcesize[1]),1]
        self.trans = 1
        self.surfcache = {}
    def blit(self,surf,pos):
        if isinstance(surf,pygame.Surface):
            ob = TexQuad(pos,surface=surf,cache=False)
        else:
            ob = surf.copy()
            ob.pos = pos
        self.obs.append(ob)
    def draw(self):
        og.glScale(*self.scale)
        if self.trans:
            og.glTranslate(0,self.sourcesize[1],0)
        [o.draw() for o in self.obs]
        #og.glFlush()
    def get_size(self):
        return 256,192
    def get_height(self):
        return 192
    def get_width(self):
        return 256
    def copy(self):
        s = TexQuad([0,0],surface=pygame.Surface(self.sourcesize))
        s.obs = self.obs[:]
        return s
    def fill(self,color):
        og.glClearColor(color[0]/255., color[1]/255., color[2]/255., 1.0)
        og.glClear(og.GL_COLOR_BUFFER_BIT|og.GL_DEPTH_BUFFER_BIT)

pygame.x = 0
pygame.y = 0

def draw(list=[]):
    #og.glClear(og.GL_COLOR_BUFFER_BIT|og.GL_DEPTH_BUFFER_BIT)
    #og.glClear(og.GL_COLOR_BUFFER_BIT)
    for key in texture.textures.keys():
        tex = texture.textures[key]
        if time.time()-tex.die>0:
            del texture.textures[key]
    og.glMatrixMode(og.GL_MODELVIEW)
    og.glLoadIdentity()
    
    og.glTranslate(-pygame.x,-pygame.y,0)

    for s in list:
        s.draw()
        if hasattr(s,"obs"):
            del s.obs[:]
    
    #~ og.glBegin(og.GL_TRIANGLES)
    #~ og.glColor4f(0,1,0,1)
    #~ og.glVertex3f(21.66425,4.40801,0)
    #~ og.glVertex3f(21.66425,-4.40799,0)
    #~ og.glVertex3f(-22.41575,-4.40799,0)
    #~ og.glEnd()

    pygame.display.flip()
    spd=1
    if pygame.key.get_pressed()[pygame.K_y]:
        pygame.y += spd
        print pygame.y
    if pygame.key.get_pressed()[pygame.K_h]:
        pygame.y -= spd
        print pygame.y
    if pygame.key.get_pressed()[pygame.K_g]:
        pygame.x -= spd
        print pygame.x
    if pygame.key.get_pressed()[pygame.K_j]:
        pygame.x += spd
        print pygame.x
        
if __name__=="__main__":
    init([320,240])
    tq = TexQuad([0,-240],path="../art/general/logo.png")
    tqsub = tq.subsurface([[100,0],[250,100]])
    #tqsub.pos = [100,-180]
    o = tqsub
    while 1:
        draw([o])
        for e in pygame.event.get():
            if e.type==pygame.QUIT: import sys;sys.exit()
            if e.type==pygame.MOUSEBUTTONDOWN:
                if o==tqsub: o = tq
                else: o = tqsub