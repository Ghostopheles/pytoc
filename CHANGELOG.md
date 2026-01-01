# 0.7.0
> [!WARNING]
> ⚠️ This release contains a minimum Python version bump to 3.12 ⚠️

### Added
- Added support for the new (not new) TOC variables and conditionals
- Added support for client-specific TOC files based on the file name
    - You can find this value, if specified, in the `TOCFile.ClientType` attribute. This attribute does not get exported

### Changed
- Migrated project management to `uv`
- Bumped minimum required Python version to 3.12

# 0.6.0
> [!WARNING]
> This release contains breaking changes, marked with ⚠️.

### Added
- Added a few new default directives
    - `SavedVariablesMachine`
    - `LoadFirst`
    - `LoadSavedVariablesFirst`
    - `AllowLoad`
    - `AllowLoadGameType`
    - `UseSecureEnvironment`
    - `Category`
    - `Group`
- Added a localized attribute for the Category directive, `LocalizedCategory`

### Changed
- ⚠️ Adjusted the string -> boolean conversion logic to be consistent with the way the WoW client parses these values
    - When exporting to a TOC file, the boolean values are now always converted to 1 or 0, regardless of the original input value
- ⚠️ Adjusted localized directive naming
    - `LocalizedTitles` -> `LocalizedTitle`
- Updated tests to be a bit more robust

### Fixed
- Fixed an issue that could be caused by TOC lines starting with `##` that were not actually directives (i.e. comments)
- Fixed an issue where SavedVariables entries with only one value would end up mangled
- Fixed an issue with localized directives overwriting each other

## Known Issues
- Attempting to parse a TOC file containing localized directives that are not `Title` or `Category` will result in an error being thrown. The current system for handling localization is a disaster and needs to be rewritten to fix this.
