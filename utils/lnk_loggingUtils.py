import logging
import threading
import inspect

def getLogger(level=logging.INFO, debug=False):
    if debug:
        level = logging.DEBUG
    logger = logging.getLogger(__package__.split('.')[0])
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        formatter = logging.Formatter("%(name)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s")
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    else:
        for handler in logger.handlers:
            handler.setLevel(level)
    return logger

# class LoggerControl:
#     _instance = None
#     _lock = threading.Lock()

#     def __new__(cls, *args, **kwargs):
#         # ensures the same, single instance of the object is returned on
#         # each call to the class i.e. just one logger is used and this same
#         # logger is returned and manipulated by calls to LoggerControl()
#         if cls._instance is None:
#             # this is the first call to the class, we must initialise our singleton logger
#             with cls._lock:
#                 if not cls._instance:
#                     # create a new 'bare' LoggerControl class object
#                     # same as: cls._instance = super().__new__(cls)
#                     cls._instance = object.__new__(cls)
#                     # initialise the 'self.logger' within our singleton LoggerControl object
#                     cls._instance._initialize(*args, **kwargs)
#                     print('making a new logger')
#         else:
#             print('returning pre-genned logger')
#             # this is the second (or later) call to the object
#             # return the LoggerControl class object that was previously generated
#             pass
#         return cls._instance

#     def _initialize(self, level=logging.INFO):
#             self.logger = logging.getLogger(__package__.split('.')[0])
#             self.loggingPreviousLevel = level
#             self.logger.setLevel(level)
#             self.logger.propagate = False

#             if not self.logger.handlers:
#                 formatter = logging.Formatter("%(name)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s")

#                 console_handler = logging.StreamHandler()
#                 console_handler.setFormatter(formatter)
#                 self.logger.addHandler(console_handler)

#     def set_level(self, level):
#         self.logger.setLevel(level)

#     def get_logger(self):
#         return self.logger

#     def doDebug(self, putItOn=True):
#         if putItOn:
#             print('putting on debug mode in logger A')
#             if self.logger.level > logging.DEBUG:
#                 self.loggingPreviousLevel = self.logger.level
#                 print('putting on debug mode in logger A')
#                 self.set_level(logging.DEBUG)
#         else:
#             if self.logger.level == logging.DEBUG:
#                 if self.loggingPreviousLevel > logging.DEBUG:
#                     self.set_level(self.loggingPreviousLevel)

