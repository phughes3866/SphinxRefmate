import ast
import os, sys, re, zlib
import sublime, sublime_plugin
from collections import defaultdict

# sphinx_swift_settings_file_variables = ["command_path", "extra_sphinx_conf_files", "intersphinx_map_file", "bib_ref_file"]
plugin_settings_file = 'sphinx-refmate.sublime-settings'
#*************************************************
#
# file manipulation utilities
#
#*************************************************

class ContextuallyVisibleCommandMenuItemCommand(sublime_plugin.TextCommand):
    """
    A wrapper to be used for menu commands to make them visible only in certain scopes/contexts.
    The class overrides the 'is_visible' method so it returns True only when the current scope matches the target scope
    """
    def run(self, edit, command_name, scope_selector, **kwargs):
        self.view.run_command(command_name, kwargs)

    def is_visible(self, command_name, scope_selector, **kwargs):
        return self.view.match_selector(self.view.sel()[0].begin(), scope_selector)

class ContextuallyVisibleParentMenuItemCommand(sublime_plugin.TextCommand):
    """
    A wrapper to be used for parent menus (command-less) to make them visible only in certain scopes/contexts.
    The class overrides the 'is_visible' method so it returns True only when the current scope matches the target scope
    """
    def run(self, edit, scope_selector, **kwargs):
        pass

    def is_visible(self, scope_selector, **kwargs):
        return self.view.match_selector(self.view.sel()[0].begin(), scope_selector)

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
        if not "text.restructuredtext" in currentScope:
            showRefMateError('Failed to run because you are not operating in a text.restructuredtext scope. '
                '(Current scope = {})\n\n{}\n'.format(currentScope, referStr))
            return False
    return True


# def which(program):
#     def is_exe(fpath):
#         return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

#     fpath, fname = os.path.split(program)
#     if fpath: # program's location has been specified
#         if is_exe(program):
#             return program
#     else: # program's location not given
#         for path in os.environ["PATH"].split(os.pathsep):
#             exe_file = os.path.join(path, program)
#             if is_exe(exe_file):
#                 return exe_file

#     return None

def parse_pyfile_for_ast_types(pyfile, ast_type_list=[ast.Assign]):
    ret_list = []
    try:
        # print('trying to open {}'.format(config_file))
        with open(pyfile) as f:
            node_tree = ast.parse(f.read())
        ret_list = [x for x in node_tree.body if type(x) in ast_type_list]
    except:
        return None
    else:
        return ret_list

def showRefMateError(errormsg):
    sublime.error_message("sphinx-refmate plugin error::\n\n{}".format(errormsg))

# def get_intersphinx_map_from_config_file(config_file):
#     found_map = {}
#     ast_assigns = parse_pyfile_for_ast_types(config_file, [ast.Assign])
#     if ast_assigns:
#         # print('no. of assigns = {}'.format(len(ast_assigns)))
#         for x in ast_assigns:
#             # print('name = {}'.format(x.targets[0].id))
#             if x.targets[0].id == 'intersphinx_mapping':
#                 try:
#                     found_map = eval(compile(ast.Expression(x.value), "<ast expression", "eval"))
#                 except:
#                     return None
#                 else:
#                     return found_map


    # ModuleType = type(ast)
    # with open(mod_path, "r", encoding='UTF-8') as file_mod:
    #     data = file_mod.read()

    # try:
    #     ast_data = ast.parse(data, filename=mod_path)
    # except:
    #     if raise_exception:
    #         raise
    #     print("Syntax error 'ast.parse' can't read %r" % mod_path)
    #     import traceback
    #     traceback.print_exc()
    #     ast_data = None

    # if ast_data:
    #     for body in ast_data.body:
    #         if body.__class__ == ast.Assign:
    #             if len(body.targets) == 1:
    #                 if getattr(body.targets[0], "id", "") == variable:
    #                     try:
    #                         return ast.literal_eval(body.value)
    #                     except:
    #                         if raise_exception:
    #                             raise
    #                         print("AST error parsing %r for %r" % (variable, mod_path))
    #                         import traceback
    #                         traceback.print_exc()
    # return default


# Example use, read from ourself :)
# that_variable = safe_eval_var_from_file(__file__, "this_variable")
# this_variable = {"Hello": 1.5, b'World': [1, 2, 3], "this is": {'a set'}}
# assert(this_variable == that_variable)

#*************************************************
#
# sublime text interaction utilities
#
#*************************************************

# class InsertMyText(sublime_plugin.TextCommand):
#     def run(self, edit, args):
#         # inserts args['text'] at current cursor position
#         # https://forum.sublimetext.com/t/chage-hello-world-to-insert-at-cursor-position/9270/1
#         self.view.insert(edit, self.view.sel()[0].begin(), args['text'])

#*************************************************
#
# Utilities for project and plugin settings loading
#
#*************************************************

# def get_project_settings(for_this_plugin):
#     proj_data = sublime.active_window().project_data()
#     if not proj_data:
#         return {}
#     try:
#         proj_setts = proj_data['settings'][for_this_plugin]
#         return proj_setts
#     except KeyError:
#         return {}

# def get_plugin_settings(this_plugin_settings_file, these_settings, loc_proj_overrides=False):
#     """
#     Return a dictionary of settings from the .sublime-settings filename passed in this_plugin_settings_file
#     The settings returned are those that match the 'these_settings' list of varnames
#     If loc_proj_overrides is True then a subsequent check for matching varname settings is done in the active sublime project file
#     The section of the sublime project file consulted is ["settings"]["plugin_name"] where plugin_name is this_plugin_settings_file minus the .sublime-settings extension
#     """
#     end_dict = {}
#     settings = sublime.load_settings(this_plugin_settings_file)
#     for varname in these_settings:
#         end_dict[varname] = settings.get(varname)
#     if loc_proj_overrides:
#         plugin_name = this_plugin_settings_file[0:this_plugin_settings_file.find('.')]
#         proj_settings = get_project_settings(plugin_name)
#         if proj_settings:
#             for proj_varname in these_settings:
#                 proj_varvalue = proj_settings.get(proj_varname, None) 
#                 if not proj_varvalue is None:
#                     # print("updating {}".format(proj_varname))
#                     end_dict[varname] = proj_varvalue
#     return end_dict


#*******************************************************************
#
# Various reST parsing utilities
#
#*******************************************************************



# def get_variables(node):
#     variables = set()
#     var_dict = {}
#     if hasattr(node, 'body'):
#         for subnode in node.body:
#             variables |= get_variables(subnode)
#     elif isinstance(node, _ast.Assign):
#         for name in node.targets:
#             if isinstance(name, _ast.Name):
#                 variables.add(name.id)
#     return variables

# def get_rst_epilog(filename):
#         # \s*rst_epilog\s+=\s+\"\"\"     # rst_epilog var start
#         # (?P<stuff>.*)                  # contents
#         # \"\"\"                         # end of docstring var
#     print('epilog searching file {}'.format(filename))
#     pattern = re.compile(r"""
#         ^rst_epilog\s+[\+=]+\s+\"\"\"     # rst_epilog var start
#         (?P<stuff>.*?)\"\"\"
#         """, re.VERBOSE | re.MULTILINE | re.DOTALL)
#     with open(filename, 'r') as ifile:
#         # Read file object to string
#         text = ifile.read()
#     # for match in pattern.finditer(text):
#     #     return match.group(1)
#     found = re.search(pattern, text)
#     print('file {}, found: {}'.format(filename, found))
#     if found:
#         return found.group('stuff')
#     return None



#****************************************************************************
#
# The following utilities perform queries / manipulation on the intersphinx_mapping dictionary
#
#****************************************************************************

# def get_intersphinx_mapping():
#     """
#     Finds the file in which intersphinx_mapping is defined (same one as used by intersphinx itself)
#     imports this file as a module and then returns the resultant intersphinx_mapping dictionary
#     !!! can't we just find 'conf.py' in the project's base directory, parse it to find [intersphinx_map_file] ???
#     """
#     settings = get_plugin_settings("sphinx-swift.sublime-settings", sphinx_swift_settings_file_variables, True)
#     print('these settings {}'.format(settings))
#     inv_map_source = settings.get("intersphinx_map_file", "")
#     print('inv map source= {}'.format(inv_map_source))
#     if not inv_map_source:
#         sublime.error_message("Unable to find [intersphinx_map_file] setting in sphinx-swift.sublime-settings")
#         return
#     the_path, the_file = os.path.split(inv_map_source)
#     print("PATH:{} FILE:{}".format(the_path, the_file))
#     sys.path.append(the_path)
#     # import the file without the .py extension name according to import syntax
#     mapmod = __import__(os.path.splitext(the_file)[0])
#     return mapmod.intersphinx_mapping

# def get_this_proj_intersphinx_label(map_with_fq_filepaths, cur_project_dir):
#     """
#     The top set of keys in the intersphinx map are shortname labels that intersphinx uses to identify different projects
#     A sub-tuple in the dict (here invdata[1]) is a list of possible locations for the project's objects.inv file 
#     This utility checks all the locations (only filepath ones) to see if the current project dir name is in the filepath
#     If a match is found this immediately returns the shortname label, which can be used to locate current project data in the intersphinx map
#     This is a 'good guess' to determine which intersphinx entry relates to the current project
#     """
#     for shortname, invdata in map_with_fq_filepaths.items():
#         for invpath in invdata[1]:
#             # if invpath and not invpath.startswith("http"):
#             #     if cur_project_dir in invpath:
#             #         return shortname
#             if invpath:
#                 if invpath.startswith(cur_project_dir):
#                     return shortname
#     return None

# def get_objinv_from_intersphinx_map(the_map, the_key):
#     """
#     Return a filename string for the first existing 'objects.inv' found in the_key section of the_map (intersphinx_mapping)
#     These filenames are now absolute in intersphinx_mapping
#     Display an error and Return None if no existing files are found 
#     """
#     for filestr in the_map[the_key][1]:
#         # filestr = os.path.normpath(os.path.join(proj_root_folder, f))
#         # if filestr:
#         print('checking for objinv at: {}'.format(filestr))
#         if os.path.exists(filestr):
#             return filestr
#     sublime.error_message("[key={}] - cannot locate an 'objects.inv' file in the intersphinx_mapping.".format(the_key))
#     return None  


# ************************************************************
#
# The following utils parse sphinx's 'objects.inv' files seeking out different types of link information
# These were borrowed from the intersphinx sphinx plugin, and slightly modified
#
# ************************************************************


                    # # NOTE: The following (from intersphinx) may be useful for reading object.inv files from the net (and files?)
                    # from sphinx.ext import intersphinx
                    # import warnings


                    # def fetch_inventory(uri):
                    #     """Read a Sphinx inventory file into a dictionary."""
                    #     class MockConfig(object):
                    #         intersphinx_timeout = None  # type: int
                    #         tls_verify = False

                    #     class MockApp(object):
                    #         srcdir = ''
                    #         config = MockConfig()

                    #         def warn(self, msg):
                    #             warnings.warn(msg)

                    #     return intersphinx.fetch_inventory(MockApp(), '', uri)


                    # uri = 'http://docs.python.org/2.7/objects.inv'

                    # # Read inventory into a dictionary
                    # inv = fetch_inventory(uri)
                    # # Or just print it
                    # intersphinx.debug(['', uri])

