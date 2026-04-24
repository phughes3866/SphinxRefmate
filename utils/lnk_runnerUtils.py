import os
import sublime
import subprocess
from threading import Thread

import inspect
def debuginfo(message, on=True):
    if on:
        caller = inspect.getframeinfo(inspect.stack()[1][0])
        print(f"{os.path.basename(caller.filename)}:{caller.function}:{caller.lineno} - {message}")

runnerSubprocessArgsGovDict = {
    "description"   : "Arguments for subprocess command",
    "mandKeys"      : ["cmdArgs"], 
    "optKeys"       : [],
    "checks"        : {},
    "defaultValues" : {}
}

# stdin=None, input=None, stdout=None, stderr=None, capture_output=False,
# shell=False, cwd=None, timeout=None, check=False,
# encoding=None, errors=None, text=None, env=None, universal_newlines=None
class subprocessRunner():
    def __init__(self, cmdTokens: list, processArgs):
        self.OK = False
        self.cmdTokens = cmdTokens
        self.processArgs = processArgs
        self.completed_process = None
        self.failStr = ""

    def run(self):
        try:
            self.completed_process = subprocess.run(self.cmdTokens, **self.processArgs)
            self.OK = True
        except subprocess.TimeoutExpired:
            self.failStr = (f'Shell command timed out after {self.processArgs.get("timeout", "excess")} seconds.\n\n'
                             'The timeout can be set in the range 1-600 seconds.')
        except Exception as err:
            self.failStr = ("Shell command failed as an unexpected exception occurred.\n\n"
                              "Details:: {}\n\n{}".format(err.__class__.__name__, err))
        return self.completed_process

# class subprocessRunner():

#     def __init__(self, cmdTokens: list, **processArgs):
#         self.metaOK = False
#         self.processOK = False
#         self.completed_process = None
#         self.processArgs = processArgs
#         # self.processArgs.update(subprocessRunner.captureArgs)
#         self.metaFailStr = ""
#         self.processFailStr = ""
#         try:
#             self.completed_process = subprocess.run(cmdTokens, **self.processArgs)
#             self.metaOK = True
#         except subprocess.TimeoutExpired:
#             self.metaFailStr = (f'The given shell command timed out after {processArgs.get("timeout", "excess")} seconds.\n\n'
#                              'The timeout can be set in the range 1-600 seconds.')
#         except Exception as err:
#             self.metaFailStr = ("Shell command failed as an unexpected exception occurred.\n\n"
#                               "Details:: {}\n\n{}".format(err.__class__.__name__, err))
#         if self.completed_process:
#             self.processOK = self.completed_process.returncode == 0
#             self.processFailStr = self.completed_process.stderr

#     @classmethod
#     def getBinary(cls, cmdTokens: list, **processArgs):
#         captureArgs = {
#             "capture_output"    : True,
#         }
#         processArgs.update(captureArgs)
#         obj = cls(cmdTokens, **processArgs)
#         return obj

#     @classmethod
#     def getText(cls, cmdTokens: list, **processArgs):
#         captureArgs = {
#             "capture_output"    : True,
#             "text"              : True
#         }
#         processArgs.update(captureArgs)
#         obj = cls(cmdTokens, **processArgs)
#         return obj

#     def allOK(self):
#         return self.metaOK and self.processOK


class shellCommandThreadObj(Thread):
    """
    Run a shell command as a threaded subprocess, according to parameters given in 'passedArgs'
    Distinguish between two types of command, dependent on whether a target 'view' is passed to __init__:
    `- A text command, whose output we are interested in capturing and putting somewhere e.g. a new tab
     - A simple spawned command, which we can simply run and leave
    Captured text from text commands is output to the given destination(s) 
    If an error/exception occurs then an error msg is stored in an object attribute (self.errStr) which is
    `- also output by a thread manager (in a sublime message_dialog box) on thread completion.
    """
    def __init__(self, cmdTokens: list, callback=None, processArgs={}):
        super(shellCommandThreadObj, self).__init__()
        self.cmdTokens = cmdTokens
        self.callback = callback
        self.process_args = processArgs
        self.completed_process = None
        self.failStr = ""

    def run(self):
        # print("Running shell command NOW:")
        runObj = subprocessRunner(self.cmdTokens, self.process_args)
        self.completed_process = runObj.run()
        self.OK = runObj.OK
        self.failStr = runObj.failStr
        if self.callback is not None:
            self.callback.process_args = self.process_args
            self.callback.completed_process = self.completed_process
            self.callback.OK = self.OK
            self.callback.failStr = self.failStr
            self.callback.set()



class livingThreadStatusAnimator():

    """
    Animates an indicator, [=   ], in the status area while a thread runs
    :param thread:
        The thread to track for activity
    :param message:
        The message to display next to the activity indicator
    :param success_message:
        The message to display once the thread is complete
    """
    __objectIncremental = 1

    def __init__(self, thread, message, success_message=None):
        self.thread = thread
        self.message = message
        if success_message:
            self.success_message = success_message
        else:
            self.success_message = f'{message} [=DONE=]'
        self.objID = f'_threadAnimator{livingThreadStatusAnimator.__objectIncremental}'
        livingThreadStatusAnimator.__objectIncremental += 1
        self.incrementOrDecrement = 1
        self.size = 8
        self.spaceToken = 0
        self.last_view = None
        self.window = None
        # execute self.run asynchronously in 100ms (tenth of a second)
        # `- this is the animation step time for [=     ] to move to [ =   ]
        #  - this same timeout call will be set at the end of each self.run
        sublime.set_timeout(lambda: self.spaceShift(), 100)

    def spaceShift(self):
        # debuginfo(f'spaceToken = {self.spaceToken}')
        if self.window is None:
            self.window = sublime.active_window()
        active_view = self.window.active_view()

        if self.last_view is not None and active_view != self.last_view:
            # the active view has changed since last self.spaceShift e.g. user viewing another file
            # `- be tidy and erase the status message associated with the previous view
            self.last_view.erase_status(self.objID)
            self.last_view = None

        if not self.thread.is_alive():
            def cleanup():
                active_view.erase_status(self.objID)
            # if hasattr(self.thread, 'textOut') and self.thread.textOut is None:
            # if self.thread.textOut is None:
            # if not self.thread.commandSuccess:
            #     cleanup()
            #     if self.thread.errStr is not None:
            #         print(self.thread.errStr)
            #     return
            active_view.set_status(self.objID, self.success_message)
            # if self.thread.outputMsgBox is not None:
                # sublime.message_dialog(self.thread.outputMsgBox)
            sublime.set_timeout(cleanup, 1000)
            return

        self.beforeCount = self.spaceToken % self.size  # cycles 0,1,2,3..self.size-1,0,1,2,3..self.size-1
        self.afterCount = (self.size - 1) - self.beforeCount
        self.beforeSpaces = ' ' * self.beforeCount
        self.afterSpaces = ' ' * self.afterCount
        active_view.set_status(self.objID, f'{self.message} [{self.beforeSpaces}={self.afterSpaces}]')

        if self.last_view is None:
            self.last_view = active_view

        if not self.afterCount:
            # triggered when animation reaches its rightmost point, initiates countdown
            self.incrementOrDecrement = -1
        if not self.beforeCount:
            # triggered when animation reaches its leftmost point, initiates countup
            self.incrementOrDecrement = 1
        self.spaceToken += self.incrementOrDecrement
        
        # set animation to step in 100ms
        sublime.set_timeout(lambda: self.spaceShift(), 100)
