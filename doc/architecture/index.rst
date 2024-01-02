.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _introduction:

************
Introduction
************

Welcome to the architecture documentation of |UCS|.

This document doesn't cover installation, the usage of UCS or parts of the
product. For instructions about how to install and use UCS, see
:cite:t:`ucs-manual`.

.. TODO Remove this sentence once the whole document is done.

The document is released step by step after each part is finished. The beginning
is at the first, high level.

Your feedback is welcome and highly appreciated. If you have comments, suggestions,
or criticism, please `send your feedback
<https://www.univention.com/feedback/?architecture=generic>`_ for document
improvement.

For feedback on single sections, use the feedback link next to the section
title.

Audience
========

This document is for consultants, administrators, solution architects, software
developers and system engineers. It describes the technical architecture of UCS
on three different detail levels.

The first, high level, :ref:`positions UCS in the known IT world
<positioning>` and describes the :ref:`concepts <concepts>`. This view helps
readers to understand the principles of UCS. Chapters 2 and 3 assume you are
familiar with information technology in general and that you have heard of
computer network building blocks and software.

.. TODO : Enable the references, once the sections are written:
   """covers the :ref:`product components <product-components>` and the :ref:`numerous
   services <services>` UCS offers to IT infrastructures. Software developers and"""

The second, medium level, is for administrators and solution architects. It
covers the product components and the numerous services UCS offers to IT
infrastructures. You read about the user facing product components and what
services UCS runs. You learn what open source software contributes to the
capability of UCS and how it interoperates together.

Software developers and system engineers get an overview of the technical parts.

A general understanding of Linux operating systems for servers and IT
administration are beneficial for understanding.

For notation, the document uses the *C4 model* notation and the *ArchiMate*
notation. For more information, refer to :ref:`architecture-notation`.

.. TODO : Enable the references, once the sections are written:
   """The third, low level is about the :ref:`libraries <libraries>`, :ref:`internal
   systems and storage <systems-storage>`. It describes the pieces a software"""

The third, low level is about the libraries, internal systems and storage. It
describes the pieces a software developer and system engineer needs to know to
contribute to UCS. General knowledge of software architecture and software
engineering are helpful at this level.

Learning objectives
===================

After reading this document you have a broad understanding of the UCS
architecture. It equips consultants, administrators, and solution architects to
better plan their IT environment with UCS. It enables software developers and
system engineers to get familiar with software development for UCS.

How to use the document
=======================

This document contains numerous figures. As far as possible, they use SVG
format. If you need a larger view of the image, open it in a dedicated tab in
your web browser:

.. tab:: Chromium based browsers

   To open the figure in the same tab:

   #. Click the figure.

   Alternatively, to open the figure in a new tab:

   #. Right click the figure.
   #. Click :guilabel:`Open Image in New Tab` from the context menu.

.. tab:: Mozilla Firefox

   To open the figure in a new tab:

   #. Right click the figure.
   #. Click :guilabel:`Open Image in New Tab` from the context menu.
