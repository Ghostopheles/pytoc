import re

from pathlib import Path
from typing import Optional, Union, List
from dataclasses import dataclass, field, InitVar


from .enums import *
from .file_entry import *
from .parser import *
from .shared import *


@dataclass
class TOCFile:
    _file_path: InitVar[str | Path] = None
    _AST: Optional[TOCAST] = None

    Interface: Optional[TOCListValue[int]] = None
    Title: Optional[TOCLocalizedDirectiveValue] = None
    Author: Optional[TOCLocalizedDirectiveValue] = None
    Version: Optional[TOCLocalizedDirectiveValue] = None
    Notes: Optional[TOCLocalizedDirectiveValue] = None
    Group: Optional[TOCLocalizedDirectiveValue] = None
    Category: Optional[TOCLocalizedDirectiveValue] = None
    SavedVariables: Optional[TOCListValue[str]] = None
    SavedVariablesPerCharacter: Optional[TOCListValue[str]] = None
    SavedVariablesMachine: Optional[TOCListValue[str]] = None
    IconTexture: Optional[TOCLocalizedDirectiveValue] = None
    IconAtlas: Optional[TOCLocalizedDirectiveValue] = None
    AddonCompartmentFunc: Optional[TOCLocalizedDirectiveValue] = None
    AddonCompartmentFuncOnEnter: Optional[TOCLocalizedDirectiveValue] = None
    AddonCompartmentFuncOnLeave: Optional[TOCLocalizedDirectiveValue] = None
    LoadOnDemand: Optional[TOCBoolType] = None
    LoadFirst: Optional[TOCBoolType] = None
    LoadWith: Optional[TOCListValue[str]] = None
    LoadManagers: Optional[TOCListValue[str]] = None
    Dependencies: Optional[TOCListValue[str]] = None
    OptionalDeps: Optional[TOCListValue[str]] = None
    DefaultState: Optional[TOCBoolType] = None
    OnlyBetaAndPTR: Optional[TOCBoolType] = None
    LoadSavedVariablesFirst: Optional[TOCBoolType] = None
    AllowLoad: Optional[TOCAllowLoad] = None
    AllowLoadGameType: Optional[TOCAllowLoadGameType] = None
    AllowLoadTextLocale: Optional[TOCAllowLoadTextLocale] = None
    UseSecureEnvironment: Optional[TOCBoolType] = None
    ExtendedDirectives: Optional[dict[str, str]] = field(default_factory=dict)
    UnknownDirectives: Optional[dict[str, TOCUnkValue]] = field(default_factory=dict)
    Files: Optional[list[TOCFileEntryLine]] = field(default_factory=list)
    Comments: Optional[TOCListValue[TOCCommentLine]] = field(default_factory=list)

    def __post_init__(self, _file_path: str | Path = None):
        if _file_path is None:
            return

        self.load_file(_file_path)

    def set_ast(self, ast: TOCAST):
        for node in ast.Lines:
            if isinstance(node, TOCFileEntryLine):
                self.Files.append(node)

            if isinstance(node, TOCDirectiveLine):
                if node.IsExtendedDirective:
                    self.ExtendedDirectives.setdefault(node.RawName, node.Value)
                elif isinstance(node.Value, TOCUnkValue):
                    self.UnknownDirectives.setdefault(node.CanonicalName, node.Value)
                elif condition_class := CONDITION_DIRECTIVES_TO_CLASS.get(node.CanonicalName):
                    setattr(self, node.CanonicalName, condition_class(frozenset(node.Value)))
                else:
                    if isinstance(node.Value, str):
                        node.Value = node.Value.removesuffix("\n")

                    spec = TOC_DIRECTIVES.get(node.CanonicalName)
                    existing_attribute = getattr(self, node.CanonicalName, None)
                    if existing_attribute is not None and isinstance(existing_attribute, TOCListValue):
                        existing_attribute.append_line(node)
                        continue

                    if spec is not None and (spec.CanBeLocalized or node.IsExtendedDirective):
                        locale = node.Locale if node.Locale is not None else PYTOC_DEFAULT_LOCALE
                        if not isinstance(locale, TOCTextLocale):
                            if locale is not None:
                                locale = TOCTextLocale[locale]
                            else:
                                locale = PYTOC_DEFAULT_LOCALE

                        if existing_attribute is not None:
                            if PYTOC_CHECK_DUPLICATES and not spec.AllowDuplicates:
                                assert getattr(self, node.CanonicalName) is None, f"Attempt to register duplicate {node.CanonicalName} directive"
                            if isinstance(existing_attribute, TOCLocalizedDirectiveValue):
                                existing_attribute.set_translation(locale, node.Value)
                            continue

                        else:
                            attr = TOCLocalizedDirectiveValue(node.RawText)
                            attr.set_translation(locale, node.Value)
                            setattr(self, node.CanonicalName, attr)
                            continue

                    setattr(self, node.CanonicalName, node.Value)

            if isinstance(node, TOCCommentLine):
                self.Comments.append(node)
        self._AST = ast
        return self

    def load_file(self, file_path: Union[str | Path]):
        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"TOC file does not exist at the given path: '{file_path}'")

        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()

        ast = TOCAST.from_lines(lines)
        self.set_ast(ast)

    def export(self, export_path: Union[str | Path], overwrite: bool = False):
        if not isinstance(export_path, Path):
            export_path = Path(export_path)

        if export_path.exists() and not overwrite:
            raise FileExistsError(f"File already exists at the provided export path. To overwrite, pass `overwrite=True` into TOCFile.Export().")

        text = "".join(node.RawText for node in self._AST.Lines)
        with open(export_path, "w", encoding="utf-8", newline="") as f:
            f.write(text)

    def get_all_addon_file_names(self) -> List[str]:
        return [f.FileEntry.export() for f in self.Files]

    def can_load_addon(self, context: TOCEvaluationContext) -> tuple[bool, TOCAddonLoadError]:
        if self.Dependencies is not None and len(self.Dependencies) > 0:
            deps_fulfilled = True
            for dep in self.Dependencies:
                if not context.is_addon_loaded(dep):
                    deps_fulfilled = False
                    break

            if not deps_fulfilled:
                return False, TOCAddonLoadError.MissingDependency

        if self.AllowLoad is not None and not self.AllowLoad.evaluate(context):
            return False, TOCAddonLoadError.WrongEnvironment
        elif self.AllowLoadGameType is not None and not self.AllowLoadGameType.evaluate(context):
            return False, TOCAddonLoadError.WrongGameType
        elif self.AllowLoadTextLocale is not None and not self.AllowLoadTextLocale.evaluate(context):
            return False, TOCAddonLoadError.WrongTextLocale

        return True, TOCAddonLoadError.Success

    def add_dependency(self, dep_name: str, required: bool = False):
        attr_name = "Dependencies" if required else "OptionalDeps"
        attr = getattr(self, attr_name, None)
        if attr is None:
            if not dep_name.endswith("\n"):
                value_name = dep_name
                dep_name += "\n"
            else:
                value_name = dep_name.removesuffix("\n")
            attr = TOCListValue(dep_name, [value_name])
            setattr(self, attr_name, attr)
            return

        attr: TOCListValue
        attr.append(dep_name, dep_name)
