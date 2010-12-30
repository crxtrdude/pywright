import pygame
pygame.display.set_mode([5,5])

import os
os.chdir("..")
import sys
sys.path.append("core")
import core,libengine

def check_text(game):
    core.assets.game = game
    core.assets.stack = [libengine.Script()]
    core.assets.cur_script.init()
    def play_sound(*args,**kwargs):
        pass
    core.assets.play_sound = play_sound
    check_dirs("games/"+game)
    
def check_dirs(path):
    for file in os.listdir(path):
        p = path+"/"+file
        if ".hg" in p:
            continue
        elif os.path.isdir(p):
            check_dirs(p)
        elif file.endswith(".txt"):
            check_file(p)
            
def check_file(path):
    f = open(path)
    for i,line in enumerate(f):
        line = line.strip().decode("ascii","ignore")
        if line.startswith('"') and line.endswith('"'):
            check_line(path,i,line)
            
def check_line(path,i,line):
    tb = core.textbox(line[1:-1].replace("{n}","\n"))
    tb.can_skip = True
    tb.enter_down()
    try:
        tb.update()
    except:
        print path,i
        import traceback
        traceback.print_exc()
    if getattr(tb,"OVERAGE",0)>1:
        print path,i,tb.written
    
check_text("Turnabout Substitution")