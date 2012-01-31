import os

filepaths = ["art","music","sfx","movies"]
ignore = ".hg"
priority = ["png","jpg","bmp","mp3","ogg"]

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
    def __init__(self):
        self.map = {}
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
    def lookup(self,thingie):
        thingie = thingie.lower()
        if thingie in self.map:
            return self.map[thingie].path.split("./",1)[1]
    def override(self,other_reg):
        self.map.update(other_reg.map)
            
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
    reg = Registry()
    reg.build("./games/Turnabout Substitution")
    assert not reg.lookup("art/port/kristoph2/normal(talk)")
    assert reg.lookup("art/port/apollo/normal(talk)")=="games/Turnabout Substitution/art/port/Apollo/normal(talk).png",reg.lookup("art/port/apollo/normal(talk)")
    
    base = Registry()
    base.build(".")
    assert base.lookup("art/port/kristoph2/normal(talk)")=="art/port/kristoph2/normal(talk).png",reg.lookup("art/port/kristoph2/normal(talk)")
    assert base.lookup("art/port/apollo/normal(talk)")=="art/port/apollo/normal(talk).png",base.lookup("art/port/apollo/normal(talk)")
    
    base.override(reg)
    assert base.lookup("art/port/kristoph2/normal(talk)")=="art/port/kristoph2/normal(talk).png",reg.lookup("art/port/kristoph2/normal(talk)")
    assert reg.lookup("art/port/apollo/normal(talk)")=="games/Turnabout Substitution/art/port/Apollo/normal(talk).png",reg.lookup("art/port/apollo/normal(talk)")
    
if __name__=="__main__":
    testfile()
    test()