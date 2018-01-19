HTTP Interface for UDM in REST architectural style
==================================================

# Summary of REST constraints:

1. Client - Server components
2. Stateless communication i.e. authentication, languages
3. implicit or explicit marking of the representations as (non-)cacheable (implicit if the protocol semantic defines, something is not cacheable (e.g. responses of PUT requests) i.e. Last-Modified, E-Tag, If-Unmodified-Since, If-Modified-Since, Vary, ...
4. Uniform interface
	1. identification of resources: every "concept" (type of information) gets a unique URI, the data/realization of the concept is not the ressource but only a part of a representation of the resource
	2. manipulation of resources via representations: retrieval and modification of ressources are done by performing actions on resources by exchanging representations of the current or intended state (or representation of error conditions) including metadata which are describing the ressource, representation, communication -- all in a standardized media format (i.e. mime type).
	3. self describing messages - every message describes itself via standardized representations, metadata, control data so that the semantic can be understood by every intermediary component
	4. hypermedia as the engine of application state - all state transitions must come from the content of the retrieval of a representation. there are no static types, URI's. An client has only the knowledge of one URI. the semantic is defined by the links, link relations, forms in the representations which are using an hypermedia format (i.e. text/html) (not even schematized JSON!).
5. Layered System (every intermediary component (proxy, gateway) understands the semantic of every message)
6. Code on Demand: client functionality can be extended e.g. ajax support via javascript, usabiltiy, layout, design, style, performance enhancements (but not application logic!) and maybe partly support for JSON

# Conception of the Data Format
REST requires self descriptive messages in a standardized media format i.e. representation format (text/html) and representation metadata (HTTP header) and REST requires that hypermedia is the engine of application state.
The following considerations are taken into mind when we create an API for automated processing.

The API is NOT driven by fixed URI path's and fixed parameters but taken from the data format.
A client has no logic about the application, only about generic standardized response formats such as link relations, HTTP headers, methods, HTML or XML elements, javascript Code-On-Demand for the layout/design/usability and JSON.
https://www.iana.org/assignments/link-relations/link-relations.xhtml
collection, create-form, edit, edit-form, edit-media, icon, help, first, start, next, prev/previous, item, index, last, preload, (related), search, self, section, type, up, 

Our client should be able to solve our specific use cases while gaining the advantages of the REST architectural style.

Our client therefore knows how to render a formular for specific actions and what our specific link relations are/mean.

Versioning of the API happens via new "rel" types, not by adding a /api/v2/ into the URI!
By evaluating the user-agent of the client we can encapsulate legacy parts of the service or if really necessary provide a legacy interface.

If we follow these constraints we are able to create a CLI client, use our regular UMC web interface to use this service and provide a scalable and stable API for e.g. customer extensions.
We can also use the API to automatically upload the license file, when we receive a license request.

# Use cases:

## getModules()

List all existing modules (e.g. users, computers, groups, shares, printers, mail, nagios, dhcp, dns, networks, policy, ldap directory tree, upload-license) and their possible actions (create, search) for the current user.

Without a search it is not possible to modify, move or remove an object because only the server knows the semantics and the identifiers of these actions. Otherwise out-of-bands-information-is-driving-interaction-instead-of-hypermedia.

→ list with every module-name: `{ links: create, search}` and `license`: `<link rel="udm/license-information"> <link rel="udm/license-upload"> <link rel="udm/license-request"/>`

## createObjectForm(module)

Get a form with all possible choices (specific object-type (e.g. users/user), container, (template), checkbox-if-you-want-a-wizard)

→ form method=POST enctype=application/www-form-urlencoded (or javascript overwriteability for JSON)

## createObject(module, object\_type, container, template, want\_wizard):

Get a form with all possible input values for a specific object type

→ form method=POST, enctype=multipart/form-data (if uploads are necessary, e.g. userPhoto) else application/x-www-form-urlencoded with a javascript overwritten JSON possibility
  `<input>` for every property (or selected properties if want\_wizard), containing information how to retrieve possible values, containing information about the data-type/syntax, requirements

## searchObjectForm(module)

Get a form for searching for objects of the given module: possible selections are: (object-type, container, property-or-dn, search-value, checkbox-include-hidden-object, checkbox-do-not-substring-search, wanted-properties, wanted-results)

→ form (with javascript instructions)

## searchObject(module, object\_type, container, property\_name (or default: "dn"), search\_value, include\_hidden, do\_substring, wanted\_properties=None, wanted\_results)

Return a list of objects, limited to number of wanted-results, including the wanted properties (or a default selection = the "name"/identify-property with their possible actions (modify, move, remove)

→ `<input name="" value="">` for each wanted property, `<form action="URI" method="DELETE" enctype="">`, `<link rel="edit-form">` (for both, edit&move) `<link rel="/udm/report">`

_TODO_: we need to return a form for all values with a checkbox, for the report selection. But a form inside a form (e.g. the DELETE form) is not possible in HTML?!

`<form method=POST enctype=application/x-www-form-urlencoded>` ... `<input>` for report-type `<input type="submit">` for report creation

_TODO_: multi-edit

## openObject(identifier = URI mit dem DN)

Erhalten der Werte eines Objekts (z.B. in einem JSON Format)

## modifyObject(module, object\_type, dn)

Get a form for editing an object

→ `<form method=POST enctype=multipart/x-www-form-urlencoded>` (if uploads are necessary, e.g. userPhoto) else application/x-www-form-urlencoded with a javascript overwritten JSON possibility
  `<input type=position>` for moving the object
  `<input>` for every property, containing information how to retrieve possible values, containig information about the data-type/syntax, requireness, editable
  Javascript Code-On-Demand way to set If-Unmodified-Since/If-None-Match and a flag, to ignore server side inbetween modifications

## deleteObject(module, object\_type, dn)

Removes the object and returns a success/error message

## uploadLicense(license\_ldif)
Installs a ucs license by showing a file upload dialog and a textare field for inserting the license directly.

→ `<form method="POST" enctype="application/x-www-form-urlencoded"><textarea type="text" name="license" required/></form>`

→ `<form method="POST" enctype="multipart/form-data"><input type="file" name="license" required/></form>`

## requestLicense(email)

Renders a form which can be used to request a new license from univention

`<form method=POST enctype=application/x-www-form-urlencoded><input name="email" required>`

## getLicenseInformation()

Render a HTML site containing information about the license
