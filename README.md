<!-- [![Package Control](https://img.shields.io/packagecontrol/dt/SphinxRefmate?style=flat-square)](https://packagecontrol.io/packages/SphinxRefmate) -->
[![GitHub tag (latest SemVer)](https://img.shields.io/github/tag/phughes3866/SphinxRefmate?style=flat-square&logo=github)](https://github.com/phughes3866/SphinxRefmate/tags)
[![Project license](https://img.shields.io/github/license/phughes3866/SphinxRefmate?style=flat-square&logo=github)](https://github.com/phughes3866/SphinxRefmate/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/phughes3866/SphinxRefmate?style=flat-square&logo=github)](https://github.com/phughes3866/SphinxRefmate/stargazers)
[![Donate to this project using Paypal](https://img.shields.io/badge/paypal-donate-blue.svg?style=flat-square&logo=paypal)](https://www.paypal.me/mrpaulhughes/5gbp)

# SphinxRefmate

> "A referencing toolkit to assist with writing Sphinx Documentation projects in restructured text."

## About
sphinx-refmate is a sublime Text 3 and 4 plugin designed to be a minimal hassle reference manager during the development of Sphinx Documentation projects in restructured Text. The plugin gathers references from Sphinx projects, on demand, and presents these to the user in the form of a Sublime Text quick-menu. This menu can be fuzzy-searched so that a reference can be easily located, clicked and thereby inserted into the current document in the correct format.

The following types of references can be gathered and input:

* Section labels/references (reST `:ref:`)
* Page references (reST `:doc:`)
* Glossary terms (reST `:term:`)
* Bibliography citations (reST `[author_1966]_`)
* Substitutions (reST `|subst|`)

## Installation
Installation should be carried out using the [Sublime Package Manager](http://wbond.net/sublime_packages/package_control). 

* `Ctrl+Shift+P` or `Cmd+Shift+P` in Linux/Windows/OS X
* type `install`, select `Package Control: Install Package`
* type `sphinx`, select `sphinx-refmate`

## Usage
Tools -> Command Palette (`Cmd+Shift+P` or `Ctrl+Shift+P`) and type `Sphinx Refmate`.

-- or --

Use the pre-set key bindings (Note: Might not work if these are overridden by other plugins in your setup):

* Insert local project ref/doc/term references: `Ctrl+Alt+I` (or `Cmd+Alt+I` if you're on a Mac).
* Insert multi project ref/doc/term references: `Ctrl+Alt+O` (or `Cmd+Alt+O` if you're on a Mac).
* Insert bibliography citations: `Ctrl+Alt+L` (or `Cmd+Alt+L` if you're on a Mac).
* Insert reST substitutions: `Ctrl+Alt+K` (or `Cmd+Alt+K` if you're on a Mac).

-- or --

Use the context menu:

Right click in the current buffer and select `Sphinx Refmate` -> `submenus`.

Note: The context menu is context sensitive and will only show when you're in a `text.restructuredtext` scope.

-- or --

Use the main topbar menu in Sublime Text: `Tools` -> `Sphinx Refmate` -> `submenus`

## Plugin Settings
Plugin settings can be edited via `Preferences` -> `Package Settings` -> `Sphinx Refmate`, which presents the standard twin panel of default/user settings.

### "sphinx_check": true
This setting determines whether to check we're in a sphinx project before running plugin features (checks for top folder conf.py)

### "rst_check": true
This setting determines whether to check we're in a restructured text context (scope) before running plugin features.

**NOTE:**  _Sphinx Refmate's right-click context menu is set to only be displayed in restructured text scopes, regardless of how "rst_check" is set._

### "intersphinx_map_source_list": ["filename1.py", "filename2.py"]


### "bib_ref_file_list": ["filename1.rst", "filename2.rst"]
When called upon to do so, SphinxRefmate scans, in turn, **all** of the files in the _bib_ref_file_list_ in order to compile a list of restructured text citations. The citations sought are those of a standard restructured text variety, see [docutils reST/citations](https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#citations) for more details. Note that this feature is designed to function solely within one project, which is in line with the intra-project manner in which sphinx treats reST citations.

### "rst_epilog_source_list": ["filename1.py", "filename2.py"]
When called upon to do so, SphinxRefmate scans, in turn, **all** of the files in the _rst_epilog_source_list_ in order to compile a list of restructured text substitutions from those defined in all ``rst_epilog =`` or ``rst_epilog +=`` statements. The substitutions sought are those defined according to restructured text standards, see [docutils reST/substitutions](https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#substitution-definitions) for more details. Note that this feature is designed to function solely within one project, which is in line with the intra-project manner in which sphinx treats reST substitutions.



## Per Project Plugin Settings
All of SphinxRefmate's file list settings can be overridden on an individual sublime text project basis, if required, 
by placing an entry such as the following, within the 'settings' section of the project's sublime-project file::

```json
"SphinxRefmate": { 
	"intersphinx_map_source_list": [ "/strangely/located/conf.py" ],
	"bib_ref_file_list": [ "../commondata/suite_bibliography.rst" ],
	"rst_epilog_source_list": [ "../commondata/rstepilog_include.py" ]
			}
```
