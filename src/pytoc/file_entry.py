import re

from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Optional, Any

from .enums import *

# TOC eval context


@dataclass(frozen=True)
class TOCEvaluationContext:
	GameType: TOCGameType
	Environment: TOCEnvironment
	TextLocale: TOCTextLocale

	@property
	def Family(self):
		try:
			return TOC_GAME_TYPE_TO_FAMILY[self.GameType]
		except KeyError:
			raise KeyError(f"Unknown GameType specified: {self.GameType}")


# TOC conditions


class TOCCondition(ABC):
	AllowedValues: frozenset[Any]
	ExportName: str

	@abstractmethod
	def evaluate(self, ctx: TOCEvaluationContext) -> bool: ...

	def export(self) -> str:
		return f"[{self.ExportName} " + ", ".join(self.AllowedValues) + "]"


@dataclass(frozen=True)
class TOCAllowLoad(TOCCondition):
	AllowedValues: frozenset[TOCEnvironment]
	ExportName: str = "AllowLoad"

	def evaluate(self, ctx: TOCEvaluationContext) -> bool:
		return ctx.Environment in self.AllowedValues or TOCEnvironment.Both in self.AllowedValues


@dataclass(frozen=True)
class TOCAllowLoadEnvironment(TOCCondition):
	AllowedValues: frozenset[TOCEnvironment]
	ExportName: str = "AllowLoadEnvironment"

	def evaluate(self, ctx: TOCEvaluationContext) -> bool:
		return ctx.Environment in self.AllowedValues or TOCEnvironment.Both in self.AllowedValues


@dataclass(frozen=True)
class TOCAllowLoadGameType(TOCCondition):
	AllowedValues: frozenset[TOCGameType]
	ExportName: str = "AllowLoadGameType"

	def evaluate(self, ctx: TOCEvaluationContext) -> bool:
		return ctx.GameType in self.AllowedValues


@dataclass(frozen=True)
class TOCAllowLoadTextLocale(TOCCondition):
	AllowedValues: frozenset[TOCTextLocale]
	ExportName: str = "AllowLoadTextLocale"

	def evaluate(self, ctx: TOCEvaluationContext) -> bool:
		return ctx.TextLocale in self.AllowedValues


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
