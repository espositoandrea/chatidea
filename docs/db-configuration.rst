================================================================================
                          Database Configuration Files
================================================================================

The CHATIDEA framework currently uses three different configuration files to
connect to a database. Note that the task of collapsing the three configuration
files into a single simpler file is in the backlog of the project: please refer
to the right version of the framework to get an accurate documentation of the
state of the configuration schema.

The three files are responsible for: defining the database schema and all the
relationships among entities; defining the basic concepts with which users will
interact; defining how the concepts should be presented and viewed by the
users. The path of the three files must be made available through a ``.env``
file.

The following are the configuration schemas for each of the three files
(respectively). Note that if CHATIDEA recognizes an error in the configuration,
it will prevent you from running the framework to avoid non-deterministic
behaviors.

.. Defining the Database Schema
.. ============================

.. jsonschema:: extras/schemas/schema.schema.json
   :auto_target: false
   :auto_reference: false
   :lift_definitions: false
   :lift_description: true

.. Defining the Concepts Managed by the Chatbot
.. ============================================

.. jsonschema:: extras/schemas/concept.schema.json
   :auto_target: false
   :auto_reference: false
   :lift_definitions: false
   :lift_description: true

.. Defining What Fields Are Shown and How
.. ======================================

.. jsonschema:: extras/schemas/view.schema.json
   :auto_target: false
   :auto_reference: false
   :lift_definitions: false
   :lift_description: true

