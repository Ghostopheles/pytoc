"""Tests targeting coverage gaps and known blind spots."""

import pytest
import warnings

from pathlib import Path
from pytoc import (
    TOCFile,
    TOCEvaluationContext,
    TOCGameType,
    TOCEnvironment,
    TOCTextLocale,
    TOCFamily,
    TOCAddonLoadError,
    TOCFileEntry,
    TOCLocalizedDirectiveValue,
    TOCBoolType,
    TOCListValue,
    TOCAllowLoadGameType,
    TOCAllowLoadTextLocale,
    TOCAllowLoad,
)
from pytoc.load_conditions import (
    TOCExcludeLoad,
    TOCExcludeLoadEnvironment,
    TOCExcludeLoadGameType,
    TOCExcludeLoadTextLocale,
    TOCAllowLoadEnvironment,
)
from pytoc.utils import StringToBoolean
from pytoc.parser import TOCAST, parse_directive_line, parse_typed_value
from pytoc.directives import TOCBoolType, TOCIntValue, TOCLocalizedDirectiveValue, TOCUnkValue


# ---------------------------------------------------------------------------
# Task 2: Exclude* load conditions
# ---------------------------------------------------------------------------


class TestExcludeLoad:
    def test_excludeload_blocks_matching_env(self):
        ctx = TOCEvaluationContext(TOCGameType.Mainline, TOCEnvironment.Global, TOCTextLocale.enUS)
        cond = TOCExcludeLoad(frozenset({TOCEnvironment.Global}))
        assert not cond.evaluate(ctx)

    def test_excludeload_allows_nonmatching_env(self):
        ctx = TOCEvaluationContext(TOCGameType.Mainline, TOCEnvironment.Glue, TOCTextLocale.enUS)
        cond = TOCExcludeLoad(frozenset({TOCEnvironment.Global}))
        assert cond.evaluate(ctx)

    def test_excludeload_blocks_when_both_in_values(self):
        ctx = TOCEvaluationContext(TOCGameType.Mainline, TOCEnvironment.Global, TOCTextLocale.enUS)
        cond = TOCExcludeLoad(frozenset({TOCEnvironment.Both}))
        assert not cond.evaluate(ctx)

    def test_excludeloadenvironment_blocks_matching_env(self):
        ctx = TOCEvaluationContext(TOCGameType.Mainline, TOCEnvironment.Glue, TOCTextLocale.enUS)
        cond = TOCExcludeLoadEnvironment(frozenset({TOCEnvironment.Glue}))
        assert not cond.evaluate(ctx)

    def test_excludeloadenvironment_allows_nonmatching_env(self):
        ctx = TOCEvaluationContext(TOCGameType.Mainline, TOCEnvironment.Global, TOCTextLocale.enUS)
        cond = TOCExcludeLoadEnvironment(frozenset({TOCEnvironment.Glue}))
        assert cond.evaluate(ctx)

    def test_excludeloadgametype_blocks_matching(self):
        ctx = TOCEvaluationContext(TOCGameType.Mainline, TOCEnvironment.Global, TOCTextLocale.enUS)
        cond = TOCExcludeLoadGameType(frozenset({TOCGameType.Mainline}))
        assert not cond.evaluate(ctx)

    def test_excludeloadgametype_allows_nonmatching(self):
        ctx = TOCEvaluationContext(TOCGameType.Classic, TOCEnvironment.Global, TOCTextLocale.enUS)
        cond = TOCExcludeLoadGameType(frozenset({TOCGameType.Mainline}))
        assert cond.evaluate(ctx)

    def test_excludeloadtextlocale_blocks_matching(self):
        ctx = TOCEvaluationContext(TOCGameType.Mainline, TOCEnvironment.Global, TOCTextLocale.deDE)
        cond = TOCExcludeLoadTextLocale(frozenset({TOCTextLocale.deDE}))
        assert not cond.evaluate(ctx)

    def test_excludeloadtextlocale_allows_nonmatching(self):
        ctx = TOCEvaluationContext(TOCGameType.Mainline, TOCEnvironment.Global, TOCTextLocale.enUS)
        cond = TOCExcludeLoadTextLocale(frozenset({TOCTextLocale.deDE}))
        assert cond.evaluate(ctx)


# ---------------------------------------------------------------------------
# Task 3: can_load_addon WrongEnvironment and WrongTextLocale
# ---------------------------------------------------------------------------


class TestCanLoadAddonErrorPaths:
    def test_wrong_environment(self):
        ctx = TOCEvaluationContext(TOCGameType.Mainline, TOCEnvironment.Glue, TOCTextLocale.enUS)
        toc = TOCFile()
        toc.AllowLoad = TOCAllowLoad(frozenset({TOCEnvironment.Global}))
        can_load, err = toc.can_load_addon(ctx)
        assert not can_load
        assert err == TOCAddonLoadError.WrongEnvironment

    def test_wrong_text_locale(self):
        ctx = TOCEvaluationContext(TOCGameType.Mainline, TOCEnvironment.Global, TOCTextLocale.frFR)
        toc = TOCFile()
        toc.AllowLoadTextLocale = TOCAllowLoadTextLocale(frozenset({TOCTextLocale.enUS}))
        can_load, err = toc.can_load_addon(ctx)
        assert not can_load
        assert err == TOCAddonLoadError.WrongTextLocale

    def test_success_with_all_conditions_met(self):
        ctx = TOCEvaluationContext(TOCGameType.Mainline, TOCEnvironment.Global, TOCTextLocale.enUS)
        toc = TOCFile()
        toc.AllowLoad = TOCAllowLoad(frozenset({TOCEnvironment.Global}))
        toc.AllowLoadGameType = TOCAllowLoadGameType(frozenset({TOCGameType.Mainline}))
        toc.AllowLoadTextLocale = TOCAllowLoadTextLocale(frozenset({TOCTextLocale.enUS}))
        can_load, err = toc.can_load_addon(ctx)
        assert can_load
        assert err == TOCAddonLoadError.Success


# ---------------------------------------------------------------------------
# Task 4: add_dependency optional path
# ---------------------------------------------------------------------------


class TestAddDependency:
    def test_add_optional_dependency(self):
        toc = TOCFile()
        toc.add_dependency("LibFoo", required=False)
        assert "LibFoo" in toc.OptionalDeps

    def test_add_optional_dependency_multiple(self):
        toc = TOCFile()
        toc.add_dependency("LibFoo", required=False)
        toc.add_dependency("LibBar", required=False)
        assert "LibFoo" in toc.OptionalDeps
        assert "LibBar" in toc.OptionalDeps

    def test_add_required_dependency(self):
        toc = TOCFile()
        toc.add_dependency("LibFoo", required=True)
        assert "LibFoo" in toc.Dependencies

    def test_optional_dep_not_in_required(self):
        toc = TOCFile()
        toc.add_dependency("LibFoo", required=False)
        assert toc.Dependencies is None or "LibFoo" not in toc.Dependencies

    def test_required_dep_not_in_optional(self):
        toc = TOCFile()
        toc.add_dependency("LibFoo", required=True)
        assert toc.OptionalDeps is None or "LibFoo" not in toc.OptionalDeps


# ---------------------------------------------------------------------------
# Task 5: remove_file and update_file_path
# ---------------------------------------------------------------------------


class TestFileMutations:
    def test_remove_file(self):
        toc = TOCFile()
        toc.add_file("file1.lua")
        toc.add_file("file2.lua")
        toc.add_file("file3.lua")
        toc.remove_file(1)
        names = toc.get_raw_files()
        assert names == ["file1.lua", "file3.lua"]

    def test_remove_file_first(self):
        toc = TOCFile()
        toc.add_file("file1.lua")
        toc.add_file("file2.lua")
        toc.remove_file(0)
        assert toc.get_raw_files() == ["file2.lua"]

    def test_remove_file_last(self):
        toc = TOCFile()
        toc.add_file("file1.lua")
        toc.add_file("file2.lua")
        toc.remove_file(1)
        assert toc.get_raw_files() == ["file1.lua"]

    def test_update_file_path(self):
        toc = TOCFile()
        toc.add_file("file1.lua")
        toc.add_file("file2.lua")
        toc.update_file_path(0, "renamed.lua")
        names = toc.get_raw_files()
        assert names == ["renamed.lua", "file2.lua"]

    def test_update_file_path_preserves_others(self):
        toc = TOCFile()
        toc.add_file("a.lua")
        toc.add_file("b.lua")
        toc.add_file("c.lua")
        toc.update_file_path(1, "b_new.lua")
        assert toc.get_raw_files() == ["a.lua", "b_new.lua", "c.lua"]


# ---------------------------------------------------------------------------
# Task 6: export FileExistsError and line-length warning
# ---------------------------------------------------------------------------


class TestExportEdgeCases:
    def test_export_raises_when_exists_no_overwrite(self, tmp_path):
        toc = TOCFile()
        toc.add_file("file.lua")
        out = tmp_path / "out.toc"
        toc.export(out, overwrite=True)
        with pytest.raises(FileExistsError):
            toc.export(out, overwrite=False)

    def test_export_line_length_warning(self, tmp_path):
        toc = TOCFile()
        long_title = "A" * 1100
        toc.Title = TOCLocalizedDirectiveValue(long_title)
        out = tmp_path / "warn.toc"
        with pytest.warns(UserWarning, match="characters"):
            toc.export(out, overwrite=True)

    def test_export_no_warning_for_normal_lines(self, tmp_path):
        toc = TOCFile()
        toc.Title = TOCLocalizedDirectiveValue("Normal Title")
        out = tmp_path / "ok.toc"
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            toc.export(out, overwrite=True)


# ---------------------------------------------------------------------------
# Task 7: localized directive mutation
# ---------------------------------------------------------------------------


class TestLocalizedDirectiveMutation:
    def test_set_directive_none_removes_it(self):
        toc = TOCFile()
        toc.Title = TOCLocalizedDirectiveValue("Hello")
        assert toc.Title == "Hello"
        toc.Title = None
        assert toc.Title is None

    def test_set_directive_adds_new_locale(self):
        toc = TOCFile()
        toc.Title = TOCLocalizedDirectiveValue("English")
        toc.Title = TOCLocalizedDirectiveValue("English", {TOCTextLocale.enUS: "English", TOCTextLocale.deDE: "Englisch"})
        assert toc.Title.get_translation(TOCTextLocale.deDE) == "Englisch"

    def test_set_directive_removes_obsolete_locale(self):
        toc = TOCFile()
        toc.Title = TOCLocalizedDirectiveValue("English", {TOCTextLocale.enUS: "English", TOCTextLocale.deDE: "Englisch"})
        toc.Title = TOCLocalizedDirectiveValue("English")
        assert toc.Title.get_translation(TOCTextLocale.deDE) is None

    def test_set_list_directive_replaces(self):
        toc = TOCFile()
        toc.SavedVariables = TOCListValue[str]("Foo, Bar", ["Foo", "Bar"])
        toc.SavedVariables = TOCListValue[str]("Baz", ["Baz"])
        assert list(toc.SavedVariables) == ["Baz"]

    def test_set_list_directive_from_string(self):
        toc = TOCFile()
        toc.SavedVariables = "Foo, Bar, Baz"
        assert "Foo" in toc.SavedVariables
        assert "Bar" in toc.SavedVariables
        assert "Baz" in toc.SavedVariables

    def test_set_list_directive_from_list(self):
        toc = TOCFile()
        toc.SavedVariables = ["Alpha", "Beta"]
        assert list(toc.SavedVariables) == ["Alpha", "Beta"]

    def test_set_directive_none_on_absent_noop(self):
        toc = TOCFile()
        toc.Title = None
        assert toc.Title is None


# ---------------------------------------------------------------------------
# Task 8: Parser edge cases
# ---------------------------------------------------------------------------


class TestParserEdgeCases:
    def test_extended_directive_with_locale(self):
        line = "## X-Website-deDE: https://example.de\n"
        node = parse_directive_line(0, line)
        assert node.IsExtendedDirective
        assert node.Locale == TOCTextLocale.deDE

    def test_parse_typed_value_int_value_error(self):
        from pytoc.directives import TOCDirectiveSpec, TOCIntValue as IntVal

        spec = TOCDirectiveSpec(Name="Interface", ValueType=IntVal)
        with pytest.raises(ValueError):
            parse_typed_value("not_an_int", spec)

    def test_line_too_long_warning_on_parse(self):
        long_line = "## Title: " + "A" * 1100 + "\n"
        with pytest.warns(UserWarning):
            TOCAST.from_lines([long_line])

    def test_unrecognized_directive_becomes_unk(self):
        line = "## WeirdDirective: some value\n"
        node = parse_directive_line(0, line)
        from pytoc.directives import TOCUnkValue

        assert isinstance(node.Value, TOCUnkValue)

    def test_alias_directive_resolves_to_canonical(self):
        line = "## RequiredDeps: LibFoo\n"
        node = parse_directive_line(0, line)
        assert node.CanonicalName == "Dependencies"

    def test_empty_file_produces_empty_ast(self):
        ast = TOCAST.from_lines([])
        assert ast.Lines == []

    def test_comment_line_parsed(self):
        from pytoc.parser import parse_comment

        node = parse_comment(0, "# This is a comment\n")
        assert node.Value == "This is a comment"

    def test_parse_typed_value_list_from_tuple(self):
        from pytoc.directives import TOCDirectiveSpec

        spec = TOCDirectiveSpec(Name="SavedVariables", ValueType=TOCListValue[str])
        result = parse_typed_value(("Foo", "Bar"), spec)
        assert isinstance(result, TOCListValue)
        assert list(result) == ["Foo", "Bar"]


# ---------------------------------------------------------------------------
# Task 9: StringToBoolean edge cases
# ---------------------------------------------------------------------------


class TestStringToBoolean:
    def test_empty_string_returns_default_false(self):
        assert StringToBoolean("") is False

    def test_empty_string_returns_custom_default(self):
        assert StringToBoolean("", defaultReturn=True) is True

    def test_unknown_string_returns_default(self):
        assert StringToBoolean("blah") is False

    def test_on(self):
        assert StringToBoolean("on") is True

    def test_off(self):
        assert StringToBoolean("off") is False

    def test_enabled(self):
        assert StringToBoolean("enabled") is True

    def test_disabled(self):
        assert StringToBoolean("disabled") is False

    def test_truthy_digits(self):
        for digit in "23456789":
            assert StringToBoolean(digit) is True

    def test_falsey_chars(self):
        assert StringToBoolean("n") is False
        assert StringToBoolean("f") is False
        assert StringToBoolean("0") is False

    def test_case_insensitive(self):
        assert StringToBoolean("ON") is True
        assert StringToBoolean("OFF") is False
        assert StringToBoolean("Y") is True


# ---------------------------------------------------------------------------
# Task 10: has_translation and TOCBoolType.Raw setter
# ---------------------------------------------------------------------------


class TestDirectiveTypeMethods:
    def test_has_translation_true(self):
        v = TOCLocalizedDirectiveValue("Hello", {TOCTextLocale.enUS: "Hello", TOCTextLocale.deDE: "Hallo"})
        assert v.has_translation(TOCTextLocale.deDE)

    def test_has_translation_false(self):
        v = TOCLocalizedDirectiveValue("Hello")
        assert not v.has_translation(TOCTextLocale.frFR)

    def test_booltype_raw_setter_updates_value(self):
        b = TOCBoolType("1", True)
        b.Raw = "0"
        assert b.Value is False
        assert b.Raw == "0"

    def test_booltype_raw_setter_truthy(self):
        b = TOCBoolType("0", False)
        b.Raw = "1"
        assert b.Value is True

    def test_booltype_eq_bool(self):
        b = TOCBoolType("1", True)
        assert b == True
        assert b != False

    def test_booltype_eq_booltype(self):
        assert TOCBoolType("1", True) == TOCBoolType("1", True)
        assert TOCBoolType("1", True) != TOCBoolType("0", False)

    def test_booltype_hash(self):
        s = {TOCBoolType("1", True), TOCBoolType("0", False)}
        assert len(s) == 2

    def test_localized_eq_string(self):
        v = TOCLocalizedDirectiveValue("Hello")
        assert v == "Hello"
        assert v != "World"

    def test_localized_eq_localized(self):
        a = TOCLocalizedDirectiveValue("Hello")
        b = TOCLocalizedDirectiveValue("Hello")
        assert a == b

    def test_unkvalue_eq_string(self):
        u = TOCUnkValue("raw", "cleaned")
        assert u == "cleaned"


# ---------------------------------------------------------------------------
# Task 11: resolve_path KeyError and Family KeyError
# ---------------------------------------------------------------------------


class TestErrorPaths:
    def test_resolve_path_unknown_variable(self):
        ctx = TOCEvaluationContext(TOCGameType.Mainline, TOCEnvironment.Global, TOCTextLocale.enUS)
        entry = TOCFileEntry("[Unknown]/file.lua")
        with pytest.raises(KeyError, match="Unknown"):
            entry.resolve_path(ctx)

    def test_family_unknown_gametype(self):
        # Create a context then monkey-patch GameType to something not in the mapping
        ctx = TOCEvaluationContext(TOCGameType.Mainline, TOCEnvironment.Global, TOCTextLocale.enUS)
        ctx.GameType = "completely_fake_game_type"
        with pytest.raises(KeyError):
            _ = ctx.Family


# ---------------------------------------------------------------------------
# Task 12: TOCFile misc — repr, Comments, add_empty_line
# ---------------------------------------------------------------------------


class TestTOCFileMisc:
    def test_repr(self):
        toc = TOCFile()
        r = repr(toc)
        assert r.startswith("TOCFile(lines=")

    def test_comments_empty(self):
        toc = TOCFile()
        assert toc.Comments == []

    def test_comments_from_parsed_file(self):
        lines = ["# This is a comment\n", "## Title: MyAddon\n"]
        from pytoc.parser import TOCAST

        toc = TOCFile()
        toc._AST = TOCAST.from_lines(lines)
        assert len(toc.Comments) == 1
        assert toc.Comments[0].Value == "This is a comment"

    def test_add_empty_line(self):
        toc = TOCFile()
        toc.add_file("file.lua")
        before = len(toc._AST.Lines)
        toc.add_empty_line()
        assert len(toc._AST.Lines) == before + 1

    def test_add_empty_line_roundtrip(self, tmp_path):
        toc = TOCFile()
        toc.Title = TOCLocalizedDirectiveValue("Test")
        toc.add_empty_line()
        toc.add_file("file.lua")
        out = tmp_path / "test.toc"
        toc.export(out, overwrite=True)
        toc2 = TOCFile(out)
        assert toc2.Title == "Test"
        assert toc2.get_raw_files() == ["file.lua"]


# ---------------------------------------------------------------------------
# Tasks 13-16: High-risk mutation paths
# ---------------------------------------------------------------------------


class TestCoerceScalar:
    """toc.py:196-198, 200, 202-203 — _coerce_scalar"""

    def test_bool_directive_set_from_python_true(self):
        toc = TOCFile()
        toc.LoadOnDemand = True
        assert toc.LoadOnDemand == True
        assert bool(toc.LoadOnDemand) is True

    def test_bool_directive_set_from_python_false(self):
        toc = TOCFile()
        toc.LoadOnDemand = False
        assert toc.LoadOnDemand == False
        assert bool(toc.LoadOnDemand) is False

    def test_bool_directive_set_from_string_truthy(self):
        toc = TOCFile()
        toc.LoadOnDemand = "1"
        assert bool(toc.LoadOnDemand) is True

    def test_bool_directive_set_from_string_falsey(self):
        toc = TOCFile()
        toc.LoadOnDemand = "0"
        assert bool(toc.LoadOnDemand) is False

    def test_bool_directive_roundtrips_correctly(self, tmp_path):
        toc = TOCFile()
        toc.LoadOnDemand = True
        out = tmp_path / "bool.toc"
        toc.export(out, overwrite=True)
        toc2 = TOCFile(out)
        assert bool(toc2.LoadOnDemand) is True

    def test_condition_directive_set_from_frozenset(self):
        toc = TOCFile()
        toc.AllowLoadGameType = frozenset({TOCGameType.Mainline})
        ctx = TOCEvaluationContext(TOCGameType.Mainline, TOCEnvironment.Global, TOCTextLocale.enUS)
        can_load, _ = toc.can_load_addon(ctx)
        assert can_load

    def test_condition_directive_set_from_frozenset_blocks_wrong(self):
        toc = TOCFile()
        toc.AllowLoadGameType = frozenset({TOCGameType.Mainline})
        ctx = TOCEvaluationContext(TOCGameType.Classic, TOCEnvironment.Global, TOCTextLocale.enUS)
        can_load, err = toc.can_load_addon(ctx)
        assert not can_load
        assert err == TOCAddonLoadError.WrongGameType

    def test_condition_directive_set_from_set(self):
        toc = TOCFile()
        toc.AllowLoad = {TOCEnvironment.Global}
        ctx = TOCEvaluationContext(TOCGameType.Mainline, TOCEnvironment.Global, TOCTextLocale.enUS)
        can_load, _ = toc.can_load_addon(ctx)
        assert can_load

    def test_condition_directive_set_from_list(self):
        toc = TOCFile()
        toc.AllowLoadGameType = [TOCGameType.Mainline, TOCGameType.Classic]
        ctx_main = TOCEvaluationContext(TOCGameType.Mainline, TOCEnvironment.Global, TOCTextLocale.enUS)
        ctx_classic = TOCEvaluationContext(TOCGameType.Classic, TOCEnvironment.Global, TOCTextLocale.enUS)
        assert toc.can_load_addon(ctx_main)[0]
        assert toc.can_load_addon(ctx_classic)[0]


class TestListDirectiveConversion:
    """toc.py:259-262 — list item coercion in _set_directive"""

    def test_interface_from_list_of_strings(self):
        toc = TOCFile()
        toc.Interface = ["110000", "110105"]
        values = list(toc.Interface)
        assert values == [110000, 110105]
        assert all(isinstance(v, int) for v in values)

    def test_interface_from_single_string(self):
        toc = TOCFile()
        toc.Interface = "110000"
        assert list(toc.Interface) == [110000]

    def test_interface_from_list_of_strings_roundtrips(self, tmp_path):
        toc = TOCFile()
        toc.Interface = ["110000", "110105"]
        out = tmp_path / "iface.toc"
        toc.export(out, overwrite=True)
        toc2 = TOCFile(out)
        assert list(toc2.Interface) == [110000, 110105]

    def test_savedvariables_from_non_string_values(self):
        # lt=str, v=int → hits general lt(v) fallback (line 261-262)
        toc = TOCFile()
        toc.SavedVariables = [42, 99]
        values = list(toc.SavedVariables)
        assert values == ["42", "99"]
        assert all(isinstance(v, str) for v in values)


class TestFilesOnlyTOCInsertion:
    """toc.py:126-127, 131 — _directive_section_end_idx with no directives"""

    def test_directive_inserted_before_files_in_files_only_toc(self):
        from pytoc.parser import TOCAST, TOCFileEntryLine

        toc = TOCFile()
        toc.add_file("file1.lua")
        toc.add_file("file2.lua")
        # No directives yet — only file entries in AST
        toc.Title = TOCLocalizedDirectiveValue("MyAddon")
        lines = toc._AST.Lines
        # Find positions
        from pytoc.parser import TOCDirectiveLine

        directive_positions = [i for i, n in enumerate(lines) if isinstance(n, TOCDirectiveLine)]
        file_positions = [i for i, n in enumerate(lines) if isinstance(n, TOCFileEntryLine)]
        assert directive_positions, "No directive found"
        assert file_positions, "No files found"
        assert max(directive_positions) < min(file_positions), "Directive inserted after files"

    def test_directive_added_to_empty_toc(self):
        toc = TOCFile()
        toc.Title = TOCLocalizedDirectiveValue("Test")
        assert toc.Title == "Test"

    def test_second_directive_in_files_only_toc(self):
        toc = TOCFile()
        toc.add_file("a.lua")
        toc.Title = TOCLocalizedDirectiveValue("Title")
        toc.Notes = TOCLocalizedDirectiveValue("Notes text")
        from pytoc.parser import TOCDirectiveLine, TOCFileEntryLine

        lines = toc._AST.Lines
        directive_positions = [i for i, n in enumerate(lines) if isinstance(n, TOCDirectiveLine)]
        file_positions = [i for i, n in enumerate(lines) if isinstance(n, TOCFileEntryLine)]
        assert max(directive_positions) < min(file_positions)


class TestLocalizedDirectiveCoercion:
    """toc.py:216, 218 — _set_directive coercion for localized specs"""

    def test_set_localized_directive_from_plain_string(self):
        toc = TOCFile()
        toc.Title = "Hello World"
        assert toc.Title == "Hello World"

    def test_set_localized_directive_from_plain_string_roundtrips(self, tmp_path):
        toc = TOCFile()
        toc.Title = "Hello World"
        out = tmp_path / "str.toc"
        toc.export(out, overwrite=True)
        toc2 = TOCFile(out)
        assert toc2.Title == "Hello World"

    def test_set_localized_directive_from_non_string(self):
        toc = TOCFile()
        toc.Title = 12345
        assert toc.Title == "12345"

    def test_set_localized_directive_from_non_string_roundtrips(self, tmp_path):
        toc = TOCFile()
        toc.Title = 12345
        out = tmp_path / "nonstr.toc"
        toc.export(out, overwrite=True)
        toc2 = TOCFile(out)
        assert toc2.Title == "12345"

    def test_overwrite_localized_directive_with_plain_string(self):
        toc = TOCFile()
        toc.Title = TOCLocalizedDirectiveValue("Original")
        toc.Title = "Replaced"
        assert toc.Title == "Replaced"
