import os,sys
if sys.platform=="win32":
    os.environ['SDL_VIDEODRIVER']='windib'
import zlib
from core import pygame
import threading,time,urllib,urllib2
from zipfile import ZipFile,ZIP_DEFLATED

ERROR_STR= """Error removing %(path)s, %(error)s """

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

def cver(verstr):
    """Converts a version string into a number"""
    if verstr.startswith("b"):
        return int(verstr[1:])-1000
    return int(verstr)
def getver(folder):
    try:
        if ".pwv" in os.listdir(folder):
            return cver(open(folder+"/.pwv").read())
    except:
        pass
    return 0
def zipinfo(name):
    spl = name.rsplit(".zip_",1)
    if len(spl)<2: return None
    ver = cver(spl[1])
    if "/" in spl[0]:
        spl[0] = spl[0].rsplit("/",1)[1]
    inf = {"name":spl[0],"ver":ver,"realpath":name}
    return inf

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
        files[file] = getver(dir+"/"+file)
    return files
def names(url):
    try:
        f = urllib2.urlopen("http://pywright.dawnsoft.org/"+url)
    except:
        return {}
    lines = f.read().replace("\r\n","\n").split("\n")
    f.close()
    files = {}
    for x in lines:
        if not x.strip(): continue
        inf = zipinfo(x)
        if inf and (not files.has_key(inf["name"]) or files[inf["name"]]<inf["ver"]):
            files[inf["name"]]=inf
    return files

screen = pygame.display.set_mode([400,50])
root = widget()
root.width,root.height = [640,480]

label = editbox(None,"Select Art Type to Download:")
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

def build_list(dir="art/port",url="zip_port_info"):
    list.children = [list.status_box,list.scbar]
    fnd = 0
    list.status_box.text="Scanning local files..."
    mn = mynames(dir)
    list.status_box.text="Fetching data from server..."
    an = names(url)
    for n in sorted(an.keys()):
        if n not in mn or an[n]["ver"]>mn[n]:
            fnd = 1
            cb = checkbox(n)
            cb.file = an[n]["realpath"]
            cb.filename = an[n]["name"]
            list.add_child(cb)
            if n in mn: cb.editbox.col = [255,0,0]
    if not fnd:
        list.status_box.text  = "No new "+dir+" are available to download"
    else:
        list.status_box.text = "Download "+dir+". Updated or new."

class Engine:
    mode = "port"
    quit_threads = 0
    dl_url = "http://pywright.dawnsoft.org/"
    def Download_X(self,mode,path,url):
        def t():
            self.mode = mode
            self.path = path
            self.url = url
            build_list(path,url)
            rpos = root.children[root.start_index].rpos
            root.children[root.start_index] = button(self,"download")
            root.children[root.start_index].rpos = rpos
        threading.Thread(target=t).start()
    def Download_Characters(self):
        self.Download_X("port","art/port","ports.php")
    def Download_Backgrounds(self):
        self.Download_X("bg","art/bg","bg.php")
    def Download_Foreground(self):
        self.Download_X("fg","art/fg","fg.php")
    def Download_Games(self):
        self.Download_X("games","games","games2.php")
    def Download_Music(self):
        self.Download_X("music","music","music2.php")
    def Upload_My_Games(self):
        list.status_box.text="Fetching data from server..."
        def t():
            self.mode = "send"
            list.children  = [list.status_box,list.scbar]
            online_games = names("games.php")
            for n in os.listdir("games"):
                if n==".svn": continue
                cb = checkbox(n)
                if n not in online_games.keys() or online_games[n]["ver"]<getver("games/"+n):
                    cb.editbox.col = [255,0,0]
                list.add_child(cb)
            rpos = root.children[root.start_index].rpos
            root.children[root.start_index] = button(self,"upload")
            root.children[root.start_index].rpos = rpos
            list.status_box.text="Which game to upload: Red games have been changed by you."
        threading.Thread(target=t).start()
    def Update_PyWright(self,thread=True):
        def t():
            list.status_box.text="Fetching data from server..."
            self.mode = "engine"
            list.children  = [list.status_box,list.scbar]
            self.path = "."
            self.url = "updates2.php"
            ver = getver(".")
            online_update = names("updates2.php")
            cb = None
            for n in online_update:
                if online_update[n]["ver"]>ver:
                    cb = checkbox(n)
                    cb.editbox.col = [255,0,0]
                    cb.file = online_update[n]["realpath"]
                    list.add_child(cb)
            if not cb:
                list.status_box.text="No updates found."
                return
            rpos = root.children[root.start_index].rpos
            root.children[root.start_index] = button(self,"update")
            root.children[root.start_index].rpos = rpos
            list.status_box.text="Download engine updates (just get the latest one):"
            #~ rpos = root.children[root.start_index].rpos
            #~ root.children[root.start_index] = button(self,"download")
            #~ root.children[root.start_index].rpos = rpos
        if thread:
            thread = threading.Thread(target=t)
            thread.start()
            return thread
        else: t()
    def do_downloads(self,checkfolder=True,output=None):
        for x in list.children[2:]:
            if x.checked:
                if not hasattr(self,"progress"):
                    self.progress = progress()
                    root.add_child(self.progress)
                self.progress.height = 20
                self.progress.width = 400
                self.progress.rpos[1] = list.rpos[1]+list.height+20
                self.progress.progress = 0
                print self.dl_url+"/"+x.file
                serv = urllib2.urlopen(self.dl_url+x.file)
                size = int(serv.info()["Content-Length"])
                read = 0
                bytes = 0
                cli = open(x.filename,"wb")
                s = time.time()
                bps = 0
                while not Engine.quit_threads:
                    r = serv.read(1024)
                    if not r: break
                    cli.write(r)
                    read += len(r)
                    bytes += len(r)
                    self.progress.progress = read/float(size)
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
                serv.close()
                cli.close()
                if os.path.exists(self.path+"/"+x.text):
                    if not os.path.isdir(self.path+"/"+x.text):
                        os.remove(self.path+"/"+x.text)
                    else:
                        removeall(self.path+"/"+x.text)
                if not os.path.exists(self.path+"/"+x.text):
                    os.mkdir(self.path+"/"+x.text)
                try:
                    z = ZipFile(x.filename,"r")
                except:
                    print "File corrupt"
                    return
                for name in z.namelist():
                    txt = z.read(name)
                    if "/" in name:
                        try:
                            os.makedirs(self.path+"/"+x.text+"/"+name.rsplit("/",1)[0])
                        except:
                            pass
                    if not name.endswith("/"):
                        f = open(self.path+"/"+x.text+"/"+name,"wb")
                        f.write(txt)
                        f.close()
                z.close()
                os.remove(x.filename)
                root.children.remove(self.progress)
                list.children.remove(x)
                if len(list.children)<=2:
                    list.status_box.text = "No more new downloads."
                del self.progress
    def download(self):
        t = threading.Thread(target=self.do_downloads)
        t.start()
    def upload(self):
        t = threading.Thread(target=self.do_uploads)
        t.start()
    def update(self):
        t = threading.Thread(target=self.do_update)
        t.start()
    def do_uploads(self):
        for x in list.children[2:]:
            if x.checked:
                if not hasattr(self,"progress"):
                    self.progress = progress()
                    root.add_child(self.progress)
                self.progress.height = 20
                self.progress.width = 400
                self.progress.rpos[1] = list.rpos[1]+list.height+20
                self.progress.progress = 0
                self.progress.text = "Upload commencing, may take some time"
                z = ZipFile(x.text+".zip","w")
                for folder,folders,files in os.walk("games/"+x.text):
                    if ".svn" in folder: continue
                    for file in files:
                        if file in ["save","last"]: continue
                        file = (folder+"/"+file).replace("\\","/")
                        z.write(file,file.replace("games/"+x.text,""))
                z.close()
                
                
                data = {}
                data["id"]=x.text+".zip,"+str(dates_content("games/"+x.text))
                data["file"] = open(x.text+".zip","rb").read()
                os.remove(x.text+".zip")
                
                import httplib
                conn = httplib.HTTPConnection("pywright.dawnsoft.org")
                conn.connect()
                conn.putrequest("POST","/up.php")
                data = urllib.urlencode(data)
                size = len(data)
                print size
                conn.putheader("Content-Length",str(size))
                conn.putheader("Content-Type","application/x-www-form-urlencoded")
                conn.endheaders()
                print "sending the data"
                while data:
                    s = data[:2024]
                    data = data[2024:]
                    conn.send(s)
                    self.progress.progress = (size-len(data))/float(size)
                    if Engine.quit_threads: return
                conn.send("\r\n\r\n")
                resp = conn.getresponse()
                print resp.read()
                conn.close()

                root.children.remove(self.progress)
                x.editbox.col = [0,0,0]
                x.checked = False
                del self.progress
    def do_update(self,output=False):
        for x in list.children[2:]:
            if x.checked:
                print x
                if not hasattr(self,"progress"):
                    self.progress = progress()
                    root.add_child(self.progress)
                self.progress.height = 20
                self.progress.width = 400
                self.progress.rpos[1] = list.rpos[1]+list.height+20
                self.progress.progress = 0
                serv = urllib2.urlopen(self.dl_url+x.file)
                size = int(serv.info()["Content-Length"])
                read = 0
                bytes = 0
                cli = open("update.zip","wb")
                s = time.time()
                bps = 0
                while not Engine.quit_threads:
                    r = serv.read(1024)
                    if not r: break
                    cli.write(r)
                    read += len(r)
                    bytes += len(r)
                    self.progress.progress = read/float(size)
                    if time.time()-s>1:
                        bps = bytes/(time.time()-s)
                        s = time.time()
                        bytes = 0
                    self.progress.text = "%.02dKB/%.02dKB : %.02d KB/s"%(read/1000.0,size/1000.0,bps/1000.0)
                    if output:
                        self.progress.rpos = [0,0]
                        self.progress.draw(screen)
                        pygame.display.flip()
                        for evt in pygame.event.get():
                            if evt.type == pygame.QUIT: raise SystemExit
                serv.close()
                cli.close()
                root.children.remove(self.progress)
                list.children.remove(x)
                if os.path.exists("update.zip"):
                    z = ZipFile("update.zip","r")
                    for name in z.namelist():
                        txt = z.read(name)
                        print name
                        if "/" in name:
                            try:
                                os.makedirs("./"+name.rsplit("/",1)[0])
                            except:
                                pass
                        try:
                            f = open("./"+name,"wb")
                            f.write(txt)
                            f.close()
                        except:
                            pass
                    z.close()
                    os.remove("update.zip")
                list.status_box.text = "Update completed."
                del self.progress
                
def run():
    screen = pygame.display.set_mode([400,480])
    e = Engine()
    start = button(e,"download")
    start.rpos[1] = list.rpos[1]+list.height
    root.add_child(start)
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

    #~ lbl = root.add_child(editbox(None,"Manage Games:"))
    #~ lbl.rpos[1]=60
    #~ lbl.draw_back=False
    #~ lbl.draw(screen)
    #~ up_b = button(e,"Upload My Games")
    #~ up_b.rpos[1]=lbl.rpos[1]
    #~ up_b.rpos[0]=lbl.rpos[0]+lbl.width+5
    #~ up_b.draw(screen)
    #~ root.add_child(up_b)
    
    pwup_b = button(e,"Update PyWright")
    pwup_b.rpos[1]=80
    pwup_b.rpos[0]=300
    pwup_b.draw(screen)
    root.add_child(pwup_b)

    clock = pygame.time.Clock()
    running = True  
    while running:
        mp = pygame.mouse.get_pos()
        clock.tick(60)
        screen.fill([225,225,225])
        root.draw(screen)
        pygame.display.flip()
        pygame.event.pump()
        quit = root.handle_events(pygame.event.get())
        if quit:
            Engine.quit_threads = True
            running = False
if __name__=="__main__":
    run()