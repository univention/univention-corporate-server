.. _domain-admindiary:

Protocol of activities in the domain
====================================

The *Admin Diary* app provides the facility to log important events happening in
the domain. This includes among others:

* Creation, move, modification and deletion of users and other objects using
  |UCSUDM|

* Installation, update and deinstallation of apps

* Server password changes

* Start, end and eventual failures of domain joins

* Start and end of UCS updates

.. _domain-ldap-adminndiary-list:

.. figure:: /images/admindiary-list.*
   :alt: View of events in Admin Diary

   View of events in Admin Diary

:numref:`domain-ldap-adminndiary-list` shows, how events are shown in the UMC
module :guilabel:`Admin Diary`. By default the displayed entries are grouped by
week and can additionally be filtered through the search field. Selecting an
entry from the list opens a dialog showing additional details about the who and
when of the event, as shown in :numref:`domain-ldap-adminndiary-detail`.
Moreover there is the possibility to comment each event.

.. _domain-ldap-adminndiary-detail:

.. figure:: /images/admindiary-detail.*
   :alt: Detail view in Admin Diary

   Detail view in Admin Diary

The app consists of two components:

Admin Diary backend
   The backend must be installed on one system in the domain before the frontend
   can be installed. It includes a customization for :program:`rsyslog` and
   writes into a central database, which defaults to PostgreSQL. If MariaDB or
   MySQL is already installed on the target system, it will be used instead of
   PostgreSQL.

Admin Diary frontend
   Likewise the frontend must be installed at least once, but more installations
   are also possible. The frontend includes the UMC module :guilabel:`Admin
   Diary`, which is used to show and comment the entries. When installing it on
   a different host than where the backend is installed, access to the central
   database needs to be configured manually. The required steps for this are
   described in `Admin Diary - How to separate Frontend and Backend
   <https://help.univention.com/t/admin-diary-how-to-seperate-frontend-and-backend/11331>`_.
