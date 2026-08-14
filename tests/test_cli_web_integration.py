import pytest
from delta.main import build_parser

def test_web_flag_parsing():
    parser = build_parser()
    args = parser.parse_args(["--web"])
    assert args.web is True
