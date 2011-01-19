import pygame
import OpenGL.GL as og
import time
import math
import collada

class transformGL:
    def scale(self,ob,new_size):
        ob = ob.copy()
        csize = [ob.width*ob.sc[0],ob.height*ob.sc[1]]
        if csize[0]==0: csize[0]=1
        if csize[1]==0: csize[1]=1
        d = [new_size[i]/float(csize[i]) for i in range(len(csize))]
        ob.sc[0],ob.sc[1] = d
        if hasattr(ob,"width"):ob.width*=ob.sc[0]
        if hasattr(ob,"height"):ob.height*=ob.sc[1]
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
    bigalpha = None
    def __init__(self,surf,cache=True):
        self.name = int(og.glGenTextures(1))
        self.cache = cache
        self.die = time.time()+1
        if cache and pygame.TEXTURE_CACHE: texture.textures[self.name] = self
        self.update(surf)
    def newname(self):
        if self.textures.get(self.name,None):
            del self.textures[self.name]
        self.name = og.glGenTextures(1)
        if self.cache and pygame.TEXTURE_CACHE: self.textures[self.name] = self
    def update(self,surf):
        if not isinstance(surf,pygame.Surface):
            surf = pygame.image.load(surf)
        self.width,self.height = surf.get_size()
        self.nwidth = nextPowerOf2(self.width)
        self.nheight = nextPowerOf2(self.height)
        if self.width<=1 or self.height<=1: return
        ns = pygame.Surface([self.nwidth,self.nheight]).convert_alpha()
        ns.fill([0,0,0,0])
        ns.blit(surf,[0,self.nheight-self.height])
        surfstr = pygame.image.tostring(ns,"RGBA",True)
        self.rebind_string(surfstr)
    def rebind_string(self,surfstr):
        og.glBindTexture(og.GL_TEXTURE_2D,self.name)
        og.glTexImage2D(og.GL_TEXTURE_2D,0,og.GL_RGBA,self.nwidth,self.nheight,0,og.GL_RGBA,og.GL_UNSIGNED_BYTE,surfstr)
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
        self.die = time.time()+10
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
        pygame.real_screen = scr = pygame.display.set_mode(size,
            pygame.OPENGL|fs*pygame.FULLSCREEN|pygame.HWSURFACE|pygame.DOUBLEBUF)
    except:
        pygame.real_screen = scr = pygame.display.set_mode(size,
            pygame.OPENGL|fs*pygame.FULLSCREEN|pygame.DOUBLEBUF)
            
    og.glClearColor(0.0, 0.0, 0.0, 0.0)
    
    og.glMatrixMode(og.GL_PROJECTION)
    og.glLoadIdentity()
    og.glOrtho(0,size[0],0,size[1],-1000,1000)
    og.glViewport(0,0,size[0],size[1])
    
    og.glEnable(og.GL_TEXTURE_2D)
    og.glBlendFunc(og.GL_SRC_ALPHA,og.GL_ONE_MINUS_SRC_ALPHA)
    og.glEnable(og.GL_BLEND)
    og.glDisable(og.GL_DEPTH_TEST)
    og.glDisable(og.GL_ALPHA_TEST)
    
    og.glCullFace(og.GL_BACK)
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
    def draw(self,pos=None):
        if not pos: pos = self.pos[:]
        if self.sc[0]<0 and hasattr(self,"width"):
            pos[0]+=self.width
        if self.sc[1]<0 and hasattr(self,"height"):
            pos[1]+=self.height
        while len(pos)<3:
            pos.append(0)
        og.glPushMatrix()
        w = float(getattr(self,"width",0))*self.sc[0]
        h = float(getattr(self,"height",0))*self.sc[1]
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
    def draw(self,pos=None):
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
    def draw(self,pos=None):
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
    dlist = None
    def _init(self,path=None,surface=None,rect=None,cache=True):
        if isinstance(path,texture):
            self.texture = path
        elif path:
            self.texture = texture(path,cache)
        elif surface:
            self.texture = texture(surface,cache)
        else:
            if not hasattr(self,"defaulttex"): TexQuad.defaulttex = texture(pygame.Surface([0,0]),True)
            self.texture = self.defaulttex
        self.obs = []
        if not rect:
            rect = [[0,0],[self.texture.width,self.texture.height]]
        self.rect = rect
    def __del__(self):
        del self.texture
        if self.dlist and og.glIsList(self.dlist):
            og.glDeleteLists(self.dlist,1)
    def srect(self,rect):
        sp,si = rect[:]
        ep = [sp[0]+si[0],sp[1]+si[1]]
        nw,nh = float(self.texture.nwidth),float(self.texture.nheight)
        self._rect = [[sp[0]/nw,(self.height-sp[1])/nh],[ep[0]/nw,(self.height-ep[1])/nh]]
    def grect(self):
        return self._rect
    rect = property(grect,srect)
    def gpsize(self):
        sp,ep = self._rect
        return abs(ep[0]-sp[0])*self.texture.nwidth,abs(ep[1]-sp[1])*self.texture.nheight
    polysize = property(gpsize)
    def __getattr__(self,key):
        if key == "width": return self.texture.width
        if key == "height": return self.texture.height
        raise AttributeError()
    def _render(self,redo=False):
        og.glColor4f(*self.color)
        if not pygame.DISPLAY_LIST: 
            self.dlist = None
        if not pygame.DISPLAY_LIST or redo or not self.dlist or not og.glIsList(self.dlist):
            if pygame.DISPLAY_LIST:
                self.dlist = og.glGenLists(1)
                og.glNewList(self.dlist,og.GL_COMPILE)
                #print "create list",self
            sp,ep = self._rect
            og.glEnable(og.GL_TEXTURE_2D)
            self.texture.use()
            og.glBegin(og.GL_QUADS)
            og.glTexCoord2f(sp[0],ep[1])
            og.glVertex3f(0,-1,0)
            og.glTexCoord2f(ep[0],ep[1])
            og.glVertex3f(1,-1,0)
            og.glTexCoord2f(ep[0],sp[1])
            og.glVertex3f(1,0,0)
            og.glTexCoord2f(sp[0],sp[1])
            og.glVertex3f(0,0,0)
            og.glEnd()
            og.glDisable(og.GL_TEXTURE_2D)
            if pygame.DISPLAY_LIST:
                og.glEndList()
        if pygame.DISPLAY_LIST:
            og.glCallList(self.dlist)
    def _draw(self):
        width,height = self.polysize
        if width and height:
            og.glScale(width,height,1)
            self._render()
            og.glScale(1.0/width,1.0/height,1)
        [o[0].draw(o[1]) for o in self.obs]
        #self.obs = []
    def set_alpha(self,val,flags=0):
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
        o = TexQuad(self.pos,self.texture)
        o._rect = self.rect[:]
        o.obs = [x.copy() for x in self.obs]
        o.sc = self.sc[:]
        o.color = self.color[:]
        o.ori = self.ori[:]
        return o
    convert_alpha = copy = convert
    def blit(self,surf,pos):
        if isinstance(surf,pygame.Surface):
            ob = TexQuad(pos,surf,cache=False)
        else:
            ob = surf
        ob.sc = [1.0/self.sc[i] for i in range(len(self.sc))]
        #ob.pos = [0,0]
        self.obs.append([ob,pos[:]])
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
            ob = TexQuad(pos,surf,cache=False)
        else:
            ob = surf
        self.obs.append([ob,pos[:]])
    def draw(self,pos=None):
        og.glScale(*self.scale)
        if self.trans:
            og.glTranslate(0,self.sourcesize[1],0)
        [o[0].draw(pos=o[1]) for o in self.obs]
    def get_size(self):
        return 256,192
    def get_height(self):
        return 192
    def get_width(self):
        return 256
    def copy(self):
        s = TexQuad([0,0],pygame.Surface(self.sourcesize))
        s.obs = self.obs[:]
        return s
    def fill(self,color):
        og.glClearColor(color[0]/255., color[1]/255., color[2]/255., 1.0)
        og.glClear(og.GL_COLOR_BUFFER_BIT|og.GL_DEPTH_BUFFER_BIT)

pygame.x = 0
pygame.y = 0

def draw(list=[]):
    og.glClear(og.GL_COLOR_BUFFER_BIT|og.GL_DEPTH_BUFFER_BIT)
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

    #og.glFinish()
    pygame.display.flip()
    
    #~ if pygame.key.get_pressed()[pygame.K_y]:
        #~ pygame.y += 10
        #~ print pygame.y
    #~ if pygame.key.get_pressed()[pygame.K_h]:
        #~ pygame.y -= 10
        #~ print pygame.y
    #~ if pygame.key.get_pressed()[pygame.K_g]:
        #~ pygame.x -= 10
        #~ print pygame.x
    #~ if pygame.key.get_pressed()[pygame.K_j]:
        #~ pygame.x += 10
        
if __name__=="__main__":
    init([320,240])
    tq = TexQuad([0,-240],"../art/general/logo.png")
    tqsub = tq.subsurface([[100,0],[100,100]])
    tqsub.pos = [100,-180]
    o = tqsub
    while 1:
        draw([o])
        for e in pygame.event.get():
            if e.type==pygame.QUIT: import sys;sys.exit()
            if e.type==pygame.MOUSEBUTTONDOWN:
                if o==tqsub: o = tq
                else: o = tqsub