========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |github-actions| |requires|
        | |codecov|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|
.. |docs| image:: https://readthedocs.org/projects/freesurfer_analyses/badge/?style=flat
    :target: https://freesurfer_analyses.readthedocs.io/
    :alt: Documentation Status

.. |github-actions| image:: https://github.com/GalBenZvi/freesurfer_analyses/actions/workflows/github-actions.yml/badge.svg
    :alt: GitHub Actions Build Status
    :target: https://github.com/GalBenZvi/freesurfer_analyses/actions

.. |requires| image:: https://requires.io/github/GalBenZvi/freesurfer_analyses/requirements.svg?branch=main
    :alt: Requirements Status
    :target: https://requires.io/github/GalBenZvi/freesurfer_analyses/requirements/?branch=main

.. |codecov| image:: https://codecov.io/gh/GalBenZvi/freesurfer_analyses/branch/main/graphs/badge.svg?branch=main
    :alt: Coverage Status
    :target: https://codecov.io/github/GalBenZvi/freesurfer_analyses

.. |version| image:: https://img.shields.io/pypi/v/freesurfer-analyses.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/freesurfer-analyses

.. |wheel| image:: https://img.shields.io/pypi/wheel/freesurfer-analyses.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/freesurfer-analyses

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/freesurfer-analyses.svg
    :alt: Supported versions
    :target: https://pypi.org/project/freesurfer-analyses

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/freesurfer-analyses.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/freesurfer-analyses

.. |commits-since| image:: https://img.shields.io/github/commits-since/GalBenZvi/freesurfer_analyses/v0.0.0.svg
    :alt: Commits since latest release
    :target: https://github.com/GalBenZvi/freesurfer_analyses/compare/v0.0.0...main



.. end-badges

A package to post-process freesurfer's 'reconall' derivatives

* Free software: Apache Software License 2.0

Installation
============

::

    pip install freesurfer-analyses

You can also install the in-development version with::

    pip install https://github.com/GalBenZvi/freesurfer_analyses/archive/main.zip


Documentation
=============


https://freesurfer_analyses.readthedocs.io/


Development
===========

To run all the tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
