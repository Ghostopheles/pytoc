import os

from dataclasses import dataclass, field
from typing import Optional, Any, Union


@dataclass(repr=False)
class TOCFile:
    Interface: Union[int, list[int]] = field(default_factory=int)
    Title: str = field(default_factory=str)
    Author: str = field(default_factory=str)
    Version: str = field(default_factory=str)
    Files: list[str] = field(default_factory=list)
    Notes: Optional[str] = field(default_factory=str)
    LocalizedTitles: Optional[dict[str, str]] = field(default_factory=dict)
    SavedVariables: Optional[list[str]] = field(default_factory=list)
    SavedVariablesPerCharacter: Optional[list[str]] = field(default_factory=list)
    IconTexture: Optional[str] = field(default_factory=str)
    IconAtlas: Optional[str] = field(default_factory=str)
    AddonCompartmentFunc: Optional[str] = field(default_factory=str)
    AddonCompartmentFuncOnEnter: Optional[str] = field(default_factory=str)
    AddonCompartmentFuncOnLeave: Optional[str] = field(default_factory=str)
    LoadOnDemand: Optional[int] = field(default_factory=int)
    LoadWith: Optional[list[str]] = field(default_factory=list)
    LoadManagers: Optional[list[str]] = field(default_factory=list)
    Dependencies: Optional[list[str]] = field(default_factory=list)
    AdditionalFields: Optional[dict[str, Any]] = field(default_factory=dict)
    DefaultState: Optional[bool] = field(default=False)
    OnlyBetaAndPTR: Optional[bool] = field(default=False)

    def __init__(self, file_path: str):
        super().__init__()
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
        if directive.startswith("X-"):
            self.add_additional_field(directive, value)
        elif directive.lower().startswith("title-"):
            split = directive.split("-", 1)
            locale = split[1]
            self.add_localized_title(locale, value)
        else:
            self.__setattr__(directive, value)

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
