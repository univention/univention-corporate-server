<?xml version="1.0"?>

<xsl:stylesheet version="1.0"
  xmlns="http://www.w3.org/1999/xhtml"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:rss="http://purl.org/rss/1.0/"
  xmlns:atom="http://www.w3.org/2005/Atom">

  <xsl:output indent="yes" encoding="UTF-8"/>

  <xsl:template match="/rss|/atom:feed">
    <html>
      <head>
        <title>
          <xsl:value-of select="/rss/channel/title"/>
        </title>
        <style type="text/css">
          img {
              border: 0;
              padding: 5px;
          }
        </style>
      </head>
      <body>
        <p>
          You're viewing an XML content feed which is
          intended to be viewed within a feed aggregator.
        </p>

        <xsl:variable name="link" select="/rss/channel/link"/>
        <h3>Subscribe to <a href="{$link}"><xsl:value-of select="/rss/channel/title"/></a></h3>
        <xsl:variable name="cimage" select="/rss/channel/image/url"/>
        <div style="float:right;"><img src="{$cimage}"/></div>
        <p>
          Subscribe now in your favorite RSS aggregator:
        </p>

        <xsl:variable name="resource" select="/rss/channel/atom:link"/>

        <div>
          <a href="http://www.rojo.com/add-subscription?resource={$resource}">
            <img src="http://www.rojo.com/skins/static/images/add-to-rojo.gif" alt="Subscribe in Rojo"/>
          </a>

          <a href="http://add.my.yahoo.com/rss?url={$resource}">
            <img src="http://us.i1.yimg.com/us.yimg.com/i/us/my/addtomyyahoo4.gif" alt="Add to My yahoo" />
          </a>

          <a href="http://www.newsgator.com/ngs/subscriber/subext.aspx?url={$resource}">
            <img src="http://www.newsgator.com/images/ngsub1.gif" alt="Subscribe in NewsGator Online"/>
          </a>

          <a href="http://www.bloglines.com/sub/{$resource}">
            <img src="http://www.bloglines.com/images/sub_modern5.gif" alt="Subscribe with Bloglines"/>
          </a>

          <a href="http://fusion.google.com/add?feedurl={$resource}">
            <img src="http://buttons.googlesyndication.com/fusion/add.gif" alt="Subscribe with Google Reader"/>
          </a>
        </div>

        <p>
          <h3>Preview</h3>
        </p>

        <xsl:apply-templates select="/rss/channel/item" />

      </body>
    </html>
  </xsl:template>

  <xsl:template match="item">
    <xsl:variable name="link" select="link"/>
    <p>
      <a href="{$link}">
        <xsl:value-of select="title"/>
      </a>
      <br />
      <xsl:value-of select="description"/>
    </p>
  </xsl:template>

</xsl:stylesheet>
