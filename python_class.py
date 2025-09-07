import ast
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from wattleflow.core import IExpression
from core.builder import UMLBuilder


def _unparse(node: Optional[ast.AST]) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{_unparse(node.value)}.{node.attr}"
        if isinstance(node, ast.Subscript):
            return f"{_unparse(node.value)}[{_unparse(getattr(node, 'slice', None))}]"
        if isinstance(node, ast.Tuple):
            return ", ".join(_unparse(elt) for elt in node.elts)
        return node.__class__.__name__


def _visibility(name: str) -> str:
    if name.startswith("__") and not name.endswith("__"):
        return "-"
    if name.startswith("_"):
        return "#"
    return "+"


@dataclass
class MethodInfo:
    name: str
    params: List[Tuple[str, str]]
    returns: str
    is_classmethod: bool = False
    is_staticmethod: bool = False

    def signature(self) -> str:
        args = ", ".join(f"{n}: {t}" if t else n for n, t in self.params)
        ret = f": {self.returns}" if self.returns else ""
        return f"{self.name}({args}){ret}"


@dataclass
class ClassInfo:
    name: str
    bases: List[str] = field(default_factory=list)
    attrs: List[Tuple[str, str]] = field(default_factory=list)
    methods: List[MethodInfo] = field(default_factory=list)


class ParsePythonModule(IExpression):
    """
    interpret(context) očekuje cijeli Python modul kao string
    i puni self.classes za daljnji render.
    """

    def __init__(self):
        self.classes: Dict[str, ClassInfo] = {}

    def interpret(self, context: str) -> bool:
        try:
            tree = ast.parse(context)
        except SyntaxError:
            return False

        for node in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
            self._parse_class(node)

        return bool(self.classes)

    def _parse_class(self, node: ast.ClassDef) -> None:
        ci = ClassInfo(
            name=node.name,
            bases=[_unparse(b) for b in node.bases if not isinstance(b, ast.Call)],
        )

        # class-level atributi
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                ci.attrs.append((stmt.target.id, _unparse(stmt.annotation)))
            elif isinstance(stmt, ast.Assign):
                for t in stmt.targets:
                    if isinstance(t, ast.Name):
                        ci.attrs.append((t.id, ""))

        # metode + instance atributi
        for stmt in node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                m = self._parse_method(stmt)
                # ukloni self/cls iz potpisa
                if m.params and (
                    m.is_classmethod
                    and m.params[0][0] == "cls"  # noqa: W503
                    or (not m.is_classmethod and m.params[0][0] == "self")  # noqa: W503
                ):
                    m.params = m.params[1:]
                ci.methods.append(m)

                for n in ast.walk(stmt):
                    if isinstance(n, ast.AnnAssign) and isinstance(
                        n.target, ast.Attribute
                    ):
                        if (
                            isinstance(n.target.value, ast.Name)
                            and n.target.value.id == "self"  # noqa: W503
                        ):
                            ci.attrs.append((n.target.attr, _unparse(n.annotation)))
                    elif isinstance(n, ast.Assign):
                        for t in n.targets:
                            if (
                                isinstance(t, ast.Attribute)
                                and isinstance(t.value, ast.Name)  # noqa: W503
                                and t.value.id == "self"  # noqa: W503
                            ):
                                ci.attrs.append((t.attr, ""))

        # deduplikacija (zadnja vrijednost pobjeđuje)
        seen: Dict[str, str] = {}
        for name, typ in ci.attrs:
            seen[name] = typ or seen.get(name, "")
        ci.attrs = [(k, seen[k]) for k in seen.keys()]

        self.classes[ci.name] = ci

    @staticmethod
    def _dec_name(d: ast.AST) -> str:
        if isinstance(d, ast.Name):
            return d.id
        if isinstance(d, ast.Attribute):
            return d.attr
        return _unparse(d)

    def _parse_method(self, fn: ast.FunctionDef) -> MethodInfo:
        returns = _unparse(fn.returns)
        deco_names = {self._dec_name(d) for d in fn.decorator_list}
        is_class = "classmethod" in deco_names
        is_static = "staticmethod" in deco_names

        params: List[Tuple[str, str]] = []
        a = fn.args
        ordered = (
            (a.posonlyargs or [])
            + a.args  # noqa: W503
            + ([] if a.vararg is None else [a.vararg])  # noqa: W503
            + a.kwonlyargs  # noqa: W503
            + ([] if a.kwarg is None else [a.kwarg])  # noqa: W503
        )

        for p in ordered:
            name = p.arg
            if a.vararg is p:
                name = "*" + name
            if a.kwarg is p:
                name = "**" + name
            params.append((name, _unparse(getattr(p, "annotation", None))))

        return MethodInfo(
            name=fn.name,
            params=params,
            returns=returns,
            is_classmethod=is_class,
            is_staticmethod=is_static,
        )


class PythonUMLClassBuilder(UMLBuilder):
    def build(self) -> None:
        expr = ParsePythonModule()
        src = str(self._content)

        if not expr.interpret(src):
            self._rendered = "@startuml\n' Nije pronađena nijedna klasa.\n@enduml"
            return

        uml: List[str] = ["@startuml", "skinparam linetype ortho", "!pragma teoz true"]

        # klase
        for cls in expr.classes.values():
            uml.append(f"class {cls.name} {{")
            for name, typ in cls.attrs:
                vis = _visibility(name)
                uml.append(f"  {vis} {name}{f': {typ}' if typ else ''}")
            for m in cls.methods:
                vis = _visibility(m.name)
                stereo = (
                    " «class»"
                    if m.is_classmethod
                    else (" «static»" if m.is_staticmethod else "")
                )
                uml.append(f"  {vis} {m.signature()}{stereo}")
            uml.append("}")

        local: Set[str] = set(expr.classes.keys())
        for cls in expr.classes.values():
            for b in cls.bases:
                if b and b not in {"object", "Any"}:
                    uml.append(f"{b} <|-- {cls.name}")

        # jednostavna kompozicija (tip atributa je ime druge lokalne klase)
        for cls in expr.classes.values():
            for _, typ in cls.attrs:
                raw = typ
                for prefix in ("Optional[", "List[", "Dict[", "Set[", "Tuple["):
                    if raw.startswith(prefix):
                        raw = raw[len(prefix) :]
                raw = raw.rstrip("]").split(",")[0].strip().strip('"').strip("'")
                if raw in local and raw != cls.name:
                    uml.append(f"{cls.name} *-- {raw}")

        uml.append("@enduml")
        self._rendered = "\n".join(uml)
