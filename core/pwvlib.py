#No this has nothing to do with pwlib
#It's a way to get version information from archives and folders
import os

def cver(verstr):
    """Converts a version string into a number"""
    if verstr.startswith("b"):
        return float(verstr[1:])-100000
    return float(verstr)
    
def cver_t(verstr):
    """Converts a version string into a tuple"""
    if verstr.startswith("b"):
        return tuple([0,0,0,0]+list(cver_t(verstr[1:])))
    return tuple([int(x) for x in verstr.split(".")])
        
def cver_s(tup):
    """Convert tuple version back to string"""
    tup = list(tup)
    while tup and not tup[-1]:
        del tup[-1]
    if not tup:
        return "0.0"
    if len(tup)==1:
        tup.append(0)
    return ".".join([str(x) for x in tup])

def compare_versions(v1,v2):
    v1 = list(v1)
    v2 = list(v2)
    while len(v1)<len(v2):
        v1.append(0)
    while len(v2)<len(v1):
        v2.append(0)
    return cmp(tuple(v1),tuple(v2))

def read_pwv(txt):
    d = {}
    if txt[0]=="b" or txt[0].isdigit() and "\n" not in txt:
        d["version"] = cver_t(txt.strip())
        return d
    for line in txt.split("\n"):
        if not line:
            continue
        key,val = line.strip().split(" ",1)
        if key in ["version","min_pywright_version"]:
            val = cver_t(val)
        d[key] = val
    return d

def shortest_pwv_path(zip):
    pwvpaths = []
    for path in zip.namelist():
        if path.endswith("/data.txt") or path=="data.txt":
            pwvpaths.append(path)
        elif path.endswith("/.pwv") or path==".pwv":
            pwvpaths.append(path)
    pwvpaths.sort(key=lambda o: len(o))
    return pwvpaths[0]

def extract_pwv(zip,name):
    pth = shortest_pwv_path(zip)
    txt = zip.read(pth)
    f = open(name+".pwv","w")
    f.write(txt)
    f.close()
    return txt

def get_data_from_folder(folder):
    for vfile in ["data.txt",".pwv"]:
        try:
            f = open(folder+"/"+vfile)
            txt = f.read()
            f.close()
            return read_pwv(txt)
        except:
            pass
    return {"version":(0,)}