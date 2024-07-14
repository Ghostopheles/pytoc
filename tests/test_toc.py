import os
import pytest

from pytoc import TOCFile, Dependency

PWD = os.path.dirname(os.path.realpath(__file__))


def test_parser():
    file = TOCFile(f"{PWD}/testfile.toc")
    assert file.Interface == ["100207", "110000"]
    assert file.Title == "GhostTools"
    assert file.LocalizedTitles["frFR"] == "GhostToolsfrfr"
    assert (
        file.Notes == "A collection of cadaverous tools for the discerning necromancer."
    )
    assert file.Bad == "bad:data : ## # ###"
    assert file.SavedVariables == [
        "GhostConfig",
        "GhostData",
        "GhostScanData",
        "GhostSavedProfile",
    ]
    assert file.IconTexture == "Interface/AddOns/totalRP3/Resources/policegar"
    assert file.AddonCompartmentFunc == "GHOST_OnAddonCompartmentClick"
    assert file.AddonCompartmentFuncOnEnter == "GHOST_OnAddonCompartmentEnter"
    assert file.AddonCompartmentFuncOnLeave == "GHOST_OnAddonCompartmentLeave"
    assert file.AdditionalFields["X-Website"] == "https://ghst.tools"
    assert file.Files == [
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
    ]
    assert file.DefaultState == False
    assert file.OnlyBetaAndPTR == False
    assert file.LoadWith == None
    assert file.LoadManagers == None
    with pytest.raises(FileNotFoundError):
        TOCFile("watch out! there's a ghost!")

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


EXPORT_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "test_output.toc"
)


def test_export():
    toc = TOCFile()
    toc.Interface = "110000"
    toc.Author = "Ghost"
    toc.OnlyBetaAndPTR = True
    toc.DefaultState = True
    toc.Files = ["file1.lua", "file2.xml"]
    toc.export(EXPORT_PATH, True)
    assert os.path.exists(EXPORT_PATH)


def test_read_export():
    toc = TOCFile(EXPORT_PATH)
    assert toc.Interface == "110000"
    assert toc.Author == "Ghost"
    assert toc.OnlyBetaAndPTR == True
    assert toc.DefaultState == True
    assert toc.Files == ["file1.lua", "file2.xml"]
