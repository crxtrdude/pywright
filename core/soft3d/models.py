import math
import pygame
import euclid
from util import *

def rot(x,y,z,rx,ry,rz,c):
    cx,cy,cz = c[:3]
    x=x-cx
    y=y-cy
    z=z-cz
    my = euclid.Matrix4.new_rotatey(ry*math.pi/180.0)
    mz = euclid.Matrix4.new_rotatez(rz*math.pi/180.0)
    if rz:
        mx = euclid.Matrix4.new_rotatez(rz*math.pi/180.0)
        x,y,z = mx*euclid.Point3(x,y,z)
    if rx:
        mx = euclid.Matrix4.new_rotatex(rx*math.pi/180.0)
        x,y,z = mx*euclid.Point3(x,y,z)
    if ry:
        mx = euclid.Matrix4.new_rotatey(ry*math.pi/180.0)
        x,y,z = mx*euclid.Point3(x,y,z)
    return [x+cx,y+cy,z+cz]

class Quad:
    def __init__(self,points,color,texture,normal=[0,0,0]):
        self.points = points
        self.color = color
        self.texture = texture
        self.center = self.points[0]
        self.normal = self.points[0][:3]
        self.ori = [0,0,0]
        self.mesh=None
    def normalize_normal(self):
        return
        mag = math.sqrt(self.normal[0]**2+self.normal[1]**2+self.normal[2]**2)
        self.normal = [nn/mag for nn in self.normal]
    def calc_corners(self,c,scale=[1,1,1]):
        self.corners = []
        for p in self.points:
            p = rot(p[0]*scale[0],p[1]*scale[1],p[2]*scale[2],self.ori[0],self.ori[1],self.ori[2],self.mesh.center) + p[3:]
            p = c.trans(p)
            self.corners.append(p)
    def rot(self,rx=0,ry=0,rz=0,center=None):
        if not center:
            center = self.center
        self.ori[0]+=rx
        self.ori[1]+=ry
        self.ori[2]+=rz
        rot(self.normal[0],self.normal[1],self.normal[2],rx,ry,rz,[0,0,0])
        self.normalize_normal()
            
class Tri(Quad):
    pass
    
class Mesh:
    def __init__(self,quads):
        self.quads = quads
        [setattr(q,"mesh",self) for q in self.quads]
        self.center = [0,0,0]#get_center(quads)
        self.scale = [1,1,1]
    def trans(self,x=0,y=0,z=0):
        [trans(q,x,y,z) for q in self.quads]
        self.center[0]+=x
        self.center[1]+=y
        self.center[2]+=z
    def rot(self,rx=0,ry=0,rz=0):
        c = self.center
        [q.rot(rx,ry,rz,c) for q in self.quads]
    def calc_normals(self):
        return
        c = self.center
        for q in self.quads:
            p = q.points[0]
            q.normal = [p[0]-c[0],p[1]-c[1],p[2]-c[2]]
            q.normalize_normal()
            
import obj
def load_obj(fn,path):
    quads = []
    o = obj.OBJ(fn,path)
    for s in o.tris:
        t = Tri(s["p"],[0,0,0],s["t"],s["n"])
        #scale(t,3)
        quads.append(t)
    for s in o.quads:
        t = Quad(s["p"],[0,0,0],s["t"],s["n"])
        #scale(t,3)
        quads.append(t)
    m = Mesh(quads)
    m.calc_normals()
    return m