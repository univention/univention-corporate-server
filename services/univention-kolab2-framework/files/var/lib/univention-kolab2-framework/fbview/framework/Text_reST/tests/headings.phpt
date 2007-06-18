--TEST--
Text_reST_Parser:: heading/section parsing
--FILE--
<?php
require_once dirname(__FILE__) . '/../reST.php';

$document = &Text_reST::parse("

===================
  Document Title
===================

Here is a paragraph.

Sub-heading 1
-------------

Another paragraph.

Sub-sub-heading 1
^^^^^^^^^^^^^^^^^

another paragraph.

Sub-sub-heading 2
^^^^^^^^^^^^^^^^^

another paragraph.

Sub-heading 2
-------------

another paragraph

");

$document->dump();
--EXPECT--
Document::
  Section:: level="1"
    Heading:: level="1"
      "Document Title"
    Paragraph::
      "Here is a paragraph."
    Section:: level="2"
      Heading:: level="2"
        "Sub-heading 1"
      Paragraph::
        "Another paragraph."
      Section:: level="3"
        Heading:: level="3"
          "Sub-sub-heading 1"
        Paragraph::
          "another paragraph."
      Section:: level="3"
        Heading:: level="3"
          "Sub-sub-heading 2"
        Paragraph::
          "another paragraph."
    Section:: level="2"
      Heading:: level="2"
        "Sub-heading 2"
      Paragraph::
        "another paragraph"
