import os
import pygame
import numpy
import math
import random
try:
    import ccontext
except:
    ccontext = None

#try:
#    import psyco
#    psyco.full()
#except:
#    pass


LOW = 320,240
HIGH = 192,120
s_w,s_h = LOW
r_w,r_h = 640,480
clock = pygame.time.Clock()

from models import *
from util import *

class SoftContext:
    def __init__(self,s_w,s_h,r_w,r_h):
        self.s_w = s_w
        self.s_h = s_h
        self.r_w = r_w
        self.r_h = r_h
        self.make_screen()
        self.textures = {}
        self.objects = []
    def load_object(self,fn,path="."):
        ob = load_obj(fn,path)
        for q in ob.quads:
            if q.texture not in self.textures and q.texture:
                self.textures[q.texture] = load_tex(path+"/"+q.texture)
            if q.texture:
                q.texture = self.textures[q.texture]
        self.objects.append(ob)
        return ob
    def make_screen(self):
        self.surf = pygame.Surface([self.s_w,self.s_h]).convert()
        self.arr = pygame.surfarray.pixels2d(self.surf)
        self.odepth = [(1000,None) for i in range(self.s_w*self.s_h)]
    def trans(self,p):
        s_w,s_h,r_w,r_h = [self.s_w,self.s_h,self.r_w,self.r_h]
        x,y,z,u,v = p
        if ccontext:
            return ccontext.trans(s_w,s_h,r_w,r_h,x,y,z,u,v)
        z = float((z*1.0/300.0)+1)
        if z==0:
            z=0.001
        d = s_w
        x = (d*x/float(r_w))/z
        x+=s_w//2
        d = s_h
        y = (d*y/float(r_w))/z
        y+=s_h//2
        return [x,y,z,u,v]
    def draw(self,meshes=None):
        if not meshes:
            meshes = self.objects
        pygame.arr = self.arr
        pygame.s_w = self.s_w
        pygame.s_h = self.s_h
        pygame.depth = self.odepth[:]
        self.surf.fill([255,0,255])
        pygame.points = 0
        pygame.hidden = 0
        pygame.backface = 0
        for m in meshes:
            for q in sorted(m.quads,key=lambda q: q.points[2]):
                draw_quad(q,self)
        surf = pygame.transform.scale(self.surf,[self.r_w,self.r_h])
        surf.set_colorkey([255,0,255])
        return surf

def load_tex(img):
    #~ if not img:
        #~ img = "core/soft3d/m16.bmp"
    tex = pygame.transform.flip(pygame.image.load(img),0,1)
    
    texarr = []
    alpha = 255
    for z in range(1):
        blank = tex.convert()
        blank.fill([0,0,0])
        tex.set_alpha(alpha)
        blank.blit(tex,[0,0])
        alpha = int(0.8*alpha)
        arr = pygame.surfarray.array2d(blank)
        texarr.append(arr)
    tw = tex.get_width()-1
    th = tex.get_height()-1
    return texarr,tw,th

def draw_point(x,y,z,u,v,texture):
    if not texture:
        return
    if x<0 or x>=pygame.s_w:
        return
    if y<0 or y>=pygame.s_h:
        return
    if z<=0.001 or z*30>=50:
        return
    if pygame.depth[y*pygame.s_w+x][0]<z:
        pygame.hidden += 1
        return
    pygame.points += 1
    texarr,tw,th = texture
    u,v=int(u%1*tw),int(v%1*th)
    pygame.arr[x,y] = texarr[0][u,v]
    pygame.depth[y*pygame.s_w+x] = (z,[u,th-v])
    
        
def draw_tri(a,b,c,texture):
    """draws triangle with horizontal lines"""
    #Sort points vertically
    a,b,c = sorted([a,b,c],key=lambda t: t[1])
    #upside down triangle with flat top
    if a[1]==b[1]:
        draw_tri_point_down(a,b,c,texture)
        return
    #triangle with flat bottom
    if b[1]==c[1]:
        draw_tri_point_up(a,b,c,texture)
        return
    #triangle should be split
    else:
        draw_tri_split(a,b,c,texture)
        
def draw_tri_split(a,b,c,texture):
    """Split a rotated triangle into an upward and downward pointing one"""
    d = [0,b[1],0,0,0]
    if c[0]==a[0]:
        d[0] = c[0]
    else:
        m = (c[1]-a[1])/(c[0]-a[0])
        i=a[1]-m*a[0]
        d[0] = (d[1]-i)/m
    if c[2]==a[2]:
        d[2] = c[2]
    else:
        m = (c[1]-a[1])/(c[2]-a[2])
        i=a[1]-m*a[2]
        d[2] = (d[1]-i)/m
    if c[3]==a[3]:
        d[3] = c[3]
    else:
        m = (c[1]-a[1])/(c[3]-a[3])
        i=a[1]-m*a[3]
        d[3] = (d[1]-i)/m
    if c[4]==a[4]:
        d[4] = c[4]
    else:
        m = (c[1]-a[1])/(c[4]-a[4])
        i=a[1]-m*a[4]
        d[4] = (d[1]-i)/m
    draw_tri_point_up(a,b,d,texture)
    draw_tri_point_down(b,d,c,texture)
    
def draw_line(x1,y1,z1,u1,v1,x2,y2,z2,u2,v2,texture):
    """horizontal"""
    x,y,z,u,v = x1,y1,z1,u1,v1
    w = abs(x2-x1)
    if not w:
        return
    if y<0 or y>=pygame.s_h:
        return
    dx = 1
    dy = 0
    dz = (z2-z1)/w
    du = (u2-u1)/w
    dv = (v2-v1)/w
    while x<x2:
        if x>=pygame.s_w:
            return
        if x>=0:
            draw_point(int(x),int(y),z,u,v,texture)
        x+=dx
        y+=dy
        z+=dz
        u+=du
        v+=dv

def draw_tri_point_up(a,b,c,texture):
    """flat bottom"""
    b,c = sorted([b,c],key=lambda t: t[0])
    x,y,z,u,v = a
    ex,ey,ez,eu,ev = a
    if c[0]<b[0]:
        b,c = c,b
    ydist = float(b[1]-y)
    dx1 = (b[0]-x)/ydist
    dx2 = (c[0]-ex)/ydist
    dy1 = 1
    dy2 = 1
    dz1 = (b[2]-z)/ydist
    dz2 = (c[2]-ez)/ydist
    du1 = (b[3]-u)/ydist
    du2 = (c[3]-eu)/ydist
    dv1 = (b[4]-v)/ydist
    dv2 = (c[4]-ev)/ydist
    while y<=b[1]:
        draw_line(x,y,z,u,v,ex,ey,ez,eu,ev,texture)
        x+=dx1
        y+=dy1
        z+=dz1
        u+=du1
        v+=dv1
        ex+=dx2
        ey+=dy2
        ez+=dz2
        eu+=du2
        ev+=dv2

def draw_tri_point_down(a,b,c,texture):
    """flat top"""
    if b[0]<a[0]:
        b,a = a,b
    x,y,z,u,v = a
    ex,ey,ez,eu,ev = b
    ydist = float(c[1]-y)
    dx1 = (c[0]-x)/ydist
    dx2 = (c[0]-ex)/ydist
    dy1 = 1
    dy2 = 1
    dz1 = (c[2]-z)/ydist
    dz2 = (c[2]-ez)/ydist
    du1 = (c[3]-u)/ydist
    du2 = (c[3]-eu)/ydist
    dv1 = (c[4]-v)/ydist
    dv2 = (c[4]-ev)/ydist
    while y<=c[1]:
        draw_line(x,y,z,u,v,ex,ey,ez,eu,ev,texture)
        x+=dx1
        y+=dy1
        z+=dz1
        u+=du1
        v+=dv1
        ex+=dx2
        ey+=dy2
        ez+=dz2
        eu+=du2
        ev+=dv2
        
def draw_quad(q,c):
    """Draws a quad sample in screen space"""
    #~ n = q.normal
    #~ co = [q.points[0][0],q.points[0][1],q.points[0][2]-100]
    #~ dp = n[0]*co[0]+n[1]*co[1]+n[2]*co[2]
    #~ if dp<0:
        #~ pygame.backface += 1
        #~ return
    q.calc_corners(c)
    inside = False
    for c in q.corners:
        if c[0]>=0 and c[0]<pygame.s_w and c[1]>=0 and c[1]<pygame.s_h and c[2]>0 and c[2]*30<50:
            inside = True
            break
    if not inside:
        return
    if isinstance(q,Tri):
        return draw_tri(q.corners[0],q.corners[1],q.corners[2],q.texture)
    ul = q.corners[0]
    ur = q.corners[1]
    br = q.corners[2]
    bl = q.corners[3]
    draw_tri(ul,ur,br,q.texture)
    draw_tri(ul,br,bl,q.texture)

def main():
    pygame.screen = s = pygame.display.set_mode([r_w,r_h],pygame.DOUBLEBUF)
    softcontext = SoftContext(s_w,s_h,r_w,r_h)
    for fn in os.listdir("."):
        if fn.endswith(".obj"):
            softcontext.load_object(fn)
    objects = softcontext.objects
    ob_i = 0
    next_update = 1
    pygame.points = 0
    pygame.hidden = 0
    pygame.backface = 0
    running = 1
    while running:
        dt = clock.tick(60)
        o = objects[ob_i]
        pygame.display.set_caption("%s p:%s f:%s hp:%s bf:%s"%(clock.get_fps(),pygame.points,len(o.quads),pygame.hidden,pygame.backface))
        m = LOW
        for e in pygame.event.get():
            if e.type==pygame.QUIT:
                running = 0
            if e.type==pygame.KEYDOWN and e.key==pygame.K_PERIOD:
                ob_i-=1
                if ob_i<0:
                    ob_i = len(objects)-1
                m = LOW
            if e.type==pygame.KEYDOWN and e.key==pygame.K_COMMA:
                ob_i+=1
                if ob_i>=len(objects):
                    ob_i = 0
                m = LOW
            if e.type==pygame.KEYDOWN and e.key==pygame.K_F9:
                pygame.image.save(pygame.screen,"screen.jpg")
            if e.type==pygame.KEYDOWN and e.key==pygame.K_n:
                softcontext.s_w*=2
                softcontext.s_h*=2
                softcontext.make_screen()
            if e.type==pygame.KEYDOWN and e.key==pygame.K_m:
                softcontext.s_w/=2
                softcontext.s_h/=2
                softcontext.make_screen()
            if e.type==pygame.MOUSEMOTION:
                if e.buttons[0]:
                    m = LOW
                    x,y = e.rel
                    o.rot(ry=-x*2.0)
                    o.rot(rx=y*2.20)
                    o.rot(rz=0)
            if e.type==pygame.MOUSEBUTTONDOWN:
                if e.button==1:
                    x,y = e.pos
                    x=int(x*(softcontext.s_w/float(softcontext.r_w)))
                    y=int(y*(softcontext.s_h/float(softcontext.r_h)))
                    point = pygame.depth[y*softcontext.s_w+x][1]
                    if point:
                        u,v = point
                        for rect in [[122,256,55,199],[178,239,88,215],[277,357,25,77]]:
                            if u>=rect[0] and u<=rect[0]+rect[2] and v>=rect[1] and v<=rect[1]+rect[3]:
                                print "handle of gun clicked"
                                break
        keys = pygame.key.get_pressed()
        spd = 5
        if keys[pygame.K_a]:
            o.trans(z=-spd)
            m = LOW
        if keys[pygame.K_z]:
            o.trans(z=spd)
            m = LOW
        if keys[pygame.K_r]:
            o.rot(ry=1)
            m = LOW
        if keys[pygame.K_t]:
            o.rot(rx=1)
            m = LOW
        if keys[pygame.K_y]:
            o.rot(rz=1)
            m = LOW
        set = False
        #For regular rendering
        set = True
        if m != (softcontext.s_w,softcontext.s_h):
            set = True
            next_update=-1
            softcontext.s_w,softcontext.s_h = m
            softcontext.make_screen()
        if next_update<0 and (m!=HIGH or set):
            next_update = 60
            surf = softcontext.draw([o])
            pygame.screen.fill([0,0,0])
            pygame.screen.blit(surf,[0,0])
        next_update -= dt
        pygame.display.flip()

if __name__ == "__main__":
    #~ import cProfile as profile
    #~ profile.run("main()")
    main()
