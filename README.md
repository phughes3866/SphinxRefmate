# SphinxRefmate
# HTML, CSS, JavaScript, JSON, React and Vue code formatter for Sublime Text 2 and 3 via node.js
#### [Sublime Text 3](http://www.sublimetext.com/3)
#### [JS-beautify](https://github.com/einars/js-beautify)
#### [Node.js download](http://nodejs.org/#download)

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
Tools -> Command Palette (`Cmd+Shift+P` or `Ctrl+Shift+P`) and type `sphinx-refmate`.

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

## Settings
Plugin settings can be edited via `Preferences` -> `Package Settings` -> `Sphinx Refmate`, which presents a twin panel of default/user settings.

### 
