import os,zipfile,StringIO

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

global_registry_cache = {}
class Registry:
    def __init__(self,root=None,use_cache=True):
        self.map = {}
        self.ext_map = {}
        self.use_cache = use_cache
        if root:
            self.build(root)
    def open(self,path,mode="rb"):
        if ".zip/" in path:
            normal,zip = path.split(".zip/",1)
            zf = zipfile.ZipFile(normal+".zip")
            return StringIO.StringIO(zf.open(zip,"r").read())
        return open(path,mode)
    def clear_cache(self):
        global_registry_cache.clear()
    def build(self,root):
        if self.use_cache and root in global_registry_cache:
            self.map,self.ext_map = global_registry_cache[root]
            return
        self.root = root
        for sub in filepaths:
            if os.path.isdir(root+"/"+sub):
                self.index(root+"/"+sub)
        global_registry_cache[root] = [self.map,self.ext_map]
    def list_files(self,path):
        if os.path.isdir(path):
            return os.listdir(path)
        if zipfile.is_zipfile(path):
            return zipfile.ZipFile(path,"r").namelist()
    def index(self,path):
        in_zip = zipfile.is_zipfile(path)
        subdirs = []
        for sub in self.list_files(path):
            if sub==".hg":
                continue
            elif os.path.isdir(path+"/"+sub) or zipfile.is_zipfile(path+"/"+sub):
                subdirs.append(path+"/"+sub)
            else:
                self.mapfile(path+"/"+sub,in_zip)
        for sub in subdirs:
            self.index(sub)
    def mapfile(self,path,in_zip=False):
        file = File(path)
        tag = file.pathtag.split(self.root.lower()+"/",1)[1]
        if in_zip:
            spl = tag.split("/")
            spl[-2] = spl[-2].rsplit(".",1)[0]
            tag = "/".join(spl)
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
        print "building registry for",root
        reg = Registry()
        reg.build(root)
        cur_reg.override(reg)
    return cur_reg
        

def test():
    os.chdir("..")
    rec = Registry("./games/PW - The Contempt of Court/The Haunted Turnabout")
    assert rec.lookup("art/port/Maplethorpe/angry(blink).png")=="games/PW - The Contempt of Court/The Haunted Turnabout/art/port/Maplethorpe/angry(blink).png"
    assert rec.lookup("art/port/Maris/angry(blink).png")=="games/PW - The Contempt of Court/The Haunted Turnabout/art/port/Maris.zip/angry(blink).png"
    assert rec.lookup("art/port/Maris/hand1(blink).png")=="games/PW - The Contempt of Court/The Haunted Turnabout/art/port/Maris.zip/hand1(blink).png"
    
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