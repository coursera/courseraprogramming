courseraprogramming
===================

.. image:: https://travis-ci.org/coursera/courseraprogramming.svg
    :target: https://travis-ci.org/coursera/courseraprogramming

This command-line tool is a software development toolkit to help instructional
teams author asynchronous graders for Coursera (typically programming
assignments). Coursera's asynchronous grading environment is based upon
`docker <https://www.docker.com/>`_. While use of this tool is by no means
required to develop the docker container images, we believe it is helpful in the
endeavour. See below for brief descriptions of this tool's capabilities.

Installation
------------

To install this sdk, simply execute::

    sudo pip install courseraprogramming

`pip <https://pip.pypa.io/en/latest/index.html>`_ is a python package manager.
If you do not have ``pip`` installed on your machine, please follow the
installation instructions for your platform found at:
https://pip.pypa.io/en/latest/installing.html#install-or-upgrade-pip

The tool includes its own usage information and documentation. Simply run::

    courseraprogramming -h

or::

    courseraprogramming --help

for a complete list of features, flags, and documentation.

Note: the tool requires ``docker`` to already be installed on your machine.
Please see the docker
`installation instructions <http://docs.docker.com/index.html>`_ for further
information.

Subcommands
-----------

sanity
^^^^^^

Runs a number of sanity checks on your development environment and the
Dockerfile that builds your grader to help catch pitfalls early.

Examples:
 - ``courseraprogramming sanity`` checks the python and docker environment for
   successful basic operations.
 - ``courseraprogramming sanity --skip-environment -f ./Dockerfile`` skips the
   environment checks, but runs a number of checks against the Dockerfile to
   help users avoid authoring pitfalls.
 - ``courseraprogramming sanity --help`` displays usage for the sanity subcommand.

ls & cat
^^^^^^^^

These subcommands help you verify that a built docker container image actually
has what you expect inside of it. You can use these commands to poke at the
file system and verify that everything is where it should be.

Examples:
 - ``courseraprogramming ls $MY_CONTAINER_IMAGE /path/to/dir``
 - ``courseraprogramming cat $MY_CONTAINER_IMAGE /path/to/MyFile.sh``
 - ``courseraprogramming cat --help``

inspect
^^^^^^^

Allows for interactive inspection of your docker grading container image to help
debug grader issues. By default, it provides a shell that runs in a simulation
of the hardened sandbox environment.

Examples:
 - ``courseraprogramming inspect $MY_CONTAINER_IMAGE`` launches a basic shell within
   the container running as a deprivileged user, with memory constraints and the
   network configured similar to the production environment.
 - ``courseraprogramming inspect --super-user --unlimited-memory --allow-network
   $MY_CONTAINER_IMAGE`` launches a shell running as a root user with the
   production-simulating constraints removed.
 - ``courseraprogramming inspect -d /path/to/sample/submission $MY_CONTAINER_IMAGE``
   launches a container mapping the sample submission on the host into the
   grading container. If you interactively invoke the configured grading script
   and interactively debug your grader.
 - ``courseraprogramming inspect -h`` displays a list of all arguments and flags that can be
   passed to the ``inspect`` subcommand.

grade
^^^^^

This grade subcommand loosely replicates the production grading environment on
your local machine, including applying CPU and memory limits, running as the
correct user id, mounting the external file systems correctly, and relinquishing
the appropriate extra linux capabilities. Note that because the GrID system has
adopted a defense-in-depth or layered defensive posture, not all layers of the
production environment can be faithfully replicated locally.

The grade subcommand has 2 sub-sub-commands. ``local`` runs a local grader
container image on a sample submission found on the local file system. The
future ``remote`` sub-sub-command will run a local grader container image on a
sample submission downloaded from Coursera.org. This sub-sub-command is intended
to help instructional teams verify new versions of their graders correctly
handle problematic submissions.

Examples:
 - ``courseraprogramming grade local $MY_CONTAINER_IMAGE
   /path/to/sample/submission/``
   invokes the grader passing in the sample submission into the grader.
 - ``courseraprogramming grade local --help`` displays the full list of
   flags and options available.

upload
^^^^^^

Allows an instructional team to upload their containers to Coursera without
using a web browser. It is designed to even work in an unattended fashion (i.e.
from a jenkins job). In order to make the upload command work from a Jenkins
automated build machine, simply copy the `~/.coursera` directory from a working
machine, and install it in the jenkins home folder. Beware that the oauth2_cache
file within that directory contains a refresh token for the user who authorized
themselves. This refresh token should be treated as if it were a password and
not shared or otherwise disclosed!

To find the course id, item id, and part id, first go to the web authoring
interface for your programming assignment. There, the URL will be of the form:
``/:courseSlug/author/outline/programming/:itemId/``. The part id will be
displayed in the authoring user interface for each part. To convert the
``courseSlug`` into a ``courseId``, you can take advantage of our `Course API` putting in the appropriate ``courseSlug``. For example, given a
course slug of ``developer-iot``, you can query the course id by making the
request: ``https://api.coursera.org/api/onDemandCourses.v1?q=slug&slug=developer-iot``.
The response will be a JSON object containing an ``id`` field with the value:
``iRl53_BWEeW4_wr--Yv6Aw``.

This command can also be used to customize the resources that will be allocated
to your grader when it grades learner submissions. The CPU, memory limit and
timeout are all customizable.

 - ``--grader-cpu`` takes a value of 1 or 2, representing the number of cores
   the grader will have access to when grading. The default is 1.
 - ``--grader-memory-limit`` takes a value of 1024 or 2048, representing the
   amount of memory in MB the grader will have access to when grading. The
   default is 1024.
 - ``--grading-timeout`` takes a value between 300 and 1800, representing the
   amount of time the grader is allowed to run before it times out. Note this
   value is counted from the moment the grader starts execution and does not
   include the time it takes Coursera to schedule the grader. The default value
   is 1200.

Examples:
 - ``courseraprogramming upload $MY_CONTAINER_IMAGE $COURSE_ID $ITEM_ID
   $PART_ID`` uploads the specified grader container image to Coursera, begins
   and the post-upload processing, and associates the new grader with the
   specified item part in a new draft. Navigate to the course authoring UI to
   publish the draft to make it live.
 - ``courseraprogramming upload --help`` displays all available options
   for the :code:`upload` subcommand.

publish
^^^^^^^

Allows an instructional team to publish changes made to programming
assignments. Beware that *all* changes made to your assignment will be
published, not just grader changes.  Like ``upload``, it is designed to work in
an unattended fashion. Multiple items can be published at the same time using
the ``--additional-items`` flag. There are multiple different error conditions
that are represented by exit codes. An exit code of 1 represents a fatal error
while an exit code of 2 represents a retryable error.

Examples:
 - ``courseraprogramming publish $COURSE_ID $ITEM_ID`` publishes the item
   with item id $ITEM_ID in the course $COURSE_ID
 - ``courseraprogramming publish $COURSE_ID $ITEM_ID_1 --additional-items
   $ITEM_ID_2 $ITEM_ID_3`` publishes the items with ids $ITEM_ID_1, $ITEM_ID_2
   and $ITEM_ID_3 in the course $COURSE_ID

Bugs / Issues / Feature Requests
--------------------------------

Please us the github issue tracker to document any bugs or other issues you
encounter while using this tool.

Supported Platforms
^^^^^^^^^^^^^^^^^^^

Note: We do not have the bandwidth to officially support this tool on windows.
That said, patches to add / maintain windows support are welcome!

Developing / Contributing
-------------------------

We recommend developing ``courseraprogramming`` within a python
`virtualenv <https://pypi.python.org/pypi/virtualenv>`_.
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
