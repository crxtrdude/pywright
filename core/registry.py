import os,zipfile,StringIO

filepaths = ["data/art","art.zip","data/music","data/sfx","movies"]
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
    a = File("../data/art/port/kristoph2/normal(talk).txt")
    b = File("../data/art/port/kristoph2/normal(talk).png")
    c = File("../data/art/port/kristoph12/normal(talk).jpg")
    d = File("../data/art/port/kristoph2/normal(talk)")
    assert a.path=="../data/art/port/kristoph2/normal(talk).txt"
    assert b.path=="../data/art/port/kristoph2/normal(talk).png"
    assert c.path=="../data/art/port/kristoph12/normal(talk).jpg"
    assert d.path=="../data/art/port/kristoph2/normal(talk)"
    assert a.filetag==b.filetag==c.filetag==d.filetag
    assert a.pathtag==b.pathtag!=c.pathtag
    assert b.priority<c.priority,"bpri:%s cpri:%s"%(b.priority,c.priority)
    assert c.priority<d.priority

global_registry_cache = {}
class Registry:
    def __init__(self,root=None,use_cache=True):
        self.map = {}
        self.listdir_map = {}
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
    def build(self,root,progress_function=lambda:1):
        print "building root"
        if self.use_cache and root in global_registry_cache:
            self.map,self.ext_map = global_registry_cache[root]
            return
        self.root = root
        for sub in filepaths:
            print "check",sub
            if os.path.isdir(root+"/"+sub) or zipfile.is_zipfile(root+"/"+sub):
                self.index(root+"/"+sub)
            progress_function()
        global_registry_cache[root] = [self.map,self.ext_map]
    def list_files(self,path):
        if os.path.isdir(path):
            return os.listdir(path)
        if zipfile.is_zipfile(path):
            return zipfile.ZipFile(path,"r").namelist()
    def index(self,path):
        in_zip = zipfile.is_zipfile(path)
        subdirs = []
        self.mapfile(path+"/",in_zip)
        for sub in self.list_files(path):
            if sub==".hg":
                continue
            elif os.path.isdir(path+"/"+sub) or zipfile.is_zipfile(path+"/"+sub):
                subdirs.append(path+"/"+sub)
            else:
                self.mapfile(path+"/"+sub,in_zip)
        for sub in subdirs:
            self.index(sub)
    def list_dir(self,path):
        path = self.cleanpath(path)
        print self.listdir_map.keys()
        return self.listdir_map["./"+path]
    def mapfile(self,path,in_zip=False):
        parent,sub = path.rsplit("/",1)
        parent = parent.split(".zip",1)
        parent = "".join(parent)
        
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
            
        if parent not in self.listdir_map:
            self.listdir_map[parent] = []
            print "create list map",parent
        self.listdir_map[parent].append(sub)
    def cleanpath(self,path):
        return os.path.normpath(path).replace("\\","/").replace(".zip/","/")
    def lookup(self,thingie,ext=False):
        thingie = self.cleanpath(thingie)
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
        self.listdir_map.update(other_reg.listdir_map)
            
def combine_registries(root,progress_function=lambda:1):
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
        reg.build(root,progress_function)
        cur_reg.override(reg)
    return cur_reg
        

def test():
    os.chdir("..")
    
    rec = Registry("./games/PW - The Contempt of Court - artzip")
    print rec.listdir_map.keys()
    print rec.list_dir("./games/PW - The Contempt of Court - artzip/data/art")
    #print rec.map
    print rec.lookup("data/art/port/White/twitch.txt")
    return
    
    rec = Registry("./games/PW - The Contempt of Court.zip")
    print rec.listdir_map.keys()
    #print rec.map
    #print rec.lookup("art/port/White/twitch.txt")
    return
    
    rec = Registry("./games/PW - The Contempt of Court/The Haunted Turnabout")
    assert rec.lookup("data/art/port/Maplethorpe/angry(blink).png")=="games/PW - The Contempt of Court/The Haunted Turnabout/data/art/port/Maplethorpe/angry(blink).png"
    assert rec.lookup("data/art/port/Maris/angry(blink).png")=="games/PW - The Contempt of Court/The Haunted Turnabout/data/art/port/Maris.zip/angry(blink).png"
    assert rec.lookup("data/art/port/Maris/hand1(blink).png")=="games/PW - The Contempt of Court/The Haunted Turnabout/data/art/port/Maris.zip/hand1(blink).png"
    
    reg = Registry("./games/Turnabout Substitution")
    assert not reg.lookup("data/art/port/kristoph2/normal(talk)")
    assert reg.lookup("data/art/port/apollo/normal(talk)")=="games/Turnabout Substitution/data/art/port/Apollo/normal(talk).png",reg.lookup("data/art/port/apollo/normal(talk)")
    
    base = Registry(".")
    assert base.lookup("data/art/port/kristoph2/normal(talk).txt",True)=="data/art/port/kristoph2/normal(talk).txt",base.lookup("data/art/port/kristoph2/normal(talk).txt",True)
    assert base.lookup("data/art/port/kristoph2/normal(talk)")=="data/art/port/kristoph2/normal(talk).png",base.lookup("data/art/port/kristoph2/normal(talk)")
    assert base.lookup("data/art/port/apollo/normal(talk)")=="data/art/port/apollo/normal(talk).png",base.lookup("data/art/port/apollo/normal(talk)")
    assert base.lookup("data/art/fg/../general/logosmall")=="data/art/general/logosmall.png"

    base.override(reg)
    assert base.lookup("data/art/port/kristoph2/normal(talk)")=="data/art/port/kristoph2/normal(talk).png",base.lookup("data/art/port/kristoph2/normal(talk)")
    assert reg.lookup("data/art/port/apollo/normal(talk)")=="games/Turnabout Substitution/data/art/port/Apollo/normal(talk).png",reg.lookup("data/art/port/apollo/normal(talk)")

    
    rec = Registry("examples/rectangles")
    assert rec.lookup("data/art/fg/lilmiles-walkeast.txt")=="examples/rectangles/data/art/fg/lilmiles-walkeast.png"
    assert rec.lookup("data/art/fg/lilmiles-walkeast.txt",True)=="examples/rectangles/data/art/fg/lilmiles-walkeast.txt"
    base.override(rec)
    assert rec.lookup("data/art/fg/lilmiles-walkeast.txt")=="examples/rectangles/data/art/fg/lilmiles-walkeast.png"
    assert rec.lookup("data/art/fg/lilmiles-walkeast.txt",True)=="examples/rectangles/data/art/fg/lilmiles-walkeast.txt"

if __name__=="__main__":
    testfile()
    test()
