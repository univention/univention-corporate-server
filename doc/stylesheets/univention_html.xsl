<?xml version='1.0'?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
		xmlns="http://www.w3.org/1999/xhtml">
  <xsl:import href="/usr/share/xml/docbook/stylesheet/docbook-xsl/xhtml/docbook.xsl"/>
  <xsl:include href="common.xsl"/>
  <xsl:include href="common_html.xsl"/>

  <xsl:template match="title" mode="book.titlepage.recto.auto.mode">
    <xsl:variable name="id">
      <xsl:choose>
	<!-- if title is in an *info wrapper, get the grandparent -->
	<xsl:when test="contains(local-name(..), 'info')">
          <xsl:call-template name="object.id">
            <xsl:with-param name="object" select="../.."/>
          </xsl:call-template>
	</xsl:when>
	<xsl:otherwise>
          <xsl:call-template name="object.id">
            <xsl:with-param name="object" select=".."/>
          </xsl:call-template>
	</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <h1>
      <xsl:apply-templates select="." mode="common.html.attributes"/>
      <xsl:if test="$generate.id.attributes = 0">
	<a name="{$id}"/>
      </xsl:if>
      <xsl:choose>
	<xsl:when test="$show.revisionflag != 0 and @revisionflag">
          <span class="{@revisionflag}">
            <xsl:apply-templates mode="titlepage.mode"/>
          </span>
	</xsl:when>
	<xsl:otherwise>
          <xsl:apply-templates mode="titlepage.mode"/>
	</xsl:otherwise>
      </xsl:choose>
    </h1>
    <div align="center">
      <img src="images/ucs_logo.png" width="60%"/>
    </div>
  </xsl:template>

  <!-- Table of Contents -->
  <xsl:param name="generate.toc">
    /appendix toc,title
    article/appendix  nop
    article   toc,title
    book      toc,title,example,equation
    chapter   toc
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
