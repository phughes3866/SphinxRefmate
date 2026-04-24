from .lnk_loggingUtils import getLogger; logger = getLogger(debug=True)
import sublime
import subprocess
import inspect
import os
# from pathlib import Path
# from datetime import datetime

def debuginfo(message, stepsBack=1):
    caller = inspect.getframeinfo(inspect.stack()[stepsBack][0])
    print(f"{os.path.basename(caller.filename)}:{caller.function}:{caller.lineno} - {message}")

def exceptionDetails(eObj: Exception, delimiter=": "):
    # carriageReturns = ["\n\n", " "][oneLine]
    return f'{eObj.__class__.__name__}{delimiter}{str(eObj)}'

class MessageOutputUtils():
    """
    Pre-mixin class for sublime text's windowCommand and textCommand classes
    """

    def __init__(self, *args, **kwargs):
        if not hasattr(self, "pluginName"):
            self.pluginName = __package__.split('.')[0]
        if not hasattr(self, "commandName"):
            if self.__class__.__name__.endswith("Command"):
                self.commandName = self.__class__.__name__[:-7]
            else:
                self.commandName = self.__class__.__name__
        # print(f'MessageOutputUtils init: pluginName = {self.pluginName}')
        self.dBugForce = self.dBugF
        super(MessageOutputUtils, self).__init__(*args, **kwargs)

    def _msgBoxTitle(self, oneLine=False):
        if oneLine:
            return f"{self.pluginName}:[{self.commandName}] "
        else:
            return f"{self.pluginName} (Sublime Text Plugin):\n[Command: {self.commandName}]\n\n"

    def msgBox(self, msg: str):
        sublime.message_dialog(f'{self._msgBoxTitle()}{msg}')

    def ok_cancel_dialog(self, msg: str):
        return sublime.ok_cancel_dialog(f'{self._msgBoxTitle()}{msg}')

    def status_message(self, msg: str):
        sublime.status_message(f'{self._msgBoxTitle(oneLine=True)}{msg}')

    def console_message(self, msg: str):
        print(f'{self._msgBoxTitle(oneLine=True)}{msg}')

    def error_message(self, msg):
        # same appearance as message_dialog but additionally writes output to console
        sublime.error_message(f'{self._msgBoxTitle()}{msg}')

    def dBug(self, msg, Force=False):
        if hasattr(self, "doDebug"):
            if self.doDebug:
                debuginfo(msg, stepsBack=2)

    def dBugF(self, msg):
            debuginfo(msg, stepsBack=2)

    # def debugOn(self):
    #     self.doDebug = True

    # def debugOff(self):
    #     self.doDebug = False

    def setDebugMode(self, status: bool):
        self.doDebug = status

    def getDebugMode(self):
        if not hasattr(self, "doDebug"):
            self.doDebug = False 
        return self.doDebug

class DebugReport():
    """
    """

    def __init__(self, debugActive=False, prefixStr='- '):
        self._debugActive = debugActive
        self._prefixStr = prefixStr
        self._reportLines = []
        self.prefixLen = len(prefixStr)

    def __call__(self, *args, **kwargs):
        self.addLine(*args, **kwargs)

    def _prepAndPrefix(self, strToPrepAndPrefix, insertInitPrefix=True):
        if insertInitPrefix:
            strToPrepAndPrefix = self._prefixStr + strToPrepAndPrefix
        return strToPrepAndPrefix.replace("\n", f"\n{self._prefixStr}")

    def addLine(self, theLine=""):
        self._reportLines += [theLine]

    def printRep(self, titleStr="", footerStr="", forcePrint=False):
        if self._debugActive or forcePrint:
            if titleStr:
                self._reportLines.insert(0, self._prepAndPrefix(titleStr))
            if footerStr:
                self._reportLines += [ self._prepAndPrefix(footerStr, insertInitPrefix=False) ]
            # print(self._reportLines)
            if self._reportLines:
                if not titleStr and not footerStr:
                    self._reportLines[0] = self._prepAndPrefix(self._reportLines[0])
                fullReport = f'\n{self._prefixStr}'.join(self._reportLines)
                print(fullReport)


def openSublimeTextInstance(*args):
    """
    Open an instance of sublime text as if '*args' were passed on the command line
    e.g. openSublimeTextInstance('-n', '/home/paul') will open a new instance with /home/paul as the TLD
    """
    executable_path = sublime.executable_path()
    # as I am targeting only linux, the following osx adjustment is not required
    # if sublime.platform() == 'osx':
    #     app_path = executable_path[:executable_path.rfind('.app/') + 5]
    #     executable_path = app_path + 'Contents/SharedSupport/bin/subl'
    subprocess.Popen([executable_path] + list(args))

def amInSublProject(windowObj):
    status = ""
    try:
        answer = bool(windowObj.extract_variables().get('project_name'))
        if answer:
            status = "Currently working within a sublime.project"
    except Exception as e:
        status = f'Error determining if we are in a sublime.project {str(e)[:20]}'
        answer = False
    return answer, status

def dictHone(td: dict, template: dict, keysOnly=False, exclusive=True):
    """
    conforms a target dict (td) to a given template dict according to the following algorithm
    1. if 'exclusive' flag is True (default) then all key/value pairs in td,
       which have no corresponding key in the template, are removed.
    2. key/value pairs which are in the template, but not in td, are then inserted as follows:
       `- if 'keysOnly'==True (default) then just the key is inserted, with a None value
        - if 'keysOnly'==False then the key/value combination is inserted
    The 'honed' dictionary (new dict = nd) is returned
    """
    if exclusive:
        # remove spurious keys
        nd = { k: v for k, v in td.items() if k in template }
    else:
        nd = td 
    for k, v in template.items():
        if not k in nd:
            # add missing key to nd from template
            if keysOnly:
                nd[k] = None
            else:
                nd[k] = v
    return nd

