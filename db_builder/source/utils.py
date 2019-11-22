#!/usr/bin/env python3
# coding=utf8
"""utils is a collection of functions used in db_builder
They do not tie directly to any other class
"""
from typing import Set, Tuple, List
import os
import shutil
import pyodbc


def list_databases(svr: str) -> Set[str]:
    """ List all databases in server"""

    conn = pyodbc.connect((f"Driver={{SQL Server}};Server={svr};"
                           "Database=master;Trusted_Connection=yes;"))
    cur = conn.cursor()
    cur.execute("SELECT name FROM sys.databases")
    return set(
        row[0]
        for row in cur.fetchall()
    )


def copy_folder(old: str, new: str) -> None:
    """ copies folder old and contents to folder new"""
    if os.path.isdir(new):
        return

    try:
        shutil.copytree(old, new)
    except shutil.Error as shutil_error:
        print(f'Files not copied. Error: {shutil_error}')
    except OSError as os_error:
        print(f'Files not copied. Error: {os_error}')


def get_file_parts(path: str, start: str,
                   end: str = '[END]') -> Tuple[List[str]]:
    """ Reads file and separates into (opening, useful part, ending) """
    with open(path, 'r') as f:
        lines = f.read().splitlines()

    start_loc = lines.index(start) + 1

    opening = lines[:start_loc]
    middle = lines[start_loc:]

    end_loc = middle.index(end)
    ending = middle[end_loc:]

    middle = middle[:end_loc]

    return opening, middle, ending


def add_sorted_line(lines: List[str], new_line: str) -> List[str]:
    """ Appends new line to list and returns the sorted list """
    if new_line not in lines:
        lines.append(new_line)
    lines.sort()

    return lines


def combine_lines(parts: Tuple[List[str]]) -> List[str]:
    """ Flattens tuple of lists into list of strings ending with '\n' """
    return [row + '\n' for part in parts for row in part]


def save_config(path: str, to_save: List[str]) -> bool:
    """ Saves the list of strings as config file """
    try:
        with open(path, 'r+') as f:
            f.seek(0)
            f.writelines(to_save)
            f.truncate()
        return True
    except Exception as err:
        print(err)
        return False
