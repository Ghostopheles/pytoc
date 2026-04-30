from pathlib import Path
from typing import Any, Optional, Union, get_args, get_origin

from .enums import *
from .file_entry import *
from .parser import *
from .directives import *
from .shared import *
from .utils import StringToBoolean
from .context import TOCEvaluationContext


def _build_directive_raw(raw_name: str, locale: Optional[Union[TOCTextLocale, str]], value_str: str) -> str:
    if locale is not None:
        loc_str = locale.name if isinstance(locale, TOCTextLocale) else str(locale)
        suffix = f"-{loc_str}"
    else:
        suffix = ""
    if not value_str.endswith("\n"):
        value_str = value_str + "\n"
    return f"{PYTOC_DIRECTIVE_PREFIX} {raw_name}{suffix}: {value_str}"


def _value_to_str(value: Any) -> str:
    if isinstance(value, TOCListValue):
        return ", ".join(str(v) for v in value.Value)
    if isinstance(value, (TOCBoolType, TOCIntValue)):
        return str(value.Value)
    if isinstance(value, TOCEnumValue):
        return str(value.Value)
    if isinstance(value, TOCCondition):
        return ", ".join(str(v) for v in value.Values)
    if isinstance(value, TOCLocalizedDirectiveValue):
        return value.get_translation(PYTOC_DEFAULT_LOCALE) or ""
    if isinstance(value, TOCUnkValue):
        return value.Value
    if isinstance(value, (list, tuple, set, frozenset)):
        return ", ".join(str(v) for v in value)
    return str(value)


def _normalize_locale_key(loc) -> Optional[TOCTextLocale]:
    if loc is None:
        return None
    if isinstance(loc, TOCTextLocale):
        return loc
    if isinstance(loc, str) and loc in TOCTextLocale.__members__:
        return TOCTextLocale[loc]
    return None


class _DirectiveDescriptor:
    __slots__ = ("spec",)

    def __init__(self, spec: TOCDirectiveSpec):
        self.spec = spec

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance._get_directive(self.spec)

    def __set__(self, instance, value):
        instance._set_directive(self.spec, value)


class _TOCFileMeta(type):
    def __new__(mcls, name, bases, ns):
        cls = super().__new__(mcls, name, bases, ns)
        for spec in TOC_DIRECTIVES.values():
            setattr(cls, spec.Name, _DirectiveDescriptor(spec))
        return cls


class TOCFile(metaclass=_TOCFileMeta):
    Interface: Optional[TOCListValue[int]]
    Title: Optional[TOCLocalizedDirectiveValue]
    Author: Optional[TOCLocalizedDirectiveValue]
    Version: Optional[TOCLocalizedDirectiveValue]
    Notes: Optional[TOCLocalizedDirectiveValue]
    Group: Optional[TOCLocalizedDirectiveValue]
    Category: Optional[TOCLocalizedDirectiveValue]
    SavedVariables: Optional[TOCListValue[str]]
    SavedVariablesPerCharacter: Optional[TOCListValue[str]]
    SavedVariablesMachine: Optional[TOCListValue[str]]
    IconTexture: Optional[TOCLocalizedDirectiveValue]
    IconAtlas: Optional[TOCLocalizedDirectiveValue]
    AddonCompartmentFunc: Optional[TOCLocalizedDirectiveValue]
    AddonCompartmentFuncOnEnter: Optional[TOCLocalizedDirectiveValue]
    AddonCompartmentFuncOnLeave: Optional[TOCLocalizedDirectiveValue]
    LoadOnDemand: Optional[TOCBoolType]
    LoadFirst: Optional[TOCBoolType]
    LoadWith: Optional[TOCListValue[str]]
    LoadManagers: Optional[TOCListValue[str]]
    Dependencies: Optional[TOCListValue[str]]
    OptionalDeps: Optional[TOCListValue[str]]
    DefaultState: Optional[TOCBoolType]
    OnlyBetaAndPTR: Optional[TOCBoolType]
    LoadSavedVariablesFirst: Optional[TOCBoolType]
    AllowLoad: Optional[TOCAllowLoad]
    AllowLoadGameType: Optional[TOCAllowLoadGameType]
    AllowLoadTextLocale: Optional[TOCAllowLoadTextLocale]
    UseSecureEnvironment: Optional[TOCBoolType]
    AllowAddOnTableAccess: Optional[TOCBoolType]

    def __init__(self, file_path: Optional[Union[str, Path]] = None):
        self._AST: TOCAST = TOCAST.empty()
        if file_path is not None:
            self.load_file(file_path)

    def __repr__(self):
        return f"TOCFile(lines={len(self._AST.Lines)})"

    def _iter_directive_nodes(self, canonical: str):
        for i, n in enumerate(self._AST.Lines):
            if isinstance(n, TOCDirectiveLine) and not n.IsExtendedDirective and n.CanonicalName == canonical:
                yield i, n

    def _directive_section_end_idx(self) -> int:
        last_directive = -1
        first_file = None
        for i, n in enumerate(self._AST.Lines):
            if isinstance(n, TOCDirectiveLine):
                last_directive = i
            elif isinstance(n, TOCFileEntryLine) and first_file is None:
                first_file = i
        if last_directive >= 0:
            return last_directive + 1
        if first_file is not None:
            return first_file
        return len(self._AST.Lines)

    def _insertion_idx_for_directive(self, canonical: str) -> int:
        last = -1
        for i, n in enumerate(self._AST.Lines):
            if isinstance(n, TOCDirectiveLine) and not n.IsExtendedDirective and n.CanonicalName == canonical:
                last = i
        if last >= 0:
            return last + 1
        return self._directive_section_end_idx()

    def _make_directive_node(self, canonical: str, raw_name: str, locale: Optional[TOCTextLocale], value: Any) -> TOCDirectiveLine:
        raw = _build_directive_raw(raw_name, locale, _value_to_str(value))
        return TOCDirectiveLine(
            LineNumber=0,
            RawText=raw,
            CanonicalName=canonical,
            RawName=raw_name,
            Locale=locale,
            Value=value,
            IsExtendedDirective=False,
        )

    def _remove_indices(self, indices):
        for i in sorted(indices, reverse=True):
            del self._AST.Lines[i]

    def _get_directive(self, spec: TOCDirectiveSpec):
        nodes = list(self._iter_directive_nodes(spec.Name))
        if not nodes:
            return None

        if spec.CanBeLocalized:
            agg = TOCLocalizedDirectiveValue.__new__(TOCLocalizedDirectiveValue)
            agg.Raw = nodes[0][1].RawText
            agg.Localizations = {}
            for _, n in nodes:
                loc = _normalize_locale_key(n.Locale) or PYTOC_DEFAULT_LOCALE
                if isinstance(n.Value, TOCLocalizedDirectiveValue):
                    text = n.Value.get_translation(PYTOC_DEFAULT_LOCALE)
                else:
                    text = _value_to_str(n.Value)
                if text is not None:
                    agg.Localizations[loc] = text
            return agg

        if get_origin(spec.ValueType) is TOCListValue:
            (lt,) = get_args(spec.ValueType)
            all_values = []
            raws = []
            for _, n in nodes:
                if isinstance(n.Value, TOCListValue):
                    all_values.extend(n.Value.Value)
                    raws.append(n.Value.Raw)
                else:
                    all_values.append(n.Value)
                    raws.append(str(n.Value))
            return TOCListValue[lt](", ".join(r.rstrip("\n") for r in raws), all_values)

        return nodes[0][1].Value

    def _coerce_scalar(self, spec: TOCDirectiveSpec, value: Any):
        vt = spec.ValueType
        if vt is TOCBoolType and not isinstance(value, TOCBoolType):
            if isinstance(value, str):
                return TOCBoolType(value, StringToBoolean(value))
            return TOCBoolType(str(int(bool(value))), bool(value))
        if vt is TOCIntValue and not isinstance(value, TOCIntValue):
            return TOCIntValue(str(value), int(value))
        if isinstance(vt, type) and issubclass(vt, TOCCondition) and not isinstance(value, TOCCondition):
            if isinstance(value, (list, tuple, set, frozenset)):
                return vt(frozenset(value))
        return value

    def _set_directive(self, spec: TOCDirectiveSpec, value: Any):
        existing = list(self._iter_directive_nodes(spec.Name))
        canonical = spec.Name

        if value is None:
            self._remove_indices([i for i, _ in existing])
            return

        if spec.CanBeLocalized:
            if isinstance(value, str):
                value = TOCLocalizedDirectiveValue(value)
            elif not isinstance(value, TOCLocalizedDirectiveValue):
                value = TOCLocalizedDirectiveValue(str(value))

            existing_by_locale: dict[TOCTextLocale, list] = {}
            for i, n in existing:
                key = _normalize_locale_key(n.Locale) or PYTOC_DEFAULT_LOCALE
                existing_by_locale.setdefault(key, []).append((i, n))

            new_locales = set(value.Localizations.keys())

            for loc, text in value.Localizations.items():
                if loc in existing_by_locale:
                    for _, n in existing_by_locale[loc]:
                        n.Value = TOCLocalizedDirectiveValue(text)
                        n.RawText = _build_directive_raw(n.RawName, n.Locale, text)
                else:
                    line_locale = None if loc == PYTOC_DEFAULT_LOCALE else loc
                    new_node = self._make_directive_node(canonical, canonical, line_locale, TOCLocalizedDirectiveValue(text))
                    self._AST.Lines.insert(self._insertion_idx_for_directive(canonical), new_node)

            obsolete = []
            for loc, lst in existing_by_locale.items():
                if loc not in new_locales:
                    obsolete.extend(i for i, _ in lst)
            self._remove_indices(obsolete)
            return

        if get_origin(spec.ValueType) is TOCListValue:
            (lt,) = get_args(spec.ValueType)
            if isinstance(value, TOCListValue):
                items = list(value.Value)
            elif isinstance(value, (list, tuple)):
                items = list(value)
            elif isinstance(value, str):
                items = [v.strip() for v in value.split(",") if v.strip()]
            else:
                items = [value]

            converted = []
            for v in items:
                if isinstance(v, lt):
                    converted.append(v)
                elif isinstance(v, str) and lt is int:
                    converted.append(int(v))
                else:
                    converted.append(lt(v))

            new_lv = TOCListValue[lt](", ".join(str(v) for v in converted), converted)

            if existing:
                _, first = existing[0]
                first.Value = new_lv
                first.RawText = _build_directive_raw(first.RawName, first.Locale, _value_to_str(new_lv))
                self._remove_indices([i for i, _ in existing[1:]])
            else:
                node = self._make_directive_node(canonical, canonical, None, new_lv)
                self._AST.Lines.insert(self._directive_section_end_idx(), node)
            return

        # scalar
        value = self._coerce_scalar(spec, value)
        if existing:
            _, first = existing[0]
            first.Value = value
            first.RawText = _build_directive_raw(first.RawName, first.Locale, _value_to_str(value))
            self._remove_indices([i for i, _ in existing[1:]])
        else:
            node = self._make_directive_node(canonical, canonical, None, value)
            self._AST.Lines.insert(self._directive_section_end_idx(), node)

    @property
    def Files(self) -> list[TOCFileEntryLine]:
        return [n for n in self._AST.Lines if isinstance(n, TOCFileEntryLine)]

    @property
    def Comments(self) -> list[TOCCommentLine]:
        return [n for n in self._AST.Lines if isinstance(n, TOCCommentLine)]

    @property
    def ExtendedDirectives(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for n in self._AST.Lines:
            if isinstance(n, TOCDirectiveLine) and n.IsExtendedDirective:
                if isinstance(n.Value, TOCLocalizedDirectiveValue):
                    text = n.Value.get_translation(PYTOC_DEFAULT_LOCALE)
                else:
                    text = _value_to_str(n.Value)
                out.setdefault(n.RawName, text)
        return out

    @property
    def UnknownDirectives(self) -> dict[str, TOCUnkValue]:
        out: dict[str, TOCUnkValue] = {}
        for n in self._AST.Lines:
            if isinstance(n, TOCDirectiveLine) and not n.IsExtendedDirective and isinstance(n.Value, TOCUnkValue):
                out.setdefault(n.CanonicalName, n.Value)
        return out

    def load_file(self, file_path: Union[str, Path]):
        if not isinstance(file_path, Path):
            file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"TOC file does not exist at the given path: '{file_path}'")
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
        self._AST = TOCAST.from_lines(lines)

    def export(self, export_path: Union[str, Path], overwrite: bool = False):
        if not isinstance(export_path, Path):
            export_path = Path(export_path)
        if export_path.exists() and not overwrite:
            raise FileExistsError(f"File already exists at '{export_path}'. Pass overwrite=True to replace it.")
        text = "".join(n.RawText for n in self._AST.Lines)
        with open(export_path, "w", encoding="utf-8", newline="") as f:
            f.write(text)

    def get_all_addon_file_names(self) -> list[str]:
        return [n.FileEntry.export() for n in self.Files]

    def get_raw_files(self) -> list[str]:
        return [n.FileEntry.RawFilePath for n in self.Files]

    def add_file(self, file_path: str):
        if not file_path.endswith("\n"):
            file_path = file_path + "\n"
        node = parse_file_line(0, file_path)
        self._AST.Lines.append(node)

    def remove_file(self, index: int):
        ast_indices = [i for i, n in enumerate(self._AST.Lines) if isinstance(n, TOCFileEntryLine)]
        del self._AST.Lines[ast_indices[index]]

    def update_file_path(self, index: int, new_path: str):
        ast_indices = [i for i, n in enumerate(self._AST.Lines) if isinstance(n, TOCFileEntryLine)]
        if not new_path.endswith("\n"):
            new_path = new_path + "\n"
        self._AST.Lines[ast_indices[index]] = parse_file_line(0, new_path)

    def add_empty_line(self):
        self._AST.Lines.append(TOCEmptyLine(0, "\n"))

    def add_dependency(self, dep_name: str, required: bool = False):
        spec_name = "Dependencies" if required else "OptionalDeps"
        spec = TOC_DIRECTIVES[spec_name]
        current = self._get_directive(spec)
        if current is None:
            new_lv = TOCListValue[str](dep_name, [dep_name])
        else:
            new_values = list(current.Value) + [dep_name]
            new_lv = TOCListValue[str](", ".join(new_values), new_values)
        self._set_directive(spec, new_lv)

    def can_load_addon(self, context: TOCEvaluationContext) -> tuple[bool, TOCAddonLoadError]:
        deps = self.Dependencies
        if deps is not None and len(deps) > 0:
            for dep in deps:
                if not context.is_addon_loaded(dep):
                    return False, TOCAddonLoadError.MissingDependency

        if self.AllowLoad is not None and not self.AllowLoad.evaluate(context):
            return False, TOCAddonLoadError.WrongEnvironment
        if self.AllowLoadGameType is not None and not self.AllowLoadGameType.evaluate(context):
            return False, TOCAddonLoadError.WrongGameType
        if self.AllowLoadTextLocale is not None and not self.AllowLoadTextLocale.evaluate(context):
            return False, TOCAddonLoadError.WrongTextLocale

        return True, TOCAddonLoadError.Success
