"""
pypath/pypath
~~~~~~~~~~~~~

This is a demonstration docstring.
"""

import contextlib
import os
from functools import lru_cache
from pathlib import Path


class PyPath:
    def __init__(self, path, pattern="~", git_as_root=True):
        self.path = Path(path).resolve()
        self.pattern = pattern
        self.git_as_root = git_as_root

    @property
    @lru_cache
    def root_path(self):
        return (
            self._get_git_path(self.path)
            if self.git_as_root is True and self._get_git_path(self.path) is not None
            else self.path
        )

    @property
    @lru_cache
    def relative_path(self):
        return (
            str(self.path.relative_to(self.root_path)).replace(".py", "").replace("/__init__", "")
        )

    @property
    @lru_cache
    def input_docstring(self):
        docstring_border_count = 0
        docstring_lines = []
        for line_num, line in enumerate(self.input_pycontent.strip().split("\n")):
            if '"""' in line or "'''" in line:
                docstring_border_count += 1
                continue
            if line_num == 0:
                break
            if docstring_border_count == 1:
                docstring_lines.append(line)
        return "\n".join(docstring_lines)

    @property
    @lru_cache
    def output_docstring(self):
        input_docstring_array = self.input_docstring.split("\n")
        file_path = None
        file_underscore = None
        for idx, line in enumerate(input_docstring_array):
            if self._str_likely_a_path(line):
                file_path = line
                with contextlib.suppress(IndexError):
                    if self._is_likely_an_underscore(input_docstring_array[idx + 1]):
                        file_underscore = input_docstring_array[idx + 1]
                break
        if file_path is None or file_underscore is None:
            return (
                f"{self.relative_path}\n{self._underscore}\n\n{self.input_docstring}"
                if self.input_docstring
                else f"{self.relative_path}\n{self._underscore}"
            )
        return (
            "\n".join(input_docstring_array)
            .replace(file_path, self.relative_path)
            .replace(file_underscore, self._underscore)
        )

    @property
    @lru_cache
    def input_pycontent(self):
        with open(self.path, "r") as f:
            return f.read()

    @property
    @lru_cache
    def output_pycontent(self):
        # Ammended python file
        if not self.input_docstring:
            return f'"""\n{self.output_docstring}\n"""\n\n{self.input_pycontent}'
        return self.input_pycontent.replace(self.input_docstring, self.output_docstring)

    def overwrite_pyfile(self):
        # Directly calling a class property when writing to file does not seem to work as expected
        export_content = self.output_pycontent
        with open(self.path, "w") as f:
            f.write(export_content)

    @property
    @lru_cache
    def _underscore(self):
        underscore_pattern = ""
        underscore_idx = 0
        while len(underscore_pattern) < len(self.relative_path):
            try:
                underscore_pattern += self.pattern[underscore_idx]
                underscore_idx += 1
            except IndexError:
                underscore_idx = 0
        return underscore_pattern

    @staticmethod
    def _get_git_path(path):
        path = path.resolve()
        if path.is_file():
            path = path.parent
        if path == path.parent:
            return None
        return (
            path
            if ".git" in [item.lower() for item in os.listdir(path)]
            else PyPath._get_git_path(path.parent)
        )

    @staticmethod
    def _str_likely_a_path(s):
        s_path = Path(s)
        return len(s_path.parents) - 1 > PyPath._get_adj_space_count(s_path)

    @staticmethod
    def _is_likely_an_underscore(s):
        for i in range(len(s)):
            adjusted_s = s[: -(i + 1)]
            if len(adjusted_s) == 1:
                break
            pattern_found = (s).count(adjusted_s)
            if pattern_found > 1:
                return True
        return False

    @staticmethod
    def _get_adj_space_count(path, space_count=0):
        """Gets adjusted spaces in path - takes directory with many spaces and treats it as
        1 space."""
        if path == path.parent:
            return max(space_count, 0)
        if num_spaces_in_current_dir := Path(path).name.count(" "):
            return PyPath._get_adj_space_count(
                path.parent, space_count + num_spaces_in_current_dir - 2
            )
        return PyPath._get_adj_space_count(path.parent, space_count)
