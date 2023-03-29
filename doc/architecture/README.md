<!--
Like what you see? Join us!
https://www.univention.com/about-us/careers/vacancies/

Copyright (C) 2021-2023 Univention GmbH

SPDX-License-Identifier: AGPL-3.0-only

https://www.univention.com/

All rights reserved.

The source code of this program is made available under the terms of
the GNU Affero General Public License v3.0 only (AGPL-3.0-only) as
published by the Free Software Foundation.

Binary versions of this program provided by Univention to you as
well as other copyrighted, protected or trademarked materials like
Logos, graphics, fonts, specific documentations and configurations,
cryptographic keys etc. are subject to a license agreement between
you and Univention and not subject to the AGPL-3.0-only.

In the case you use this program under the terms of the AGPL-3.0-only,
the program is provided in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public
License with the Debian GNU/Linux or Univention distribution in file
/usr/share/common-licenses/AGPL-3; if not, see
<https://www.gnu.org/licenses/agpl-3.0.txt>.
-->

****************************************
Univention Corporate Server Architecture
****************************************

Local build
===========

Requirements:

* The KNUT CA certificate must be part of your local certificate installation.
  See `Install KNUT domain root CA certificate in the Dev Onboarding
  <http://univention.gitpages.knut.univention.de/internal/dev-onboarding/connection.html#install-knut-domain-root-ca-certificate>`__.

* Use Python virtual environment for a separated Python environment decoupled
  from your local Python installation. Install the deb-package on Debian/Ubuntu:
  ``apt install virtualenvwrapper``.

  * Create a new virtual environment with ``mkvirtualenv $env_name``.
  * Enter a virtual environment with ``workon $env_name``.
  * Leave a virtual environment with ``deactivate``.

  On other operating systems see the `Virtualenvwrapper documentation
  <https://virtualenvwrapper.readthedocs.io/en/latest/>`__.  See `Controlling
  the Active Environment
  <https://virtualenvwrapper.readthedocs.io/en/4.8.4/command_ref.html#controlling-the-active-environment>`__
  on how to switch environments. For this project and other Sphinx based
  projects from Univention, one such virtual environment is enough.


Prepare local Python environment once:

1. Checkout this repository.

#. Install the dependencies:

   .. code-block::

      python3 -m pip install --upgrade pip
      pip install -r requirements.txt --cert /etc/ssl/certs/ca-certificates

With the requirements, `Univention Sphinx Book theme
<https://git.knut.univention.de/univention/documentation/univention_sphinx_book_theme>`_
and `Univention Sphinx extension
<https://git.knut.univention.de/univention/documentation/univention_sphinx_extension>`_
are also installed.

Build the documentation:

1. Run the static build: ``make html`` or run a live server: ``make livehtml``.
#. Open http://localhost:8000 in your browser.

To build the documentation with the make target interface known from the other UCS documentation, run::

    make check install DESTDIR=../public

The ``check`` target runs the checks *linkcheck* and *spelling*. The
``install`` target builds the HTML files and PDF file. The HTML files and the
PDF for publishing can the be found in ``../public/html``.
