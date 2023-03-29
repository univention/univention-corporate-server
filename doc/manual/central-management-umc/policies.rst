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

.. _central-policies:

Policies
========

*Policies* describe administrative settings which can practically be used on
more than one object. They facilitate the administration as they can be
connected to containers and then apply to all the objects in the container in
question and the objects in sub containers. The values are applied according to
the inheritance principle. For every object, the applied value is always that
which lies closest to the object in question.

If, for example, the same password expiry interval is to be defined for all
users of a location, then a special container can be created for these users.
After moving the user objects into the container, a password policy can be
linked to the container. This policy is valid for all user objects within the
container.

An exception to this rule is a value which was defined in a policy in the form
of *fixed attributes*. Such values cannot be overwritten by subordinate
policies.

The command line program :command:`univention-policy-result` can be used to show
in detail which policy applies to which directory service object.

Every policy applies to a certain type of UMC domain object, e.g., for users or
DHCP subnets.

.. _central-management-umc-create-policy:

Creating a policy
-----------------

Policies can be managed via the UMC module :guilabel:`Policies`. The operation
is the same as for the functions described in :ref:`central-user-interface`.

The attributes and properties of the policies are described in the corresponding
chapters, e.g. the DHCP policies in the network chapter.

The names of policies must not contain any umlauts.

*Referencing objects* provides a list of all containers or LDAP
objects for which this policy currently applies.

The expanded settings host some general policy options which are generally only
required in special cases.

LDAP filter
   A LDAP filter expression can be specified here, which an object must match
   for this policy to get applied.

Required object classes
   Here you can specify LDAP object classes that an object must possess for the
   policy to apply to this object. If, for example, a user policy is only
   relevant for Windows environments, the ``sambaSamAccount`` object class could
   be demanded here.

Excluded object classes
   Similar to the configuration of the required object classes, you can also
   list object classes here which should be excluded.

Fixed attributes
   Attributes can be selected here, the values of which may not be changed by
   subordinate policies.

Empty attributes
   Attributes can be selected here, which are to be set to empty in the policy,
   meaning they will be stored without containing a value. This can be useful
   for removing values inherited by an object from a superordinate policy. In
   subordinate policies, new values can be assigned to the attributes in
   question.

.. _central-policies-assign:

Applying policies
-----------------

Policies can be assigned in two ways:

* A policy can be assigned to the LDAP base or a container/OU. To do so, the
  :guilabel:`Policies` tab in the properties of the LDAP object must be opened
  in the navigation (see :ref:`central-navigation`).

* A *Policies* tab is shown in the UMC modules of LDAP directory
  objects for which there are policies available (e.g., for users). A particular
  policy for a user can be specified at this place.

The *Policies* configuration dialogue is functionally identical;
however, all policy types are offered when assigning policies to a LDAP
container, whilst only the policy types applicable for the object type in
question are offered when assigning policies to an LDAP object.

A policy can be assigned to the LDAP object or container under *Policies*. The
values resulting from this policy are displayed directly. The
*Inherited* setting means that the settings are adopted from a
superordinate policy again - when one exists.

If an object is linked to a policy, or inherits policy settings which cannot be
applied to the object, the settings remain without effect for the object. This
makes it possible, for example, to assign a policy to the base entry of the LDAP
directory, which is then valid for all the objects of the domain which can apply
this policy. Objects which cannot apply to this policy are not affected.

.. _central-management-umc-edit-policy:

Editing a policy
----------------

Policies can be edited and deleted in the UMC module :guilabel:`Policies`. The
interface is described in :ref:`central-user-interface`.

.. caution::

   When editing a policy, the settings for all the objects linked to this policy
   are changed! The values from the changed policy apply to objects already
   registered in the system and linked to the policy, in the same way as to
   objects added in the future.

The policy tab of the individual LDAP objects also includes the :guilabel:`edit`
option, which can be used to edit the policy currently applicable for this
object.
