from unittest.mock import patch

import pytest

from aiutil.pyscript.etc_sysctl import etc_sysctl


@patch("subprocess.run")
def test_etc_sysctl_apply(mock_run, tmp_path):
    conf_file = tmp_path / "sysctl.conf"
    etc_sysctl("vm.swappiness", "10", path=conf_file, apply=True)
    assert conf_file.read_text(encoding="utf-8") == "vm.swappiness = 10\n"
    mock_run.assert_called_once_with(["sysctl", "-p", str(conf_file)], check=True)


def test_etc_sysctl_invalid_value(tmp_path):
    conf_file = tmp_path / "sysctl.conf"
    with pytest.raises(
        ValueError, match="Invalid value '5' for key 'kernel.perf_event_paranoid'"
    ):
        etc_sysctl("kernel.perf_event_paranoid", "5", path=conf_file)


def test_etc_sysctl_new_file(tmp_path):
    conf_file = tmp_path / "sysctl.conf"
    etc_sysctl("vm.swappiness", "10", path=conf_file)
    assert conf_file.read_text(encoding="utf-8") == "vm.swappiness = 10\n"


def test_etc_sysctl_append(tmp_path):
    conf_file = tmp_path / "sysctl.conf"
    conf_file.write_text("net.ipv4.ip_forward = 0\n")
    etc_sysctl("vm.swappiness", "10", path=conf_file)
    content = conf_file.read_text(encoding="utf-8")
    assert "net.ipv4.ip_forward = 0" in content
    assert "vm.swappiness = 10" in content


def test_etc_sysctl_overwrite(tmp_path):
    conf_file = tmp_path / "sysctl.conf"
    conf_file.write_text("vm.swappiness = 60\n")
    etc_sysctl("vm.swappiness", "10", path=conf_file)
    assert conf_file.read_text(encoding="utf-8") == "vm.swappiness = 10\n"


def test_etc_sysctl_overwrite_with_spaces(tmp_path):
    conf_file = tmp_path / "sysctl.conf"
    conf_file.write_text("  vm.swappiness   = 60  \n")
    etc_sysctl("vm.swappiness", "10", path=conf_file)
    assert conf_file.read_text(encoding="utf-8") == "vm.swappiness = 10\n"
