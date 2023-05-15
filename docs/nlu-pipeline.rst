================================================================================
                                The NLU Pipeline
================================================================================

Executing the Pipeline
----------------------

Requirements
~~~~~~~~~~~~

Executing the Natural Language Understanding (NLU) Pipeline allows to
extract a Natural Language dataset from a database and a set of
configuration files, in order to train a NLU model. To execute the
pipeline, the following need to be installed in your machine (please
refer to the official documentations for instructions on how to install
them).

-  `Python 3.9 (with PIP) <https://www.python.org/downloads>`__
-  `Node.js (with NPM) <https://nodejs.org/>`__
-  `Pipenv <https://pipenv.pypa.io>`__

Before continuing, a database is needed. Be sure to have a DBMS running
on your system or on a remote server, and remember to set the
appropriate SQL dialect needed in the file
``chatidea/database/broker.py``.

Install all Python and Node.js dependencies in a virtual environment
using the following command:

.. code:: shell

   PIPENV_VENV_IN_PROJECT=1 pipenv install --dev
   npm i --dev

Then edit the ``.env`` file to fit your environment. If the ``.env``
file does not exist, copy the provided example template. This can be
done using the following command.

.. code:: shell

   cp .env.example .env

Running the Pipeline
~~~~~~~~~~~~~~~~~~~~

The NLU pipeline is fully contained in the directory ``nlu-model``, thus
be sure to change the directory using the following command before
executing the pipeline.

.. code:: shell

   cd nlu-model

Generate Data and Train the Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Natural Language Pipeline is fully tracked with
`DVC <https://dvc.org>`__. Most of the time, you can download the
pre-trained models and any intermediate file, avoiding the need of
retraining. To do this, you can simply run the command ``dvc pull``.
However, if you edit any file required by the NLU model, you change the
database, or you simply want to re-train the whole model, you can
re-execute the pipeline using the following command.

.. code:: shell

   dvc repro

If you want to share the built version of the model and any intermediate
files with collaborators, after a commit you can run ``dvc push`` to
push all the built files that have changed.
