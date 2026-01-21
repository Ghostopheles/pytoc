import re

from typing import Optional
from dataclasses import dataclass

from .enums import *
from .load_conditions import *
from .context import TOCEvaluationContext

# TOC variables

_TOC_VAR_PATTERN = re.compile(r"\[([A-Za-z0-9_]+)\]")

_TOC_DEFAULT_VARIABLES = {"family": lambda ctx: ctx.Family, "game": lambda ctx: ctx.GameType, "textlocale": lambda ctx: ctx.TextLocale}


@dataclass(frozen=True)
class TOCFileEntry:
    """A file found in the 'files' section of a TOC file. Represents the .lua and .xml files."""

    RawFilePath: str
    Conditions: Optional[list[TOCCondition]] = None

    def __str__(self):
        return self.RawFilePath

    def resolve_path(self, ctx: TOCEvaluationContext) -> str:
        def replace(match: re.Match):
            name = match.group(1)
            try:
                return _TOC_DEFAULT_VARIABLES[name.lower()](ctx)
            except KeyError:
                raise KeyError(f"Undefined file path variable: {name}")

        return _TOC_VAR_PATTERN.sub(replace, self.RawFilePath)

    def should_load(self, ctx: TOCEvaluationContext) -> bool:
        should_load = True
        if self.Conditions:
            for condition in self.Conditions:
                condition: TOCCondition
                if not condition.evaluate(ctx):
                    should_load = False
                    break

        return should_load

    def export(self) -> str:
        path = self.RawFilePath

        if self.Conditions:
            for condition in self.Conditions:
                condition_str = f" {condition.export()}"
                path += condition_str

        return path.strip()
