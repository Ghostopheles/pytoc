from pathlib import Path
from dataclasses import dataclass, field, InitVar
from typing import Optional, Union, List, Any, get_args

from .enums import *
from .file_entry import *
from .parser import *
from .shared import *


@dataclass
class TOCFileBinding:
    """A binding between a file and it's node in the AST"""

    LocalFile: TOCFileEntryLine
    NodeIndex: int


@dataclass
class TOCDirectiveBinding:
    """A binding between a given TOC directive and it's nodes in the AST"""

    DirectiveName: str
    NodeIndices: list[int]


@dataclass
class TOCFile:
    _file_path: InitVar[Optional[Union[str, Path]]] = None
    _AST: Optional[TOCAST] = field(default=None, init=False, repr=True)

    _attr_bindings: dict[str, TOCDirectiveBinding] = field(default_factory=dict, init=False, repr=False)
    _attr_dirty: bool = field(default=False, init=False, repr=False)

    _file_bindings: list[TOCFileBinding] = field(default_factory=list, init=False, repr=False)
    _files_dirty: bool = field(default=False, init=False, repr=False)

    _initialized: bool = field(default=False, init=False, repr=False)

    Interface: Optional[TOCListValue[int]] = field(default=None, init=False)
    Title: Optional[TOCLocalizedDirectiveValue] = field(default=None, init=False)
    Author: Optional[TOCLocalizedDirectiveValue] = field(default=None, init=False)
    Version: Optional[TOCLocalizedDirectiveValue] = field(default=None, init=False)
    Notes: Optional[TOCLocalizedDirectiveValue] = field(default=None, init=False)
    Group: Optional[TOCLocalizedDirectiveValue] = field(default=None, init=False)
    Category: Optional[TOCLocalizedDirectiveValue] = field(default=None, init=False)
    SavedVariables: Optional[TOCListValue[str]] = field(default=None, init=False)
    SavedVariablesPerCharacter: Optional[TOCListValue[str]] = field(default=None, init=False)
    SavedVariablesMachine: Optional[TOCListValue[str]] = field(default=None, init=False)
    IconTexture: Optional[TOCLocalizedDirectiveValue] = field(default=None, init=False)
    IconAtlas: Optional[TOCLocalizedDirectiveValue] = field(default=None, init=False)
    AddonCompartmentFunc: Optional[TOCLocalizedDirectiveValue] = field(default=None, init=False)
    AddonCompartmentFuncOnEnter: Optional[TOCLocalizedDirectiveValue] = field(default=None, init=False)
    AddonCompartmentFuncOnLeave: Optional[TOCLocalizedDirectiveValue] = field(default=None, init=False)
    LoadOnDemand: Optional[TOCBoolType] = field(default=None, init=False)
    LoadFirst: Optional[TOCBoolType] = field(default=None, init=False)
    LoadWith: Optional[TOCListValue[str]] = field(default=None, init=False)
    LoadManagers: Optional[TOCListValue[str]] = field(default=None, init=False)
    Dependencies: Optional[TOCListValue[str]] = field(default=None, init=False)
    OptionalDeps: Optional[TOCListValue[str]] = field(default=None, init=False)
    DefaultState: Optional[TOCBoolType] = field(default=None, init=False)
    OnlyBetaAndPTR: Optional[TOCBoolType] = field(default=None, init=False)
    LoadSavedVariablesFirst: Optional[TOCBoolType] = field(default=None, init=False)
    AllowLoad: Optional[TOCAllowLoad] = field(default=None, init=False)
    AllowLoadGameType: Optional[TOCAllowLoadGameType] = field(default=None, init=False)
    AllowLoadTextLocale: Optional[TOCAllowLoadTextLocale] = field(default=None, init=False)
    UseSecureEnvironment: Optional[TOCBoolType] = field(default=None, init=False)

    ExtendedDirectives: Optional[dict[str, str]] = field(default_factory=dict, init=False)
    UnknownDirectives: Optional[dict[str, TOCUnkValue]] = field(default_factory=dict, init=False)
    Files: Optional[list[TOCFileEntryLine]] = field(default_factory=list, init=False)
    Comments: Optional[TOCListValue[TOCCommentLine]] = field(default_factory=list, init=False)

    def __set(self, name: str, value: Any):
        # using object.__setattr__ to avoid calling into our own hook uwu
        object.__setattr__(self, name, value)

    def __post_init__(self, _file_path: str | Path = None):
        if _file_path is not None:
            self.load_file(_file_path)
        else:
            self.setup_empty()

        self.__set("_initialized", True)

    def __setattr__(self, name: str, value: Any):
        if not self._initialized or name.startswith("_"):
            self.__set(name, value)
            return

        old_value = getattr(self, name, None)
        self.__set(name, value)

        if name in TOC_DIRECTIVES or name in CONDITION_DIRECTIVES_TO_CLASS:
            if old_value != value:
                self.__set("_attr_dirty", True)

    def setup_empty(self):
        ast = TOCAST.empty()
        self.set_ast(ast)

    def __add_directive_binding(self, attr_name: str, node_index: int):
        if attr_name not in self._attr_bindings:
            self._attr_bindings[attr_name] = TOCDirectiveBinding(DirectiveName=attr_name, NodeIndices=[node_index])
        else:
            self._attr_bindings[attr_name].NodeIndices.append(node_index)

    def __add_file_binding(self, node: TOCFileEntryLine, node_index: int):
        self._file_bindings.append(TOCFileBinding(node, node_index))

    def __process_directive_line(self, node: TOCDirectiveLine, node_index: int):
        if node.IsExtendedDirective:
            self.ExtendedDirectives.setdefault(node.RawName, node.Value)
            self.__add_directive_binding(node.RawName, node_index)

        elif isinstance(node.Value, TOCUnkValue):
            self.UnknownDirectives.setdefault(node.CanonicalName, node.Value)
            self.__add_directive_binding(node.CanonicalName, node_index)

        elif condition_class := CONDITION_DIRECTIVES_TO_CLASS.get(node.CanonicalName):
            self.__set(node.CanonicalName, condition_class(frozenset(node.Value)))
            self.__add_directive_binding(node.CanonicalName, node_index)

        else:
            if isinstance(node.Value, str):
                node.Value = node.Value.removesuffix("\n")

            spec = TOC_DIRECTIVES.get(node.CanonicalName)
            existing_attribute = getattr(self, node.CanonicalName, None)

            if existing_attribute is not None and isinstance(existing_attribute, TOCListValue):
                existing_attribute.append_line(node)
                self.__add_directive_binding(node.CanonicalName, node_index)
                return

            if spec is not None and spec.CanBeLocalized:
                locale = node.Locale if node.Locale is not None else PYTOC_DEFAULT_LOCALE
                if not isinstance(locale, TOCTextLocale):
                    locale = TOCTextLocale[locale]

                if existing_attribute is not None:
                    if PYTOC_CHECK_DUPLICATES and not spec.AllowDuplicates:
                        assert getattr(self, node.CanonicalName) is None, f"Attempt to register duplicate {node.CanonicalName} directive"

                    if isinstance(existing_attribute, TOCLocalizedDirectiveValue):
                        existing_attribute.set_translation(locale, node.Value)

                    self.__add_directive_binding(node.CanonicalName, node_index)
                    return
                else:
                    attr = TOCLocalizedDirectiveValue(node.RawText)
                    attr.set_translation(locale, node.Value)
                    self.__set(node.CanonicalName, attr)
                    self.__add_directive_binding(node.CanonicalName, node_index)
                    return

        self.__set(node.CanonicalName, node.Value)
        self.__add_directive_binding(node.CanonicalName, node_index)

    def __regenerate_directive_line(self, node: TOCDirectiveLine) -> str:
        locale_suffix = f"-{node.Locale}" if node.Locale else ""

        if isinstance(node.Value, TOCListValue):
            value_str = ", ".join(str(v) for v in node.Value.Value)  # Value on Value on Value! :(
        elif isinstance(node.Value, (TOCBoolType, TOCIntValue)):
            value_str = str(node.Value.Value)
        elif isinstance(node.Value, (list, tuple)):
            value_str = ", ".join(str(v) for v in node.Value)
        else:
            value_str = str(node.Value) if not isinstance(node.Value, str) else node.Value

        if not value_str.endswith("\n"):
            value_str += "\n"

        return f"{PYTOC_DIRECTIVE_PREFIX} {node.RawName}{locale_suffix}: {value_str}"

    def __generate_directive_raw_text(self, attr_name: str, value: Any):
        if isinstance(value, TOCListValue):
            value_str = ", ".join(str(v) for v in value.Value)
        else:
            value_str = str(value) if not isinstance(value, str) else value

        if not value_str.endswith("\n"):
            value_str += "\n"

        return f"{PYTOC_DIRECTIVE_PREFIX} {attr_name}: {value_str}"

    def __reindex_bindings_after(self, start_index: int):
        for binding in self._attr_bindings.values():
            binding.NodeIndices = [idx + 1 if idx >= start_index else idx for idx in binding.NodeIndices]

        for i, binding in enumerate(self._file_bindings):
            if binding.NodeIndex >= start_index:
                self._file_bindings[i] = TOCFileBinding(binding.LocalFile, binding.NodeIndex + 1)

    def __insert_new_directive(self, attr_name: str, value: Any):
        insert_at = 0
        for i, node in enumerate(self._AST.Lines):
            if isinstance(node, TOCDirectiveLine):
                insert_at = i + 1
            elif isinstance(node, TOCFileEntryLine):
                break

        new_node = TOCDirectiveLine(
            LineNumber=insert_at,
            RawText=self.__generate_directive_raw_text(attr_name, value),
            CanonicalName=attr_name,
            RawName=attr_name,
            Value=value,
            Locale=None,
            IsExtendedDirective=False,
        )

        self._AST.Lines.insert(insert_at, new_node)
        self.__add_directive_binding(attr_name, insert_at)
        self.__reindex_bindings_after(insert_at)

    def set_ast(self, ast: TOCAST, overwrite: bool = False):
        if self._initialized and not overwrite:
            raise Exception("Attempt to set a new AST on an initialized TOCFile. To overwrite, pass `overwrite=True` into TOCFile.set_ast().")

        self._attr_bindings.clear()
        self._file_bindings.clear()

        for i, node in enumerate(ast.Lines):
            if isinstance(node, TOCFileEntryLine):
                self.Files.append(node)
                self.__add_file_binding(node, i)
                continue

            if isinstance(node, TOCDirectiveLine):
                self.__process_directive_line(node, i)

            elif isinstance(node, TOCCommentLine):
                self.Comments.append(node)

        self.__set("_AST", ast)

    def sync_attributes_to_ast(self):
        if not self._attr_dirty:
            return

        for attr_name, binding in self._attr_bindings.items():
            attr_value = getattr(self, attr_name, None)
            if attr_value is None:
                continue

            for node_idx in binding.NodeIndices:
                if node_idx >= len(self._AST.Lines):
                    continue

                node = self._AST.Lines[node_idx]
                if not isinstance(node, TOCDirectiveLine):
                    continue

                if isinstance(attr_value, TOCLocalizedDirectiveValue):
                    locale = node.Locale if node.Locale else PYTOC_DEFAULT_LOCALE
                    if not isinstance(locale, TOCTextLocale):
                        locale = TOCTextLocale[locale] if locale else PYTOC_DEFAULT_LOCALE

                    new_value = attr_value.get_translation(locale)
                    if new_value is not None:
                        node.Value = new_value
                        node.RawText = self.__regenerate_directive_line(node)

                elif isinstance(attr_value, TOCListValue):
                    node.Value = attr_value.Value
                    node.RawText = self.__regenerate_directive_line(node)

                elif isinstance(attr_value, TOCCondition):
                    node.Value = list(attr_value.Values)
                    node.RawText = self.__regenerate_directive_line(node)

                else:
                    node.Value = attr_value
                    node.RawText = self.__regenerate_directive_line(node)

        self.__set("_attr_dirty", False)

    def rebuild_file_section(self):
        ast = self._AST
        indices = [i for i, n in enumerate(ast.Lines) if isinstance(n, TOCFileEntryLine)]

        if not indices:
            insert_at = len(ast.Lines)
        else:
            insert_at = indices[0]
            for i in reversed(indices):
                del ast.Lines[i]

        new_bindings = []

        for lf in self.Files:
            node = TOCFileEntryLine(LineNumber=lf.LineNumber, RawText=lf.RawText, FileEntry=lf.FileEntry)
            ast.Lines.insert(insert_at, node)
            new_bindings.append(TOCFileBinding(lf, insert_at))
            insert_at += 1

        self.__set("_file_bindings", new_bindings)
        self.__set("_files_dirty", False)

    def update_file_node(self, node_index: int, local_file: TOCFileEntryLine):
        node = self._AST.Lines[node_index]

        node: TOCFileEntryLine
        node.FileEntry = local_file.FileEntry
        node.RawText = local_file.RawText

    def sync_files_to_ast(self):
        if not self._files_dirty:
            return

        old_bindings = self._file_bindings
        new_files = self.Files

        if len(old_bindings) == len(new_files):
            for binding, new_file in zip(old_bindings, new_files):
                self.update_file_node(binding.NodeIndex, new_file)
        else:
            self.rebuild_file_section()

        self.__set("_files_dirty", False)

    def sync_all(self):
        self.sync_attributes_to_ast()
        self.sync_files_to_ast()

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
        self.sync_all()

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

            self.__insert_new_directive(attr_name, attr)
            return

        attr: TOCListValue
        attr.append(dep_name, dep_name)
        self.__set("_attr_dirty", True)

    def update_file_path(self, index: int, new_path: str):
        local_file = self.Files[index]
        new_file = parse_file_line(local_file.LineNumber, new_path)

        del self.Files[index]
        self.Files.insert(index, new_file)

        self.__set("_files_dirty", True)

    def add_file(self, file_path: str):
        if not self.Files:
            line_number = 1
        else:
            last_line_number = self.Files[-1].LineNumber
            line_number = last_line_number + 1

        if not file_path.endswith("\n"):
            file_path += "\n"

        new_file = parse_file_line(line_number, file_path)
        self.Files.append(new_file)

        self.__set("_files_dirty", True)

    def remove_file(self, index: int):
        del self.Files[index]
        del self._file_bindings[index]

        self.__set("_files_dirty", True)

    def set_directive(self, directive: str, value: Any):
        canonical_name = ALIAS_TO_CANONICAL.get(directive.lower())
        spec = TOC_DIRECTIVES.get(canonical_name, None)
        if spec is None:
            print("SPEC IS NONE! BARK BARK BARK")
            return

        spec: TOCDirectiveSpec
        if get_origin(spec.ValueType) is TOCListValue and isinstance(value, list):
            value = ", ".join([str(v) for v in value])

        if spec.ValueType is TOCBoolType:
            value = str(value)

        node = parse_typed_value(value, spec)
        if not isinstance(node, TOCCondition):
            if not node.Raw.endswith("\n"):
                node.Raw += "\n"

        if spec.ValueType is TOCLocalizedDirectiveValue:
            node.set_translation(PYTOC_DEFAULT_LOCALE, value)

        self.__insert_new_directive(directive, value)
        self.__set(canonical_name, node)
        self.__set("_attr_dirty", True)

    def add_empty_line(self):
        line_number = len(self._AST.Lines) + 1
        line = TOCEmptyLine(line_number, "\n")

        self._AST.Lines.insert(line_number, line)
