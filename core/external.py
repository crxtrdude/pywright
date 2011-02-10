import os
import sys
import subprocess

operations = {
"gifsicle_explode": '%(command)s --no-background -U -e "%(path)s" -o "%(path)s"',
"gifsicle_info": '%(command)s -I "%(path)s"',
"mpg123_towav": '%(command)s -w "%(output)s" "%(input)s"',
"oggenc2_toogg": '%(command)s "%(input)s" -o "%(output)s" --resample=44100'
}

class ExternalProgramRunner:
    def __init__(self):
        """Register applications"""
        self.commands = {}

        #Don't use shell on windows
        self.use_shell = True
        if "win" in sys.platform:
            self.use_shell = False

    def run(self, d):
        print d,d["command"],self.commands[d["command"]]
        command = d["command"]
        d["command"] = self.commands[command]
        operation = operations["%s_%s"%(command,d["operation"])]
        sh = operation%d
        sh.replace("/",os.path.sep)
        print sh
        proc = subprocess.Popen(sh,stdout=subprocess.PIPE,shell=self.use_shell)
        return proc.communicate()

def run(d):
    pr = ExternalProgramRunner()
    pr.commands["gifsicle"] = "gifsicle"
    pr.commands["mpg123"] = "mpg123"
    pr.commands["oggenc2"] = "oggenc"
    return pr.run(d)

if __name__=="__main__":
    run(eval(sys.argv[1]))
