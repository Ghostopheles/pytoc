from typing import Any, Optional, Union, get_origin, get_args


class TypedProperty:
	def __init__(self, name, types, default):
		self._qualified_name = name
		self._internal_name = self._convert_to_internal_name(name)
		self._type = types
		self._default = default

	def __get__(self, instance, owner):
		try:
			return getattr(instance, self._internal_name)
		except AttributeError:
			return self._default

	def __set__(self, instance, value):
		if not self._is_valid_type(value):
			value = self._cast_to_valid_type(value)
		setattr(instance, self._internal_name, value)

	def _is_valid_type(self, value: Any) -> bool:
		if value is None:
			return self._is_optional()

		origin = get_origin(self._type)
		if origin is Union:
			return any(self._is_instance(value, t) for t in get_args(self._type))

		return self._is_instance(value, self._type)

	def _cast(self, value, t):
		origin = get_origin(t)
		args = get_args(t)
		if origin is None:
			if isinstance(value, t):
				return value

			return t(value)
		if origin is Union:
			for t in get_args(t):
				try:
					return self._cast(value, t)
				except (ValueError, TypeError):
					continue
			raise TypeError(f"Cannot cast {value} to any of {args}")
		if origin is Optional:
			if value is None:
				return None
			return self._cast(value, args[0])
		if origin is list:
			return [self._cast(v, args[0]) for v in value]
		return t(value)

	def _cast_to_valid_type(self, value: Any):
		if value is None:
			return None

		origin = get_origin(self._type)
		if origin is Union:
			for t in get_args(self._type):
				try:
					return self._cast(value, t)
				except (ValueError, TypeError):
					continue
			raise TypeError(f"Cannot cast {value} to any of {get_args(self._type)}")
		return self._cast(value, self._type)

	def _is_optional(self):
		origin = get_origin(self._type)
		if origin is Union:
			return type(None) in get_args(self._type)
		return False

	def _is_instance(self, value, t):
		origin = get_origin(self._type)
		args = get_args(t)
		if origin is None:
			return isinstance(value, t)
		if origin is Union:
			return any(self._is_instance(value, ty) for ty in args)
		if origin is Optional:
			return value is None or self._is_instance(value, args[0])
		if origin is list:
			return isinstance(value, list) and all(isinstance(v, args[0]) for v in value)
		return False

	def _convert_to_internal_name(self, qualified_name: str) -> str:
		return f"_{qualified_name.lower()}"


class TypedMeta(type):
	def __new__(cls, name, bases, dct):
		for attr_name, attr_type in dct.get("__annotations__", {}).items():
			default = dct.get(attr_name)
			dct[attr_name] = TypedProperty(attr_name, attr_type, default)
		return super().__new__(cls, name, bases, dct)


class TypedClass(metaclass=TypedMeta):
	pass
