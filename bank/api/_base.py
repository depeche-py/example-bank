import explicit_di as _di
import fastapi as _fastapi

from .. import infra as _infra
from ..handlers import commands, queries

app = _fastapi.FastAPI()


def _container() -> _di.Container:
    return _infra.get_di_container()


container = _fastapi.Depends(_container)


def _command_handler(
    container_instance: _di.Container = container,
) -> commands.CommandHandlerWithDI:
    return container_instance.resolve(commands.CommandHandlerWithDI)


command_handler = _fastapi.Depends(_command_handler)


def _query_handler(
    container_instance: _di.Container = container,
) -> queries.QueryHandler:
    return container_instance.resolve(queries.QueryHandler)


query_handler = _fastapi.Depends(_query_handler)
