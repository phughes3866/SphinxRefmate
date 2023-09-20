import os
import sys
import ast
import re
import zlib
import sublime
import sublime_plugin
from collections import defaultdict
from .utils import refmate_utils
from .utils.constants import pluginEnv, pluginSettingsGovernor
try:
    from saltydog.saltydog import pluginCentraliser, MessageOutputUtilsClassAddin
except:
    from .utils.saltydog import pluginCentraliser, MessageOutputUtilsClassAddin

global pluginCentral

if int(sublime.version()) >= 3114:

    # Clear module cache to force reloading all modules of this package.
    prefix = __package__ + "."  # don't clear the base package
    for module_name in [
        module_name
        for module_name in sys.modules
        if module_name.startswith(prefix) and module_name != __name__
    ]:
        del sys.modules[module_name]
    prefix = None

    # Import public API classes
    # from .core.command import MyTextCommand
    # from .core.events import MyEventListener

    def plugin_loaded():
        """
        Initialize plugin:
        This module level function is called on ST startup when the API is ready. 
        """
        # print(f'{pluginEnv["pluginName"]} (re)loaded')
        # initialiseSettings(pluginSettingsGovernor, pluginEnv)
        global pluginCentral
        pluginCentral = pluginCentraliser(pluginSettingsGovernor, pluginEnv)
        print(f'{pluginCentral.pluginName} settings initialised')

    def plugin_unloaded():
        """
        This module level function is called just before the plugin is unloaded.
        Complete tasks.
        Cleanup package caches.
        Exit threads.
        """
        # deactivateSettings()
        # print(f'{pluginEnv["pluginName"]} unloaded')
        # pass

else:
    raise ImportWarning(f"The {pluginEnv['pluginName']} plugin doesn't work with Sublime Text versions prior to 3114")


class CiteFromBiblioFilesCommand(sublime_plugin.TextCommand):
    # """
    # Parses a list of files to regex search for sphinx project bibliographies
    # This can only be one file so only a single bibliography is supported
    # The name of the file must be set in sphinx-swift settings as "bibliography_rst_file"
    # An external utility then constructs a dictionary of cit / ref pairs from the parsed bibliography
    # Presents to user (in sublime's quick panel) a list of references
    # If the user selects one the citation is put in at the cursor position
    # """
    def on_done(self, index):
        """Callback function for sublime's quick-menu presentation of citations
        """
        if index == -1:
            # noop; nothing was selected, e.g. the user pressed escape
            return
        else:
            self.view.run_command('insert', {"characters": self.insert_list[index]})

    def get_refs_from_file(self, filename):
        # opens file with std rst refs and parses it into a dict of 2 part dicts (cit / ref)
        # pattern for matching in target filename is ".. [author_yr] Author, 1966 Great Book"
        pattern = re.compile(r"""
            ^\.\.\s+\[
            (?P<cit>.*?)\]\s+
            (?P<ref>.*)$
            """, re.VERBOSE | re.MULTILINE)
        with open(filename, 'r') as reffile:
            # Read file object to string
            text = reffile.read()
        # for match in pattern.finditer(text):
        #     return match.group(1)
        found = re.findall(pattern, text)
        if found:
            return dict(found)
        return None

    def run(self, edit):
        global pluginCentral
        if not pluginCentral.allowCommandsToRun():
            return

        self.insert_list = []
        self.display_list = []

        # Perform some initial environment checks
        # `- Are we in a sphinx project and a restructured text scope?
        subl_top_folder_path = self.view.window().extract_variables()["folder"]
        docScope = self.view.scope_name(self.view.sel()[0].begin())

        refmate_settings = pluginCentral.settingsAsDict()
        if not refmate_utils.sphinx_and_rst_checks(subl_top_folder_path, docScope, refmate_settings):
            return

        cite_file_list = refmate_settings.get('bib_ref_file_list', [])
        if not cite_file_list:
            pluginCentral.error_message("Unable to run as no bibliography files were provided in the settings.\n\n"
                "The plugin is not currently configured for citation insertions.")
            return

        # Process our list of cite_files to build a dictionary of available citations
        # `- collect data on the number of missing/empty files as we go
        empty_filecount = 0
        missing_filecount = 0
        single_parse_result = {}
        collect_parse_result = {}
        for f in cite_file_list:
            fq_ref_file = os.path.normpath(os.path.join(subl_top_folder_path, f))
            if not os.path.isfile(fq_ref_file):
                missing_filecount += 1
            else:
                single_parse_result = self.get_refs_from_file(fq_ref_file)
            if single_parse_result:
                collect_parse_result.update(single_parse_result)
            else:
                empty_filecount += 1

        # Process our dictionary of collected citations
        # `- build display/insert lists
        if collect_parse_result:
            parsing_status_msg = "{} references found".format(len(collect_parse_result))
            if missing_filecount > 0 or empty_filecount > 0:
                parsing_status_msg += ": Warning: {} missing/{} empty files".format(missing_filecount, empty_filecount)
            for cit, ref in collect_parse_result.items():
                self.insert_list.append("[{}]_".format(cit))
                self.display_list.append("[{}] = {}".format(cit, ref))
            pluginCentral.status_message(parsing_status_msg)
            sublime.active_window().show_quick_panel(
                self.display_list, 
                self.on_done
            )
        else:
            pluginCentral.error_message(f"No references found in the searched files: {cite_file_list}\n\n"
                "Check that your settings point to where your bibliography entries are located.")


class InsertRstEpilogSubstitutionCommand(sublime_plugin.TextCommand):
    """
    Present user with a list of sphinx reST |substitutions| which are valid in the current sphinx project. Insert the chosen one at current cursor pos
    1. compile list of substitutions - some standard ones, plus we must parse conf.py and extract those in the rst_epilog variable
    2. parse any other files that contain rst_epilog additions that are used by the project (these files are in a list in the sphinx-swift settings)
    2. show the |substitutions| plus their expanded text to the user in a quick panel
    3. insert the chosen |substitution| at the current cursor position
    """
    def on_done(self, index):
        if index == -1:
            # noop; nothing was selected, e.g. the user pressed escape
            return
        else:
            self.view.run_command('insert', {"characters": self.insert_list[index]})

    def get_rstEpilogs_from_config_file(self, config_file):
        found_rstEp = ""
        ast_assigns = refmate_utils.parse_pyfile_for_ast_types(config_file, [ast.Assign, ast.AugAssign])
        if ast_assigns:
            # print('file:  {} gave {} aug/assigns'.format(config_file, len(ast_assigns)))
            for x in ast_assigns:
                # print('type of assign = {}'.format(type(x)))
                addMe = False
                if type(x) is ast.AugAssign:
                    if x.target.id == 'rst_epilog':
                        addMe = True
                elif type(x) is ast.Assign:
                    if x.targets[0].id == 'rst_epilog':
                        addMe = True
                if addMe:
                    try:
                        found_rstEp += eval(compile(ast.Expression(x.value), "<ast expression", "eval"))
                        raise TypeError("Only integers are allowed")
                    except Exception as xcept:
                        pluginCentral.xcept_message(f"Exception evaluating ast expression [{x.value}]", xcept)
        # print('gathered: {}'.format(found_rstEp))
        return found_rstEp

    def get_rst_epilog_2part_replacement_dict(self, rst_epilog_str):
        find_replacement_patterns = re.compile(r"""
            ^\.\.\s+
            \|(?P<short>.*)\|
            \s+replace::\s+
            (?P<long>.*)$
            """, re.VERBOSE | re.MULTILINE)
        return dict(re.findall(find_replacement_patterns, rst_epilog_str))

    def run(self, edit):
        global pluginCentral
        if not pluginCentral.allowCommandsToRun():
            return
        # Perform some initial environment checks
        # `- Are we in a sphinx project and a restructured text scope?
        subl_top_folder_path = self.view.window().extract_variables()["folder"]
        docScope = self.view.scope_name(self.view.sel()[0].begin())
        refmate_settings = pluginCentral.settingsAsDict()
        # projectPluginSettings = self.view.window().project_data().get('settings')
        projectSetts = {}
        projectPluginSettings = sublime.active_window().project_data().get('settings')
        if projectPluginSettings:
            projectSetts = projectPluginSettings.get(pluginName+'PS')
        sublime.message_dialog(f'sfile: {refmate_settings}\npSetts: {projectSetts}')
        return
        if refmate_settings is None: return
        # refmate_settings = sublime.load_settings(pluginSettingsFile)
        # proj_plugin_settings = sublime.active_window().active_view().settings().get(pluginName, {})
        # # any SphinxRefmate settings in the .sublime-project file will override same name Default/User settings
        # refmate_settings.update(proj_plugin_settings)
        if not refmate_utils.sphinx_and_rst_checks(subl_top_folder_path, docScope, refmate_settings):
            return

        # Pre-populate our display/insert lists with some standard Sphinx replacements
        self.insert_list = ["|release|",
                            "|version|"]
        self.display_list = ["|release| STD conf.py: full version str e.g. 2.5.2b3",
                            "|version| STD conf.py: major + minor versions e.g. 2.5"]

        sphinx_rst_epilog_files = refmate_settings.get('rst_epilog_source_list', [])
        if not sphinx_rst_epilog_files:
            pluginCentral.error_message("Search file list for rst_epilog / rst_prolog entries is empty.\n\n"
                "This plugin is not currently configured for automatic reST substitution insertions. "
                "Please update the settings if you wish to implement this feature.")
        else:
            empty_filecount = 0
            missing_filecount = 0
            for f in sphinx_rst_epilog_files:
                fq_ref_file = os.path.normpath(os.path.join(subl_top_folder_path, f))
                if not os.path.isfile(fq_ref_file):
                    missing_filecount += 1
                    # sublime.error_message("No sphinx config file at project root.\n Missing: {}".format(f))
                else:  # parse the file to collect 'rst_epilog' style |substitutions|
                    oneRstEpilog = self.get_rstEpilogs_from_config_file(fq_ref_file)
                    if not oneRstEpilog:
                        empty_filecount += 1
                        # self.status_message("No rst_epilog in {}".format(f))
                    else:
                        convertedRstEpilog = self.get_rst_epilog_2part_replacement_dict(oneRstEpilog)
                        if convertedRstEpilog:
                            for shorty, longy in convertedRstEpilog.items():
                                self.insert_list.append("|{}|".format(shorty))
                                self.display_list.append("|{}| = {}".format(shorty, longy))
            parsing_status_msg = "{} replacements loaded from {} rst_epilog locations"\
                                        .format(len(self.display_list) - 2, len(sphinx_rst_epilog_files))
            if missing_filecount > 0 or empty_filecount > 0:
                parsing_status_msg += ": Warning: {} missing/{} empty files".format(missing_filecount, empty_filecount)

            pluginCentral.status_message(parsing_status_msg)
            # There will always be something to display as this routine inserts several of sphinx's own standard replacements
            sublime.active_window().show_quick_panel(
                self.display_list, 
                self.on_done
            )

class ContextuallyVisibleParentMenuItemCommand(sublime_plugin.TextCommand):
    """
    A wrapper to be used for parent menus (command-less) to make them visible only in certain scopes/contexts.
    The class overrides the 'is_visible' method so it returns True only when the current scope matches the target scope
    """
    def run(self, edit, **kwargs):
        pass

    def is_visible(self, **kwargs):
        # refmate_settings = sublime.load_settings(pluginSettingsFile)
        # proj_plugin_settings = sublime.active_window().active_view().settings().get(pluginName, {})
        # # any SphinxRefmate settings in the .sublime-project file will override same name Default/User settings
        # refmate_settings.update(proj_plugin_settings)
        refmate_settings = pluginCentral.settingsAsDict()
        if refmate_settings.get('rst_check'):
            contextOK = self.view.match_selector(self.view.sel()[0].begin(), "text.restructuredtext")
        else:
            contextOK = True
        return refmate_settings.get('enable_context_menu', False) and contextOK


class HonedIntersphinxMap():
    """
    Build a honed version of a standard intersphinx_mapping dictionary, for local referencing purposes
    Honing involves the following work on the one or more objects.inv paths in each intersphinx_mapping entry:
    a) Getting rid of entries that are not local files (e.g. 'None', 'http...')
    b) Normalising (making absolute) filepaths relative to the sublime project directory
    c) Omitting any filepaths that do not point to an extant file
    d) Determining which intersphinx_mapping name/entry corresponds to our local project
       `- by EITHER:
        a) Reading the SphinxRefmate['cur_proj_intersphinx_map_name'] in the .sublime-project settings section
           `- and checking this matches an actual intersphinx_mapping name/key 
        b) matching one of the objects.inv paths to within our current project tree
    """
    def normalise_map_dict(self, md, norm_path):
        retDict = {}
        self.mapProcReport = ''
        normFailInfo = defaultdict(list)
        try:
            for shortname, invdata in md.items():
                fq_file_list = []
                for i, invpath in enumerate(invdata[1]):
                    if invpath is not None and not invpath.startswith('http'):
                        try:
                            np = os.path.normpath(os.path.join(norm_path, invpath))
                        except Exception as err:
                            normFailInfo[shortname].append('[{}] Error: Cannot normalise path to {} [{}].'.format(invpath, norm_path, err))
                            continue
                        if os.access(np, os.R_OK):
                            fq_file_list.append(np)
                            if not self.curProjKey:
                                if np.startswith(norm_path):
                                    self.curProjKey = shortname
                        else:
                            normFailInfo[shortname].append('[{}] Error: File not readable.'.format(invpath))
                    else:
                        normFailInfo[shortname].append('[{}] Skipping: Non-file item.'.format(invpath))
                if fq_file_list:
                    # we found at least one objects.inv, clear any errors encountered in obtaining others
                    normFailInfo.pop(shortname, True)
                    # save our object.inv path(s) in the correct format for returning
                    retDict[shortname] = (invdata[0], tuple(fq_file_list))
        except Exception as err:
            print('Error processing {} entry in intersphinx map: [{}]\nErr = {}'.format(shortname, invdata, err))
            retDict = {}
        if normFailInfo:
            detailStr = ''
            for key, value in normFailInfo.items():
                for i, failInfo in enumerate(value):
                    detailStr += '\n{}: {}'.format(key, failInfo)
            self.mapProcReport = 'No valid objects.inv files could be located for the following '\
                'Sphinx projects: {}\n'.format(", ".join([key for key, value in normFailInfo.items()]))
            self.mapProcReport += 'Details: {}'.format(detailStr)
        if retDict:
            # we have at least one valid objects.inv locations
            if not self.curProjKey:
                # but we've been unable to identify which objects.inv belongs to the curren edit project
                pluginCentral.msgBox("{} Warning: Cannot identify current Sphinx project in the intersphinx_mapping.\n\n"
                    "We will continue but if you use SphinxRefmate to insert a reference under these circumstances, "
                    "then that reference will be transformed into a fully qualified hyperlink, at build time, rather than "
                    "a relative link.\n\nOne way to overcome this problem is to set the [cur_proj_intersphinx_map_name] setting in the "
                    "[SphinxRefmate] section of the current project's .sublime-project file, so that it matches the correct "
                    "intersphinx_mapping key.".format(pluginName))
            if self.mapProcReport:
                # but we couldn't locate an objects.inv one or more projects
                pluginCentral.msgBox("{} Warning: Unable to build reference lists for all identified projects:\n\n"
                    "{}".format(pluginName, self.mapProcReport))
        return retDict

    def __init__(self, stdMap={}, subl_proj_root_path="", plugin_settings={}):
        self.givenMap = stdMap
        self.subl_top_folder_path = subl_proj_root_path
        self.OK = True
        self.whatsWrong = ''
        self.mapProcReport = ''
        # the current project intersphinx map key/name may have been provided in the .sublime-settings of a project
        # in which case we don't have to work out our current project key by path comparisons (which is not guaranteed to work)
        self.curProjKey = plugin_settings.get('cur_proj_intersphinx_map_name', '')
        if self.curProjKey:
            if self.curProjKey not in self.givenMap:
                pluginCentral.msgBox('cant find {} key'.format(self.curProjKey))
                self.curProjKey = ''

        # Init Step 1: Perform our objects.inv path normalisations
        self.honedMap = self.normalise_map_dict(self.givenMap, self.subl_top_folder_path)
        if not self.honedMap:
            self.whatsWrong = 'Problems found in normalising the objects.inv location paths to the current '\
                'project (top level) folder: {}\n\nYou may need to amend '\
                'your intersphinx_mapping settings.'.format(self.subl_top_folder_path)
            if self.mapProcReport:
                self.whatsWrong += '\nFailed intersphinx_mapping summary:\n{}'.format(self.mapProcReport)
            self.OK = False

    def getObjectInv(self, projectIDKey=None):
        """
        Return the first available objects.inv filepath for a project
        This will have been pre-checked as extant by the normalise_map_dict function
        """
        if self.OK:
            try:
                self.searchLine = self.honedMap.get(projectIDKey, None)
            except Exception as err:
                print('Error retrieving [{}] entry from map: {}\n\nErr: {}'.format(projectIDKey, self.honedMap, err))
                self.searchLine = None
            return self.searchLine[1][0]

    def getCurProjObjectInv(self):
        if self.OK:
            return self.getObjectInv(self.curProjKey)

    def getKeyList(self):
        if self.OK:
            return [projectShortname for projectShortname, infoTuple in self.honedMap.items()]

    def OK(self):
        return self.OK

    def errorStr(self):
        return self.whatsWrong


class IntersphinxMapFinder():

    @staticmethod
    def get_intersphinx_map_from_config_file(config_file):
        found_map = {}
        ast_assigns = refmate_utils.parse_pyfile_for_ast_types(config_file, [ast.Assign])
        if ast_assigns:
            # print('no. of assigns = {}'.format(len(ast_assigns)))
            for x in ast_assigns:
                # print('name = {}'.format(x.targets[0].id))
                if x.targets[0].id == 'intersphinx_mapping':
                    try:
                        found_map = eval(compile(ast.Expression(x.value), "<ast expression", "eval"))
                    except Exception as err:
                        print('Cannot evaluate ast expression [{}]. Gave error: {}'.format(x.value, err))
                        return None
                    else:
                        return found_map

    def __init__(self, sublProjFolder=None, plugin_settings={}):
        self.mapSourceFile = ""
        self.whatsWrong = ""
        self.OK = True
        self.subl_top_folder_path = sublProjFolder
        self.confFilesSearched = []

        # Init Step 1: Get 'map_file_list' from plugin (+project) settings
        #              map_file_list will contain filenames to search for 'intersphinx_mapping' variable
        self.map_file_list = plugin_settings.get('intersphinx_map_source_list', [])
        # We should now have some file names in 'map_file_list' to search
        if not self.map_file_list:
            self.whatsWrong = "Cannot search for project links as no search targets for 'intersphinx_mapping' were defined in the settings.\n"\
                "Please amend the plugin settings if you want to auto-insert local project references."
            self.OK = False

        # Init Step 2: Get first available 'intersphinx_mapping' var and load it into self.map_dict
        #              Files in self.map_file_list are searched in order until 'intersphinx_mapping' is found
        if self.OK:
            self.map_dict = {}
            for file_to_search in self.map_file_list:
                # the 'file_to_search', as got from settings, is likely to be relative to project/folder root:
                # `- normalise it (absolute paths should not be affected)
                try:
                    fq_map_file = os.path.normpath(os.path.join(self.subl_top_folder_path, file_to_search))
                except Exception as err:
                    print('Cannot normalise path {} to folder {}.\nErr: {}'.format(file_to_search, self.subl_top_folder_path, err))
                    self.confFilesSearched.append('{} [Invalid Path]'.format(file_to_search))
                    continue
                if not os.access(fq_map_file, os.R_OK):
                    self.confFilesSearched.append('{} [File Unreadable]'.format(file_to_search))
                    continue
                self.map_dict = IntersphinxMapFinder.get_intersphinx_map_from_config_file(fq_map_file)
                # print('{} gave map: {}'.format(file_to_search, map_dict))
                if self.map_dict:
                    self.mapSourceFile = fq_map_file
                    # print('found map in file: {}'.format(file_to_search))
                    break
                else:
                    self.confFilesSearched.append('{} [Contains No Map]'.format(file_to_search))
            if not self.map_dict:
                self.whatsWrong = 'Cannot locate a valid intersphinx_mapping variable in any of the '\
                    'config files searched.\n\nFiles searched:\n{}'.format("\n".join(self.confFilesSearched))
                self.OK = False

    def OK(self):
        return self.OK

    def errorStr(self):
        return self.whatsWrong

    def sourceFile(self):
        if self.OK:
            return self.mapSourceFile

    def intersphinx_mapping(self):
        if self.OK:
            return self.map_dict


class InsertSphinxLinksCommand(sublime_plugin.TextCommand):
    """
    Builds a list of sphinx labels, docs, OR glossary terms - or all 3, for one or more Sphinx projects, 
    `- from objects.inv files via intersphinx_mapping settings.
    The intersphinx_mapping variable contains file paths of sphinx project reference databases (objects.inv files)
    The intersphinx_mapping var is located by searching a list of sphinx config files (as defined in the plugin and project settings)
    Note the requirement that an 'intersphinx_mapping' dictionary (see intersphinx extension) is available in the configs
    The 'intersphinx_mapping' dictionary can, however, be put into a config file without running intersphinx
    The objects.inv paths that are found, if relative (highly likely), are normalised with respect to the sublime folder/project root
    ` - this, it's assumed, is the root of the sphinx project, where the sphinx conf.py file resides
    For each sphinx project referenced (just the current, or all) the first found and extant objects.inv file is used.
    The links found in this objects.inf file are presented to the user in a sublime quick panel where one can be selected to insert
    """
    def on_done(self, index):
        # callback function following quickpanel execution
        if index == -1:
            # noop; nothing was selected e.g. the user pressed escape
            return
        else:
            self.view.run_command('insert', {"characters": self.datalist[index]})

    # @staticmethod
    def fetch_inv_lists(self, invloc, refTypeTarget="", intersphinx_key="", is_cur_proj=False):
        """
        Parse a sphinx objects.inv file on the local filesystem at invloc
        return 2 x lists with data/display entries for the identified section of objects.inv
        return empty lists if there are errors processing the objects.inv file
        """
        kosherLine1 = '# Sphinx inventory version 2'
        datalist = []
        displaylist = []
        bufsize = 16 * 1024
        display_prefix = intersphinx_key + ":"
        data_prefix = intersphinx_key + ":"
        if is_cur_proj:
            display_prefix = "*" + display_prefix
            data_prefix = ""

        def read_chunks():
            decompressor = zlib.decompressobj()
            for chunk in iter(lambda: f.read(bufsize), b''):
                yield decompressor.decompress(chunk)
            yield decompressor.flush()

        def split_lines(iter):
            buf = b''
            for chunk in iter:
                buf += chunk
                lineend = buf.find(b'\n')
                while lineend != -1:
                    yield buf[:lineend].decode('utf-8')
                    buf = buf[lineend + 1:]
                    lineend = buf.find(b'\n')
            assert not buf

        try:
            f = open(invloc, 'rb')
            try:
                # Sphinx v2 inventories begin with the following 4 uncompressed lines:
                # Sphinx inventory version 2
                # Project: <project name>
                # Version: <full version number>
                # The remainder of this file is compressed using zlib.
                line = f.readline().rstrip().decode('utf-8')
                if line == kosherLine1:
                    # set up some variables and constants
                    dataMappings = defaultdict(list)
                    displayMappings = defaultdict(list)
                    validRefTypes = ['doc', 'label', 'term']
                    # The first line of the open file 'f' has already been read by the calling function
                    # read line 2 and extract 'projname'
                    line = f.readline()
                    # projname = line.rstrip()[11:].decode('utf-8')
                    # read line 3 and extract 'projname'
                    line = f.readline()
                    # version = line.rstrip()[11:].decode('utf-8')
                    # read line 4 and check for 'zlib' encoding notice
                    line = f.readline().decode('utf-8')
                    if 'zlib' not in line:
                        refmate_utils.error_message("Badly formatted objects.inv file at {}\n\nNo zlib line(4)".format(invloc))
                    else:
                        # main
                        for line in split_lines(read_chunks()):
                            # be careful to handle names with embedded spaces correctly
                            m = re.match(r'(?x)(.+?)\s+(\S*:\S*)\s+(\S+)\s+(\S+)\s+(.*)',
                                         line.rstrip())
                            if not m:
                                continue
                            name, entrytype, prio, location, dispname = m.groups()
                                
                            # adjust any shorthand entries
                            # - any $ terminating the location is shorthand for 'name'
                            if location.endswith(u'$'):
                                location = location[:-1] + name
                            # - any -(dash) terminating the dispname is also shorthand for 'name'
                            if dispname == "-":
                                dispname = name

                            if entrytype.startswith("std:"):
                                # we are only concerned with the standard namespace entries (std)
                                lineRefType = entrytype[4:]  # strip 'std:'
                                if lineRefType in validRefTypes:
                                    if lineRefType == "label":
                                        insertStr = ":ref:`{}{}`".format(data_prefix, name)
                                        displayStr = "{}>section: {} (ref:{})".format(display_prefix, dispname, name)
                                    elif lineRefType == "doc":
                                        insertStr = ":doc:`{}{}`".format(data_prefix, name)
                                        displayStr = "{}>page: {} (doc:{})".format(display_prefix, dispname, name)
                                    elif lineRefType == "term":
                                        insertStr = ":term:`{}{}`".format(data_prefix, name)
                                        displayStr = "{}>glossary_term: {} (term:{})".format(display_prefix, dispname, name)
                                    dataMappings[lineRefType].append(insertStr)
                                    displayMappings[lineRefType].append(displayStr)

                        if refTypeTarget in validRefTypes:
                            # build lists for a single refType
                            datalist = dataMappings[refTypeTarget]
                            displaylist = displayMappings[refTypeTarget]
                        else:
                            # (default) build lists for all refTypes
                            for x in validRefTypes:
                                datalist.extend(dataMappings[x])
                                displaylist.extend(displayMappings[x])

                    # datalist, displaylist = InsertSphinxLinksCommand.read_inventory_v2(f, refTypeTarget=refTypeTarget, \
                        # display_prefix=display_prefix)
                else:
                    pluginCentral.error_message('Unknown first line identifier in objects.inv file: {}\n\n'
                                           'Identifier found: [{}]\n\n'
                                           'Identifier expected: [{}]'.format(invloc, line, kosherLine1))
            except Exception as err:
                pluginCentral.xcept_message(f"Unable to parse intersphinx inventory [{invloc}]", err)
        except Exception as err:
            pluginCentral.xcept_message(f"Unable to open intersphinx inventory [{invloc}]", err)
        finally:
            f.close()
            return datalist, displaylist

    def run(self, edit, withinProj=False, refTypeToGet='all'):
        global pluginCentral
        if not pluginCentral.allowCommandsToRun():
            return

        # The refTypeToGet and withinProj vars must be set in the sublime command calls to this routine
        if refTypeToGet not in ['label', 'doc', 'term', 'all']:
            pluginCentral.error_message("Oops. Programming error. Incorrect [{}] setting for refTypeToGet parameter".format(refTypeToGet))
            return

        self.datalist = []
        self.displaylist = []

        # Perform some initial environment checks
        # `- Are we in a sphinx project and a restructured text scope?
        subl_top_folder_path = self.view.window().extract_variables()["folder"]
        docScope = self.view.scope_name(self.view.sel()[0].begin())
        # refmate_settings = sublime.load_settings(pluginSettingsFile)
        # proj_plugin_settings = sublime.active_window().active_view().settings().get(pluginName, {})
        # # any SphinxRefmate settings in the .sublime-project file will override same name Default/User settings
        # refmate_settings.update(proj_plugin_settings)
        refmate_settings = pluginCentral.settingsAsDict()
        if not refmate_utils.sphinx_and_rst_checks(subl_top_folder_path, docScope, refmate_settings):
            return

        mapFinder = IntersphinxMapFinder(subl_top_folder_path, refmate_settings)
        if not mapFinder.OK:
            pluginCentral.error_message('Error searching for intersphinx mapping: {}'.format(mapFinder.errorStr()))
            mapFinder = None
            return

        honedSphinxMap = HonedIntersphinxMap(mapFinder.intersphinx_mapping(), subl_top_folder_path, refmate_settings)
        if not honedSphinxMap.OK:
            pluginCentral.error_message('Cannot process intersphinx_mapping at: {}\n\n {}'.format(mapFinder.sourceFile(), honedSphinxMap.errorStr()))
            honedSphinxMap = None
            return

        # Are we referencing a single project, or all 'intersphinx' projects
        # if withinProj.lower() in ['true', 'yes']:
        if withinProj:
            # limit projects to search for refs to current project
            projKeyList = [honedSphinxMap.curProjKey]
        else:
            projKeyList = honedSphinxMap.getKeyList()

        # Local lan sphinx projects are prefixed with the value of 'priv_project_prefix' in their intersphinx_map name
        # If referencing a non-local project we DO NOT want to put in references that point to a local project
        priv_prefix = refmate_settings.get('priv_project_prefix', '')
        if priv_prefix:
            if len(projKeyList) > 1 and not honedSphinxMap.curProjKey.startswith(priv_prefix):
                # sublime.message_dialog('missing out locs from {}'.format(projKeyList))
                for i in projKeyList:
                    if i.startswith(priv_prefix):
                        projKeyList.remove(i)
                # sublime.message_dialog('with private ones gone {}'.format(projKeyList))
            
        for thisKey in projKeyList:
            OI = honedSphinxMap.getObjectInv(thisKey)
            if OI:
                pluginCentral.status_message("Parsing {} entries (for intersphinx key/name: {})".format(OI, thisKey))
                curProj = False
                if thisKey == honedSphinxMap.curProjKey:
                    curProj = True
                    # add asterix to easily identify local project in the display
                    # prefixToDisplay = '*' + prefixToDisplay
                # build data/display lists for each required project
                datal, displ = self.fetch_inv_lists(OI, refTypeTarget=refTypeToGet, intersphinx_key=thisKey, is_cur_proj=curProj)
                self.datalist += datal
                self.displaylist += displ

        if not self.datalist:
            pluginCentral.error_message('No [{}] entries found in {}'.format(refTypeToGet, OI))
            return
        elif len(self.datalist) == len(self.displaylist):
            pluginCentral.status_message("Found {} {} entries to display.".format(len(self.datalist), refTypeToGet))
            sublime.active_window().show_quick_panel(
                self.displaylist, 
                self.on_done
            )
        else:
            pluginCentral.error_message('Data mismatch in retrieving [{}] entries from {}'.format(refTypeToGet, OI))
            return
