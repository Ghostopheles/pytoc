from typing import Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

from .enums import *
from .context import TOCEvaluationContext

# TOC conditions


class TOCCondition(ABC):
    Values: frozenset[Any]
    ExportName: str

    @abstractmethod
    def evaluate(self, ctx: TOCEvaluationContext) -> bool: ...

    def export(self) -> str:
        return f"[{self.ExportName} " + ", ".join(self.Values) + "]"


@dataclass(frozen=True)
class TOCAllowLoad(TOCCondition):
    Values: frozenset[TOCEnvironment]
    ExportName: str = "AllowLoad"

    def evaluate(self, ctx: TOCEvaluationContext) -> bool:
        return ctx.Environment in self.Values or TOCEnvironment.Both in self.Values


@dataclass(frozen=True)
class TOCAllowLoadEnvironment(TOCCondition):
    Values: frozenset[TOCEnvironment]
    ExportName: str = "AllowLoadEnvironment"

    def evaluate(self, ctx: TOCEvaluationContext) -> bool:
        return ctx.Environment in self.Values or TOCEnvironment.Both in self.Values


@dataclass(frozen=True)
class TOCAllowLoadGameType(TOCCondition):
    Values: frozenset[TOCGameType]
    ExportName: str = "AllowLoadGameType"

    def evaluate(self, ctx: TOCEvaluationContext) -> bool:
        return ctx.GameType in self.Values


@dataclass(frozen=True)
class TOCAllowLoadTextLocale(TOCCondition):
    Values: frozenset[TOCTextLocale]
    ExportName: str = "AllowLoadTextLocale"

    def evaluate(self, ctx: TOCEvaluationContext) -> bool:
        return ctx.TextLocale in self.Values


# inverse conditions (why? because)


@dataclass(frozen=True)
class TOCExcludeLoad(TOCCondition):
    Values: frozenset[TOCEnvironment]
    ExportName: str = "ExcludeLoad"

    def evaluate(self, ctx: TOCEvaluationContext) -> bool:
        return ctx.Environment not in self.Values or TOCEnvironment.Both not in self.Values


@dataclass(frozen=True)
class TOCExcludeLoadEnvironment(TOCCondition):
    Values: frozenset[TOCEnvironment]
    ExportName: str = "ExcludeLoadEnvironment"

    def evaluate(self, ctx: TOCEvaluationContext) -> bool:
        return ctx.Environment not in self.Values or TOCEnvironment.Both not in self.Values


@dataclass(frozen=True)
class TOCExcludeLoadGameType(TOCCondition):
    Values: frozenset[TOCGameType]
    ExportName: str = "ExcludeLoadGameType"

    def evaluate(self, ctx: TOCEvaluationContext) -> bool:
        return ctx.GameType not in self.Values


@dataclass(frozen=True)
class TOCExcludeLoadTextLocale(TOCCondition):
    Values: frozenset[TOCTextLocale]
    ExportName: str = "ExcludeLoadTextLocale"

    def evaluate(self, ctx: TOCEvaluationContext) -> bool:
        return ctx.TextLocale not in self.Values
