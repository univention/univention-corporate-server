.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _services-udm-rest-api:

UDM HTTP REST API
=================

This section describes the technical architecture for the *UDM HTTP REST API*, a
JSON HTTP interface to interact with *Univention Directory Manager*. It follows
a *RESTful* architecture, adheres to *REST* principles and provides an *OpenAPI*
schema.

For a general overview about |UDM|, see :ref:`component-management-system` and
:ref:`services-udm`.

For information about how to use the API as a developer,
see :ref:`uv-dev-ref:udm-rest-api` in :cite:t:`developer-reference`.

You find the source code for *UDM HTTP REST API* at
:uv:src:`management/univention-directory-manager-rest/`.

.. tip::

   This section uses various concepts of the
   :ref:`architecture-notation-archimate` notation. To avoid confusion, have a
   close look at the figures and make yourself familiar with the different
   concepts in the :ref:`notation-archimate-application-layer` and the
   :ref:`notation-archimate-relationships` in the appendix.

:numref:`services-udm-http-rest-api-context` shows the relation of *UDM HTTP
REST API* down the line from the |UCS| *Product components* with the
:ref:`component-management-system`, and its :ref:`component-domain-management`
implemented by *Univention Directory Manager (UDM)*.

.. _services-udm-http-rest-api-context:

.. figure:: /images/udm-rest-api-context.*
   :width: 200px

   *UDM HTTP REST API* as part of |UDM| in the domain management

The *Univention Corporate Server* application component has *Product components*
services assigned to it. *Product components* are an abstract container for the
main product building blocks, see :ref:`product-components`. *Product
components* consist of the *UCS Management system* and other application
services. *UCS Management System* application service consists of the *Domain
Management* application service and others. *Univention Directory Manager (UDM)*
application service serves the application services *Domain management* and *UDM
HTTP REST API*.

.. hint::

   :numref:`services-udm-http-rest-api-context` isn't a layer diagram, because
   it uses composition and aggregation relations between the different concepts.

.. _services-udm-rest-api-architecture:

Architecture
------------

:numref:`services-udm-http-rest-api-overview` provides an overview of the
architecture of *UDM HTTP REST API*.

.. _services-udm-http-rest-api-nested:

.. figure:: /images/udm-rest-api-nested.*
   :width: 700px

   UDM HTTP REST API overview in a nested view

.. index::
   pair: tornado; udm http rest api
   pair: reverse proxy; udm http rest api

The main building blocks are the following concepts:

*UDM REST API* application component
   The central part of the *UDM HTTP REST API* is the application component that
   contains the respective application services for communication with the
   outside world, the server, and the gateway.

   The package :program:`univention-directory-manager-rest` provides this
   application component and all the pieces outlined later.

*UDM HTTP REST API* application service
   The application service that the *UDM HTTP REST API* explicitly exposes. It's
   an abstraction of the other application processes that realize it.

*Gateway for UDM HTTP REST API* application process
   *UDM HTTP REST API* launches one *Gateway* process. It forwards each request
   from the *Reverse Proxy* to the appropriate *Server for UDM REST API* process
   with the required locale.

*Server for UDM HTTP REST API* application process
   *Server for UDM HTTP REST API* is a dedicated server process for each
   configured natural language. It serves the content accordingly.

*Reverse proxy* application service
   The *Reverse proxy* functions as gateway. It adds HTTP security headers and
   forwards HTTP requests to the *Gateway for UDM HTTP REST API* service. It
   also handles errors in case the *Server for UDM HTTP REST API* is
   unreachable. It's part of the web server on |UCS|.

*HTTP JSON interface* application interface
   *UDM HTTP REST API* can answer requests in the ``HAL+JSON`` format.

   Hypertext Application Language (HAL) provides hypermedia controls to navigate
   the API efficiently and independently.

*openapi.json*
   The *openapi.json* describes the *HTTP JSON interface* in the OpenAPI schema
   following the OpenAPI specification. The JSON file allows to auto-generate
   RPC clients.

.. _services-udm-rest-api-technology:

Technology
----------

:numref:`services-udm-http-rest-api-overview` shows the architecture in a
non-nested view with some more concepts around the reverse proxy. It also adds
the technology layer with :term:`Tornado`, :term:`Apache HTTP server` and
:term:`Apache module mod_proxy`.

*Tornado* implements the server and the gateway application process for the *UDM
HTTP REST API*. As other services also use *Apache HTTP server*, so does the
*UDM HTTP REST API*.

.. _services-udm-http-rest-api-overview:

.. figure:: /images/udm-rest-api-overview.*

   UDM HTTP REST API and its relation to the web server

You can see in :numref:`services-udm-http-rest-api-overview`, that the *UDM HTTP
REST API* application services is an abstraction for the application processes
*Gateway for UDM HTTP REST API* and *Server for UDM HTTP REST API*. All three
concepts are assigned to the *UDM REST API* application component.

.. _services-udm-rest-api-flow:

Request flow
------------

:numref:`services-umd-http-rest-api-flow` shows the abstract flow of a request
through the different concepts to the data store in the domain database *LDAP
directory*. The flow emphasizes the dependency of the UDM REST API to |UDM|. For
more information about the UDM architecture and how *UDM Python library* relates
to it, see :ref:`services-udm-architecture`.

.. _services-umd-http-rest-api-flow:

.. figure:: /images/udm-rest-api-flow.*
   :width: 450px

   Request flow for *UDM HTTP REST API*

.. _services-udm-rest-api-capability:

Capabilities
------------

*UDM HTTP REST API* provides capabilities as shown in
:numref:`services-umd-http-rest-api-capability`. Different concepts of the *UDM
REST API* realize different capabilities, so that all of them serve a dedicated
purpose.

.. _services-umd-http-rest-api-capability:

.. figure:: /images/udm-rest-api-capabilities.*
   :width: 600px

   UDM HTTP REST API capabilities

.. hint::

   A capability in :ref:`ArchiMate <notation-archimate-motivation-layer>`
   represents an ability that an active structure element possesses.

   In the :numref:`services-umd-http-rest-api-capability`, you see different
   relations such as realization, aggregation, and assignment. Be aware of their
   different meaning.

OpenAPI schema
   The *OpenAPI schema* provides the definition of the *UDM HTTP REST API* in a
   programming language agnostic manner. It uses the OpenAPI specification and
   helps to transfer the knowledge about the API from the API provider to the
   API consumer.

RESTful architecture
   For more information, see :ref:`services-udm-rest-api-restful`.

Multi-Language support
   The :ref:`component-management-system` supports multiple languages, such as
   English and German. *UDM HTTP REST API* belongs to the UCS management system
   and therefore supports the same set of languages. Language support is
   important for *UDM HTTP REST API* to provide localized messages to the client
   and the user.

.. seealso::

   `What is OpenAPI? <open-api-what-is-it_>`_
      for more information about OpenAPI and the specification.


.. _services-udm-rest-api-restful:

RESTful architecture
--------------------

The *UDM HTTP REST API* adheres to the *RESTful* architecture as defined in
:cite:t:`fielding-rest`. The term *REST* stands for **Re**\ presentation **S**\
:spelling:ignore:`tate` **T**\ :spelling:ignore:`ransfer` and includes six
architectural and four interface constraints that make a service *RESTful*.

.. seealso::

   :uv:src:`UDM HTTP API </management/univention-directory-manager-rest/README.md>`
      for a detailed description about the RESTful architecture, the rationale
      of the constraints, compliance and compliance violations, and the OpenAPI
      interface.

.. _restful-architecture-constraints:

Architectural constraints
~~~~~~~~~~~~~~~~~~~~~~~~~

The six architectural constraints are the following

#. Client-server

   The *client-server constraint* enforces a clear separation between a passive
   server component and an active client component. The server component has the
   authority over the entire service realm and its meaning. The client
   component must not make any assumptions about the server logic.

   The client-server constraint allows clients and servers to evolve
   independently, because it supports separation of concerns and reduces
   interdependencies. Clients focus on the user interface and hypermedia.
   Servers focus on business logic and the representation of resources.

#. Stateless

   The *stateless constraint* enforces a stateless communication between clients
   and servers. This means that each request must contain all the information
   necessary for the server to fully understand and process the request. The
   client is responsible for handling all session state. This separation allows
   scalability by adding server instances or processes, since each server can
   handle requests independently.

   Stateless communication simplifies the server implementation and enables
   service scalability.

#. Cache

   The *cache constraint* forces data in a response to be either explicitly or
   implicitly enabled for caching. Caching improves performance by reducing the
   need for repeated requests to the server.

#. Uniform interface

   The *uniform interface constraint* requires that components communicate using
   generic and standardized data formats that all participating components
   understand. The interface must satisfy the interface constraints described
   later.

   The server must provide the same unified interface that satisfies the data
   manipulation constraint of all server data. Clients, servers, or other
   intermediaries can work seamlessly with the API using the same standardized
   interface. The API doesn't require application-specific data formats or
   schemas.

   The standardized data format JSON focuses on structure and representation of
   data. The lacks of mechanisms for semantic and hypermedia interaction make
   JSON unsuitable as uniform interface.

#. Layered system

   The *layered system constraint* extends the client-server constraint by
   introducing intermediate components that have the ability to fully understand
   and manipulate messages. The intermediate components use the principles of
   *stateless* and *self-describing messages* to extend the architecture.
   Crucially, each layer operates behind a unified interface that hides layer
   specifics from clients and components. This layer opacity gives the system a
   remarkable degree of flexibility and adaptability.

#. Code-on-demand (optional)

   The *code-on-demand constraint* gives servers the optional ability to extend
   client functionality by embedding code in representations. This optional
   constraint comes with the trade-off of potentially limiting availability to
   clients capable of running the embedded code.

.. _restful-interface-constraints:

Interface constraints
~~~~~~~~~~~~~~~~~~~~~

The four interface constraints are the following:

#. Identification of resources

   The *identification of resources constraint* means that the server abstracts
   all information as a resource. Each resource must have one or more names or
   identifiers, typically represented by a unique HTTP URI. The server manages
   the URIs and has the authority to assign them. URIs serve as straightforward
   identifiers and don't carry any additional semantic information.

   Clients access resources using resource identifiers only. Clients should
   refrain from manually constructing URIs unless the server provides URI
   templates. Clients navigate through state transitions using links found
   within retrieved representations, allowing them to follow hypermedia links
   and traverse the API without hardcoded URIs. The server can change URIs
   without disrupting clients.

#. Manipulation of resources through representations

   A resource represents a set of entities that the API reflects through
   representations or identifies through URIs when a concrete realization of the
   concept doesn't yet exist. This fundamental principle implies that the state
   and representation of a resource can change dynamically over time while
   remaining the same resource.

   It's important to understand that a representation of a resource isn't the
   resource itself. The API represents a resource in various formats, such as
   HTML, XML, JSON, LDIF representing it's current state, key-value pairs
   representing the wanted state, images, or even error conditions such as ``404
   Not Found``. In REST, the client achieves state changes by examining the
   response and the ways the response provides to modify the representation.
   This involves selecting a transformation, creating, or modifying a
   representation, and sending it back to the server.

#. Self-descriptive messages

   The *self-descriptive message constraint* ensures that the API transmits
   messages as representations consisting of resource or request data metadata
   and control data.

   The MIME media type of the request data plays a critical role in
   specifying both the syntax and semantics of message payloads.

   Metadata, presented in the form of key-value pairs, describes how to
   interpret the message, defines caching rules, provides authentication
   information, specifies encodings, languages of representation, and more.

   Control data, a form of metadata, describes metadata, and enables various
   capability.

#. Hypermedia as the Engine of Application State

   The *hypermedia as the engine of application state (HATEOAS) constraint*
   means that representations must not only convey data, but also contain
   information to control the state of the application. Each response should
   include all available state transfer capabilities, such as HTML forms, state
   changes links, URI templates, or other relevant resources.

   Hypermedia refers to data formats that can include hyperlinks and other
   hypermedia elements. Specifications such as *JSON-LD*, *UBER*, *SIREN*, *HAL*,
   *Collection+JSON*, and *Hydra* extend JSON to include hypermedia elements.

   HATEOAS has the following requirements:

   * The client must know the media type and it must be rich enough to describe
     all possible client-server interactions.

   * The client should only follow links contained in the representation, and
     shouldn't construct identifiers without user interaction.

.. _services-udm-rest-api-dependencies:

Dependencies
------------

You can resolve the other detailed dependencies with the package manager. *UDM
HTTP REST API* depends on the following elements:

* :ref:`services-udm`
* :ref:`services-umc` for providing the components for the caching of LDAP
  connections

* UDM-UMC module, a dedicated :ref:`UMC module <services-umc-modules>` that
  provides the common abstraction of UDM modules.

  .. FIXME : Probably refers to *UDM in UMC* from :ref:`services-udm-architecture`.

* :term:`Tornado`

The following :ref:`server roles <concept-role>` need *UDM HTTP REST API*:

* UCS Primary Directory Node
* UCS Backup Directory Node
