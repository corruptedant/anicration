"""Globally used functions(or frequently used functions)"""

import logging
import sys

logger = logging.getLogger(__name__)

VERBOSITY = 1

# Higher the verbosity level, the more detailed. Hence, 0 is minimum(process bar, for example)
# 1 = INFO --- 2 = DEBUG --- 3 = WTF ( rarely anything uses this )
def _v_print(*values, verbosity=1, level=logger.info, **kwargs):
    sep = kwargs.pop('sep', ' ')
    if verbosity is None:
        pass
    elif VERBOSITY >= verbosity:
        print(*values, sep=sep, end=kwargs.pop('end', '\n'), file=sys.stdout)
    string = sep.join([str(value) for value in values])
    if level is not None:
        level(string)

def _set_verbosity(value):
    global VERBOSITY
    VERBOSITY = value
