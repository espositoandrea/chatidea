================================================================================
                                   Deploying
================================================================================

The project is configured to be deployed using containerization. More
precisely, one container for each micro-service is expected. Thus, this
repository holds configuration files for Docker, using Dockerfiles and
docker-compose (used to manage the communication between the micro-services).
To build the deployment containers, run the following:

.. code-block:: shell

   docker-compose build

To execute the chatbot, run the following command (remove the ``-d`` at the end
to avoid executing as a daemon).

.. code-block:: shell

   docker-compose up -d

To shut-down the services, you can either use ``C-c`` (if you are not running
in daemon mode) or you can run the following command:

.. code-block:: shell

   docker-compose down

Testing the Deployment on Apple Silicon and Other ARM Processors
================================================================

At the moment, the project is based on `Rasa <https://rasa.com>`_. Sadly, the
official Docker image of Rasa does not support the ARM architecture. As a
workaround, until an official version is released, an `unofficial image
<https://hub.docker.com/r/khalosa/rasa-aarch64>`_ can be downloaded from
`Docker Hub <https://hub.docker.com>`_. To use it, in the file
``nlu-model/Dockerfile`` replace the ``FROM`` image by changing ``rasa/rasa``
to ``khalosa/rasa-aarch64:3.5.2``. The following command does that
automatically.

.. NOTE::

   ``sed``'s inplace option ``-i`` is not used to ensure POSIX compatibility,
   as macOS system do not ship by default with the GNU version of ``sed``

.. code-block:: shell

   TEMP_FILE=$(mktemp) && \
       sed '1s;rasa/rasa;khalosa/rasa-aarch64:3.5.2;' nlu-model/Dockerfile > $TEMP_FILE && \
       mv $TEMP_FILE nlu-model/Dockerfile
