import sys
from pathlib import Path
import pytest
from aiutil.pyscript import shebang

BASE_DIR = Path(__file__).parent


@pytest.mark.skipif(sys.platform == "win32", reason="Skip test on Windows")
def test_shebang():
    shebang.update_shebang(BASE_DIR / "script_dir", "#!/usr/bin/env python3")
