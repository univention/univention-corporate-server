.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
.. SPDX-License-Identifier: AGPL-3.0-only

.. _architecture-notation:

*********************
Architecture notation
*********************

A notation helps a lot to understand complex architectures and to explain the
software architecture of |UCS|. A standardized notation is key to communicate an
architecture.

This section describes the notation and elements used in this document. It's
intended to help you as reader to understand the notations. This section tries
to duplicate as little content as possible and instead provide deep links to the
corresponding resources on the internet.

.. _architecture-notation-c4-model:

C4 model
========

.. index::
   pair: architecture notation; c4 model

The document uses the C4 model in the :ref:`concepts` section.

   The C4 model is a lean graphical notation technique for modeling the
   architecture of software systems. It's based on a structural decomposition of
   a system into containers and components and relies on existing modeling
   techniques such as the Unified Modeling Language (UML) or Entity Relation
   Diagrams (ERD) for the more detailed decomposition of the architectural
   building blocks.

   — Wikipedia contributors, `"C4 model" <w-c4-model_>`_, Wikipedia, The Free Encyclopedia, (accessed January 24, 2023).

The C4 model is notation independent and provides:

#. A set of hierarchical abstractions for software systems, containers, components, and code.

#. A set of hierarchical diagrams for system context, containers, components, and code.

The C4 model is a good to learn, developer friendly approach to software
architecture diagramming. But, it comes to limits when it comes to model the
architecture. Diagramming tools draw just boxes and lines and can't answer
questions like "What dependencies does component X have?"

.. seealso::

   `The C4 model for visualizing software architecture <c4-model_>`_
      for a description of the C4 model from :cite:t:`c4-model`

.. _architecture-notation-archimate:

ArchiMate
=========

This document uses the *ArchiMate®* enterprise architecture modeling notation
in its architecture views.
For formal definitions,
see the `ArchiMate® specification 3.2 <archimate-3-2-spec_>`_.

*ArchiMate®* is a registered trademark of The Open Group.
The documentation and architecture views are independently created by Univention GmbH.
They don't imply certification, authorization, licensing, affiliation with,
or endorsement by The Open Group.

.. seealso::

   `Free ArchiMate 3.2 Overview PDFs in multiple languages <archimate-mastering-overviews_>`_
      for overview PDF files about ArchiMate 3.2 in different languages, such as
      English and German.

   `Mastering ArchiMate Edition 3.1 <archimate-mastering_>`_
      for a free PDF excerpt of the book from :cite:t:`mastering-archimate`

.. _architecture-notation-archimate-why:

Why ArchiMate?
--------------

   ArchiMate isn't about standard boxes and lines, it's all about a common
   language that provides the foundations for a good architecture description.

   Using the language without its notation is already of great value as it
   allows people to understand each other.

   — Jean-Baptiste Sarrodie, `"Why ArchiMate?" <archimate-why_>`_, 28. September 2018

For a general introduction to the notation,
see the `ArchiMate® specification 3.2 <archimate-3-2-spec_>`_.

.. seealso::

   `"ArchiMate", Wikipedia, The Free Encyclopedia <w-archimate_>`_
      for an overview of the ArchiMate frameworks, language, and viewpoints

.. _architecture-notation-archimate-layers-and-elements:

ArchiMate layers and elements
-----------------------------

For details about the notation used in this documentation,
see the following sections of the official specification:

Business layer
   * `ArchiMate business layer <archimate-business-layer_>`_
   * `Summary of Business Layer Elements <archimate-business-layer-summary_>`_.

Application layer
   * `ArchiMate application layer <archimate-application-layer_>`_
   * `Summary of Application Layer Elements <archimate-application-layer-summary_>`_.

Technology layer
   * `ArchiMate technology layer <archimate-technology-layer_>`_
   * `Summary of Technology Layer Elements <archimate-technology-layer-summary_>`_.

Motivation elements
   * `ArchiMate motivation elements <archimate-motivation-elements_>`_
   * `Summary of Motivation Elements <archimate-motivation-elements-summary_>`_.

Strategy elements
   * `ArchiMate strategy elements <archimate-strategy-elements_>`_
   * `Summary of Strategy Elements <archimate-strategy-elements-summary_>`_.

.. _notation-archimate-relationships:

Relationships
-------------

For details about relationships and derivation rules in the notation,
see the following sections of the official specification:

* `Summary of Relationships <archimate-relations-summary_>`_.

* `ArchiMate Relationships <archimate-relations_>`_.

* `Derivation of Relationships <archimate-relations-derivations_>`_.

* `ArchiMate Specification of Derivation Rules <archimate-derivation-rules_>`_.
