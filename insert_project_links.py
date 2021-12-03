import os
import sys
import ast
import re
import zlib
import sublime
import sublime_plugin
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
import refmate_utils


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
                sublime.message_dialog("{} Warning: Cannot identify current Sphinx project in the intersphinx_mapping.\n\n"
                    "We will continue but if you use SphinxRefmate to insert a reference under these circumstances, "
                    "then that reference will be transformed into a fully qualified hyperlink, at build time, rather than "
                    "a relative link.\n\nOne way to overcome this problem is to set the [cur_proj_intersphinx_map_name] setting in the "
                    "[SphinxRefmate] section of the current project's .sublime-project file, so that it matches the correct "
                    "intersphinx_mapping key.".format(refmate_utils.plugin_canon_name))
            if self.mapProcReport:
                # but we couldn't locate an objects.inv one or more projects
                sublime.message_dialog("{} Warning: Unable to build reference lists for all identified projects:\n\n"
                    "{}".format(refmate_utils.plugin_canon_name, self.mapProcReport))
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
                sublime.message_dialog('cant find {} key'.format(self.curProjKey))
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

    @staticmethod
    def fetch_inv_lists(invloc, refTypeTarget="", intersphinx_key="", is_cur_proj=False):
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
                        refmate_utils.showRefMateError("Badly formatted objects.inv file at {}\n\nNo zlib line(4)".format(invloc))
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
                    refmate_utils.showRefMateError('Unknown first line identifier in objects.inv file: {}\n\n'
                                           'Identifier found: [{}]\n\n'
                                           'Identifier expected: [{}]'.format(invloc, line, kosherLine1))
            except Exception as err:
                refmate_utils.showRefMateError("Unable to parse intersphinx inventory [{}] "
                    "due to {}: {}".format(invloc, err.__class__.__name__, err))
        except Exception as err:
            refmate_utils.showRefMateError("Unable to open intersphinx inventory [{}] "
                "due to {}: {}".format(invloc, err.__class__.__name__, err))
        finally:
            f.close()
            return datalist, displaylist

    def run(self, edit, withinProj=False, refTypeToGet='all'):

        # The refTypeToGet and withinProj vars must be set in the sublime command calls to this routine
        if refTypeToGet not in ['label', 'doc', 'term', 'all']:
            refmate_utils.showRefMateError("Oops. Programming error. Incorrect [{}] setting for refTypeToGet parameter".format(refTypeToGet))
            return

        self.datalist = []
        self.displaylist = []

        # Perform some initial environment checks
        # `- Are we in a sphinx project and a restructured text scope?
        subl_top_folder_path = self.view.window().extract_variables()["folder"]
        docScope = self.view.scope_name(self.view.sel()[0].begin())
        refmate_settings = sublime.load_settings(refmate_utils.plugin_settings_file)
        proj_plugin_settings = sublime.active_window().active_view().settings().get(refmate_utils.plugin_canon_name, {})
        # any SphinxRefmate settings in the .sublime-project file will override same name Default/User settings
        refmate_settings.update(proj_plugin_settings)
        if not refmate_utils.sphinx_and_rst_checks(subl_top_folder_path, docScope, refmate_settings):
            return

        mapFinder = IntersphinxMapFinder(subl_top_folder_path, refmate_settings)
        if not mapFinder.OK:
            refmate_utils.showRefMateError('Error searching for intersphinx mapping: {}'.format(mapFinder.errorStr()))
            mapFinder = None
            return

        honedSphinxMap = HonedIntersphinxMap(mapFinder.intersphinx_mapping(), subl_top_folder_path, refmate_settings)
        if not honedSphinxMap.OK:
            refmate_utils.showRefMateError('Cannot process intersphinx_mapping at: {}\n\n {}'.format(mapFinder.sourceFile(), honedSphinxMap.errorStr()))
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
                sublime.status_message("Parsing {} entries (for intersphinx key/name: {})".format(OI, thisKey))
                curProj = False
                if thisKey == honedSphinxMap.curProjKey:
                    curProj = True
                    # add asterix to easily identify local project in the display
                    # prefixToDisplay = '*' + prefixToDisplay
                # build data/display lists for each required project
                datal, displ = InsertSphinxLinksCommand.fetch_inv_lists(OI, refTypeTarget=refTypeToGet, intersphinx_key=thisKey, is_cur_proj=curProj)
                self.datalist += datal
                self.displaylist += displ

        if not self.datalist:
            refmate_utils.showRefMateError('No [{}] entries found in {}'.format(refTypeToGet, OI))
            return
        elif len(self.datalist) == len(self.displaylist):
            sublime.status_message("Found {} {} entries to display.".format(len(self.datalist), refTypeToGet))
            sublime.active_window().show_quick_panel(
                self.displaylist, 
                self.on_done
            )
        else:
            refmate_utils.showRefMateError('Data mismatch in retrieving [{}] entries from {}'.format(refTypeToGet, OI))
            return
