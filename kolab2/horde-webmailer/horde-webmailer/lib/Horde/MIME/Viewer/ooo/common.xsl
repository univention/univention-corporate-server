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
                xmlns:xalan="http://xml.apache.org/xalan"
                xmlns:java="http://xml.apache.org/xslt/java"
                exclude-result-prefixes="java">



    <!-- ************ -->
    <!-- *** body *** -->
    <!-- ************ -->


    <xsl:template match="/*/office:body">
        <xsl:param name="collectedGlobalData"/>

        <!-- isDebugMode-START: only isDebugMode purpose: shows the inlined style attributes of the temporary variable -->
        <xsl:if test="$isDebugMode and not($outputType = 'CSS_HEADER')">
            <xsl:element name="debug_tree_of_styles"><xsl:text>
            </xsl:text><xsl:for-each select="$collectedGlobalData/allstyles/*">
<xsl:text>                      </xsl:text><xsl:value-of select="name()"/><xsl:text> = </xsl:text><xsl:value-of select="."/><xsl:text>
            </xsl:text>
                    </xsl:for-each>
            </xsl:element>
        </xsl:if>
    <!-- isDebugMode-END -->


		<!-- not using of 'apply-styles-and-content' as the content table information migth have been added to 'collectedGlobalData' variable -->
        <xsl:apply-templates select="@text:style-name | @draw:style-name | @draw:text-style-name | @table:style-name"><!-- | @presentation:style-name -->
            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
        </xsl:apply-templates>


        <!-- Usability feature, a link to the Content talbe above all level 1 header -->
        <xsl:if test="$contentTableHeadings">
            <xsl:call-template name="add-child-document-usability-links"/>
        </xsl:if>


		<xsl:choose>
	        <xsl:when test="not($outputType = 'WML') and not($outputType = 'PALM')">
	        	<xsl:choose>
			        <!--If the input document is a global document and embed child documents (links) the transformation of the children will be started as well.
			            This is necessary as child documents do not know anything about their embedding into a global document. Chapters of childs
			            always start to count by zero instead of continously numbering.
			            For this, the chapter numbers of the current document (as a sequence of a global document) is dependent
			            of the number of chapter of the same level in preceding documents.
			            In case of multiple children, for usability reasons some linking is gonna be offered and the URLs of the content-table,
			            preceding and following file have to be given for the transformation.
			            -->
		            <xsl:when test="/*/@office:class='text-global' and /*/office:body/text:section/text:section-source/@xlink:href">
						<!-- the children will be called later with a modified 'collectedGlobalData' variable -->
		                <xsl:call-template name="transform-global-document-and-children">
		                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
		                </xsl:call-template>
		            </xsl:when>
					<xsl:otherwise>
				        <xsl:apply-templates>
				            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
				        </xsl:apply-templates>
					</xsl:otherwise>
				</xsl:choose>
	        </xsl:when>
			<xsl:otherwise>
		        <xsl:apply-templates>
		            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
		        </xsl:apply-templates>
			</xsl:otherwise>
		</xsl:choose>



        <!-- Usability feature, a link to the Content talbe above all level 1 header -->
        <xsl:if test="$contentTableHeadings">
            <xsl:call-template name="add-child-document-usability-links"/>
        </xsl:if>


    </xsl:template>




    <!-- deactivating default template -->
    <xsl:template match="*"/>


    <!-- allowing all matched text nodes -->
    <xsl:template match="text()">
<!-- WML         <xsl:value-of select="normalize-space(.)"/> -->
        <xsl:value-of select="."/>
    </xsl:template>



    <!-- ################### -->
    <!-- ### INLINE-TEXT ### -->
    <!-- ################### -->


    <!-- ****************** -->
    <!-- *** Whitespace *** -->
    <!-- ****************** -->


    <xsl:template match="text:s">
        <xsl:call-template name="write-breakable-whitespace">
            <xsl:with-param name="whitespaces" select="@text:c"/>
        </xsl:call-template>
    </xsl:template>


    <!--write the number of 'whitespaces' -->
    <xsl:template name="write-breakable-whitespace">
        <xsl:param name="whitespaces"/>

        <!--write two space chars as the normal white space character will be stripped
            and the other is able to break -->
        <xsl:text>&#160;</xsl:text>
        <xsl:if test="$whitespaces >= 2">
            <xsl:call-template name="write-breakable-whitespace-2">
                <xsl:with-param name="whitespaces" select="$whitespaces - 1"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>


    <!--write the number of 'whitespaces' -->
    <xsl:template name="write-breakable-whitespace-2">
        <xsl:param name="whitespaces"/>
        <!--write two space chars as the normal white space character will be stripped
            and the other is able to break -->
        <xsl:text> </xsl:text>
        <xsl:if test="$whitespaces >= 2">
            <xsl:call-template name="write-breakable-whitespace">
                <xsl:with-param name="whitespaces" select="$whitespaces - 1"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>




    <!-- *************** -->
    <!-- *** Textbox *** -->
    <!-- *************** -->

    <xsl:template match="draw:text-box">
        <xsl:param name="collectedGlobalData"/>

            <xsl:choose>
                <!--+++++ CSS (CASCADING STLYE SHEET) HEADER STYLE WAY +++++-->
                <!--                or                  -->
                <!--+++++ HTML 4.0 INLINED WAY  +++++-->
                <xsl:when test="$outputType = 'CSS_HEADER' or $outputType = 'CSS_INLINED'">
                    <xsl:element name="span">
                        <xsl:if test="@fo:min-height | @svg:width">
                            <xsl:attribute name="style">
                                <xsl:choose>
                                    <xsl:when test="not(@svg:width)">
                                        <xsl:text>height: </xsl:text><xsl:value-of select="@fo:min-height"/><xsl:text>; </xsl:text>
                                    </xsl:when>
                                    <xsl:when test="not(@fo:min-height)">
                                        <xsl:text>width: </xsl:text><xsl:value-of select="@svg:width"/><xsl:text>; </xsl:text>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:text>height: </xsl:text><xsl:value-of select="@fo:min-height"/><xsl:text>; </xsl:text>
                                        <xsl:text>width: </xsl:text><xsl:value-of select="@svg:width"/><xsl:text>; </xsl:text>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:attribute>
                        </xsl:if>
                        <xsl:apply-templates select="@draw:name"/>
                        <xsl:call-template name="apply-styles-and-content">
                            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                        </xsl:call-template>
                    </xsl:element>
                </xsl:when>
                <!-- 2DO prove best usage for PALM -->
                <!--+++++ PALM 3.2 SUBSET INLINED WAY  +++++-->
                <xsl:when test="$outputType = 'PALM'">
                    <xsl:element name="span">
                        <xsl:call-template name="apply-styles-and-content">
                            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                        </xsl:call-template>
                    </xsl:element>
                </xsl:when>
                <!-- 2DO prove best usage for WML -->
                <!--+++++ WML / WAP  +++++-->
                <xsl:otherwise>
                    <!-- no nested p tags in wml1.1 allowed -->
                    <xsl:choose>
                        <xsl:when test="ancestor::*[contains($wap-paragraph-elements, name())]">
                            <xsl:call-template name="apply-styles-and-content">
                                <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:element name="p">
                                <xsl:call-template name="apply-styles-and-content">
                                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                </xsl:call-template>
                             </xsl:element>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:otherwise>
            </xsl:choose>
    </xsl:template>

    <!-- ID / NAME of text-box -->
    <xsl:template match="@draw:name">

        <xsl:attribute name="id">
            <xsl:value-of select="."/>
        </xsl:attribute>
    </xsl:template>



    <!-- ****************** -->
    <!-- *** Paragraphs *** -->
    <!-- ****************** -->

    <xsl:template match="text:p | draw:page">
        <xsl:param name="collectedGlobalData"/>

            <xsl:choose>
                <!--+++++ CSS (CASCADING STLYE SHEET) HEADER STYLE WAY +++++-->
                <xsl:when test="$outputType = 'CSS_HEADER'">
                    <xsl:element name="p">
                        <xsl:call-template name="apply-styles-and-content">
                            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                        </xsl:call-template>
                    </xsl:element>
                </xsl:when>

                <!--+++++ HTML 4.0 INLINED WAY  +++++-->
                <xsl:when test="$outputType = 'CSS_INLINED'">
                    <xsl:element name="p">
                        <xsl:call-template name="apply-styles-and-content">
                            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                        </xsl:call-template>
                    </xsl:element>
                </xsl:when>
                <!--+++++ PALM 3.2 SUBSET INLINED WAY  +++++-->
                <xsl:when test="$outputType = 'PALM'">
                    <xsl:choose>
                        <!-- in palm paragraphs children of text:list-items are better shown without 'p' tag-->
                        <xsl:when test="name(parent::*) = 'text:list-item'">
                            <xsl:call-template name="apply-styles-and-content">
                                <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:element name="p">
                                <xsl:call-template name="apply-styles-and-content">
                                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                </xsl:call-template>
                            </xsl:element>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <!--+++++ WML / WAP  +++++-->
                <xsl:otherwise>
                    <!-- no nested p tags in wml1.1 allowed -->
                    <xsl:choose>
                        <xsl:when test="ancestor::*[contains($wap-paragraph-elements, name())]">
                            <xsl:call-template name="apply-styles-and-content">
                                <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:element name="p">
                                <xsl:call-template name="apply-styles-and-content">
                                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                </xsl:call-template>
                             </xsl:element>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:otherwise>
            </xsl:choose>
    </xsl:template>



    <!-- ***************** -->
    <!-- *** Text Span *** -->
    <!-- ***************** -->

    <xsl:template match="text:span">
        <xsl:param name="collectedGlobalData"/>

        <xsl:choose>
            <!--+++++ CSS (CASCADING STLYE SHEET) HEADER STYLE WAY +++++-->
            <xsl:when test="$outputType = 'CSS_HEADER'">
                <xsl:element name="span">
                    <xsl:call-template name="apply-styles-and-content">
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    </xsl:call-template>
                </xsl:element>
            </xsl:when>

            <!--+++++ HTML 4.0 INLINED WAY  +++++-->
            <xsl:when test="$outputType = 'CSS_INLINED'">
                <xsl:element name="span">
                    <xsl:call-template name="apply-styles-and-content">
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    </xsl:call-template>
                </xsl:element>
            </xsl:when>
            <!--+++++ PALM 3.2 SUBSET INLINED WAY  +++++-->
            <xsl:when test="$outputType = 'PALM'">
                <xsl:call-template name="apply-styles-and-content">
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                </xsl:call-template>
            </xsl:when>
            <!--+++++ WML / WAP  +++++-->
            <xsl:otherwise>
                <!-- no nested p tags in wml1.1 allowed -->
                <xsl:choose>
                    <xsl:when test="ancestor::*[contains($wap-paragraph-elements, name())]">
                        <xsl:call-template name="apply-styles-and-content">
                            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:element name="p">
                            <xsl:call-template name="apply-styles-and-content">
                                <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                            </xsl:call-template>
                        </xsl:element>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>



    <!-- **************** -->
    <!-- *** Headings *** -->
    <!-- **************** -->

    <xsl:template match="text:h">
        <xsl:param name="collectedGlobalData"/>

        <!-- Every heading element will get an unique anchor for its file, from its hiearchy level and name:
            For example:  The heading title 'My favorite heading' might get <a name="1+2+2+My+favorite+heading"/> -->
        <xsl:choose>
            <xsl:when test="$disableLinkedTableOfContent or $isJavaDisabled or not($outputType = 'CSS_HEADER')">
            <!-- The URL linking of an table-of-content is due to a bug (cmp. bug id# 102311) not mapped as URL in the XML.
                 Linking of the table-of-content can therefore only be archieved by a work-around in HTML -->
                <xsl:call-template name="create-heading">
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                </xsl:call-template>
           </xsl:when>
           <xsl:otherwise>
                <!-- necessary as anchor for the content table -->
                <xsl:call-template name="create-heading-anchor">
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                </xsl:call-template>

                <!-- no embedding the orginal header, as an explicit anchor might be already set -->
                <xsl:call-template name="create-heading">
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


    <!-- default matching for header elements -->
    <xsl:template name="create-heading">
        <xsl:param name="collectedGlobalData"/>

        <xsl:choose>
            <!--+++++ CSS (CASCADING STLYE SHEET) HEADER STYLE WAY +++++-->
            <xsl:when test="$outputType = 'CSS_HEADER'">

                <xsl:variable name="headertyp" select="concat('h', @text:level)"/>
                <xsl:element name="{$headertyp}">

                    <!-- outline style 'text:min-label-width' is interpreted as a CSS 'margin-left' attribute -->
                    <xsl:variable name="min-label" select="$office:styles/text:outline-style/text:outline-level-style[@text:level = current()/@text:level]/style:properties/@text:min-label-width"/>
                    <xsl:if test="$min-label">
                        <xsl:attribute name="style"><xsl:text>margin-left:</xsl:text><xsl:value-of select="$min-label"/><xsl:text>;</xsl:text></xsl:attribute>
                    </xsl:if>


                    <xsl:attribute name="class"><xsl:value-of select="translate(@text:style-name, '. %()/\', '')"/></xsl:attribute>

                    <!-- writing out a chapter number if desired (noticable when a corresponding 'text:outline-style' exist -->
                    <xsl:if test="string-length($office:styles/text:outline-style/text:outline-level-style[@text:level = current()/@text:level]/@style:num-format) != 0">

                        <xsl:choose>
                            <xsl:when test="$disableLinkedTableOfContent or $isJavaDisabled or not($outputType = 'CSS_HEADER')">
                                <!-- the chapter number is the sum of 'text:start-value' and preceding siblings of 'text:h' with the same 'text:level',
                                     furthermore when the current document is referenced by a global document - as part of a whole sequence of documents -,
                                     the chapter no. is dependent of the amount of started headers in preceding documents.
                                     If the 'text:start-value is not set the default value of '1' has to be taken. -->
                                <xsl:variable name="startValue" select="$office:styles/text:outline-style/text:outline-level-style[@text:level = current()/@text:level]/@text:start-value"/>
                                <xsl:choose>
                                    <xsl:when test="$startValue">
                                        <xsl:choose>
                                            <xsl:when test="@text:level='1'">
                                                <xsl:value-of select="count(preceding-sibling::text:h[@text:level = current()/@text:level])
                                                            + $precedingChapterLevel1
                                                            + $startValue"/>
                                            </xsl:when>
                                            <xsl:when test="@text:level='2'">
                                                <xsl:value-of select="count(preceding-sibling::text:h[@text:level = current()/@text:level])
                                                            + $precedingChapterLevel2
                                                            + $startValue"/>
                                            </xsl:when>
                                            <xsl:when test="@text:level='3'">
                                                <xsl:value-of select="count(preceding-sibling::text:h[@text:level = current()/@text:level])
                                                            + $precedingChapterLevel3
                                                            + $startValue"/>
                                            </xsl:when>
                                            <xsl:when test="@text:level='4'">
                                                <xsl:value-of select="count(preceding-sibling::text:h[@text:level = current()/@text:level])
                                                            + $precedingChapterLevel4
                                                            + $startValue"/>
                                            </xsl:when>
                                            <xsl:when test="@text:level='5'">
                                                <xsl:value-of select="count(preceding-sibling::text:h[@text:level = current()/@text:level])
                                                            + $precedingChapterLevel5
                                                            + $startValue"/>
                                            </xsl:when>
                                            <xsl:when test="@text:level='6'">
                                                <xsl:value-of select="count(preceding-sibling::text:h[@text:level = current()/@text:level])
                                                            + $precedingChapterLevel6
                                                            + $startValue"/>
                                            </xsl:when>
                                            <xsl:when test="@text:level='7'">
                                                <xsl:value-of select="count(preceding-sibling::text:h[@text:level = current()/@text:level])
                                                            + $precedingChapterLevel7
                                                            + $startValue"/>
                                            </xsl:when>
                                            <xsl:when test="@text:level='8'">
                                                <xsl:value-of select="count(preceding-sibling::text:h[@text:level = current()/@text:level])
                                                            + $precedingChapterLevel8
                                                            + $startValue"/>
                                            </xsl:when>
                                            <xsl:when test="@text:level='9'">
                                                <xsl:value-of select="count(preceding-sibling::text:h[@text:level = current()/@text:level])
                                                            + $precedingChapterLevel9
                                                            + $startValue"/>
                                            </xsl:when>
                                            <xsl:when test="@text:level='10'">
                                                <xsl:value-of select="count(preceding-sibling::text:h[@text:level = current()/@text:level])
                                                            + $precedingChapterLevel10
                                                            + $startValue"/>
                                            </xsl:when>
                                        </xsl:choose>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:choose>
                                            <xsl:when test="@text:level='1'">
                                                <xsl:value-of select="count(preceding-sibling::text:h[@text:level = current()/@text:level])
                                                            + $precedingChapterLevel1
                                                            + 1"/>
                                            </xsl:when>
                                            <xsl:when test="@text:level='2'">
                                                <xsl:value-of select="count(preceding-sibling::text:h[@text:level = current()/@text:level])
                                                            + $precedingChapterLevel2
                                                            + 1"/>
                                            </xsl:when>
                                            <xsl:when test="@text:level='3'">
                                                <xsl:value-of select="count(preceding-sibling::text:h[@text:level = current()/@text:level])
                                                            + $precedingChapterLevel3
                                                            + 1"/>
                                            </xsl:when>
                                            <xsl:when test="@text:level='4'">
                                                <xsl:value-of select="count(preceding-sibling::text:h[@text:level = current()/@text:level])
                                                            + $precedingChapterLevel4
                                                            + 1"/>
                                            </xsl:when>
                                            <xsl:when test="@text:level='5'">
                                                <xsl:value-of select="count(preceding-sibling::text:h[@text:level = current()/@text:level])
                                                            + $precedingChapterLevel5
                                                            + 1"/>
                                            </xsl:when>
                                            <xsl:when test="@text:level='6'">
                                                <xsl:value-of select="count(preceding-sibling::text:h[@text:level = current()/@text:level])
                                                            + $precedingChapterLevel6
                                                            + 1"/>
                                            </xsl:when>
                                            <xsl:when test="@text:level='7'">
                                                <xsl:value-of select="count(preceding-sibling::text:h[@text:level = current()/@text:level])
                                                            + $precedingChapterLevel7
                                                            + 1"/>
                                            </xsl:when>
                                            <xsl:when test="@text:level='8'">
                                                <xsl:value-of select="count(preceding-sibling::text:h[@text:level = current()/@text:level])
                                                            + $precedingChapterLevel8
                                                            + 1"/>
                                            </xsl:when>
                                            <xsl:when test="@text:level='9'">
                                                <xsl:value-of select="count(preceding-sibling::text:h[@text:level = current()/@text:level])
                                                            + $precedingChapterLevel9
                                                            + 1"/>
                                            </xsl:when>
                                            <xsl:when test="@text:level='10'">
                                                <xsl:value-of select="count(preceding-sibling::text:h[@text:level = current()/@text:level])
                                                            + $precedingChapterLevel10
                                                            + 1"/>
                                            </xsl:when>
                                        </xsl:choose>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="get-absolute-chapter-no">
                                    <xsl:with-param name="precedingChapterLevel1"    select="$precedingChapterLevel1"/>
                                    <xsl:with-param name="collectedGlobalData"       select="$collectedGlobalData"/>
                                </xsl:call-template>
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:text> &#160; &#160;</xsl:text>
                    </xsl:if>
                    <xsl:apply-templates>
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    </xsl:apply-templates>

                </xsl:element>
            </xsl:when>


            <!--+++++ HTML 4.0 INLINED WAY  +++++-->
            <xsl:when test="$outputType = 'CSS_INLINED'">
                <xsl:variable name="headertyp" select="concat('h', @text:level)"/>
                <xsl:element name="{$headertyp}">

                    <xsl:apply-templates select="@text:style-name">
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    </xsl:apply-templates>

                    <!-- writing out a chapter number if desired (noticable when a corresponding 'text:outline-style' exist -->
                    <xsl:if test="$office:styles/text:outline-style/text:outline-level-style[@text:level = current()/@text:level]/@text:style-name">

                        <!-- the chapter number is the sum of 'text:start-value' and preceding siblings of 'text:h' with the same 'text:level' -->
                        <xsl:value-of select="count(preceding-sibling::text:h[@text:level = current()/@text:level])
                                            + $office:styles/text:outline-style/text:outline-level-style[@text:level = current()/@text:level]/@text:start-value"/>
                        <xsl:text> &#160; &#160;</xsl:text>
                    </xsl:if>

                </xsl:element>
            </xsl:when>

            <!-- 2DO: add Chapter No. for PALM and WML <-> problem nested apply-templates -->

            <!--+++++ PALM 3.2 SUBSET INLINED WAY  +++++-->
            <xsl:when test="$outputType = 'PALM'">
                <xsl:variable name="headertyp" select="concat('h', @text:level)"/>
                <xsl:element name="{$headertyp}">


                    <!-- All children content have to be nested in the styles (e.g. <i><b>ANY CONTENT</b></i>)
                         for this xsl:apply-templates will be called later / implicit -->
                    <xsl:call-template name="create-attribute-ALIGN">
                        <!-- getting the css styles for the style name (mapped by style-mapping.xsl) -->
                        <xsl:with-param name="styleProperties" select="$collectedGlobalData/allstyles/*[name()=current()/@text:style-name]"/>
                    </xsl:call-template>
                </xsl:element>
            </xsl:when>

            <!--+++++ WML / WAP  +++++-->
            <xsl:otherwise>
                <!-- no nested p tags in wml1.1 allowed -->
                <xsl:choose>
                    <xsl:when test="ancestor::*[contains($wap-paragraph-elements, name())]">
                        <!-- since no header styles exist, an emphasis is used -->
                        <xsl:element name="em">

                            <!-- writing out a chapter number if desired (noticable when a corresponding 'text:outline-style' exist -->
                            <xsl:if test="$office:styles/text:outline-style/text:outline-level-style[@text:level = current()/@text:level]/@text:style-name">

                                <!-- the chapter number is the sum of 'text:start-value' and preceding siblings of 'text:h' with the same 'text:level' -->
                                <xsl:value-of select="count(preceding-sibling::text:h[@text:level = current()/@text:level])
                                                    + $office:styles/text:outline-style/text:outline-level-style[@text:level = current()/@text:level]/@text:start-value"/>
                                <xsl:text> &#160; &#160;</xsl:text>
                            </xsl:if>

                            <xsl:apply-templates select="@text:style-name">
                                <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                            </xsl:apply-templates>

                        </xsl:element>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:element name="p">
                            <!-- since no header styles exist, an emphasis is used -->
                            <xsl:element name="em">
                                <xsl:call-template name="apply-styles-and-content">
                                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                </xsl:call-template>
                            </xsl:element>
                        </xsl:element>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>



    <!-- ************* -->
    <!-- *** Link  *** -->
    <!-- ************* -->

    <xsl:template match="text:a | draw:a">
        <xsl:param name="collectedGlobalData"/>

        <xsl:call-template name="create-common-link">
            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
        </xsl:call-template>
    </xsl:template>


    <xsl:template name="create-common-link">
        <xsl:param name="collectedGlobalData"/>

        <xsl:choose>
            <xsl:when test="not($outputType = 'WML')">
                <xsl:element name="a">
                    <xsl:attribute name="href"><xsl:value-of select="@xlink:href"/></xsl:attribute>
                    <!--<xsl:attribute name="class">ContentLink</xsl:attribute>-->
                    <xsl:call-template name="apply-styles-and-content">
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    </xsl:call-template>
                </xsl:element>
            </xsl:when>
            <xsl:otherwise>
                <!-- no nested p tags in wml1.1 allowed -->
                <xsl:choose>
                    <xsl:when test="ancestor::*[contains($wap-paragraph-elements, name())]">
                        <xsl:element name="a">
                            <xsl:attribute name="href"><xsl:value-of select="@xlink:href"/></xsl:attribute>
                            <xsl:apply-templates select="descendant::text()"/>
                        </xsl:element>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:element name="p">
                            <xsl:element name="a">
                                <xsl:attribute name="href"><xsl:value-of select="@xlink:href"/></xsl:attribute>
                                <xsl:apply-templates select="descendant::text()"/>
                            </xsl:element>
                        </xsl:element>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>





    <!-- ******************* -->
    <!-- *** Image Link  *** -->
    <!-- ******************* -->

    <xsl:template match="draw:image">
        <xsl:param name="collectedGlobalData"/>

        <!-- NO IMAGES SUPPLIED FOR WAP OR PALM -->
        <xsl:if test="$outputType = 'CSS_HEADER' or $outputType = 'CSS_INLINED'">

            <xsl:element name="img">
                <xsl:if test="@svg:width">
                    <xsl:attribute name="width">
                        <xsl:call-template name="convert2pixel">
                            <xsl:with-param name="value" select="@svg:width"/>
                        </xsl:call-template>
                    </xsl:attribute>
                </xsl:if>
                <xsl:if test="@svg:height">
                    <xsl:attribute name="height">
                        <xsl:call-template name="convert2pixel">
                            <xsl:with-param name="value" select="@svg:height"/>
                        </xsl:call-template>
                    </xsl:attribute>
                </xsl:if>
                <xsl:if test="svg:desc">
                    <xsl:attribute name="alt">
                        <xsl:value-of select="svg:desc"/>
                    </xsl:attribute>
                </xsl:if>
                <xsl:choose>
                     <!-- for images jared in open office document -->
                    <xsl:when test="contains(@xlink:href, '#Pictures/')">
                        <!-- creating an absolute http URL to the packed image file -->
                        <xsl:attribute name="src"><xsl:value-of select="concat($jaredRootURL, '/Pictures/', substring-after(@xlink:href, '#Pictures/'), $optionalURLSuffix)"/></xsl:attribute>
                    </xsl:when>
<!--                    Due to a XT bug no DOS ':' before DRIVE letter is allowed, it would result in a unkown protoco exception, but a file URL for a DOS
						path needs the DRIVE letter, therefore all relative URLs remain relativ

					<xsl:when test="contains(@xlink:href,'//') or (substring(@xlink:href,2,1) = ':') or starts-with(@xlink:href, '/')">
                        <xsl:attribute name="src"><xsl:value-of select="@xlink:href"/></xsl:attribute>
                    </xsl:when>
                    <xsl:otherwise>
                        <!~~ creating a absolute path/URL for the referenced resource ~~>
                        <xsl:attribute name="src"><xsl:value-of select="concat($absoluteSourceDirRef, @xlink:href, $optionalURLSuffix)"/></xsl:attribute>
                    </xsl:otherwise>
-->
					<xsl:otherwise>
                        <xsl:attribute name="src"><xsl:value-of select="@xlink:href"/></xsl:attribute>
                    </xsl:otherwise>
                </xsl:choose>

                <xsl:call-template name="apply-styles-and-content">
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                </xsl:call-template>
            </xsl:element>
            <!-- adding a line break to make the presentation more even with the OOo view -->
            <xsl:element name="br"/>
        </xsl:if>
    </xsl:template>



    <!-- ******************** -->
    <!-- *** ordered list *** -->
    <!-- ******************** -->

    <xsl:template match="text:ordered-list">
        <xsl:param name="collectedGlobalData"/>

            <xsl:choose>
                <!--+++++ CSS (CASCADING STLYE SHEET) HEADER STYLE WAY +++++-->
                <xsl:when test="$outputType = 'CSS_HEADER'">
                    <xsl:element name="ol">
                        <xsl:call-template name="apply-styles-and-content">
                            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                        </xsl:call-template>
                    </xsl:element>
                </xsl:when>
                <!--+++++ HTML 4.0 INLINED WAY  +++++-->
                <xsl:when test="$outputType = 'CSS_INLINED'">
                    <xsl:element name="ol">
                        <xsl:call-template name="apply-styles-and-content">
                            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                        </xsl:call-template>
                    </xsl:element>
                </xsl:when>
                <!--+++++ PALM 3.2 SUBSET AND WAP INLINED WAY  +++++-->
                <xsl:when test="$outputType = 'PALM'">
                    <xsl:element name="ol">
                        <xsl:call-template name="apply-styles-and-content">
                            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                        </xsl:call-template>
                    </xsl:element>
                </xsl:when>
                <!--+++++ WML / WAP  +++++-->
                <xsl:otherwise>
                    <xsl:choose>
                        <!-- simulating content break of capsulated list elements -->
                        <xsl:when test="ancestor::text:list-item">
                            <xsl:choose>
                                <xsl:when test="ancestor::*[contains($wap-paragraph-elements, name())]">
                                    <!-- simulating content break of capsulated list elements -->
                                    <xsl:element name="br"></xsl:element>
                                    <xsl:call-template name="apply-styles-and-content">
                                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                    </xsl:call-template>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:element name="p">
                                        <!-- simulating content break of capsulated list elements -->
                                        <xsl:element name="br"></xsl:element>
                                        <xsl:call-template name="apply-styles-and-content">
                                            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                        </xsl:call-template>
                                    </xsl:element>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:call-template name="apply-styles-and-content">
                                <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                            </xsl:call-template>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:otherwise>
            </xsl:choose>
    </xsl:template>



    <!-- ********************** -->
    <!-- *** unordered list *** -->
    <!-- ********************** -->

    <xsl:template match="text:unordered-list">
        <xsl:param name="collectedGlobalData"/>

        <xsl:choose>
            <!--+++++ CSS (CASCADING STLYE SHEET) HEADER STYLE WAY +++++-->
            <xsl:when test="$outputType = 'CSS_HEADER'">
                <xsl:element name="ul">
                    <xsl:call-template name="apply-styles-and-content">
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    </xsl:call-template>
                </xsl:element>
            </xsl:when>

            <!--+++++ HTML 4.0 INLINED WAY  +++++-->
            <xsl:when test="$outputType = 'CSS_INLINED'">
                <xsl:element name="ul">
                    <xsl:call-template name="apply-styles-and-content">
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    </xsl:call-template>
                </xsl:element>
            </xsl:when>

            <!--+++++ PALM 3.2 SUBSET AND WAP INLINED WAY  +++++-->
            <xsl:when test="$outputType = 'PALM'">
                <xsl:element name="ul">
                    <xsl:call-template name="apply-styles-and-content">
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    </xsl:call-template>
                </xsl:element>
            </xsl:when>

            <!--+++++ WML / WAP  +++++-->
            <xsl:otherwise>
                <xsl:choose>
                    <!-- simulating content break of capsulated list elements -->
                    <xsl:when test="ancestor::text:list-item">
                        <xsl:choose>
                            <xsl:when test="ancestor::*[contains($wap-paragraph-elements, name())]">
                                <!-- simulating content break of capsulated list elements -->
                                <xsl:element name="br"></xsl:element>
                                <xsl:call-template name="apply-styles-and-content">
                                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:element name="p">
                                    <!-- simulating content break of capsulated list elements -->
                                    <xsl:element name="br"></xsl:element>
                                    <xsl:call-template name="apply-styles-and-content">
                                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                    </xsl:call-template>
                                </xsl:element>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="apply-styles-and-content">
                            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>



    <!-- ****************** -->
    <!-- *** list item  *** -->
    <!-- ****************** -->

    <xsl:template match="text:list-item">
        <xsl:param name="collectedGlobalData"/>

        <xsl:choose>
            <!--+++++ CSS (CASCADING STLYE SHEET) HEADER STYLE WAY +++++-->
            <xsl:when test="$outputType = 'CSS_HEADER'">
                <xsl:element name="li">
                    <xsl:call-template name="apply-styles-and-content">
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    </xsl:call-template>
                </xsl:element>
            </xsl:when>

            <!--+++++ HTML 4.0 INLINED WAY  +++++-->
            <xsl:when test="$outputType = 'CSS_INLINED'">
                <xsl:element name="li">
                    <xsl:call-template name="apply-styles-and-content">
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    </xsl:call-template>
                </xsl:element>
            </xsl:when>

            <!--+++++ PALM 3.2 SUBSET AND WAP INLINED WAY  +++++-->
            <xsl:when test="$outputType = 'PALM'">
                <xsl:element name="li">
                    <xsl:call-template name="apply-styles-and-content">
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    </xsl:call-template>
                </xsl:element>
            </xsl:when>

            <!--+++++ WML / WAP  +++++-->
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="ancestor::*[contains($wap-paragraph-elements, name())]">
                        <!-- simulating list elements -->
                        <xsl:for-each select="ancestor::text:list-item">*</xsl:for-each>
                        <xsl:text>* </xsl:text>
                        <xsl:call-template name="apply-styles-and-content">
                            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                        </xsl:call-template>
                        <!-- list item break simulation (not in a table)-->
                        <xsl:if test="not(ancestor::table:table-cell) or following-sibling::text:list-item">
                            <xsl:element name="br"/>
                        </xsl:if>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:element name="p">
                            <!-- simulating list elements -->
                            <xsl:for-each select="ancestor::text:list-item">*</xsl:for-each>
                            <xsl:text>* </xsl:text>
                            <xsl:call-template name="apply-styles-and-content">
                                <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                            </xsl:call-template>
                            <!-- list item break simulation (not in a table)-->
                            <xsl:if test="not(ancestor::table:table-cell) or following-sibling::text:list-item">
                                <xsl:element name="br"/>
                            </xsl:if>
                        </xsl:element>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>



    <!-- ********************************************** -->
    <!-- *** Text Section (contains: draw:text-box) *** -->
    <!-- ********************************************** -->

        <xsl:template match="text:section">
        <xsl:param name="collectedGlobalData"/>

        <xsl:if test="not(contains(@text:display, 'none'))">
            <xsl:choose>
                <!--+++++ CSS (CASCADING STLYE SHEET) HEADER STYLE WAY +++++-->
                <xsl:when test="$outputType = 'CSS_HEADER'">
                    <xsl:element name="span">
                        <xsl:call-template name="apply-styles-and-content">
                            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                        </xsl:call-template>
                    </xsl:element>
                </xsl:when>
                <!--+++++ HTML 4.0 INLINED WAY  +++++-->
                <xsl:when test="$outputType = 'CSS_INLINED'">
                    <xsl:element name="span">
                        <xsl:call-template name="apply-styles-and-content">
                            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                        </xsl:call-template>
                    </xsl:element>
                </xsl:when>
                <!--+++++ PALM 3.2 SUBSET INLINED WAY  +++++-->
                <xsl:when test="$outputType = 'PALM'">
                    <xsl:choose>
                        <xsl:when test="name(parent::*) = 'text:list-item'">
                                        <xsl:call-template name="apply-styles-and-content">
                                            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                        </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:element name="p">
                                <xsl:call-template name="apply-styles-and-content">
                                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                </xsl:call-template>
                            </xsl:element>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <!--+++++ WML / WAP  +++++-->
                <xsl:otherwise>
                    <xsl:choose>
                        <xsl:when test="not($outputType = 'WML')">
                            <xsl:element name="a">
                                <xsl:attribute name="href"><xsl:value-of select="@xlink:href"/></xsl:attribute>
                                <xsl:call-template name="apply-styles-and-content">
                                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                </xsl:call-template>
                            </xsl:element>
                        </xsl:when>
                        <xsl:otherwise>
                            <!-- no nested p tags in wml1.1 allowed -->
                            <xsl:choose>
                                <xsl:when test="ancestor::*[contains($wap-paragraph-elements, name())]">
                                    <xsl:call-template name="apply-styles-and-content">
                                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                    </xsl:call-template>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:element name="p">
                                        <xsl:call-template name="apply-styles-and-content">
                                            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                        </xsl:call-template>
                                    </xsl:element>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:template>



    <xsl:template match="text:line-break">
        <xsl:element name="br"/>
    </xsl:template>


<!--
    TABHANDLING PROBLEM: Tabs are possible to be shown in the HTML text file, but will be later stripped as whitespaces.
        To prevent this one way would be the PRE tag which unfortunately ALWAYS result into a line-break. No surrounding NOBR tags help.

    <xsl:template match="text:tab-stop">
        <xsl:if test="not(preceding-sibling::text:tab-stop)">
            <xsl:element name="pre"><xsl:text>&#9;</xsl:text><xsl:for-each select="following-sibling::text:tab-stop"><xsl:text>&#9;</xsl:text></xsl:for-each></xsl:element>
        </xsl:if>
     </xsl:template>

    <xsl:template match="text:tab-stop"><xsl:text>&#9;</xsl:text></xsl:template>
-->
    <!-- HOTFIX: 8 non-breakable-spaces instead of a TAB is a hack sometimes less Tabs are needed and the code more difficult to read -->
    <xsl:template match="text:tab-stop">
        <xsl:call-template name="write-breakable-whitespace">
            <xsl:with-param name="whitespaces" select="8"/>
        </xsl:call-template>
    </xsl:template>

    <!-- currently there have to be an explicit call of the style attribute nodes, maybe the attributes nodes have no priority only order relevant-->
    <!-- STRANGE: checked with biorythm.sxc a simple xsl:apply-templates did not recognice the styles. Maybe caused by the template match order?  -->
    <xsl:template name="apply-styles-and-content">
        <xsl:param name="collectedGlobalData"/>

        <xsl:apply-templates select="@text:style-name | @draw:style-name | @draw:text-style-name | @table:style-name"><!-- | @presentation:style-name -->
            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
        </xsl:apply-templates>

        <xsl:apply-templates>
            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
        </xsl:apply-templates>
    </xsl:template>


    <xsl:template match="@text:style-name | @draw:style-name | @draw:text-style-name | @table:style-name"><!-- | @presentation:style-name-->
        <xsl:param name="collectedGlobalData"/>

        <xsl:choose>
            <!--+++++ CSS (CASCADING STLYE SHEET) HEADER STYLE WAY +++++-->
            <xsl:when test="$outputType = 'CSS_HEADER'">
                <xsl:attribute name="class"><xsl:value-of select="translate(., '. %()/\', '')"/></xsl:attribute>
            </xsl:when>

            <!--+++++ HTML 4.0 INLINED WAY  +++++-->
            <xsl:when test="$outputType = 'CSS_INLINED'">
                <xsl:attribute name="style"><xsl:value-of select="$collectedGlobalData/allstyles/*[name()=current()/.]"/></xsl:attribute>
            </xsl:when>

            <!--+++++ PALM 3.2 SUBSET INLINED WAY  and  WML / WAP   +++++-->
            <xsl:when test="$outputType = 'PALM' or $outputType = 'WML'">
                <!-- getting the css styles for the style name (mapped by style-mapping.xsl) -->
                <xsl:variable name="styleProperties" select="$collectedGlobalData/allstyles/*[name()=current()/.]"/>
                <!-- changing the context node -->
                <xsl:for-each select="parent::*">
                    <xsl:call-template name="create-nested-format-tags">
                        <xsl:with-param name="styleProperties" select="$styleProperties"/>
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:when>
        </xsl:choose>
    </xsl:template>


    <xsl:template match="text:sequence">
        <xsl:param name="collectedGlobalData"/>

        <xsl:apply-templates>
            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
        </xsl:apply-templates>
    </xsl:template>


</xsl:stylesheet>
