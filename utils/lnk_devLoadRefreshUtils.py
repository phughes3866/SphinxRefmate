from os.path import basename
import sys
import sublime
import inspect

pluginName = __package__.split('.')[0]
fileName = basename(__file__)

def _devPrint(msg):
    print(f'{pluginName}: {msg} [from:{fileName}]')

def _clearPluginCache():
    # print('running clear cache')
    if int(sublime.version()) >= 3114:
        frm = inspect.stack()[1]
        callingModuleName = inspect.getmodule(frm[0]).__name__
        # Clear module cache to force reloading all modules of this package.
        # print(f'package = {__package__}, name = {__name__}, caller = {mod.__name__}')
        prefix = __package__ + "."  # don't clear the base package
        sysModules = sys.modules.copy()
        pluginModuleList = [
            module_name
            for module_name in sysModules
            if module_name.startswith(prefix) and module_name != callingModuleName # __name__
        ]
        if len(pluginModuleList) > 1:
            # submodule count will equal 1 if only this present submodule is loaded
            # which means that sublime is starting up so no auto refresh is needed.
            # This assumes that the package has more than this single module to load,
            # and that this single module is loaded first.
            _devPrint('Plugin auto-refresh of submodules on save is running:')
            for module_name in pluginModuleList:
                _devPrint(f' - deleting/refreshing module: {module_name}')
                del sys.modules[module_name]
        else:
            _devPrint(f'Plugin auto-refresh of submodules not running. Initial load detected.')
        prefix = None
    else:
        raise ImportWarning("Doesn't support Sublime Text versions prior to 3114")


def _loadUnloadMessages():
    if int(sublime.version()) >= 3114:

        def plugin_loaded():
            """
            Initialize plugin
            """
            _devPrint('Plugin (re)loaded')
            pass

        def plugin_unloaded():
            """
            Complete tasks.
            Cleanup package caches.
            Exit threads.
            """
            _devPrint('Plugin unloaded')


    else:
        raise ImportWarning("Doesn't support Sublime Text versions prior to 3114")

def devStartupShim():
    _loadUnloadMessages()
    _clearPluginCache()