import os
import ast
import sublime
import sublime_plugin
from .constants import pluginEnv


def sphinx_and_rst_checks(proj_folder, currentScope, refmate_settings):
    """
    Checks that:
    a) We're in a sphinx docs project (proj_folder has a conf.py file)
    b) We're in a restructured text context/scope (according to currentScope)
    Returns True if both tests pass (or are overridden in refmate_settings)
    Displays error message if either test fails, then returns False
    """
    referStr = "(Note: It is possible to override this check in the plugin settings.)"
    if refmate_settings.get('sphinx_check', True):
        if not os.access(os.path.join(proj_folder, 'conf.py'), os.R_OK):
            showRefMateError('Failed to run because you are not working within a sphinx docs project '
                '(no readable conf.py found at project root: {})\n\n{}\n'.format(proj_folder, referStr))
            return False
    if refmate_settings.get('rst_check', True):
        if "text.restructuredtext" not in currentScope:
            showRefMateError('Failed to run because you are not operating in a text.restructuredtext scope. '
                '(Current scope = {})\n\n{}\n'.format(currentScope, referStr))
            return False
    return True


def parse_pyfile_for_ast_types(pyfile, ast_type_list=[ast.Assign]):
    ret_list = []
    try:
        # print('trying to open {}'.format(config_file))
        with open(pyfile) as f:
            node_tree = ast.parse(f.read())
        ret_list = [x for x in node_tree.body if type(x) in ast_type_list]
    except Exception as xcept:
        print("Exception opening or ast parsing [{}]: "
            "{}: {}".format(pyfile, xcept.__class__.__name__, xcept))
        return None
    else:
        return ret_list


# def showRefMateError(errormsg):
#     sublime.error_message("{} plugin error::\n\n{}".format(pluginName, errormsg))

# def stripUnknownSettings(userSettings, areGlobal=True):
#     nonSectionSettings = [globalOnlySettings, projectOnlySettings][areGlobal is True]
#     print(f'global={areGlobal} - nonSectionSettings={nonSectionSettings}')
#     # parseA: Weedle out non-section variables e.g. defined in project but meant for globals (and vice versa)
#     parseASettings = {k: v for k, v in userSettings.items() if k not in nonSectionSettings}
#     # parseB: Weedle out completely wrong-named variables
#     parseBSettings = {k: v for k, v in parseASettings.items() if k in allPluginSettingsKey}
#     if len(parseBSettings) < len(userSettings):
#         print(f'parseB: {parseBSettings}')
#         print(f'userSettings: {userSettings}')
#         # some trimming was done
#         trimmed = {k for k in userSettings.keys() if k not in parseBSettings}
#         print(f'trimmed: {trimmed}')
#         misplacedVars = []
#         bogusVars = []
#         for k in trimmed:
#             misplacedVars.append(k) if k in allPluginSettingsKey else bogusVars.append(k)
#         errorRep = 'Error found in plugin settings:'
#         if misplacedVars:
#             usualContext = ["a project's .sublime-project", "the plugin's .sublime-settings"][areGlobal is True]
#             misplacedContext = ["the plugin's .sublime-settings", "the project's .sublime-project"][areGlobal is True]
#             misplacedMsg = f'\n\nThe following settings were found in {misplacedContext} file. The correct location is in {usualContext} file::\n\n{misplacedVars}'
#             errorRep += misplacedMsg
#         if bogusVars:
#             errorRep += f"\n\nThe following unrecognised settings were found {bogusVars}"
#         errorRep += '\n\nPlease check and adjust your settings file(s).'
#         error_message(errorRep)
#         return None
#     else:
#         return parseBSettings

# def get_active_plugin_settings():
#     setts = sublime.load_settings(pluginSettingsFile).to_dict()
#     print(f'setts = {setts}')
#     my_plugin_global_settings = stripUnknownSettings(setts, areGlobal=True)
#     if my_plugin_global_settings is None: return None # something was wrong with the global settings names/location
#     my_tested_global_settings = validateSettings(my_plugin_global_settings)
#     if my_tested_global_settings is None: return None # something was wrong with the global settings values

#     rawProjectSettings = sublime.active_window().active_view().settings().get(pluginName, {})
#     if rawProjectSettings:
#         cur_proj_plugin_overrides = stripUnknownSettings(rawProjectSettings, areGlobal=False)
#         if cur_proj_plugin_overrides is None: return None
#     # if cur_proj_plugin_overrides:
#         # Deal with special cases i.e. global settings that are not simply overridden by project equivalents

#         # 1: more conf.py files for rstEpilog parsing
#     # any current project settings in the .sublime-project file will override same name 
#     # `- settings in the plugin's Default/User .sublime-settings files
#     active_settings = dict(my_plugin_global_settings, **cur_proj_plugin_overrides)
#     return active_settings
