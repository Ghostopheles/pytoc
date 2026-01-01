from enum import StrEnum


class TOCGameType(StrEnum):
	Standard = "standard"
	Mainline = "mainline"
	Wowhack = "wowhack"
	Wowlabs = "wowlabs"
	Plunderstorm = "plunderstorm"
	Classic = "classic"
	Vanilla = "vanilla"
	TBC = "tbc"
	Wrath = "wrath"
	Mists = "mists"


class TOCEnvironment(StrEnum):
	Global = "global"
	Glue = "glue"
	Both = "both"


class TOCFamily(StrEnum):
	Mainline = "Mainline"
	Classic = "Classic"


class TOCTextLocale(StrEnum):
	enUS = "enUS"
	enGB = "enGB"
	enTW = "enTW"
	zhTW = "zhTW"
	esES = "esES"
	ruRU = "ruRU"
	koKR = "koKR"
	ptPT = "ptPT"
	esMX = "esMX"
	itIT = "itIT"
	deDE = "deDE"
	frFR = "frFR"
	enCN = "enCN"
	zhCN = "zhCN"
	ptBR = "ptBR"


TOC_GAME_TYPE_TO_FAMILY = {
	TOCGameType.Standard: TOCFamily.Mainline,
	TOCGameType.Mainline: TOCFamily.Mainline,
	TOCGameType.Wowhack: TOCFamily.Mainline,
	TOCGameType.Wowlabs: TOCFamily.Mainline,
	TOCGameType.Plunderstorm: TOCFamily.Mainline,
	TOCGameType.Classic: TOCFamily.Classic,
	TOCGameType.Vanilla: TOCFamily.Classic,
	TOCGameType.TBC: TOCFamily.Classic,
	TOCGameType.Wrath: TOCFamily.Classic,
	TOCGameType.Mists: TOCFamily.Classic,
}
