# MIT License
#
# Copyright (c) 2024 Chris Fisher ("cdfisher")
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""parser_utils.py - (c) 2023-2024 Chris Fisher ("cdfisher")
Utility functions for use in conjunction with mwparserfromhell, generally relating to the retrieval or modification
of template parameter values.
"""

import re
from mwparserfromhell.nodes.template import Template


# get all version_name, param_name, param_val sets for a template
def get_all_param_versions(t: Template, parameter: str, split_comma_vals=True) -> list:
    """Gets a list of all values of a given template parameter used in a template along with which version of the
    template is

    :param t: template to parse
    :type t: Template

    :param parameter: The template parameter of interest.
    :type parameter: str

    :param split_comma_vals: Whether to split `parameter` values that are comma-separated lists into separate entries,
    defaults to False.
    :type split_comma_vals: bool

    :return: Returns a list of all [template_version_name, parameter_version_name, parameter_value] list entries in
    `template`.
    :rtype: list
    """
    matches = []

    if t.has(parameter):
        val = t.get(parameter).value.strip(' \r\n')

        if split_comma_vals:
            if ',' in val:
                values = val.split(',')
                for v in values:
                    matches.append(["default", parameter, v])

            else:
                matches.append(["default", parameter, val])

        else:
            matches.append(["default", parameter, val])

        default_val = val

        # Case: multiple template versions, has default parameter
        n = 0
        while True:
            n += 1
            ver = f'version{n}'
            param = f'{parameter}{n}'
            if t.has(ver):
                if t.has(param):
                    val = t.get(param).value.strip(' \r\n')
                    if split_comma_vals:
                        if ',' in val:
                            values = val.split(',')
                            for v in values:
                                matches.append([ver, param, v])

                        else:
                            matches.append([ver, param, val])

                    else:
                        matches.append([ver, param, val])

                else:
                    matches.append(([ver, "default", default_val]))

            else:
                break

    # Case: multiple template versions, no default parameter
    else:
        n = 0
        while True:
            n += 1
            ver = f'version{n}'
            param = f'{parameter}{n}'
            if t.has(ver):
                if t.has(param):
                    val = t.get(param).value.strip(' \r\n')
                    if split_comma_vals:
                        if ',' in val:
                            values = val.split(',')
                            for v in values:
                                matches.append([ver, param, v])

                        else:
                            matches.append([ver, param, val])

                    else:
                        matches.append([ver, param, val])

                else:
                    continue

            else:
                break

    return matches


# get version_name, param_name, param_val for template where a param value is matched
def get_matching_param_versions(t: Template, parameter: str, match_value: str, case_sensitive=False,
                                strip_comments=True) -> list:
    """

    :param t: template to parse
    :type t: Template

    :param parameter: The template parameter of interest.
    :type parameter: str

    :param match_value: Value to match the `parameter` value against. Can be a regular expression or a basic string.
    :type match_value: str

    :param case_sensitive: Whether or not matching is case-sensitive, defaults to False.
    :type case_sensitive: bool

    :param strip_comments: Whether or not wikicode comments should be stripped from values before matching, defaults to
    True.
    :type strip_comments: bool

    :return: Returns a list of all [template_version_name, parameter_version_name, parameter_value] list entries in
    `template` where parameter_value matches `match_value`.
    :rtype: list
    """
    matches = []
    if case_sensitive:
        match_value = match_value.lower()

    if t.has(parameter):
        val = t.get(parameter).value.strip(' \r\n')
        if strip_comments:
            val = re.sub("(<!--.*?-->)", "", val, flags=re.DOTALL)
        if re.search(match_value, val) is not None:
            matches.append(["default", parameter, val])

        # Case: multiple template versions, has default parameter
        n = 0
        while True:
            n += 1
            ver = f'version{n}'
            param = f'{parameter}{n}'
            if t.has(ver):
                if t.has(param):
                    val = t.get(param).value.strip(' \r\n')
                    if strip_comments:
                        val = re.sub("(<!--.*?-->)", "", val, flags=re.DOTALL)
                    if re.search(match_value, val) is not None:
                        matches.append([ver, param, val])

                else:
                    continue

            else:
                break

    # Case: multiple template versions, no default parameter
    else:
        n = 0
        while True:
            n += 1
            ver = f'version{n}'
            param = f'{parameter}{n}'
            if t.has(ver):
                if t.has(param):
                    val = t.get(param).value.strip(' \r\n')
                    if strip_comments:
                        val = re.sub("(<!--.*?-->)", "", val, flags=re.DOTALL)
                    if re.search(match_value, val) is not None:
                        matches.append([ver, param, val])

                else:
                    continue

            else:
                break

    return matches
