![Tests](https://github.com/Ghostopheles/pytoc/actions/workflows/tests.yml/badge.svg)

# pytoc

A Python package for parsing World of Warcraft TOC files used in addons.

## Installation

You can install this package via `pip` by pointing it to this repository.

```py
pip install git+https://github.com/Ghostopheles/pytoc.git
```

## Usage

Usage is fairly minimal and straightforward to read a TOC file:
```py
from pytoc import TOCFile, Dependency

file_path: str = "X:/path/to/my/addon.toc"
toc = TOCFile(file_path)

print(toc.Interface)
print(toc.Title)
print(toc.LocalizedTitles["frFR"])
print(toc.AdditionalFields["X-Website"])

for file in toc.Files:
    print(file)

for dep in toc.Dependencies
    dep: Dependency
    print(f"Dependency Name: {dep.Name} Required: {dep.Required}")
```

Here's how you can write and export a TOC file:
```py
from pytoc import TOCFile, Dependency

toc = TOCFile()
toc.Interface = "110000"
toc.Author = "Ghost"
toc.Files = ["file1.lua", "file2.xml"]

required = True
toc.add_dependency("totalRP3", required)

output = "path/to/dest.toc"
toc.export(output)
```

For some examples, take a look at the [test_toc.py](tests/test_toc.py) file.

## Notes

All dependency fields will be added to the `TOCFile` object. Fields that are not available to addons, or extra fields that don't begin with "X-" will be added directly to the object.

Fields will overwrite eachother if more than one of that directive is present in the TOC file.

For certain fields that accept comma-delimited input, the attribute may end up being either a `list` or a `str|int`, depending on if there are multiple entries or just a single one.

Currently, entries are not cast to their intended types. i.e. `Interface` will be left as a string instead of converted to an integer.
