# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import physioblocks

project = physioblocks.__name__
copyright = physioblocks.__copyright__
author = str(physioblocks.__authors__)
release = physioblocks.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration


extensions = [
    "sphinx.ext.autodoc",
    "sphinxcontrib.tikz",
    "sphinx_rtd_theme",
]

# Mappings for sphinx.ext.intersphinx. Projects have to have Sphinx-generated doc!
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "numpy": ("https://numpy.org/doc/", None),
}

tikz_latex_preamble = "\\usepackage[siunitx, RPvoltages]{circuitikz}"

add_module_names = False
pygments_style = "sphinx"
templates_path = ["_templates"]
exclude_patterns = []
mathjax3_config = {"chtml": {"displayAlign": "left"}}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]


# autodoc options
autodoc_type_aliases = {
    "SystemFunction": "SystemFunction",
    "NDArray": "NDArray",
    "Iterable": "Iterable",
}
autodoc_member_order = "bysource"
