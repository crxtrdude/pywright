charstream = ""   #contains characters
codestream = ""    #contains codes
string_table = {}  #maps codes to strings of characters

def init_table(code_size,char_size):
    """code_size - bits per code, maximum length of string_table
    char_size - how many bits for a character (ie, 256 for ascii)"""
    string_table = []
    for i in range(char_size):
        string_table.append(chr(i))
    return string_table

def get_code(string_table,c):
    code = None
    for i,v in enumerate(string_table):
        if v==c:
            code = i
            break
    return code
#Input: charstream  Output: codestream
def compress(charstream,code_size,char_size):
    codestream = []    #contains codes
    string_table = init_table(code_size,char_size)
    prefix = ""
    cstr = ""
    for c in charstream:
        cstr = prefix+c
        code = get_code(string_table,cstr)
        if code:
            prefix = cstr
        else:
            string_table.append(cstr)
            codestream.append(get_code(string_table,prefix))
            prefix = c
    codestream.append(get_code(string_table,prefix))
    return codestream,string_table
def decompress(codestream,code_size,char_size):
    string_table = init_table(code_size,char_size)
    code = None
    lastcode = None
    charstream = ""
    prefix = ""
    cstr = ""
    for code in codestream:
        if code<len(string_table):
            charstream+=string_table[code]
            if lastcode:
                prefix = string_table[lastcode]
                cstr = string_table[code][0]
                string_table.append(prefix+cstr)
        else:
            prefix = string_table[lastcode]
            cstr = prefix[0]
            cstr = prefix+cstr
            charstream += cstr
            string_table.append(cstr)
        lastcode = code
    
if __name__=="__main__":
    print compress("ABACABA",12,256)
    print decompress([65, 66, 65, 67, 256, 65],12,256)