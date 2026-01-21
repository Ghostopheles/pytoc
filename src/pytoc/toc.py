import re

from pathlib import Path
from dataclasses import dataclass
from typing import Any, Optional, Union

from .enums import *
from .utils import StringToBoolean
from .meta import TypedClass
from .file_entry import *

DO_NOT_EXPORT_FIELDS = {"ClientType", "FilePath"}

CONDITION_VARIABLE_PATTERN = re.compile(r"\[([^\]]+)\]")

# i don't like this, but this old code has forced my hand
BOOLEAN_DIRECTIVES_LOWER = ("defaultstate", "onlybetaandptr", "loadondemand", "loadfirst", "loadsavedvariablesfirst", "usesecureenvironment")
SAVEDVARIABLES_DIRECTIVES_LOWER = ("savedvariables", "savedvariablespercharacter", "savedvariablesmachine")
CONDITION_DIRECTIVES_TO_CLASS = {
	"AllowLoad": TOCAllowLoad,
	"AllowLoadGameType": TOCAllowLoadGameType,
	"AllowLoadEnvironment": TOCAllowLoadEnvironment,
	"AllowLoadTextLocale": TOCAllowLoadTextLocale,
	"ExcludeLoad": TOCExcludeLoad,
	"ExcludeLoadGameType": TOCExcludeLoadGameType,
	"ExcludeLoadEnvironment": TOCExcludeLoadEnvironment,
	"ExcludeLoadTextLocale": TOCExcludeLoadTextLocale,
}
CONDITION_DIRECTIVES_LOWER = {key.lower() for key in CONDITION_DIRECTIVES_TO_CLASS.keys()}


@dataclass
class TOCDependency:
	Name: str
	Required: bool


class TOCFile(TypedClass):
	FilePath: Optional[Path] = None
	ClientType: Optional[TOCGameType] = None  # target client for client-specific TOC files. i.e. MyAddon_Standard.toc
	Interface: Optional[Union[int, list[int]]] = None
	Title: Optional[str] = None
	Author: Optional[str] = None
	Version: Optional[str] = None
	Files: Optional[list[TOCFileEntry]] = None
	Notes: Optional[str] = None
	Group: Optional[str] = None
	Category: Optional[str] = None
	LocalizedCategory: Optional[dict[str, str]] = None
	LocalizedTitle: Optional[dict[str, str]] = None
	SavedVariables: Optional[list[str]] = None
	SavedVariablesPerCharacter: Optional[list[str]] = None
	SavedVariablesMachine: Optional[list[str]] = None  # restricted to secure addons
	IconTexture: Optional[str] = None
	IconAtlas: Optional[str] = None
	AddonCompartmentFunc: Optional[str] = None
	AddonCompartmentFuncOnEnter: Optional[str] = None
	AddonCompartmentFuncOnLeave: Optional[str] = None
	LoadOnDemand: Optional[int] = None
	LoadWith: Optional[list[str]] = None
	LoadFirst: Optional[bool] = None
	LoadManagers: Optional[list[str]] = None
	Dependencies: Optional[list[TOCDependency]] = None
	DefaultState: Optional[bool] = None
	OnlyBetaAndPTR: Optional[bool] = None
	LoadSavedVariablesFirst: Optional[bool] = None
	AllowLoad: Optional[TOCAllowLoad] = None  # only useful to secure addons
	AllowLoadGameType: Optional[TOCAllowLoadGameType] = None
	AllowLoadTextLocale: Optional[TOCAllowLoadTextLocale] = None
	AllowLoadEnvironment: Optional[TOCAllowLoadEnvironment] = None
	UseSecureEnvironment: Optional[bool] = None  # restricted to secure addons
	AdditionalFields: Optional[dict[str, Any]] = None  # this is a dict of x- fields

	def __init__(self, file_path: Optional[Union[Path, str]] = None):
		super().__init__()
		if file_path is not None:
			if not isinstance(file_path, Path):
				file_path = Path(file_path)

			self.FilePath = file_path
			self.parse_toc_file(file_path)

	def has_attr(self, attr: str) -> bool:
		return attr in self.__dict__

	def get_target_client_from_path(self, file_path: Path) -> Optional[TOCGameType]:
		str_path = str(file_path)
		if not "_" in str_path:
			return None

		path_split = str_path.split("_")
		suffix = path_split[-1].removesuffix(".toc")
		if suffix.lower() in TOCGameType:
			if suffix.title() in TOCGameType._member_names_:
				return TOCGameType[suffix.title()]
			elif suffix.upper() in TOCGameType._member_names_:
				return TOCGameType[suffix.upper()]

		return None

	def export(self, file_path: str, overwrite: bool = False):
		file_path = Path(file_path)
		if file_path.exists() and not overwrite:
			raise FileExistsError("Destination file already exists. To overwrite, set overwrite=True")

		lines = []
		files = []
		for directive in self.__annotations__:
			if directive in DO_NOT_EXPORT_FIELDS:
				continue

			if directive == "Files":
				_files = self.Files
				if _files is None or len(_files) == 0:
					continue

				files.append("\n".join([f.export() for f in _files]))
			elif directive == "Dependencies":
				deps = self.Dependencies
				if deps is None or len(deps) == 0:
					continue

				required = [dep.Name for dep in deps if dep.Required]
				optional = [dep.Name for dep in deps if not dep.Required]

				if len(required) > 0:
					lines.append("## RequiredDeps: " + ", ".join(required) + "\n")

				if len(optional) > 0:
					lines.append("## OptionalDeps: " + ", ".join(optional) + "\n")
			elif "Localized" in directive:
				real_directive = directive.replace("Localized", "", 1)
				localized_dict = getattr(self, directive)
				if localized_dict is None or len(localized_dict) == 0:
					continue

				for locale, value in localized_dict.items():
					lines.append(f"## {real_directive}-{locale}: {value}\n")
			else:
				data = self.__getattribute__(directive)
				if data is None:
					continue

				if isinstance(data, TOCCondition):
					lines.append(f"## {directive}: {', '.join(data.AllowedValues)}\n")
				elif isinstance(data, list) and len(data) > 0:
					str_data = [str(v) for v in data]
					lines.append(f"## {directive}: " + ", ".join(str_data) + "\n")
				else:
					directive_lower = directive.lower()
					if directive_lower in BOOLEAN_DIRECTIVES_LOWER:
						# convert our boolean directive to a 1 or 0
						data = "1" if data else "0"

					lines.append(f"## {directive}: {data}\n")

		lines.append("\n")
		lines.extend(files)

		with open(file_path, "w", encoding="utf-8") as f:
			f.writelines(lines)

	def parse_toc_file(self, file_path: Path):
		if not file_path.exists():
			raise FileNotFoundError("TOC file not found")

		self.ClientType = self.get_target_client_from_path(file_path)

		# toc files should be utf-8 encoded
		with open(file_path, "r", encoding="utf-8") as f:
			toc_file = f.read()

		for line in toc_file.splitlines():
			if line.startswith("##") and ":" in line:
				# this line is a directive
				line = line.replace("## ", "", 1)
				line = line.lstrip()
				line_split = line.split(":", 1)
				directive = line_split[0]
				value = line_split[1].lstrip()
				if "," in value and directive.lower() != "notes":
					value = value.split(",")
					value = [v.lstrip() for v in value]
			elif not line.startswith("#") and line != "":
				# this line is not a directive, nor a comment, so it must be a file path
				self.add_file(line)
				continue
			else:
				# not handling comments rn
				continue

			self.set_field(directive, value)

	def set_field(self, directive: str, value: Any):
		directive_lower = directive.lower()
		if directive_lower.startswith("x-"):
			self.add_additional_field(directive, value)
		elif "-" in directive_lower:
			split = directive.split("-", 1)
			directive = split[0]
			locale = split[1]
			self.add_localized_directive(directive, value, locale)
		elif directive_lower.startswith("dep") or directive_lower == "requireddeps":
			required = True
			self.add_dependency(value, required)
		elif directive_lower == "optionaldeps":
			required = False
			self.add_dependency(value, required)
		elif directive_lower in BOOLEAN_DIRECTIVES_LOWER:
			self.__setattr__(directive, StringToBoolean(value, False))
		elif directive_lower in SAVEDVARIABLES_DIRECTIVES_LOWER:
			self.add_saved_variable(directive, value)
		elif directive_lower in CONDITION_DIRECTIVES_LOWER:
			self.add_conditional_field(directive, value)
		else:
			self.__setattr__(directive, value)

	def add_dependency(self, name: str, required: bool):
		if not self.has_attr("_dependencies"):
			self.Dependencies = []

		if isinstance(name, list):
			for _name in name:
				self.Dependencies.append(TOCDependency(_name, required))
		else:
			self.Dependencies.append(TOCDependency(name, required))

	def add_localized_directive(self, directive: str, value: str, locale: str):
		# localized directive will be accessible via the `.Localized<directive>` attribute
		# currently this only supports the localized directives that are annotated on this class :(
		# (this means ONLY LocalizedTitle and LocalizedCategory)
		# TODO: fix this terribleness

		# hack check to prevent weirdo errors
		if directive not in ("Title", "Category"):
			raise ValueError(f"Localized directives are only supported for Title and Category, not {directive}")

		internal_attr_name = "_localized" + directive.lower()
		if not self.has_attr(internal_attr_name):
			localized_dict = {}
		else:
			localized_dict = getattr(self, internal_attr_name)

		localized_dict[locale] = value

		attr_name = f"Localized{directive}"
		setattr(self, attr_name, localized_dict)

	def add_additional_field(self, directive: str, value: Any):
		if not self.has_attr("_additionalFields"):
			self.AdditionalFields = {}

		self.AdditionalFields[directive] = value

	def split_file_path_and_conditions(self, line: str) -> tuple[str, list[str]]:
		line = line.strip()
		depth = 0

		for i, char in enumerate(line):
			if char == "[":
				depth += 1
			elif char == "]":
				depth -= 1
			elif char.isspace() and depth == 0:
				path = line[:i]
				rest = line[i:].strip()
				return path, CONDITION_VARIABLE_PATTERN.findall(rest)

		return line, []

	def parse_condition(self, text: str) -> Optional[TOCCondition]:
		name, *rest = text.split(None, 1)
		args = []

		if rest:
			args = [a.strip() for a in rest[0].split(",")]

		condition_class = CONDITION_DIRECTIVES_TO_CLASS.get(name)

		if condition_class:
			return condition_class(frozenset(args))

		return None

	def parse_file_line(self, line: str):
		raw_path, condition_texts = self.split_file_path_and_conditions(line)

		conditions = [self.parse_condition(text) for text in condition_texts]

		if not conditions:
			return TOCFileEntry(raw_path)

		return TOCFileEntry(raw_path, conditions)

	def add_file(self, file_name: str):
		if not self.has_attr("_files"):
			self.Files = []

		file_entry = self.parse_file_line(file_name)
		self.Files.append(file_entry)

	def add_saved_variable(self, directive: str, value: Union[str, list[str]]):
		if isinstance(value, str):
			value = [value]
		setattr(self, directive, value)

	def add_conditional_field(self, directive: str, value: Union[str, list[str]]):
		if isinstance(value, str):
			value = [value]

		try:
			directive_class = CONDITION_DIRECTIVES_TO_CLASS[directive]({*value})
		except KeyError:
			raise KeyError(f"Unknown conditional directive: {directive}")

		setattr(self, directive, directive_class)

	def get_raw_files(self) -> list[str]:
		"""Returns a list of raw file paths. (no variable or conditional parsing done)"""

		raw_files = []
		for file in self.Files:
			raw_files.append(file.export())

		return raw_files

	def can_load_addon(self, context: TOCEvaluationContext) -> tuple[bool, TOCAddonLoadError]:
		if self.Dependencies and len(self.Dependencies) > 0:
			deps_fulfilled = True
			for dep in self.Dependencies:
				if dep.Required and not context.is_addon_loaded(dep.Name):
					deps_fulfilled = False
					break

			if not deps_fulfilled:
				return False, TOCAddonLoadError.MissingDependency

		if self.AllowLoad and not self.AllowLoad.evaluate(context):
			return False, TOCAddonLoadError.WrongEnvironment
		elif self.AllowLoadEnvironment and not self.AllowLoadEnvironment.evaluate(context):
			return False, TOCAddonLoadError.WrongEnvironment
		elif self.AllowLoadGameType and not self.AllowLoadGameType.evaluate(context):
			return False, TOCAddonLoadError.WrongGameType
		elif self.AllowLoadTextLocale and not self.AllowLoadTextLocale.evaluate(context):
			return False, TOCAddonLoadError.WrongTextLocale

		return True, TOCAddonLoadError.Success
