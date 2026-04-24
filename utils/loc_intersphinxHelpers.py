from .lnk_loggingUtils import getLogger; logger = getLogger(debug=True)
import os
import sys
import zlib
import re
import logging
from collections import defaultdict
import inspect
from .lnk_ioUtils import exceptionDetails

validRefTypesList = ['doc', 'label', 'term']

def getThinIntersphinxMap(givenMap, relativePathStart, targetKeyList=[], oneFilePerKey=True):
    retDict = {}
    if targetKeyList:
        # We have a limited list of target keys to parse
        # Omit dictionary entries that do not match this target key list
        for k in list(givenMap.keys()):
            if k not in targetKeyList:
                givenMap.pop(k, None)
    try:
        for shortname, invdata in givenMap.items():
            logger.debug(f'Processing {len(invdata)} intersphinxMap object.inv location(s) for handle: {shortname}')
            fq_file_list = []
            for invpath in invdata[1]:
                # data format = { shortname: (webBaseUrl, (tuple of obj.inv locations))}
                if invpath is not None and not invpath.startswith('http'):
                    # 'None' as an invpath indicates there is an object.inv file at the webBaseUrl location
                    # we are not interested in any remote/Url located object.inv files, only local ones
                    try:
                        np = os.path.normpath(os.path.join(relativePathStart, invpath))
                    except Exception as err:
                        logger.debug(f'- Ignoring \"{invpath}\" due to {exceptionDetails(err)}')
                        continue
                    if os.access(np, os.R_OK):
                        logger.debug(f'- Adding \"{invpath}\" (Extant and readable file).')
                        fq_file_list.append(np)
                        if oneFilePerKey:
                            logger.debug(f'- One file found for intersphinx {shortname} entry. Moving on as this is enough.')
                            break
                    else:
                        logger.debug(f'- Ignoring \"{invpath}\" (File not readable).')
                else:
                    logger.debug(f'- Ignoring \"{invpath}\" (Non-file item).')
            if fq_file_list:
                # save our object.inv path(s) in the correct format for returning
                # old intersphinx format: retDict[shortname] = (invdata[0], tuple(fq_file_list))
                retDict[shortname] = tuple(fq_file_list)
            else:
                logger.info(f'Handle \"{shortname}\" yielded no usable objects.inv files')
    except Exception as err:
        logger.error(f'Failure parsing intersphinx map: {exceptionDetails(err)}')
        retDict = {}
    logger.debug(f'retdict = {retDict}')
    print(f'retdict = {retDict}')
    return retDict

def getObjInvDisplayLists(objInvPathStr,
                          refTypeTargetList=validRefTypesList,
                          intersphinx_key="",
                          is_cur_proj=False):
    """
    Parse a sphinx objects.inv file on the local filesystem at objInvPathStr
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
        f = open(objInvPathStr, 'rb')
        try:
            # Sphinx v2 inventories begin with the following 4 uncompressed lines:
            # Sphinx inventory version 2
            # Project: <project name>
            # Version: <full version number>
            # The remainder of this file is compressed using zlib.
            line = f.readline().rstrip().decode('utf-8')
            logger.debug(f'line one = {line}')
            if line == kosherLine1:
                # set up some variables and constants
                dataMappings = defaultdict(list)
                displayMappings = defaultdict(list)
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
                    logger.error("Badly formatted objects.inv file at {}\n\nNo zlib line(4)".format(objInvPathStr))
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
                            if lineRefType in validRefTypesList:
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

                    # if refTypeTarget in validRefTypesList:
                    #     # build lists for a single refType
                    #     datalist = dataMappings[refTypeTarget]
                    #     displaylist = displayMappings[refTypeTarget]
                    # else:
                    #     # (default) build lists for all refTypes
                    for x in refTypeTargetList:
                        datalist.extend(dataMappings[x])
                        displaylist.extend(displayMappings[x])

                # datalist, displaylist = InsertSphinxLinksCommand.read_inventory_v2(f, refTypeTarget=refTypeTarget, \
                    # display_prefix=display_prefix)
            else:
                logger.error('Unknown first line identifier in objects.inv file: {}\n\n'
                                       'Identifier found: [{}]\n\n'
                                       'Identifier expected: [{}]'.format(objInvPathStr, line, kosherLine1))
        except Exception as err:
            errDetails = lnk_ioUtils.exceptionDetails(err)
            logger.error(f"Unable to parse intersphinx {objInvPathStr} inventory. {errDetails}")
    except Exception as err:
        errDetails = lnk_ioUtils.exceptionDetails(err)
        logger.error(f"Unable to open intersphinx inventory [{objInvPathStr}]. {errDetails}")
    finally:
        f.close()
        return datalist, displaylist