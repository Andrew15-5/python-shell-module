#!/usr/bin/python3
from inspect import cleandoc
import re
from subprocess import PIPE, Popen
from typing import Iterable, List, Union

__all__ = ["normalize_short_and_long_args", "quotes_wrapper", "Shell",
           "ShortArgsOption"]


class Shell:
    """
    Simple class that allows to execute shell command and get it's output
    and exit_code. Also allows to chain Shell instances same way pipeline
    does.

    Note: After instanciating this class (executing shell command) Python does
    not wait for the end of the command execution. In order to do that you have
    to invoke any method except shell().

    P.S. subprocess.Popen is used as a base.
    """

    def __init__(self, command, stdin=PIPE, stdout=PIPE, stderr=PIPE):
        self.command = command
        if isinstance(command, str):
            self.process = Popen(command, shell=True,
                                 stdin=stdin, stdout=stdout, stderr=stderr)
        else:
            self.process = Popen(list(command),
                                 stdin=stdin, stdout=stdout, stderr=stderr)
        self.stdin = self.process.stdin
        self.stdout = self.process.stdout
        self.stderr = self.process.stderr
        self.__communicate = None

    def __print_output(self, index: int) -> str:
        if self.__communicate is None:
            self.__communicate = self.process.communicate()
        return self.__communicate[index].decode("utf-8")

    def error_output(self) -> str:
        '''Returns content of stderr file descriptor.'''
        return self.__print_output(1)

    def exit_code(self) -> int:
        '''Waits the end of the command execution and returns its exit code.'''
        try:
            self.__communicate = self.process.communicate()
        except KeyboardInterrupt:
            pass
        return self.process.wait()

    def get_lines(self, exclude_last_lf=True, stderr=False) -> List[str]:
        R"""
        Returns content of stdout splitted by lines excluding last "\n"
        character (if present). Default output is stdout (also can be stderr).

        Parameters:
            exclude_last_lf (bool): remove last blank line in list. Default is
                True.
            stderr (bool): grab output of stdout or stderr. Default is False
                (grap output of stdout).

        Returns:
            List[str]: output splitted by lines.
        """
        if stderr:
            output = self.error_output()
        else:
            output = self.output()
        output = output.split('\n')
        if exclude_last_lf and len(output) and output[-1] == '':
            output.pop(-1)
        return output

    def output(self) -> str:
        '''Returns content of stdout file descriptor.'''
        return self.__print_output(0)

    def shell(self, command, stdin="parent fd", stdout=PIPE, stderr=PIPE):
        """
        Gives the ability to chain shell commands.

        Parameters:
            command (str | Iterable[str]): shell command that needs to be
                executed.
            stdin (int): stdin file descriptor. Default is "parent fd" aka
                self.stdout (to gain ability of chaining shell commands aka
                piping).
            stdout (int): stdout file descriptor. Default is PIPE.
            stderr (int): stderr file descriptor. Default is PIPE.

        Returns:
            Shell: class instance that can be chained.
        """

        if stdin == "parent fd":
            stdin = self.stdout
        shell = Shell(command, stdin, stdout, stderr)
        return shell

    def wait(self) -> int:
        '''Waits the end of the command execution and returns its exit code.'''
        return self.exit_code()


class ShortArgsOption:
    '''Enum object for normalize_short_and_long_args()'''
    TOGETHER = 0
    APART = 1
    NO_DASH = 2
    _last = 2


def normalize_short_and_long_args(
        short_args: Union[str, Iterable[str]] = [],
        long_args: Iterable[str] = [],
        short_args_option: ShortArgsOption = ShortArgsOption.TOGETHER) -> str:
    """
    Returns string of normalized short and long args.

    Parameters:
        short_args (str | Iterable[str]): string or array of short arguments.
            Prefix-dash is ignored. Default is [] (no short arguments).
        long_args (Iterable[str]): array of long arguments. Prefix-dashes are
            ignored. Default is [] (no long arguments).
        short_args_option (ShortArgsOption): sets the way short args are
            formatted. Default is ShortArgsOption.TOGETHER.

    Raises:
        ValueError: spaces in short args which are TOGETHER or
            any of short args which are TOGETHER is longer than 1 char. or
            invalid value of short_args_option.

    Returns:
        str: string of normalized short and long args.
    """
    if (type(short_args_option) != int or
        short_args_option < 0 or
            short_args_option > ShortArgsOption._last):
        raise ValueError(cleandoc(
            """Invalid value of short_args_option. Valid values are:
            ShortArgsOption.TOGETHER,
            ShortArgsOption.APART,
            ShortArgsOption.NO_DASH."""))

    # Make aliases for better readability
    shargs = short_args
    largs = long_args

    # Shargs
    if isinstance(shargs, str) and shargs:
        if short_args_option == ShortArgsOption.TOGETHER and shargs.find(' ') > -1:
            raise ValueError("No spaces are allowed in short args (str).")
        shargs = shargs.replace('-', '')
        if short_args_option == ShortArgsOption.TOGETHER:
            shargs = f"-{shargs}"
        elif short_args_option == ShortArgsOption.APART:
            shargs = '-' + " -".join(shargs)
        elif short_args_option == ShortArgsOption.NO_DASH:
            shargs = ' '.join(shargs)
    elif (isinstance(shargs, Iterable) and
          len(shargs) and
          all(isinstance(e, str) for e in shargs) and
          len([e for e in shargs if e])):
        shargs = [arg.replace('-', '') for arg in shargs]
        if short_args_option == ShortArgsOption.TOGETHER:
            if not all(len(e) == 1 for e in shargs):
                raise ValueError("Short arguments must be 1 character long.")
            shargs = '-' + ''.join(shargs)
        elif short_args_option == ShortArgsOption.APART:
            shargs = '-' + " -".join(shargs)
        elif short_args_option == ShortArgsOption.NO_DASH:
            shargs = ' '.join(shargs)
    else:
        shargs = ''

    # Largs
    if (not isinstance(largs, str) and
        isinstance(largs, Iterable) and
        len(largs) and
        all(isinstance(e, str) for e in largs) and
            len([e for e in largs if e])):
        largs = [re.sub(r'^-+', '', arg) for arg in largs]
        largs = " --".join(largs)
        largs = f"--{largs}"
    else:
        largs = ''

    # Return str
    if shargs:
        if largs:
            return f"{shargs} {largs}"
        else:
            return shargs
    else:
        if largs:
            return largs
        else:
            return ''


def quotes_wrapper(path: Union[str, Iterable[str]]) -> str:
    """
    Wraps string(s) in "double quotes". In case of Iterable[str] each element
    is wrapped in its personal double quotes and then elements are concatenated
    with single whitespace between them.

    Parameters:
        path (str | Iterable[str]): string or array of strings that needs to be
            wrapped in double quotes.

    Raises:
        TypeError: path's type isn't (str | Iterable[str]) or type of elements
            of path (Iterable[str]) are not str.
        ValueError: spaces in short args which are TOGETHER or
            any of short args which are TOGETHER is longer than 1 char. or
            invalid value of short_args_option.
        IndexError: path (Iterable[str]) is empty.

    Returns:
        str: string wrapped with double quotes.
    """
    if isinstance(path, str):
        path = path.replace('"', R'\"')
        path = f'"{path}"'
    elif isinstance(path, Iterable):
        if len(path) == 0:
            raise IndexError("path is empty.")
        try:
            path = [e.replace('"', R'\"') for e in path]
            path = f'''"{'" "'.join(path)}"'''
        except AttributeError:
            raise TypeError("type of elements of path must be str.")
    else:
        raise TypeError("path's type must be str or Iterable[str].")
    return path
