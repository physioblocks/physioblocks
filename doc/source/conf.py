# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import shutil
import subprocess
import sys
import warnings
from pathlib import Path

from sphinx.application import Sphinx

import physioblocks
from physioblocks.launcher.constants import (
    LAUNCHER_SERIES_DIR_NAME,
    LAUNCHER_USER_ALIASES_DIR_NAME,
    LAUNCHER_USER_LIBRARY_DIR_NAME,
)

project = physioblocks.__name__
copyright = physioblocks.__copyright__
author = str(physioblocks.__authors__)
release = physioblocks.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration


extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinxcontrib.tikz",
]
autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "ignore-module-all": True,
}
autosummary_ignore_module_all = True

# Mappings for sphinx.ext.intersphinx. Projects have to have Sphinx-generated doc!
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}

tikz_latex_preamble = "\\usepackage[siunitx, RPvoltages]{circuitikz}"

add_module_names = False
pygments_style = "sphinx"
exclude_patterns = []
mathjax3_config = {"chtml": {"displayAlign": "center"}}

napoleon_custom_sections = [
    "Scheme",
    "Fluxes",
    "Discretization",
    "Internal Equations",
    "Saved Quantities",
    "Configuration",
    "Aliases",
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]


# NamedTuple fields are already documented in the "Attributes" section.
def _skip_namedtuple_fields(app, what, name, obj, skip, options):
    if (obj.__doc__ or "").startswith("Alias for field number"):
        return True
    return None


def _on_builder_inited(app: Sphinx):
    # Generate the example results if 'run-example' is set to true. Default is True
    if app.config.run_examples:
        _run_examples(app.srcdir, app.outdir)


def _run_examples(exec_dir: Path, out_dir: Path):
    # Initialize the launcher folder
    temp_launcher_folder = exec_dir / "_simulations"
    _initialize_launcher_folder(exec_dir, temp_launcher_folder)

    try:
        # Initialize example folder
        example_configurations_folder = exec_dir / "examples" / "configurations"
        example_configurations_folder.mkdir(exist_ok=True)

        example_library_folder = exec_dir / "examples" / "library"
        example_library_folder.mkdir(exist_ok=True)
        shutil.copytree(
            example_library_folder,
            temp_launcher_folder / LAUNCHER_USER_LIBRARY_DIR_NAME,
            dirs_exist_ok=True,
        )

        example_aliases_folder = exec_dir / "examples" / "aliases"
        example_aliases_folder.mkdir(exist_ok=True)
        shutil.copytree(
            example_aliases_folder,
            temp_launcher_folder / LAUNCHER_USER_ALIASES_DIR_NAME,
            dirs_exist_ok=True,
        )

        output_simulation_folder = out_dir

        # run example simulations
        _generate_simulation_results(
            exec_dir,
            example_configurations_folder,
            temp_launcher_folder,
            output_simulation_folder,
        )

    finally:
        shutil.rmtree(temp_launcher_folder)


def _initialize_launcher_folder(exec_dir: Path, path: Path):
    # Initialized a result folder
    exit_code = subprocess.call(
        [
            sys.executable,
            "-m",
            "physioblocks.launcher.configure",
            "-d",
            str(path),
        ],
        cwd=exec_dir,
    )
    if exit_code != 0:
        warnings.warn("Launcher configuration failed", stacklevel=2)


def _generate_simulation_results(
    exec_dir: Path,
    configurations_folder: Path,
    launcher_folder: Path,
    output_folder: Path,
):
    configurations = [
        file
        for file in configurations_folder.rglob("*")
        if file.suffix in {".json", ".jsonc"}
    ]
    for configuration in sorted(configurations):
        series_name = configuration.name.removesuffix(configuration.suffix)
        series_path = launcher_folder / LAUNCHER_SERIES_DIR_NAME / series_name

        # Run simulation
        exit_code = subprocess.call(
            [
                sys.executable,
                "-m",
                "physioblocks.launcher",
                str(configuration),
                "-d",
                str(launcher_folder),
                "-s",
                series_name,
            ],
            cwd=exec_dir,
        )
        if exit_code != 0:
            warnings.warn(
                f"Simulation for configuration at {configuration} failed",
                stacklevel=2,
            )

        # copy the html to the output folder
        rel_config = configuration.relative_to(configurations_folder)
        html_folder: Path = output_folder / rel_config.with_suffix("")
        html_folder.mkdir(exist_ok=True, parents=True)
        for file in series_path.rglob("*"):
            if file.suffix == ".html":
                shutil.copy(file, html_folder)


def setup(app: Sphinx):
    app.add_config_value(
        "run_examples",
        default=True,
        rebuild="html",
        types=(bool),
        description="Generate the simulations results for documentation examples.",
    )
    app.connect("autodoc-skip-member", _skip_namedtuple_fields)
    app.connect("builder-inited", _on_builder_inited)
