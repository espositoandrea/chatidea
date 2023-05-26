================================================================================
                              Overall Architecture
================================================================================

Although initially born as a monolithic system, CHATIDEA is now developed using
a micro-services architecture. The main advantages of this architecture is the
decoupling of the different components, allowing edits to any of them without
affecting the others (unless the interfaces are changed). CHATIDEA works using
three different components: a Natural Language Understanding (NLU) model, a
database, and a middleware that translates users' intents to SQL queries.

Although the middleware may be replaced by an AI model that automatically
translates natural language to SQL query (for example, using `OpenAI's
Codex`_), keeping the two steps separate allows to keep the code base
independent from a specific vendor. Note that OpenAI may still be used as the
NLU component.

.. _OpenAI's Codex: https://openai.com/blog/openai-codex

The micro-services architecture, where each micro-services is managed through a
Docker container, allows for a deployment architecture that makes use of
Kubernetes, managing multiple instances of the same component to balance load
and allow better overall availability to final users.

The following sections describe the three components of CHATIDEA and their
relationship with the system. Details on the interfaces that let the components
communicate are also given.

The Database
============

The database component is required for the correct functioning of CHATIDEA, as
CHATIDEA is a tool to generate chatbots for database exploration. However, the
system is fully independent from the actual database in use: provided the
correct configurations, the database is only used as the source of data to be
queried. Please refer to the :doc:`configuration documentation
<db-configuration>` for more details on how to configure the database.

The database communicates with the middleware using ODBC.

The NLU Model
=============

The Natural Language Understanding (NLU) model is used to parse users' requests
and understand the intents of the users, extracting the parameters required to
execute the action associated to the intent. Please refer to the :doc:`nlu
pipeline documentation <nlu-pipeline>` for more details on the NLU model
itself.

Currently, the model communicates with the middleware using SocketIO, however
future versions aim to use REST APIs.

The Middleware
==============

The Middleware orchestrates the various components. It receives requests (text)
from the users, passing them to the NLU component obtaining the intents and its
required parameters. Finally, it maps all available intents to a set of
operations on the database, and it executes them providing the output to the
user.

Currently, the Middleware is also responsible for the presentation of the
output to the users. However, in future versions we aim to decouple the
front-end from the actual middleware.
