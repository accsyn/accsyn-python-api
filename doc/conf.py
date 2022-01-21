# :coding: utf-8
# :copyright: Copyright (c) 2021 accsyn/HDR AB

"""accsyn Python API documentation build configuration file."""

import os
import re
from pkg_resources import get_distribution, DistributionNotFound

# -- General ------------------------------------------------------------------

# Extensions.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "lowdown",
]


# The suffix of source filenames.
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = u"accsyn Python API"
copyright = u"2021, accsyn/HDR AB"

# contents of docs/conf.py
try:
    release = get_distribution("accsyn-python-api").version
    # take major/minor/patch
    VERSION = release.split("-")[0]
except DistributionNotFound:
    # package is not installed
    VERSION = "Unknown version"

version = VERSION
release = VERSION

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_template"]

# A list of prefixes to ignore for module listings.
modindex_common_prefix = ["accsyn_api."]

# -- HTML output --------------------------------------------------------------

if not os.environ.get("READTHEDOCS", None) == "True":
    # Only import and set the theme if building locally.
    import sphinx_rtd_theme

    html_theme = "sphinx_rtd_theme"
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

html_static_path = ["_static"]
html_style = "accsyn.css"

# If True, copy source rst files to output for reference.
html_copy_source = True


# -- Autodoc ------------------------------------------------------------------

autodoc_default_flags = ["members", "undoc-members", "inherited-members"]
autodoc_member_order = "bysource"


def autodoc_skip(app, what, name, obj, skip, options):
    """Don't skip __init__ method for autodoc."""
    if name == "__init__":
        return False

    return skip


import os
import sys

sys.path.insert(0, os.path.join(os.path.abspath(".."), "source"))

# -- Intersphinx --------------------------------------------------------------

# intersphinx_mapping = {
#    'python': ('http://docs.python.org/', None),
#    'accsyn': (
#        'http://rtd.accsyn.com/docs/accsyn/en/stable/', None
#    )
# }


# -- Todos ---------------------------------------------------------------------

# todo_include_todos = os.environ.get('ACCSYN_DOC_INCLUDE_TODOS', False) == 'True'


# -- Setup --------------------------------------------------------------------


def setup(app):
    app.connect("autodoc-skip-member", autodoc_skip)
