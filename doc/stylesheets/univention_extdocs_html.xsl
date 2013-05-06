<?xml version='1.0'?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
		xmlns="http://www.w3.org/1999/xhtml">
  <xsl:import href="/usr/share/xml/docbook/stylesheet/docbook-xsl/xhtml/docbook.xsl"/>
  <xsl:include href="common.xsl"/>
  <xsl:include href="common_html.xsl"/>

  <!-- Table of Contents: no chapter toc -->
  <xsl:param name="generate.toc">
    /appendix toc,title
    article/appendix  nop
    article   toc,title
    book      toc,title,example,equation
    /chapter  toc
    part      toc,title
    /preface  toc,title
    reference toc,title
    /sect1    toc
    /sect2    toc
    /sect3    toc
    /sect4    toc
    /sect5    toc
    /section  toc
    set       toc,title
  </xsl:param>

</xsl:stylesheet>
<!-- vim: set ts=8 sw=2 et: -->
