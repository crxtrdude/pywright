from core import settings
from core.core import *

def make_screen():
    if assets.swidth<256:
        assets.swidth=256
    if assets.sheight/assets.num_screens<192:
        assets.sheight = 192*assets.num_screens
    if not hasattr(assets,"cur_screen"):
        assets.cur_screen = 0
    if android:
        flags = pygame.FULLSCREEN
    else:
        flags = pygame.RESIZABLE|pygame.FULLSCREEN*assets.fullscreen
    SCREEN=pygame.real_screen = pygame.display.set_mode([assets.swidth,assets.sheight],flags)
    ns = assets.num_screens
    if assets.cur_screen:
        ns = 2
    pygame.screen = pygame.Surface([sw,sh*2]).convert()
    pygame.blank = pygame.screen.convert()
    pygame.blank.fill([0,0,0])
    pygame.js1 = None
    def gl():
        return pygame.js1 and pygame.js1.get_numhats() and pygame.js1.get_hat(0)[0]<0
    def gr():
        return pygame.js1 and pygame.js1.get_numhats() and pygame.js1.get_hat(0)[0]>0
    def gu():
        return pygame.js1 and pygame.js1.get_numhats() and pygame.js1.get_hat(0)[1]>0
    def gd():
        return pygame.js1 and pygame.js1.get_numhats() and pygame.js1.get_hat(0)[1]<0
    pygame.jsleft = gl
    pygame.jsright = gr
    pygame.jsup = gu
    pygame.jsdown = gd
    if not android:
        pygame.display.set_icon(pygame.image.load("art/general/bb.png"))
        if pygame.joystick.get_init():
            pygame.joystick.quit()
        pygame.joystick.init()
        if pygame.joystick.get_count():
            pygame.js1 = pygame.joystick.Joystick(0)
            pygame.js1.init()
        if os.environ.get("SDL_VIDEODRIVER",0)=="dummy":
            pygame.screen = pygame.Surface([sw,sh*2],0,32)
            pygame.blank = pygame.Surface([sw,sh*2],0,32)
            pygame.blank.fill([0,0,0])

def scale_relative_click(pos,rel):
    mode,dim = settings.screen_format(assets)
    def col(pp,ss):
        if pos[0]>=pp[0] and pos[0]<=pp[0]+ss[0]\
            and pos[1]>=pp[1] and pos[1]<=pp[1]+ss[1]:
            x = rel[0]/float(ss[0])*sw
            y = rel[1]/float(ss[1])*sh
            return [x,y]
    if dim["top"]:
        r = col(*dim["top"][2:])
        if r:
            return r
    if dim["bottom"]:
        r = col(*dim["bottom"][2:])
        if r:
            return r
    return rel
    
def translate_click(pos):
    mode,dim = settings.screen_format(assets)
    def col(pp,ss):
        if pos[0]>=pp[0] and pos[0]<=pp[0]+ss[0]\
            and pos[1]>=pp[1] and pos[1]<=pp[1]+ss[1]:
            x = pos[0]-pp[0]
            x = x/float(ss[0])*sw
            y = pos[1]-pp[1]
            y = y/float(ss[1])*sh
            return [int(x),int(y)]
    if dim["top"]:
        r = col(*dim["top"][2:])
        if r:
            return r
    if dim["bottom"]:
        r = col(*dim["bottom"][2:])
        if r:
            r[1]+=sh
            return r
    return [-100000,-100000]
def fit(surf,size):
    if assets.smoothscale and surf.get_bitsize() in [24,32]:
        surf = pygame.transform.scale2x(surf)
        surf = pygame.transform.smoothscale(surf,[int(x) for x in size])
    else:
        surf = pygame.transform.scale(surf,[int(x) for x in size])
    return surf
def draw_screen(showfps):
    scale = 0
    if assets.sheight!=sh or assets.swidth!=sw: scale = 1
    scaled = pygame.screen
    top = scaled.subsurface([[0,0],[sw,sh]])
    bottom = top
    mode,dim = settings.screen_format(assets)
    if mode == "two_screens" or mode == "horizontal" or mode == "show_one" or mode == "small_bottom_screen":
        bottom = scaled.subsurface([[0,sh],[sw,sh]])
    pygame.real_screen.fill([10,10,10])
    def draw_segment(dest,surf,pos,size):
        rp = [pos[0]*assets.swidth,pos[1]*assets.sheight]
        rs = [size[0]*assets.swidth,size[1]*assets.sheight]
        surf = fit(surf,rs)
        dest.blit(surf,rp)
    if dim["top"]:
        draw_segment(pygame.real_screen,top,dim["top"][0],dim["top"][1])
    if dim["bottom"]:
        draw_segment(pygame.real_screen,bottom,dim["bottom"][0],dim["bottom"][1])
    if showfps:
        pygame.real_screen.blit(assets.get_font("nt").render(str(assets.clock.get_fps()),1,[100,180,200]),[0,pygame.real_screen.get_height()-12])
    pygame.display.flip()