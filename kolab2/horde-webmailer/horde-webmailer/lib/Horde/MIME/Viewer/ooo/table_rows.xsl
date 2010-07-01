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



    <!-- ********************************************* -->
    <!-- *** write (explicit) repeating table rows *** -->
    <!-- ********************************************* -->

    <xsl:template name="repeat-write-row">
        <xsl:param name="collectedGlobalData"/>
        <xsl:param name="allColumnStyleEntries"/>
        <xsl:param name="number-rows-repeated" select="1"/>
        <xsl:param name="maxRowLength"/>

        <xsl:choose>
            <!-- write an entry of a row and repeat calling this method until all elements are written out -->
            <xsl:when test="$number-rows-repeated > 1 and (table:table-cell/text() or table:table-cell/*)">
                <xsl:call-template name="write-row">
                    <xsl:with-param name="collectedGlobalData"       select="$collectedGlobalData"/>
                    <xsl:with-param name="allColumnStyleEntries"    select="$allColumnStyleEntries"/>
                    <xsl:with-param name="maxRowLength"             select="$maxRowLength"/>
                </xsl:call-template>

                <!-- 2DO: take variable from the output of repeated write-row and iterate giving out the variable -->
                <xsl:call-template name="repeat-write-row">
                    <xsl:with-param name="collectedGlobalData"       select="$collectedGlobalData"/>
                    <xsl:with-param name="allColumnStyleEntries"    select="$allColumnStyleEntries"/>
                    <xsl:with-param name="maxRowLength"             select="$maxRowLength"/>
                    <xsl:with-param name="number-rows-repeated"     select="$number-rows-repeated - 1"/>
                </xsl:call-template>
            </xsl:when>
            <!-- write a single entry of a row -->
            <xsl:otherwise>
                <xsl:call-template name="write-row">
                    <xsl:with-param name="collectedGlobalData"       select="$collectedGlobalData"/>
                    <xsl:with-param name="allColumnStyleEntries"    select="$allColumnStyleEntries"/>
                    <xsl:with-param name="maxRowLength"             select="$maxRowLength"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>



    <xsl:template name="write-row">
        <xsl:param name="collectedGlobalData"/>
        <xsl:param name="allColumnStyleEntries"/>
        <xsl:param name="maxRowLength"/>


        <xsl:element name="tr">
            <!-- writing the style of the row -->
            <xsl:call-template name='add-style-properties'>
                <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
            </xsl:call-template>

            <xsl:if test="$isDebugMode">
                <xsl:message>
*************************'tr' element has been added!</xsl:message>
            </xsl:if>

            <xsl:apply-templates select="table:table-cell">
                <xsl:with-param name="collectedGlobalData"       select="$collectedGlobalData"/>
                <xsl:with-param name="allColumnStyleEntries"    select="$allColumnStyleEntries"/>
                <xsl:with-param name="maxRowLength"             select="$maxRowLength"/>
            </xsl:apply-templates>

        </xsl:element>
    </xsl:template>


    <!-- **************************** -->
    <!-- *** HELPER: table styles *** -->
    <!-- **************************** -->

    <xsl:template name="add-style-properties">
        <xsl:param name="collectedGlobalData"/>
        <xsl:param name="allColumnStyleEntries"/>
        <xsl:param name="node-position"/>

        <xsl:choose>
            <!--+++++ CSS (CASCADING STLYE SHEET) HEADER STYLE WAY +++++-->
            <xsl:when test="$outputType = 'CSS_HEADER'">
                <xsl:attribute name="class">
                    <xsl:value-of select="translate(@table:style-name, '. %()/\', '')"/>
                </xsl:attribute>
            </xsl:when>

            <!--+++++ HTML 4.0 INLINED WAY  +++++-->
            <xsl:when test="$outputType = 'CSS_INLINED'">
                <xsl:attribute name="style">
                    <xsl:value-of select="$collectedGlobalData/allstyles/*[name()=current()/@table:style-name]"/>
                </xsl:attribute>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

</xsl:stylesheet>
