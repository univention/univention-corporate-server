--TEST--
Text_reST_Parser:: text role parsing
--FILE--
<?php
require_once dirname(__FILE__) . '/../reST.php';

$document = &Text_reST::parse("

This is a test paragraph.  It has *italics* and **bold**, ``literal text``,
`A title reference` another :title-reference:`title reference`.  It has
some :sup:`superscript` and some :sub:`subscript`.

");

$document->dump();
--EXPECT--
Document::
  Paragraph::
    "This is a test paragraph.  It has "
    Interpreted-Text:: role="emphasis"
      "italics"
    " and "
    Interpreted-Text:: role="strong"
      "bold"
    ", "
    Interpreted-Text:: role="literal"
      "literal text"
    ", "
    Interpreted-Text:: role="title-reference"
      "A title reference"
    " another "
    Interpreted-Text:: role="title-reference"
      "title reference"
    ".  It has some "
    Interpreted-Text:: role="superscript"
      "superscript"
    " and some "
    Interpreted-Text:: role="subscript"
      "subscript"
    "."
