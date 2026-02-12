import re

from dataclasses import dataclass
from typing import Optional, Any, get_args, get_origin

from .enums import *
from .file_entry import *
from .directives import *

FILE_CONDITION_VARIABLE_PATTERN = re.compile(r"\[([^\]]+)\]")

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


class TOCLineNode:
    LineNumber: int
    RawText: str
    AllowDuplicates: bool = True


@dataclass
class TOCEmptyLine(TOCLineNode):
    LineNumber: int
    RawText: str


@dataclass
class TOCCommentLine(TOCLineNode):
    LineNumber: int
    RawText: str
    Value: str


@dataclass
class TOCFileEntryLine(TOCLineNode):
    LineNumber: int
    RawText: str
    FileEntry: TOCFileEntry


@dataclass
class TOCUnrecognizedLine(TOCLineNode):
    LineNumber: int
    RawText: str


@dataclass
class TOCDirectiveLine(TOCLineNode):
    LineNumber: int
    RawText: str
    CanonicalName: str
    RawName: str
    Locale: Optional[str]
    Value: Any
    ExtendedName: str = None
    IsExtendedDirective: bool = False
    AllowDuplicates: bool = True


# abstract syntax tree pog


def cleanup_text(text: str) -> str:
    """Strips whitespace and removes trailing newlines from the provided string"""
    return text.strip().removesuffix("\n")


def is_empty(line: str) -> bool:
    return not line or len(line.strip()) == 0


def is_directive(line: str) -> bool:
    return line.startswith("## ") and ":" in line


def is_comment(line: str) -> bool:
    return len(line) > 1 and line.startswith("#") and not is_directive(line)


def is_extended_directive(directive_name: str) -> bool:
    return directive_name.lower().startswith("x-")


def resolve_directive_name_and_locale(raw: str) -> tuple[str, Optional[str]]:
    if "-" in raw:
        if raw.startswith("X-"):
            parts = raw.rsplit("-", 1)
            base, maybe_locale = parts[0], parts[1]
            if not maybe_locale in list(TOCTextLocale):
                base = f"{base}-{maybe_locale}"
                locale = None
            else:
                locale = TOCTextLocale[maybe_locale]
        else:
            base, locale = raw.split("-", 1)
    else:
        base, locale = raw, None

    canonical = ALIAS_TO_CANONICAL.get(base.lower(), base)
    return canonical, locale


def parse_typed_value(raw_value: str, spec: TOCDirectiveSpec):
    _type = spec.ValueType

    if _type is TOCBoolType:
        val = StringToBoolean(raw_value)
        return TOCBoolType(raw_value, val)

    if _type is TOCIntValue:
        try:
            val = int(raw_value)
        except ValueError:
            raise ValueError(f"Expected integer for {spec.Name}, got: {raw_value}")
        return TOCIntValue(raw_value, val)

    if _type is TOCLocalizedDirectiveValue:
        val = str(raw_value)
        return TOCLocalizedDirectiveValue(val)

    if get_origin(_type) is TOCListValue:
        (list_type,) = get_args(_type)
        values = []

        if isinstance(raw_value, list_type):
            values.append(raw_value)
        elif isinstance(raw_value, str):
            for v in raw_value.split(","):
                if isinstance(v, str):
                    v = v.strip()
                if not isinstance(v, list_type):
                    v = list_type(v)
                values.append(v)

        return TOCListValue[list_type](raw_value, values)

    if get_origin(_type) is TOCEnumValue:
        (enum_type,) = get_args(_type)
        return TOCEnumValue[enum_type](raw_value, enum_type[raw_value.strip()])

    if _type in CONDITION_DIRECTIVES_TO_CLASS.values():
        if not isinstance(raw_value, list):
            raw_value = frozenset([raw_value])
        return _type(raw_value)

    if not isinstance(raw_value, _type):
        return _type(raw_value)

    return raw_value


def parse_directive_line(line_no: int, line: str) -> Optional[TOCDirectiveLine]:
    name, value = line.split(": ", 1)
    name = name.split(" ", 1)[1]
    canonical, locale = resolve_directive_name_and_locale(name)
    is_extended = is_extended_directive(canonical)

    value.removesuffix("\n")

    if is_extended:  # use raw value for 'X-' directives
        node = TOCLocalizedDirectiveValue(value)
        node.set_translation(locale, cleanup_text(value))
        parsed_value = node
    else:
        spec = TOC_DIRECTIVES.get(canonical)
        if spec is None:
            for spec_name, func in ALIAS_FUNCTIONS.items():
                if func(name):
                    spec = TOC_DIRECTIVES.get(spec_name)

        if spec is None:
            # this is an unknown creatura
            parsed_value = TOCUnkValue(value, cleanup_text(value))
        else:
            parsed_value = parse_typed_value(value, spec)

    return TOCDirectiveLine(
        RawText=line,
        CanonicalName=canonical,
        RawName=name,
        Locale=locale,
        Value=parsed_value,
        IsExtendedDirective=is_extended,
        LineNumber=line_no,
    )


def split_file_path_and_conditions(line: str):
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
            return path, FILE_CONDITION_VARIABLE_PATTERN.findall(rest)

    return line, []


def parse_condition(text: str) -> Optional[TOCCondition]:
    name, *rest = text.split(None, 1)
    args = []

    if rest:
        args = [a.strip() for a in rest[0].split(",")]

    condition_class = CONDITION_DIRECTIVES_TO_CLASS.get(name)

    if condition_class:
        return condition_class(frozenset(args))

    return None


def parse_file_line(line_no: int, line: str):
    raw_path, condition_texts = split_file_path_and_conditions(line)
    conditions = [parse_condition(text) for text in condition_texts]
    if not conditions:
        return TOCFileEntryLine(
            line_no,
            line,
            FileEntry=TOCFileEntry(raw_path),
        )

    return TOCFileEntryLine(
        line_no,
        line,
        FileEntry=TOCFileEntry(raw_path, conditions),
    )


def parse_comment(line_no: int, line: str) -> TOCCommentLine:
    value = cleanup_text(line.lstrip("#"))
    return TOCCommentLine(line_no, line, value)


@dataclass
class TOCAST:
    Lines: list[TOCLineNode]

    @classmethod
    def from_lines(cls, lines: List[str]):
        toc_lines = []
        for line_no, raw_line in enumerate(lines):
            if is_empty(raw_line):
                toc_lines.append(TOCEmptyLine(line_no, raw_line))
            elif is_directive(raw_line):
                node = parse_directive_line(line_no, raw_line)
                if node:
                    toc_lines.append(node)
            elif is_comment(raw_line):
                node = parse_comment(line_no, raw_line)
                toc_lines.append(node)
            else:
                node = parse_file_line(line_no, raw_line)
                toc_lines.append(node)

        return cls(toc_lines)

    @classmethod
    def empty(cls):
        lines = []
        return cls(lines)
