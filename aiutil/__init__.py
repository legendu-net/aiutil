"""A utils Python package for data scientists."""

from importlib.metadata import version

from loguru import logger

__version__ = version("aiutil")

# Stay silent when imported as a library so that aiutil does not write to the
# logging of the application using it. The command-line tools of aiutil call
# logger.enable("aiutil") to opt back in.
logger.disable("aiutil")
