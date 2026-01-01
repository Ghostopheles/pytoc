from dataclasses import dataclass, field

from .enums import *


@dataclass
class TOCEvaluationContext:
	GameType: TOCGameType
	Environment: TOCEnvironment
	TextLocale: TOCTextLocale
	LoadedAddons: dict[str, bool] = field(default_factory=dict)

	@property
	def Family(self) -> TOCFamily:
		try:
			return TOC_GAME_TYPE_TO_FAMILY[self.GameType]
		except KeyError:
			raise KeyError(f"Unknown GameType specified: {self.GameType}")

	def load_addon(self, addon_name: str):
		self.LoadedAddons[addon_name] = True

	def unload_addon(self, addon_name: str):
		if addon_name in self.LoadedAddons:
			self.LoadedAddons.pop(addon_name)

	def is_addon_loaded(self, addon_name: str) -> bool:
		return self.LoadedAddons.get(addon_name, False)
