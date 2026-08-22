import re

import signal_engine


def test_version_is_semver():
    assert re.fullmatch(r"\d+\.\d+\.\d+", signal_engine.__version__)


def test_cli_status_reports_missing_database(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    from signal_engine.cli import main

    assert main(["status"]) == 0
    assert "no database yet" in capsys.readouterr().out


def test_cli_unimplemented_command_exits_nonzero(capsys):
    from signal_engine.cli import main

    assert main(["digest"]) == 1
    assert "not implemented" in capsys.readouterr().err
