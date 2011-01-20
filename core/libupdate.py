import os,sys
sys.path.append("core/include")
sys.path.append("include")
if sys.platform=="win32":
    os.environ['SDL_VIDEODRIVER']='windib'
import zlib
from core import pygame
import threading,time,urllib,urllib2
from zipfile import ZipFile,ZIP_DEFLATED
from pwvlib import *

ERROR_STR= """Error removing %(path)s, %(error)s """
ROOT_URL = "http://74.207.230.140/"
ROOT_URL = "http://pywright.dawnsoft.org/"

def rmgeneric(path, __func__):
    try:
        __func__(path)
        print 'Removed ', path
    except OSError, (errno, strerror):
        print ERROR_STR % {'path' : path, 'error': strerror }
            
def removeall(path):
    if not os.path.isdir(path):
        return
    files=os.listdir(path)
    for x in files:
        fullpath=os.path.join(path, x)
        if os.path.isfile(fullpath):
            f=os.remove
            rmgeneric(fullpath, f)
        elif os.path.isdir(fullpath):
            removeall(fullpath)
            f=os.rmdir
            rmgeneric(fullpath, f)

import md5

from gui import *

def createfiles(dir="port"):
    for f in os.listdir("art/"+dir):
        if f == ".svn": continue
        if not os.path.isdir(f): continue
        myzip = ZipFile("zip_"+dir+"/"+f+".zip","w",ZIP_DEFLATED)
        for sub in os.listdir("art/"+dir+"/"+f):
            if sub == ".svn": continue
            myzip.write("art/"+dir+"/"+f+"/"+sub,sub)
        myzip.close()
        print "wrote","zips/"+f+".zip"
        
def create_path(dir):
    pathfull = ""
    for pathpart in dir.split("/"):
        pathfull+=pathpart+"/"
        if not os.path.exists(pathfull):
            os.mkdir(pathfull)
for required_path in ["art/3d","art/bg","art/ev","art/fg","art/general","art/port","music","games","fonts","sfx"]:
    create_path(required_path)

def mynames(dir="art/port"):
    files = {}
    for file in [x for x in os.listdir(dir) if x != ".svn"]:
        files[file] = get_data_from_folder(dir+"/"+file)
    return files

import cStringIO
iconcache = {}
def load_image(path):
    if path not in iconcache:
        f = urllib2.urlopen(path.replace(" ","%20"))
        txt = f.read()
        f.close()
        f = cStringIO.StringIO(txt)
        icon = pygame.image.load(f,path)
        iconcache[path] = icon
    return iconcache[path]
    
class my_o_dict(dict):
    pass
def names(url):
    url = url.replace("(","%28").replace(")","%29").replace(" ","%20")
    if 1:#try:
        f = urllib2.urlopen(ROOT_URL+url)
    else:#except:
        print "fail"
        return {}
    txt = f.read()
    lines = eval(txt)
    f.close()
    files = my_o_dict()
    files.okeys = []
    for x in lines:
        if x["zipname"] in files:
            if compare_versions(x["version"],files[x["zipname"]]["version"])<0:
                continue
        else:
            files.okeys.append(x["zipname"])
        files[x["zipname"]]=x
    return files

screen = pygame.display.set_mode([400,50])
root = widget()
root.width,root.height = [640,480]

Label = label
label = editbox(None,"Select content type to download:")
label.draw_back=False
root.add_child(label)
label.draw(screen)

list = scrollpane([0,0])
list.rpos[1]=100
list.width,list.height = [400,300]
list.status_box = editbox(None,"")
list.status_box.draw_back = False
list.status_box.draw(screen)
root.add_child(list)

def build_list(dir="art/port",url="zip_port_info",check_folder=None):
    list.pane.children = [list.status_box]
    fnd = 0
    list.status_box.text="Scanning local files..."
    mn = mynames(dir)
    list.status_box.text="Fetching data from server..."
    an = names(url)
    if check_folder:
        d = get_data_from_folder(check_folder)
        mn = {}
        for n in an:
            mn[n] = d
    cases = {"NEW":[],"UPDATED":[],"INSTALLED":[]}
    for n in an.okeys:
        if n not in mn:
            status = "NEW"
        elif compare_versions(an[n]["version"],mn[n]["version"])>0:
            status = "UPDATED"
        else:
            status = "INSTALLED"
        fnd = 1
        cb = checkbox(an[n].get("title",an[n]["zipname"]))
        cb.name = n
        cb.file = an[n]["zipfile"]
        cb.filename = an[n]["zipname"]
        p = pane([0,0])
        p.width,p.height = [380,95]
        p.align = "horiz"
        image_b = button(None,"")
        image_b.background = False
        image_b.border = False
        image_b.click_down_over = cb.click_down_over
        def load_icon_this(url=an[n]["iconurl"],but=image_b):
            try:
                image = load_image(url)
            except:
                image = None
            but.graphic = image
        threading.Thread(target=load_icon_this).start()
        p.add_child(image_b)
        stats = pane([0,0])
        stats.width,stats.height = [340,93]
        stats.align = "vert"
        stats.background = False
        stats.border = False
        stats.add_child(cb)
        sline = status 
        if an[n].get("author",""):
            sline += "                    "+"by "+an[n]["author"]
        stats.add_child(Label(sline))
        stats.date = 0
        if an[n].get("version_date",""):
            stats.date = an[n]["version"]
            stats.add_child(Label("ver %s updated on %s"%(cver_s(an[n]["version"]),an[n]["version_date"])))
        if an[n].get("website",""):
            url = an[n]["website"]
            urlb = button(None,url)
            urlb.textcolor = [0,0,255]
            try:
                import webbrowser
                setattr(urlb,url,lambda *args: webbrowser.open(url))
            except ImportError:
                pass
            stats.add_child(urlb)
        p.add_child(stats)
        p.bgcolor = {"NEW":[255,200,200],"UPDATED":[200,255,200],"INSTALLED":[255,255,255]}[status]
        p.date = stats.date
        cases[status].append(p)
    for s in ["UPDATED","NEW","INSTALLED"]:
        for n in reversed(sorted(cases[s],key=lambda el:el.date)):
            list.add_child(n)
    if dir == ".":
        dir = "updates"
    if not fnd:
        list.status_box.text  = "No "+dir+" are available to download"
    else:
        list.status_box.text = "Download "+dir+"! Click check boxes to select."

import libengine
get_url = "updates3/games.cgi?content_type=%s&ver_type=tuple&fullurl=true&version="+str(libengine.__version__)
print get_url
class Engine:
    mode = "port"
    quit_threads = 0
    root = root
    num_threads = 0
    def Download_X(self,mode,path,url,check_folder=None):
        def t():
            self.mode = mode
            self.path = path
            self.url = url
            print "try download",self.url
            build_list(path,url,check_folder)
            rpos = root.children[root.start_index].rpos
            root.children[root.start_index] = button(self,"download")
            root.children[root.start_index].rpos = rpos
        threading.Thread(target=t).start()
    def Download_Characters(self):
        self.Download_X("port","art/port",get_url%("port",))
    def Download_Backgrounds(self):
        self.Download_X("bg","art/bg",get_url%("bg",))
    def Download_Foreground(self):
        self.Download_X("fg","art/fg",get_url%("fg",))
    def Download_Games(self):
        self.Download_X("games","games",get_url%("games",))
    def Download_Music(self):
        self.Download_X("music","music",get_url%("music",))
    def Update_PyWright(self,thread=True):
        self.path = "."
        self.Download_X("engine",".",get_url%("engine",),check_folder=".")
    def get_download_in_progress(self,check):
        path,filename,url,seek = self.path,check.filename,check.file,False
        if os.path.exists("downloads/"+check.filename+"_url") and os.path.exists("downloads/"+check.filename):
            try:
                path,filename,url = open("downloads/"+check.filename+"_url","r").read().split("\t")
                seek = True
            except:
                pass
        return path,filename,url,seek
    def do_downloads(self,checkfolder=True,output=None):
        print "doing downloads"
        for x in list.pane.children[1:]:
            check = x.children[1].children[0]
            if check.checked:
                path,filename,url,seek = self.get_download_in_progress(check)
                self.download_file(path,filename,url,output,seek)
    def make_download_folders(self):
        if not os.path.exists("downloads"):
            os.mkdir("downloads")
    def download_file(self,path,filename,url,output=None,seek=False):
        self.num_threads += 1
        self.make_download_folders()
        if not hasattr(self,"progress"):
            self.progress = progress()
            root.add_child(self.progress)
        self.progress.height = 20
        self.progress.width = 400
        self.progress.rpos[1] = list.rpos[1]+list.height+20
        self.progress.progress = 0
        headers = {"User-Agent":"pywright downloader"}
        size = None
        print "download with seek",seek,url
        if seek:
            try:
                f = open("downloads/"+filename,"rb")
                old = f.read()
                f.close()
                cli = open("downloads/"+filename,"w")
                cli.write(old)
                seek = len(old)
                print "seeked",seek,"bytes"
                serv = urllib2.urlopen(url.replace(" ","%20"))
                size = int(serv.info()["Content-Length"])
                if seek>size:
                    print "resetting download"
                    seek = 0
                    os.remove("downloads/"+filename+"_url")
                    cli = open("downloads/"+filename,"w")
                headers["Range"] = "bytes=%d-%d"%(seek,size)
                serv.close()
                print "headers:",headers
            except:
                import traceback
                traceback.print_exc()
                seek = 0
        if not seek:
            seek = 0
            cli = open("downloads/"+filename,"wb")
            print "opened new file"
        
        req = urllib2.Request(url.replace(" ","%20"),None,headers)
        try:
            serv = urllib2.urlopen(req)
            print "opened resume"
        except:
            seek = 0
            serv = urllib2.urlopen(url)
            print "opened new"
        if not size:
            size = int(serv.info()["Content-Length"])
        print "size of document:",size
        read = seek
        bytes = seek
        prog = open("downloads/"+filename+"_url","w")
        prog.write(path+"\t"+filename+"\t"+url)
        prog.close()
        f = open("downloads/last","w")
        f.write(path+" "+filename)
        f.close()
        s = time.time()
        bps = 0
        while not Engine.quit_threads:
            r = serv.read(4096)
            if not r: break
            cli.write(r)
            cli.flush()
            read += len(r)
            bytes += len(r)
            self.progress.progress = read/float(size)
            print self.progress.progress
            if time.time()-s>1:
                bps = bytes/(time.time()-s)
                s = time.time()
                bytes = 0
            self.progress.text = "%sKB/%sKB - %s KB/s"%(read/1000.0,size/1000.0,bps/1000.0)
            if output:
                self.progress.rpos = [0,0]
                self.progress.width = 256
                self.progress.draw(output[0])
                output[1]()
                for evt in pygame.event.get():
                    if evt.type == pygame.QUIT: raise SystemExit
        print "closing server"
        serv.close()
        print "closing download file"
        cli.close()
        print "extract zip?"
        if read==size:
            self.progress.text = self.extract_zip(path,filename)
        print "delete progress bar"
        del self.progress
        print "switch modes"
        if self.mode == "games":
            self.Download_Games()
        self.num_threads -= 1
    def extract_zip(self,todir,filename):
        try:
            z = ZipFile("downloads/"+filename,"r")
        except:
            import traceback
            traceback.print_exc()
            return "Corrupt"
        
        if self.mode == "engine":
            root = "./"
            block = None
        #Extract folder from zip to todir
        elif filename+"/" in z.namelist():
            root = todir+"/"
            block = filename+"/"
        #Create folder from filename, extract contents of zip to there
        else:
            root = todir+"/"+filename+"/"
            try:
                os.makedirs(root)
            except:
                pass
            block = None
        for name in z.namelist():
            if hasattr(self,"progress"):
                self.progress.text = "extracting:"+name
            print "extract:",name
            try:
                txt = z.read(name)
            except:
                return "Corrupt download"
            if block:
                if not name.startswith(block):
                    continue
            if "/" in name and not os.path.exists(root+name.rsplit("/",1)[0]):
                os.makedirs(root+name.rsplit("/",1)[0])
            if not name.endswith("/"):
                f = open(root+name,"wb")
                f.write(txt)
                f.close()
        z.close()
        os.remove("downloads/"+filename)
        try:
            os.remove("downloads/last")
        except:
            pass
        if self.mode == "engine":
            self.root.children[:] = [editbox(None,"In order to complete upgrade you must restart.")]
            self.need_restart = True
        return "FINISHED"
    def download(self):
        t = threading.Thread(target=self.do_downloads)
        t.start()
    def End_updater(self,*args):
        Engine.quit_threads = True
        self.running = False
                
def run():
    screen = pygame.display.set_mode([400,480])
    e = Engine()
    e.running = True
    start = button(e,"download")
    start.rpos[1] = list.rpos[1]+list.height
    end = button(e,"End updater")
    end.rpos[1] = start.rpos[1]+50
    root.add_child(start)
    root.add_child(end)
    root.start_index = root.children.index(start)

    char_b = button(e,"Download Characters")
    #char_b.rpos[0]=label.rpos[0]+label.width
    char_b.rpos[1]=20
    char_b.draw(screen)
    root.add_child(char_b)
    bg_b = button(e,"Download Backgrounds")
    bg_b.rpos[0]=char_b.rpos[0]+char_b.width+5
    bg_b.rpos[1]=20
    bg_b.draw(screen)
    root.add_child(bg_b)
    fg_b = button(e,"Download Foreground")
    fg_b.rpos[0]=bg_b.rpos[0]+bg_b.width+5
    fg_b.rpos[1]=20
    fg_b.draw(screen)
    root.add_child(fg_b)
    game_b = button(e,"Download Games")
    game_b.rpos[0]=0
    game_b.rpos[1]=40
    game_b.draw(screen)
    root.add_child(game_b)
    music_b = button(e,"Download Music")
    music_b.rpos[0]=game_b.rpos[0]+game_b.width+5
    music_b.rpos[1]=40
    music_b.draw(screen)
    root.add_child(music_b)
    info_label = editbox(None, "Hold shift to select multiple items in a category")
    root.add_child(info_label)
    info_label.draw_back = False
    info_label.rpos[0]=0
    info_label.rpos[1]=60
    
    pwup_b = button(e,"Update PyWright")
    pwup_b.rpos[1]=80
    pwup_b.rpos[0]=300
    pwup_b.draw(screen)
    root.add_child(pwup_b)
    
    if os.path.exists("downloads/last"):
        try:
            last_path,last_dl = open("downloads/last","r").read().split(" ")
            e.extract_zip(last_path,last_dl)
        except:
            os.remove("downloads/last")

    clock = pygame.time.Clock()
    while e.running:
        mp = pygame.mouse.get_pos()
        clock.tick(60)
        screen.fill([225,225,225])
        root.draw(screen)
        pygame.display.flip()
        pygame.event.pump()
        quit = root.handle_events(pygame.event.get())
        if quit:
            Engine.quit_threads = True
            e.running = False
            if getattr(e,"need_restart",False):
                sys.exit()
    while Engine.num_threads:
        print Engine.num_threads
        pass
if __name__=="__main__":
    run()
