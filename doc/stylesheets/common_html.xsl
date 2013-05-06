<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
                xmlns="http://www.w3.org/1999/xhtml">

  <xsl:param name="docbook.css.source">univention.css</xsl:param>
  <xsl:param name="html.stylesheet" select="'univention.css'"/>

  <xsl:template name="system.head.content">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  </xsl:template>

  <xsl:template name="user.header.content">
    <div id="header">
      <div id="header-wrapper">
        <div id="header-left">
          <a href="http://www.univention.de/"><img alt="" src="images/univention_logo.png" /></a>
        </div>
        <div id="header-right" />
      </div>
    </div>
  </xsl:template>

  <!-- guimenu -->
  <xsl:template match="guimenu">
    <xsl:call-template name="inline.charseq"/>
  </xsl:template>

  <!-- package -->
  <xsl:template match="package">
    <xsl:call-template name="inline.charseq"/>
  </xsl:template>

  <!-- mousebutton -->
  <xsl:template name="inline.squarebracketsseq">
    <xsl:param name="content">
      <xsl:call-template name="anchor"/>
      <xsl:call-template name="simple.xlink">
        <xsl:with-param name="content">
          <xsl:apply-templates/>
        </xsl:with-param>
      </xsl:call-template>
    </xsl:param>
    <span>
      <xsl:apply-templates select="." mode="common.html.attributes"/>
      <xsl:text>[</xsl:text>
      <xsl:copy-of select="$content"/>
      <xsl:text>]</xsl:text>
      <xsl:call-template name="apply-annotations"/>
    </span>
  </xsl:template>

  <xsl:template match="mousebutton">
    <xsl:call-template name="inline.squarebracketsseq"/>
  </xsl:template>

  <!-- titlepage -->
  <xsl:template name="book.titlepage.before.verso"/>
  <xsl:template name="book.titlepage.before.recto"/>

  <xsl:template name="book.titlepage.recto">
    <xsl:apply-templates mode="book.titlepage.recto.auto.mode" select="bookinfo/title"/>
    <xsl:apply-templates mode="book.titlepage.recto.auto.mode" select="bookinfo/subtitle"/>
  </xsl:template>

  <!-- http://docbook.sourceforge.net/release/xsl/current/doc/html/citerefentry.link.html -->
  <xsl:param name="citerefentry.link" select="1"/>
  <xsl:template name="generate.citerefentry.link">
    <xsl:text>http://manpages.debian.net/cgi-bin/man.cgi?format=html&amp;query=</xsl:text>
    <xsl:value-of select="refentrytitle"/>
    <xsl:if test="manvolnum">
      <xsl:text>&amp;sektion=</xsl:text>
      <xsl:value-of select="manvolnum"/>
    </xsl:if>
  </xsl:template>

  <!-- Feedback links - Section -->
  <xsl:template name="section.heading">
    <xsl:param name="section" select="."/>
    <xsl:param name="level" select="1"/>
    <xsl:param name="allow-anchors" select="1"/>
    <xsl:param name="title"/>
    <xsl:param name="class" select="'title'"/>

    <!-- declare and initialize the variable language, which is used to localize the feedback link -->
    <xsl:variable name="language">
      <xsl:call-template name="l10n.language"/>
    </xsl:variable>

    <xsl:variable name="url_toplevel">
      <xsl:choose>
	<xsl:when test="$language=en">com</xsl:when>
	<xsl:otherwise>de</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>


    <xsl:variable name="id">
      <xsl:choose>
	<xsl:when test="self::subtitle">
	  <xsl:call-template name="object.id">
	    <xsl:with-param name="object" select="."/>
	  </xsl:call-template>
	</xsl:when>
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

    <xsl:variable name="hlevel">
      <xsl:choose>
	<xsl:when test="$level &gt; 5">6</xsl:when>
	<xsl:otherwise>
	  <xsl:value-of select="$level + 1"/>
	</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:element name="h{$hlevel}">
      <xsl:attribute name="class"><xsl:value-of select="$class"/></xsl:attribute>
      <xsl:if test="$css.decoration != '0'">
	<xsl:if test="$hlevel&lt;3">
	  <xsl:attribute name="style">clear: both</xsl:attribute>
	</xsl:if>
      </xsl:if>
      <xsl:if test="$allow-anchors != 0 and $generate.id.attributes = 0">
	<xsl:call-template name="anchor">
	  <xsl:with-param name="node" select="$section"/>
	  <xsl:with-param name="conditional" select="0"/>
	</xsl:call-template>
      </xsl:if>
      <xsl:if test="$generate.id.attributes != 0 and not(local-name(.) = 'appendix')">
	<xsl:attribute name="id"><xsl:value-of select="$id"/></xsl:attribute>
      </xsl:if>
      <xsl:copy-of select="$title"/>
      <xsl:choose>
        <xsl:when test="contains($language,'de')">
          <a href="http://www.univention.de/feedback?manual={$id}"><img src="illustrations/manual-feedback-button.svg" width="auto" height="24" align="right" alt="Feedback"/></a>
        </xsl:when>
        <xsl:otherwise>
          <a href="http://www.univention.com/feedback?manual={$id}"><img src="illustrations/manual-feedback-button.svg" width="auto" height="24" align="right" alt="Feedback"/></a>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:element>
  </xsl:template>


<!-- assign the anchor a class, so that css can be used to fix the offset when following a link -->
<xsl:template name="anchor">
  <xsl:param name="node" select="."/>
  <xsl:param name="conditional" select="1"/>
  <xsl:variable name="id">
    <xsl:call-template name="object.id">
      <xsl:with-param name="object" select="$node"/>
    </xsl:call-template>
  </xsl:variable>
  <xsl:if test="$conditional = 0 or $node/@id or $node/@xml:id">
    <a name="{$id}" class="anchor"/>
  </xsl:if>
</xsl:template>

</xsl:stylesheet>
<!-- vim: set ts=8 sw=2 et: -->
