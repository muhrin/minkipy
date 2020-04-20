.. minkipy documentation master file, created by
   sphinx-quickstart on Fri Mar 31 17:03:20 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _minkiPy: https://github.com/muhrin/minkipy
.. _object-relational mapper: https://en.wikipedia.org/wiki/Object-relational_mapping
.. _data mapper pattern: https://en.wikipedia.org/wiki/Data_mapper_pattern
.. _gui: https://github.com/muhrin/minkipy_gui/
.. _store: examples/quick-start.ipynb#Storing-objects
.. _find: examples/quick-start.ipynb#Finding-objects
.. _annotate: examples/quick-start.ipynb#Annotating-objects
.. _history: examples/quick-start.ipynb#Version-control
.. _RabbitMQ: https://www.rabbitmq.com/
.. _MongoDB: https://www.mongodb.com/


Welcome to minkiPy's documentation!
===================================

.. image:: https://codecov.io/gh/muhrin/minkipy/branch/develop/graph/badge.svg
    :target: https://codecov.io/gh/muhrin/minkipy
    :alt: Coveralls

.. image:: https://travis-ci.org/muhrin/minkipy.svg
    :target: https://travis-ci.org/muhrin/minkipy
    :alt: Travis CI

.. image:: https://img.shields.io/pypi/v/minkipy.svg
    :target: https://pypi.python.org/pypi/minkipy/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/wheel/minkipy.svg
    :target: https://pypi.python.org/pypi/minkipy/

.. image:: https://img.shields.io/pypi/pyversions/minkipy.svg
    :target: https://pypi.python.org/pypi/minkipy/

.. image:: https://img.shields.io/pypi/l/minkipy.svg
    :target: https://pypi.python.org/pypi/minkipy/


`minkiPy`_: a collaborative task submission engine.

MincePy is a lightweight but powerful task submission engine designed for running big-data and computational science
workflows in a collaborative environment.  All data is stored in a common `MongoDB`_ database and tasks are submitted
using the `RabbitMQ`_ message broker.

Features
++++++++

* Robust task submission, tasks automatically requeued if the worker dies.
* Tasks are python functions with arguments stored in the database.
* Optimistic locking.
* Python 3.5+ compatible.
* A responsive, Qt, `gui`_.


Installation
++++++++++++

Installation with pip:

.. code-block:: shell

    pip install minkipy


Installation from git:

.. code-block:: shell

    # via pip
    pip install https://github.com/muhrin/minkipy/archive/master.zip

    # manually
    git clone https://github.com/muhrin/minkipy.git
    cd minkipy
    python setup.py install


Next you'll need MongoDB, in Ubuntu it's as simple as:


.. code-block:: shell

    apt install mongodb

see `here <https://docs.mongodb.com/manual/administration/install-community/>`_, for other platforms.


Development
+++++++++++

Clone the project:

.. code-block:: shell

    git clone https://github.com/muhrin/minkipy.git
    cd minkipy


Create a new virtualenv for `minkiPy`_:

.. code-block:: shell

    virtualenv -p python3 minkipy

Install all requirements for `minkiPy`_:

.. code-block:: shell

    env/bin/pip install -e '.[dev]'

Table Of Contents
+++++++++++++++++

.. toctree::
   :glob:
   :maxdepth: 3

   apidoc


Versioning
++++++++++

This software follows `Semantic Versioning`_


.. _Semantic Versioning: http://semver.org/
