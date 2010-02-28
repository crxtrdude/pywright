#IMPROVEMENTS
#scroll, zoom don't save that they are scrolling background image (maybe shouldnt scroll background image!)
#save and load still available in menu after game exits
#instance attributes which are based on assets.variables: one object created, change variable, create another -
#   need to save the actual variable and not rely on assets.variables entry to be accurate

import gui
from core import *


def cp(l,o,p):
    """Copy properties named in the list l from object o into dict p"""
    for arg in l:
        if hasattr(o,arg):
            p[arg] = getattr(o,arg)

def save(ob):
    oprops = {}
    cp(["id_name"],ob,oprops)
    if hasattr(ob,"fail"):
        oprops["fail"] = ob.fail
    if isinstance(ob,(sprite,portrait,listmenu,menu)):
        cp(["dim","pos","z","rot","x","id_name","scale","name","pri","fade","wait","spd"],ob,oprops)
    if isinstance(ob,bg):
        return ["bg",[],oprops]
    elif isinstance(ob,testimony_blink):
        return ["testimony_blink",[],oprops]
    elif isinstance(ob,fg):
        return ["fg",[],oprops]
    elif isinstance(ob,evidence):
        oprops["id"] = ob.id
        return ["evidence",[],oprops]
    elif isinstance(ob,portrait):
        cp(["clicksound","nametag","charname","emoname","modename"],ob,oprops)
        return ["char",[ob.name,ob.hide],oprops]
    elif isinstance(ob,evidence_menu):
        cp(["page","sx","sy","mode","pri","z","item_set"],ob,oprops)
        oprops["items"] = [x.id for x in ob.items]
        return ["ev_menu",[],oprops]
    elif isinstance(ob,scroll):
        cp(["dx","dy","amtx","amty","speed","wait","filter","kill"],ob,oprops)
        oprops["ob_ids"] = [o.id_name for o in ob.obs if hasattr(o,"id_name")]
        return ["scroll",[],oprops]
    elif isinstance(ob,zoomanim):
        cp(["mag_per_frame","frames","wait","kill"],ob,oprops)
        oprops["ob_ids"] = [o.id_name for o in ob.obs if hasattr(o,"id_name")]
        return ["zoomanim",[],oprops]
    elif isinstance(ob,rotateanim):
        cp(["axis","degrees","wait","kill","speed"],ob,oprops)
        oprops["ob_ids"] = [o.id_name for o in ob.obs if hasattr(o,"id_name")]
        return ["rotateanim",[],oprops]
    elif isinstance(ob,fadeanim):
        cp(["start","end","speed","wait"],ob,oprops)
        oprops["ob_ids"] = [o.id_name for o in ob.obs if hasattr(o,"id_name")]
        return ["fadeanim",[],oprops]
    elif isinstance(ob,textbox):
        cp(["z","num_lines","kill","skipping","statement","wait","pressing","presenting","can_skip","blocking","_clicksound","go"],ob,oprops)
        oprops["text"] = getattr(ob,"text").split("\n",1)[1]
        return ["textbox",[oprops["text"],ob.color,ob.delay,ob.speed,ob.rightp,ob.leftp,ob.nametag],oprops]
    elif isinstance(ob,textblock):
        cp(["text","lines","color"],ob,oprops)
        return ["textblock",[oprops["text"]],oprops]
    elif isinstance(ob,uglyarrow):
        cp(["showleft","width","height","high"],ob,oprops)
        if ob.textbox:
            oprops["_tb"] = True
        return ["uglyarrow",[],oprops]
    elif isinstance(ob,penalty):
        cp(["pos","delay"],ob,oprops)
        return ["penalty",[ob.end,ob.var],oprops]
    elif isinstance(ob,menu):
        cp(["options","scene","open_script","selected"],ob,oprops)
        return ["menu",[],oprops]
    elif isinstance(ob,listmenu):
        cp(["max_fade","options","si","selected","hidden","tag"],ob,oprops)
        return ["listmenu",[],oprops]
    elif isinstance(ob,examine_menu):
        cp(["hide","regions","blocking","xscroll","xscrolling","mx","my","selected"],ob,oprops)
        oprops["bg_ids"] = [o.id_name for o in ob.bg if hasattr(o,"id_name")]
        return ["examinemenu",[],oprops]
    elif isinstance(ob,guiWait):
        cp(["run"],ob,oprops)
        return ["guiWait",[],oprops]
    elif isinstance(ob,gui.button) and hasattr(ob,"s_text"):
        cp(["s_text","s_graphic","rpos","s_macroname","id_name","z","pri"],ob,oprops)
        return ["button",[],oprops]
    elif isinstance(ob,waitenter):
        return ["waitenter",[],oprops]
    elif isinstance(ob,delay):
        cp(["ticks"],ob,oprops)
        return ["delay",[],oprops]
    elif isinstance(ob,timer):
        cp(["ticks","run"],ob,oprops)
        return ["timer",[],oprops]