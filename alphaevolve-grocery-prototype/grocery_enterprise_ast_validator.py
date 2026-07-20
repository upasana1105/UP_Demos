"""Enhanced AST Safety Guardrails & Validator for AlphaEvolve.

Enforces:
  1. Cyclomatic Complexity M <= 10.
  2. Prevention of self-recursion.
  3. Memory allocation safeguards.
  4. Whitelist of safe builtins and modules.
  5. EVOLVE-BLOCK tag integrity.
"""

import ast
from typing import Any, Dict, List, Set

ALLOWED_BUILTINS: Set[str] = {
    "abs",
    "all",
    "any",
    "dict",
    "float",
    "int",
    "len",
    "list",
    "max",
    "min",
    "range",
    "round",
    "set",
    "str",
    "sum",
    "tuple",
    "zip",
}

FORBIDDEN_NAMES: Set[str] = {
    "__import__",
    "eval",
    "exec",
    "open",
    "input",
    "compile",
    "globals",
    "locals",
    "getattr",
    "setattr",
    "delattr",
    "os",
    "sys",
    "subprocess",
    "shutil",
    "socket",
    "importlib",
}


def calculate_cyclomatic_complexity(node: ast.AST) -> int:
  """Calculates cyclomatic complexity M of an AST node."""
  complexity = 1
  for child in ast.walk(node):
    if isinstance(
        child,
        (
            ast.If,
            ast.For,
            ast.While,
            ast.ExceptHandler,
            ast.With,
            ast.Assert,
            ast.IfExp,
        ),
    ):
      complexity += 1
    elif isinstance(child, ast.BoolOp):
      complexity += len(child.values) - 1
  return complexity


class ASTValidator(ast.NodeVisitor):
  """AST Visitor to enforce security and safety constraints on evolved programs."""

  def __init__(self):
    self.errors: List[str] = []
    self.has_score_grocery_item = False
    self.cyclomatic_complexity = 0

  def visit_FunctionDef(self, node: ast.FunctionDef):
    if node.name == "score_grocery_item":
      self.has_score_grocery_item = True
      self.cyclomatic_complexity = calculate_cyclomatic_complexity(node)

    self.generic_visit(node)

  def visit_Call(self, node: ast.Call):
    # Recursion Check: Check if score_grocery_item is calling itself
    if isinstance(node.func, ast.Name):
      if node.func.id == "score_grocery_item":
        self.errors.append("Self-recursion detected: 'score_grocery_item' calls itself.")
      elif node.func.id in FORBIDDEN_NAMES:
        self.errors.append(f"Forbidden call to builtin/function: '{node.func.id}'")

    self.generic_visit(node)

  def visit_Name(self, node: ast.Name):
    if node.id in FORBIDDEN_NAMES:
      self.errors.append(f"Use of forbidden name/module: '{node.id}'")
    self.generic_visit(node)

  def visit_Import(self, node: ast.Import):
    for alias in node.names:
      if alias.name not in {"math"}:
        self.errors.append(f"Forbidden import: '{alias.name}'. Only 'math' is permitted.")

  def visit_ImportFrom(self, node: ast.ImportFrom):
    if node.module not in {"math"}:
      self.errors.append(f"Forbidden import from module: '{node.module}'.")

  def visit_BinOp(self, node: ast.BinOp):
    # Memory Safeguard: Block multiplication with huge numbers
    if isinstance(node.op, ast.Mult):
      if isinstance(node.left, ast.Constant) and isinstance(node.left.value, (int, float)):
        if abs(node.left.value) > 10000:
          self.errors.append(f"Memory safeguard: Multiplication factor {node.left.value} exceeds limit 10000.")
      if isinstance(node.right, ast.Constant) and isinstance(node.right.value, (int, float)):
        if abs(node.right.value) > 10000:
          self.errors.append(f"Memory safeguard: Multiplication factor {node.right.value} exceeds limit 10000.")
    self.generic_visit(node)


def validate_ast(code_str: str, max_complexity: int = 10) -> Dict[str, Any]:
  """Validates code string against AST safety guardrails."""
  # Tag integrity check
  if "# EVOLVE-BLOCK START" not in code_str or "# EVOLVE-BLOCK END" not in code_str:
    return {
        "valid": False,
        "error": "Missing mandatory '# EVOLVE-BLOCK START' or '# EVOLVE-BLOCK END' annotations.",
        "complexity": 0,
    }

  try:
    tree = ast.parse(code_str)
  except SyntaxError as e:
    return {
        "valid": False,
        "error": f"AST Parse SyntaxError: {e}",
        "complexity": 0,
    }

  validator = ASTValidator()
  validator.visit(tree)

  if not validator.has_score_grocery_item:
    return {
        "valid": False,
        "error": "Required function 'score_grocery_item' not defined.",
        "complexity": 0,
    }

  if validator.cyclomatic_complexity > max_complexity:
    validator.errors.append(
        f"Cyclomatic complexity M={validator.cyclomatic_complexity} exceeds max threshold {max_complexity}."
    )

  if validator.errors:
    return {
        "valid": False,
        "error": "; ".join(validator.errors),
        "complexity": validator.cyclomatic_complexity,
    }

  return {
      "valid": True,
      "error": None,
      "complexity": validator.cyclomatic_complexity,
  }


def validate_code_ast(code_str: str, max_complexity: int = 10):
  """Alias returning (is_valid: bool, status_message: str)."""
  res = validate_ast(code_str, max_complexity=max_complexity)
  if res["valid"]:
    return True, f"AST Validation Passed (Safe, M={res['complexity']})"
  else:
    return False, res["error"]

