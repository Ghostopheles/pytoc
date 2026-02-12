![Tests](https://github.com/Ghostopheles/pytoc/actions/workflows/tests.yml/badge.svg)

# pytoc

A Python package for reading and writing World of Warcraft addon [TOC](https://warcraft.wiki.gg/wiki/TOC_format) files.

> [!WARNING]
> pytoc is currently in the midst of a rewrite to better support faithful imports, exports, and load order simulation. Some information may be outdated or incorrect.

## Installation

You can install this package via `pip`.

```
pip install wow-pytoc
```

## Usage

Reading a TOC file:
```py
from pytoc import *

file_path: str = "X:/path/to/my/addon.toc"
toc = TOCFile(file_path)

print(toc.Interface)
print(toc.Title)
print(toc.LocalizedTitle["frFR"])
print(toc.AdditionalFields["X-Website"])

for file in toc.Files:
    file: TOCFileEntry
    print(file)
    if file.Conditions:
        for condition in file.Conditions:
            print(condition.export())

for dep in toc.Dependencies
    dep: TOCDependency
    print(f"Dependency Name: {dep.Name} Required: {dep.Required}")
```

Writing a TOC file:
```py
from pytoc import TOCFile

toc = TOCFile()
toc.Interface = 110000
toc.Author = "Ghost"
toc.Title = "My Addon"
toc.LocalizedTitle = {
    "frFR": "Mon Addon",
}
toc.Files = [
    TOCFileEntry("file1.lua"),
    TOCFileEntry("file2.xml"),
    TOCFileEntry("MainlineOnly.lua", [
        TOCAllowLoadGameType({TOCGameType.Mainline})
    ]),
    TOCFileEntry("PlunderstormGlueOnly.lua", [
        TOCAllowLoadGameType({TOCGameType.Plunderstorm}),
        TOCAllowLoadEnvironment({TOCEnvironment.Glue})
    ])
]

required = True
toc.add_dependency("totalRP3", required)

output = "path/to/dest.toc"
overwrite = True
toc.export(output, overwrite)
```

For some examples, take a look at the [test_toc.py](tests/test_toc.py) file.

## Notes/Quirks
> [!NOTE]
> - All dependency fields will be added to the `TOCFile.Dependencies` list. 
> - Non-standard directives (that don't start with `X-`) will be added directly to the `TOCFile` object, but will **not** be exported.
> - Fields will overwrite eachother if more than one of that directive is present in the TOC file, taking the last found value.
> - For certain fields that accept comma-delimited input, the attribute may end up being either a `list` or a `str|int`, depending on if there are multiple values or just a single one.
> - Comments and empty lines will be ignored in the current parser and will not be preserved when exporting.
