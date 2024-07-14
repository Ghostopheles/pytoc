import os
import pytest

from pytoc import TOCFile

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
    with pytest.raises(Exception):
        assert file.LoadWith == None
