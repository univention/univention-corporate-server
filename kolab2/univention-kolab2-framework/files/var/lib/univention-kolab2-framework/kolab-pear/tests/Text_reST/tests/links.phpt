--TEST--
Text_reST_Parser:: link parsing
--FILE--
<?php
require_once dirname(__FILE__) . '/../reST.php';

$document = &Text_reST::parse("

.. __: http://dev.horde.org/

Test link: http://www.horde.org/.  Test email: foo@example.com.  An anonymous
link to `Slashdot <http://slashdot.org/>`__.  Here's the `Horde dev site`__.
Here's `another link`__.

__ http://example.com/

Here's one for Python_.  Here's one for `verified voting`_.

.. _Python: http://www.python.org/
.. _verified voting: http://www.verifiedvoting.org/

Here's a `named email address`_.

.. _named email address: foo@example.com

");

$document->dump();
--EXPECT--
Document::
  Paragraph::
    "Test link: "
    Link:: href="http://www.horde.org/"
      "http://www.horde.org/"
    ".  Test email: "
    Link:: href="mailto:foo@example.com"
      "foo@example.com"
    ".  An anonymous link to "
    Link:: href="http://slashdot.org/"
      "Slashdot"
    ".  Here's the "
    Link:: href="http://dev.horde.org/"
      "Horde dev site"
    ". Here's "
    Link:: href="http://example.com/"
      "another link"
    "."
  Paragraph::
    "Here's one for "
    Link:: href="http://www.python.org/" name="python"
      "Python"
    ".  Here's one for "
    Link:: href="http://www.verifiedvoting.org/" name="verified voting"
      "verified voting"
    "."
  Paragraph::
    "Here's a "
    Link:: href="mailto:foo@example.com" name="named email address"
      "named email address"
    "."
