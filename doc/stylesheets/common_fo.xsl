<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
                xmlns:fo="http://www.w3.org/1999/XSL/Format">

  <xsl:param name="paper.type" select="'A4'"/>
  <xsl:param name="double.sided" select="'1'"/>
  <xsl:param name="fop1.extensions" select="1"/>
  <xsl:param name="draft.mode">no</xsl:param>
  <xsl:param name="draft.watermark.image">/usr/share/xml/docbook/stylesheet/docbook-xsl/images/draft.png</xsl:param>

  <!-- margins -->
  <xsl:param name="page.margin.top">0</xsl:param>
  <xsl:param name="page.margin.inner">2cm</xsl:param>
  <xsl:param name="page.margin.outer">2cm</xsl:param>
  <xsl:param name="page.margin.bottom">0</xsl:param>
  <xsl:param name="body.margin.top">100</xsl:param>
  <xsl:param name="body.margin.bottom">3cm</xsl:param>
  <xsl:param name="body.margin.left">2cm</xsl:param>
  <xsl:param name="body.margin.right">2cm</xsl:param>


  <!-- header and footer -->
  <xsl:param name="header.rule">0</xsl:param>
  <xsl:param name="footer.rule">0</xsl:param>
  <xsl:param name="header.column.widths">1 0 1</xsl:param>
  <xsl:param name="region.before.extent">80</xsl:param>
  <xsl:param name="region.after.extent">17mm</xsl:param>


  <!-- guimenu -->
  <xsl:template match="guimenu">
    <xsl:call-template name="inline.boldseq"/>
  </xsl:template>

  <!-- package -->
  <xsl:template name="inline.bolditalicseq">
    <xsl:param name="content">
      <xsl:call-template name="simple.xlink">
        <xsl:with-param name="content">
          <xsl:apply-templates/>
        </xsl:with-param>
      </xsl:call-template>
    </xsl:param>
    <fo:inline font-style="italic" font-weight="bold">
      <xsl:call-template name="anchor"/>
      <xsl:if test="@dir">
        <xsl:attribute name="direction">
          <xsl:choose>
            <xsl:when test="@dir = 'ltr' or @dir = 'lro'">ltr</xsl:when>
            <xsl:otherwise>rtl</xsl:otherwise>
          </xsl:choose>
        </xsl:attribute>
      </xsl:if>
      <xsl:copy-of select="$content"/>
    </fo:inline>
  </xsl:template>

  <xsl:template match="package">
    <xsl:call-template name="inline.bolditalicseq"/>
  </xsl:template>

  <!-- mousebutton -->
  <xsl:template name="inline.boldsquarebracketsseq">
    <xsl:param name="content">
      <xsl:call-template name="simple.xlink">
        <xsl:with-param name="content">
          <xsl:apply-templates/>
        </xsl:with-param>
      </xsl:call-template>
    </xsl:param>
    <fo:inline font-weight="bold">
      <xsl:if test="@dir">
        <xsl:attribute name="direction">
          <xsl:choose>
            <xsl:when test="@dir = 'ltr' or @dir = 'lro'">ltr</xsl:when>
            <xsl:otherwise>rtl</xsl:otherwise>
          </xsl:choose>
        </xsl:attribute>
      </xsl:if>
      <xsl:text>[</xsl:text>
      <xsl:copy-of select="$content"/>
      <xsl:text>]</xsl:text>
    </fo:inline>
  </xsl:template>

  <xsl:template match="mousebutton">
    <xsl:call-template name="inline.boldsquarebracketsseq"/>
  </xsl:template>

  <!-- illustration path -->
  <xsl:param name="front.cover" select="'illustrations/page-background-title-page.jpg'"/>
  <xsl:param name="odd.header.image" select="'illustrations/page-background-odd-header.jpg'"/>
  <xsl:param name="odd.footer.image" select="'illustrations/page-background-odd-footer.jpg'"/>
  <xsl:param name="even.header.image" select="'illustrations/page-background-even-header.jpg'"/>
  <xsl:param name="even.footer.image" select="'illustrations/page-background-even-footer.jpg'"/>

  <!-- images -->
  <xsl:template name="user.pagemasters">
    <!-- front image -->
    <fo:simple-page-master master-name="front-cover"
                           page-width="{$page.width}"
                           page-height="{$page.height}"
                           margin-top="0"
                           margin-bottom="0"
                           margin-left="1"
                           margin-right="0">
      <fo:region-body margin-bottom="0" margin-top="0"
                      column-gap="{$column.gap.front}"
                      column-count="{$column.count.front}"
                      background-image="url({$front.cover})"/>
    </fo:simple-page-master>

    <!-- odd-pages-logo -->
    <fo:simple-page-master master-name="odd-pages"
                           page-width="{$page.width}"
                           page-height="{$page.height}"
                           margin-top="{$page.margin.top}"
                           margin-bottom="{$page.margin.bottom}">
      <xsl:attribute name="margin-{$direction.align.end}">
        <xsl:value-of select="$page.margin.outer"/>
      </xsl:attribute>
      <xsl:if test="$axf.extensions != 0">
        <xsl:call-template name="axf-page-master-properties">
          <xsl:with-param name="page.master">odd-pages</xsl:with-param>
        </xsl:call-template>
      </xsl:if>
      <fo:region-body margin-bottom="{$body.margin.bottom}"
                      margin-top="{$body.margin.top}"
                      margin-left="{$body.margin.left}"
                      column-gap="{$column.gap.body}"
                      column-count="{$column.count.body}">
      </fo:region-body>
      <fo:region-before region-name="xsl-region-before-odd"
                        start-indent="-2cm"
                        extent="{$region.before.extent}"
                        display-align="after"
                        background-repeat="no-repeat"
                        background-image="url({$odd.header.image})"
                        />
      <fo:region-after region-name="xsl-region-after-odd"
                       start-indent="-2cm"
                       extent="{$region.after.extent}"
                       display-align="before"
                       background-repeat="no-repeat"
                       background-image="url({$odd.footer.image})"/>
    </fo:simple-page-master>

    <!-- even-pages-logo -->
    <fo:simple-page-master master-name="even-pages"
                           page-width="{$page.width}"
                           page-height="{$page.height}"
                           margin-top="{$page.margin.top}"

                           margin-bottom="{$page.margin.bottom}">
      <xsl:attribute name="margin-{$direction.align.start}">
        <xsl:value-of select="$page.margin.outer"/>
        <xsl:if test="$fop.extensions != 0">
          <xsl:value-of select="concat(' - (',$title.margin.left,')')"/>
        </xsl:if>
      </xsl:attribute>
      <xsl:if test="$axf.extensions != 0">
        <xsl:call-template name="axf-page-master-properties">
          <xsl:with-param name="page.master">even-pages</xsl:with-param>
        </xsl:call-template>
      </xsl:if>
      <fo:region-body margin-bottom="{$body.margin.bottom}"
                      margin-top="{$body.margin.top}"
                      margin-right="{$body.margin.right}"
                      column-gap="{$column.gap.body}"
                      column-count="{$column.count.body}">
      </fo:region-body>
      <fo:region-before region-name="xsl-region-before-even"
                        end-indent="-2cm"
                        extent="{$region.before.extent}"
                        display-align="after"
                        background-repeat="no-repeat"
                        background-position-horizontal="right"
                        background-image="url({$even.header.image})"
                        />
      <fo:region-after region-name="xsl-region-after-even"
                       end-indent="-2cm"
                       extent="{$region.after.extent}"
                       display-align="before"
                       background-repeat="no-repeat"
                       background-position-horizontal="right"
                       background-image="url({$even.footer.image})"/>
    </fo:simple-page-master>

    <!-- body-sequence-master  -->
    <fo:page-sequence-master master-name="body-custom">
      <fo:repeatable-page-master-alternatives>
        <fo:conditional-page-master-reference master-reference="blank"
                                              blank-or-not-blank="blank"/>
        <fo:conditional-page-master-reference master-reference="odd-pages"
                                              page-position="first"/>
        <fo:conditional-page-master-reference master-reference="odd-pages"
                                              odd-or-even="odd"/>
        <fo:conditional-page-master-reference
           odd-or-even="even">
          <xsl:attribute name="master-reference">
            <xsl:choose>
              <xsl:when test="$double.sided != 0">even-pages</xsl:when>
              <xsl:otherwise>odd-pages</xsl:otherwise>
            </xsl:choose>
          </xsl:attribute>
        </fo:conditional-page-master-reference>
      </fo:repeatable-page-master-alternatives>
    </fo:page-sequence-master>

    <!-- titlepage-sequence master -->
    <fo:page-sequence-master master-name="titlepage-custom">
      <fo:repeatable-page-master-alternatives>
        <fo:conditional-page-master-reference master-reference="blank"
                                              blank-or-not-blank="blank"/>
        <fo:conditional-page-master-reference master-reference="even-pages"
                                              page-position="first"/>
        <fo:conditional-page-master-reference master-reference="titlepage-odd"
                                              odd-or-even="odd"/>
        <fo:conditional-page-master-reference
                                              odd-or-even="even">
          <xsl:attribute name="master-reference">
            <xsl:choose>
              <xsl:when test="$double.sided != 0">even-pages</xsl:when>
              <xsl:otherwise>titlepage-odd</xsl:otherwise>
            </xsl:choose>
          </xsl:attribute>
        </fo:conditional-page-master-reference>
      </fo:repeatable-page-master-alternatives>
    </fo:page-sequence-master>


    <!-- lot-sequence-master -->
    <fo:page-sequence-master master-name="lot-custom">
      <fo:repeatable-page-master-alternatives>
        <fo:conditional-page-master-reference master-reference="blank"
                                              blank-or-not-blank="blank"/>
        <fo:conditional-page-master-reference master-reference="odd-pages"
                                              page-position="first"/>
        <fo:conditional-page-master-reference master-reference="odd-pages"
                                              odd-or-even="odd"/>
        <fo:conditional-page-master-reference
           odd-or-even="even">
          <xsl:attribute name="master-reference">
            <xsl:choose>
              <xsl:when test="$double.sided != 0">even-pages</xsl:when>
              <xsl:otherwise>odd-pages</xsl:otherwise>
            </xsl:choose>
          </xsl:attribute>
        </fo:conditional-page-master-reference>
      </fo:repeatable-page-master-alternatives>
    </fo:page-sequence-master>

  </xsl:template>


  <!-- select.user.pagemaster -->
  <xsl:template name="select.user.pagemaster">
    <xsl:param name="element"/>
    <xsl:param name="pageclass"/>
    <xsl:param name="default-pagemaster"/>
    <xsl:choose>
      <xsl:when test="$default-pagemaster = 'body'">
        <xsl:value-of select="'body-custom'" />
      </xsl:when>
      <xsl:when test="$default-pagemaster = 'lot'">
        <xsl:value-of select="'lot-custom'" />
      </xsl:when>
      <xsl:when test="$default-pagemaster = 'titlepage'">
        <xsl:value-of select="'titlepage-custom'" />
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$default-pagemaster"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- titlepage -->
  <xsl:template name="front.cover">
    <fo:page-sequence master-reference="front-cover" force-page-count="no-force">
      <fo:flow flow-name="xsl-region-body">
        <fo:block>
          <xsl:apply-templates mode="book.titlepage.recto.auto.mode" select="bookinfo/title"/>
          <xsl:apply-templates mode="book.titlepage.recto.auto.mode" select="bookinfo/subtitle"/>
        </fo:block>
      </fo:flow>
    </fo:page-sequence>
  </xsl:template>

  <xsl:template match="title" mode="book.titlepage.recto.auto.mode">
    <fo:block xsl:use-attribute-sets="book.titlepage.recto.style" text-align="center" font-size="20pt" margin-top="240pt" font-weight="bold" font-family="{$title.fontset}">
      <xsl:call-template name="division.title">
        <xsl:with-param name="node" select="ancestor-or-self::book[1]"/>
      </xsl:call-template>
    </fo:block>
  </xsl:template>

  <xsl:template match="subtitle" mode="book.titlepage.recto.auto.mode">
    <fo:block xsl:use-attribute-sets="book.titlepage.recto.style" text-align="center" font-size="17pt" margin-top="290pt" font-family="{$title.fontset}">
      <xsl:apply-templates select="." mode="book.titlepage.recto.mode"/>
    </fo:block>
  </xsl:template>

  <xsl:template name="book.titlepage.verso">
    <xsl:apply-templates mode="book.titlepage.verso.auto.mode" select="bookinfo/legalnotice"/>
    <xsl:apply-templates mode="book.titlepage.verso.auto.mode" select="info/legalnotice"/>
  </xsl:template>

  <xsl:template match="legalnotice" mode="book.titlepage.verso.auto.mode">
    <fo:block xsl:use-attribute-sets="book.titlepage.verso.style" margin-top="370pt">
      <xsl:apply-templates select="." mode="book.titlepage.verso.mode"/>
    </fo:block>
  </xsl:template>

  <xsl:template name="book.titlepage.before.verso"/>
  <xsl:template name="book.titlepage.before.recto"/>
  <xsl:template name="book.titlepage.recto"/>

  <!-- header -->
  <xsl:template name="header.content">
    <xsl:param name="pageclass" select="''"/>
    <xsl:param name="sequence" select="''"/>
    <xsl:param name="position" select="''"/>
    <xsl:param name="gentext-key" select="''"/>

    <fo:block>
      <xsl:choose>
        <xsl:when test="$sequence = 'odd' and $position = 'right'">
          <fo:retrieve-marker retrieve-class-name="section.head.marker"
                              retrieve-position="first-including-carryover"
                              retrieve-boundary="page-sequence"/>
        </xsl:when>
        <xsl:when test="$sequence = 'even' and $position = 'left'">
          <fo:retrieve-marker retrieve-class-name="section.head.marker"
                              retrieve-position="first-including-carryover"
                              retrieve-boundary="page-sequence"/>
        </xsl:when>
      </xsl:choose>
    </fo:block>
  </xsl:template>

  <xsl:attribute-set name="header.content.properties">
    <xsl:attribute name="font-style">italic</xsl:attribute>
  </xsl:attribute-set>

  <!-- footer -->
  <xsl:template name="footer.content">
    <xsl:param name="pageclass" select="''"/>
    <xsl:param name="sequence" select="''"/>
    <xsl:param name="position" select="''"/>
    <xsl:param name="gentext-key" select="''"/>
    <fo:block>
      <xsl:choose>
        <xsl:when test="$pageclass='titlepage' or $pageclass='lot' or $pageclass='front' or $pageclass='back' or $pageclass='index'">
        </xsl:when>
        <xsl:otherwise>
          <xsl:choose>
            <xsl:when test="$sequence = 'even'
                            and $position='left'">
              <fo:page-number/>
            </xsl:when>

            <xsl:when test="($sequence = 'odd' or $sequence = 'first')
                            and $position='right'">
              <fo:page-number/>
            </xsl:when>

            <xsl:when test="$sequence='blank' and $position = 'left'">
              <fo:page-number/>
            </xsl:when>
          </xsl:choose>
        </xsl:otherwise>
      </xsl:choose>
    </fo:block>
  </xsl:template>

  <!-- page number formating -->
  <xsl:template name="page.number.format">
    1
  </xsl:template>

  <xsl:template name="initial.page.number">
    <xsl:param name="element" select="local-name(.)"/>
    <xsl:param name="master-reference" select="''"/>

    <xsl:variable name="first.book.content"
                  select="ancestor::book/*[
                          not(self::title or
                          self::subtitle or
                          self::titleabbrev or
                          self::bookinfo or
                          self::info or
                          self::dedication or
                          self::preface or
                          self::toc or
                          self::lot)][1]"/>
    <xsl:choose>
      <xsl:when test="$element = 'toc'">auto</xsl:when>
      <xsl:when test="$element = 'book'">auto</xsl:when>
      <xsl:when test="$element = 'preface'">auto</xsl:when>
      <xsl:when test="($element = 'dedication' or $element = 'article')

                      and not(preceding::chapter
                      or preceding::preface
                      or preceding::appendix
                      or preceding::article
                      or preceding::dedication
                      or parent::part
                      or parent::reference)">1</xsl:when>
      <xsl:when test="generate-id($first.book.content) =
                      generate-id(.)">auto</xsl:when>
      <xsl:otherwise>auto</xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- font sizes -->
  <xsl:attribute-set name="section.title.level1.properties">
    <xsl:attribute name="font-size">
      <xsl:value-of select="$body.font.master * 1.8"/>
      <xsl:text>pt</xsl:text>
    </xsl:attribute>
  </xsl:attribute-set>
  <xsl:attribute-set name="section.title.level2.properties">
    <xsl:attribute name="font-size">
      <xsl:value-of select="$body.font.master * 1.5"/>
      <xsl:text>pt</xsl:text>
    </xsl:attribute>
  </xsl:attribute-set>
  <xsl:attribute-set name="section.title.level3.properties">
    <xsl:attribute name="font-size">
      <xsl:value-of select="$body.font.master * 1.2"/>
      <xsl:text>pt</xsl:text>
    </xsl:attribute>
  </xsl:attribute-set>
  <xsl:attribute-set name="section.title.level4.properties">
    <xsl:attribute name="font-size">
      <xsl:value-of select="$body.font.master * 1.1"/>
      <xsl:text>pt</xsl:text>
    </xsl:attribute>
  </xsl:attribute-set>
  <xsl:attribute-set name="section.title.level5.properties">
    <xsl:attribute name="font-size">
      <xsl:value-of select="$body.font.master"/>
      <xsl:text>pt</xsl:text>
    </xsl:attribute>
  </xsl:attribute-set>
  <xsl:attribute-set name="section.title.level6.properties">
    <xsl:attribute name="font-size">
      <xsl:value-of select="$body.font.master"/>
      <xsl:text>pt</xsl:text>
    </xsl:attribute>
  </xsl:attribute-set>

<!-- Feedback links - Section -->
  <xsl:template name="section.heading">
    <xsl:param name="level" select="1"/>
    <xsl:param name="marker" select="1"/>
    <xsl:param name="title"/>
    <xsl:param name="marker.title"/>

    <!-- declare and initialize the variable language, which is used to localize the feedback link -->
    <xsl:variable name="language">
      <xsl:call-template name="l10n.language"/>
    </xsl:variable>

    <xsl:variable name="url_toplevel">
      <xsl:choose>
	<xsl:when test="contains($language,'de')">de</xsl:when>
	<xsl:otherwise>com</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>

  <xsl:variable name="section"
                select="(ancestor::section |
                        ancestor::simplesect |
                        ancestor::sect1 |
                        ancestor::sect2 |
                        ancestor::sect3 |
                        ancestor::sect4 |
                        ancestor::sect5)[position() = last()]"/>


    <xsl:variable name="sectionid">
      <xsl:call-template name="object.id">
        <xsl:with-param name="object" select="$section"/>
      </xsl:call-template>
    </xsl:variable>


    <fo:block xsl:use-attribute-sets="section.title.properties">
      <xsl:if test="$marker != 0">
	<fo:marker marker-class-name="section.head.marker">
	  <xsl:copy-of select="$marker.title"/>
	</fo:marker>
      </xsl:if>

      <xsl:choose>
	<xsl:when test="$level=1">
	  <fo:block-container>
	    <fo:block-container>
	      <fo:block xsl:use-attribute-sets="section.title.level1.properties">
		<xsl:copy-of select="$title"/>
	      </fo:block>
	    </fo:block-container>

	    <fo:block-container position="absolute" left="17.1cm">
	      <fo:block>
		<fo:basic-link external-destination="url('http://www.univention.{$url_toplevel}/feedback?manual={$sectionid}')"
			       color="blue" text-decoration="underline">
		  <fo:external-graphic src="url(illustrations/manual-feedback-button.svg)" width="auto" height="auto" content-width="auto"  content-height="16px" content-type="content-type:image/svg+xml"/>
		</fo:basic-link>
	      </fo:block>
	    </fo:block-container>
	  </fo:block-container>
	</xsl:when>

	<xsl:when test="$level=2">
	  <fo:block-container>
	    <fo:block-container>
	      <fo:block xsl:use-attribute-sets="section.title.level2.properties">
		<xsl:copy-of select="$title"/>
	      </fo:block>
	    </fo:block-container>

	    <fo:block-container position="absolute" left="17.1cm">
	      <fo:block>
		<fo:basic-link external-destination="url('http://www.univention.{$url_toplevel}/feedback?manual={$sectionid}')"
			       color="blue" text-decoration="underline">
		  <fo:external-graphic src="url(illustrations/manual-feedback-button.svg)" width="auto" height="auto" content-width="auto"  content-height="16px" content-type="content-type:image/svg+xml"/>
		</fo:basic-link>
	      </fo:block>
	    </fo:block-container>
	  </fo:block-container>
	</xsl:when>

	<xsl:when test="$level=3">
	  <fo:block-container>
	    <fo:block-container>
	      <fo:block xsl:use-attribute-sets="section.title.level3.properties">
		<xsl:copy-of select="$title"/>
	      </fo:block>
	    </fo:block-container>

	    <fo:block-container position="absolute" left="17.1cm">
	      <fo:block>
		<fo:basic-link external-destination="url('http://www.univention.{$url_toplevel}/feedback?manual={$sectionid}')"
			       color="blue" text-decoration="underline">
		  <fo:external-graphic src="url(illustrations/manual-feedback-button.svg)" width="auto" height="auto" content-width="auto"  content-height="16px" content-type="content-type:image/svg+xml"/>
		</fo:basic-link>
	      </fo:block>
	    </fo:block-container>
	  </fo:block-container>
	</xsl:when>

	<xsl:when test="$level=4">
	  <fo:block-container>
	    <fo:block-container>
	      <fo:block xsl:use-attribute-sets="section.title.level4.properties">
		<xsl:copy-of select="$title"/>
	      </fo:block>
	    </fo:block-container>

	    <fo:block-container position="absolute" left="17.1cm">
	      <fo:block>
		<fo:basic-link external-destination="url('http://www.univention.{$url_toplevel}/feedback?manual={$sectionid}')"
			       color="blue" text-decoration="underline">
		  <fo:external-graphic src="url(illustrations/manual-feedback-button.svg)" width="auto" height="auto" content-width="auto"  content-height="16px" content-type="content-type:image/svg+xml"/>
		</fo:basic-link>
	      </fo:block>
	    </fo:block-container>
	  </fo:block-container>
	</xsl:when>

	<xsl:when test="$level=5">
	  <fo:block-container>
	    <fo:block-container>
	      <fo:block xsl:use-attribute-sets="section.title.level5.properties">
		<xsl:copy-of select="$title"/>
	      </fo:block>
	    </fo:block-container>

	    <fo:block-container position="absolute" left="17.1cm">
	      <fo:block>
		<fo:basic-link external-destination="url('http://www.univention.{$url_toplevel}/feedback?manual={$sectionid}')"
			       color="blue" text-decoration="underline">
		  <fo:external-graphic src="url(illustrations/manual-feedback-button.svg)" width="auto" height="auto" content-width="auto"  content-height="16px" content-type="content-type:image/svg+xml"/>
		</fo:basic-link>
	      </fo:block>
	    </fo:block-container>
	  </fo:block-container>
	</xsl:when>

	<xsl:otherwise>
	  <fo:block-container>
	    <fo:block-container>
	      <fo:block xsl:use-attribute-sets="section.title.level6.properties">
		<xsl:copy-of select="$title"/>
	      </fo:block>
	    </fo:block-container>

	    <fo:block-container position="absolute" left="17.1cm">
	      <fo:block>
		<fo:basic-link external-destination="url('http://www.univention.{$url_toplevel}/feedback?manual={$sectionid}')"
			       color="blue" text-decoration="underline">
		  <fo:external-graphic src="url(illustrations/manual-feedback-button.svg)" width="auto" height="auto" content-width="auto"  content-height="16px" content-type="content-type:image/svg+xml"/>
		</fo:basic-link>
	      </fo:block>
	    </fo:block-container>
	  </fo:block-container>
	</xsl:otherwise>
      </xsl:choose>
    </fo:block>
  </xsl:template>

  <!-- http://www.sagehill.net/docbookxsl/FittingText.html -->
  <xsl:param name="hyphenate.verbatim" select="0"/>
  <!-- PMH 2013-05-03: hyphenate.verbatim + hyphenation-character only works with fop-1.1, but then minus characters and page numbers get broken -->
  <xsl:attribute-set name="monospace.verbatim.properties" use-attribute-sets="verbatim.properties monospace.properties">
    <xsl:attribute name="text-align">start</xsl:attribute>
    <xsl:attribute name="wrap-option">wrap</xsl:attribute>
    <xsl:attribute name="background-color">#E0E0E0</xsl:attribute>
  </xsl:attribute-set>

</xsl:stylesheet>
<!-- vim: set ts=8 sw=2 et: -->
