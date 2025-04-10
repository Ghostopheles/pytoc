![Tests](https://github.com/Ghostopheles/pytoc/actions/workflows/tests.yml/badge.svg)

# pytoc

A Python package for parsing World of Warcraft addon TOC files.

## Installation

You can install this package via `pip`.

```py
pip install wow-pytoc
```

## Usage

Reading a TOC file:
```py
from pytoc import TOCFile, Dependency

file_path: str = "X:/path/to/my/addon.toc"
toc = TOCFile(file_path)

print(toc.Interface)
print(toc.Title)
print(toc.LocalizedTitle["frFR"])
print(toc.AdditionalFields["X-Website"])

for file in toc.Files:
    print(file)

for dep in toc.Dependencies
    dep: Dependency
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
toc.Files = ["file1.lua", "file2.xml"]

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
