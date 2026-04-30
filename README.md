![Tests](https://github.com/Ghostopheles/pytoc/actions/workflows/tests.yml/badge.svg)

# pytoc

A Python package for reading and writing World of Warcraft addon [TOC](https://warcraft.wiki.gg/wiki/TOC_format) files.

## Installation

```
pip install wow-pytoc 
```

## Usage

### Reading a TOC file

```py
from pytoc import TOCFile, TOCTextLocale

toc = TOCFile("path/to/MyAddon.toc")

print(toc.Interface)          # TOCListValue[int] of all interface versions
print(toc.Title)              # base (enUS) value
print(toc.Title.get_translation(TOCTextLocale.frFR))
print(toc.ExtendedDirectives.get("X-Website"))
print(toc.UnknownDirectives.get("SomeUnknownField"))

for dep in toc.Dependencies:
    print(f"Required: {dep}")
for dep in toc.OptionalDeps:
    print(f"Optional: {dep}")

for file_line in toc.Files:
    entry = file_line.FileEntry
    print(entry.export())
```

### Writing a TOC file

```py
from pytoc import TOCFile, TOCLocalizedDirectiveValue, TOCListValue, TOCTextLocale

toc = TOCFile()
toc.Interface = TOCListValue("110000", [110000])
toc.Author = TOCLocalizedDirectiveValue("Ghost")
toc.Title = TOCLocalizedDirectiveValue(
    "MyAddon",
    {TOCTextLocale.frFR: "MonAddon", TOCTextLocale.deDE: "MeinAddon"},
)

toc.add_file("MyAddon.lua")
toc.add_file("MyAddon.xml")
toc.add_dependency("totalRP3", required=False)

toc.export("path/to/MyAddon.toc", overwrite=True)
```

### Round-trip

Reading and exporting an existing file produces byte-identical output.

```py
toc = TOCFile("MyAddon.toc")
toc.Author = TOCLocalizedDirectiveValue("NewAuthor")
toc.export("MyAddon.toc", overwrite=True)
# Every line unchanged except ## Author:
```

### Load condition simulation

`TOCEvaluationContext` lets you simulate whether an addon (or a specific file entry) would load under given game conditions.

```py
from pytoc import (
    TOCFile, TOCEvaluationContext, TOCAllowLoadGameType,
    TOCGameType, TOCEnvironment, TOCTextLocale,
)

ctx = TOCEvaluationContext(TOCGameType.Mainline, TOCEnvironment.Global, TOCTextLocale.enUS)

toc = TOCFile("MyAddon.toc")
can_load, err = toc.can_load_addon(ctx)

# Per-file entry
for file_line in toc.Files:
    if file_line.FileEntry.should_load(ctx):
        print(file_line.FileEntry.resolve_path(ctx))
```

## Notes/Quirks

> [!NOTE]
> - `Dependencies` and `OptionalDeps` are `TOCListValue[str]`; use `add_dependency(name, required=True/False)` to append safely.
> - `X-` prefixed fields are available via `toc.ExtendedDirectives` (a `dict[str, str]`).
> - Unrecognised directives (non-`X-`, not in the known list) land in `toc.UnknownDirectives` and are **not** exported.
> - Multiple occurrences of the same directive are merged - last value wins for scalars, values are combined for list fields.
> - Comments and blank lines are preserved on round-trip.
