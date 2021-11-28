import os
import sys
import re
import ast
import sublime
import sublime_plugin
sys.path.insert(0, os.path.dirname(__file__))
import refmate_utils


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
        args = {}
        args['contents'] = self.insert_list[index]
        self.view.run_command('insert_snippet', args)

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
        self.insert_list = []
        self.display_list = []

        # Perform some initial environment checks
        # `- Are we in a sphinx project and a restructured text scope?
        subl_top_folder_path = self.view.window().extract_variables()["folder"]
        docScope = self.view.scope_name(self.view.sel()[0].begin())
        refmate_settings = sublime.load_settings(refmate_utils.plugin_settings_file)
        if not refmate_utils.sphinx_and_rst_checks(subl_top_folder_path, docScope, refmate_settings):
            return

        cite_file_list = refmate_settings.get('bib_ref_file_list', [])
        # The project's 'bib_ref_file_list' gets appended i.e. adds to rather than replaces any plugin's list
        proj_plugin_settings = sublime.active_window().active_view().settings().get('sphinx-refmate')
        if proj_plugin_settings:
            extra_cite_file_list = proj_plugin_settings.get('bib_ref_file_list', [])
            if extra_cite_file_list and type(extra_cite_file_list) == list:
                cite_file_list.extend(extra_cite_file_list)
        if not cite_file_list:
            refmate_utils.showRefMateError("Unable to run as no bibliography files were provided in the settings.\n\n"
                "sphinx-refmate is not currently configured for citation insertions.")
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
                self.insert_list.append("[{}]_ ".format(cit))
                self.display_list.append("[{}] = {}".format(cit, ref))
            sublime.status_message(parsing_status_msg)
            sublime.active_window().show_quick_panel(
                self.display_list, 
                self.on_done
            )
        else:
            refmate_utils.showRefMateError("No references found in the searched files: {}\n\n"
                "Check that your settings point to where your bibliography entries are located.".format(cite_file_list))


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
        args = {}
        args['contents'] = self.insert_list[index]
        self.view.run_command('insert_snippet', args)

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
                    except Exception as err:
                        print('Cannot evaluate ast expression [{}]. Gave error: {}'.format(x.value, err))
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
        # Perform some initial environment checks
        # `- Are we in a sphinx project and a restructured text scope?
        subl_top_folder_path = self.view.window().extract_variables()["folder"]
        docScope = self.view.scope_name(self.view.sel()[0].begin())
        refmate_settings = sublime.load_settings(refmate_utils.plugin_settings_file)
        if not refmate_utils.sphinx_and_rst_checks(subl_top_folder_path, docScope, refmate_settings):
            return

        # Pre-populate our display/insert lists with some standard Sphinx replacements
        self.insert_list = ["|release| ",
                            "|version| "]
        self.display_list = ["|release| STD conf.py: full version str e.g. 2.5.2b3",
                            "|version| STD conf.py: major + minor versions e.g. 2.5"]

        sphinx_rst_epilog_files = refmate_settings.get('rst_epilog_source_list', [])
        # The project's 'extra_rst_epilog_source_list' gets appended i.e. adds to rather than replaces any plugin's list
        proj_plugin_settings = sublime.active_window().active_view().settings().get('sphinx-refmate')
        if proj_plugin_settings:
            sphinx_rst_epilog_files.extend(proj_plugin_settings.get('extra_rst_epilog_source_list', []))
        if not sphinx_rst_epilog_files:
            refmate_utils.showRefMateError("Search file list for rst_epilog entries is empty.\n\n"
                "sphinx-refmate is not configured for automatic rst_epilog insertions at this time.\n\n"
                "Please update the sphinx-refmate plugin settings if you wish to implement this feature.")
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
                        # sublime.status_message("No rst_epilog in {}".format(f))
                    else:
                        convertedRstEpilog = self.get_rst_epilog_2part_replacement_dict(oneRstEpilog)
                        if convertedRstEpilog:
                            for shorty, longy in convertedRstEpilog.items():
                                self.insert_list.append("|{}| ".format(shorty))
                                self.display_list.append("|{}| = {}".format(shorty, longy))
            parsing_status_msg = "{} replacements loaded from {} rst_epilog locations"\
                                        .format(len(self.display_list) - 2, len(sphinx_rst_epilog_files))
            if missing_filecount > 0 or empty_filecount > 0:
                parsing_status_msg += ": Warning: {} missing/{} empty files".format(missing_filecount, empty_filecount)

            sublime.status_message(parsing_status_msg)
            # There will always be something to display as this routine inserts several of sphinx's own standard replacements
            sublime.active_window().show_quick_panel(
                self.display_list, 
                self.on_done
            )
