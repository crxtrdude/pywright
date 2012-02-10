import os

filepaths = ["art","music","sfx","movies"]
ignore = ".hg"
priority = ["png","jpg","gif","bmp","mp3","ogg"]

class File:
    def __init__(self,path):
        self.path = path
        self.filename = self.path.rsplit("/",1)[1]
        self.pathtag = self.path
        self.filetag = self.filename
        self.ext = ""
        if "." in self.filename:
            self.pathtag = self.path.rsplit(".",1)[0]
            self.filetag,self.ext = self.filename.rsplit(".",1)
        self.priority = 12
        if self.ext in priority:
            self.priority = priority.index(self.ext)
        
        self.filetag = self.filetag.lower()
        self.pathtag = self.pathtag.lower()
        self.pathtagext = self.pathtag+"."+self.ext
    def __repr__(self):
        return self.path
            
def testfile():
    a = File("../art/port/kristoph2/normal(talk).txt")
    b = File("../art/port/kristoph2/normal(talk).png")
    c = File("../art/port/kristoph12/normal(talk).jpg")
    d = File("../art/port/kristoph2/normal(talk)")
    assert a.path=="../art/port/kristoph2/normal(talk).txt"
    assert b.path=="../art/port/kristoph2/normal(talk).png"
    assert c.path=="../art/port/kristoph12/normal(talk).jpg"
    assert d.path=="../art/port/kristoph2/normal(talk)"
    assert a.filetag==b.filetag==c.filetag==d.filetag
    assert a.pathtag==b.pathtag!=c.pathtag
    assert b.priority<c.priority,"bpri:%s cpri:%s"%(b.priority,c.priority)
    assert c.priority<d.priority

class Registry:
    def __init__(self,root=None):
        self.map = {}
        self.ext_map = {}
        if root:
            self.build(root)
    def build(self,root):
        self.root = root
        for sub in filepaths:
            if os.path.isdir(root+"/"+sub):
                self.index(root+"/"+sub)
    def index(self,path):
        subdirs = []
        for sub in os.listdir(path):
            if sub==".hg":
                continue
            elif os.path.isdir(path+"/"+sub):
                subdirs.append(path+"/"+sub)
            else:
                self.mapfile(path+"/"+sub)
        for sub in subdirs:
            self.index(sub)
    def mapfile(self,path):
        file = File(path)
        tag = file.pathtag.split(self.root.lower()+"/",1)[1]
        if tag in self.map:
            if file.priority<=self.map[tag].priority:
                self.map[tag] = file
        else:
            self.map[tag] = file
        tagext = file.pathtagext.split(self.root.lower()+"/",1)[1]
        if tagext in self.ext_map:
            if file.priority<=self.ext_map[tagext].priority:
                self.ext_map[tagext] = file
        else:
            self.ext_map[tagext] = file
    def lookup(self,thingie,ext=False):
        thingie = os.path.normpath(thingie).replace("\\","/")
        f = File(thingie)
        map = self.map
        tag = f.pathtag
        if ext:
            map = self.ext_map
            tag = f.pathtagext
        if tag in map:
            path = map[tag].path
            if "./" in path:
                path = path.split("./",1)[1]
            return path
    def override(self,other_reg):
        self.map.update(other_reg.map)
        self.ext_map.update(other_reg.ext_map)
            
def combine_registries(root):
    spl = root.split("/")
    last = ""
    order = []
    for x in spl:
        if last:
            last+="/"+x
        else:
            last=x
        order.append(last)
    cur_reg = Registry()
    for root in order:
        reg = Registry()
        reg.build(root)
        cur_reg.override(reg)
        

def test():
    os.chdir("..")
    reg = Registry("./games/Turnabout Substitution")
    assert not reg.lookup("art/port/kristoph2/normal(talk)")
    assert reg.lookup("art/port/apollo/normal(talk)")=="games/Turnabout Substitution/art/port/Apollo/normal(talk).png",reg.lookup("art/port/apollo/normal(talk)")
    
    base = Registry(".")
    assert base.lookup("art/port/kristoph2/normal(talk).txt",True)=="art/port/kristoph2/normal(talk).txt",base.lookup("art/port/kristoph2/normal(talk).txt",True)
    assert base.lookup("art/port/kristoph2/normal(talk)")=="art/port/kristoph2/normal(talk).png",base.lookup("art/port/kristoph2/normal(talk)")
    assert base.lookup("art/port/apollo/normal(talk)")=="art/port/apollo/normal(talk).png",base.lookup("art/port/apollo/normal(talk)")
    assert base.lookup("art/fg/../general/logosmall")=="art/general/logosmall.png"

    base.override(reg)
    assert base.lookup("art/port/kristoph2/normal(talk)")=="art/port/kristoph2/normal(talk).png",base.lookup("art/port/kristoph2/normal(talk)")
    assert reg.lookup("art/port/apollo/normal(talk)")=="games/Turnabout Substitution/art/port/Apollo/normal(talk).png",reg.lookup("art/port/apollo/normal(talk)")

    
    rec = Registry("examples/rectangles")
    assert rec.lookup("art/fg/lilmiles-walkeast.txt")=="examples/rectangles/art/fg/lilmiles-walkeast.png"
    assert rec.lookup("art/fg/lilmiles-walkeast.txt",True)=="examples/rectangles/art/fg/lilmiles-walkeast.txt"
    base.override(rec)
    assert rec.lookup("art/fg/lilmiles-walkeast.txt")=="examples/rectangles/art/fg/lilmiles-walkeast.png"
    assert rec.lookup("art/fg/lilmiles-walkeast.txt",True)=="examples/rectangles/art/fg/lilmiles-walkeast.txt"
    
if __name__=="__main__":
    testfile()
    test()