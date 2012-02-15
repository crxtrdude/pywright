#Expression info
#f:str_begins_with() - in parenthesis can only be an inline string not a variable
#                       may or may not have quotes around it

#TODO: show evidence at start that is never revealed
#TODO: make sure to read as utf8

#TODO: psyche locks
"""
Need to figure out when retourci should actually use 'resume' and when it should
restart the cross exam. AAO has no 'resume' command, so uses RetourCI for both
kinds of things

Should create objects for each aao line, so that they can be manipulated better
and produce better code

Should build script first, then download and convert art, and use threads for the downloading

The delay function is not accurate - in AAO it is timed from the start of the message, in pywright
it is timed from the end. We adjust for this by guessing how long a text line will be printed,
but this is not very accurate. When you combine delay and a line of text, check that
the timing works out.

Currently doing one to one mapping of aao investigations, which are a mix of
standard features and specialized investigation features (different from pywright
where other than the main menu there are no special features). Later, converting
to more natural pywright code might be a good idea, such as using the specialized
menu."""

import os
from BeautifulSoup import BeautifulSoup
import urllib
import urllib2
import re
import sys
sys.path.append("../../tools")
import runner
external = runner.runner
import gif2strip

import threading

#game_id = 14571 #JM shot dunk
#game_id = "10711" #My dialogue test case
#game_id = "21671" #investigation test 1, moving, talking, presenting, examining, and hide/reveal dialog and frames
#game_id = "22330"  #investigation test 2: hide/reveal scene, hide/reveal scene intro


#game_id="19583" #TAP Case2 Prelude
#game_id="21329" #TAP Case2 Day1 Investigation
game_id="21884" #TAP Case2 Day2 Trial
game_id="18079"
game_url = "http://aceattorney.sparklin.org/jeu.php?id_proces=%s"%game_id #JM shot dunk

class WorkThread:
    def __init__(self,rootpath):
        self.rootpath = rootpath
        self.conversions = []
    def run(self):
        while self.conversions:
            conv = self.conversions.pop()
            if "charname" in conv:
                if not os.path.exists(self.rootpath+"/art/port/"+conv["charname"]):
                    os.mkdir(self.rootpath+"/art/port/"+conv["charname"])
            #print "..."
            #print "churn on",conv["url"]
            wget(conv["url"],self.rootpath+"/"+conv["dest"])
            #print self.conversions
    def start(self):
        self.t = threading.Thread(target=self.run)
        self.t.start()

class Resources:
    def __init__(self,rootpath,temppath):
        self.rootpath = rootpath
        self.temppath = temppath
        self.bg = {}
        self.fg = {}
        self.ev = {}
        self.mus = {}
        self.sfx = {}
        self.port = {}
        self.create_folders()
        self.evidence = open(self.rootpath+"/evidence.txt","w")
        self.intro = open(self.rootpath+"/intro.txt","w")
        self.presets = open(self.rootpath+"/presets.txt","w")
    def create_folders(self):
        if not os.path.exists(self.temppath):
            os.mkdir(self.temppath)
        for pth in ["","art","art/fg","art/bg","art/ev","art/port","music","sfx"]:
            pth = self.rootpath+"/"+pth
            if not os.path.exists(pth):
                os.mkdir(pth)
    def close(self):
        self.evidence.close()
        self.intro.close()
        self.presets.close()
    def write_ev_check(self,txt,file):
        f = open(self.rootpath+"/"+file,"w")
        f.write(txt)
        f.close()
    def saveall(self):
        threads = []
        for i in range(1):
            threads.append(WorkThread(self.rootpath))
        for norm in [self.bg,self.fg,self.ev,self.mus,self.sfx,self.port]:
            for name in norm:
                t = threads.pop(0)
                t.conversions.append(norm[name])
                threads.append(t)
        [t.run() for t in threads]
        while [1 for x in threads if x.conversions]:
            print x.conversions
        

res = Resources("games/aao_%s"%game_id,temppath="tmp")

if os.path.exists(res.rootpath+"/%s.html"%game_id):
    f = open(res.rootpath+"/%s.html"%game_id)
    html = f.read()
    f.close()
else:
    print "opening url"
    f = urllib.urlopen(game_url)
    print "reading"
    html = f.read()
    f.close()
    f = open(res.rootpath+"/%s.html"%game_id,"w")
    f.write(html)
    f.close()

gs = re.compile("<script.*?>(.*?)</script>",re.DOTALL|re.MULTILINE)
js = re.findall(gs,html)
main_code = js[6]
def jsformat(line,context):
    line = line.strip()
    if line.startswith("var "):
        line = line[4:]
    if line.startswith("function "):
        context["function"] = "true"
        context["brace"] = 0
        if "{" in line:
            context["brace"] = 1
        return ""
    line = line.replace("new Array()","{}")
    return line.strip()
def js2py(line,context):
    if context.get("function",""):
        for chr in line:
            if chr == "{":
                context["brace"] += 1
            elif chr == "}":
                context["brace"] -= 1
                if context["brace"]<=0:
                    context["function"] = ""
                    context["brace"] = 0
        return ""
    line = line.replace("<!--","").replace("-->","")
    return jsformat(line,context)
main_code = main_code.replace("new Array()","{}")
main_code = main_code.replace("var ","")
namespace = {}
lines = main_code.split("\n")
context = {}
for line in lines:
    line = js2py(line,context)
    if line:
        exec(line,namespace,namespace)
print namespace["donnees_messages"][1]

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
    return ""
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

def textify(contentlist,colorize=False,replace_line_end=None):
    t = ""
    for c in contentlist:
        if isinstance(c,unicode) or isinstance(c,str):
            t += c
        elif c.name == "em":
            t += textify(c.contents,colorize)
        elif c.name == "span":
            if colorize:
                s = c._getAttrMap().get("style","").split(";")
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
    saveto = saveto.replace("\\","sl")
    print "get",url,"to",saveto
    import urllib
    if url.endswith(".gif"):
        print "convert gif"
        prefix=saveto.rsplit(".",1)[0]
        saveto = prefix+".png"
        txt_name = prefix+".txt"
        if not (os.path.exists(txt_name) or os.path.exists(saveto)):
            try:
                gif2strip.go(url,saveto)
            except (urllib2.HTTPError,urllib2.URLError):
                pass
    elif url.endswith(".mp3"):
        if not os.path.exists(saveto):
            def progress(a,b,c):
                print int(a)*int(b)/float(c)
            urllib.urlretrieve(url.replace(" ","%20"),"input.mp3",reporthook=progress)
            external.run({"command":"mpg123","operation":"towav","input":"input.mp3","output":"output.wav"})
            external.run({"command":"oggenc2","operation":"toogg","input":"output.wav","output":"output.ogg"})
            f = open("output.ogg","rb")
            o = f.read()
            f.close()
            f = open(saveto,"wb")
            f.write(o)
            f.close()
            os.remove("input.mp3")
            os.remove("output.wav")
            os.remove("output.ogg")
    elif not os.path.exists(saveto):
        print "retrieving"
        urllib.urlretrieve(url.replace(" ","%20"),saveto)
    print "returning"
    return saveto
def nice_name(t):
    return t.replace("/","_").replace(":","").replace(" ","_")
def add_art(t,type):
    if t == "no":
        if type=="bg":
            return "black"
        return None
    url = t
    if not url.startswith("http://"):
        url = "http://aceattorney.sparklin.org/"+t
    nicet = nice_name(t)
    name = nicet.replace(".jpg",".png")
    saveto = "art/"+type+"/"+name
    getattr(res,type)[name] = {"url":url,"dest":saveto}
    return name.rsplit(".",1)[0]
def bg(t):
    return add_art(t,"bg")
def fg(t):
    return add_art(t,"fg")
def makeev(t):
    return add_art(t,"ev")
def setupchar(id, name, talk, blink):
    print char_id_name,"ev"+id+"$"
    charname = char_id_name["ev"+id+"$"].replace(" ","_").replace("?","_qu_")
    talkname = nice_name(talk).rsplit(".",1)[0]+"(talk).png"
    blinkname = nice_name(talk).rsplit(".",1)[0]+"(blink).png"
    for name,url in [[talkname,talk],[blinkname,blink]]:
        if not url.startswith("http://"):
            url = "http://aceattorney.sparklin.org/"+url
        res.port[name] = {"url":url,"dest":"art/port/"+charname+"/"+name,"charname":charname}
    return charname, nice_name(talk).rsplit(".",1)[0]
def song(t,path):
    """Download song, return song name to play"""
    if t == "-1" or t not in all_songs:
        return -1
    url = all_songs[t]
    nice_t = nice_name(url)
    saveto = (path+"/"+nice_t)
    if not url.startswith("http://"):
        url = "http://aceattorney.sparklin.org/"+url
    prefix=saveto.rsplit(".",1)[0]
    saveto=prefix+".ogg"
    nice_t = nice_t.rsplit(".",1)[0]+".ogg"
    res.mus[nice_t] = {"url":url,"dest":saveto}
    return nice_t

char_id_name = {}
all_evidence = {}  #True for each evidence id that should be revealed at the start
def get_ev_id(element):
    return "ev%s"%element["id"].split("_")[1]
f = res.evidence
print "search for ev"
soup = BeautifulSoup(html)
for ev in soup.findAll(id=re.compile("(preuve|profil)_\d+")):
    evid = get_ev_id(ev)
    if ev["id"].startswith("profil"):
        evid+="$"
    all_evidence[evid] = True
    for img in ev.findAll(id=re.compile("(preuve|profil)_\d+_image")):
        src = img["src"]
        print src
        imname = makeev(src)
        f.write("set %s_pic %s\n"%(evid,imname))
    for name in ev.findAll(id=re.compile("(preuve|profil)_\d+_nom")):
        name = textify(name.contents,replace_line_end="")
        if evid.endswith("$"):
            char_id_name[evid] = name
        f.write("set %s_name %s\n"%(evid,name))
    for desc in ev.findAll(id=re.compile("(preuve|profil)_\d+_description")):
        print desc.contents,textify(desc.contents)
        f.write("set %s_desc %s\n"%(evid,textify(desc.contents,replace_line_end="{n}")))
    for check in ev.findAll(id=re.compile("(preuve|profil)_\d+_verifier")):
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
            res.write_ev_check(page_output,"%s_check.txt"%evid)

#Show evidence
def AfficherElement(vals,elements):
    type,evid = elements
    if type=="profil":
        evid+="$"
    vals["pretextcode"] = "ev ev%s"%evid
    vals["postcode"] = "delete name=%s"%evid

#Delete evidence
def MasquerElements(vals,elements):
    types,ids = elements
    for i in range(len(types)):
        evid = "ev%s"%ids[i]
        if types[i]=="profil":
            evid+="$"
        vals["pretextcode"] += "\ndelev %s"%evid
    
#Add evidence
def DevoilerElements(vals,elements):
    types,ids = elements
    for i in range(len(types)):
        evid = "ev%s"%ids[i]
        if types[i]=="profil":
            evid+="$"
        vals["pretextcode"] += "\naddev %s"%evid
        all_evidence[evid] = False

#Lists
def RepondreQuestion(vals,elements,amt=3):
    txt = "list noback\n"
    labels = []
    num = amt
    for item in elements:
        if num:
            num -= 1
            labels.append(item)
        else:
            label = labels.pop(0)
            txt+="li "+label+" result=line_"+item+"\n"
    txt += "showlist\n"
    vals["postcode"] = txt
    
def ChoixEntre2(vals,elements):
    return RepondreQuestion(vals,elements,2)
    
def ChoixEntre4(vals,elements):
    return RepondreQuestion(vals,elements,4)

#Present single
def DemanderPreuve(vals,elements):
    evtypes = elements[0]
    evids = elements[1]
    fail = elements[2]
    gotos = elements[3]
    gotocode = ""
    if evids:
        for i in range(max(evids.keys())+1):
            evid = "ev%s"%evids[i]
            if evtypes[i]=="profil":
                evid+="$"
            gotocode += "label %s\n"%evid
            gotocode += "goto line_%s\n"%gotos[i]
    txt = """present noback fail=%(fail)s
%(gotocode)s
"""%{"gotocode":gotocode,"fail":"line_"+fail}
    vals["postcode"] = txt

#GOTO
def AllerMessage(vals,elements):
    vals["postcode"] = "goto line_"+elements[0]
    
#Click position in an image
def PointerImage(vals,elements):
    url = elements[0]
    xes = elements[1]
    yes = elements[2]
    x2s = elements[3]
    y2s = elements[4]
    successes = elements[6]
    fail = elements[5]
    img = bg(url)
    def make_region(x1,y1,x2,y2,success):
        w = int(x2)-int(x1)
        h = int(y2)-int(y1)
        print x1,y1,w,h,success
        return "region %s %s %s %s line_%s\n"%(x1,y1,w,h,success)
    regions = ""
    if xes:
        for i in range(max(xes.keys())+1):
            regions += make_region(xes[i],yes[i],x2s[i],y2s[i],successes[i])
    vals["postcode"] = """bg %(image)s
examine hide fail=%(fail)s
%(regions)s
"""%{"image":img,"fail":"line_"+fail,"regions":regions}
#Click position in an image


#Add and subtract to penalty
def ReglerVie(vals,elements):
    """Set penalty to amount"""
    value = int(int(textify(elements[0]))/120.0*100)
    code = "set _diff %s\n"%value
    code += "subvar _diff $penalty\n"
    code += "penalty $_diff\n"
    vals["postcode"] = code
def PerteVie(vals,elements):
    """Subtract amount from penalty"""
    amt = int(int(elements[0])/120.0*100)
    vals["postcode"] = "penalty -%d"%(amt,)
def FaireClignoterVie(vals,elements):
    """Show flashing element of penalty"""
    vals["postcode"] = "flashpenalty %s"%int(elements[0][0])
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
    from_statement,ev_type,ev_id,to_statement,failure_msg = (elements + [[],[],[]])[:5]
    from_statement = from_statement.split("_")
    ev_type = ev_type.split("_")
    ev_id = ev_id.split("_")
    to_statement = to_statement.split("_")
    for i in range(len(from_statement)):
        jumpto_when_present[to_statement[i]] = "ev"+ev_id[i]+" st_"+from_statement[i]
    if failure_msg:
        label_none[failure_msg] = "none"
        
def InputVar(vals,elements):
    """Ask user to define variable
    [varname,vartype,password?]"""
    vals["postcode"] += """gui Input %s name=_in x=12 y=12 password width=100
gui Button _next__inputvar name=_inb x=12 y=40 enter
gui Wait
label _next__inputvar
delete name=_in
delete name=_inb"""%(elements[0][0])

def TesterVar(vals,elements):
    """Evaluate a variable value
    [varname,valid values in em,jump points in em, fail point]"""
    varname = elements[0]
    indexes_values = elements[1]
    indexes_jump = elements[2]
    fail = elements[3]
    code = "\n"
    keys = indexes_values.keys()
    keys.sort()
    for i in keys:
        valid = indexes_values[i]
        jump = indexes_jump[i]
        code += "is %s = %s line_%s\n"%(varname,valid,jump)
    code += "goto line_%s"%fail
    vals["postcode"] += code
def DefinirVar(vals,elements):
    """Define variable"""
    vals["postcode"] += "\nsetvar %s %s"%(elements[0],elements[1])
def EvaluerCondition(vals,elements):
    """Evalute condition (condition,jump_if_success,jump_if_fail)"""
    condition,succeed,fail = [x[0] for x in elements]
    condition = condition.replace("&amp;","AND")
    vals["postcode"] += "\nis %s line_%s\ngoto line_%s"%(condition,succeed,fail)
    
def do_statement(vals):
    if crossexam[0]:
        vals["precode"] += "\nstatement st_"+vals["id_num"]
        if vals["hidden"]:
            vals["precode"] += " test=aao_st_show_"+vals["id_num"]
        return True

def AllerCI(vals,elements):
    """Start cross exam statement"""
    jumpto_when_press[elements[0]] = vals["id_num"]
    
def pauseCI(vals,elements):
    """Pause cross exam"""
    if crossexam[0]:
        crossexam[0] = None
        vals["postcode"] = u"endcross\n"
    
def RetourCI(vals,elements):
    """Return to cross exam"""
    #vals["postcode"] = "resume"
    vals["postcode"] = "goto "+"line_"+elements[0]

def MasquerMessage(vals,elements):
    """Hide message OR STATEMENT"""
    vals["postcode"] = "set aao_st_show_"+elements[0]+" false"
    vals["postcode"] += "\nset aao_line_hide_%s true"%elements[0]
def AjouterCI(vals,elements):
    """Reveal hidden statement OR LINE"""
    vals["postcode"] = "set aao_st_show_"+elements[0]+" true"
    vals["postcode"] += "\nset aao_line_hide_%s false"%elements[0]
    
def FinDuJeu(vals,elements):
    """Finish the Game"""
    vals["postcode"] = "endscript"

#Investigation
def CreerLieu(vals,elements):
    """Create place, just records the name of somewhere"""
    vals["postcode"] = "label SCENE_NO_%s\n"%elements[0]
    vals["postcode"] += "label SCENE_%s\n"%elements[1]
    vals["postcode"] += "set CURRENT_PLACE SCENE_%s\n"%elements[1]
    vals["postcode"] += "{intro_logic %s %s}"%(elements[0],int(vals["id_num"])+1)
    vals["globals"]["current_place"] = elements[0]
    if elements[2]=="1":
        wp("set scene_hidden_%s true\n"%elements[0])

def DiscussionEnqueteV2(vals,elements):
    """List of discussion topics"""
    #[{0: '8', 1: '11'}, {0: 'Line1', 1: 'Line2'}, {0: '0', 1: '1'}, '', '0']
    #list of sections to jump to when item is selected
    #list of labels for topics
    #list of whether each topic is hidden or not
    #dont know
    #dont know
    topic_jump, topic_label, topic_hide, dn, dn = elements
    vals["postcode"] = "list\n"
    if topic_jump:
        for i in range(max(topic_jump.keys())+1):
            jumpto = topic_jump[i]
            label = topic_label[i]
            hide = topic_hide[i]
            if hide=='1':
                vals["presets"] += "set convo_hidden_%s_%s true\n"%(vals["globals"]["current_place"],i+1)
            vals["postcode"] += "isnot convo_hidden_%s_%s?\n"%(vals["globals"]["current_place"],i+1)
            vals["postcode"] += "li %s result=line_%s\n"%(label,jumpto)
    vals["postcode"] += "showlist\ngoto $CURRENT_PLACE\n"
    
def DevoilerVerrousLieu(vals,elements):
    """Reveal Psyche Locks"""
    vals["postcode"] = '#TAP MODIFY\n"PSYCHE LOCKS REVEAL!"\n'
    vals["postcode"]+="#"+repr(elements)
def LancerVerrous(vals,elements):
    """Launch Psyche Locks"""
    vals["postcode"] = '#TAP MODIFY\n"LAUNCH PSYCHE LOCKS!"\n'
    vals["postcode"]+="#"+repr(elements)
def afficherVerrous(vals,elements):
    """Display psyche locks"""
    vals["postcode"] = '#TAP MODIFY\n"DISPLAY PSYCHE LOCKS!"\n'
    vals["postcode"]+="#"+repr(elements)
def DemanderEltVerrous(vals,elements):
    """Ask locks?"""
    vals["postcode"] = '#TAP MODIFY\n"ASK PSYCHE LOCKS! (dont ask me what that means, google translate is weird)"\n'
    vals["postcode"]+="#"+repr(elements)
def FinVerrous(vals,elements):
    """Finish locks"""
    vals["postcode"] = '#TAP MODIFY\n"FINISH LOCKS"\n'
    vals["postcode"]+="#"+repr(elements)

def DevoilerConversation(vals,elements):
    """Reveal hidden discussion topic"""
    #location id, conversation id
    #basically, set a variable
    #location id and/or conversation id might be expressions
    vals["postcode"] = "set convo_hidden_%s_%s false\n"%(elements[0],elements[1])
def MasquerConversation(vals,elements):
    """Hide discussion topic"""
    #location id, conversation id
    #basically, set a variable
    #location id and/or conversation id might be expressions
    vals["postcode"] = "set convo_hidden_%s_%s true\n"%(elements[0],elements[1])
    
def MasquerIntroLieu(vals,elements):
    """Hide location intro text"""
    vals["postcode"] = "set intro_hidden_%s true\n"%(elements[0])
def DevoilerIntroLieu(vals,elements):
    """Reveal location intro text"""
    vals["postcode"] = "set intro_hidden_%s false\n"%(elements[0])
def MasquerLieu(vals,elements):
    """Hide location"""
    vals["postcode"] = "set scene_hidden_%s true\n"%(elements[0])
def DevoilerLieu(vals,elements):
    """Reveal location"""
    vals["postcode"] = "set scene_hidden_%s false\n"%(elements[0])
    
def SeDeplacer(vals,elements):
    """Show menu to move to another scene"""
    items = ""
    for e in elements:
        scid,scname = e.split("_",1)
        items += "isnot scene_hidden_%s?\nli %s result=SCENE_NO_%s\n"%(scid,scname,scid)
    vals["postcode"] = """
    list
    %(items)s
    showlist
    goto $CURRENT_PLACE
    """%{"items":items}
    

def apply_event(vals,code):
    func = code[0]
    l = []
    for i in sorted(code.keys()):
        if i!=0:
            l.append(code[i])
    if func.strip():
        print "calling",func.strip(),l
        func = eval(func.strip())
        func(vals,l)
def end_cross_exam(vals):
    t = ""
    for id_num in jumpto_when_press.keys():
        t+=u"\nlabel press st_"+jumpto_when_press[id_num]
        t+=u"\ngoto line_%s\n"%id_num
        del jumpto_when_press[id_num]
    for id_num in jumpto_when_present.keys():
        t+=u"\nlabel "+jumpto_when_present[id_num]
        t+=u"\ngoto line_%s\n"%id_num
        del jumpto_when_present[id_num]
    for id_num in label_none.keys():
        t+=u"\nlabel "+label_none[id_num]
        t+=u"\ngoto line_%s\n"%id_num
        del label_none[id_num]
    return t
            
def make_textbox(t):
    print "make textbox of",repr(t)
    #pauses, flashes, shakes, and spaces
    t = textify(BeautifulSoup(t),True)
    t = t.replace("\n","{n}")
    t = t.replace("[#]","{p60}").replace("[#f]","{f}").replace("[#s]","{s}").replace("&nbsp;"," ")
    while 1:
        match = re.search("\[#\d*\]",t)
        if not match:
            break
        found = t[match.start():match.end()]
        t = t[:match.start()]+"{p"+found[2:-1]+"}"+t[match.end():]
    return t
st = u'Those two years...[#30] <span style="color: red;">that trial</span>they\nwere the happiest moments\nof my life but also the saddest.'
en = u'Those two years...{p30} {c900}that trial{c}they{n}were the happiest moments{n}of my life but also the saddest.'
tr = make_textbox(st)
assert tr==en,repr(tr)
    
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

def w(t):
    res.intro.write(t.encode("utf8"))
    res.intro.flush()
def wp(t):
    res.presets.write(t.encode("utf8"))
    res.presets.flush()
w(u"include evidence\ninclude presets")
wp(u"""
macro intro_logic
is intro_hidden_$1 = true?
set aao_line_hide_$2 false
is intro_hidden_$1 = false?
set aao_line_hide_$2 true
set intro_hidden_$1 = x
endmacro

set _textbox_wrap true
set _debug true
""")
had_fg = False
linked = False
globals = {}
for id in sorted(namespace["donnees_messages"].keys()):
    print id
    id_num = str(id)
    vals = {"id_num":id_num,"char":None,"charblink":None,
                "text":"","color":"",
                "nametag":"","bg":None,"fg":None,
                "precode":"",
                "pretextcode":"",
                "postcode":"",
                "presets":"",
                "skip":False,
                "operation":None,
                "hidden":False,
                "linked":False,
                "globals":globals}
    line_attr = namespace["donnees_messages"][id]
    for attr_key in sorted(line_attr.keys()):
        t = line_attr[attr_key]
        if attr_key == "lie_au_suivant":
            vals["linked"] = int(t)
        if attr_key == "defil_auto":
            vals['text_delay'] = int(t)
        if attr_key == 'son':
            vals['mus'] = t
        if attr_key == 'type_son':
            vals['mus_type'] = t
        if attr_key == "texte":
            vals["text"]+=make_textbox(t)
        if attr_key == "couleur":
            vals["color"] = get_color(t)
        if attr_key == 'auteur':
            vals["nametag"]=t.replace(" ","_")
        if attr_key == 'fond' and t:
            if t=="no":
                vals['bg'] = 'black'
            else:
                vals['bg'] = bg(t)
                if not t.endswith(".gif"):
                    vals['fg'] = fg(t.rsplit(".",1)[0]+".gif")
        if attr_key == 'id_auteur':
            vals['char_id'] = t
        if attr_key == 'image_perso':
            if t == "no":
                pass
            elif vals['char_id'] == "-4":
                vals['fg'] = fg(t)
            else:
                vals['char'] = t
        if attr_key == 'image_fixe_perso':
            if t == "no":
                pass
            elif vals['char_id'] == '-4':
                pass
            else:
                vals["charblink"] = t
        if attr_key == 'operation' and t:
            vals["operation"] = t
        if attr_key == 'cache':
            vals["hidden"] = int(t)
    if vals["operation"]:
        apply_event(vals,vals["operation"])
    is_statement = do_statement(vals)
    if vals["hidden"]:
        wp("set aao_line_hide_%s true\n"%id_num)
    if not is_statement:
        vals["precode"] = "is aao_line_hide_%s?\ngoto line_%s\n"%(id_num,int(id_num)+1)+vals["precode"]
    if vals["skip"]:
        vals["postcode"]+="goto line_%s"%(int(id_num)+1)
    #A delay from the beginning of text before continuing
    if "text_delay" in vals and vals["text_delay"]:
        wait_time = cent_to_frame(vals["text_delay"])
        text_length = len(vals["text"])*3
        wait_time = (wait_time-text_length)
        if wait_time>0:
            vals["text"]+="{p%s}"%wait_time
        vals["text"]+="{next}"
    if id_num in label_none or id_num in jumpto_when_press or id_num in jumpto_when_present:
        w(end_cross_exam(vals))
    w(u"\nlabel line_%s\n"%id_num)
    if "mus" in vals and vals['mus']:
        path = {"0":"sfx","1":"music"}[vals['mus_type']]
        mus_name = song(vals['mus'],path)
        if mus_name == -1:
            w(u"\nmus\n")
        elif path=="music":
            w(u"\nmus "+mus_name+"\n")
        elif path=="sfx":
            w(u"\nsfx "+mus_name+"\n")
    if vals["precode"]:
        w(u"\n"+vals["precode"]+"\n")
    if vals["bg"]:
        w(u"\nbg "+vals["bg"])
    if not vals["char"]:
        w(u"\nchar "+vals["nametag"]+u" hide")
    else:
        charname,ename = setupchar(vals["char_id"], vals["nametag"], vals["char"], vals["charblink"])
        w(u"\nchar %s nametag=%s e=%s"%(charname, vals["nametag"], ename))
    if had_fg and not vals["bg"]:
        w(u"\ndelete name=fg")
    had_fg = False
    if vals["fg"]:
        had_fg = True
        w(u"\nfg "+vals["fg"]+u" nowait name=fg")
    if vals["pretextcode"]:
        w(u"\n"+vals["pretextcode"]+u"\n")
    if vals["text"].strip():
        if linked:
            vals["text"] = "{spd0}{$_last_written_text}{spd1}"+vals["text"]
            linked = False
        vals["text"] = vals["color"]+vals["text"]
        if vals["linked"]:
            vals["text"] += "{next}"
            linked = True
        w(u'\n"%s"'%vals["text"])
    if vals["postcode"]:
        w(u"\n"+vals["postcode"]+u"\n")
    if vals["presets"]:
        wp(vals["presets"])
w(u'\nlabel line_%s\nset _speaking NO_ONE\n"THE END"\n'%(int(id_num)+1))

for evid in all_evidence:
    if all_evidence[evid]:
        res.evidence.write(("\naddev %s\n"%evid).encode('utf8'))
        
res.saveall()
res.close()
