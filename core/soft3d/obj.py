import pygame
#import models
 
def MTL(filename):
    contents = {}
    mtl = None
    try:
        f = open(filename, "r")
    except:
        return contents
    for line in f:
        if line.startswith('#'): continue
        values = line.split()
        if not values: continue
        if values[0] == 'newmtl':
            mtl = contents[values[1]] = {}
        elif mtl is None:
            return contents
            raise ValueError, "mtl file doesn't start with newmtl stmt"
        elif values[0] == 'map_Kd':
            mtl[values[0]] = values[1]
        else:
            pass#mtl[values[0]] = map(float, values[1:])
    return contents

 
class OBJ:
    def __init__(self, filename, path, swapyz=True):
        """Loads a Wavefront OBJ file. """
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        self.mtl = {None:{}}
 
        material = None
        for line in open(path+"/"+filename, "r"):
            if line.startswith('#'): continue
            values = line.split()
            if not values: continue
            if values[0] == 'v':
                v = map(float, values[1:4])
                if swapyz:
                    v = [v[0], v[2], v[1]]
                self.vertices.append(v)
            elif values[0] == 'vn':
                v = map(float, values[1:4])
                if swapyz:
                    v = [v[0], v[2], v[1]]
                self.normals.append(v)
            elif values[0] == 'vt':
                self.texcoords.append(map(float, values[1:3]))
            elif values[0] in ('usemtl', 'usemat'):
                material = values[1]
            elif values[0] == 'mtllib':
                self.mtl = MTL(path+"/"+values[1])
            elif values[0] == 'f':
                face = []
                texcoords = []
                norms = []
                for v in values[1:]:
                    w = v.split('/')
                    face.append(int(w[0]))
                    if len(w) >= 2 and len(w[1]) > 0:
                        texcoords.append(int(w[1]))
                    else:
                        texcoords.append(0)
                    if len(w) >= 3 and len(w[2]) > 0:
                        norms.append(int(w[2]))
                    else:
                        norms.append(0)
                self.faces.append((face, norms, texcoords, material))
        
        self.tris = []
        self.quads = []
        self.tex = []
        for face,norms,texcoords,mat in self.faces:
            diffuse = self.mtl.get(mat,{}).get("map_Kd",None)
            uv1=uv2=uv3=uv4=[0,0]
            if len(face)<3:
                continue
            v1 = self.vertices[face[0]-1]
            v2 = self.vertices[face[1]-1]
            v3 = self.vertices[face[2]-1]
            if texcoords and texcoords[0]:
                uv1 = self.texcoords[texcoords[0]-1]
                uv2 = self.texcoords[texcoords[1]-1]
                uv3 = self.texcoords[texcoords[2]-1]
            s1 = v1+uv1
            s2 = v2+uv2
            s3 = v3+uv3
            s = [s1,s2,s3]
            if len(face)==4:
                v4 = self.vertices[face[3]-1]
                if texcoords and texcoords[0]:
                    uv4 = self.texcoords[texcoords[3]-1]
                s4 = v4+uv4
                s+=[s4]
                self.quads.append({"p":s,"t":diffuse,"n":norms})
            else:
                self.tris.append({"p":s,"t":diffuse,"n":norms})