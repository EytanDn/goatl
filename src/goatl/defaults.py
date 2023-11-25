import logging


class DEFAULTS:
    CALL_MSG = "Calling {funcName} with {args} and {kwargs}"
    RETURN_MSG = "Returned {result}"
    CALL_LEVEL = logging.INFO
    RETURN_LEVEL = logging.DEBUG
    INIT_MSG = "Initialized {args[0]}"
    INIT_LEVEL = logging.DEBUG