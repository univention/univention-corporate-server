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
                xmlns:xalan="http://xml.apache.org/xalan"
                xmlns:java="http://xml.apache.org/xslt/java"
                exclude-result-prefixes="java">


    <xsl:template name="write-style-properties">
        <xsl:param name="styleAttributePath"/>

        <xsl:choose>
            <!--+++++ CSS PROPERTIES  +++++-->
            <xsl:when test="$outputType = 'CSS_HEADER' or $outputType = 'CSS_INLINED'">

                <xsl:for-each select="$styleAttributePath">
                <!-- isDebugModeMESSAGE:
                    <xsl:message> Name:<xsl:value-of select="name()"/> Value:<xsl:value-of select="."/></xsl:message>      -->


                    <!-- <!ATTLIST style:properties style:horizontal-pos (from-left|left|center|right|from-inside|inside|outside)#IMPLIED>-->
                    <!-- 2DO: is inside/from-inside also better showable ? -->
                    <!-- !!!! 2DO: Still there have to be placed a <br clear='all'/> to disable the flow!!!!-->
                    <!--           The OOo attribute 'style:number-wrapped-paragraphs' is currently ignored -->
                    <xsl:choose>
                        <xsl:when test='name(.)="style:wrap"'>
                            <xsl:choose>
                                <xsl:when test='.="left"'>
                                    <xsl:text>float: right; </xsl:text>
                                </xsl:when>
                                <xsl:when test='.="right"'>
                                    <xsl:text>float: left; </xsl:text>
                                </xsl:when>
                            </xsl:choose>
                        </xsl:when>

                        <xsl:when test='name(.) = "style:horizontal-pos"'>
                            <xsl:choose>
                                <xsl:when test='.="left"'>
                                    <xsl:text>align: left; </xsl:text>
                                </xsl:when>
                                <xsl:when test='.="right"'>
                                    <xsl:text>align: right; </xsl:text>
                                </xsl:when>
                                <xsl:when test='.="center"'>
                                    <xsl:text>align: center; </xsl:text>
                                </xsl:when>
                            </xsl:choose>
                        </xsl:when>
<!-- results into a bad view (overlapped) in Mozilla 1.0
                        <xsl:when test='name(.) = "table:align"'>
                            <xsl:choose>
                                <xsl:when test='.="left"'>
                                    <xsl:text>float: right; </xsl:text>
                                </xsl:when>
                                <xsl:when test='.="right"'>
                                    <xsl:text>float: left; </xsl:text>
                                </xsl:when>
                            </xsl:choose>
                        </xsl:when>
-->

                        <!-- PADDING for all variations: fo:padding, fo:padding-top, fo:padding-bottom, fo:padding-left, fo:padding-right -->
                        <xsl:when test='contains(name(.),"fo:padding")'>
                            <xsl:text>padding: </xsl:text>
                            <xsl:value-of select="."/>
                            <xsl:text>; </xsl:text>
                        </xsl:when>
                        <!--
                        fo:border
                        fo:border-top
                        fo:border-bottom
                        fo:border-left
                        fo:border-right

                            At present, all four borders must be set simultaneously by using either
                            the fo:border property or by attaching all four of the other border
                            properties to an item set element. In the latter case, if one or more
                            of the properties is missing their values are assumed to be none. The
                            only border styles supported are none or hidden, solid, and double. Any
                            other border style specified is displayed as solid. Transparent borders
                            are not supported and the border widths thin, medium, and thick are
                            mapped to lengths. In addition, only some distinct border widths are
                            supported. Unsupported widths are rounded up to the next supported
                            width.
                            If there are no padding properties specified within the same
                            item set element, a default padding is used for sides that have a
                            border. A value of 0cm is used for sides without a border.
                            (cp. wd-so-xml-text.sdw)
                        -->

<!--2DO START: change measurement equally -->
                        <xsl:when test='name(.)="fo:border"'>
                            <xsl:choose>
                                <!-- changing the distance measure: inch to in -->
                                <xsl:when test="contains(., 'ch')">
                                    <xsl:text>border-width:</xsl:text><xsl:value-of select="substring-before(.,'ch ')"/><xsl:text>; </xsl:text>
                                    <xsl:text>border-style:</xsl:text><xsl:value-of select="substring-before(substring-after(.,'ch '), ' ')"/><xsl:text>; </xsl:text>
                                    <xsl:text>border-color:</xsl:text><xsl:value-of select="substring-after(substring-after(.,'ch '), ' ')"/><xsl:text>; </xsl:text>
                                </xsl:when>
                                <xsl:when test="contains(., 'cm')">
                                    <xsl:text>border-width:</xsl:text><xsl:value-of select="substring-before(.,' ')"/><xsl:text>; </xsl:text>
                                    <xsl:text>border-style:</xsl:text><xsl:value-of select="substring-before(substring-after(.,'cm '), ' ')"/><xsl:text>; </xsl:text>
                                    <xsl:text>border-color:</xsl:text><xsl:value-of select="substring-after(substring-after(.,'cm '), ' ')"/><xsl:text>; </xsl:text>
                                </xsl:when>
                                <xsl:when test="contains(., 'pt')">
                                    <xsl:text>border-width:</xsl:text><xsl:value-of select="substring-before(.,' ')"/><xsl:text>; </xsl:text>
                                    <xsl:text>border-style:</xsl:text><xsl:value-of select="substring-before(substring-after(.,'pt '), ' ')"/><xsl:text>; </xsl:text>
                                    <xsl:text>border-color:</xsl:text><xsl:value-of select="substring-after(substring-after(.,'pt '), ' ')"/><xsl:text>; </xsl:text>
                                </xsl:when>
                            </xsl:choose>
                        </xsl:when>
                        <xsl:when test='name(.)="fo:border-top"'>
                            <xsl:text>border-top: </xsl:text><xsl:value-of select="."/><xsl:text>; </xsl:text>
                        </xsl:when>
                        <xsl:when test='name(.)="fo:border-bottom"'>
                            <xsl:text>border-bottom: </xsl:text><xsl:value-of select="."/><xsl:text>; </xsl:text>
                        </xsl:when>
                        <xsl:when test='name(.)="fo:border-left"'>
                            <xsl:text>border-left: </xsl:text><xsl:value-of select="."/><xsl:text>; </xsl:text>
                        </xsl:when>
                        <xsl:when test='name(.)="fo:border-right"'>
                            <xsl:text>border-right: </xsl:text><xsl:value-of select="."/><xsl:text>; </xsl:text>
                        </xsl:when>
                        <xsl:when test='name(.)="style:column-width"'>
                            <xsl:choose>
                                <!-- changing the distance measure: inch to in -->
                                <xsl:when test="contains(., 'ch')">
                                    <xsl:text>width:</xsl:text><xsl:value-of select="substring-before(.,'ch')"/><xsl:text>; </xsl:text>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:text>width:</xsl:text><xsl:value-of select="."/><xsl:text>; </xsl:text>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:when>
                        <xsl:when test='name(.)="style:row-height"'>
                            <xsl:choose>
                                <!-- changing the distance measure: inch to in -->
                                <xsl:when test="contains(., 'ch')">
                                    <xsl:text>height:</xsl:text><xsl:value-of select="substring-before(.,'ch')"/><xsl:text>; </xsl:text>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:text>height:</xsl:text><xsl:value-of select="."/><xsl:text>; </xsl:text>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:when>
                        <xsl:when test='name(.)="fo:width"'>
                            <xsl:choose>
                                <!-- changing the distance measure: inch to in -->
                                <xsl:when test="contains(., 'ch')">
                                    <xsl:text>width:</xsl:text><xsl:value-of select="substring-before(.,'ch')"/><xsl:text>; </xsl:text>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:text>width:</xsl:text><xsl:value-of select="."/><xsl:text>; </xsl:text>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:when>
<!--2DO END: change measurement equally -->
                        <xsl:when test='name(.)="fo:font-style"'>
                            <xsl:value-of select="substring-after(name(.), ':')"/><xsl:text>:</xsl:text><xsl:value-of select="."/><xsl:text>; </xsl:text>
                        </xsl:when>
                        <xsl:when test='name(.)="style:font-name"'>
                            <xsl:text>font-family:</xsl:text>
                                <xsl:variable name="content" select="."/>
                                <xsl:value-of select="$office:font-decls/style:font-decl[@style:name=$content]/@fo:font-family"/>
                            <xsl:text>; </xsl:text>
                            <xsl:if test="contains($office:font-decls/style:font-decl[@style:name=$content]/@style:font-style-name, 'Italic')">
                                <xsl:text>font-style:italic; </xsl:text>
                            </xsl:if>
                            <xsl:if test="contains($office:font-decls/style:font-decl[@style:name=$content]/@style:font-style-name, 'Bold')">
                                <xsl:text>font-weight:bold; </xsl:text>
                            </xsl:if>
                        </xsl:when>
                        <xsl:when test='name(.)="fo:font-weight"'>
                            <xsl:value-of select="substring-after(name(.), ':')"/><xsl:text>:</xsl:text><xsl:value-of select="."/><xsl:text>; </xsl:text>
                        </xsl:when>
                        <xsl:when test='name(.)="fo:font-size"'>
                            <xsl:value-of select="substring-after(name(.), ':')"/><xsl:text>:</xsl:text><xsl:value-of select="."/><xsl:text>; </xsl:text>
                        </xsl:when>
                        <xsl:when test='name(.)="fo:font-family"'>
                            <xsl:value-of select="substring-after(name(.), ':')"/><xsl:text>:</xsl:text><xsl:value-of select="."/><xsl:text>; </xsl:text>
                        </xsl:when>
                        <xsl:when test='name(.)="fo:color"'>
                            <xsl:value-of select="substring-after(name(.), ':')"/><xsl:text>:</xsl:text><xsl:value-of select="."/><xsl:text>; </xsl:text>
                        </xsl:when>
                        <xsl:when test='name(.)="fo:margin-left"'>
                            <xsl:value-of select="substring-after(name(.), ':')"/><xsl:text>:</xsl:text><xsl:value-of select="."/><xsl:text>; </xsl:text>
                        </xsl:when>
                        <xsl:when test='name(.)="fo:margin-right"'>
                            <xsl:value-of select="substring-after(name(.), ':')"/><xsl:text>:</xsl:text><xsl:value-of select="."/><xsl:text>; </xsl:text>
                        </xsl:when>
                        <xsl:when test='name(.)="fo:margin-top"'>
                            <xsl:value-of select="substring-after(name(.), ':')"/><xsl:text>:</xsl:text><xsl:value-of select="."/><xsl:text>; </xsl:text>
                        </xsl:when>
                        <xsl:when test='name(.)="fo:margin-bottom"'>
                            <xsl:value-of select="substring-after(name(.), ':')"/><xsl:text>:</xsl:text><xsl:value-of select="."/><xsl:text>; </xsl:text>
                        </xsl:when>
                        <xsl:when test='name(.)="fo:line-height"'>
                            <xsl:value-of select="substring-after(name(.), ':')"/><xsl:text>:</xsl:text><xsl:value-of select="."/><xsl:text>; </xsl:text>
                        </xsl:when>
                        <xsl:when test='name(.)="fo:text-align"'>
                            <!-- IMPORTANT is necessary as table cell value alignment is decided by runtime over the valuetype
                                 Otherwise a table cell style-class will ALWAYS be overwritten by the run-time value -->
                             <xsl:choose>
                                <xsl:when test="contains(., 'start')">
                                    <xsl:text>text-align:left ! important; </xsl:text>
                                </xsl:when>
                                <xsl:when test="contains(., 'end')">
                                    <xsl:text>text-align:right ! important; </xsl:text>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:text>text-align:</xsl:text><xsl:value-of select='.'/><xsl:text> ! important; </xsl:text>
                                </xsl:otherwise>
                             </xsl:choose>
                        </xsl:when>
                        <xsl:when test='name(.)="fo:text-indent"'>
                            <xsl:value-of select="substring-after(name(.), ':')"/><xsl:text>:</xsl:text><xsl:value-of select="."/><xsl:text>; </xsl:text>
                        </xsl:when>
                        <xsl:when test='name(.)="style:text-background-color"'>
                            <xsl:text>background-color:</xsl:text><xsl:value-of select="."/><xsl:text>; </xsl:text>
                        </xsl:when>
                        <xsl:when test='name(.)="fo:background-color"'>
                            <xsl:text>background-color:</xsl:text><xsl:value-of select="."/><xsl:text>; </xsl:text>
                        </xsl:when>
                        <xsl:when test='name(.)="style:background-image"'>
                            <xsl:text>background-image:url(</xsl:text><xsl:value-of select="@xlink:href"/><xsl:text>); </xsl:text>
                            <xsl:choose>
                                <xsl:when test="@style:repeat = 'repeat'">
                                    <xsl:text>background-repeat:repeat; </xsl:text>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:text>background-repeat:no-repeat; </xsl:text>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:when>
                        <!-- text-shadow is a CSS2 feature and yet not common used in user-agents -->
                        <xsl:when test='name(.)="fo:text-shadow"'>
                            <xsl:value-of select="substring-after(name(.), ':')"/><xsl:text>:</xsl:text><xsl:value-of select="."/><xsl:text>; </xsl:text>
                        </xsl:when>
                        <xsl:when test='name(.)="style:text-crossing-out"'>
                            <xsl:if test='not(.="none")'>
                                <xsl:text>text-decoration:line-through; </xsl:text>
                            </xsl:if>
                        </xsl:when>
                        <xsl:when test='name(.)="style:text-underline"'>
                            <xsl:if test='not(.="none")'>
                                <xsl:text>text-decoration:underline; </xsl:text>
                            </xsl:if>
                        </xsl:when>
                        <xsl:when test='name(.)="style:text-position"'>
                            <xsl:if test='contains(., "sub")'>
                                <xsl:text>vertical-align:sub; </xsl:text>
                            </xsl:if>
                            <xsl:if test='contains(., "sup")'>
                                <xsl:text>vertical-align:sup; </xsl:text>
                            </xsl:if>
                        </xsl:when>
                        <!-- isDebugModeMESSAGE:
                        <xsl:otherwise>
                                <xsl:message>No transformation implemented for attribute-typ <xsl:value-of select="name(.)"/></xsl:message>
                        </xsl:otherwise>-->
                    </xsl:choose>
                </xsl:for-each>
            </xsl:when>
            <!--+++++ PALM 3.2 SUBSET AND WAP PROPERTIES  +++++-->
            <xsl:otherwise>
                <xsl:for-each select="$styleAttributePath">
                    <!-- isDebugModeMESSAGE:
                    <xsl:message> Name:<xsl:value-of select="name()"/> Value:<xsl:value-of select="."/></xsl:message>      -->

                    <!-- BUG WORK AROUND:
                    Due to a bug in the XT Processor, it is not possible to create serveral elements in variable and search over them,
                    after explicit conversion to nodeset
                    This generated sting identifier shall be later changed back to a set of elements
                    -->
                    <xsl:choose>
                        <!--*** FORMAT ATTRIBUTES ***-->

                        <!-- Italic -->
                        <xsl:when test='name(.)="fo:font-style"'>
                            <xsl:if test="contains(., 'italic') or contains(., 'oblique')">
                                <xsl:text>italic, </xsl:text>
                            </xsl:if>
                        </xsl:when>

                        <!-- Boldface -->
                        <xsl:when test='name(.)="fo:font-weight"'>
                            <xsl:if test="contains(., 'bold') or contains(., 'bolder')">
                                <xsl:text>bold, </xsl:text>
                            </xsl:if>
                        </xsl:when>

                        <!-- Underline -->
                        <xsl:when test='name(.)="style:text-underline"'>
                            <xsl:text>underline, </xsl:text>
                        </xsl:when>

                        <!-- Alignment -->
                        <xsl:when test='name(.)="fo:text-align"'>
                             <xsl:choose>
                                <xsl:when test="contains(., 'start')">
                                    <xsl:text>align:left, </xsl:text>
                                </xsl:when>
                                <xsl:when test="contains(., 'end')">
                                    <xsl:text>align:right, </xsl:text>
                                </xsl:when>
                                <xsl:when test="contains(., 'center')">
                                    <xsl:text>align:center, </xsl:text>
                                </xsl:when>
                             </xsl:choose>
                        </xsl:when>

                        <!-- strikethrough -->
                        <xsl:when test='name(.)="style:text-crossing-out"'>
                            <xsl:text>strike, </xsl:text>
                        </xsl:when>

                        <!-- Font - size (Palm: emulator transformed sizes to available set (e.g. 30 to (probably) 9)-->
                        <xsl:when test='name(.)="fo:font-size"'>
                            <xsl:text>size:</xsl:text><xsl:value-of select="."/><xsl:text>:size, </xsl:text>
                        </xsl:when>

                        <!-- Font - Color (PALM: but mostly only 2 available)
                            black (#000000)
                            gray (#808080)(rendered as dark gray)
                            silver (#C0C0C0)(rendered as light gray)
                            white (#FFFFFF)-->
                        <xsl:when test='name(.)="fo:color"'>
                            <xsl:choose>
                                <xsl:when test="contains(. , '#FFFFFF') or contains(. , '#ffffff') or contains(. , 'white') or contains(. , 'WHITE')">
                                    <xsl:text>color:#FFFFFF, </xsl:text>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:text>color:#000000, </xsl:text>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:when>


                        <!--*** TABLE ATTRIBUTES ***-->
                        <xsl:when test='name(.)="fo:font-size"'>
                            <xsl:text>size:</xsl:text><xsl:value-of select="."/><xsl:text>:size, </xsl:text>
                        </xsl:when>
                        <xsl:when test='name(.)="style:column-width"'>
                            <xsl:choose>
                                <!-- changing the distance measure: inch to in -->
                                <xsl:when test="contains(., 'ch')">
                                    <xsl:text>width:</xsl:text><xsl:value-of select="substring-before(.,'ch')"/><xsl:text>:width, </xsl:text>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:text>width:</xsl:text><xsl:value-of select="."/><xsl:text>:width; </xsl:text>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:when>
                        <xsl:when test='name(.)="style:row-height"'>
                            <xsl:choose>
                                <!-- changing the distance measure: inch to in -->
                                <xsl:when test="contains(., 'ch')">
                                    <xsl:text>height:</xsl:text><xsl:value-of select="substring-before(.,'ch')"/><xsl:text>:height; </xsl:text>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:text>height:</xsl:text><xsl:value-of select="."/><xsl:text>:height; </xsl:text>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:when>
                        <xsl:when test='name(.)="style:width"'> <!--earlier fo:width-->
                            <xsl:choose>
                                <!-- changing the distance measure: inch to in -->
                                <xsl:when test="contains(., 'ch')">
                                    <xsl:text>width:</xsl:text><xsl:value-of select="substring-before(.,'ch')"/><xsl:text>:width; </xsl:text>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:text>width:</xsl:text><xsl:value-of select="."/><xsl:text>:width; </xsl:text>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:when>
                    </xsl:choose>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>



<!-- 2DO: NAMING CONVENTION variable are written with '-' instead of case-sensitive writing -->



    <!-- ***** MEASUREMENT CONVERSIONS *****

     * 1 centimeter = 10 mm

     * 1 inch = 25.4 mm
        While the English have already seen the light (read: the metric system), the US
        remains loyal to this medieval system.

     * 1 didot point = 0.376065 mm
            The didot system originated in France but was used in most of Europe

     * 1 pica point = 0.35146 mm
            The Pica points system was developed in England and is used in Great-Britain and the US.

     * 1 PostScript point = 0.35277138 mm
            When Adobe created PostScript, they added their own system of points.
            There are exactly 72 PostScript points in 1 inch.

     * 1 pixel = 0.26458333.. mm   (by 96 dpi)
            Most pictures have the 96 dpi resolution, but the dpi variable may vary by stylesheet parameter
    -->


    <!-- changing measure to mm -->
    <xsl:template name="convert2mm">
        <xsl:param name="value"/>

        <xsl:param name="centimeter-in-mm"          select="10"/>
        <xsl:param name="inch-in-mm"                select="25.4"/>
        <xsl:param name="didot-point-in-mm"         select="0.376065"/>
        <xsl:param name="pica-point-in-mm"          select="0.35146"/>

        <xsl:choose>
            <xsl:when test="contains($value, 'cm')">
                <xsl:value-of select="round(number(substring-before($value,'cm' )) * $centimeter-in-mm)"/>
            </xsl:when>
            <xsl:when test="contains($value, 'in')">
                <xsl:value-of select="round(number(substring-before($value,'in' )) * $inch-in-mm)"/>
            </xsl:when>
            <xsl:when test="contains($value, 'dpt')">
                <xsl:value-of select="round(number(substring-before($value,'dpt')) * $didot-point-in-mm)"/>
            </xsl:when>
            <xsl:when test="contains($value, 'ppt')">
                <xsl:value-of select="round(number(substring-before($value,'ppt')) * $pica-point-in-mm)"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$value"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


    <!-- changing measure to cm -->
    <xsl:template name="convert2cm">
        <xsl:param name="value"/>

        <xsl:param name="centimeter-in-mm"          select="10"/>
        <xsl:param name="inch-in-mm"                select="25.4"/>
        <xsl:param name="didot-point-in-mm"         select="0.376065"/>
        <xsl:param name="pica-point-in-mm"          select="0.35146"/>

        <xsl:choose>
            <xsl:when test="contains($value, 'mm')">
                <xsl:value-of select="round(number(substring-before($value, 'mm')) div $centimeter-in-mm)"/>
            </xsl:when>
            <xsl:when test="contains($value, 'in')">
                <xsl:value-of select="round(number(substring-before($value, 'in')) div $centimeter-in-mm * $inch-in-mm)"/>
            </xsl:when>
            <xsl:when test="contains($value, 'dpt')">
                <xsl:value-of select="round(number(substring-before($value,'dpt')) div $centimeter-in-mm * $didot-point-in-mm)"/>
            </xsl:when>
            <xsl:when test="contains($value, 'ppt')">
                <xsl:value-of select="round(number(substring-before($value,'ppt')) div $centimeter-in-mm * $pica-point-in-mm)"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$value"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- changing measure to inch (cp. section comment) -->
    <xsl:template name="convert2inch">
        <xsl:param name="value"/>

        <xsl:param name="centimeter-in-mm"          select="10"/>
        <xsl:param name="inch-in-mm"                select="25.4"/>
        <xsl:param name="didot-point-in-mm"         select="0.376065"/>
        <xsl:param name="pica-point-in-mm"          select="0.35146"/>

        <xsl:choose>
            <xsl:when test="contains($value, 'mm')">
                <xsl:value-of select="round(number(substring-before($value, 'mm')) div $inch-in-mm)"/>
            </xsl:when>
            <xsl:when test="contains($value, 'cm')">
                <xsl:value-of select="round(number(substring-before($value, 'cm')) div $inch-in-mm * $centimeter-in-mm)"/>
            </xsl:when>
            <xsl:when test="contains($value, 'dpt')">
                <xsl:value-of select="round(number(substring-before($value,'dpt')) div $inch-in-mm * $didot-point-in-mm)"/>
            </xsl:when>
            <xsl:when test="contains($value, 'ppt')">
                <xsl:value-of select="round(number(substring-before($value,'ppt')) div $inch-in-mm * $pica-point-in-mm)"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$value"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


    <!-- changing measure to dpt (cp. section comment) -->
    <xsl:template name="convert2dpt">
        <xsl:param name="value"/>

        <xsl:param name="centimeter-in-mm"          select="10"/>
        <xsl:param name="inch-in-mm"                select="25.4"/>
        <xsl:param name="didot-point-in-mm"         select="0.376065"/>
        <xsl:param name="pica-point-in-mm"          select="0.35146"/>

        <xsl:choose>
            <xsl:when test="contains($value, 'mm')">
                <xsl:value-of select="round(number(substring-before($value, 'mm')) div $didot-point-in-mm)"/>
            </xsl:when>
            <xsl:when test="contains($value, 'cm')">
                <xsl:value-of select="round(number(substring-before($value, 'cm')) div $didot-point-in-mm * $centimeter-in-mm)"/>
            </xsl:when>
            <xsl:when test="contains($value, 'in')">
                <xsl:value-of select="round(number(substring-before($value, 'in')) div $didot-point-in-mm * $inch-in-mm)"/>
            </xsl:when>
            <xsl:when test="contains($value, 'ppt')">
                <xsl:value-of select="round(number(substring-before($value,'ppt')) div $didot-point-in-mm * $pica-point-in-mm)"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$value"/>
            </xsl:otherwise>
        </xsl:choose>

    </xsl:template>


    <!-- changing measure to ppt (cp. section comment) -->
    <xsl:template name="convert2ppt">
        <xsl:param name="value"/>

        <xsl:param name="centimeter-in-mm"          select="10"/>
        <xsl:param name="inch-in-mm"                select="25.4"/>
        <xsl:param name="didot-point-in-mm"         select="0.376065"/>
        <xsl:param name="pica-point-in-mm"          select="0.35146"/>

        <xsl:choose>
            <xsl:when test="contains($value, 'mm')">
                <xsl:value-of select="round(number(substring-before($value, 'mm')) div $pica-point-in-mm)"/>
            </xsl:when>
            <xsl:when test="contains($value, 'cm')">
                <xsl:value-of select="round(number(substring-before($value, 'cm')) div $pica-point-in-mm * $centimeter-in-mm)"/>
            </xsl:when>
            <xsl:when test="contains($value, 'in')">
                <xsl:value-of select="round(number(substring-before($value, 'in')) div $pica-point-in-mm * $inch-in-mm)"/>
            </xsl:when>
            <xsl:when test="contains($value, 'dpt')">
                <xsl:value-of select="round(number(substring-before($value,'dpt')) div $pica-point-in-mm * $didot-point-in-mm)"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$value"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


    <!-- changing measure to pixel by via parameter provided dpi (dots per inch) standard factor (cp. section comment) -->
    <xsl:template name="convert2pixel">
        <xsl:param name="value"/>

        <xsl:param name="centimeter-in-mm"          select="10"/>
        <xsl:param name="inch-in-mm"                select="25.4"/>
        <xsl:param name="didot-point-in-mm"         select="0.376065"/>
        <xsl:param name="pica-point-in-mm"          select="0.35146"/>
        <xsl:param name="pixel-in-mm"               select="$inch-in-mm div $dpi"/>

        <xsl:choose>
            <xsl:when test="contains($value, 'mm')">
                <xsl:value-of select="round(number(substring-before($value, 'mm')) div $pixel-in-mm)"/>
            </xsl:when>
            <xsl:when test="contains($value, 'cm')">
                <xsl:value-of select="round(number(substring-before($value, 'cm')) div $pixel-in-mm * $centimeter-in-mm)"/>
            </xsl:when>
            <xsl:when test="contains($value, 'in')">
                <xsl:value-of select="round(number(substring-before($value, 'in')) div $pixel-in-mm * $inch-in-mm)"/>
            </xsl:when>
            <xsl:when test="contains($value, 'dpt')">
                <xsl:value-of select="round(number(substring-before($value,'dpt')) div $pixel-in-mm * $didot-point-in-mm)"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$value"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

</xsl:stylesheet>
