from argparse import ArgumentTypeError
from typing import Any


class CogError(Exception):
    """Any exception raised by Cog."""

    def __init__(self, msg: Any, file: str = "", line: int = 0):
        if file:
            super().__init__(f"{file}({line}): {msg}")
        else:
            super().__init__(msg)


class CogUsageError(CogError, ArgumentTypeError):
    """An error in usage of command-line arguments in cog."""

    pass


class CogGeneratedError(CogError):
    """An error raised by a user's cog generator."""

    pass


class CogUserException(CogError):
    """An exception caught when running a user's cog generator.

    The argument is the traceback message to print.

    """

    pass


class CogCheckFailed(CogError):
    """A --check failed."""

    pass
