# from https://github.com/PatrickKalkman/python-di/blob/master/custom_di/container.py
import inspect
from typing import Type, TypeVar


class NotRegisteredError(Exception):
    pass


T = TypeVar("T")


class Container:
    def __init__(self):
        self._registry = {}

    def register(self, dependency_type, implementation=None):
        if not implementation:
            implementation = dependency_type

        if inspect.isclass(implementation):
            for base in inspect.getmro(implementation):
                if base not in (object, dependency_type):
                    self._registry[base] = implementation

        self._registry[dependency_type] = implementation

    def is_registered(self, dependency_type):
        return dependency_type in self._registry

    def resolve(self, dependency_type: Type[T]) -> T:
        if dependency_type not in self._registry:
            raise NotRegisteredError(f"Dependency {dependency_type} not registered")
        implementation = self._registry[dependency_type]
        if inspect.isclass(implementation):
            constructor_signature = inspect.signature(implementation.__init__)
        elif inspect.ismethod(implementation) or inspect.isfunction(implementation):
            constructor_signature = inspect.signature(implementation)
        else:
            raise Exception(f"Cannot resolve {dependency_type}")
        constructor_params = constructor_signature.parameters.values()

        dependencies = [
            self.resolve(param.annotation)
            for param in constructor_params
            if param.annotation is not inspect.Parameter.empty
        ]

        return implementation(*dependencies)  # type: ignore


class Injector:
    def __init__(self, container: Container):
        self._container = container

    def inject(self, fn, **kwargs):
        signature = inspect.signature(fn)
        params = signature.parameters.values()

        call_params = []
        for param in params:
            if param.name in kwargs:
                call_params.append(kwargs[param.name])
                continue
            elif param.default is not inspect.Parameter.empty:
                continue
            if param.annotation is inspect.Parameter.empty:
                raise Exception(f"Missing value for {param.name}")
            if not self._container.is_registered(param.annotation):
                raise Exception(f"Missing registration for {param.annotation}")
            call_params.append(self._container.resolve(param.annotation))

        return fn(*call_params)
