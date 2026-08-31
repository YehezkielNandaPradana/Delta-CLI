# tests/test_ast_symbol_parser.py
from delta.intelligence.symbols.ast_parser import ASTSymbolParser

def test_parse_python_symbols():
    py_code = '''
class AuthService:
    """Handles authentication."""
    def validate_token(self, token: str) -> bool:
        return len(token) > 10

def generate_key(user_id: int):
    return f"key_{user_id}"
'''
    parser = ASTSymbolParser()
    symbols = parser.parse_content("auth/service.py", py_code, language="python")
    names = [s.name for s in symbols]
    assert "AuthService" in names
    assert "validate_token" in names
    assert "generate_key" in names

    auth_cls = next(s for s in symbols if s.name == "AuthService")
    assert auth_cls.kind == "class"
    assert "Handles authentication" in auth_cls.docstring

    val_tok = next(s for s in symbols if s.name == "validate_token")
    assert val_tok.kind == "method"
    assert val_tok.parent_name == "AuthService"

def test_parse_js_ts_symbols():
    js_code = '''
export class TokenValidator {
    verify(token) {
        return true;
    }
}

export function parseHeader(header) {
    return header.split(" ");
}
'''
    parser = ASTSymbolParser()
    symbols = parser.parse_content("src/auth.ts", js_code, language="typescript")
    names = [s.name for s in symbols]
    assert "TokenValidator" in names
    assert "verify" in names
    assert "parseHeader" in names

def test_parse_php_symbols():
    php_code = '''<?php
class UserService {
    public function findUser($id) {
        return null;
    }
}

function helperFunc() {
    return 1;
}
'''
    parser = ASTSymbolParser()
    symbols = parser.parse_content("src/UserService.php", php_code, language="php")
    names = [s.name for s in symbols]
    assert "UserService" in names
    assert "findUser" in names
    assert "helperFunc" in names
