# Redirects from legacy DocBook text to Sphinx builds

The legacy DocBook text for the app-center documentation was published
at <https://docs.software-univention.de/app-provider-5.0.html>. The
generic link to the latest documentation was
<https://docs.software-univention.de/app-provider.html>.

Links to the documentation are spread in Univention products, Univention
forum, blog postings, reader's bookmark lists and so on. For readers'
convenience the links need to keep working after the Sphinx builds
replace the DocBook text.

The implemented solution replaces the single HTML DocBook build file
with a HTML file that takes care of the redirects. When a reader opens
an old link, their browser redirects them to the new documentation
location.

In the document's root directory is the file `app-provider-5.0.html`,
called *redirect map* in this README. In takes care of the redirection
from the before mentioned links to the new location and supports the
following cases:

1. The reader accesses the link directly. Then the browser redirects
   the reader to the new location after 15 seconds. Before redirection,
   the reader sees the document header and a hint about the redirection
   together with the direct link.
2. The reader accesses the documentation with an anchor link to a
   specific section, for example
   <https://docs.software-univention.de/app-provider-5.0.html#testing:test-app-center>.
   The redirect map detects the hash part of the link and redirects the
   reader's browser to the new location
   <https://docs.software-univention.de/app-center/5.0/en/lifecycle.html#testing-test-app-center>
   directly and immediately.

The redirect map is not automatically copied to the docs.univention.de
repository by the build pipeline. Changes to `app-provider-5.0.html`
need to be pushed manually to the docs.univention.de documentation
repository.
