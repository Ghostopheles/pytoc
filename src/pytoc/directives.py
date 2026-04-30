from collections.abc import Callable
from typing import Optional, List, Type
from dataclasses import dataclass, field


from .enums import TOCTextLocale
from .utils import StringToBoolean
from .shared import PYTOC_DEFAULT_LOCALE
from .load_conditions import TOCAllowLoad, TOCAllowLoadGameType, TOCAllowLoadTextLocale


@dataclass
class TOCBoolType:
    _Raw: str
    Value: bool

    @property
    def Raw(self) -> str:
        return self._Raw

    @Raw.setter
    def Raw(self, s: str) -> None:
        self._Raw = s
        self.Value = StringToBoolean(s)

    def __bool__(self):
        return self.Value

    def __eq__(self, other):
        if isinstance(other, TOCBoolType):
            return self.Value == other.Value
        if isinstance(other, bool):
            return self.Value == other
        return NotImplemented

    def __hash__(self):
        return hash(self.Value)


@dataclass
class TOCIntValue:
    Raw: str
    Value: int


@dataclass
class TOCListValue[T]:
    Raw: str
    Value: List[T]

    Converter: Callable[[str], T] = field(repr=False, default=None)

    def __post_init__(self):
        if self.Converter is None:
            return

        new_values: List[T] = []
        for v in self.Value:
            if isinstance(v, str):
                new_values.append(self.Converter(v))
            else:
                new_values.append(v)

        self.Value = new_values

    def __iter__(self):
        return iter(self.Value)

    def __contains__(self, value):
        return value in self.Value

    def __len__(self):
        return len(self.Value)

    def __getitem__(self, idx):
        return self.Value[idx]

    def __eq__(self, other):
        if other is None:
            return False
        if isinstance(other, TOCListValue):
            return self.Value == other.Value
        if isinstance(other, list):
            return self.Value == other
        if len(self.Value) == 1:
            return self.Value[0] == other
        return NotImplemented

    def __hash__(self):
        return hash(tuple(self.Value))


@dataclass
class TOCEnumValue[T]:
    Raw: str
    Value: T


@dataclass
class TOCUnkValue:
    Raw: str
    Value: str

    def __str__(self):
        return self.Value

    def __eq__(self, other):
        if isinstance(other, str):
            return self.__str__() == other
        return super().__eq__(other)


@dataclass
class TOCLocalizedDirectiveValue:
    Raw: str
    Localizations: dict[TOCTextLocale, str] = field(default_factory=dict)

    def __cleanup_text(self, text: str) -> str:
        if text.startswith("## "):
            split = text.split(":", 1)
            clean_text = split[-1]
        else:
            clean_text = text

        return clean_text.strip().removesuffix("\n")

    def __post_init__(self):
        default_text = self.__cleanup_text(self.Raw)
        self.set_translation(PYTOC_DEFAULT_LOCALE, default_text)

    def __str__(self):
        return self.get_translation(PYTOC_DEFAULT_LOCALE)

    def __bytes__(self):
        return self.__str__().encode("utf-8")

    def __eq__(self, other):
        if isinstance(other, str):
            return self.__str__() == other
        elif isinstance(other, TOCLocalizedDirectiveValue):
            return self.__str__() == other.__str__()
        else:
            return super().__eq__(other)

    def get_translation(self, locale: TOCTextLocale) -> Optional[str]:
        return self.Localizations.get(locale)

    def set_translation(self, locale: TOCTextLocale, text: str):
        if not isinstance(locale, TOCTextLocale):
            if locale is not None:
                locale = TOCTextLocale[locale]
            else:
                locale = PYTOC_DEFAULT_LOCALE

        text = self.__cleanup_text(text)
        self.Localizations[locale] = text

    def has_translation(self, locale: TOCTextLocale) -> bool:
        return self.Localizations.get(locale, None) is not None


# schema


@dataclass(frozen=True)
class TOCDirectiveSpec:
    Name: str
    ValueType: Type  # i.e. TOCBoolType, etc
    Aliases: Optional[tuple[str, ...]] = None
    AliasFunc: Callable[[str], bool] = None  # func that takes in the directive name, and returns true if it is an alias
    CanBeLocalized: bool = False
    AllowDuplicates: bool = True


TOC_DIRECTIVES: dict[str, TOCDirectiveSpec] = {
    "Interface": TOCDirectiveSpec(Name="Interface", ValueType=TOCListValue[int]),
    "Title": TOCDirectiveSpec(Name="Title", ValueType=TOCLocalizedDirectiveValue, CanBeLocalized=True),
    "Author": TOCDirectiveSpec(Name="Author", ValueType=TOCLocalizedDirectiveValue, CanBeLocalized=True),
    "Version": TOCDirectiveSpec(Name="Version", ValueType=TOCLocalizedDirectiveValue, CanBeLocalized=True),
    "Notes": TOCDirectiveSpec(Name="Notes", ValueType=TOCLocalizedDirectiveValue, CanBeLocalized=True),
    "Group": TOCDirectiveSpec(Name="Group", ValueType=TOCLocalizedDirectiveValue, CanBeLocalized=True),
    "Category": TOCDirectiveSpec(Name="Category", ValueType=TOCLocalizedDirectiveValue, CanBeLocalized=True),
    "SavedVariables": TOCDirectiveSpec(
        Name="SavedVariables",
        ValueType=TOCListValue[str],
    ),
    "SavedVariablesPerCharacter": TOCDirectiveSpec(
        Name="SavedVariablesPerCharacter",
        ValueType=TOCListValue[str],
    ),
    "SavedVariablesMachine": TOCDirectiveSpec(
        Name="SavedVariablesMachine",
        ValueType=TOCListValue[str],
    ),
    "IconTexture": TOCDirectiveSpec(Name="IconTexture", ValueType=TOCLocalizedDirectiveValue, CanBeLocalized=True),
    "IconAtlas": TOCDirectiveSpec(Name="IconAtlas", ValueType=TOCLocalizedDirectiveValue, CanBeLocalized=True),
    "AddonCompartmentFunc": TOCDirectiveSpec(Name="AddonCompartmentFunc", ValueType=TOCLocalizedDirectiveValue, CanBeLocalized=True),
    "AddonCompartmentFuncOnEnter": TOCDirectiveSpec(Name="AddonCompartmentFuncOnEnter", ValueType=TOCLocalizedDirectiveValue, CanBeLocalized=True),
    "AddonCompartmentFuncOnLeave": TOCDirectiveSpec(Name="AddonCompartmentFuncOnLeave", ValueType=TOCLocalizedDirectiveValue, CanBeLocalized=True),
    "LoadOnDemand": TOCDirectiveSpec(
        Name="LoadOnDemand",
        ValueType=TOCBoolType,
    ),
    "LoadFirst": TOCDirectiveSpec(
        Name="LoadFirst",
        ValueType=TOCBoolType,
    ),
    "LoadWith": TOCDirectiveSpec(
        Name="LoadWith",
        ValueType=TOCListValue[str],
    ),
    "LoadManagers": TOCDirectiveSpec(
        Name="LoadManagers",
        ValueType=TOCListValue[str],
    ),
    "Dependencies": TOCDirectiveSpec(
        Name="Dependencies",
        ValueType=TOCListValue[str],
        Aliases=("RequiredDeps",),
        AliasFunc=lambda name: name.lower().startswith("dep"),
        AllowDuplicates=True,
    ),
    "OptionalDeps": TOCDirectiveSpec(
        Name="OptionalDeps",
        ValueType=TOCListValue[str],
    ),
    "DefaultState": TOCDirectiveSpec(
        Name="DefaultState",
        ValueType=TOCBoolType,
    ),
    "OnlyBetaAndPTR": TOCDirectiveSpec(
        Name="OnlyBetaAndPTR",
        ValueType=TOCBoolType,
    ),
    "LoadSavedVariablesFirst": TOCDirectiveSpec(
        Name="LoadSavedVariablesFirst",
        ValueType=TOCBoolType,
    ),
    "AllowLoad": TOCDirectiveSpec(Name="AllowLoad", ValueType=TOCAllowLoad),
    "AllowLoadGameType": TOCDirectiveSpec(Name="AllowLoadGameType", ValueType=TOCAllowLoadGameType),
    "AllowLoadTextLocale": TOCDirectiveSpec(Name="AllowLoadTextLocale", ValueType=TOCAllowLoadTextLocale),
    "UseSecureEnvironment": TOCDirectiveSpec(Name="UseSecureEnvironment", ValueType=TOCBoolType),
}
ALIAS_TO_CANONICAL: dict[str, str] = dict()
ALIAS_FUNCTIONS: dict[str, Callable[[str], bool]] = dict()

for spec in TOC_DIRECTIVES.values():
    ALIAS_TO_CANONICAL[spec.Name] = spec.Name
    ALIAS_TO_CANONICAL[spec.Name.lower()] = spec.Name
    if spec.Aliases:
        for name in spec.Aliases:
            ALIAS_TO_CANONICAL[name] = spec.Name
            ALIAS_TO_CANONICAL[name.lower()] = spec.Name
    if spec.AliasFunc is not None:
        ALIAS_FUNCTIONS[spec.Name] = spec.AliasFunc
