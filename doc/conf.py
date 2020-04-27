# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------

project = "Smorest CRUD"
author = "JetBridge Inc."

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
# extensions = []
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "recommonmark",
    "sphinxcontrib.apidoc",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "source/smorest_crud.test*"]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

apidoc_excluded_paths = ["test"]
apidoc_module_dir = "../smorest_crud"
apidoc_output_dir = "source"
apidoc_separate_modules = True
# set_type_checking_flag = True


# -- Automatically run sphinx-apidoc --------------------------------------


def run_apidoc(_):
    from sphinx import apidoc

    docs_path = os.path.dirname(__file__)
    apidoc_path = os.path.join(docs_path, "source")
    module_path = os.path.join(docs_path, "..", "smorest_crud")

    apidoc.main(
        [
            "--force",
            "--module-first",
            "--separate",
            "-d",
            "3",
            "-o",
            apidoc_path,
            module_path,
        ]
    )


# def setup(app):
#     app.connect("builder-inited", run_apidoc)
