#!/usr/bin/python3
from core import (
    Shell,
    ShortArgsOption,
    expose_tilde,
    normalize_short_and_long_args,
    quotes_wrapper
)
from gnu_coreutils import ls

__all__ = ["GID", "GROUP", "HOME", "Shell", "ShortArgsOption", "UID", "USER",
           "expose_tilde", "ls", "normalize_short_and_long_args",
           "quotes_wrapper"]

GID = Shell("id -g").output()[:-1]
GROUP = Shell("id -gn").output()[:-1]
HOME = Shell("printf ~").output()
UID = Shell("id -u").output()[:-1]
USER = Shell("id -un").output()[:-1]

if __name__ == "__main__":
    print(f"{GID=}")
    print(f"{GROUP=}")
    print(f"{HOME=}")
    print(f"{UID=}")
    print(f"{USER=}")
