import pythonlzw
import pygame

class gif_d:
    def __repr__(self):
        nd = {}
        nd.update(self.__dict__)
        if "colors" in nd:
            del nd["colors"]
        return str(nd)
        
def pbin(n):
    n = bin(n)[2:]
    return ("00000000"+n)[-8:]
assert pbin(4)=="00000100",pbin(4)

def get_gifhead(f):
    head = f.read(6)
    return head
def read_int(f,length):
    s = 0
    for i in range(length):
        s+=ord(f.read(1))
    return s
def unpack_color(f):
    d = gif_d()
    color_pack = pbin(ord(f.read(1)))
    d.gct = int(color_pack[0])
    d.cres = int(color_pack[1:4],2)+1
    d.csort = int(color_pack[4])
    d.gctsize = 2**(int(color_pack[5:],2)+1)
    return d
def get_screen(f,d):
    d.width = read_int(f,2)
    d.height = read_int(f,2)
    d.color_fmt = unpack_color(f)
    d.bg_color = read_int(f,1)
    d.aspect = read_int(f,1)
    d.pixel_aspect = 1
    if d.aspect:
        d.pixel_aspect = d.aspect*64-15
def get_colors(f,d):
    d.colors = []
    for i in range(d.color_fmt.gctsize):
        r=read_int(f,1)
        g=read_int(f,1)
        b=read_int(f,1)
        d.colors.append((r,g,b))
def get_anim_ext(f,d):
    app_block_len = read_int(f,1)
    app_block = f.read(app_block_len)
    app_sub_len = read_int(f,1)
    app_sub = f.read(app_sub_len)
    term = f.read(1)
    if app_block == "NETSCAPE2.0":
        d.loops = ord(app_sub[1])+ord(app_sub[2])
        print app_block,repr(app_sub),repr(term)
disposals = ["undefined","leave","restorecolor","restoreimage",0,0,0,0]
def unpack_gce(f):
    packed = pbin(ord(f.read(1)))
    print repr(packed)
    reserved = packed[:3]
    disposal = disposals[int(packed[3:6],2)]
    user = int(packed[6],2)
    transp_flag = int(packed[7],2)
    return disposal,user,transp_flag
def get_graphic_control_ext(f,d):
    print "getting graphic control"
    d = gif_d()
    block_size = read_int(f,1)
    d.disposal,d.userinput,d.transpflag = unpack_gce(f)
    d.delay = read_int(f,2)
    d.transp_index = read_int(f,1)
    term = f.read(1)
    return d
def unpack_image(f,d):
    packed = pbin(ord(f.read(1)))
    d.lct = int(packed[0],2)
    d.interlace = int(packed[1],2)
    d.sort = int(packed[2],2)
    d.reserved = int(packed[3:4],2)
    d.lct_size = 0
    if d.lct:
        d.lct_size = 2**(int(packed[4:],2)+1)
def get_lct(f,image):
    image.colors = []
    for i in range(image.lct_size):
        r=read_int(f,1)
        g=read_int(f,1)
        b=read_int(f,1)
        image.colors.append((r,g,b))
def init_table(code_size,char_size):
    """code_size - bits per code, maximum length of string_table
    char_size - how many bits for a character (ie, 256 for ascii)"""
    string_table = []
    for i in range(char_size):
        string_table.append([i])
    string_table.append("CLEAR")
    string_table.append("END")
    return string_table
def decompress(f,d):
    npages=d.lzw_min_code
    print "npage",npages,d.color_fmt.cres
    code_size=(npages+1)
    char_size=(2**(npages))
    print "decomp",npages,char_size,code_size
    string_table = init_table(code_size,char_size)
    code = None
    lastcode = None
    charstream = []
    prefix = []
    cstr = ""
    codestream = []
    lastbits = ""
    finished = 0
    while 1:
        amt = ord(f.read(1))
        if not amt:
            print "finished",code_size
            return charstream
            break
        chunk = f.read(amt)
        #~ unpacker = pythonlzw.BitUnpacker(code_size-1)
        #~ charstream.extend(unpacker.unpack(chunk))
        #~ continue
        p = ""
        #print "charstream:",len(charstream)
        #print len(chunk)
        for byte in chunk:
            p+=pbin(ord(byte))
        #for i in range(len(p)//code_size):
        #    print p[i*code_size:i*code_size+code_size]
        for byte in chunk:
            #print "byte",pbin(ord(byte)),code_size#,charstream
            bits = pbin(ord(byte))+lastbits
            if len(bits)<code_size:
                lastbits = bits
                continue
            #print "bits",bits
            bits,lastbits = bits[-code_size:],bits[:-code_size]
            code = int(bits,2)
            #print bits,code,lastcode
            if code==char_size+1:
                print "end"
                return charstream
            elif code==char_size:
                #print "clear"
                code_size=(npages+1)
                string_table = init_table(code_size,char_size)
                continue
            if code<len(string_table):
                charstream.extend(string_table[code])
                if lastcode:
                    #print len(string_table),lastcode
                    try:
                        prefix = string_table[lastcode]
                    except:
                        return charstream
                    cstr = string_table[code][0]
                    #print "cstr",cstr
                    string_table.append(prefix+[cstr])
                    if code_size<12 and len(string_table)==(2**code_size):
                        code_size+=1
            else:
                prefix = string_table[lastcode]
                cstr = prefix+[prefix[0]]
                charstream.extend(cstr)
                while code>=len(string_table):
                    string_table.append(cstr)
                if code_size<12 and len(string_table)==(2**code_size):
                    code_size+=1
            lastcode = code
            #print string_table
def get_image(f,d,frame):
    image = gif_d()
    if getattr(d,"next_control",None):
        image.control = d.next_control
        d.next_control = None
    image.left = read_int(f,2)
    image.top = read_int(f,2)
    image.width = read_int(f,2)
    image.height = read_int(f,2)
    unpack_image(f,image)
    if image.lct:
        get_lct(f,image)
    d.lzw_min_code = read_int(f,1)
    raster = decompress(f,d)
    print len(raster)
    surf = pygame.Surface([image.width,image.height])
    x=image.left
    y=image.top
    for c in raster:
        if c>=len(d.colors):
            col = [255,0,255]
        else:
            col = d.colors[c]
        surf.set_at([x,y],col)
        x+=1
        if x>=image.left+image.width:
            y+=1
            x=0
    pygame.image.save(surf,"%s.png"%frame)
    term = read_int(f,1)
    #~ assert term==0
    return image
def get_images(f,d):
    next = f.read(1)
    if not len(next):
        return True
    control = ord(next)
    print "control",control
    if control == 0x2C:
        d.frames.append(get_image(f,d,len(d.frames)))
        #return True
    elif control == 0x21:
        app_ext_lab = read_int(f,1)
        if app_ext_lab == 255:
            get_anim_ext(f,d)
        elif app_ext_lab == 0xF9:
            d.next_control = get_graphic_control_ext(f,d)
    else:
        while control != 0:
            control = ord(f.read(1))

def load_gif(path):
    d = gif_d()
    d.frames = []
    f = open(path,"rb")
    if get_gifhead(f)!="GIF89a":
        return "not a gif file"
    get_screen(f,d)
    get_colors(f,d)
    while 1:
        if get_images(f,d):
            break
    print d

print load_gif("earth.gif")