import os,sys,pygame,math,urllib2,urllib,socket,time
sys.path.append("tools")
import runner
external = runner.runner
import re

def recog(file):
    f = open(file)
    beg = f.read(15)
    f.close()
    if "PNG" in beg:
        return "png"
    if "GIF" in beg:
        return "gif"
    if "JFIF" in beg:
        return "jpg"

if __name__=="__main__":
    try:
        pygame.display.set_mode([1,1])
    except:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        pygame.display.set_mode([1,1])

MAX_SURFACE_WIDTH=1024

def go(path_to_gif,saveto=None,delete=False,giffolder="tmp/"):
    if path_to_gif.startswith("http://"):
        for t in range(5):
            try:
                print "open"
                f = urllib2.urlopen("http://"+urllib.quote(path_to_gif.split("http://",1)[1]),timeout=5)
                path_to_gif = giffolder+path_to_gif.rsplit("/",1)[1]
            except socket.timeout:
                print "need sleep"
                time.sleep(2)
                continue
            try:
                print "ready to write"
                out = open(path_to_gif,"wb")
                out.write(f.read())
            except socket.timeout:
                print "need sleep"
                time.sleep(2)
                f.close()
                out.close()
                continue
            print "writ"
            f.close()
            out.close()
            break
    if not saveto:
        root = path_to_gif.rsplit(".",1)[0]
    else:
        root = saveto.rsplit(".",1)[0]
    strip_name = root+".png"
    txt_name = root+".txt"

    if recog(path_to_gif) in ["png","jpg"]:
        out = open(strip_name,"wb")
        out.write(open(path_to_gif,"rb").read())
        out.close()
        out = open(txt_name,"w")
        out.write("")
        out.close()
        return root
    stdout,stderr = external.run({"command":"gifsicle","operation":"info","path":path_to_gif})
    loop = "loop forever" in stdout
    delays = []
    for x in stdout.split("  + ")[1:]:
        delay = x.find(" delay ")
        if delay==-1:
            delays.append(None)
            continue
        s = re.findall("(\d+(\.\d+))s",x)
        if s:
            print s
            delays.append(float(s[0][0]))
    #delays are seconds: need frames, 60frames = 1 second
    delays = [x*60.0 for x in delays if x]
    print loop,delays
    
    stdout,stderr = external.run({"command":"gifsicle","operation":"explode","path":path_to_gif})
    if delete:
        os.remove(path_to_gif)
    i = 0
    pygame_frames = []
    while True:
        next_frame = "%s.%.3d"%(path_to_gif,i)
        if not os.path.exists(next_frame):
            break
        frame = pygame.image.load(next_frame)
        os.remove(next_frame)
        pygame_frames.append(frame)
        i += 1
    num_frames = len(pygame_frames)
    width,height = list(pygame_frames[0].get_size())
    in_row = MAX_SURFACE_WIDTH//width
    if num_frames<in_row:
        in_row = num_frames
    num_rows = int(math.ceil(num_frames/float(in_row)))
    out = pygame.Surface([width*in_row,height*num_rows]).convert_alpha()
    out.fill([0,0,0,0])
    x = 0
    y = 0
    for f in pygame_frames:
        if x+f.get_width()>out.get_width():
            x = 0
            y+=f.get_height()
        out.blit(f,[x,y])
        x+=f.get_width()
    pygame.image.save(out,strip_name)
    f = open(txt_name,"w")
    f.write("horizontal %s\nvertical %s\nlength %s\n"%(in_row,num_rows,len(pygame_frames)))
    if loop:
        f.write("loops 1\n")
    else:
        f.write("loops 0\n")
    for i,d in enumerate(delays):
        if d:
            d = int(d)
            if d==0:
                d=1
            f.write("framedelay %s %s\n"%(i,d))
    return root

if __name__ == "__main__":
    if len(sys.argv)<2:
        for f in os.listdir("."):
            if f.endswith(".gif"):
                saveto=f.replace("(a)","(blink)").replace("(b)","(talk)").replace("klavier-","")
                go(f,saveto)
    else:
        go(sys.argv[1])
