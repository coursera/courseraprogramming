courseraprogramming
===================

.. image:: https://travis-ci.org/coursera/courseraprogramming.svg
    :target: https://travis-ci.org/coursera/courseraprogramming

This command-line tool is a software development toolkit that helps to develop
asynchronous graders for Coursera (typically programming assignments).

To install this sdk, simply execute::

    sudo pip install courseraprogramming

The tool includes its own usage information. Simply run::

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

