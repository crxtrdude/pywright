#No this has nothing to do with pwlib
#It's a way to get version information from archives and folders
import os

def cver(verstr):
    """Converts a version string into a number"""
    if verstr.startswith("b"):
        return float(verstr[1:])-100000
    return float(verstr)

def read_pwv(txt):
    d = {}
    if txt[0]=="b" or txt[0].isdigit() and "\n" not in txt:
        d["version"] = cver(txt.strip())
        return d
    for line in txt.split("\n"):
        if not line:
            continue
        key,val = line.strip().split(" ",1)
        if key == "version":
            val = cver(val)
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
    return {"version":0}