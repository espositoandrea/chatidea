# CHATIDEA's Documentation

This folder holds the documentation of the CHATIDEA framework.

## How to Build

The documentation is managed through [Sphinx](https://www.sphinx-doc.org/en/master/). Thus, you can build the documentation in various formats using Sphinx builders. For example, you can build a PDF using `make latexpdf` and an HTML version using `make html`.

Before building the documentation, ensure that all the documentation's requirements are installed. These are managed using Poetry, and can be installed using

```sh
poetry install --with docs
```
