# characters/strings that are interpreted as falsey/truthy according to the WoW client
FALSEY_CHARS = ("0", "n", "f")
FALSEY_STRINGS = ("off", "disabled")
TRUTHY_CHARS = ("1", "2", "3", "4", "5", "6", "7", "8", "9", "y", "t")
TRUTHY_STRINGS = ("on", "enabled")


# this function is terrible, but it supports legacy slash commands
def StringToBoolean(string: str, defaultReturn: bool = False):
    if len(string) == 0:
        return defaultReturn

    string = string.lower()
    firstChar = string[0]

    if firstChar in FALSEY_CHARS or string in FALSEY_STRINGS:
        return False
    elif firstChar in TRUTHY_CHARS or string in TRUTHY_STRINGS:
        return True

    return defaultReturn
