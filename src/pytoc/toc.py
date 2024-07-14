import os

from dataclasses import dataclass, field
from typing import Optional, Any, Union


@dataclass
class Dependency:
    Name: str
    Required: bool


@dataclass(
    repr=False,
)
class TOCFile:
    Interface: Union[int, list[int]] = None
    Title: str = None
    Author: str = None
    Version: str = None
    Files: list[str] = None
    Notes: Optional[str] = None
    LocalizedTitles: Optional[dict[str, str]] = None
    SavedVariables: Optional[list[str]] = None
    SavedVariablesPerCharacter: Optional[list[str]] = None
    IconTexture: Optional[str] = None
    IconAtlas: Optional[str] = None
    AddonCompartmentFunc: Optional[str] = None
    AddonCompartmentFuncOnEnter: Optional[str] = None
    AddonCompartmentFuncOnLeave: Optional[str] = None
    LoadOnDemand: Optional[int] = None
    LoadWith: Optional[list[str]] = None
    LoadManagers: Optional[list[str]] = None
    Dependencies: Optional[list[Dependency]] = None
    AdditionalFields: Optional[dict[str, Any]] = None
    DefaultState: Optional[bool] = False
    OnlyBetaAndPTR: Optional[bool] = False

    def __init__(self, file_path: Optional[str]):
        super().__init__()
        if file_path is not None:
            self.parse_toc_file(file_path)

    def has_attr(self, attr: str) -> bool:
        return attr in self.__dict__

    def parse_toc_file(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError("TOC file not found")

        with open(file_path, "r") as f:
            toc_file = f.read()

        for line in toc_file.splitlines():
            if line.startswith("##"):
                # line is a directive
                line = line.replace("## ", "", 1)
                line = line.lstrip()
                line_split = line.split(":", 1)
                directive = line_split[0]
                value = line_split[1].lstrip()
                if "," in value and directive.lower() != "notes":
                    value = value.split(",")
                    value = [v.lstrip() for v in value]
            elif not line.startswith("#") and line != "":
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
        elif directive_lower.startswith("dep"):
            required = True
            self.add_dependency(value, required)
        elif directive_lower == "optionaldeps":
            required = False
            self.add_dependency(value, required)
        else:
            self.__setattr__(directive, value)

    def add_dependency(self, name: str, required: bool):
        if not self.has_attr("Dependencies"):
            self.Dependencies = []

        self.Dependencies.append(Dependency(name, required))

    def add_localized_title(self, locale: str, value: str):
        if not self.has_attr("LocalizedTitles"):
            self.LocalizedTitles = {}

        self.LocalizedTitles[locale] = value

    def add_additional_field(self, directive: str, value: Any):
        if not self.has_attr("AdditionalFields"):
            self.AdditionalFields = {}

        self.AdditionalFields[directive] = value

    def add_file(self, file_name: str):
        if not self.has_attr("Files"):
            self.Files = []

        self.Files.append(file_name)
