import os
import pytest

from pytoc import TOCFile, Dependency

PWD = os.path.dirname(os.path.realpath(__file__))


def test_parser():
	file = TOCFile(f"{PWD}/testfile.toc")
	assert file.Interface == [110000, 110105, 11507, 30404, 40402, 50500]
	assert file.Title == "GhostTools"
	assert file.LocalizedTitle["frFR"] == "GrasTools"
	assert file.LocalizedTitle["deDE"] == "DieGeistTools"
	assert file.Notes == "A collection of cadaverous tools for the discerning necromancer."
	assert file.Bad == "bad:data : ## # ###"
	assert file.SavedVariables == [
		"GhostConfig",
		"GhostData",
		"GhostScanData",
		"GhostSavedProfile",
	]
	assert file.SavedVariablesPerCharacter == ["GhostEventLog"]
	assert file.SavedVariablesMachine == ["GhostWumbo"]
	assert file.IconTexture == "Interface/AddOns/totalRP3/Resources/policegar"
	assert file.IconAtlas == "ui-debug-tool-icon-large"
	assert file.AddonCompartmentFunc == "GHOST_OnAddonCompartmentClick"
	assert file.AddonCompartmentFuncOnEnter == "GHOST_OnAddonCompartmentEnter"
	assert file.AddonCompartmentFuncOnLeave == "GHOST_OnAddonCompartmentLeave"
	assert file.AdditionalFields["X-Website"] == "https://ghst.tools"
	assert file.get_raw_files() == [
		"Libs/LibStub/LibStub.lua",
		"Libs/CallbackHandler-1.0/CallbackHandler-1.0.xml",
		"Libs/LibDataBroker-1.1/LibDataBroker-1.1.lua",
		"Libs/LibDBIcon-1.0/LibDBIcon-1.0/lib.xml",
		"Libs/FAIAP.lua",
		"GhostTools.lua",
		"GhostAddonCompartment.lua",
		"Experiments/Experiments.lua",
		"Experiments/EventLog.lua",
		"Core/ConsoleScripts.lua",
		"Core/EventListener.lua",
		"Core/ErrorHandler.lua",
		"Core/Global.lua",
		"Core/SlashCommands.lua",
		"Core/Macros.lua",
		"Core/Coroutines.lua",
		"Core/Mixins.lua",
		"[Family]/FamilyFile.lua",
		"[Game]/UIKerning.lua",
		"ClassicOnly.lua [AllowLoadGameType classic]",
	]
	assert file.DefaultState == None
	assert file.OnlyBetaAndPTR == None
	assert file.LoadWith == None
	assert file.LoadManagers == None
	assert file.LoadFirst == None
	with pytest.raises(FileNotFoundError):
		TOCFile("bad/file/path")

	# dep name: required?
	expected_deps = {
		"totalRP3": False,
		"KethoDoc": False,
		"LibAdvFlight-1.0": False,
		"LibSmokeSignal-1.0": False,
		"BugGrabber": False,
		"Warmup": False,
		"Blackjack": True,
		"Graveyard": True,
		"FIFA2025": True,
	}

	for dep in file.Dependencies:
		dep: Dependency
		if expected_deps[dep.Name] == dep.Required:
			expected_deps.pop(dep.Name)

	assert len(expected_deps) == 0

	assert file.UseSecureEnvironment == True

	assert file.Group == "GhostTools"

	assert file.Category == "Roleplay"
	assert file.LocalizedCategory["enUS"] == "Roleplay"
	assert file.LocalizedCategory["deDE"] == "Rollenspiel"
	assert file.LocalizedCategory["esES"] == "Juego de rol"
	assert file.LocalizedCategory["esMX"] == "Juego de rol"
	assert file.LocalizedCategory["frFR"] == "Jeu de rôle"
	assert file.LocalizedCategory["itIT"] == "Gioco di Ruolo"
	assert file.LocalizedCategory["koKR"] == "롤플레잉"
	assert file.LocalizedCategory["ptBR"] == "Interpretação de Papel"
	assert file.LocalizedCategory["ruRU"] == "Ролевая игра"
	assert file.LocalizedCategory["zhCN"] == "角色扮演"
	assert file.LocalizedCategory["zhTW"] == "角色扮演"


EXPORT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_output.toc")


def test_export():
	toc = TOCFile()
	toc.Interface = "110000"
	toc.Author = "Ghost"
	toc.Title = "GhostTools"
	toc.LocalizedTitle = {"frFR": "GrasTools", "deDE": "DieGeistTools"}
	toc.Category = "Roleplay"
	toc.LocalizedCategory = {
		"frFR": "Jeu de rôle",
		"deDE": "Rollenspiel",
		"esES": "Juego de rol",
		"esMX": "Juego de rol",
		"itIT": "Gioco di Ruolo",
		"koKR": "롤플레잉",
		"ptBR": "Interpretação de Papel",
		"ruRU": "Ролевая игра",
		"zhCN": "角色扮演",
		"zhTW": "角色扮演",
	}
	toc.OnlyBetaAndPTR = True
	toc.DefaultState = True
	toc.Files = ["file1.lua", "file2.xml"]

	overwrite = True
	toc.export(EXPORT_PATH, overwrite)
	assert os.path.exists(EXPORT_PATH)


def test_read_export():
	toc = TOCFile(EXPORT_PATH)
	assert toc.Interface == 110000
	assert toc.Author == "Ghost"
	assert toc.Title == "GhostTools"
	assert toc.LocalizedTitle["frFR"] == "GrasTools"
	assert toc.LocalizedTitle["deDE"] == "DieGeistTools"
	assert toc.Category == "Roleplay"
	assert toc.LocalizedCategory["deDE"] == "Rollenspiel"
	assert toc.LocalizedCategory["esES"] == "Juego de rol"
	assert toc.LocalizedCategory["esMX"] == "Juego de rol"
	assert toc.LocalizedCategory["frFR"] == "Jeu de rôle"
	assert toc.LocalizedCategory["itIT"] == "Gioco di Ruolo"
	assert toc.LocalizedCategory["koKR"] == "롤플레잉"
	assert toc.LocalizedCategory["ptBR"] == "Interpretação de Papel"
	assert toc.LocalizedCategory["ruRU"] == "Ролевая игра"
	assert toc.LocalizedCategory["zhCN"] == "角色扮演"
	assert toc.LocalizedCategory["zhTW"] == "角色扮演"
	assert toc.OnlyBetaAndPTR == True
	assert toc.DefaultState == True
	assert toc.get_raw_files() == ["file1.lua", "file2.xml"]
