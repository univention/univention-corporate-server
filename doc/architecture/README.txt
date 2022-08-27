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
