import importlib.util
import subprocess
import typing
from logging import getLogger

from thonny import get_workbench
from thonny.lsp_proxy import LanguageServerProxy
from thonny.running import create_frontend_python_process

logger = getLogger(__name__)


class RuffProxy(LanguageServerProxy):

    def _create_server_process(self) -> subprocess.Popen[bytes]:
        return create_frontend_python_process(
            ["-m", "ruff", "server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=False,
        )

    def get_supported_language_ids(self) -> typing.Set[str]:
        return {"python"}


def load_plugin():
    # Ruff is launched with the same Python that runs the IDE, so only register
    # it when that runtime actually has it. Registering a server that can't
    # start would just produce a crash/restart cycle.
    if importlib.util.find_spec("ruff") is None:
        logger.info("ruff is not installed in this runtime; Ruff linting is disabled")
        return
    get_workbench().add_language_server_proxy_class(RuffProxy)
