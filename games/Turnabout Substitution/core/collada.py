import xml.etree.ElementTree as ET
import OpenGL.GL as og

ET.namespace = ""

class vector:
    pass

class mesh:
    def __init__(self,node):
        self.id = node.attrib['id']
        self.name = node.attrib['name']
        self.arrays = {}
        self.vertexes = []
        self.normals = []
        self.colors = []
        self.triangles = []
        for mesh in node.getchildren():
            self.addmesh(mesh)
    def draw(self,scale=1):
        og.glBegin(og.GL_TRIANGLES)
        for tri in self.triangles:
            for pt in tri.pts:
                og.glColor4f(pt.color.r,pt.color.g,pt.color.b,pt.color.a)
                og.glNormal3f(pt.normal.x,pt.normal.y,pt.normal.z)
                og.glVertex3f(pt.vertex.x,pt.vertex.y,pt.vertex.z)
        og.glEnd()
    def addmesh(self,mesh):
        if not mesh.tag.endswith("}mesh"): return
        for node in mesh.getchildren():
            if node.tag==ET.namespace+"source":
                source = node
                for val in source.getchildren():
                    if val.tag.endswith("}float_array"):
                        self.arrays[val.attrib["id"]] = [float(x) for x in val.text.split(" ")]
                    if val.tag.endswith("}technique_common"):
                        accessor = val.find(ET.namespace+"accessor")
                        params = [x.attrib["name"] for x in accessor.getchildren()]
                        fp = params[0]
                        newarray = []
                        for i in self.arrays[accessor.attrib['source'][1:]]:
                            if params[0]==fp: 
                                current = vector()
                                newarray.append(current)
                            setattr(current,params[0].lower(),i)
                            params = params[1:] + [params[0]]
                        self.arrays[source.attrib['id']] = newarray
            if node.tag==ET.namespace+"vertices":
                sem = node.find(ET.namespace+"input")
                self.vertexes = self.arrays[sem.attrib['source'][1:]]
                self.arrays[node.attrib['id']] = self.vertexes
            if node.tag==ET.namespace+"triangles":
                reader = {}
                array = {}
                array["POSITION"] = self.vertexes
                for sem in node.findall(ET.namespace+"input"):
                    reader[sem.attrib['semantic']] = int(sem.attrib['offset'])
                    array[sem.attrib['semantic']] = self.arrays[sem.attrib['source'][1:]]
                points = [int(x) for x in node.find(ET.namespace+"p").text.split(" ")]
                for v in range(len(points)//9):
                    tri = vector()
                    tri.pts = []
                    for i in range(3):
                        pt = vector()
                        for sem in ["VERTEX","NORMAL","COLOR"]:
                            arr = array[sem]
                            index = points[v*9+i*3+reader[sem]]
                            val = arr[index]
                            setattr(pt,sem.lower(),val)
                        tri.pts.append(pt)
                    self.triangles.append(tri)

def read(file):
    tree = ET.parse(file)
    tag = tree.getroot().tag
    if "{" in tag: 
        ET.namespace = tag[tag.find("{"):tag.find("}",1)+1]
    meshes = []
    for x in tree.getiterator():
        if x.tag.endswith("}geometry"):
            meshes.append(mesh(x))
    return meshes

if __name__=="__main__":
    print read("../art/3d/breifcase.dae")