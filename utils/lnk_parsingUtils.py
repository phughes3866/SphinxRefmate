from .lnk_loggingUtils import getLogger; logger = getLogger(debug=True)
import importlib.machinery
import importlib.util
import threading
import logging
import sublime
from .lnk_ioUtils import exceptionDetails
from .lnk_dictUtils import dictContentsChecker, mandatoryKeyChecker

defaultPluginName = __package__.split('.')[0]

def get_user_plugin_settings(pluginName: str = defaultPluginName,
                               pluginSettingsFileName: str = ""):
    if not pluginSettingsFileName:
        pluginSettingsFileName = f"{pluginName}.sublime-settings"
    # use sublime's 'load_settings' to get a combo of the default plugin settings and user plugin settings overrides
    pluginUserSettings = sublime.load_settings(pluginSettingsFileName).to_dict()
    return pluginUserSettings

def get_project_plugin_settings(pluginName: str = defaultPluginName):
    # return any current project settings under the 'pluginName' key (in the sublime-project file)
    return sublime.active_window().active_view().settings().get(pluginName, {})

def get_combo_plugin_settings(pluginName: str = defaultPluginName,
                               pluginSettingsFileName: str = ""):
    """
    return a dictionary with the plugin settings for "pluginName"
    """
    pluginUserSettings = get_user_plugin_settings(pluginName, pluginSettingsFileName)
    cur_proj_plugin_overrides = get_project_plugin_settings(pluginName)
    # combine setting dicts so any current project settings will override same name Default/User 
    # `- settings from the plugin's .sublime-settings files
    return dict(pluginUserSettings, **cur_proj_plugin_overrides)

def getSettingsVars(varNames: list, plusMode=False, userSettings=True):
    """
    Return a block (dictionary) of plugin settings values corresponding to varName settings
    The block of settings requested, should be one of three 'settingsVarProfiles'
    Profile A: User settings allowing project settings overrides (plusMode=False, userSettings=True)
    Profile B: Purely project defined settings (userSettings=False)
    Profile C: User settings allowing project settings extensions (plusMode=True, userSettings=True)
    Any settings values which can't be satisfactorily calculated, are returned with value set to None
    """
    if not userSettings:
        # Type B settings vars requested (from project settings only)
        retDict = {k: v for k, v in get_project_plugin_settings().items() if k in varNames}
    elif not plusMode:
        # Type A settings vars requested (from user settings with project settings overrides)
        retDict = {k: v for k, v in get_combo_plugin_settings().items() if k in varNames}
    else:
        # Type C settings vars requested (from user settings with project settings {}_plus extensions)
        allUserSettings = get_user_plugin_settings()
        allProjectSettings = get_project_plugin_settings()
        plusMap = {k: k + '_plus' for k in varNames}
        retDict = {}
        for key, plusKey in plusMap.items():
            if key in allProjectSettings:
                # project settings contain both key and plusKey values
                # this is probably a bit of a user misuse/mistake with the settings
                # nevertheless, make an override adjustment before attempting the extension
                allUserSettings[key] = allProjectSettings[key]
            # Now seeking to extend varName(in user/override settings) with varName_plus(in project settings)
            if plusKey in allProjectSettings:
                # we have a project settings extension variable (varName_plus)
                if key not in allUserSettings:
                    # but we don't have a regular/underlying user settings varName
                    logger.debug(f'Cannot extend non-existent user setting: {key}')
                else:
                    # we have both the user 'varName' and its intended project 'varName_plus' extension
                    # For extension to be possible, the type of these two varNames must match
                    keyVType = type(allUserSettings[key])
                    plusKeyVType = type(allProjectSettings[plusKey])
                    # logger.debug(f'Attempting to combine {key}[{keyVType}] '
                                 # f'with {plusKey}[{plusKeyVType}]')
                    if keyVType != plusKeyVType:
                        logger.error(f'Config problems: Cannot combine {key}[{keyVType}] '
                                     f'with {plusKey}[{plusKeyVType}]')
                        retDict[key] = allUserSettings[key]
                    elif keyVType is dict:
                        retDict[key] = dict(allUserSettings[key], **allProjectSettings[plusKey])
                    elif keyVType is list:
                        retDict[key] = list(allUserSettings[key] + allProjectSettings[plusKey])
                    else:
                        logger.debug(f'Cannot combine two items of type: {keyVType} '
                                      '(only dicts and lists can combine)')
                        # makes sense to use the underlying user settings value, in this case
                        retDict[key] = allUserSettings[key]
            elif key in allUserSettings:
                logger.debug(f'Only orig {key}={allUserSettings[key]} (no {plusKey})')
                # makes sense to use the underlying user settings value, in this case
                retDict[key] = allUserSettings[key]
            else:
                logger.debug(f'No orig {key} and no {plusKey}')
    # Mop up: set varNames to 'None' for missing/incalculable values
    # for k in varNames:
        # if k not in retDict:
            # retDict[k] = None
    return retDict

def getSettingsVarsByType(Atypes: list,
                          Btypes: list,
                          Ctypes: list):
    retDict = {}
    if Atypes:
        retDict = dict(retDict, **getSettingsVars(Atypes, plusMode=False, userSettings=True))
    if Btypes:
        retDict = dict(retDict, **getSettingsVars(Btypes, userSettings=False))
    if Ctypes:
        retDict = dict(retDict, **getSettingsVars(Ctypes, plusMode=True, userSettings=True))
    return retDict


class pluginSettingsManager:
    """
    Singleton class to manage plugin settings.
    - Loads settings schema dictionary on singleton initiation
    - As part of the initiation, the schema is used to perform checks on both user and sublime project settings,
      for the plugin. These checks can include flagging missing mandatory variables and also checking that
      variables are defined with the correct type/format
    - Provides [get, getOne, getAll] methods for retrieving settings
    - All 'get{}' methods are guaranteed to return a value for the setting(s) requested
      -- if the setting is not defined in the settings file, then a default value
      -- as defined in the schema, will be used if available. If no default value
      -- is available the 'get{}' method will return None for that setting.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        # ensures the same, single instance of the object is returned on
        # each call to the class i.e. this is a singleton pattern
        if cls._instance is None:
            # this is the first call to the class, we must initialise our singleton settings holder
            with cls._lock:
                if not cls._instance:
                    # create a new 'bare' pluginSettingsManager class object
                    # same as: cls._instance = super().__new__(cls)
                    cls._instance = object.__new__(cls)
                    # initialise our singleton pluginSettingsManager object
                    cls._instance._initialize(*args, **kwargs)
                    print('making a new pluginSettingsManager object')
        else:
            print('returning pre-genned pluginSettingsManager object')
            # this is the second (or later) call to the object
            # return the class object that was previously generated
            pass
        return cls._instance

    def _initialize(self, settingsSchema: dict):
        self.bigSchema = settingsSchema
        self.theAs = [k for k,v in self.bigSchema.items() if v.get('profile') == 'A']
        self.theBs = [k for k,v in self.bigSchema.items() if v.get('profile') == 'B']
        self.theCs = [k for k,v in self.bigSchema.items() if v.get('profile') == 'C']
        self.userOrProjMands = [k for k,v in self.bigSchema.items() if not 'default' in v and not k in self.theBs]
        self.projMands = [k for k,v in self.bigSchema.items() if not 'default' in v and k in self.theBs]
        self.theDefaults = {k:v['default'] for k, v in self.bigSchema.items() if 'default' in v}

        # compile check dicts for user settings file and project settings (sublime-project) files
        # Process type A settings
        self.userSettingsChecks = {k:v['checks'] for k, v in self.bigSchema.items() if 'checks' in v and k in self.theAs}
        self.projSettingsChecks = {k:v['checks'] for k, v in self.bigSchema.items() if 'checks' in v and k in self.theAs}
        
        # Process type B settings
        self.projSettingsChecks = dict(self.projSettingsChecks, **{k:v['checks'] for k, v in self.bigSchema.items() if 'checks' in v and k in self.theBs})

        # Process type C settings
        for k in self.theCs:
            if 'checks' in self.bigSchema[k]:
                self.userSettingsChecks[k] = self.bigSchema[k]['checks']
                self.projSettingsChecks[k+'_plus'] = self.bigSchema[k]['checks']

        userSettingsDict = get_user_plugin_settings()
        dCheck = dictContentsChecker(userSettingsDict, self.userSettingsChecks)
        print(f'User settings check OK?: {dCheck.isOK()}')
        print(f'User settings errors: {dCheck.getErrorList()}')

        projSettingsDict = get_project_plugin_settings()
        dCheck = dictContentsChecker(projSettingsDict, self.projSettingsChecks)
        print(f'Proj settings check OK?: {dCheck.isOK()}')
        print(f'Proj settings errors: {dCheck.getErrorList()}')

        missingUserMands = mandatoryKeyChecker(get_combo_plugin_settings(), self.userOrProjMands)
        missingProjMands = mandatoryKeyChecker(get_project_plugin_settings(), self.projMands)

        # logger.info(f'user settings checks = {self.userSettingsChecks}')
        # logger.info(f'proj settings checks = {self.projSettingsChecks}')
        logger.info(f'missing user settings = {missingUserMands}')
        logger.info(f'missing proj settings = {missingProjMands}')
        # return self

    def addDefaults(self, inDict, varList, addNones=True):
        for varName in varList:
            if not varName in inDict:
                if varName in self.theDefaults:
                    inDict[varName] = self.theDefaults[varName]
                elif addNones:
                    inDict[varName] = None
        return inDict

    def get(self, varNames: list, addDefaults=True):
        Atypes = []
        Btypes = []
        Ctypes = []
        for var in varNames:
            if var in self.theAs:
                Atypes += [var]
            elif var in self.theBs:
                Btypes += [var]
            elif var in self.theCs:
                Ctypes += [var]
        retDict = getSettingsVarsByType(Atypes, Btypes, Ctypes)
        retDict = self.addDefaults(retDict, varNames)
        return retDict

    def getOne(self, varName: str, addDefaults=True):
        return self.get([varName], addDefaults)[varName]

    def getAll(self, addDefaults=True):
        retDict = getSettingsVarsByType(self.theAs, self.theBs, self.theCs)
        if addDefaults:
            for k, v in self.theDefaults.items():
                if not k in retDict:
                    retDict[k] = v
        return retDict

def getPyFileVars(pyFilePathStr: str, varNames: list):
    """
    Dynamically + temporarily import a python sourcefile/module.
    Extract a list of varnames from the temp module (set value to 'None' for non-existent varnames)
    Delete the temp module (so it will be garbage collected).
    Return a tuple with the variables requested.
    Set all variable values to 'None' if major error occurs e.g. source file not readable
    Warning: This function will run/import the code in pyFilePathStr
           : Ensure that you trust any file you pass to this function
           : Consider parsing untrusted source code differently, e.g. with python's 'ast' module
           : `- if you wish to extract data from potentially unsafe code
    """
    try:
        loader = importlib.machinery.SourceFileLoader( 'temp_py_mod', pyFilePathStr )
        spec = importlib.util.spec_from_loader( 'temp_py_mod', loader )
        temp_py_mod = importlib.util.module_from_spec( spec )
        loader.exec_module( temp_py_mod )
    except Exception as err:
        logger.error(f'{exceptionDetails(err)}')
        return (None,) * len(varNames)
    else:
        resList = []
        for varName in varNames:
            resList.append(getattr(temp_py_mod, varName, None))
        return tuple(resList)
