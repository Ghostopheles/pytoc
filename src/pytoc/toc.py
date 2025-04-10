import os

from dataclasses import dataclass
from typing import Any, Optional, Union

from .meta import TypedClass

# characters/strings that are interpreted as falsey/truthy according to the WoW client
FALSEY_CHARS = ("0", "n", "f")
FALSEY_STRINGS = ("off", "disabled")
TRUTHY_CHARS = ("1", "2", "3", "4", "5", "6", "7", "8", "9", "y", "t")
TRUTHY_STRINGS = ("on", "enabled")


# this function is terrible, but it supports legacy slash commands
def StringToBoolean(string: str, defaultReturn: bool = False):
    if len(string) == 0:
        return defaultReturn

    string = string.lower()
    firstChar = string[0]

    if firstChar in FALSEY_CHARS or string in FALSEY_STRINGS:
        return False
    elif firstChar in TRUTHY_CHARS or string in TRUTHY_STRINGS:
        return True

    return defaultReturn


# i don't like this, but this old code has forced my hand
BOOLEAN_DIRECTIVES_LOWER = (
    "defaultstate",
    "onlybetaandptr",
    "loadondemand",
    "loadfirst",
    "loadsavedvariablesfirst",
    "usesecureenvironment",
)


@dataclass
class Dependency:
    Name: str
    Required: bool


class TOCFile(TypedClass):
    Interface: Optional[Union[int, list[int]]] = None
    Title: Optional[str] = None
    Author: Optional[str] = None
    Version: Optional[str] = None
    Files: Optional[list[str]] = None
    Notes: Optional[str] = None
    LocalizedTitles: Optional[dict[str, str]] = None
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
    LoadFirst: Optional[bool] = False
    LoadManagers: Optional[list[str]] = None
    Dependencies: Optional[list[Dependency]] = None
    DefaultState: Optional[bool] = False
    OnlyBetaAndPTR: Optional[bool] = False
    LoadSavedVariablesFirst: Optional[bool] = False
    AllowLoad: Optional[str] = None  # restricted to secure addons
    AllowLoadGameType: Optional[str] = None
    UseSecureEnvironment: Optional[bool] = False  # restricted to secure addons
    AdditionalFields: Optional[dict[str, Any]] = None  # this is a dict of x- fields

    def __init__(self, file_path: Optional[str] = None):
        super().__init__()
        if file_path is not None:
            self.parse_toc_file(file_path)

    def has_attr(self, attr: str) -> bool:
        return attr in self.__dict__

    def export(self, file_path: str, overwrite: bool = False):
        if os.path.exists(file_path) and not overwrite:
            raise FileExistsError(
                "Destination file already exists. To overwrite, set overwrite=True"
            )

        lines = []
        files = []
        for directive in self.__annotations__:
            if directive == "Files":
                _files = self.Files
                if _files is None or len(_files) == 0:
                    continue

                files.append("\n".join(_files))
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
            else:
                data = self.__getattribute__(directive)
                if data is None:
                    continue

                if isinstance(data, list) and len(data) > 0:
                    str_data = [str(v) for v in data]
                    lines.append(f"## {directive}: " + ", ".join(str_data) + "\n")
                else:
                    if directive.lower() in BOOLEAN_DIRECTIVES_LOWER:
                        # convert our boolean directive to a 1 or 0
                        data = "1" if data else "0"

                    lines.append(f"## {directive}: {data}\n")

        lines.append("\n")
        lines.extend(files)

        with open(file_path, "w") as f:
            f.writelines(lines)

    def parse_toc_file(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError("TOC file not found")

        # toc files should be utf-8 encoded
        with open(file_path, "r", encoding="utf-8") as f:
            toc_file = f.read()

        for line in toc_file.splitlines():
            if line.startswith("##"):
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
        elif directive_lower.startswith("title-"):
            split = directive.split("-", 1)
            locale = split[1]
            self.add_localized_title(locale, value)
        elif directive_lower.startswith("dep") or directive_lower == "requireddeps":
            required = True
            self.add_dependency(value, required)
        elif directive_lower == "optionaldeps":
            required = False
            self.add_dependency(value, required)
        elif directive_lower in BOOLEAN_DIRECTIVES_LOWER:
            self.__setattr__(directive, StringToBoolean(value, False))
        else:
            self.__setattr__(directive, value)

    def add_dependency(self, name: str, required: bool):
        if not self.has_attr("_dependencies"):
            self.Dependencies = []

        if isinstance(name, list):
            for _name in name:
                self.Dependencies.append(Dependency(_name, required))
        else:
            self.Dependencies.append(Dependency(name, required))

    def add_localized_title(self, locale: str, value: str):
        if not self.has_attr("_localizedTitles"):
            self.LocalizedTitles = {}

        self.LocalizedTitles[locale] = value

    def add_additional_field(self, directive: str, value: Any):
        if not self.has_attr("_additionalFields"):
            self.AdditionalFields = {}

        self.AdditionalFields[directive] = value

    def add_file(self, file_name: str):
        if not self.has_attr("_files"):
            self.Files = []

        self.Files.append(file_name)

    def add_saved_variable(self, var_name: str, per_character: bool = False):
        if not per_character:
            if not self.has_attr("_savedVariables"):
                self.SavedVariables = []
            self.SavedVariables.append(var_name)
        else:
            if not self.has_attr("_savedVariablesPerCharacter"):
                self.SavedVariablesPerCharacter = []
            self.SavedVariablesPerCharacter.append(var_name)
