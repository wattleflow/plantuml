# Module Name: tools/main.py
# Description: This modul contains SQL UML Builder class.
# Author: (wattleflow@outlook.com)
# Copyright: (c) 2022-2025 WattleFlow
# License: Apache 2 Licence

import sys
import argparse
import pathlib
from abc import ABC
from logging import NOTSET, Handler
from typing import Optional
from wattleflow.concrete import StrategyGenerate
from wattleflow.constants import Event

from core.builder import UMLBuilder
from builders.sql_entity import SQLEntityBuilder
from builders.python_class import PythonUMLClassBuilder


class BuilderNotFound(ValueError):
    pass


class UMLStrategy(StrategyGenerate, ABC):
    def __init__(
        self,
        filename: str,
        level: int = NOTSET,
        handler: Optional[Handler] = None,
        **kwargs,
    ):
        super().__init__(level=level, handler=handler)
        self.debug(msg=Event.Constructor.value, filename=filename, **kwargs)
        self.content: str = ""
        self.filename: pathlib.Path = pathlib.Path(filename)

    def _find_builder(self) -> UMLBuilder:
        ext: str = self.filename.suffix.lower()
        if ext in [".sql"]:
            return SQLEntityBuilder(caller=self, filename=str(self.filename))
        elif ext in [".py"]:
            return PythonUMLClassBuilder(caller=self, filename=str(self.filename))
        raise BuilderNotFound(f"Unknown extension: [{self.filename.suffix}]")

    def execute(self, **kwargs):
        builder = self._find_builder()
        builder.build()
        print(builder.rendered)


# ---------------------------- CLI entrypoint ----------------------------


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="plantuml", description="Generate PlantUML code, from a given filename."
    )
    parser.add_argument(
        "filename",
        help="Path to the source code filename.",
    )
    parser.add_argument(
        "--log-level",
        default="NOTSET",
        help="Logging level (eg NOTSET, INFO, DEBUG, WARNING, ERROR).",
    )

    import logging

    args = parser.parse_args(argv)
    level = getattr(logging, str(args.log_level).upper(), NOTSET)

    try:
        UMLStrategy(filename=args.filename, level=level).execute()
        return 0
    except FileNotFoundError as e:
        print(f"Error: File not found: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error while generating UML. {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
