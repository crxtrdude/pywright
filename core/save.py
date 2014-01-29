#IMPROVEMENTS
#scroll, zoom don't save that they are scrolling background image (maybe shouldnt scroll background image!)
#save and load still available in menu after game exits
#instance attributes which are based on assets.variables: one object created, change variable, create another -
#   need to save the actual variable and not rely on assets.variables entry to be accurate

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
        cp(["dim","pos","z","rot","x","id_name","scale","name","pri","fade","wait","spd","blinkspeed","loops","loopmode","start","end","screen_setting"],ob,oprops)
    if isinstance(ob,fadesprite) or isinstance(ob,portrait):
        cp(["invert","tint","greyscale"],ob,oprops)
    if isinstance(ob,bg):
        return ["bg",[],oprops]
    elif isinstance(ob,testimony_blink):
        return ["testimony_blink",[],oprops]
    elif isinstance(ob,fg):
        return ["fg",[],oprops]
    elif isinstance(ob,evidence):
        oprops["id"] = ob.id
	oprops["page"] = ob.page
        return ["evidence",[],oprops]
    elif isinstance(ob,portrait):
        cp(["clicksound","nametag","charname","emoname","modename","blinkemo","supermode"],ob,oprops)
        tsprops = {}
        bsprops = {}
        copy = ["loops","x","blinkspeed","spd","start","end","loopmode","dim"]
        if hasattr(ob,"talk_sprite"):
            cp(copy,ob.talk_sprite,tsprops)
        if hasattr(ob,"talk_sprite"):
            cp(copy,ob.blink_sprite,bsprops)
        oprops["tsprite"] = tsprops
        oprops["bsprite"] = bsprops
        return ["char",[ob.name,ob.hide],oprops]
    elif isinstance(ob,mesh):
        cp(["regions"],ob,oprops)
        return ["mesh",[ob.meshfile],oprops]
    elif isinstance(ob,surf3d):
        return ["surf3d",[ob.pos,ob.sw,ob.sh,ob.width,ob.height],oprops]
    elif isinstance(ob,evidence_menu):
        cp(["page","sx","sy","mode","pri","z","item_set"],ob,oprops)
        oprops["items"] = [{"id":x.id,"page":x.page} for x in ob.items]
        return ["ev_menu",[],oprops]
    elif isinstance(ob,scroll):
        cp(["dx","dy","dz","amtx","amty","speed","wait","filter","kill"],ob,oprops)
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
    elif isinstance(ob,tintanim):
        cp(["start","end","speed","wait"],ob,oprops)
        oprops["ob_ids"] = [o.id_name for o in ob.obs if hasattr(o,"id_name")]
        return ["tintanim",[],oprops]
    elif isinstance(ob,textbox):
        cp(["z","num_lines","kill","skipping","statement","wait","pressing","presenting","can_skip","blocking","_clicksound","go"],ob,oprops)
        t = getattr(ob,"text","")
        if "\n" not in t:
            return
        oprops["text"] = t.split("\n",1)[1]
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
        cp(["pos","delay","flash_amount","flash_dir","flash_color"],ob,oprops)
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
    elif isinstance(ob,ws_button) and hasattr(ob,"s_text"):
        cp(["s_text","s_graphic","rpos","s_macroname","id_name","z","pri","hold_func","screen_setting"],ob,oprops)
        return ["button",[],oprops]
    elif isinstance(ob,waitenter):
        return ["waitenter",[],oprops]
    elif isinstance(ob,delay):
        cp(["ticks"],ob,oprops)
        return ["delay",[],oprops]
    elif isinstance(ob,timer):
        cp(["ticks","run"],ob,oprops)
        return ["timer",[],oprops]
