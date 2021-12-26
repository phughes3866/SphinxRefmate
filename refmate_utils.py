import os
import ast
import sublime
import sublime_plugin

plugin_settings_file = 'SphinxRefmate.sublime-settings'
plugin_canon_name = 'SphinxRefmate'


class ContextuallyVisibleParentMenuItemCommand(sublime_plugin.TextCommand):
    """
    A wrapper to be used for parent menus (command-less) to make them visible only in certain scopes/contexts.
    The class overrides the 'is_visible' method so it returns True only when the current scope matches the target scope
    """
    def run(self, edit, **kwargs):
        pass

    def is_visible(self, **kwargs):
        refmate_settings = sublime.load_settings(plugin_settings_file)
        proj_plugin_settings = sublime.active_window().active_view().settings().get(plugin_canon_name, {})
        # any SphinxRefmate settings in the .sublime-project file will override same name Default/User settings
        refmate_settings.update(proj_plugin_settings)
        if refmate_settings.get('rst_check'):
            contextOK = self.view.match_selector(self.view.sel()[0].begin(), "text.restructuredtext")
        else:
            contextOK = True
        return refmate_settings.get('enable_context_menu', False) and contextOK


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
    except Exception as err:
        print("Exception opening or ast parsing [{}]: "
            "{}: {}".format(pyfile, err.__class__.__name__, err))
        return None
    else:
        return ret_list


def showRefMateError(errormsg):
    sublime.error_message("{} plugin error::\n\n{}".format(plugin_canon_name, errormsg))
