<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
		xmlns:fo="http://www.w3.org/1999/XSL/Format">
  <xsl:import href="/usr/share/xml/docbook/stylesheet/docbook-xsl/fo/docbook.xsl"/>
  <xsl:include href="common.xsl"/>
  <xsl:include href="common_fo.xsl"/>

  <xsl:template name="force.page.count">
    <xsl:param name="element" select="local-name(.)"/>
    <xsl:param name="master-reference" select="''"/>

    <xsl:choose>
      <xsl:when test="starts-with($master-reference,
		      'lot')">no-force</xsl:when>
      <xsl:when test="$element = 'preface'">end-on-even</xsl:when>
      <xsl:when test="starts-with($master-reference,
		      'front')">no-force</xsl:when>
      <!-- double-sided output -->
      <xsl:when test="$double.sided != 0">no-force</xsl:when>
      <!-- single-sided output -->
      <xsl:otherwise>no-force</xsl:otherwise>
    </xsl:choose>
  </xsl:template>

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
