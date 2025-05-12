#!/usr/bin/env python3
"""
extract_deps.py

Scans Python (.py) and Jupyter Notebook (.ipynb) files for imports and
generates Poetry 'add' commands for each detected top-level package.

Usage:
  python extract_deps.py path/to/project [another/path.ipynb] \
      [-o deps_commands.txt]

This will print lines like:
  poetry add flask
  poetry add numpy

or write them to the specified output file.

Features:
- Automatically includes 'ipykernel' if any .ipynb files are scanned.
- Maps common import names to the correct PyPI package names (e.g., 'skimage' -> 'scikit-image').
"""

import argparse
import ast
import json
import os
import sys


# Mapping from import name to PyPI package name
PACKAGE_MAP = {
    'skimage': 'scikit-image',
    # add more mappings here as needed, e.g.:
    # 'PIL': 'Pillow',
    # 'cv2': 'opencv-python',
}


def find_files(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            for root, _, fs in os.walk(p):
                for f in fs:
                    if f.endswith('.py') or f.endswith('.ipynb'):
                        files.append(os.path.join(root, f))
        elif os.path.isfile(p) and (p.endswith('.py') or p.endswith('.ipynb')):
            files.append(p)
        else:
            print(f"Warning: skipping invalid path: {p}", file=sys.stderr)
    return files


def extract_imports_from_code(code):
    modules = set()
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return modules
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module.split('.')[0])
    return modules


def extract_imports_from_py(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return extract_imports_from_code(f.read())
    except Exception as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        return set()


def extract_imports_from_ipynb(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        modules = set()
        for cell in data.get('cells', []):
            if cell.get('cell_type') == 'code':
                code = ''.join(cell.get('source', []))
                modules |= extract_imports_from_code(code)
        return modules
    except Exception as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        return set()


def main():
    parser = argparse.ArgumentParser(
        description="Extract dependencies and generate Poetry add commands."
    )
    parser.add_argument(
        'paths', nargs='+', help="Files or directories to scan (.py, .ipynb)"
    )
    parser.add_argument(
        '-o', '--output', help="Output file for commands (default: stdout)"
    )
    args = parser.parse_args()

    files = find_files(args.paths)
    if not files:
        print("No Python or notebook files found.", file=sys.stderr)
        sys.exit(1)

    # Detect if any notebooks were scanned
    include_ipykernel = any(f.endswith('.ipynb') for f in files)

    all_modules = set()
    for path in files:
        if path.endswith('.py'):
            all_modules |= extract_imports_from_py(path)
        elif path.endswith('.ipynb'):
            all_modules |= extract_imports_from_ipynb(path)

    # Always include ipykernel if notebooks are present
    if include_ipykernel:
        all_modules.add('ipykernel')

    # Optionally filter out standard library modules by populating this set
    stdlib = set()

    # Prepare final dependency list, applying package name mappings
    deps = sorted(all_modules - stdlib)
    deps = [PACKAGE_MAP.get(m, m) for m in deps]

    commands = [f"poetry add {m}" for m in deps]

    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write("\n".join(commands))
            print(f"Wrote {len(commands)} commands to {args.output}")
        except Exception as e:
            print(f"Error writing to {args.output}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("\n".join(commands))


if __name__ == '__main__':
    main()
