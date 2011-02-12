import os
import sys
import subprocess

WIN_REG = {"gifsicle":"TOOLS:gifsicle_1.60_windows\\bin\\gifsicle.exe",
    "mpg123":"TOOLS:mp3ogg\\mpg123.exe",
    "oggenc2":"TOOLS:mp3ogg\\oggenc2.exe"
}
LINUX_REG = {"gifsicle":"gifsicle",
    "mpg123":"mpg123",
    "oggenc2":"oggenc"
}

DIR = os.path.split(os.path.abspath(__file__))[0]
def get_registry():
    reg = LINUX_REG
    if "win" in sys.platform:
        reg = WIN_REG
    tool_config = os.path.join(DIR,"tools.ini")
    if os.path.exists(tool_config):
        f = open(tool_config)
        for comm in f.read().split("\n"):
            try:
                command,path = [x.strip() for x in comm.split("=")]
                reg[command] = path
            except Exception:
                pass
        f.close()
    f = open(tool_config,"w")
    for k in reg:
        f.write("%s = %s\n"%(k,reg[k]))
    f.close()
    return reg

operations = {
"gifsicle_explode": '%(command)s --no-background -U -e "%(path)s" -o "%(path)s"',
"gifsicle_info": '%(command)s -I "%(path)s"',
"mpg123_towav": '%(command)s -w "%(output)s" "%(input)s"',
"oggenc2_toogg": '%(command)s "%(input)s" -o "%(output)s" --resample=44100'
}

class ExternalProgramRunner:
    def __init__(self,paths={"TOOLS":DIR}):
        """Register applications"""
        self.commands = get_registry()
        self.paths = paths

        #Don't use shell on windows
        self.use_shell = True
        if "win" in sys.platform:
            self.use_shell = False

    def run(self, d):
        print d,d["command"],self.commands[d["command"]]
        command = d["command"]
        d["command"] = self.make_command(command)
        operation = operations["%s_%s"%(command,d["operation"])]
        sh = operation%d
        sh.replace("/",os.path.sep)
        print sh
        proc = subprocess.Popen(sh,stdout=subprocess.PIPE,shell=self.use_shell)
        return proc.communicate()
        
    def make_command(self, command):
        path = self.commands[command]
        if ":" in path:
            root,path = path.split(":",1)
            root = self.paths[root]
            path = os.path.join(root,path)
        return path

runner = ExternalProgramRunner()

if __name__=="__main__":
    print runner.run(eval(sys.argv[1]))
