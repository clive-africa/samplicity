import os
import sys

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------
project = 'samplicity'
copyright = '2024, Clive Hogarth'
author = 'Clive Hogarth'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# -- Extension configuration -------------------------------------------------
autodoc_member_order = 'bysource'
