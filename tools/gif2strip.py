import os,sys,subprocess,pygame,math
pygame.display.set_mode([1,1])

MAX_SURFACE_WIDTH=1024

def go(path_to_gif):
    path_to_gif = sys.argv[1]
    root = path_to_gif.rsplit(".",1)[0]
    strip_name = root+".png"
    txt_name = root+".txt"

    proc = subprocess.Popen('gifsicle --no-background -U -e "%s" -o "%s"'%(path_to_gif,path_to_gif))
    proc.wait()
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
    f.write("horizontal %s\nvertical %s\nlength %s\nloops 1\n"%(in_row,num_rows,len(pygame_frames)))

if __name__ == "__main__":
    if len(sys.argv)<2:
        sys.argv.append(r"games\aaotest\art\port\aao_1\Ressources_Images_persos_PhoenixVieux_1.gif(talk).gif")
    go(sys.argv[1])