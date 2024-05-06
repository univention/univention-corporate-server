from pathlib import Path

import pytest

from univention.testing.ldif import main


@pytest.mark.parametrize("output", [pytest.param(p, id=p.parent.name) for p in Path(__file__).parent.glob("*/OutputOK")])
def test_all(output, capsys):
    with pytest.raises(SystemExit):
        main(["--attributes", output.with_name("InputA.ldif").as_posix(), output.with_name("InputB.ldif").as_posix()])
    out, _err = capsys.readouterr()
    assert out == output.read_text()
