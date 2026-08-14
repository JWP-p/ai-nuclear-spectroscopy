import pytest

from ai_nuclear_spectroscopy.cli import build_parser


def test_fetch_limit_must_be_non_negative() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "fetch-ensdf",
                "--nucleus",
                "100Mo",
                "--output-dir",
                "out",
                "--limit",
                "-1",
            ]
        )
