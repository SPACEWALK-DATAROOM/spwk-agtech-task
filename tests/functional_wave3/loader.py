"""Execute selected original definitions, with explicit dependency bindings.

This is isolated source behavior, not application startup or framework integration.
Original decorators, declaration order and annotation policy are retained.
"""
import ast
import abc
import gzip
import __future__
import datetime
import hashlib
import io
import itertools
import json
import logging
import os
import random
import re
import sys
import time
import types
import typing
from pathlib import Path
from functools import partial
from dateutil.relativedelta import relativedelta
from types import SimpleNamespace, MethodType
import pandas as pd
import numpy as np
ROOT = Path(__file__).resolve().parents[2]

def offline(event, args):
    if event in ("socket.connect", "socket.getaddrinfo"):
        raise RuntimeError("External network is unavailable in isolated source contracts")
sys.addaudithook(offline)

def load(path, names, owner=None, **bindings):
    source = (ROOT / path).resolve()
    if ROOT not in source.parents or source.suffix != ".py":
        raise ValueError("Selected source must be a Python file inside this repository")
    text = source.read_text()
    tree = ast.parse(text, filename=str(source))
    body = tree.body
    for part in (owner.split(".") if owner else []):
        matches = [n for n in body if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == part]
        if len(matches) != 1:
            raise ValueError("Source owner must resolve exactly once: " + part)
        body = matches[0].body
    if len(names) != len(set(names)):
        raise ValueError("Duplicate requested definitions")
    nodes = []
    provenance = []
    for name in names:
        matches = [n for n in body if
                   isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == name or
                   isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
        if len(matches) != 1:
            raise ValueError("Definition must resolve exactly once: " + name)
        node = matches[0]
        original_ast = ast.dump(node, include_attributes=False)
        removed = []
        nodes.append(node)
        provenance.append({"name": name, "line": node.lineno,
                           "original_ast_sha256": hashlib.sha256(original_ast.encode()).hexdigest(),
                           "removed_prefect_task_decorators": len(removed)})
    # Preserve original declaration order, including dependencies between classes.
    nodes.sort(key=lambda n: n.lineno)
    flags = 0
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            for feature in node.names:
                flags |= getattr(__future__, feature.name).compiler_flag
    ns = {"pd": pd, "DataFrame": pd.DataFrame, "abc": abc, "ABC": abc.ABC, "abstractmethod": abc.abstractmethod, "gzip": gzip, "np": np, "logging": logging, "LOGGER": logging.getLogger("offline"),
          "datetime": datetime, "dt": datetime, "types": types, "io": io, "json": json,
          "os": os, "re": re, "time": time, "random": random, "itertools": itertools,
          "Path": Path, "partial": partial, "relativedelta": relativedelta,
          "typing": typing, "ty": typing,
          "Any": typing.Any, "Callable": typing.Callable, "Dict": typing.Dict,
          "List": typing.List, "Tuple": typing.Tuple, "Optional": typing.Optional,
          "Union": typing.Union, "Set": typing.Set, "Iterable": typing.Iterable,
          "__file__": str(source), "__name__": "isolated_source_contract", **bindings}
    safe = {"copy", "abc", "collections", "dataclasses", "datetime", "decimal", "enum", "functools", "itertools", "json", "logging", "math", "numpy", "pandas", "random", "re", "statistics", "typing"}
    for imported in tree.body:
        if isinstance(imported, ast.Import) and all(alias.name.split('.')[0] in safe for alias in imported.names) or isinstance(imported, ast.ImportFrom) and imported.module and imported.module.split('.')[0] in safe:
            exec(compile(ast.Module(body=[imported], type_ignores=[]), str(source), "exec", dont_inherit=True), ns)
    ns.update(bindings)
    ns["__name__"] = "isolated_" + hashlib.sha256(str(source).encode()).hexdigest()[:16]
    module = types.ModuleType(ns["__name__"])
    module.__dict__.update(ns)
    ns = module.__dict__
    sys.modules[module.__name__] = module
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), "exec", flags=flags, dont_inherit=True), ns)
    ns["__source_provenance__"] = {"path": path, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                                    "owner": owner, "definitions": provenance,
                                    "future_flags": flags}
    return ns


