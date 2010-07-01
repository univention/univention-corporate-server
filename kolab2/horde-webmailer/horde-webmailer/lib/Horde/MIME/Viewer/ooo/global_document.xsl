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
                extension-element-prefixes="xt"
                xmlns:urlencoder="http://www.jclark.com/xt/java/java.net.URLEncoder"
                xmlns:sxghelper="http://www.jclark.com/xt/java/com.sun.star.xslt.helper.SxgChildTransformer"
                xmlns:xalan="http://xml.apache.org/xalan"
                xmlns:java="http://xml.apache.org/xslt/java"
                exclude-result-prefixes="java">




    <!-- ********************************************** -->
    <!-- *** Global Document -  Table of Content    *** -->
    <!-- ********************************************** -->



    <xsl:template match="text:table-of-content">
        <xsl:param name="collectedGlobalData"/>

        <xsl:apply-templates>
            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
        </xsl:apply-templates>
    </xsl:template>



    <xsl:template match="text:index-body">
        <xsl:param name="collectedGlobalData"/>

        <xsl:apply-templates mode="content-table">
            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
        </xsl:apply-templates>
    </xsl:template>



    <xsl:template match="text:index-title" mode="content-table">
        <xsl:param name="collectedGlobalData"/>

        <xsl:apply-templates>
            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
        </xsl:apply-templates>
    </xsl:template>

    <xsl:template match="text:reference-ref">
        <xsl:param name="collectedGlobalData"/>

        <!-- Java is needed as we have to encode the relative links (bug#102311) -->
        <xsl:if test="not($isJavaDisabled)">
            <xsl:element name="a">
                <xsl:attribute name="href">
                    <xsl:text>#</xsl:text>
                    <xsl:call-template name="encode-string">
                        <!-- the space has to be normalized,
                            otherwise an illegal argument exception will be thrown for XT-->
                         <xsl:with-param name="textToBeEncoded" select="@text:ref-name"/>
                    </xsl:call-template>
                </xsl:attribute>

                <xsl:apply-templates>
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                </xsl:apply-templates>

            </xsl:element>
        </xsl:if>
    </xsl:template>

    <xsl:template match="text:reference-mark">
        <xsl:param name="collectedGlobalData"/>

        <!-- Java is needed as we have to encode the relative links (bug#102311) -->
        <xsl:if test="not($isJavaDisabled)">
            <xsl:element name="a">
                <xsl:attribute name="name">
                    <xsl:call-template name="encode-string">
                        <!-- the space has to be normalized,
                            otherwise an illegal argument exception will be thrown for XT-->
                        <xsl:with-param name="textToBeEncoded" select="@text:name"/>
                    </xsl:call-template>
                </xsl:attribute>

                <xsl:apply-templates>
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                </xsl:apply-templates>

            </xsl:element>
        </xsl:if>
    </xsl:template>



    <xsl:template match="text:reference-mark-start">
        <xsl:param name="collectedGlobalData"/>

        <!-- Java is needed as we have to encode the relative links (bug#102311) -->
        <xsl:if test="not($isJavaDisabled)">
            <xsl:element name="a">
                <xsl:attribute name="name">
                    <xsl:call-template name="encode-string">
                        <!-- the space has to be normalized,
                            otherwise an illegal argument exception will be thrown for XT-->
                        <xsl:with-param name="textToBeEncoded" select="@text:name"/>
                    </xsl:call-template>
                </xsl:attribute>

                <xsl:variable name="endOfReference">
                    <xsl:for-each select="text:reference-mark-end[@name=current()/@text:name]">
                        <xsl:value-of select="position()"/>
                    </xsl:for-each>
                </xsl:variable>

                <xsl:for-each select="following-sibling::*[position() &lt; $endOfReference]">
                    <xsl:apply-templates>
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    </xsl:apply-templates>
                </xsl:for-each>
            </xsl:element>
       </xsl:if>
    </xsl:template>




     <!-- content table link  -->
    <xsl:template match="text:a" mode="content-table">
        <xsl:param name="collectedGlobalData"/>


        <!-- For anchors in content-headers a bug exists (cp. bug id# 102311) and they have to be worked out separately.
            Currently the link used in the content-table of an Office XML (e.g. in the content table as '#7.Some%20Example%20Headline%7Outline')
            is not a valid URL (cp. bug id# 102311). No file destination is specified nor exist any anchor element for these
            links in the Office XML, nor is the chapter no. known in the linked files.
            A workaround for this transformation therefore had to be made. This time-consuming mechanism is disabled by default and
            can be activated by a parameter (i.e. 'disableLinkedTableOfContent'). A creation of an anchor is made for each header element.
            All header titles gonna be encoding to be usable in a relative URL. -->
        <xsl:choose>
            <xsl:when test="$disableLinkedTableOfContent or $isJavaDisabled">
                <xsl:call-template name="create-common-link">
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="create-content-table-link">
                    <xsl:with-param name="collectedGlobalData"       select="$collectedGlobalData"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>



    <xsl:template name="get-absolute-chapter-no">
        <xsl:param name="collectedGlobalData"/>
        <xsl:param name="precedingChapterLevel1"/>

        <xsl:choose>
            <xsl:when test="$globalDocumentRefToCurrentFile">

                <xsl:variable name="currentFileHeadingNo">
                    <xsl:call-template name="get-current-file-heading-no"/>
                </xsl:variable>
                <xsl:variable name="testResult" select="$contentTableHeadings/heading[$globalDocumentRefToCurrentFile = @file-url][number($currentFileHeadingNo)]"/>

                <xsl:call-template name="get-global-heading-no">
                    <xsl:with-param name="currentFileHeadingNo" select="translate($testResult/@absolute-chapter-level, '+', '.')"/>
                    <xsl:with-param name="precedingChapterLevel1" select="$precedingChapterLevel1"/>
                </xsl:call-template>

           </xsl:when>
           <xsl:otherwise>
                <!-- When the chapter is in the global document itself the link has to be relative (e.g. #index) a absolute href does not
                    work with the browser. In case of chapter in the global document, the output URL of the global document was taken. -->
                <xsl:variable name="currentFileHeadingNo">
                    <xsl:call-template name="get-current-file-heading-no"/>
                </xsl:variable>
                <xsl:variable name="testResult" select="$collectedGlobalData/content-table-headings/heading[$contentTableURL = @file-url][number($currentFileHeadingNo)]"/>

                <xsl:call-template name="get-global-heading-no">
                    <xsl:with-param name="currentFileHeadingNo" select="translate($testResult/@absolute-chapter-level, '+', '.')"/>
                    <xsl:with-param name="precedingChapterLevel1" select="$precedingChapterLevel1"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


    <xsl:template name="get-current-file-heading-no">
        <xsl:choose>
            <xsl:when test="function-available('sxghelper:get-current-child-heading-no')">
                <xsl:value-of select="sxghelper:get-current-child-heading-no()"/>
            </xsl:when>
            <xsl:when test="function-available('java:com.sun.star.xslt.helper.SxgChildTransformer.getCurrentChildHeadingNo')">
                <xsl:value-of select="java:com.sun.star.xslt.helper.SxgChildTransformer.getCurrentChildHeadingNo()"/>
            </xsl:when>
        </xsl:choose>
    </xsl:template>


    <xsl:template name="get-next-current-file-heading-no">
        <xsl:param name="file"/>
        <xsl:choose>
            <xsl:when test="function-available('sxghelper:get-next-current-child-heading-no')">
                <xsl:value-of select="sxghelper:get-next-current-child-heading-no($file)"/>
            </xsl:when>
            <xsl:when test="function-available('java:com.sun.star.xslt.helper.SxgChildTransformer.getNextCurrentChildHeadingNo')">
                <xsl:value-of select="java:com.sun.star.xslt.helper.SxgChildTransformer.getNextCurrentChildHeadingNo($file)"/>
            </xsl:when>
        </xsl:choose>
    </xsl:template>


    <xsl:template name="get-global-heading-no">
        <xsl:param name="currentFileHeadingNo"/>
        <xsl:param name="precedingChapterLevel1"/>

        <xsl:choose>
            <xsl:when test="function-available('sxghelper:get-global-heading-no')">
                <xsl:value-of select="sxghelper:get-global-heading-no(string($currentFileHeadingNo), number($precedingChapterLevel1))"/>
            </xsl:when>
            <xsl:when test="function-available('java:com.sun.star.xslt.helper.SxgChildTransformer.getGlobalHeadingNo')">
                <xsl:value-of select="java:com.sun.star.xslt.helper.SxgChildTransformer.getGlobalHeadingNo(string($currentFileHeadingNo), number($precedingChapterLevel1))"/>
            </xsl:when>
        </xsl:choose>
    </xsl:template>




    <!-- necessary as anchor for the content table -->
    <xsl:template name="create-heading-anchor">
        <xsl:param name="collectedGlobalData"/>

        <!--
        Currently the link used in the Office XML (e.g. in the content table as '#7.Some%20Example%20Headline%7Outline')
        is not a valid URL (cmp. bug id# 102311). No file destination is specified nor exist any anchor element for these
        links in the Office XML.
        Here we are creating an anchor with the space normalized text of this header as potential jump address of the content table -->

        <xsl:choose>
            <xsl:when test="$globalDocumentRefToCurrentFile">

                <xsl:variable name="currentFileHeadingNo">
                    <xsl:call-template name="get-next-current-file-heading-no">
                         <xsl:with-param name="file" select="$globalDocumentRefToCurrentFile"/>
                    </xsl:call-template>
                </xsl:variable>


                <xsl:variable name="testResult" select="$contentTableHeadings/heading[$globalDocumentRefToCurrentFile = @file-url][number($currentFileHeadingNo)]"/>
                <xsl:if test="$isDebugMode">
                    <xsl:message>Matching child document header No. <xsl:value-of select="$currentFileHeadingNo"/></xsl:message>
                    <xsl:message>absolute-chapter-level:         <xsl:value-of select="$testResult/@absolute-chapter-level"/></xsl:message>
                    <xsl:message>encodedTitle:                   <xsl:value-of select="$testResult/@encoded-title"/></xsl:message>
                    <xsl:message>globalDocumentRefToCurrentFile: <xsl:value-of select="$globalDocumentRefToCurrentFile"/></xsl:message>
                    <xsl:message>*** </xsl:message>
                </xsl:if>

                <xsl:element name="a">
                    <xsl:attribute name="name">
                        <xsl:value-of select="$testResult/@absolute-chapter-level"/>
                        <xsl:text>+</xsl:text>
                        <xsl:value-of select="$testResult/@encoded-title"/>
                    </xsl:attribute>
                </xsl:element>
           </xsl:when>

           <xsl:otherwise>
                <!-- When the chapter is in the global document itself the link has to be relative (e.g. #index) a absolute href does not
                    work with the browser. In case of chapter in the global document, the output URL of the global document was taken. -->
                <xsl:variable name="currentFileHeadingNo">
                    <xsl:call-template name="get-next-current-file-heading-no">
                         <xsl:with-param name="file" select="$contentTableURL"/>
                    </xsl:call-template>
                </xsl:variable>


                <xsl:variable name="testResult" select="$collectedGlobalData/content-table-headings/heading[$contentTableURL = @file-url][number($currentFileHeadingNo)]"/>

                <xsl:if test="$isDebugMode">
                    <xsl:message>Matching global document header No. <xsl:value-of select="$currentFileHeadingNo"/></xsl:message>
                    <xsl:message>absolute-chapter-level:  <xsl:value-of select="$testResult/@absolute-chapter-level"/></xsl:message>
                    <xsl:message>encodedTitle:            <xsl:value-of select="$testResult/@encoded-title"/></xsl:message>
                    <xsl:message>contentTableURL:         <xsl:value-of select="$contentTableURL"/></xsl:message>
                    <xsl:message>*** </xsl:message>
                </xsl:if>

                <xsl:element name="a">
                    <xsl:attribute name="name">
                        <xsl:value-of select="$testResult/@absolute-chapter-level"/>
                        <xsl:text>+</xsl:text>
                        <xsl:value-of select="$testResult/@encoded-title"/>
                    </xsl:attribute>
                </xsl:element>

            </xsl:otherwise>
        </xsl:choose>



<!--

        <xsl:variable name="title" select="normalize-space(.)"/>
        <!~~DON'T WORK    <xsl:variable name="title" select="normalize-space(descendant::text())"/>        ~~>
         <xsl:choose>
            <xsl:when test="$globalDocumentRefToCurrentFile">
                <xsl:variable name="testResults" select="$contentTableHeadings/heading[$globalDocumentRefToCurrentFile = @file-url][$title = @title][current()/@text:level = @level]"/>
                <xsl:if test="1 &lt; count($testResults)">
                    <xsl:message> *** CAUTION: Multiple chapter headings with similar names: </xsl:message>
                    <xsl:message> *** Title: <xsl:value-of select="$title"/> Level: <xsl:value-of select="@text:level"/></xsl:message>
                </xsl:if>

                 <xsl:variable name="encodedTitle" select="$testResults/@encoded-title"/>
                 <xsl:choose>
                     <xsl:when test="$encodedTitle">
                         <xsl:element name="a">
                            <xsl:attribute name="name">
                                <xsl:value-of select="$encodedTitle"/>
                            </xsl:attribute>
                         </xsl:element>
                     </xsl:when>
                     <xsl:otherwise>
                        <!~~ even when it is not ~~>
                        <xsl:variable name="newEncodedTitle">
                            <xsl:call-template name="encode-string">
                                <!~~ the space has to be normalized,
                                    otherwise an illegal argument exception will be thrown for XT~~>
                                 <xsl:with-param name="textToBeEncoded" select="$title"/>
                            </xsl:call-template>
                        </xsl:variable>
                         <xsl:element name="a">
                            <xsl:attribute name="name">
                                <xsl:value-of select="$newEncodedTitle"/>
                            </xsl:attribute>
                         </xsl:element>
                     </xsl:otherwise>
                 </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:variable name="testResults" select="$collectedGlobalData/content-table-headings/heading[$contentTableURL = @file-url][$title = @title][current()/@text:level = @level]"/>
                <xsl:if test="1 &lt; count($testResults)">
                    <xsl:message> *** CAUTION: Multiple chapter headings with similar names: </xsl:message>
                    <xsl:message> *** Title: <xsl:value-of select="$title"/> Level: <xsl:value-of select="@text:level"/></xsl:message>
                    <xsl:message> *** </xsl:message>
                </xsl:if>

                <xsl:variable name="encodedTitle" select="$testResults/@encoded-title"/>
                <xsl:choose>
                     <xsl:when test="$encodedTitle">
                         <xsl:element name="a">
                            <xsl:attribute name="name">
                                <xsl:value-of select="$encodedTitle"/>
                            </xsl:attribute>
                         </xsl:element>
                     </xsl:when>
                     <xsl:otherwise>
                        <!~~ even when it is not ~~>
                        <xsl:variable name="newEncodedTitle">
                            <xsl:call-template name="encode-string">
                                <!~~ the space has to be normalized,
                                    otherwise an illegal argument exception will be thrown for XT~~>
                                 <xsl:with-param name="textToBeEncoded" select="$title"/>
                            </xsl:call-template>
                        </xsl:variable>
                         <xsl:element name="a">
                            <xsl:attribute name="name">
                                <xsl:value-of select="$newEncodedTitle"/>
                            </xsl:attribute>
                         </xsl:element>
                     </xsl:otherwise>
                 </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>

-->

    </xsl:template>




    <!-- ************************************** -->
    <!--    CREATION OF A CONTENT TABLE LINK    -->
    <!-- ************************************** -->


    <!-- a special behavior of text:a
        (called from the 'text:a' template) -->

    <xsl:template name="create-content-table-link">
        <xsl:param name="collectedGlobalData"/>

        <xsl:choose>
            <xsl:when test="not($outputType = 'WML')">
                <xsl:element name="a">
                    <xsl:attribute name="href">
                        <xsl:choose>
                            <xsl:when test="starts-with(@xlink:href, '#')">
                                <xsl:variable name="correctHeading" select="$collectedGlobalData/content-table-headings/heading[current()/@xlink:href = @content-table-id]"/>

                                <xsl:value-of select="$correctHeading/@out-file-url"/>
                                <xsl:text>#</xsl:text>
                                <xsl:value-of select="$correctHeading/@absolute-chapter-level"/>
                                <xsl:text>+</xsl:text>
                                <xsl:value-of select="$correctHeading/@encoded-title"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="create-common-link">
                                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                </xsl:call-template>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:attribute>

                    <xsl:call-template name="apply-styles-and-content">
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    </xsl:call-template>
                </xsl:element>
            </xsl:when>
            <xsl:otherwise>
                <!-- 2DO: currently no WML support

                <!~~ no nested p tags in wml1.1 allowed ~~>
                <xsl:choose>
                    <xsl:when test="ancestor::*[contains($wap-paragraph-elements, name())]">
                        <xsl:element name="a">
                            <xsl:attribute name="href"><xsl:value-of select="@xlink:href"/></xsl:attribute>
                            <xsl:apply-templates select="."/>
                        </xsl:element>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:element name="p">
                            <xsl:element name="a">
                                <xsl:attribute name="href"><xsl:value-of select="@xlink:href"/></xsl:attribute>
                                <xsl:apply-templates select="."/>
                            </xsl:element>
                        </xsl:element>
                    </xsl:otherwise>
                </xsl:choose>  -->
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


	<!--
	    CREATION OF A HELPER VARIABLE AS WORKAROUND FOR THE CONTENT TABLE ULR BUG


        As no valid URL from the content table to the child documents exist in the content table,
        a work-around is done:

        First two helper variables are being created.

        One containing the list of all references of the global document:
        containg all their title,
        for example:

          	<chapter-ref title="aTitle 1"/>
          	<chapter-ref title="aTitle 2"/>
          	<chapter-ref title="aTitle 2/>
          	<chapter-ref title="aTitle 3/>

        The other containing all heading from the child documents linked from the global document.
        The variable 'childrenHeadings' contains their title and the number of preceding similar titles,
        for example:


          	<child file-url="aURL">
          		<heading title="aTitle1" level="1">
          		<heading title="aTitle2" level="2">
          		<heading title="aTitle3" level="1">
            </child>

        For each chapter reference from the content table the

         by encoding the chapter names of the child document with the java URLEncoder and
        use this as a part of a link. Furthermore for all heading elements a encoded anchor will be created from the heading.
        Last the workaround parses all children documents for this anhor, as there is no distinction of files from the content table entries.

        The new added node set to the collectedGlobalData variable concering the content table is written as


		<content-table-headings content-table-url="aURL_ToTheGeneratedContentTable">
      		<heading file-url="aFileURLToTheGeneratedHeading1" level="1">
      		<heading file-url="aFileURLToTheGeneratedHeading2" level="2">
      		<heading file-url="aFileURLToTheGeneratedHeading1" level="1">
      		<heading file-url="aFileURLToTheGeneratedHeading2" level="2">
		</content-table-headings>


        Preconditions:
		The correct sequence of child documents according to the Content Table is necessary, granted by the office.
	-->
	<xsl:template name="Create-helper-variables-for-Content-Table">
        <xsl:param name="collectedGlobalData"/>

        <xsl:if test="$isDebugMode"><xsl:message>Creation of global document helper variable for the content table....</xsl:message></xsl:if>

        <!-- Here a helper variable of the content table is created, of all chapter-references which point to a child document.
             an 'chapter-ref' element will be created, containg their title and the number of preceding similar titles,
             for example:

              	<chapter-ref title="aTitle 1"/>
              	<chapter-ref title="aTitle 2"/>
              	<chapter-ref title="aTitle 2"/>
              	<chapter-ref title="aTitle 3"/>
            -->
        <xsl:variable name="chapterRefs-RTF">
            <!-- '/*/' as the flat and the zipped XML file format have different root elements -->
            <xsl:for-each select="/*/office:body/text:table-of-content/text:index-body/text:p/text:a">
                <xsl:variable name="currentTitle" select="normalize-space(string(.))"/>
                <xsl:element name="chapter-ref">
                    <xsl:attribute name="title">
                        <xsl:value-of select="$currentTitle"/>
                    </xsl:attribute>
                    <xsl:attribute name="content-table-id">
                        <xsl:value-of select="@xlink:href"/>
                    </xsl:attribute>
               </xsl:element>
            </xsl:for-each>
        </xsl:variable>
        <xsl:if test="$isDebugMode"><xsl:message>Finished the Creation of global document helper variable for the content table!</xsl:message></xsl:if>




        <xsl:if test="$isDebugMode"><xsl:message>Creation of global document helper variable for the child documents....</xsl:message></xsl:if>
        <!-- Here a helper variable of created from the children documents.
             Containg all heading elements from the child documents. Some or all of them are
             chapters referenced by the Global Document.
             The variable contains their title, the level of the heading and the file URL of the child,
             for example:

          		<heading title="aTitle1" level="1" file-url="aURL1">
          		<heading title="aTitle2" level="2" file-url="aURL1">
          		<heading title="aTitle3" level="1" file-url="aURL1">
          		<heading title="aTitle4" level="1" file-url="aURL2">
          		<heading title="aTitle5" level="2" file-url="aURL2">
          		<heading title="aTitle2" level="3" file-url="aURL2">
          		<heading title="aTitle6" level="3" file-url="aURL2">
                <heading-count>7</heading-count>
            -->
        <xsl:variable name="childrenHeadings-RTF">
            <!-- all headers from children documents will be added -->
            <xsl:apply-templates select="/*/office:body/text:section" mode="creation-of-variable"/>
        </xsl:variable>
        <xsl:if test="$isDebugMode"><xsl:message>Finished the Creation of global document helper variable for the child documents!</xsl:message></xsl:if>


        <xsl:choose>
            <xsl:when test="function-available('xt:node-set')">
                <xsl:call-template name="Create-global-variable-for-Content-Table">
                    <xsl:with-param name="chapterRefs"     select="xt:node-set($chapterRefs-RTF)"/>
                    <xsl:with-param name="childrenHeadings"     select="xt:node-set($childrenHeadings-RTF)"/>
                    <xsl:with-param name="collectedGlobalData"  select="$collectedGlobalData"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="function-available('xalan:nodeset')">
                <xsl:call-template name="Create-global-variable-for-Content-Table">
                    <xsl:with-param name="chapterRefs"     select="xalan:nodeset($chapterRefs-RTF)"/>
                    <xsl:with-param name="childrenHeadings"     select="xalan:nodeset($childrenHeadings-RTF)"/>
                    <xsl:with-param name="collectedGlobalData"  select="$collectedGlobalData"/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>




    <xsl:template name="Create-global-variable-for-Content-Table">
        <xsl:param name="chapterRefs"/>
        <xsl:param name="childrenHeadings"/>
        <xsl:param name="collectedGlobalData"/>


        <xsl:if test="$isDebugMode">
            <!-- helper variable collecting all headings from the global document file children-->
            <xsl:for-each select="$childrenHeadings/heading">
                <xsl:message>#              <xsl:value-of select="position()"/></xsl:message>
                <xsl:message>level:         <xsl:value-of select="@level"/></xsl:message>
                <xsl:message>title:         <xsl:value-of select="@title"/></xsl:message>
                <xsl:message>encoded-title: <xsl:value-of select="@encoded-title"/></xsl:message>
                <xsl:message>file-url:      <xsl:value-of select="@file-url"/></xsl:message>
                <xsl:message>header-no:     <xsl:value-of select="@header-no"/></xsl:message>
                <xsl:message>**</xsl:message>
            </xsl:for-each>
            <xsl:message>**</xsl:message>
            <xsl:message>**</xsl:message>

            <!-- helper variable collecting all heading references from the content table of the the global document -->
            <xsl:message>childrenHeadings/heading-count: <xsl:value-of select="$childrenHeadings/heading-count"/></xsl:message>
            <xsl:for-each select="$chapterRefs/chapter-ref">
                <xsl:message># <xsl:value-of select="position()"/></xsl:message>
                <xsl:message>title: <xsl:value-of select="@title"/></xsl:message>
                <xsl:message>**</xsl:message>
            </xsl:for-each>
        </xsl:if>


        <xsl:choose>
            <xsl:when test="function-available('sxghelper:set-heading-no')">
                    <xsl:value-of select="sxghelper:set-heading-no(1)"/>
                    <xsl:value-of select="sxghelper:set-current-child-no(1)"/>
                    <xsl:value-of select="sxghelper:set-current-child-url(string($childrenHeadings/heading/@file-url))"/>
            </xsl:when>
            <xsl:when test="function-available('java:com.sun.star.xslt.helper.SxgChildTransformer.setHeadingNo')">
                    <xsl:value-of select="java:com.sun.star.xslt.helper.SxgChildTransformer.setHeadingNo(1)"/>
                    <xsl:value-of select="java:com.sun.star.xslt.helper.SxgChildTransformer.setCurrentChildNo(1)"/>
                    <xsl:value-of select="java:com.sun.star.xslt.helper.SxgChildTransformer.setCurrentChildUrl(string($childrenHeadings/heading/@file-ur))"/>
            </xsl:when>
        </xsl:choose>

        <xsl:if test="$isDebugMode"><xsl:message>Creating global document variable for chapter relations....</xsl:message></xsl:if>
        <xsl:variable name="contentTableHeadingsGlobalData-RTF">
            <xsl:element name="content-table-headings">
                <!-- all headings are linked from the current global document input file -->
                <xsl:attribute name="content-table-url">
                    <xsl:value-of select="$contentTableURL"/>
                </xsl:attribute>

                <!-- had to use a for loop, as a recursion ends with an stackoverflow exception after about 600 recursive calls -->
                <xsl:choose>
                    <xsl:when test="function-available('sxghelper:get-heading-no')">
                         <xsl:for-each select="$chapterRefs/chapter-ref">
                            <xsl:call-template name="searchHeadingInChildDocument">
                                <xsl:with-param name="chapterRefs"         select="$chapterRefs"/>
                                <xsl:with-param name="childrenHeadings"    select="$childrenHeadings"/>
                                <xsl:with-param name="currentChapterRefNo" select="position()"/>
                                <xsl:with-param name="currentHeadingNo"    select="sxghelper:get-heading-no()"/>
                                <xsl:with-param name="currentChildURL"     select="sxghelper:get-current-child-url()"/>
                                <xsl:with-param name="currentChildNo"      select="sxghelper:get-current-child-no()"/>
                            </xsl:call-template>
                        </xsl:for-each>
                     </xsl:when>
                    <xsl:when test="function-available('java:com.sun.star.xslt.helper.SxgChildTransformer.getHeadingNo')">
                         <xsl:for-each select="$chapterRefs/chapter-ref">
                            <xsl:call-template name="searchHeadingInChildDocument">
                                <xsl:with-param name="chapterRefs"         select="$chapterRefs"/>
                                <xsl:with-param name="childrenHeadings"    select="$childrenHeadings"/>
                                <xsl:with-param name="currentChapterRefNo" select="position()"/>
                                <xsl:with-param name="currentHeadingNo"    select="java:com.sun.star.xslt.helper.SxgChildTransformer.getHeadingNo()"/>
                                <xsl:with-param name="currentChildURL"     select="java:com.sun.star.xslt.helper.SxgChildTransformer.getCurrentChildUrl()"/>
                                <xsl:with-param name="currentChildNo"      select="java:com.sun.star.xslt.helper.SxgChildTransformer.getCurrentChildNo()"/>
                            </xsl:call-template>
                        </xsl:for-each>
                    </xsl:when>
                </xsl:choose>
            </xsl:element>

            <!-- adding the already exisiting global data environment -->
            <xsl:copy-of select="$collectedGlobalData"/>
        </xsl:variable>
        <xsl:if test="$isDebugMode"><xsl:message>Finished global document variable for chapter relations!</xsl:message></xsl:if>

        <xsl:choose>
            <xsl:when test="function-available('xt:node-set')">
                <xsl:call-template name="start-self-and-children-transformation">
                    <xsl:with-param name="collectedGlobalData"       select="xt:node-set($contentTableHeadingsGlobalData-RTF)"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="function-available('xalan:nodeset')">
                <xsl:call-template name="start-self-and-children-transformation">
                    <xsl:with-param name="collectedGlobalData"       select="xalan:nodeset($contentTableHeadingsGlobalData-RTF)"/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>


    <xsl:template name="searchHeadingInChildDocument">
        <xsl:param name="chapterRefs"/>
        <xsl:param name="childrenHeadings"/>
        <xsl:param name="currentChapterRefNo"/>
        <xsl:param name="currentHeadingNo"/>
        <xsl:param name="currentChildURL"/>
        <xsl:param name="currentChildNo"/>


        <xsl:variable name="currentChapterRef"      select="$chapterRefs/chapter-ref[$currentChapterRefNo]"/>
        <xsl:variable name="currentChapterID"       select="$currentChapterRef/@content-table-id"/>
        <xsl:variable name="currentChapterTitle"    select="$currentChapterRef/@title"/>

        <xsl:variable name="currentChildHeading"    select="$childrenHeadings/heading[$currentHeadingNo]"/>
        <xsl:variable name="headingTitle"           select="$currentChildHeading/@title"/>
        <xsl:variable name="headingLevel"           select="$currentChildHeading/@level"/>
        <xsl:variable name="headingNo"              select="$currentChildHeading/@header-no"/>
        <xsl:variable name="newChildURL"            select="$currentChildHeading/@file-url"/>

        <xsl:if test="$isDebugMode">
            <xsl:message>*** new heading </xsl:message>
            <xsl:message>currentChapterID:    <xsl:value-of select="$currentChapterID"/></xsl:message>
            <xsl:message>currentChapterTitle: <xsl:value-of select="$currentChapterTitle"/></xsl:message>
            <xsl:message>currentChapterID:    <xsl:value-of select="$currentChapterID"/></xsl:message>
            <xsl:message>currentHeadingNo:    <xsl:value-of select="$currentHeadingNo"/></xsl:message>
            <xsl:message>headingTitle:        <xsl:value-of select="$headingTitle"/></xsl:message>
            <xsl:message>headingLevel:        <xsl:value-of select="$headingLevel"/></xsl:message>
            <xsl:message>headingNo:           <xsl:value-of select="$headingNo"/></xsl:message>
            <xsl:message>newChildURL:         <xsl:value-of select="$newChildURL"/></xsl:message>
        </xsl:if>

        <xsl:variable name="outFileURL">
            <xsl:choose>
                 <xsl:when test="substring-before($newChildURL,'.xml')">
                    <xsl:value-of select="concat(substring-before($newChildURL,'.xml'),'.htm')"/>
                 </xsl:when>
                 <xsl:when test="substring-before($newChildURL,'.sx')">
                    <xsl:value-of select="concat(substring-before($newChildURL,'.sx'),'.htm')"/>
                 </xsl:when>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="isChapterHeading" select="$headingTitle = $currentChapterTitle"/>
        <xsl:variable name="isNewFile" select="string($newChildURL) != string($currentChildURL)"/>




        <xsl:if test="$isNewFile">
            <!-- reset of the already collected child headers -->
            <xsl:call-template name="calc-chapter-numbers">
                 <xsl:with-param name="level" select="0"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:variable name="absoluteChapterLevel">
            <xsl:call-template name="calc-chapter-numbers">
                 <xsl:with-param name="level" select="number($headingLevel)"/>
            </xsl:call-template>
        </xsl:variable>


        <xsl:element name="heading">
            <!-- necessary to as ID from the content table to get the correct heading element (the buggy URL used as ID)-->
            <xsl:attribute name="content-table-id">
                <xsl:choose>
                    <xsl:when test="$isChapterHeading">
                        <xsl:value-of select="$currentChapterID"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>only a heading, but not a chapter</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
            <!-- no of the used child, necessary for quick finding of chapters of next file  -->
            <xsl:attribute name="child-document-no">
                <xsl:choose>
                    <xsl:when test="$isNewFile">
                        <xsl:value-of select="$currentChildNo + 1"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$currentChildNo"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
            <!-- the URL of the child document source, containing the heading -->
            <xsl:attribute name="file-url">
                <xsl:value-of select="$newChildURL"/>
            </xsl:attribute>
            <xsl:attribute name="out-file-url">
                <xsl:value-of select="$outFileURL"/>
            </xsl:attribute>
            <xsl:attribute name="level">
                <xsl:value-of select="$headingLevel"/>
            </xsl:attribute>
            <xsl:attribute name="title">
                <xsl:value-of select="$headingTitle"/>
            </xsl:attribute>
            <xsl:attribute name="encoded-title">
                <xsl:value-of select="$currentChildHeading/@encoded-title"/>
            </xsl:attribute>
            <xsl:attribute name="absolute-chapter-level">
                <xsl:value-of select="$absoluteChapterLevel"/>
            </xsl:attribute>
        </xsl:element>


        <xsl:choose>
            <xsl:when test="$childrenHeadings/heading-count != $currentHeadingNo">
                <!-- procede as long the list of children isn'nt worked through -->
                <xsl:choose>
                    <xsl:when test="$isChapterHeading">
                        <!-- global variables have to be set, so the for-each loop can access them -->
                        <xsl:choose>
                            <xsl:when test="function-available('sxghelper:set-heading-no')">
                                <xsl:value-of select="sxghelper:set-heading-no($currentHeadingNo + 1)"/>
                                <xsl:if test="$isNewFile">
                                    <xsl:value-of select="sxghelper:set-current-child-no($currentChildNo + 1)"/>
                                    <xsl:value-of select="sxghelper:set-current-child-url(string($newChildURL))"/>
                                </xsl:if>
                             </xsl:when>
                            <xsl:when test="function-available('java:com.sun.star.xslt.helper.SxgChildTransformer.setHeadingNo')">
                                <xsl:value-of select="java:com.sun.star.xslt.helper.SxgChildTransformer.setHeadingNo($currentHeadingNo + 1)"/>
                                <xsl:if test="$isNewFile">
                                    <xsl:value-of select="java:com.sun.star.xslt.helper.SxgChildTransformer.setCurrentChildNo($currentChildNo + 1)"/>
                                    <xsl:value-of select="java:com.sun.star.xslt.helper.SxgChildTransformer.setCurrentChildUrl($newChildURL)"/>
                                </xsl:if>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- not a chapter heading, call itself until a chapter ref is found or the end of headings is reached -->
                        <xsl:call-template name="searchHeadingInChildDocument">
                            <xsl:with-param name="chapterRefs"         select="$chapterRefs"/>
                            <xsl:with-param name="childrenHeadings"    select="$childrenHeadings"/>
                            <xsl:with-param name="currentChapterRefNo" select="$currentChapterRefNo"/>
                            <xsl:with-param name="currentHeadingNo"    select="$currentHeadingNo + 1"/>
                            <xsl:with-param name="currentChildURL"     select="$currentChildURL"/>
                            <xsl:with-param name="currentChildNo"      select="$currentChildNo"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="$isDebugMode">
                    <xsl:message>All child documents have been walked through without finding the chapter name!</xsl:message>
                    <xsl:message>       childrenHeadings/heading-count:    <xsl:value-of select="$childrenHeadings/heading-count"/></xsl:message>
                    <xsl:message>       currentHeadingNo:                  <xsl:value-of select="$currentHeadingNo"/></xsl:message>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>





	<!-- Chapters from the Content Table have currently no anchor to child documents in OOo XML.
		 As solution, whenever a a global document  every header of the HTML output gets get's an anchor in the Therefore-->
    <xsl:template name="encode-string">
        <xsl:param name="encoding" select="'UTF-8'"/>
        <xsl:param name="textToBeEncoded"/>

        <xsl:choose>
            <xsl:when test="function-available('urlencoder:encode')">
                <xsl:value-of select="urlencoder:encode(normalize-space($textToBeEncoded),$encoding)"/>
            </xsl:when>
            <xsl:when test="function-available('java:java.net.URLEncoder.encode')">
                <xsl:value-of select="java:java.net.URLEncoder.encode(string(normalize-space($textToBeEncoded)),string($encoding))"/>
            </xsl:when>
        </xsl:choose>
    </xsl:template>





    <!-- ******************************************************************************************************** -->
    <!-- ***  TRANSFORMATION OF ALL CHILD DOCUMENTS OF THE GLOBAL DOCUMENTS BY USING A EXTERNAL HELPER CLASS  *** -->
    <!-- ******************************************************************************************************** -->


	<!-- a new element 'contentTableHeadings' will be added to the helper variable the first time a child will be transformed -->
    <xsl:template name="transform-global-document-and-children">
        <xsl:param name="collectedGlobalData"/>


        <xsl:choose>
            <xsl:when test="$collectedGlobalData/content-table-headings">
                <xsl:call-template name="start-child-transformation">
                    <xsl:with-param name="collectedGlobalData"   select="$collectedGlobalData"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
	            <!-- The necessary auxiliary variable hasn't build yet.
	            This variable gonna store all headers (with chapter numbers) and the URL of their files -->

                <xsl:call-template name="Create-helper-variables-for-Content-Table">
                    <xsl:with-param name="collectedGlobalData"   select="$collectedGlobalData"/>
                </xsl:call-template>

            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>



	<xsl:template name="start-self-and-children-transformation">
        <xsl:param name="collectedGlobalData"/>

        <xsl:if test="$isDebugMode">
            <xsl:call-template name="debug-content-table-headings-variable">
                <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
            </xsl:call-template>

            <xsl:message>Parsing the global document...</xsl:message>
        </xsl:if>

        <xsl:apply-templates>
            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
        </xsl:apply-templates>


        <xsl:if test="$isDebugMode"><xsl:message>Parsing the child documents...</xsl:message></xsl:if>
        <xsl:call-template name="start-child-transformation">
            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
        </xsl:call-template>

	</xsl:template>




    <xsl:template name="start-child-transformation">
        <xsl:param name="collectedGlobalData"/>

        <xsl:if test="$isDebugMode"><xsl:message>Starting the child transformations...</xsl:message></xsl:if>

        <!-- As the childs of a global document (with suffix .sxg) do not know anything about their global parent,
            the transformation of global documents children have to be done implizit.
            Otherwise the chapter number of the children will always start with zero, as they do not know anything about the
            proceding chapters.
            Furthermore, they don't have any links about preceeding and following documents and no linking for usability reasons
            could be done. Therefore the children have to be transformed during the transformation of a global (sxg) document -->
		<xsl:if test="$isDebugMode">
            <xsl:choose>
                <xsl:when test="$collectedGlobalData/content-table-headings">
                    <xsl:message>Contentable data exists as global data!</xsl:message>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:message>No Contentable global data exists!</xsl:message>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>

        <!-- currently this function only works with node-sets from XT -->
        <xsl:choose>
            <xsl:when test="function-available('sxghelper:transform-children')">
                <xsl:message>
                    <xsl:value-of select="sxghelper:transform-children( $collectedGlobalData/content-table-headings,
                                                                        string($jaredRootURL),
                                                                        string($absoluteSourceDirRef),
                                                                        string($optionalURLSuffix),
                                                                        string($dpi),
                                                                        string($outputType),
                                                                        $isDebugMode)"/>
                </xsl:message>
            </xsl:when>
            <xsl:otherwise>
                <xsl:message>Java method transformChildren to transform all children of a global document could not be found. Be sure to use the XT processor.</xsl:message>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>





    <!-- ******************************************************************************* -->
    <!-- ***  Creation of helper variable of the headings of all children documents  *** -->
    <!-- ******************************************************************************* -->


    <xsl:template match="/*/office:body/text:section" mode="creation-of-variable">
        <xsl:call-template name="getChildRootNode"/>

        <!-- after the last child document the global document will be parsed -->
        <xsl:if test="position() = last()">
            <!-- search the global document after all child documents have been searched

ODK PATCH NO INDEX ELEMENT WANTED !! - null pointer exception
            <xsl:call-template name="getPreviousHeaderNo">
                <xsl:with-param name="fileURL"                  select="$contentTableURL"/>
                <xsl:with-param name="amountOfCurrentHeading"   select="count(following-sibling::text:h)"/>
                <xsl:with-param name="nodeToSearchForHeading"   select="following-sibling::text:h"/>
            </xsl:call-template>
-->
           <!-- get the overall No of Headers -->
           <xsl:call-template name="getAllHeaderNo"/>
        </xsl:if>
    </xsl:template>


    <xsl:template name="getChildRootNode">
        <xsl:variable name="fileURL"    select="text:section-source/@xlink:href"/>

        <xsl:choose>
           	<!-- if absolute URL or absolute DOS PATH or absolute Unix path -->
			<xsl:when test="contains($fileURL,'//') or (substring($fileURL,2,1) = ':') or starts-with($fileURL, '/')">
    			<xsl:variable name="childRootNode" select="document($fileURL)"/>
                <xsl:call-template name="getPreviousHeaderNo">
                    <xsl:with-param name="fileURL"                select="$fileURL"/>
                	<!-- NO absolute source path will be added as prefix -->
                    <xsl:with-param name="amountOfCurrentHeading" select="count($childRootNode/*/office:body/descendant::text:h)"/>
                    <xsl:with-param name="nodeToSearchForHeading" select="$childRootNode/*/office:body/descendant::text:h"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
    			<xsl:variable name="childRootNode" select="document(concat($absoluteSourceDirRef,'/',$fileURL))"/>
                <xsl:call-template name="getPreviousHeaderNo">
                    <xsl:with-param name="fileURL"                select="$fileURL"/>
                	<!-- the absolute source path will be added as prefix -->
                    <xsl:with-param name="amountOfCurrentHeading" select="count($childRootNode/*/office:body/descendant::text:h)"/>
                    <xsl:with-param name="nodeToSearchForHeading" select="$childRootNode/*/office:body/descendant::text:h"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


    <xsl:template name="getPreviousHeaderNo">
        <xsl:param name="fileURL"/>
        <xsl:param name="nodeToSearchForHeading"/>
        <xsl:param name="amountOfCurrentHeading"/>

        <xsl:choose>
            <xsl:when test="function-available('sxghelper:get-previous-child-documents-heading-count')">
                <xsl:call-template name="addHeadingInfo">
                    <xsl:with-param name="nodeToSearchForHeading"   select="$nodeToSearchForHeading"/>
                    <xsl:with-param name="fileURL"                  select="$fileURL"/>
                    <xsl:with-param name="previousHeader"           select="sxghelper:get-previous-child-documents-heading-count($amountOfCurrentHeading)"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="function-available('java:com.sun.star.xslt.helper.SxgChildTransformer.getPreviousChildDocumentsHeadingCount')">
                <xsl:call-template name="addHeadingInfo">
                    <xsl:with-param name="nodeToSearchForHeading"   select="$nodeToSearchForHeading"/>
                    <xsl:with-param name="fileURL"                  select="$fileURL"/>
                    <xsl:with-param name="previousHeader"           select="java:com.sun.star.xslt.helper.SxgChildTransformer.getPreviousChildDocumentsHeadingCount($amountOfCurrentHeading)"/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>

    </xsl:template>


    <xsl:template name="addHeadingInfo">
        <xsl:param name="fileURL"/>
        <xsl:param name="previousHeader"/>
        <xsl:param name="nodeToSearchForHeading"/>

        <xsl:variable name="previousHeader2" select="number($previousHeader)"/>
        <xsl:for-each select="$nodeToSearchForHeading">

            <xsl:variable name="title" select="normalize-space(.)"/>

            <xsl:variable name="encodedTitle">
                <xsl:call-template name="encode-string">
                    <!-- the space has to be normalized,
                        otherwise an illegal argument exception will be thrown for XT-->
                     <xsl:with-param name="textToBeEncoded" select="$title"/>
                </xsl:call-template>
            </xsl:variable>

            <xsl:element name="heading">
                <!-- odd but 'descendant:text()' didn't work, but '.', to get all text nodes of the header -->
                <xsl:attribute name="title"><xsl:value-of select="$title"/></xsl:attribute>
                <xsl:attribute name="encoded-title"><xsl:value-of select="$encodedTitle"/></xsl:attribute>
                <xsl:attribute name="level"><xsl:value-of select="@text:level"/></xsl:attribute>
                <xsl:attribute name="file-url"><xsl:value-of select="$fileURL"/></xsl:attribute>
                <xsl:attribute name="header-no"><xsl:value-of select="position() + $previousHeader2"/></xsl:attribute>
            </xsl:element>
        </xsl:for-each>

    </xsl:template>


    <xsl:template name="getAllHeaderNo">

        <xsl:choose>
            <xsl:when test="function-available('sxghelper:get-all-child-documents-heading-count')">
                <xsl:call-template name="addAllHeaderNoElement">
                    <xsl:with-param name="allHeader"   select="sxghelper:get-all-child-documents-heading-count()"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="function-available('java:com.sun.star.xslt.helper.SxgChildTransformer.getAllChildDocumentsHeadingCount')">
                <xsl:call-template name="addAllHeaderNoElement">
                    <xsl:with-param name="allHeader"   select="java:com.sun.star.xslt.helper.SxgChildTransformer.getAllChildDocumentsHeadingCount()"/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="addAllHeaderNoElement">
        <xsl:param name="allHeader"/>

        <xsl:element name="heading-count">
            <xsl:value-of select="$allHeader"/>
        </xsl:element>

    </xsl:template>


    <!-- ******************************************************************************************************* -->
    <!-- ***  Creation of a line of links at the beginning and end of a child document to enhance usability  *** -->
    <!-- ******************************************************************************************************* -->

    <xsl:template name="add-child-document-usability-links">
        <xsl:element name="center">
            <xsl:element name="small">
                <xsl:text>[ </xsl:text>


                <xsl:variable name="globalDocumentDir" select="sxghelper:get-global-document-dir()"/>
                <xsl:variable name="currentChildNo" select="number($contentTableHeadings/heading[$globalDocumentRefToCurrentFile = @file-url]/@child-document-no)"/>
                <xsl:variable name="earlierDocURL" select="$contentTableHeadings/heading[($currentChildNo - 1) = @child-document-no]/@out-file-url"/>
<!--
<xsl:message>from: <xsl:value-of select="$globalDocumentRefToCurrentFile"/></xsl:message>
<xsl:message>to: <xsl:value-of select="$earlierDocURL"/></xsl:message>
<xsl:message>Is: <xsl:call-template name="get-relative-file-ref">
                    <xsl:with-param name="sourceFileRef" select="$globalDocumentRefToCurrentFile"/>
                    <xsl:with-param name="targetFileRef" select="$earlierDocURL"/>
                 </xsl:call-template>
</xsl:message>-->


                <xsl:if test="$earlierDocURL">
                    <xsl:element name="a">
                        <xsl:attribute name="href">
                            <!-- when the links starts with a '#' it's a link to the Content Table-->
                            <xsl:choose>
                                <xsl:when test="starts-with($earlierDocURL, '#')">

                                    <xsl:call-template name="get-relative-file-ref">
                                        <xsl:with-param name="sourceFileRef" select="$globalDocumentRefToCurrentFile"/>
                                        <xsl:with-param name="targetFileRef" select="."/>
                                    </xsl:call-template>
<!--        <xsl:value-of select="concat($contentTableURL, $earlierDocURL)"/>-->
                                </xsl:when>
                                <xsl:otherwise>

                                    <xsl:call-template name="get-relative-file-ref">
                                        <xsl:with-param name="sourceFileRef" select="$globalDocumentRefToCurrentFile"/>
                                        <xsl:with-param name="targetFileRef" select="$earlierDocURL"/>
                                    </xsl:call-template>
<!--

                                    <xsl:value-of select="concat($globalDocumentDir, $earlierDocURL)"/>-->
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:attribute>
                        <xsl:text>Previous document</xsl:text>
                    </xsl:element>

                    <xsl:text> | </xsl:text>
                </xsl:if>

                <xsl:element name="a">
                    <xsl:attribute name="href">
                        <!-- when globalDocumentRefToCurrentFile is unset the current file is the Content Table-->
                        <xsl:choose>
                            <xsl:when test="$globalDocumentRefToCurrentFile">
                                <xsl:variable name="contentTableDir">
                                    <xsl:call-template name="get-name-of-table-of-content-document"/>
                                </xsl:variable>

                                <xsl:call-template name="get-relative-file-ref">
                                    <xsl:with-param name="sourceFileRef" select="$globalDocumentRefToCurrentFile"/>
                                    <xsl:with-param name="targetFileRef" select="$contentTableDir"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>#</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>

<!--                    <xsl:value-of select="$contentTableURL"/>-->
                    </xsl:attribute>
                    <xsl:text>Content Table</xsl:text>
                </xsl:element>


                <xsl:variable name="nextDocURL" select="$contentTableHeadings/heading[($currentChildNo + 1) = @child-document-no]/@out-file-url"/>
                <xsl:if test="$nextDocURL">
                    <xsl:text> | </xsl:text>
                    <xsl:element name="a">
                        <xsl:attribute name="href">
                            <!-- when the links starts with a '#' it's a link to the Content Table-->
                            <xsl:choose>
                                <xsl:when test="starts-with($nextDocURL, '#')">
                                    <xsl:call-template name="get-relative-file-ref">
                                        <xsl:with-param name="sourceFileRef" select="$globalDocumentRefToCurrentFile"/>
                                        <xsl:with-param name="targetFileRef" select="."/>
                                    </xsl:call-template>
<!--                                <xsl:value-of select="concat($contentTableURL, $nextDocURL)"/>-->
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:call-template name="get-relative-file-ref">
                                        <xsl:with-param name="sourceFileRef" select="$globalDocumentRefToCurrentFile"/>
                                        <xsl:with-param name="targetFileRef" select="$nextDocURL"/>
                                    </xsl:call-template>
<!--                                 <xsl:value-of select="concat($globalDocumentDir, $nextDocURL)"/>-->
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:attribute>
                        <xsl:text>Next document</xsl:text>
                    </xsl:element>
                </xsl:if>
                <xsl:text> ]</xsl:text>
            </xsl:element>
        </xsl:element>
    </xsl:template>


    <xsl:template name="get-relative-file-ref">
        <xsl:param name="sourceFileRef"/>
        <xsl:param name="targetFileRef"/>

        <xsl:choose>
            <xsl:when test="function-available('sxghelper:get-relative-file-ref')">
                <xsl:value-of select="sxghelper:get-relative-file-ref(string($sourceFileRef), string($targetFileRef))"/>
            </xsl:when>
            <xsl:when test="function-available('java:com.sun.star.xslt.helper.SxgChildTransformer.getRelativeFileRef')">
                <xsl:value-of select="java:com.sun.star.xslt.helper.SxgChildTransformer.getRelativeFileRef(string($sourceFileRef), string($targetFileRef))"/>
            </xsl:when>
        </xsl:choose>

    </xsl:template>


    <xsl:template name="get-name-of-table-of-content-document">

        <xsl:choose>
            <xsl:when test="function-available('sxghelper:get-name-of-table-of-content-document')">
                <xsl:value-of select="sxghelper:get-name-of-table-of-content-document()"/>
            </xsl:when>
            <xsl:when test="function-available('java:com.sun.star.xslt.helper.SxgChildTransformer.getNameOfTableOfContentDocument')">
                <xsl:value-of select="java:com.sun.star.xslt.helper.SxgChildTransformer.getNameOfTableOfContentDocument()"/>
            </xsl:when>
        </xsl:choose>

    </xsl:template>


	<xsl:template name="debug-content-table-headings-variable">
        <xsl:param name="collectedGlobalData"/>

        <xsl:message><xsl:text>**** THE HEADING VARIABLE **** </xsl:text></xsl:message>
        <xsl:message>content-table-url: <xsl:value-of select="collectedGlobalData/content-table-headings/content-table-url"/></xsl:message>

        <xsl:for-each select="$collectedGlobalData/content-table-headings/heading">
            <xsl:message><xsl:text>**** new heading:        </xsl:text></xsl:message>
            <xsl:message>content-table-id:      <xsl:value-of select="@content-table-id"/></xsl:message>
            <xsl:message>child-document-no:     <xsl:value-of select="@child-document-no"/></xsl:message>
            <xsl:message>file-url:              <xsl:value-of select="@file-url"/></xsl:message>
            <xsl:message>out-file-url:          <xsl:value-of select="@out-file-url"/></xsl:message>
            <xsl:message>level:                 <xsl:value-of select="@level"/></xsl:message>
            <xsl:message>title:                 <xsl:value-of select="@title"/></xsl:message>
            <xsl:message>encoded-title:         <xsl:value-of select="@encoded-title"/></xsl:message>
            <xsl:message>absolute-chapter-level:<xsl:value-of select="@absolute-chapter-level"/></xsl:message>
        </xsl:for-each>

	</xsl:template>


	<!-- To make the headings unique, the absolute heading is added to them
	     E.g. The level 1.2.3.4. would result into a 1+2+3+4 string -->
    <xsl:template name="calc-chapter-numbers">
        <xsl:param name="level"/>

        <xsl:choose>
            <xsl:when test="function-available('sxghelper:calc-chapter-numbers')">
                <xsl:value-of select="sxghelper:calc-chapter-numbers($level)"/>
            </xsl:when>
            <xsl:when test="function-available('java:com.sun.star.xslt.helper.SxgChildTransformer.calcChapterNumbers')">
                <xsl:value-of select="java:com.sun.star.xslt.helper.SxgChildTransformer.calcChapterNumbers($level)"/>
            </xsl:when>
        </xsl:choose>

    </xsl:template>




    <xsl:template match="text:p" mode="content-table">
        <xsl:param name="collectedGlobalData"/>

        <xsl:variable name="allTabStopStyles" select="$office:automatic-styles/style:style[@style:name = current()/@text:style-name]/style:properties/style:tab-stops"/>

        <xsl:element name="table">
            <xsl:attribute name="border">0</xsl:attribute>
            <xsl:attribute name="class"><xsl:value-of select="@text:style-name"/></xsl:attribute>
<!--
<xsl:message>*********</xsl:message>
<xsl:message>Stylename:<xsl:value-of select="@text:style-name"/></xsl:message>
<xsl:message>position: <xsl:value-of select="count($allTabStopStyles/style:tab-stop)"/></xsl:message>
-->

            <xsl:element name="colgroup">
                <xsl:call-template name="create-col-element">
                    <xsl:with-param name="lastNodePosition" select="count($allTabStopStyles/style:tab-stop)"/>
                    <xsl:with-param name="allTabStopStyles" select="$allTabStopStyles"/>
                </xsl:call-template>
            </xsl:element>


            <!-- all elements before the first tabStop -->
            <xsl:variable name="testNo-RTF">
                <xsl:apply-templates select="node()" mode="cell-content"/>
            </xsl:variable>


        <xsl:choose>
            <xsl:when test="function-available('xt:node-set')">
                <xsl:variable name="tabNodePositions" select="xt:node-set($testNo-RTF)"/>
			<xsl:element name="tr">
               	 <xsl:call-template name="create-td-elements">
                    <xsl:with-param name="lastNodePosition" select="count($allTabStopStyles/style:tab-stop)"/>
                    <xsl:with-param name="position"         select="1"/>
                    <xsl:with-param name="allTabStopStyles" select="$allTabStopStyles"/>
                    <xsl:with-param name="tabNodePositions" select="$tabNodePositions"/>
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                </xsl:call-template>
            </xsl:element>

            </xsl:when>
            <xsl:when test="function-available('xalan:nodeset')">
                <xsl:variable name="tabNodePositions" select="xalan:nodeset($testNo-RTF)"/>
			<xsl:element name="tr">
               	 <xsl:call-template name="create-td-elements">
                    <xsl:with-param name="lastNodePosition" select="count($allTabStopStyles/style:tab-stop)"/>
                    <xsl:with-param name="position"         select="1"/>
                    <xsl:with-param name="allTabStopStyles" select="$allTabStopStyles"/>
                    <xsl:with-param name="tabNodePositions" select="$tabNodePositions"/>
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                </xsl:call-template>
            </xsl:element>

            </xsl:when>
        </xsl:choose>

           <!-- <xsl:variable name="tabNodePositions" select="xt:node-set($testNo-RTF)"/>

            <xsl:element name="tr">
                <xsl:call-template name="create-td-elements">
                    <xsl:with-param name="lastNodePosition" select="count($allTabStopStyles/style:tab-stop)"/>
                    <xsl:with-param name="position"         select="1"/>
                    <xsl:with-param name="allTabStopStyles" select="$allTabStopStyles"/>
                    <xsl:with-param name="tabNodePositions" select="$tabNodePositions"/>
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                </xsl:call-template>
            </xsl:element>-->


        </xsl:element>
    </xsl:template>


    <xsl:template name="create-col-element">
        <xsl:param name="lastNodePosition"/>
        <xsl:param name="allTabStopStyles"/>

        <xsl:for-each select="$allTabStopStyles/style:tab-stop">
            <xsl:element name="col">
                <xsl:attribute name="style">
                    <xsl:text>width: </xsl:text>
                    <xsl:call-template name="grap-cell-width">
                        <xsl:with-param name="position"         select="position()"/>
                        <xsl:with-param name="allTabStopStyles" select="$allTabStopStyles"/>
                    </xsl:call-template>
                </xsl:attribute>
            </xsl:element>
        </xsl:for-each>

    </xsl:template>
<!--
Scenarios tabstops

1) style:type of style:tab-stop is 'right' and earlier tabStop is not right
 -> Earlier text-nodes and following text-nodes, will be put into an inner table, with two TD first aligned left, with proceding textnodes, the latter aligned right.

2) style:type is 'right' and earlier tabStop is right
 -> following text-nodes, will be put into a right aligned TD

3) style:type is 'non-right' and earlier tabStop 'non-right' as well
 -> put the preceding tab stops into a TD (left aligned is default)

4) first style:type would have no right precedign tabStop
 -> works well with first sceanrios 1 and 3

5) last style:type would be a special case, if it would be left aligned, but this won't happen in our case.. :D

Scenarios unmatched:
- text:styleposition 'center' will not be matched in our case (effort for nothing), there will be only 'right' and not 'right'
- If the last tabStop is not from text:stylepostion 'right', the length of the last cell is undefined and a document length must be found.
  Not happens in our global document case. Also the algorithm below would have to be expanded (cp. scenario 5).

-->
    <xsl:template name="create-td-elements">
        <xsl:param name="collectedGlobalData"/>
        <xsl:param name="lastNodePosition"/>
        <xsl:param name="position"/>
        <xsl:param name="allTabStopStyles"/>
        <xsl:param name="tabNodePositions"/>
<!--
<xsl:message>++++++++</xsl:message>
<xsl:message>Position: <xsl:value-of select="$position"/></xsl:message>
<xsl:message>lastNodePosition: <xsl:value-of select="$lastNodePosition"/></xsl:message>
-->

        <xsl:variable name="currentStyleType" select="$allTabStopStyles/style:tab-stop[$position]/@style:type"/>
        <xsl:variable name="earlierStyleType" select="$allTabStopStyles/style:tab-stop[$position - 1]/@style:type"/>
        <xsl:choose>
            <xsl:when test="$currentStyleType = 'right'">
                <xsl:choose>
                    <xsl:when test="$earlierStyleType = 'right'">
                        <!--
                        2) style:type is 'right' and earlier tabStop is right
                            -> following text-nodes, will be put into a right aligned TD -->
                        <xsl:element name="td">
                            <xsl:attribute name="style">
                                <xsl:text>align: right</xsl:text>
                            </xsl:attribute>
                            <xsl:call-template name="grap-cell-content-before-tab-stop">
                                <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                <xsl:with-param name="endingTabStopPosition"  select="$position + 1"/>
                                <xsl:with-param name="lastNodePosition" select="$lastNodePosition"/>
                                <xsl:with-param name="tabNodePositions" select="$tabNodePositions"/>
                            </xsl:call-template>
                        </xsl:element>
                    </xsl:when>
                    <xsl:otherwise>
                    <!--
                        1) style:type of style:tab-stop is 'right' and earlier tabStop is not right
                         -> Earlier text-nodes and following text-nodes, will be put into an inner table, with two TD first aligned left, with proceding textnodes, the latter aligned right.-->
<!-- valid HTML but browsers make a line break (border=0 and paragraphstyle also missing):
                        <xsl:element name="table">
                            <xsl:element name="td">
                                <xsl:call-template name="grap-cell-content-before-tab-stop">
                                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                    <xsl:with-param name="endingTabStopPosition"  select="$position"/>
                                    <xsl:with-param name="lastNodePosition" select="$lastNodePosition"/>
                                    <xsl:with-param name="tabNodePositions" select="$tabNodePositions"/>
                                </xsl:call-template>
                            </xsl:element>
                            <xsl:element name="td">
                                <xsl:attribute name="style">
                                    <xsl:text>align: right</xsl:text>
                                </xsl:attribute>
                                <xsl:call-template name="grap-cell-content-before-tab-stop">
                                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                    <xsl:with-param name="endingTabStopPosition"  select="$position + 1"/>
                                    <xsl:with-param name="lastNodePosition" select="$lastNodePosition"/>
                                    <xsl:with-param name="tabNodePositions" select="$tabNodePositions"/>
                                </xsl:call-template>
                            </xsl:element>
                        </xsl:element>
-->
                            <xsl:element name="td">
                                <xsl:call-template name="grap-cell-content-before-tab-stop">
                                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                    <xsl:with-param name="endingTabStopPosition"  select="$position"/>
                                    <xsl:with-param name="lastNodePosition" select="$lastNodePosition"/>
                                    <xsl:with-param name="tabNodePositions" select="$tabNodePositions"/>
                                </xsl:call-template>
<!-- ODK FEATURE NO PAGES
                                <xsl:element name="td">
                                    <xsl:attribute name="style">
                                        <xsl:text>align: right</xsl:text>
                                    </xsl:attribute>
                                    <xsl:call-template name="grap-cell-content-before-tab-stop">
                                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                        <xsl:with-param name="endingTabStopPosition"  select="$position + 1"/>
                                        <xsl:with-param name="lastNodePosition" select="$lastNodePosition"/>
                                        <xsl:with-param name="tabNodePositions" select="$tabNodePositions"/>
                                    </xsl:call-template>
                                </xsl:element>          -->
                            </xsl:element>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="$earlierStyleType = 'right'">
                    </xsl:when>
                    <xsl:otherwise>
                    <!--
                       3) style:type is 'non-right' and earlier tabStop 'non-right' as well
                            -> put the preceding tab stops into a TD (left aligned is default) -->
                        <xsl:element name="td">
                            <xsl:call-template name="grap-cell-content-before-tab-stop">
                                <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                <xsl:with-param name="endingTabStopPosition"  select="$position"/>
                                <xsl:with-param name="lastNodePosition" select="$lastNodePosition"/>
                                <xsl:with-param name="tabNodePositions" select="$tabNodePositions"/>
                            </xsl:call-template>
                        </xsl:element>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>

        <xsl:if test="$position != $lastNodePosition">
            <xsl:call-template name="create-td-elements">
                <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                <xsl:with-param name="lastNodePosition" select="$lastNodePosition"/>
                <xsl:with-param name="position"         select="$position + 1"/>
                <xsl:with-param name="allTabStopStyles" select="$allTabStopStyles"/>
                <xsl:with-param name="tabNodePositions" select="$tabNodePositions"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>


    <xsl:template name="grap-cell-content-before-tab-stop">
        <xsl:param name="collectedGlobalData"/>
        <xsl:param name="endingTabStopPosition"/>
        <xsl:param name="tabNodePositions"/>
        <xsl:param name="lastNodePosition"/>

        <xsl:choose>
            <xsl:when test="$endingTabStopPosition = 1">
                <xsl:apply-templates mode="content-table" select="node()[position() &lt; $tabNodePositions/tab-stop-node-position[$endingTabStopPosition]]">
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                </xsl:apply-templates>
            </xsl:when>
            <xsl:when test="$endingTabStopPosition > $lastNodePosition">
                <xsl:apply-templates mode="content-table" select="node()[position() > $tabNodePositions/tab-stop-node-position[$endingTabStopPosition - 1]]">
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                </xsl:apply-templates>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates mode="content-table" select="node()[position() &lt; $tabNodePositions/tab-stop-node-position[$endingTabStopPosition]][position() > $tabNodePositions/tab-stop-node-position[$endingTabStopPosition - 1]]">
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                </xsl:apply-templates>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template mode="content-table" match="text:s">
        <xsl:call-template name="write-breakable-whitespace">
            <xsl:with-param name="whitespaces" select="@text:c"/>
        </xsl:call-template>
    </xsl:template>


    <xsl:template match="*" mode="cell-content">

        <xsl:if test="name() = 'text:tab-stop' or *[name() = 'text:tab-stop']">
            <xsl:element name="tab-stop-node-position">
                <xsl:value-of select="position()"/>
            </xsl:element>
        </xsl:if>
    </xsl:template>


    <xsl:template name="grap-cell-width">
        <xsl:param name="position"/>
        <xsl:param name="allTabStopStyles"/>

        <xsl:variable name="tabStopPosition" select="$allTabStopStyles/style:tab-stop[$position]/@style:position"/>
        <xsl:choose>
            <xsl:when test="contains($tabStopPosition, 'cm')">
                <xsl:call-template name="create-cell-width">
                    <xsl:with-param name="width"    select="number(substring-before($tabStopPosition,'cm'))"/>
                    <xsl:with-param name="unit"     select="'cm'"/>
                    <xsl:with-param name="position" select="$position - 1"/>
                    <xsl:with-param name="allTabStopStyles" select="$allTabStopStyles"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="contains($tabStopPosition, 'in')">
                <xsl:call-template name="create-cell-width">
                    <xsl:with-param name="width"    select="number(substring-before($tabStopPosition,'in'))"/>
                    <xsl:with-param name="unit"     select="'in'"/>
                    <xsl:with-param name="position" select="$position - 1"/>
                    <xsl:with-param name="allTabStopStyles" select="$allTabStopStyles"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="contains($tabStopPosition, 'ch')">
                <xsl:call-template name="create-cell-width">
                    <xsl:with-param name="width"    select="number(substring-before($tabStopPosition,'ch'))"/>
                    <xsl:with-param name="unit"     select="'ch'"/>
                    <xsl:with-param name="position" select="$position - 1"/>
                    <xsl:with-param name="allTabStopStyles" select="$allTabStopStyles"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="contains($tabStopPosition, 'pt')">
                <xsl:call-template name="create-cell-width">
                    <xsl:with-param name="width"    select="number(substring-before($tabStopPosition,'pt'))"/>
                    <xsl:with-param name="unit"     select="'pt'"/>
                    <xsl:with-param name="position" select="$position - 1"/>
                    <xsl:with-param name="allTabStopStyles" select="$allTabStopStyles"/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="create-cell-width">
        <xsl:param name="width"/>
        <xsl:param name="unit"/>
        <xsl:param name="position"/>
        <xsl:param name="allTabStopStyles"/>

        <xsl:choose>
            <xsl:when test="$position > 1">
                <xsl:call-template name="create-cell-width">
                    <xsl:with-param name="width"    select="$width - number(substring-before($allTabStopStyles/style:tab-stop[$position]/@style:position,$unit))"/>
                    <xsl:with-param name="unit"     select="$unit"/>
                    <xsl:with-param name="position" select="$position - 1"/>
                    <xsl:with-param name="allTabStopStyles" select="$allTabStopStyles"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$position = 1">
                <xsl:value-of select="concat($width - number(substring-before($allTabStopStyles/style:tab-stop[$position]/@style:position,$unit)), $unit)"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="concat($width, $unit)"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

</xsl:stylesheet>