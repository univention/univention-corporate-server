.. Like what you see? Join us!
.. https://www.univention.com/about-us/careers/vacancies/
..
.. Copyright (C) 2021-2023 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only
..
.. https://www.univention.com/
..
.. All rights reserved.
..
.. The source code of this program is made available under the terms of
.. the GNU Affero General Public License v3.0 only (AGPL-3.0-only) as
.. published by the Free Software Foundation.
..
.. Binary versions of this program provided by Univention to you as
.. well as other copyrighted, protected or trademarked materials like
.. Logos, graphics, fonts, specific documentations and configurations,
.. cryptographic keys etc. are subject to a license agreement between
.. you and Univention and not subject to the AGPL-3.0-only.
..
.. In the case you use this program under the terms of the AGPL-3.0-only,
.. the program is provided in the hope that it will be useful, but
.. WITHOUT ANY WARRANTY; without even the implied warranty of
.. MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
.. Affero General Public License for more details.
..
.. You should have received a copy of the GNU Affero General Public
.. License with the Debian GNU/Linux or Univention distribution in file
.. /usr/share/common-licenses/AGPL-3; if not, see
.. <https://www.gnu.org/licenses/agpl-3.0.txt>.

.. _users-templates:

User templates
==============

A user template can be used to preset settings when creating a user. If at least
one user template is defined, it can be selected when creating a user.

.. _user-create-template:

.. figure:: /images/users_usertemplate.*
   :alt: Selecting a user template

   Selecting a user template

User templates are administrated in the UMC module :guilabel:`LDAP directory`.
There one needs to switch to the ``univention`` container and then to the
``templates`` subcontainer. A new user template can be created here via the
:guilabel:`Add` with the object type ``Settings: User template``.

In a user template, either a fixed value can be specified (e.g., for the
address) or an attribute of the user management referenced. Attributes are then
referenced in chevrons.

A list of possible attributes can be displayed with the following command in the
section *users/user variables* of the output:

.. code-block:: console

   $ univention-director-manager users/user

If a user template is used for adding a user, this template will overwrite all
the fields with the preset values of the template. In doing so, an empty field
is set to ``""``.

It is also possible to only use partial values of attributes or convert values
in uppercase/lowercase.

For example, the UNIX home directory can be stored under
:file:`/home/<title>.<lastname>` or the primary email address can be predefined
with ``<firstname>.<lastname>@company.com``. Substitutions are generally
possibly for any value, but there is no syntax or semantics check. So, if no
first name is specified when creating a user, the above e-mail address would
begin with a dot and would thus be invalid according to the e-mail standard.
Similar sources of error can also occur when handling file paths etc.
Non-resolvable attributes (for instance due to typing errors in the template)
are deleted.

If only a single character of an attribute is required instead of the complete
attribute value, the index of the required character can be entered in the user
template in square parentheses after the name of the attribute. The count of
characters of the attribute begins with ``0``, so that index ``1`` corresponds
to the second character of the attribute value. Accordingly,
``<firstname>[0].<lastname>@company.com`` means an e-mail address will consist
of the first letter of the first name plus the last name.

A sub string of the attribute value can be defined by entering a range in square
parentheses. In doing so, the index of the first required character and the
index of the last required character plus one are to be entered. For example,
the input ``<firstname>[2:5]`` returns the third to fifth character of the first
name.

Adding ``:lower`` or ``:upper`` to the attribute name converts the attribute
value to lowercase or uppercase, e.g., ``<firstname:lower>``. If a modifier like
``:lower`` is appended to the entire field, the complete value is transformed,
e.g. ``<lastname>@company.com<:lower>``.

The option ``:umlauts`` can be used to convert special characters such as *è*,
*ä* or *ß* into the corresponding ASCII characters.

The option ``:alphanum`` can be used to remove all non alphanumeric characters
such as ````` (backtick) or ``#`` (hash). A whitelist of characters that are
ignored by this option can be defined in the UCR variable
:envvar:`directory/manager/templates/alphanum/whitelist`. If this option is
applied to an entire field, even manually placed symbols like the ``@`` in an
email address are removed. To avoid that, this option should be applied to
specific attributes only or needed symbols should be entered into the
whitelist.

The options ``:strip`` or ``:trim`` remove all white space characters from the
start and end of the string.

It is also possible to combine options, e.g: ``:umlauts,upper``.
