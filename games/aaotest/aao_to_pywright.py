#TODO: show evidence at start that is never revealed
"""Limitations:
cannot hide a statement that wasn't hidden from the start

The delay function is not accurate - in AAO it is timed from the start of the message, in pywright
it is timed from the end. We adjust for this by guessing how long a text line will be printed,
but this is not very accurate. When you combine delay and a line of text, check that
the timing works out."""

import os
from BeautifulSoup import BeautifulSoup
import urllib
import urllib2
import re
import subprocess

game_url = "http://aceattorney.sparklin.org/jeu.php?id_proces=10711" #My dialogue test case
game_url = "http://aceattorney.sparklin.org/jeu.php?id_proces=6561"

def create_folders():
    if not os.path.exists("art"):
        os.mkdir("art")
    if not os.path.exists("art/fg"):
        os.mkdir("art/fg")
    if not os.path.exists("art/bg"):
        os.mkdir("art/bg")
    if not os.path.exists("art/ev"):
        os.mkdir("art/ev")
    if not os.path.exists("art/port"):
        os.mkdir("art/port")
    if not os.path.exists("music"):
        os.mkdir("music")
    if not os.path.exists("sfx"):
        os.mkdir("sfx")
create_folders()

colors = {"red": "{c900}", "white":"{c999}", 
"green":"{c090}","blue":"{c009}","skyblue":"{c339}",
"lime":"{c393}"}
def get_color(t):
    if t in colors:
        return colors[t]
    if t.startswith("rgb("):
        c = []
        for num in t[t.find("(")+1:t.rfind(")")].split(","):
            num = int(num)
            c.append(num)
        return "{c %.02x%.02x%.02x}"%tuple(c)
    if t.startswith("#"):
        return "{c "+t[1:]+"}"
assert get_color("white")=="{c999}"
assert get_color("rgb(0,0,50)")=="{c 000032}"

def cent_to_frame(t):
    t = int(t)
    seconds = t/100.0
    #60 frames = 1 second
    frames = seconds*60.0
    if frames<=0:
        return 0
    return int(frames)
assert cent_to_frame("300")==180

f = urllib.urlopen(game_url)
html = f.read()
f.close()
f = open("last.html","w")
f.write(html)
f.close()
soup = BeautifulSoup(html)
first_line = soup.find(id=re.compile("ligne_donnees_"))
table = first_line.parent
lines = table.contents

def textify(contentlist,colorize=False,replace_line_end=None):
    t = ""
    for c in contentlist:
        if isinstance(c,unicode):
            t += c
        elif c.name == "em":
            t += textify(c.contents,colorize)
        elif c.name == "span":
            if colorize:
                s = c.attrMap.get("style","").split(";")
                print "style:",s
                for arg in s:
                    if arg.startswith("color:"):
                        col = arg.split(":")[1].strip()
                        t += get_color(col)
                        break
            t += textify(c.contents,colorize)
            if colorize:
                t += "{c}"
        else:
            pass
    if replace_line_end is not None:
        t = t.replace("\n",replace_line_end)
    return t
def wget(url,saveto):
    print "get",url,"to",saveto
    import urllib
    if url.endswith(".gif"):
        prefix=saveto.rsplit(".",1)[0]
        saveto = prefix+".png"
        txt_name = prefix+".txt"
        import gif2strip
        if not (os.path.exists(txt_name) or os.path.exists(saveto)):
            try:
                gif2strip.go(url,saveto)
            except urllib2.HTTPError:
                pass
    elif url.endswith(".mp3"):
        prefix=saveto.rsplit(".",1)[0]
        saveto=prefix+".ogg"
        if not os.path.exists(saveto):
            urllib.urlretrieve(url.replace(" ","%20"),"mp3ogg/input.mp3")
            subprocess.call(["mp3ogg\mpg123.exe","-w","mp3ogg\output.wav","mp3ogg\input.mp3"])
            subprocess.call(["mp3ogg\oggenc2.exe","mp3ogg\output.wav","mp3ogg\output.ogg","--resample=44100"])
            f = open("mp3ogg/output.ogg","rb")
            o = f.read()
            f.close()
            f = open(saveto,"wb")
            f.write(o)
            f.close()
    elif not os.path.exists(saveto):
        print "retrieving"
        urllib.urlretrieve(url.replace(" ","%20"),saveto)
    return saveto
def nice_name(t):
    return t.replace("/","_").replace(":","").replace(" ","_")
def bg(t):
    if t == "no":
        t = "black"
        return t
    url = t
    if not url.startswith("http://"):
        url = "http://aceattorney.sparklin.org/"+t
    nicet = nice_name(t)
    bgname = nicet.replace(".jpg",".png")
    print bgname,url
    saveto = "art/bg/"+bgname
    wget(url,saveto)
    return bgname.rsplit(".",1)[0]
def fg(t):
    if t == "no":
        return None
    url = t
    if not url.startswith("http://"):
        url = "http://aceattorney.sparklin.org/"+t
    nicet = nice_name(t)
    fgname = nicet
    saveto = "art/fg/"+fgname
    wget(url,saveto)
    return fgname.rsplit(".",1)[0]
def makeev(t):
    if t == "no":
        return None
    url = t
    if not url.startswith("http://"):
        url = "http://aceattorney.sparklin.org/"+t
    try:
        nicet = t.replace("/","_").replace(":","")
        fgname = "aao_"+nicet
        saveto = "art/ev/"+fgname
        img = wget(url,saveto)
        return fgname.replace(".jpg","").replace(".png","").replace(".gif","")
    except:
        raise
        return None
def setupchar(id, name, talk, blink):
    charname = "aao_"+id
    if not os.path.exists("art/port/"+charname):
        os.mkdir("art/port/"+charname)
    talkname = nice_name(talk).rsplit(".",1)[0]+"(talk).png"
    if not os.path.exists("art/port/"+charname+"/"+talkname):
        url = talk
        if not url.startswith("http://"):
            url = "http://aceattorney.sparklin.org/"+url
        wget(url,"art/port/"+charname+"/"+talkname)
    blinkname = nice_name(talk).rsplit(".",1)[0]+"(blink).png"
    if blink:
        if not os.path.exists("art/port/"+charname+"/"+blinkname):
            url = blink
            if not url.startswith("http://"):
                url = "http://aceattorney.sparklin.org/"+url
            wget(url,"art/port/"+charname+"/"+blinkname)
    return charname, nice_name(talk).rsplit(".",1)[0]


all_evidence = {}  #True for each evidence id that should be revealed at the start
def get_ev_id(element):
    return "ev%s"%element["id"].split("_")[1]
f = open("evidence.txt","w")
print "search for ev"
for ev in soup.findAll(id=re.compile("(preuve|profil)_\d")):
    evid = get_ev_id(ev)
    print ev["id"]
    if ev["id"].startswith("profil"):
        evid+="$"
    all_evidence[evid] = True
    for img in ev.findAll(id=re.compile("(preuve|profil)_\d_image")):
        print img
        src = img["src"]
        imname = makeev(src)
        f.write("set %s_pic %s\n"%(evid,imname))
    for name in ev.findAll(id=re.compile("(preuve|profil)_\d_nom")):
        f.write("set %s_name %s\n"%(evid,textify(name.contents,replace_line_end="")))
    for desc in ev.findAll(id=re.compile("(preuve|profil)_\d_description")):
        print desc.contents,textify(desc.contents)
        f.write("set %s_desc %s\n"%(evid,textify(desc.contents,replace_line_end="{n}")))
    for check in ev.findAll(id=re.compile("(preuve|profil)_\d_verifier")):
        page_output = ""
        for page in check.contents[1:]:
            page_type,page_content = [textify(x,replace_line_end="{n}") for x in page.contents[:2]]
            if page_type not in ["txt","img"] or not page_content.strip():
                continue
            if page_type == "txt":
                page_output+="bg black\ntextblock 0 0 256 192 %s\n"%page_content
            elif page_type == "img":
                page_output+="bg %s\n"%bg(page_content)
            page_output+="textblock 0 180 256 12 (Press enter for next screen)\nwaitenter\n"
        if page_output:
            f.write("set %s_check %s_check\n"%(evid,evid))
            cf = open("%s_check.txt"%evid,"w")
            cf.write(page_output)
            cf.close()
f.close()

#Show evidence
def AfficherElement(vals,elements):
    type,evid = [textify(x) for x in elements]
    if type=="profil":
        evid+="$"
    vals["pretextcode"] = "ev ev%s"%evid
    vals["postcode"] = "delete name=%s"%evid

#Delete evidence
def MasquerElements(vals,elements):
    types,ids = elements
    for i in range(len(types)):
        evid = "ev%s"%textify(ids[i])
        if textify(types[i])=="profil":
            evid+="$"
        vals["pretextcode"] += "\ndelev %s"%evid
    
#Add evidence
def DevoilerElements(vals,elements):
    types,ids = elements
    for i in range(len(types)):
        evid = "ev%s"%textify(ids[i])
        if textify(types[i])=="profil":
            evid+="$"
        vals["pretextcode"] += "\naddev %s"%evid
        all_evidence[evid] = False

#Lists
def RepondreQuestion(vals,elements,amt=3):
    txt = "list\n"
    labels = []
    num = amt
    for item in elements:
        if num:
            num -= 1
            labels.append(textify(item))
        else:
            label = labels.pop(0)
            txt+="li "+label+" result=line_"+textify(item)+"\n"
    txt += "showlist\n"
    vals["postcode"] = txt
    
def ChoixEntre2(vals,elements):
    return RepondreQuestion(vals,elements,2)
    
def ChoixEntre4(vals,elements):
    return RepondreQuestion(vals,elements,4)

#Present single
def DemanderPreuve(vals,elements):
    needev = textify(elements[1])
    fail = textify(elements[2])
    succeed = textify(elements[3])
    txt = """present
label %(goodev)s
goto %(succeed)s
label none
goto %(fail)s"""%{"goodev":"ev"+needev,"succeed":"line_"+succeed,"fail":"line_"+fail}
    vals["postcode"] = txt

#GOTO
def AllerMessage(vals,elements):
    vals["postcode"] = "goto line_"+elements[0][0]
    
intromode = False
def DevoilerIntroLieu(vals,elements):
    """Intro mode off"""
    intromode = True
def DevoilerLieu(vals,elements):
    """Intro mode off"""
    intromode = False
    
#Click position in an image
def PointerImage(vals,elements):
    url = textify(elements[0])
    x1 = textify(elements[1])
    y1 = textify(elements[2])
    x2 = textify(elements[3])
    y2 = textify(elements[4])
    w = int(x2)-int(x1)
    h = int(y2)-int(y1)
    fail = textify(elements[5])
    success = textify(elements[6])
    img = bg(url)
    vals["postcode"] = """bg %(image)s
examine hide
region %(x1)d %(y1)d %(w)d %(h)d good

label good
goto %(success)s
label none
goto %(fail)s
"""%{"image":img,"x1":int(x1),"y1":int(y1),"w":w,"h":h,"fail":"line_"+fail,"success":"line_"+success}
#Click position in an image


#Add and subtract to penalty
def ReglerVie(vals,elements):
    amt = int(int(textify(elements[0]))/120.0*100)
    vals["postcode"] = "penalty %d"%(amt,)
def PerteVie(vals,elements):
    amt = int(int(textify(elements[0]))/120.0*100)
    vals["postcode"] = "penalty -%d"%(amt,)
def FaireClignoterVie(vals,elements):
    vals["postcode"] = "penalty 0"
def ReglerGameOver(vals,elements):
    """Changes where we go if penalties run out"""
    vals["postcode"] = "setvar _penalty_script intro line_%s"%elements[0][0]

crossexam = [None]
jumpto_when_press = {}
jumpto_when_present = {}
label_none = {}

def LancerCI(vals,elements):
    """Begin cross exam"""
    print elements
    crossexam[0] = True
    vals["postcode"] = "cross"
    e2 = [x[0].split("_") for x in elements if x]
    print e2
    from_statement,ev_type,ev_id,to_statement,failure_msg = (e2 + [[],[],[]])[:5]
    for i in range(len(from_statement)):
        jumpto_when_present[textify(to_statement[i])] = "ev"+ev_id[i]+" st_"+textify(from_statement[i])
    if failure_msg:
        label_none[failure_msg[0]] = True
        
def InputVar(vals,elements):
    """Ask user to define variable"""
    print elements
    pass
def TesterVar(vals,elements):
    print elements
    """Evaluate whether the variable that was input is correct"""
def DefinirVar(vals,elements):
    """Define variable"""
    vals["postcode"] += "\nsetvar %s %s"%(elements[0][0],elements[1][0])
def EvaluerCondition(vals,elements):
    """Evalute condition (condition,jump_if_success,jump_if_fail)"""
    condition,succeed,fail = [x[0] for x in elements]
    condition = condition.replace("&amp;","AND")
    vals["postcode"] += "\nis %s line_%s\ngoto line_%s"%(condition,succeed,fail)
    
def do_statement(vals):
    if crossexam[0]:
        print "statement",vals
        vals["precode"] += "\nstatement st_"+vals["id_num"]
        if vals["hidden"]:
            vals["precode"] += " test=aao_st_show_"+vals["id_num"]

def AllerCI(vals,elements):
    """Start cross exam statement"""
    jumpto_when_press[textify(elements[0])] = vals["id_num"]
    
def pauseCI(vals,elements):
    """Pause cross exam"""
    if crossexam[0]:
        crossexam[0] = None
        vals["postcode"] = "endcross"
    
def RetourCI(vals,elements):
    """Return to cross exam"""
    vals["postcode"] = "goto "+"line_"+elements[0][0]
    
def AjouterCI(vals,elements):
    """Reveal hidden statement"""
    reveal_id = elements[0][0]
    vals["postcode"] = "set aao_st_show_"+reveal_id+" true"
    
def FinDuJeu(vals,elements):
    """Finish the Game"""
    vals["postcode"] = "endscript"

def apply_event(vals,elements):
    e = [e for e in elements if not e=="\n"]
    print e
    func = textify(e[0].contents)
    if func.strip():
        func = eval(func.strip())
        func(vals,[x.contents for x in e[1:]])
            
def make_textbox(t):
    print "make textbox of",t
    #pauses, flashes, shakes, and spaces
    t = t.replace("[#]","{p60}").replace("[#f]","{f}").replace("[#s]","{s}").replace("&nbsp;"," ")
    return t
    
songs_start = html.find("liste_adresses_mp3 =")
next = html[songs_start:]
next = next[next.find(";")+1:]
all_songs = {}
while 1:
    cur,next = next.split(";",1)
    cur = cur.replace("\n","")
    if not cur.startswith("liste_adresses_mp3["):
        break
    num = cur[cur.find("[")+1:cur.find("]")]
    name = cur[cur.find("'")+1:cur.rfind("'")]
    all_songs[num] = name

def song(t,path):
    """Download song, return song name to play"""
    if t == "-1" or t not in all_songs:
        return -1
    url = all_songs[t]
    nice_t = nice_name(url)
    saveto = (path+"/"+nice_t)
    if not url.startswith("http://"):
        url = "http://aceattorney.sparklin.org/"+url
    saveto = wget(url,saveto)
    real_ext = saveto.rsplit(".",1)[1]
    nice_t = nice_t.rsplit(".",1)[0]+"."+real_ext
    return nice_t

f = open('intro.txt','w')
f.write("include evidence")
for line in lines:
    id = None
    try:
        id = line['id']
    except TypeError:
        continue
    except KeyError:
        pass
    if id:
        id_num = id.replace("ligne_donnees_","")
        vals = {"id_num":id_num,"char":None,"charblink":None,
                    "text":"","color":"",
                    "nametag":"","bg":None,"fg":None,
                    "precode":"",
                    "pretextcode":"",
                    "postcode":"",
                    "skip":False,
                    "operation":None,
                    "hidden":False}
        for attr in line.contents:
            try:
                attr['id']
            except:
                continue
            if not attr.contents:
                continue
            print attr.contents
            t = textify(attr.contents)
            if attr['id'] == 'cache_'+id_num:
                if int(t):
                    vals['skip'] = True
            if attr['id'] == "defil_auto_"+id_num:
                vals['text_delay'] = int(t)
            if attr['id'] == 'son_'+id_num:
                vals['mus'] = t
            if attr['id'] == 'type_son_'+id_num:
                vals['mus_type'] = t
            if attr['id'] == "texte_"+id_num:
                vals["text"]+=make_textbox(textify(attr.contents,True,replace_line_end="{n}"))
            if attr['id'] == "couleur_"+id_num:
                vals["color"] = get_color(t)
            if attr['id'] == 'auteur_'+id_num:
                vals["nametag"]=t.replace(" ","_")
            if attr['id'] == 'fond_'+id_num:
                vals['bg'] = bg(t)
                vals['fg'] = fg(t.rsplit(".",1)[0]+".gif")
            if attr['id'] == 'id_auteur_'+id_num:
                vals['char_id'] = t
            if attr['id'] == 'image_perso_'+id_num:
                if t != "no":
                    vals['char'] = t
            if attr['id'] == 'image_fixe_perso_'+id_num:
                vals["charblink"] = t
            if attr['id'] == 'operation_'+id_num:
                content_list = attr.contents[0]
                if content_list:
                    vals["operation"] = content_list.contents
            if attr['id'] == 'cache_'+id_num:
                vals["hidden"] = int(t)
        if vals["operation"]:
            apply_event(vals,vals["operation"])
        do_statement(vals)
        if id_num in label_none:
            f.write("label none\n")
        if id_num in jumpto_when_press:
            f.write("label press st_"+jumpto_when_press[id_num]+"\n")
        if id_num in jumpto_when_present:
            f.write("label "+jumpto_when_present[id_num]+"\n")
        if vals["skip"]:
            continue
        if intromode and vals["text"]:
            vals["text"]+="{next}"

        #A delay from the beginning of text before continuing
        if "text_delay" in vals and vals["text_delay"]:
            wait_time = cent_to_frame(vals["text_delay"])
            text_length = len(vals["text"])*3
            wait_time = (wait_time-text_length)
            if wait_time>0:
                vals["text"]+="{p%s}"%wait_time
            vals["text"]+="{next}"


        f.write("\nlabel line_"+id_num+"\n")
        if "mus" in vals and vals['mus']:
            path = {"0":"sfx","1":"music"}[vals['mus_type']]
            mus_name = song(vals['mus'],path)
            if mus_name == -1:
                f.write("\nmus\n")
            elif path=="music":
                f.write("\nmus "+mus_name+"\n")
            elif path=="sfx":
                f.write("\nsfx "+mus_name+"\n")
        if vals["precode"]:
            f.write("\n"+vals["precode"]+"\n")
        if vals["bg"]:
            f.write("\nbg "+vals["bg"])
        if not vals["char"]:
            f.write("\nchar "+vals["nametag"]+" hide")
        else:
            charname,ename = setupchar(vals["char_id"], vals["nametag"], vals["char"], vals["charblink"])
            f.write("\nchar %s nametag=%s e=%s"%(charname, vals["nametag"], ename))
        if vals["fg"]:
            f.write("\nfg "+vals["fg"]+" nowait")
        if vals["pretextcode"]:
            f.write("\n"+vals["pretextcode"]+"\n")
        if vals["text"].strip():
            vals["text"] = vals["color"]+vals["text"]
            f.write('\n"%s"'%vals["text"])
        if vals["postcode"]:
            f.write("\n"+vals["postcode"]+"\n")
f.write('\nset _speaking NO_ONE\n"THE END"\n')
f.close()

f = open("evidence.txt","a")
for evid in all_evidence:
    if all_evidence[evid]:
        f.write("\naddev %s\n"%evid)
f.close()