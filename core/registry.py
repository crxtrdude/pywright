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
testfile()

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
        if file.pathtag in self.map:
            if file.priority<self.map[file.pathtag].priority:
                self.map[file.pathtag] = file
        else:
            self.map[file.pathtag] = file

reg = Registry()
reg.build("..")