from .lnk_loggingUtils import getLogger; logger = getLogger(debug=True)
import sublime
from typing import Union, Tuple

# def removeUnwantedDictKeys(dTarget: dict, wantedKeys: Union[dict, list]) -> dict:
#     if type(wantedKeys) is dict:
#         wantedKeys = wantedKeys.keys()
#     return {k: v for k, v in dTarget.items() if k in wantedKeys}

# def addDefaultsToDict(dTarget: dict, dDefaults: dict, forceDefaults: bool = False) -> dict:
#     for k, v in dDefaults.items():
#         if not k in dTarget or forceDefaults:
#             dTarget[k] = v
#     return dTarget

# def checkMandKeysInDict(dTarget: dict, mandatoryKeys: Union[dict, list]) -> Tuple[bool, list]:
#     if type(mandatoryKeys) is dict:
#         mandatoryKeys = mandatoryKeys.keys()
#     errList = []
#     for k in mandatoryKeys:
#         if k not in dTarget:
#             errList += [k]
#     return ( not bool(errList), errList)

# def mergeDicts(ADict: dict, BDict: dict, reverseBOverrideKeys: list = []) -> dict:
#     for k in reverseBOverrideKeys:
#         if k in BDict:
#             ADict[k] = BDict[k]
#     # combine dicts so that ADict keys pairs override any same keys in BDict
#     BDict.update(ADict) 
#     return BDict

#####################################################################################################
# Basic '_basicTestMap' functions to check types of values in dictionary entries                          #
# `- These simply return True/False dependent on check passing/failing.                             #
#  - The corresponding 'failStr' is contained within the _basicTestMap which points to the function. #
#####################################################################################################

def is_list_shaped_so(lst,
                    mustBeEmpty: bool = False,
                    mustHaveContent: bool = False,
                    contentType: type = None) -> bool:
    """
    Returns True if 'lst' is shaped as per the given parameters. False otherwise.
    """
    if type(lst) == list:
        if mustBeEmpty and len(lst):
            return False
        elif mustHaveContent and not len(lst):
            return False
        elif len(lst) and type(contentType) == tuple:
            return all(type(elem) in contentType for elem in lst)
        else:
            return True
    else:
        return False

def is_dict_shaped_so(dct,
                    mustBeEmpty: bool = False,
                    mustHaveContent: bool = False,
                    contentType: type = None) -> bool:
    """
    Returns True if 'dct' is shaped as per the given parameters. False otherwise.
    """
    if isinstance(dct, dict):
        if mustBeEmpty and bool(dct):
            return False
        elif mustHaveContent and not bool(dct):
            return False
        elif bool(dct) and type(contentType) == tuple:
            return all(type(v) in contentType for k, v in dct.items())
        else:
            return True
    else:
        return False

_basicTestMap = {
    "is_bool":                  (lambda val: type(val) == bool, "Must be a boolean value."),
    "is_int":                   (lambda val: type(val) == int, "Must be an integer."),
    "is_tuple":                 (lambda val: type(val) == tuple, "Must be a tuple."),
    "is_str":                   (lambda val: type(val) == str, "Must be a character string."),
    "is_list":                  (lambda val: type(val) == list, "Must be a list."),
    "is_dict":                  (lambda val: type(val) == dict, "Must be a dictionary."),
    "is_str_or_list":           (lambda val: type(val) in (str, list), "Must be a string or a list."),
    "is_empty_str":             (lambda val: type(val) == str and not bool(val), "Must be an empty string."),
    "is_empty_list":            (lambda val: type(val) == list and not bool(val), "Must be an empty list."),
    "is_empty_dict":            (lambda val: type(val) == dict and not bool(val), "Must be an empty dictionary."),
    "is_list_of_oom_strings":   (lambda val: is_list_shaped_so(val, mustHaveContent=True,
                                                            contentType=(str,)),
                                                            "Must be a list of one or more strings."),
    "is_list_of_zom_strings":   (lambda val: is_list_shaped_so(val, mustHaveContent=False,
                                                            contentType=(str,)),
                                                            "Must be a list of zero or more strings."),
    "is_dict_of_oom_strings":   (lambda val: is_dict_shaped_so(val, mustHaveContent=True,
                                                            contentType=(str,)),
                                                            "Must be a dictionary of one or more strings."),
    "is_dict_of_zom_strings":   (lambda val: is_dict_shaped_so(val, mustHaveContent=False,
                                                            contentType=(str,)),
                                                            "Must be a dictionary of zero or more strings.")
}

#####################################################################################################
# Basic '_basicTestMap' functions to check types of values in dictionary entries                          #
# `- These simply return True/False dependent on check passing/failing.                             #
#  - The corresponding 'failStr' is contained within the _basicTestMap which points to the function. #
#####################################################################################################

def checkItemExistsInList(item, listSchema: list):
    if item not in listSchema:
        return False, f'Value "{item}" not allowed here.'
    else:
        return True, ""

def checkListItemsWithinSchema(sublist: list, listSchema: list, allowDuplicates=False):
    for i in sublist:
        if i not in listSchema:
            return False, f'Value "{i}" not allowed here.'
    if not allowDuplicates:
        if len(set(sublist)) < len(sublist):
            return False, 'Duplicate entries not allowed.'
    return True, ""

def intWithinRange(item, lowerInt, upperInt):
    print(f'lower {lowerInt}, upper {upperInt}')
    if type(item) != int:
        return False, 'Must be an integer.'
    elif item not in range(lowerInt, upperInt + 1):
        return False, f'Must be in range {lowerInt}..{upperInt}'
    else:
        return True, ""

def isShellCmdType(item):
    failStr = "Must be str, list of str, or double enclosed list of tokens"
    if type(item) == str:
        return True, ""
    elif type(item) == list:
        if len(item) == 1 and type(item[0]) == list:
            if len(item[0]) > 0 and all(type(elem) == str for elem in item[0]):
                return True, ""
        elif len(item) > 0 and all(type(elem) == str for elem in item):    
            return True, ""
    return False, failStr

_advTestMap = {
    "checkItemExistsInList"     : checkItemExistsInList,
    "checkListItemsWithinSchema": checkListItemsWithinSchema,
    "intWithinRange"            : intWithinRange,
    "isShellCmdType"            : isShellCmdType
}

class dictContentsChecker():
    """
    A dictionary checker which utilises pre-defined test maps (pointing to test functions)
    `- to test the contents of dictionary entries.
    """

    def __init__(self, targetDict, checkDict):
        self.targetDict = targetDict
        self.checkDict = checkDict
        self.targetDictErrors = []
        # Perform checks for key values as specified in checkDict
        for k, v in self.targetDict.items():
            if k in self.checkDict:
                for thisCheck in self.checkDict.get(k, []):  # can be multiple checks for one value
                    print(f'testing {thisCheck}')
                    if type(thisCheck) == list:  # check we pass one of the checks in a list (or logic)
                        orFails = []
                        onePassed = False
                        for orCheck in thisCheck:
                            if type(orCheck) == tuple:
                                passed, errStr = self._functionTupleCheck(orCheck, self.targetDict[k])
                                if not passed:
                                    orFails.append(errStr)
                                else:
                                    onePassed = True
                            elif type(orCheck) == str:
                                if not _basicTestMap[orCheck][0](self.targetDict[k]):
                                    orFails.append(_basicTestMap[orCheck][1].strip('.'))
                                else:
                                    onePassed = True
                            else:
                                print('Error: Only str or tuple types allowed.')
                        if orFails and not onePassed:
                            multiFailStr = ', or '.join(orFails) + '.'
                            self.targetDictErrors.append((k, multiFailStr.capitalize()))
                    elif type(thisCheck) == tuple:
                        # we have a non-basic check, represented by a function name in the tuple[0] entry
                        passed, errStr = self._functionTupleCheck(thisCheck, self.targetDict[k])
                        if not passed:
                            self.targetDictErrors.append((k, errStr))
                    else:
                        if not _basicTestMap[thisCheck][0](self.targetDict[k]):
                            self.targetDictErrors.append((k, _basicTestMap[thisCheck][1]))



    def _functionTupleCheck(self, funcTuple: Tuple, itemToTest):
        """
        The first tuple entry is str pointing to an _advTestMap function that will check 'itemToTest'.
        The itemToTest will be passed as the first parameter to the retrieved function
        Further tuple entries are an ordered list of further parameters to pass to the check function
        Check functions must return 2x values: a) bool test result, b) fail string (empty if check passed)
        """
        if len(funcTuple) > 1:
            paramsToForward = list(funcTuple[1:])
        else:
            paramsToForward = []
        passBool, errStr = _advTestMap[funcTuple[0]](itemToTest, *paramsToForward)
        return passBool, errStr
        
    def isOK(self):
        return not bool(self.targetDictErrors)

    def getErrorList(self):
        # returns a list of tuple based errors [('key', 'valueError'), ...]
        return self.targetDictErrors


def mandatoryKeyChecker(targetDict, mandList):
    """
    A dictionary checker to test if mandatory settings/keys are present.
    """
    targetDictMissingKeys = []
    # Check to see if mandatory keys are present as specified in mandList
    for key in mandList:
        if not key in targetDict:
            targetDictMissingKeys.append(key)
    return targetDictMissingKeys
