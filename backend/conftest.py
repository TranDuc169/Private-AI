"""Keep each pytest invocation out of shared Windows pytest-of-Admin folders."""
import tempfile
from pathlib import Path


def pytest_configure(config):
    if config.option.basetemp is None:
        # Unique directory per run/user; never remove or reuse another run's folder.
        config._private_ai_tempdir = tempfile.TemporaryDirectory(prefix='private-ai-pytest-')
        config.option.basetemp = Path(config._private_ai_tempdir.name) / 'files'


def pytest_unconfigure(config):
    folder = getattr(config, '_private_ai_tempdir', None)
    if folder is not None:
        folder.cleanup()
