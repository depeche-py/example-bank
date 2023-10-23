from . import config as _config
from depeche_db import Executor
from . import infra as _infra


def main():
    config = _config.get()
    executor = Executor(db_dsn=config.db_dsn.get_secret_value())
    for runnable in _infra.get_runnables():
        executor.register(runnable)
    executor.run()


if __name__ == "__main__":
    main()
