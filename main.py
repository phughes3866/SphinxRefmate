from .utils.lnk_devLoadRefreshUtils import devStartupShim; devStartupShim()
from .utils.lnk_loggingUtils import getLogger; logger = getLogger(debug=True)

import os
import re
from urllib.parse import urlsplit
import sublime
import sublime_plugin


from .utils import lnk_ioUtils
from .utils.lnk_parsingUtils import get_combo_plugin_settings, get_project_plugin_settings, getPyFileVars, getSettingsVars
from .utils.loc_constants import settingsControl
from .utils.loc_intersphinxHelpers import getThinIntersphinxMap, validRefTypesList, getObjInvDisplayLists

pluginName = __package__.split('.')[0]
settings = settingsControl

class CiteFromBiblioFilesCommand(lnk_ioUtils.MessageOutputUtils, sublime_plugin.TextCommand):
    """
    Parses a list of files to regex search for sphinx project bibliographies
    This can only be one file so only a single bibliography is supported
    The name of the file must be set in sphinx-swift settings as "bibliography_rst_file"
    An external utility then constructs a dictionary of cit / ref pairs from the parsed bibliography
    Presents to user (in sublime's quick panel) a list of references
    If the user selects one the citation is put in at the cursor position
    """
    def on_done(self, index):
        """Callback function for sublime's quick-menu presentation of citations
        """
        if index == -1:
            # noop; nothing was selected, e.g. the user pressed escape
            return
        else:
            self.view.run_command('insert', {"characters": self.insert_list[index]})

    def get_refs_from_file(self, filename):
        """
        Opens the filename and parses it (regex) to find restructured text citation lines of the kind:
           ".. [author_yr] Author, 1966 Great Book"
        or in regex capture group terms:
           ".. [<cite_label>] <cite_text>"
        Care is taken to avoid footnotes, which have an almost identical syntax to citations.
        The <cite_label> must not begin with a '#' or a numerical digit, or it will be deemed a footnote reference.
        Found citation lines are parsed into a dictionary: { cite_label: cite_line } and returned
        """
        pattern = re.compile(r"""
            ^\.\.\s+\[
            (?P<cite_label>[^#\d].*?)\]\s+
            (?P<cite_text>.*)$
            """, re.VERBOSE | re.MULTILINE)
        with open(filename, 'r') as reffile:
            # Read file object to string
            text = reffile.read()
        found = re.findall(pattern, text)
        if found:
            return dict(found)
        return None

    def is_enabled(self, **kwargs):
        return bool(settings.getOne('bib_ref_file_list'))

    def run(self, edit):
        # Process a list of user provided cite_files to build a dictionary of available citations
        # `- collect data on the number of missing/empty files as we go
        cite_file_list = settings.getOne('bib_ref_file_list')
        if not cite_file_list:
            # this shouldn't happen as command is disabled if no cite file data is available
            return
        subl_top_folder_path = self.view.window().extract_variables()["folder"]
        citeFileCount = len(cite_file_list)
        datalessFileList = []
        unreadableFileList = []
        dataYieldingFileCount = 0
        single_parse_result = {}
        collect_parse_result = {}
        for f in cite_file_list:
            fq_ref_file = os.path.normpath(os.path.join(subl_top_folder_path, f))
            if not os.access(fq_ref_file, os.R_OK):
                unreadableFileList += [f]
            else:
                single_parse_result = self.get_refs_from_file(fq_ref_file)
                if single_parse_result:
                    collect_parse_result.update(single_parse_result)
                    dataYieldingFileCount += 1
                else:
                    datalessFileList += [f]

        if unreadableFileList:
            for duffOne in unreadableFileList:
                logger.info(f"User set bibliographic file \"{duffOne}\" is unreadable")
        if datalessFileList:
            for duffOne in datalessFileList:
                logger.info(f"User set bibliographic file \"{duffOne}\" yielded no citation data")

        # Process our dictionary of collected citations
        # `- build display/insert lists
        self.insert_list = []
        self.display_list = []
        if collect_parse_result:

            # Step 1 of 2: Some info/message generating
            citationCount = len(collect_parse_result)
            if dataYieldingFileCount < citeFileCount:
                # one or more files yielded no data
                msgShim = f"of {citeFileCount} "
            else:
                msgShim = ""
            placeholderInfo = (f"{citationCount} citations from {dataYieldingFileCount} "
                               f"{msgShim}source{'s'[:citeFileCount^1]}")
            logger.debug(f"{citationCount} citations found "
                         f"from {dataYieldingFileCount} {msgShim}"
                         f"user set filename{'s'[:citeFileCount^1]}")

            # Step 2 of 2: Process the cit/ref data and display the quick panel
            for cit, ref in collect_parse_result.items():
                # insert the reSt citation reference in correct syntax
                self.insert_list.append(f"[{cit}]_")
                self.display_list.append(f"[{cit}] = {ref}")
            sublime.active_window().show_quick_panel(
                self.display_list, 
                self.on_done,
                placeholder = placeholderInfo
            )
        else:
            self.error_message("No restructuredtext citations found in the searched files: "
                              f"{cite_file_list}\n\nThese files are user set.\n\n"
                               f"Please amend your {pluginName} settings so that \"bib_ref_file_list\" provides"
                               "one or more filenames for where your bibliographic data is located.")


class InsertRstEpilogSubstitutionCommand(lnk_ioUtils.MessageOutputUtils, sublime_plugin.TextCommand):
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

    def get_rst_epilog_2part_replacement_dict(self, rst_epilog_str):
        find_replacement_patterns = re.compile(r"""
            ^\.\.\s+
            \|(?P<short>.*)\|
            \s+replace::\s+
            (?P<long>.*)$
            """, re.VERBOSE | re.MULTILINE)
        return dict(re.findall(find_replacement_patterns, rst_epilog_str))

    def get_rst_epilog_and_prolog(self):
        subl_top_folder_path = self.view.window().extract_variables()["folder"]
        confPyPath = os.path.join(subl_top_folder_path, 'conf.py')
        if not os.access(confPyPath, os.R_OK):
            return (None, None)
        else:
            confPyVarsToGet = ["rst_epilog", "rst_prolog"]
            return getPyFileVars(confPyPath, confPyVarsToGet)

    def is_enabled(self):
        epilogPrologTuple = self.get_rst_epilog_and_prolog()
        shouldEnable = not all(var is None for var in epilogPrologTuple)
        if shouldEnable:
            logger.debug(f'Enabling menu for {__class__} as rstEpilog and/or rstProlog contain data.')
        else:
            logger.debug(f'Disabling menu for {__class__} as rstEpilog and rstProlog contain no data.')
        return shouldEnable 

    def run(self, edit):
        self.insert_list = []
        self.display_list = []

        epilogPrologTuple = self.get_rst_epilog_and_prolog()
        for substStr in epilogPrologTuple:
            if substStr is not None:
                convertedRstEpilog = self.get_rst_epilog_2part_replacement_dict(substStr)
                if convertedRstEpilog:
                    for shorty, longy in convertedRstEpilog.items():
                        self.insert_list.append("|{}|".format(shorty))
                        self.display_list.append("|{}| = {}".format(shorty, longy))

        parsing_status_msg = f"{len(self.display_list)} rst_[epi|pro]log replacements loaded from sphinx conf.py"
        self.status_message(parsing_status_msg)
        logger.debug(parsing_status_msg)

        # There will always be something to display as this routine inserts several of sphinx's own standard replacements
        if self.display_list:
            # Add to compiled display/insert lists with some standard Sphinx replacements
            # self.insert_list += ["|release|",
            #                     "|version|"]
            # self.display_list += ["|release| STD conf.py: full version str e.g. 2.5.2b3",
            #                     "|version| STD conf.py: major + minor versions e.g. 2.5"]

            sublime.active_window().show_quick_panel(
                self.display_list, 
                self.on_done
            )


class VisibleIfHaveConfPyAndRstContextCommand(lnk_ioUtils.MessageOutputUtils, sublime_plugin.TextCommand):
    """
    A dummy 'visibility-only' command for the top-level context menu,
    to make the menu visible only if the following 2 situations are true:
    a) a {project folder}/conf.py exists and is readable i.e. this could be a sphinx project
    b) the presently active cursor is located in a 'text.restructuredtext' scope
    The class exploits the 'is_visible' method to return True/False as required.
    This command is used in the following 1x top level context menu:
    >Sphinx Refmate>>
    i.e. >Sphinx Refmate>> will not be 'context' available if the above 2 conditions are not met.
    However, the context menu will always be visible if the 'rstEnvCheck' is set to False in settings
    """
    def run(self, edit, **kwargs):
        pass

    def is_visible(self, **kwargs):
        if not settings.getOne('rstEnvCheck'):
            logger.debug("Showing top level context menu "
                         "without checking for conf.py and reSt context "
                         "(as \"rstEnvCheck\" is disabled in settings.)")
            return True
        else:
            # Must check for a) extant 'conf.py', b) cursor in reSt context
            subl_top_folder_path = self.view.window().extract_variables()["folder"]
            # Check A: Does conf.py exist in a readable state?
            if not os.access(os.path.join(subl_top_folder_path, 'conf.py'), os.R_OK):
                logger.debug("Hiding top level context menu "
                             "as conf.py absent from project root folder")
                return False
            elif not self.view.match_selector(self.view.sel()[0].begin(), "text.restructuredtext"):
                logger.debug("Hiding top level context menu "
                             "as cursor not within \"text.restructuredtext\" scope")
                return False
            else:
                logger.debug("Showing top level context menu "
                             "as conf.py exists and cursor is within reSt context.")
                return True


class VisibleIfIntersphinxChecksOkCommand(lnk_ioUtils.MessageOutputUtils, sublime_plugin.TextCommand):
    """
    A dummy 'visibility-only' command for parent menus (which would be otherwise command-less),
    to make the menu visible only if a {project folder}/conf.py file yields the following
    two variables a) 'intersphinx_mapping' and b) 'html_baseurl'.
    The class exploits the 'is_visible' method to return True/False as required.
    This command is used in the following 2x second level context menus:
    >Sphinx Refmate>>Insert Links To Current Project>>
    >Sphinx Refmate>>Insert Links To Intersphinx Projects>>
    i.e. neither of these two menus will be 'context' available
    if the above 2 specified variables are not present in conf.py
    """

    # this string should be set in child classes
    targetMenuStr = "--placeholder--"

    def is_enabled(self, **kwargs):
        # Construct the expected sphinx-doc project %root-folder%/conf.py file path
        subl_top_folder_path = self.view.window().extract_variables()["folder"]
        confPyPath = os.path.join(subl_top_folder_path, 'conf.py')
        if not os.access(confPyPath, os.R_OK):
            logger.debug(f"{self.targetMenuStr} menu disabled: as conf.py absent from project root folder")
            return False

        logger.debug(f"Determining {self.targetMenuStr} visibility by checking for key variables in {confPyPath}")
        # try to read two required variables from conf.py
        confPyVarsToGet = ["intersphinx_mapping",
            "html_baseurl"]
        intersphinxMap, projBaseurl = getPyFileVars(confPyPath, confPyVarsToGet)
        # check the two required variables
        if intersphinxMap is None:
            logger.debug(f'{self.targetMenuStr} menu disabled: No \"intersphinx_mapping\" variable in Sphinx project conf.py')
            return False
        elif projBaseurl is None:
            logger.debug(f'{self.targetMenuStr} menu disabled: No \"html_baseurl\" variable in Sphinx project conf.py')
            return False
        else:
            logger.debug(f'{self.targetMenuStr} menu enabled: Found both \"intersphinx_mapping\" and \"html_baseurl\" in Sphinx project conf.py')
            return True


class ShowIntLinksIfIntersphinxChecksOkCommand(VisibleIfIntersphinxChecksOkCommand):
    targetMenuStr = "<<Insert Links To Current Project>>"


class ShowExtLinksIfIntersphinxChecksOkCommand(VisibleIfIntersphinxChecksOkCommand):
    targetMenuStr = "<<Insert Links To Intersphinx Projects>>"


class InsertSphinxLinksCommand(lnk_ioUtils.MessageOutputUtils, sublime_plugin.TextCommand):
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

    def run(self, edit, withinProj=False, refTypeToGet='all'):
        # The refTypeToGet and withinProj vars must be set in the sublime command calls to this routine
        if refTypeToGet == 'all':
            refTypeTargetList = validRefTypesList
        elif refTypeToGet in validRefTypesList:
            refTypeTargetList = [refTypeToGet]
        else:
            logger.error(f"Plugin config error. Incorrect [{refTypeToGet}] setting for refTypeToGet parameter")
            return

        self.datalist = []
        self.displaylist = []

        # Find some essential/useful variables from the associated sphinx project %root-folder%/conf.py file
        self.subl_top_folder_path = self.view.window().extract_variables()["folder"]
        confPyPath = os.path.join(self.subl_top_folder_path, 'conf.py')
        confPyVarsToGet = ["intersphinx_mapping",
            "html_baseurl",
            "intersphinx_resolve_self"]
        self.givenMap, projBaseurl, projResolveSelf = getPyFileVars(confPyPath, confPyVarsToGet)
        projSelfKey = settings.get(['intersphinx_self_key'])['intersphinx_self_key']

        # print(f"found intersphinx_mapping = {self.givenMap}")
        # print(f"found html_baseurl = {projBaseurl}")
        # print(f"found projResolveSelf = {projResolveSelf}")
        # print(f"found projSelfKey = {projSelfKey}")
        # return

        if self.givenMap is None:
            self.error_message('No intersphinx_mapping variable in current sphinx project conf.py')
            return

        # identify key to local proj in intersphinx_mapping
        if projSelfKey is None:
            if projResolveSelf is not None:
                projSelfKey = projResolveSelf
            elif projBaseurl is not None:
                projNetloc = urlsplit(projBaseurl).netloc
                for isKey, isData in self.givenMap.items():
                    if urlsplit(isData[0]).netloc == projNetloc:
                        projSelfKey = isKey
                        break
        # print(f'calculated proj self key = {projSelfKey}')
        # return

        # If a sphinx project is local/private, i.e. not publicly accessible on the internet
        # then we don't want links to this site to appear in public sphinx projects.
        # To distinguish between local/private projects and public projects, SphinxRefmate 
        # allows the use of a 'priv-project-prefix' (definable via plugin settings).
        # SphinxRefmate will recognise private projects by this prefix, and will not
        # put links to private projects to be inserted in public projects.
        priv_prefix = settings.get(['priv_project_prefix'])['priv_project_prefix']
        logger.debug(f"Settings yielded private/local project prefix = \"{priv_prefix}\" (for intersphinx map keys)")

        self.targetKeyList = []  # an empty self.targetKeyList list will get link data from all intersphinx map keys
        if withinProj:
            # limit link data to current project intersphinx map key
            self.targetKeyList = [projSelfKey]
        elif priv_prefix and not projSelfKey.startswith(priv_prefix):
            # present project is public, so links to private projects must not be used
            # `- so we omit intersphinx map private projects (with private prefix) from our compilations
            logger.debug("Not compiling links to private projects, "
                         "as it would be invalid to insert these "
                         f"into the present public hosted project \"{projSelfKey}\"")
            for isKey in self.givenMap.keys():
                if not isKey.startswith(priv_prefix):
                    self.targetKeyList += [isKey]
        logger.debug(f"Compiling data for following intersphinx map keys: {self.targetKeyList} (all keys if list is empty)")

        simpleMap = getThinIntersphinxMap(self.givenMap, self.subl_top_folder_path, self.targetKeyList)
        # for thisKey, objInvPaths in self.normalise_map_dict().items():
        for thisKey, objInvPaths in simpleMap.items():
            for extantPath in objInvPaths:
                logger.debug(f"Parsing {extantPath} (for sphinx project \"{thisKey}\" handle links)")
                if thisKey == projSelfKey:
                    curProj = True
                    logger.debug(f'- Intersphinx:{thisKey} is the project currently being edited')
                else:
                    curProj = False
                datal, displ = getObjInvDisplayLists(extantPath,
                                                    refTypeTargetList=refTypeTargetList,
                                                    intersphinx_key=thisKey,
                                                    is_cur_proj=curProj)
                self.datalist += datal
                self.displaylist += displ
                logger.debug(f'- Intersphinx:{thisKey} yielded {len(datal)} references of type: {refTypeTargetList}')

        if not self.datalist:
            self.status_message("No valid intersphinx data found")
            logger.error(f'No {refTypeTargetList} entries found in any objects.inv '
                         'for all searched intersphinx map keys.')
            return
        elif len(self.datalist) == len(self.displaylist):  # check display and data lists are same length
            self.status_message(f"Displaying {len(self.datalist)} objects.inv entries")
            logger.debug(f"Displaying {len(self.datalist)} objects.inv entries")
            sublime.active_window().show_quick_panel(
                self.displaylist, 
                self.on_done
            )
        else:
            self.error_message('Data mismatch in retrieving [{}] entries from {}'.format(refTypeToGet, ObjInvPath))
            return
