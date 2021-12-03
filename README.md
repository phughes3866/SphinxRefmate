[![Package Control](https://img.shields.io/packagecontrol/dt/SphinxRefmate?style=flat-square)](https://packagecontrol.io/packages/SphinxRefmate)
[![GitHub tag (latest SemVer)](https://img.shields.io/github/tag/phughes3866/SphinxRefmate?style=flat-square&logo=github)](https://github.com/phughes3866/SphinxRefmate/tags)
[![Project license](https://img.shields.io/github/license/phughes3866/SphinxRefmate?style=flat-square&logo=github)](https://github.com/phughes3866/SphinxRefmate/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/phughes3866/SphinxRefmate?style=flat-square&logo=github)](https://github.com/phughes3866/SphinxRefmate/stargazers)
[![Donate to this project using Paypal](https://img.shields.io/badge/paypal-donate-blue.svg?style=flat-square&logo=paypal)](https://www.paypal.me/mrpaulhughes/5gbp)

# SphinxRefmate

> "A referencing toolkit to assist with the creation of Sphinx Documentation projects in restructured text."

## About
SphinxRefmate is a Sublime Text plugin designed as a minimal hassle reference manager for use in the development of Sphinx Documentation projects in restructured Text. The plugin can gather a variety of reference types from Sphinx projects, on demand, and present these to the user in the form of a Sublime Text quick-panel. This menu can be fuzzy-searched so that a reference can be easily located, and clicked. This will then insert the correct piece of restructured text into the current document, at the current cursor position, in the correct format e.g. a citation reference pointing to the desired citation.

### Reference Types Supported
The following reference types can be gathered from within the currently active Sphinx Doc project:

* Bibliography citations (reST `[author_1966]_`)
* Substitutions (reST `|subst|`)

The following reference types can be gathered from the local Sphinx Doc project, **and additionally** any associated Sphinx Doc projects identifiable through the active `intersphinx_mapping` variable:

* Section labels/references (reST `:ref:`)
* Page references (reST `:doc:`)
* Glossary terms (reST `:term:`)

### Save Time and Head Scratching
If, for example, you are editing a restructured text page of a Sphinx Docs web project, and you want to insert a hyperlink to a page you created about 'London Buses' a few weeks ago, you can simply press `<ctrl><alt>I` (`<cmd><alt>I` on Mac) and a list will be brought up which includes all the doc (page) links in the current Sphinx project. You can then begin typing _'London Bu..'_ in the selection header of the quick-panel, and in doing so the precise 'doc' style link you require will become visible through the filtering, and you can click on it to insert a nicely formatted reST link. (N.B. Regular Sublime Text menus, as well as configurable key bindings, are available for all the Sphinx Refmate commands.)

## Installation
Installation should be carried out using the [Sublime Package Manager](http://wbond.net/sublime_packages/package_control). 

* `Ctrl+Shift+P` or `Cmd+Shift+P` in Linux/Windows/OS X
* type `install`, select `Package Control: Install Package`
* type `sphinx`, select `SphinxRefmate`

It is also possible to clone from the [SphinxRefmate](https://github.com/phughes3866/SphinxRefmate) github repository directly into your Sublime Text **Packages** directory.

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

## Key Bindings
Plugin key bindings can be edited via `Preferences` -> `Package Settings` -> `Sphinx Refmate`, which presents the standard twin panel of default/user key bindings. 

## Settings
Plugin settings can also be edited via `Preferences` -> `Package Settings` -> `Sphinx Refmate`. Below is a list of all the available SphinxRefmate settings, and their impact on plugin functionality.

### "sphinx_check": true
This setting determines whether Sphinx Refmate will check if it's running in a Sphinx Doc project before running plugin features (checks for top folder conf.py). Set to `false` to run in any environment.

### "rst_check": true
This setting determines whether Sphinx Refmate will check if the edit cursor is in a restructured text context (scope) before running plugin features. Set to `false` to run in any scope.

**NOTE:**  _Sphinx Refmate's right-click context menu is set to only be displayed in restructured text scopes, regardless of how "rst_check" is set._

### "priv_project_prefix": "priv"
Sphinx Refmate utilises an 'intersphinx_mapping' variable (see below) within which Sphinx Doc projects are defined by a short name key. If this name key begins with the _priv_project_prefix_ (default 'priv'), then Sphinx Refmate will consider this project private rather than public e.g. a local lan based html site rather than internet based. It is important for Sphinx Refmate to differentiate between private and public projects as unreachable links to private sites should not be offered up for insertion when editing public sites. 

### "intersphinx_map_source_list": ["filename1.py", "filename2.py"]
SphinxRefmate locates reST `:ref:`, `:doc:` and `:term:` style references by parsing a Sphinx Doc database file called `objects.inv`. This file usually resides at the root of the Sphinx Doc build tree and is an integral feature of the Sphinx project build process. The way Sphinx Refmate understands where to look for this or that project's `objects.inv` file is via the _intersphinx_mapping_ dictionary, which is usually defined in a Sphinx Doc project's `conf.py`. The `intersphinx_map_source_list` is used to provide a list of file locations in which the necessary _intersphinx_mapping_ variable is likely to be found. Sphinx Refmate parses these files in turn and uses the first _intersphinx_mapping_ variable found in order to locate `objects.inv` files for some or all of the projects therein defined. When an `objects.inv` file is located, Sphinx Refmate parses it to build a reference list. This is a reference list for one Sphinx Doc project, and Sphinx Refmate can use this, on its own or along with other such lists, to populate the quick-panel.

**Note:** _The intersphinx_mapping variable is normally associated with the Sphinx Doc Intersphinx extension, and its main function is to associate/map a number of Sphinx Doc project names (actually short aliases) to the filepath location of their objects.inv file, in order that Intersphinx can manage multiple project cross referencing at build time. The Sphinx Refmate Sublime Text plugin uses this same intersphinx_mapping variable to make manageing multiple project cross referencing at design time significantly easier. To use Sphinx Refmate successfully across multiple projects you need to have a modicum of understanding concerning the design of an intersphinx_mapping variable. See the section on intersphinx_mapping variables below, if required._

### "bib_ref_file_list": ["filename1.rst", "filename2.rst"]
When called upon to do so, SphinxRefmate scans, in turn, **all** of the files in the _bib_ref_file_list_ in order to compile a list of restructured text citations. The citations sought are those of a standard restructured text variety, see [docutils reST/citations](https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#citations) for more details. Note that this feature is designed to function solely within one project, which is in line with the intra-project manner in which sphinx treats reST citations, see: [Sphinx Doc citations](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#citations).

### "rst_epilog_source_list": ["filename1.py", "filename2.py"]
When called upon to do so, SphinxRefmate scans, in turn, **all** of the files in the _rst_epilog_source_list_ in order to compile a list of restructured text substitutions from those defined in all `rst_epilog =` or `rst_epilog +=` assignment statements. These files should be python source code files, and it is likely that you may need only one defined - the standard Sphinx Docs configuration file: `conf.py`. The substitutions sought within any discovered `rst_epilog` variable are those defined according to restructured text standards, see [docutils reST/substitutions](https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#substitution-definitions) for more details. Note that this feature is designed to function solely within one project, which is in line with the intra-project manner in which Sphinx Docs treats reST substitutions. Note also that Sphinx Docs `rst_prolog` variables are currently not parsed (if these variables are a source of reST substitutions in your project, then you will need to transfer them to `rst_epilog` variables). For more details on Sphinx rst_epilog and rst_prolog variables, see the [Sphinx configuration docs](https://www.sphinx-doc.org/en/master/usage/configuration.html)

## Per Project Plugin Settings
All of SphinxRefmate's file list settings can be overridden on an individual sublime text project basis, if required, 
by placing an entry such as the following, within the 'settings' section of the project's sublime-project file::

```json
"SphinxRefmate": { 
	"intersphinx_map_source_list": [ "/strangely/located/conf.py" ],
	"bib_ref_file_list": [ "../commondata/suite_bibliography.rst" ],
	"rst_epilog_source_list": [ "../commondata/rstepilog_include.py" ],
	"cur_proj_intersphinx_map_name": "sqsh"
			}
```

### "cur_proj_intersphinx_map_name": "mysite"

An additional Sphinx Refmate setting is definable at project level, which is not available in the Default/User settings. This is the `cur_project_intersphinx_map_name`. This gives Sphinx Refmate an assured way of identifying the current project line within the intersphinx_mapping variable. Note that it is not necessary to implement this setting as Sphinx Refmate has a fairly robust way of working out which intersphinx_mapping line relates to the current project. However, you should definitely set this variable to overcome any errors that Sphinx Refmate might report concerning an inability to identify the current project.

## Quick Panel Display Key

For lists of ref/doc/term type references, lines in the quick panel will be prefixed by the intersphinx_mapping name of the project being referenced e.g. `myproj>`. Additionally there will be an asterix prefix e.g. `*myproj>` to denote the current project (the one which is currently being edited).

For lists of citation/substitution type references there will be no prefixes. These types of references always come from the current project under edit.

## The intersphinx_mapping Variable

SphinxRefmate uses _intersphinx_mapping_ variables, and the `objects.inv` files to which they point, for the purpose of enabling documentation writers to better manage referencing. An intersphinx_mapping variable which manages cross referencing for three Sphinx Doc projects may look something like this:

```python
intersphinx_mapping = {
	'rug': ('https://rugby.org', ('_build/html/objects.inv', '../commondata/rug_objects.inv')),
	'sqsh': ('https://squash.org', ('_build/html/objects.inv', '../commondata/sqsh_objects.inv')),
	'can': ('https://canasta.org', ('_build/html/objects.inv', '../commondata/canny_objects.inv'))
	}
```

The ability to provide multiple targets for the inventory, as above, came about with Sphinx Docs v1.3. This is the type of intersphinx_mapping that Sphinx Refmate uses and expects to be defined. Sphinx Refmate only looks for filepath locations of objects.inv files. The Sphinx Intersphinx extension allows for objects.inv files to be found at website locations, but Sphinx Refmate skips any such settings in the intersphinx_mapping variable (the design choice to do this was made with respect to referencing speed). More information on Intersphinx and the intersphinx_mapping variable can be found in the [Sphinx Intersphinx Extension Documentation](https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html).

**Note:** _If you only work on a single Sphinx Docs project, and don't want to cross reference any others, there is no need to have the Intersphinx extension running. To meaningfully use Sphinx Refmate on such a project you will still need an intersphinx_mapping variable defined._

A Sphinx Refmate supporting intersphinx_mapping variable, for a single non-cross-referencing project, will probably be defined in conf.py and look something like the following:

```python
intersphinx_mapping = {'cpract': ('https://choir.practice.org',
                                  ('_build/html/objects.inv', '../commondata/cpo_objects.inv'))}
```

#### objects.inv file management
The Sphinx Doc build process dumps a project's `objects.inv` file at the build root. For html builds this usually means the _\_build/html_ directory. In the above intersphinx_mapping examples you can see that the first location given for the inventory file, in each case, is this standard location. Build directories are regularly cleared however, and they may even be empty when you are merrily working in Sublime Text to edit your source files. In such a case, if you try to activate the `objects.inv` dependent features of Sphinx Refmate, it will fail.

One effective way to ensure that Sphinx Refmate cross referencing is always fully available, is to regularly copy a project's `objects.inv` file from the standard location to a safer one. A systemd timer or cron job could be set up to do this. In these safer locations (such as ../commondata in the above examples) `objects.inv` files will be more permanently available.

## Some issues with cross-project Sphinx Doc referencing and the intersphinx_mapping variable

**Note:** _An intersphinx_mapping shortname for a project is a shorthand way for identifying a project which is chosen by the user when setting up the mapping._

#### Identifying the current project
Sphinx Refmate needs to be able to identify the local Sphinx Doc project in which it is running, and associate this with an entry in the intersphinx_mapping. This is required because often Sphinx Refmate is called upon to provide references for the current project only.

#### Identifying which Sphinx Doc projects are private (e.g. lan based) or public (e.g. internet based)
Sphinx Refmate needs to understand whether a Sphinx Doc project is private or public because it makes no sense to insert unreachable links to private resources into a public site (for html website builds).

## Editing an existing Sphinx Doc project to utilise Sphinx Refmate
Considering what is written above, an existing Sphinx Doc project may need to undergo some slight modifications if its developers want to begin using Sphinx Refmate. The types of modification that may need to happen are:

* Changing or implementing the intersphinx_mapping variable and ensuring it contains robust paths to `objects.inv` files.
* Changing the 'shortnames' for projects in the intersphinx_mapping so that they accord with notions of private/pubic as discussed. If this is the case then changing all connected references across the reST source files will also be necessary.
