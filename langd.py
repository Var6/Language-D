"""Language D compiler toolchain.

Features in this prototype:
- Python-like syntax (`fn`, `let`, indentation blocks)
- Static type checking for `Int`, `Float`, `Vector[T]`
- `class` and `struct` syntax
- Safe pointer syntax (`ptr`, `setptr`)
- C++ code generation backend
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

USE_MAP: Dict[str, str] = {
    "use std": "from d_runtime import *",
    "use ds": "from d_runtime.ds import *",
    "use algo": "from d_runtime.algorithms import *",
    "use ptr": "from d_runtime.pointers import *",
}

FN_RE = re.compile(
    r"^(?P<indent>\s*)fn\s+(?P<name>[A-Za-z_]\w*)\((?P<params>[^)]*)\)\s*(?:->\s*(?P<ret>[^:]+))?:\s*$"
)
CLASS_RE = re.compile(r"^(?P<indent>\s*)class\s+(?P<name>[A-Za-z_]\w*)\s*:\s*$")
STRUCT_RE = re.compile(r"^(?P<indent>\s*)struct\s+(?P<name>[A-Za-z_]\w*)\s*:\s*$")
LET_RE = re.compile(
    r"^(?P<indent>\s*)let\s+(?P<name>[A-Za-z_]\w*)(?:\s*:\s*(?P<type>[^=]+?))?(?:\s*=\s*(?P<expr>.+))?$"
)
PTR_DECL_RE = re.compile(
    r"^(?P<indent>\s*)ptr\s+(?P<name>[A-Za-z_]\w*)(?:\s*:\s*(?P<type>[^=]+?))?\s*=\s*(?P<expr>.+)$"
)
PTR_SET_RE = re.compile(r"^(?P<indent>\s*)setptr\s+(?P<name>[A-Za-z_]\w*)\s*=\s*(?P<expr>.+)$")
RETURN_RE = re.compile(r"^\s*return(?:\s+(?P<expr>.+))?$")
TYPE_VECTOR_RE = re.compile(r"^Vector\[(?P<inner>.+)\]$")
VECTOR_GENERIC_CALL_RE = re.compile(r"Vector\[[^\]]+\]\s*\(")


def normalize_type(type_name: Optional[str]) -> str:
    if type_name is None:
        return "Unknown"
    raw = type_name.strip()
    aliases = {
        "int": "Int",
        "float": "Float",
        "str": "String",
        "string": "String",
        "bool": "Bool",
        "void": "Void",
    }
    return aliases.get(raw.lower(), raw)


def infer_type(expr: Optional[str], symbols: Dict[str, str]) -> str:
    if expr is None:
        return "Unknown"

    value = expr.strip()
    if re.fullmatch(r"-?\d+", value):
        return "Int"
    if re.fullmatch(r"-?\d+\.\d+", value):
        return "Float"
    if re.fullmatch(r"'.*'|\".*\"", value):
        return "String"
    if value in {"True", "False"}:
        return "Bool"

    m = re.match(r"^Vector\[(.+)\]\s*\(.*\)$", value)
    if m:
        return f"Vector[{normalize_type(m.group(1))}]"

    m = re.match(r"^\[(.*)\]$", value)
    if m:
        items = [x.strip() for x in m.group(1).split(",") if x.strip()]
        if not items:
            return "Vector[Any]"
        item_types = {infer_type(item, symbols) for item in items}
        if len(item_types) == 1:
            return f"Vector[{next(iter(item_types))}]"
        return "Vector[Any]"

    if value in symbols:
        return symbols[value]

    arith = re.match(r"^([A-Za-z_]\w*)\s*[+\-*/]\s*([A-Za-z_]\w*|-?\d+(?:\.\d+)?)$", value)
    if arith:
        left = infer_type(arith.group(1), symbols)
        right = infer_type(arith.group(2), symbols)
        if "Float" in (left, right):
            return "Float"
        if left == "Int" and right == "Int":
            return "Int"

    return "Unknown"


def types_compatible(expected: str, actual: str) -> bool:
    if expected == "Unknown" or actual == "Unknown":
        return True
    if expected == actual:
        return True
    if expected == "Float" and actual == "Int":
        return True
    if expected.startswith("Vector[") and actual == "Vector[Any]":
        return True
    return False


@dataclass
class FunctionScope:
    indent: int
    name: str
    return_type: str


def check_types(source: str) -> List[str]:
    errors: List[str] = []
    symbols: Dict[str, str] = {}
    scopes: List[FunctionScope] = []

    for i, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())
        while scopes and indent <= scopes[-1].indent and stripped:
            scopes.pop()

        fm = FN_RE.match(line)
        if fm:
            ret = normalize_type(fm.group("ret")) if fm.group("ret") else "Void"
            scopes.append(FunctionScope(indent=indent, name=fm.group("name"), return_type=ret))

            params = fm.group("params").strip()
            if params:
                for raw in [p.strip() for p in params.split(",") if p.strip()]:
                    if ":" in raw:
                        pname, ptype = raw.split(":", 1)
                        symbols[pname.strip()] = normalize_type(ptype)
            continue

        rm = RETURN_RE.match(line)
        if rm and scopes:
            expr_type = infer_type(rm.group("expr"), symbols)
            expected = scopes[-1].return_type
            if expected == "Void" and rm.group("expr"):
                errors.append(f"Line {i}: function '{scopes[-1].name}' returns a value but is Void")
            elif expected != "Void" and not rm.group("expr"):
                errors.append(f"Line {i}: function '{scopes[-1].name}' must return {expected}")
            elif expected != "Void" and not types_compatible(expected, expr_type):
                errors.append(
                    f"Line {i}: return type mismatch in '{scopes[-1].name}', expected {expected} got {expr_type}"
                )
            continue

        lm = LET_RE.match(line)
        if lm:
            name = lm.group("name")
            declared = normalize_type(lm.group("type")) if lm.group("type") else "Unknown"
            actual = infer_type(lm.group("expr"), symbols)
            if declared != "Unknown" and lm.group("expr") and not types_compatible(declared, actual):
                errors.append(
                    f"Line {i}: cannot assign {actual} to {name}: {declared}"
                )
            symbols[name] = declared if declared != "Unknown" else actual
            continue

    return errors


def _replace_vector_generic_calls(expr: str) -> str:
    return re.sub(r"Vector\[[^\]]+\]\s*\(", "Vector(", expr)


def transpile_source_to_python(source: str) -> str:
    out: List[str] = []
    saw_struct = False

    for raw_line in source.splitlines():
        stripped = raw_line.strip()
        indent = raw_line[: len(raw_line) - len(raw_line.lstrip())]

        if not stripped:
            out.append(raw_line)
            continue

        if stripped in USE_MAP:
            out.append(f"{indent}{USE_MAP[stripped]}")
            continue

        sm = STRUCT_RE.match(raw_line)
        if sm:
            saw_struct = True
            out.append(f"{indent}@dataclass")
            out.append(f"{indent}class {sm.group('name')}:")
            continue

        cm = CLASS_RE.match(raw_line)
        if cm:
            out.append(raw_line)
            continue

        fm = FN_RE.match(raw_line)
        if fm:
            out.append(raw_line.replace("fn ", "def ", 1))
            continue

        lm = LET_RE.match(raw_line)
        if lm:
            name = lm.group("name")
            declared = lm.group("type")
            expr = lm.group("expr")
            if expr is not None:
                out.append(f"{lm.group('indent')}{name} = {_replace_vector_generic_calls(expr.strip())}")
            elif declared is not None:
                out.append(f"{lm.group('indent')}{name}: {declared.strip()} = None")
            else:
                out.append(f"{lm.group('indent')}{name} = None")
            continue

        pm = PTR_DECL_RE.match(raw_line)
        if pm:
            out.append(f"{pm.group('indent')}{pm.group('name')} = addr({_replace_vector_generic_calls(pm.group('expr').strip())})")
            continue

        psm = PTR_SET_RE.match(raw_line)
        if psm:
            out.append(f"{psm.group('indent')}set_val({psm.group('name')}, {_replace_vector_generic_calls(psm.group('expr').strip())})")
            continue

        out.append(_replace_vector_generic_calls(raw_line))

    if saw_struct:
        out.insert(0, "from dataclasses import dataclass")

    return "\n".join(out) + "\n"


def cpp_type(type_name: str) -> str:
    t = normalize_type(type_name)
    if t == "Int":
        return "int"
    if t == "Float":
        return "double"
    if t == "Bool":
        return "bool"
    if t == "String":
        return "std::string"
    if t == "Void":
        return "void"
    vm = TYPE_VECTOR_RE.match(t)
    if vm:
        return f"std::vector<{cpp_type(vm.group('inner'))}>"
    if t.startswith("Pointer[") and t.endswith("]"):
        return f"DPointer<{cpp_type(t[8:-1])}>"
    if t == "Unknown":
        return "auto"
    return t


def transform_cpp_expr(expr: str) -> str:
    out = expr.strip()
    out = out.replace("True", "true").replace("False", "false")
    out = re.sub(r"\bval\(([^)]+)\)", r"\1.get()", out)
    out = re.sub(r"\bquick_sort\((.+)\)", r"d_quick_sort(\1)", out)
    out = re.sub(r"\bbinary_search\(([^,()]+),\s*([^()]+)\)", r"d_binary_search(\1, \2)", out)
    out = re.sub(r"\bVector\[([^\]]+)\]\s*\((.+)\)", r"std::vector<\1>(\2)", out)
    out = out.replace("self.", "this->")
    return out


def _split_top_level_args(raw: str) -> List[str]:
    parts: List[str] = []
    depth = 0
    start = 0
    for idx, ch in enumerate(raw):
        if ch in "([{" :
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        elif ch == "," and depth == 0:
            parts.append(raw[start:idx].strip())
            start = idx + 1
    tail = raw[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def _print_to_cout(args: str) -> str:
    parts = [x for x in _split_top_level_args(args) if x]
    if not parts:
        return "std::cout << std::endl"
    joined = " << \" \" << ".join(transform_cpp_expr(p) for p in parts)
    return f"std::cout << {joined} << std::endl"


def compile_to_cpp(source: str) -> str:
    lines = source.splitlines()
    out: List[str] = [
        "#include <algorithm>",
        "#include <iostream>",
        "#include <string>",
        "#include <vector>",
        "",
        "template <typename T>",
        "std::ostream& operator<<(std::ostream& os, const std::vector<T>& v) {",
        "    os << '[';",
        "    for (size_t i = 0; i < v.size(); ++i) {",
        "        if (i) os << \", \";",
        "        os << v[i];",
        "    }",
        "    os << ']';",
        "    return os;",
        "}",
        "",
        "template <typename T>",
        "struct DPointer {",
        "    T value;",
        "    explicit DPointer(T v) : value(v) {}",
        "    T get() const { return value; }",
        "    void set(const T& v) { value = v; }",
        "};",
        "",
        "template <typename T>",
        "std::vector<T> d_quick_sort(std::vector<T> v) {",
        "    std::sort(v.begin(), v.end());",
        "    return v;",
        "}",
        "",
        "template <typename T>",
        "int d_binary_search(const std::vector<T>& v, const T& target) {",
        "    auto it = std::lower_bound(v.begin(), v.end(), target);",
        "    if (it == v.end() || *it != target) return -1;",
        "    return static_cast<int>(it - v.begin());",
        "}",
        "",
    ]

    blocks: List[Tuple[int, str]] = [(0, "root")]

    def close_block() -> None:
        level, kind = blocks.pop()
        close = "};" if kind in {"struct", "class"} else "}"
        out.append("    " * (level - 1) + close)

    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("use "):
            continue

        indent = (len(raw) - len(raw.lstrip())) // 4
        while len(blocks) - 1 > indent:
            close_block()

        fm = FN_RE.match(raw)
        if fm:
            fn_name = fm.group("name")
            params = [p.strip() for p in fm.group("params").split(",") if p.strip()]
            cpp_params: List[str] = []
            for p in params:
                if p == "self":
                    continue
                if ":" in p:
                    pname, ptype = p.split(":", 1)
                    cpp_params.append(f"{cpp_type(ptype.strip())} {pname.strip()}")
                else:
                    cpp_params.append(f"auto {p}")

            ret = cpp_type(fm.group("ret") if fm.group("ret") else "Void")
            if fn_name == "main":
                ret = "int"
            out.append("    " * indent + f"{ret} {fn_name}({', '.join(cpp_params)}) {{")
            blocks.append((indent + 1, "fn"))
            continue

        sm = STRUCT_RE.match(raw)
        if sm:
            out.append("    " * indent + f"struct {sm.group('name')} {{")
            blocks.append((indent + 1, "struct"))
            continue

        cm = CLASS_RE.match(raw)
        if cm:
            out.append("    " * indent + f"class {cm.group('name')} {{")
            out.append("    " * (indent + 1) + "public:")
            blocks.append((indent + 1, "class"))
            continue

        if stripped.startswith("if ") and stripped.endswith(":"):
            condition = transform_cpp_expr(stripped[3:-1])
            out.append("    " * indent + f"if ({condition}) {{")
            blocks.append((indent + 1, "if"))
            continue

        if stripped.startswith("elif ") and stripped.endswith(":"):
            condition = transform_cpp_expr(stripped[5:-1])
            out.append("    " * indent + f"else if ({condition}) {{")
            blocks.append((indent + 1, "if"))
            continue

        if stripped == "else:":
            out.append("    " * indent + "else {")
            blocks.append((indent + 1, "if"))
            continue

        if stripped.startswith("while ") and stripped.endswith(":"):
            condition = transform_cpp_expr(stripped[6:-1])
            out.append("    " * indent + f"while ({condition}) {{")
            blocks.append((indent + 1, "while"))
            continue

        if stripped.startswith("for ") and stripped.endswith(":"):
            m_for = re.match(r"for\s+([A-Za-z_]\w*)\s+in\s+(.+):$", stripped)
            if m_for:
                var_name = m_for.group(1)
                iterable = transform_cpp_expr(m_for.group(2))
                out.append("    " * indent + f"for (auto& {var_name} : {iterable}) {{")
                blocks.append((indent + 1, "for"))
                continue

        lm = LET_RE.match(raw)
        if lm:
            name = lm.group("name")
            declared_type = normalize_type(lm.group("type")) if lm.group("type") else "Unknown"
            expr = lm.group("expr")
            if declared_type != "Unknown":
                ctype = cpp_type(declared_type)
                if expr is None:
                    out.append("    " * indent + f"{ctype} {name};")
                else:
                    cexpr = transform_cpp_expr(expr)
                    if ctype.startswith("std::vector<") and expr.strip().startswith("[") and expr.strip().endswith("]"):
                        cexpr = "{" + expr.strip()[1:-1] + "}"
                    out.append("    " * indent + f"{ctype} {name} = {cexpr};")
            else:
                if expr is None:
                    out.append("    " * indent + f"auto {name} = 0;")
                else:
                    out.append("    " * indent + f"auto {name} = {transform_cpp_expr(expr)};")
            continue

        pm = PTR_DECL_RE.match(raw)
        if pm:
            declared_type = normalize_type(pm.group("type")) if pm.group("type") else infer_type(pm.group("expr"), {})
            ctype = cpp_type(declared_type)
            out.append(
                "    " * indent
                + f"DPointer<{ctype}> {pm.group('name')}({transform_cpp_expr(pm.group('expr'))});"
            )
            continue

        psm = PTR_SET_RE.match(raw)
        if psm:
            out.append("    " * indent + f"{psm.group('name')}.set({transform_cpp_expr(psm.group('expr'))});")
            continue

        if stripped.startswith("print(") and stripped.endswith(")"):
            out.append("    " * indent + _print_to_cout(stripped[6:-1]) + ";")
            continue

        if stripped == "main()":
            continue

        if stripped.startswith("return"):
            rm = RETURN_RE.match(raw)
            expr = rm.group("expr") if rm else None
            if expr:
                out.append("    " * indent + f"return {transform_cpp_expr(expr)};")
            else:
                out.append("    " * indent + "return;")
            continue

        if stripped.endswith(")") and not stripped.startswith(("if ", "while ", "for ")):
            out.append("    " * indent + transform_cpp_expr(stripped) + ";")
            continue

        out.append("    " * indent + transform_cpp_expr(stripped) + ";")

    while len(blocks) > 1:
        close_block()

    return "\n".join(out) + "\n"


def ensure_d_file(file_path: pathlib.Path) -> Optional[str]:
    if file_path.suffix != ".d":
        return f"Language D source files must use .d extension: {file_path}"
    return None


def run_file(file_path: pathlib.Path) -> int:
    source = file_path.read_text(encoding="utf-8")
    errors = check_types(source)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 2

    code = transpile_source_to_python(source)
    globals_dict = {"__name__": "__main__", "__file__": str(file_path)}
    exec(compile(code, str(file_path), "exec"), globals_dict)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Language D toolchain")
    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("run", help="Type-check and run a .d file")
    run_cmd.add_argument("file", help="Path to .d file")

    tr_cmd = sub.add_parser("transpile", help="Print generated Python code")
    tr_cmd.add_argument("file", help="Path to .d file")

    check_cmd = sub.add_parser("check", help="Run static type checks")
    check_cmd.add_argument("file", help="Path to .d file")

    cpp_cmd = sub.add_parser("compile-cpp", help="Generate C++ from .d source")
    cpp_cmd.add_argument("file", help="Path to .d file")
    cpp_cmd.add_argument("-o", "--out", help="Output .cpp path")

    args = parser.parse_args()
    file_path = pathlib.Path(args.file)

    if not file_path.exists():
        print(f"File not found: {file_path}", file=sys.stderr)
        return 1

    ext_error = ensure_d_file(file_path)
    if ext_error:
        print(ext_error, file=sys.stderr)
        return 1

    source = file_path.read_text(encoding="utf-8")

    if args.command == "check":
        errors = check_types(source)
        if errors:
            for err in errors:
                print(err, file=sys.stderr)
            return 2
        print("Type check passed")
        return 0

    if args.command == "transpile":
        print(transpile_source_to_python(source), end="")
        return 0

    if args.command == "compile-cpp":
        output = pathlib.Path(args.out) if args.out else file_path.with_suffix(".cpp")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(compile_to_cpp(source), encoding="utf-8")
        print(f"Generated C++: {output}")
        return 0

    return run_file(file_path)


if __name__ == "__main__":
    raise SystemExit(main())
