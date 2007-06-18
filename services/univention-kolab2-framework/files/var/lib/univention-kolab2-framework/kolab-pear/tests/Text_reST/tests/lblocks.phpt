--TEST--
Text_reST_Parser:: text role parsing
--FILE--
<?php
require_once dirname(__FILE__) . '/../reST.php';

$document = &Text_reST::parse('

::

    if ($foo) {
        ...
    }

Here is another paragraph::

    while (true) {
    }

And another. ::

    do {
        if (...) {
            break;
        }
    } while (false);

');

$document->dump();
--EXPECT--
Document::
  Literal-Block::
    "if ($foo) {
    ...
}"
  Paragraph::
    "Here is another paragraph:"
  Literal-Block::
    "while (true) {
}"
  Paragraph::
    "And another."
  Literal-Block::
    "do {
    if (...) {
        break;
    }
} while (false);"
