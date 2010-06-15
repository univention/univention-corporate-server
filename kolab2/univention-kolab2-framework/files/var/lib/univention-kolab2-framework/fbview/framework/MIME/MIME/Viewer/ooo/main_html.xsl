<!--

   The Contents of this file are made available subject to the terms of
   either of the following licenses

          - GNU Lesser General Public License Version 2.1
          - Sun Industry Standards Source License Version 1.1

   Sun Microsystems Inc., October, 2000

   GNU Lesser General Public License Version 2.1
   =============================================
   Copyright 2000 by Sun Microsystems, Inc.
   901 San Antonio Road, Palo Alto, CA 94303, USA

   This library is free software; you can redistribute it and/or
   modify it under the terms of the GNU Lesser General Public
   License version 2.1, as published by the Free Software Foundation.

   This library is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   Lesser General Public License for more details.

   You should have received a copy of the GNU Lesser General Public
   License along with this library; if not, write to the Free Software
   Foundation, Inc., 59 Temple Place, Suite 330, Boston,
   MA  02111-1307  USA


   Sun Industry Standards Source License Version 1.1
   =================================================
   The contents of this file are subject to the Sun Industry Standards
   Source License Version 1.1 (the "License"); You may not use this file
   except in compliance with the License. You may obtain a copy of the
   License at http://www.openoffice.org/license.html.

   Software provided under this License is provided on an "AS IS" basis,
   WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING,
   WITHOUT LIMITATION, WARRANTIES THAT THE SOFTWARE IS FREE OF DEFECTS,
   MERCHANTABLE, FIT FOR A PARTICULAR PURPOSE, OR NON-INFRINGING.
   See the License for the specific provisions governing your rights and
   obligations concerning the Software.

   The Initial Developer of the Original Code is: Sun Microsystems, Inc.

   Copyright © 2002 by Sun Microsystems, Inc.

   All Rights Reserved.

   Contributor(s): _______________________________________

-->
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:office="http://openoffice.org/2000/office"
                xmlns:style="http://openoffice.org/2000/style"
                xmlns:text="http://openoffice.org/2000/text"
                xmlns:table="http://openoffice.org/2000/table"
                xmlns:draw="http://openoffice.org/2000/drawing"
                xmlns:fo="http://www.w3.org/1999/XSL/Format"
                xmlns:xlink="http://www.w3.org/1999/xlink"
                xmlns:number="http://openoffice.org/2000/datastyle"
                xmlns:svg="http://www.w3.org/2000/svg"
                xmlns:chart="http://openoffice.org/2000/chart"
                xmlns:dr3d="http://openoffice.org/2000/dr3d"
                xmlns:math="http://www.w3.org/1998/Math/MathML"
                xmlns:form="http://openoffice.org/2000/form"
                xmlns:script="http://openoffice.org/2000/script"
                office:class="text"
                office:version="1.0"
                xmlns:dc="http://purl.org/dc/elements/1.1/"
                xmlns:meta="http://openoffice.org/2000/meta"
                xmlns:config="http://openoffice.org/2001/config"
                xmlns:help="http://openoffice.org/2000/help"
                xmlns:xt="http://www.jclark.com/xt"
                xmlns:system="http://www.jclark.com/xt/java/java.lang.System"
                xmlns:urlencoder="http://www.jclark.com/xt/java/java.net.URLEncoder"
                xmlns:xalan="http://xml.apache.org/xalan"
                xmlns:java="http://xml.apache.org/xslt/java"
                exclude-result-prefixes="java">

    <xsl:output method      ="xml"
                encoding    ="UTF-8"
                indent      ="yes"/>



    <!--+++++ INCLUDED XSL MODULES +++++-->
    <!-- inherited style properties will be collected and written in a CSS header (CSS) -->
    <xsl:include href="style_header.xsl"/>

    <!-- inherited style properties will be collected and written as html properties in a temporary variable (HTML4, PALM) -->
    <xsl:include href="style_inlined.xsl"/>

    <!-- our xml style properties will be mapped to CSS and HTML4.x properties -->
    <xsl:include href="style_mapping.xsl"/>

    <!-- common element handling -->
    <xsl:include href="common.xsl"/>

    <!-- table handling -->
    <xsl:include href="table.xsl"/>

    <!-- palm handling -->
    <xsl:include href="palm.xsl"/>

    <!-- global document handling -->
    <xsl:include href="global_document.xsl"/>







    <!--+++++ PARAMETER FROM THE APPLICATION AND GLOBAL VARIABLES +++++-->

    <!-- MANDATORY: URL of meta stream -->
    <xsl:param name="metaFileURL"/>

    <!-- MANDATORY: URL of styles stream -->
    <xsl:param name="stylesFileURL"/>

    <!-- MANDATORY: for resolving relative links
        For resolving realtive links to the packed SO document, i.e. the path/URL of the jared sxw file (e.g. meta.xml, styles.xml, links to graphics in a relative directory) -->
    <xsl:param name="absoluteSourceDirRef"/>

    <!-- OPTIONAL (mandatory, when when source is compressed): Necessary for the in the packed OO document embedded files (mostly graphics from the compressed /Picture dir).
         When the OpenOffice (OO) file has been unpacked the absoluteSoureDirRef can be taken,
         Otherwise, a JAR URL could be choosen or when working with OpenOffice a so called Package-URL encoded over HTTP can be used to
         access the jared contents of the the jared document. . -->
    <xsl:param name="jaredRootURL" select="$absoluteSourceDirRef"/>

    <!-- OPTIONAL (mandatory, when used in session based environment)
         Useful for WebApplications: if a HTTP session is not cookie based, URL rewriting is beeing used (the session is appended to the URL).
         This URL session is used when creating links to graphics by XSLT. Otherwise the user havt to log again in for every graphic he would like to see. -->
    <xsl:param name="optionalURLSuffix"/>

    <!-- OPTIONAL: DPI (dots per inch) the standard solution of given pictures (necessary for the conversion of 'cm' into 'pixel')-->
    <!-- Although many pictures have the 96 dpi resolution, a higher resoltion give better results for common browsers -->
    <xsl:param name="dpi" select="96"/>

    <!-- OPTIONAL: in case of using a different processor than a JAVA XSLT, you can unable the Java functionality
         (i.e. debugging time and encoding chapter names for the content-table as href and anchors ) -->
    <xsl:param name="disableJava"    select="false"/>
    <xsl:param name="isJavaDisabled" select="boolean($disableJava)"/>

    <!-- OPTIONAL: user-agent will be differntiated by this parameter given by application (e.g. java servlet)-->
    <xsl:param name="outputType" select="'CSS_HEADER'"/>
    <!-- set of possible deviceTyps (WML is set in its own startfile main_wml.xsl):
    <xsl:param name="outputType" select="'CSS_HEADER'"/>
    <xsl:param name="outputType" select="'CSS_INLINED'"/>
    <xsl:param name="outputType" select="'PALM'"/> -->

    <!-- OPTIONAL: for activating the debug mode set the variable here to 'true()' or give any value from outside -->
    <xsl:param name="debug"         select="false"/>
    <xsl:param name="isDebugMode"   select="boolean($debug)"/>

<!-- *************************************************************************
    OPTIONAL: NEEDED IN CONNECTION WITH A GLOBAL DOCUMENT -->

    <!--SUMMARY:
         following parameter triggers a (quite time consuming) enabling of bookmarks in the table-of-content.
        IN DETAIL:
         Currently some links used in the Office XML (e.g. in the content table as '#7.Some%20Example%20Headline%7Outline')
         is not a valid URL (cmp. bug id# 102311). No file destination is specified nor exist any anchor element for these
         links in the Office XML.
         A workaround for this transformation therefore had to be made. This time-consuming mechanism is disabled by default and
         can be activated by a parameter (i.e. 'disableLinkedTableOfContent'). A creation of an anchor is made for each header element.
         All header titles gonna be encoding to be usable in a relative URL.    -->
    <xsl:param name="disableLinkedTableOfContent" select="false()"/>

    <!-- The chapter numbers of the current document (as a sequence of a global document) is dependent of the number
        of chapter of the same level in preceding documents. -->
    <xsl:param name="precedingChapterLevel1"  select="0"/>
    <xsl:param name="precedingChapterLevel2"  select="0"/>
    <xsl:param name="precedingChapterLevel3"  select="0"/>
    <xsl:param name="precedingChapterLevel4"  select="0"/>
    <xsl:param name="precedingChapterLevel5"  select="0"/>
    <xsl:param name="precedingChapterLevel6"  select="0"/>
    <xsl:param name="precedingChapterLevel7"  select="0"/>
    <xsl:param name="precedingChapterLevel8"  select="0"/>
    <xsl:param name="precedingChapterLevel9"  select="0"/>
    <xsl:param name="precedingChapterLevel10" select="0"/>

    <!-- XML documents containing a table of contents,
        gonna link for usability reason above each chapter to the preceding and following document and the content table -->
    <xsl:param name="contentTableURL"/>

    <!-- Needed for the bug workaround of missing content table links
        by this ambigous HTML references from the content table can be evoided-->
    <xsl:param name="globalDocumentRefToCurrentFile"/>

    <!-- Needed for the bug workaround of missing content table links
        by this node-set the relation between content-table link and children document header can be unambigous established -->
    <xsl:param name="contentTableHeadings"/>


<!-- END OF GLOBAL DOCUMENT SECTION
*************************************************************************-->



    <!-- works for normal separated zipped xml files as for flat filter single xml file format as well -->
    <xsl:variable name="office:meta-file"           select="document($metaFileURL)"/>
    <xsl:variable name="office:styles-file"         select="document($stylesFileURL)"/>
    <xsl:variable name="office:font-decls"          select="$office:styles-file/*/office:font-decls"/>
    <xsl:variable name="office:styles"              select="$office:styles-file/*/office:styles"/>
    <!-- office:automatic-styles may occure in two different files (i.d. content.xml and styles.xml). Furthermore the top level tag is different in a flat xml file -->
    <xsl:variable name="office:automatic-styles"    select="/*/office:automatic-styles"/>

    <!-- simple declaration of WML used to avoid parser errors -->
    <xsl:variable name="wap-paragraph-elements-without-table-row"/>
    <xsl:variable name="wap-paragraph-elements"/>
    <xsl:template name="wml-repeat-write-row"/>


    <!-- ************************************* -->
    <!-- *** build the propriate HTML file *** -->
    <!-- ************************************* -->

    <xsl:template match="/">

        <!--<xsl:message>


        Entered the styleSheets, transformation begins... </xsl:message>-->

        <xsl:choose>
            <xsl:when test="$isDebugMode">
                <xsl:call-template name="check-parameter"/>

                <xsl:if test="not($isJavaDisabled)">
                    <xsl:call-template name="debug-style-collecting-time"/>
                </xsl:if>
            </xsl:when>
            <xsl:otherwise>
                <!-- to access the variable like a node-set it is necessary to convert it
                     from a result-tree-fragment (RTF) to a node set using the James Clark extension -->
                <xsl:variable name="collectedGlobalData-RTF">
                    <xsl:call-template name='create-all-inline-styles'/>
                </xsl:variable>

                <xsl:choose>
                    <xsl:when test="function-available('xt:node-set')">
                        <xsl:call-template name="start">
                            <xsl:with-param name="collectedGlobalData" select="xt:node-set($collectedGlobalData-RTF)"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:when test="function-available('xalan:nodeset')">
                        <xsl:call-template name="start">
                            <xsl:with-param name="collectedGlobalData" select="xalan:nodeset($collectedGlobalData-RTF)"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:element name="NodeSetFunctionNotAvailable"/>
                        <xsl:call-template name="start"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="start">
        <xsl:param name="collectedGlobalData"/>

        <xsl:choose>
            <!--+++++ CSS (CASCADING STLYE SHEET) HEADER STYLE WAY +++++-->
            <xsl:when test="$outputType = 'CSS_HEADER'">
                <xsl:element name="html">
                    <xsl:element name="head">
                        <xsl:if test="$isDebugMode"><xsl:message>CSS helper variable will be created....</xsl:message></xsl:if>
                        <xsl:call-template name='common-header-properties'/>
                        <xsl:if test="$isDebugMode"><xsl:message>CSS variable ready, header will be created....</xsl:message></xsl:if>
                        <!-- constructing the css header simulating inheritance of style-families by style order -->
                        <xsl:call-template name='create-css-styleheader'/>
                        <xsl:if test="$isDebugMode"><xsl:message>CSS header creation finished!</xsl:message></xsl:if>
                    </xsl:element>



                    <xsl:variable name="backgroundImageURL" select="$office:automatic-styles/style:page-master/style:properties/style:background-image/@xlink:href"/>
                    <xsl:element name="body">
                        <!-- background image -->
                        <xsl:if test="$backgroundImageURL">
                            <xsl:attribute name="background">
                                <xsl:choose>
                                    <!-- for images jared in open office document -->
                                    <xsl:when test="contains($backgroundImageURL, '#Pictures/')">
                                        <!-- creating an absolute http URL to the contained/packed image file -->
                                        <xsl:value-of select="concat($jaredRootURL, '/Pictures/', substring-after($backgroundImageURL, '#Pictures/'), $optionalURLSuffix)"/>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:attribute name="src"><xsl:value-of select="$backgroundImageURL"/></xsl:attribute>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:attribute>
                        </xsl:if>

                        <!-- processing the content of the xml file -->
                        <xsl:apply-templates select="/*/office:body">
                            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                        </xsl:apply-templates>
                    </xsl:element>

                </xsl:element>
            </xsl:when>

            <!--+++++ HTML 4.0 INLINING  +++++-->
            <xsl:when test="$outputType = 'CSS_INLINED'">
                <xsl:element name="html">
                    <xsl:element name="head">
                        <xsl:call-template name='common-header-properties'/>
                    </xsl:element>

                    <xsl:variable name="backgroundImageURL" select="$office:automatic-styles/style:page-master/style:properties/style:background-image/@xlink:href"/>
                    <xsl:element name="body">
                        <!-- background image -->
                        <xsl:if test="$backgroundImageURL">
                            <xsl:attribute name="background">
                                <xsl:choose>
                                    <!-- for images jared in open office document -->
                                    <xsl:when test="contains($backgroundImageURL, '#Pictures/')">
                                        <!-- creating an absolute http URL to the contained/packed image file -->
                                        <xsl:value-of select="concat($jaredRootURL, '/Pictures/', substring-after($backgroundImageURL, '#Pictures/'), $optionalURLSuffix)"/>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:attribute name="src"><xsl:value-of select="$backgroundImageURL"/></xsl:attribute>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:attribute>
                        </xsl:if>
                        <xsl:apply-templates select="/*/office:body">
                            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                        </xsl:apply-templates>
                    </xsl:element>
                </xsl:element>
            </xsl:when>

            <!--+++++ PALM-VII (3.2 HTML SUBSET)  +++++-->
            <xsl:when test="$outputType = 'PALM'">
                <!-- the proxy will convert the html file later to PQA -->
                <xsl:element name="html">
                    <xsl:element name="head">
                        <xsl:call-template name='palm-header-properties'/>
                    </xsl:element>

                    <xsl:element name="body">
                        <!-- processing the content of the xml file -->
                        <xsl:apply-templates select="/*/office:body">
                            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                        </xsl:apply-templates>
                    </xsl:element>
                </xsl:element>
            </xsl:when>
        </xsl:choose>
    </xsl:template>



    <!-- ********************************************* -->
    <!-- *** Header for CSS_INLINED and CSS_HEADER *** -->
    <!-- ********************************************* -->

    <xsl:template name='common-header-properties'>
        <xsl:apply-templates select="$office:meta-file/*/office:meta/dc:title"/>
        <xsl:apply-templates select="$office:meta-file/*/office:meta/dc:description"/>
<!--2DO add further header elements..
        <xsl:apply-templates select="$office:meta-file/*/office:meta/dc:subject"/>
        <xsl:apply-templates select="$office:meta-file/*/office:meta/meta:keywords[postition()=1]"/>-->
    </xsl:template>

    <xsl:template match="dc:title">
        <xsl:element name="title">
            <xsl:value-of select="."/>
        </xsl:element>
    </xsl:template>

    <xsl:template match="dc:description">
        <xsl:element name="meta">
            <xsl:attribute name="name">
                <xsl:text>description</xsl:text>
            </xsl:attribute>
            <xsl:attribute name="content">
                <xsl:value-of select="."/>
            </xsl:attribute>
        </xsl:element>
    </xsl:template>


    <!-- ********************************************* -->
    <!-- *** Measuring the time for style creating *** -->
    <!-- ********************************************* -->


    <xsl:template name="debug-style-collecting-time">

        <xsl:variable name="startTime-RTF">
            <xsl:choose>
                <xsl:when test="function-available('system:current-time-millis')">
                    <xsl:value-of select="system:current-time-millis()"/>
                </xsl:when>
                <xsl:when test="function-available('java:java.lang.System.currentTimeMillis')">
                    <xsl:value-of select="java:java.lang.System.currentTimeMillis()"/>
                </xsl:when>
            </xsl:choose>
        </xsl:variable>



        <xsl:variable name="collectedGlobalData-RTF">
            <xsl:call-template name='create-all-inline-styles'/>
        </xsl:variable>


        <xsl:choose>
            <xsl:when test="function-available('xt:node-set')">
                <xsl:message>Creating the inline styles....</xsl:message>
                <xsl:variable name="startTime"              select="number(xt:node-set($startTime-RTF))"/>
                <xsl:variable name="collectedGlobalData"    select="xt:node-set($collectedGlobalData-RTF)"/>
                <xsl:variable name="endTime"                select="system:current-time-millis()"/>

                <xsl:message>Time for instantiating style variable: <xsl:value-of select="($endTime - $startTime)"/> ms</xsl:message>
                <xsl:call-template name="start">
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="function-available('xalan:nodeset')">
                <xsl:message>Creating the inline styles....</xsl:message>
                <xsl:variable name="startTime"              select="number(xalan:nodeset($startTime-RTF))"/>
                <xsl:variable name="endTime"                select="java:java.lang.System.currentTimeMillis()"/>
                <xsl:variable name="collectedGlobalData"    select="xalan:nodeset($collectedGlobalData-RTF)"/>

                <xsl:message>Time for instantiating style variable: <xsl:value-of select="($endTime - $startTime)"/> ms</xsl:message>
                <xsl:call-template name="start">
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>

    </xsl:template>

    <!-- DEBUG purpose only: checking the parameters of this template-->
    <xsl:template name="check-parameter">
        <xsl:message>Parameter dpi: <xsl:value-of select="$dpi"/></xsl:message>
        <xsl:message>Parameter metaFileURL: <xsl:value-of select="$metaFileURL"/></xsl:message>
        <xsl:message>Parameter stylesFileURL: <xsl:value-of select="$stylesFileURL"/></xsl:message>
        <xsl:message>Parameter absoluteSourceDirRef: <xsl:value-of select="$absoluteSourceDirRef"/></xsl:message>
        <xsl:message>Parameter precedingChapterLevel1 : <xsl:value-of select="$precedingChapterLevel1"/></xsl:message>
        <xsl:message>Parameter precedingChapterLevel2 : <xsl:value-of select="$precedingChapterLevel2"/></xsl:message>
        <xsl:message>Parameter precedingChapterLevel3 : <xsl:value-of select="$precedingChapterLevel3"/></xsl:message>
        <xsl:message>Parameter precedingChapterLevel4 : <xsl:value-of select="$precedingChapterLevel4"/></xsl:message>
        <xsl:message>Parameter precedingChapterLevel5 : <xsl:value-of select="$precedingChapterLevel5"/></xsl:message>
        <xsl:message>Parameter precedingChapterLevel6 : <xsl:value-of select="$precedingChapterLevel6"/></xsl:message>
        <xsl:message>Parameter precedingChapterLevel7 : <xsl:value-of select="$precedingChapterLevel7"/></xsl:message>
        <xsl:message>Parameter precedingChapterLevel8 : <xsl:value-of select="$precedingChapterLevel8"/></xsl:message>
        <xsl:message>Parameter precedingChapterLevel9 : <xsl:value-of select="$precedingChapterLevel9"/></xsl:message>
        <xsl:message>Parameter precedingChapterLevel10: <xsl:value-of select="$precedingChapterLevel10"/></xsl:message>
    </xsl:template>

</xsl:stylesheet>
