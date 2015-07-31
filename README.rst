courseraprogramming
===================

.. image:: https://travis-ci.org/coursera/courseraprogramming.svg
    :target: https://travis-ci.org/coursera/courseraprogramming

This command-line tool is a software development toolkit that helps to develop
asynchronous graders for Coursera (typically programming assignments).

To install this sdk, simply execute::

    sudo pip install courseraprogramming

`pip <https://pip.pypa.io/en/latest/index.html>`_ is a python package manager.
If you do not have ``pip`` installed on your machine, please follow the
installation instructions for your platform found at:
<https://pip.pypa.io/en/latest/installing.html#install-or-upgrade-pip>

The tool includes its own usage information and documentation. Simply run::

    courseraprogramming -h

Developing
----------

We recommend working on courseraprogramming within a python
`virtualenv https://pypi.python.org/pypi/virtualenv`_.
To get your environment set up properly, do the following::

    virtualenv venv
    source venv/bin/activate
    python setup.py develop
    pip install -r test_requirements.txt

Tests
^^^^^

To run tests, simply run: ``nosetests``, or ``tox``.

Code Style
^^^^^^^^^^

Code should conform to pep8 style requirements. To check, simply run::

    pep8 courseraprogramming tests

