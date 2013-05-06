<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <!-- <xsl:param name="toc.max.depth">5</xsl:param> -->
  <xsl:param name="section.autolabel" select="1"/>
  <xsl:param name="section.label.includes.component.label" select="1"/>
  <xsl:param name="toc.section.depth" select="3"/>
  <xsl:param name="xref.with.number.and.title" select="0"/>

  <!-- command -->
  <xsl:template match="command">
    <xsl:call-template name="inline.monoseq"/>
  </xsl:template>

  <!-- trim leading and trailing white-space from verbatim environments -->
  <!-- PHahn 2013-04-30 -->
  <xsl:template match="programlisting/text()|screen/text()|synopsis/text()" name="univention-trim">
    <xsl:param name="content" select="string()"/>
    <xsl:param name="trim" select="'&#09;&#10;&#13;&#32;'"/>
    <xsl:variable name="length" select="string-length($content)"/>
    <xsl:choose>
      <xsl:when test="$length = 0"/>
      <!-- right trim -->
      <xsl:when test="contains($trim, substring($content, $length, 1))">
        <xsl:call-template name="univention-trim">
          <xsl:with-param name="content" select="substring($content, 1, $length - 1)"/>
        </xsl:call-template>
      </xsl:when>
      <!-- left trim -->
      <xsl:otherwise>
        <xsl:variable name="first" select="substring(normalize-space($content), 1, 1)"/>
        <xsl:variable name="prefix" select="string-length(substring-before($content, $first))"/>
        <xsl:value-of select="substring($content, 1 + $prefix)"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>
<!-- vim: set ts=8 sw=2 et: -->
