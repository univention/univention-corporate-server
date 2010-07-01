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



    <!-- ****************************** -->
    <!-- *** style sheet processing *** -->
    <!-- ****************************** -->


    <xsl:template name='create-css-styleheader'>
        <xsl:comment>
            <xsl:text>The CSS style header method for setting styles</xsl:text>
        </xsl:comment>
        <xsl:element name="style">
            <xsl:attribute name="type">text/css</xsl:attribute>
            <xsl:comment>
                <xsl:text>

        </xsl:text>
                <xsl:call-template name="write-default-styles"/>

                <!-- THE STYLE PROPERTIES OF THE FIRST WRITTEN STYLE (PARENT) IS GIVEN OUT -->

                <!-- 1) styles from office:styles are possible parent from all (itself or office:automatic-styles).
                     Therefore they are created first.
                     Beginning with the top-level parents (the styles without any parent). -->
                <xsl:for-each select="$office:styles/style:style[not(@style:parent-style-name)]">

                    <xsl:call-template name="write-styleproperty-line"/>
                    <xsl:call-template name="write-styleproperty-lines-for-children"/>
                </xsl:for-each>

                <xsl:text> </xsl:text>

                <!-- 2) styles from office:automatic-styles can only be parent of styles from the office:automatic-styles section.
                     Beginning with top-level styles, again, all children style will be recursivly traversed -->
                <xsl:for-each select="$office:automatic-styles/style:style[not(@style:parent-style-name)]">
                    <xsl:call-template name="write-styleproperty-line">
                        <xsl:with-param name="searchOnlyInAutomaticStyles" select="true()"/>
                    </xsl:call-template>
                    <xsl:call-template name="write-styleproperty-lines-for-children">
                        <xsl:with-param name="searchOnlyInAutomaticStyles"/>
                    </xsl:call-template>
                </xsl:for-each>
            //</xsl:comment>
        </xsl:element>
    </xsl:template>


    <xsl:template name='write-styleproperty-line'>
        <xsl:param name="searchOnlyInAutomaticStyles"/>

        <xsl:variable name="styleProperties">
            <xsl:call-template name="write-style-properties">
                <xsl:with-param name="styleAttributePath"   select="current()/style:properties/@*"/>
            </xsl:call-template>
        </xsl:variable>

        <!-- do not write styles with no css property -->
        <xsl:if test="not(string-length($styleProperties) = 0)">
            <!-- write out the name of the current (parent) style in the CSS headersection (e.g. "span.myStyle") -->
            <xsl:call-template name="write-style-name">
                <xsl:with-param name="is-parent-style" select="true()"/>
            </xsl:call-template>

            <!-- the names of all styles children will be written out(office:style AND office:automatic-style) -->
            <xsl:call-template name="write-children-style-names">
                <xsl:with-param name="parentStyleName"          select="@style:name"/>
                <xsl:with-param name="parentStyleFamily"        select="@style:family"/>
                <xsl:with-param name="searchOnlyInAutomaticStyles"/>
            </xsl:call-template>

        <!-- the style properties of the first written style (parent) is given out -->
        <xsl:text> {
                </xsl:text>
                <xsl:value-of select="$styleProperties"/>
        <xsl:text>}
        </xsl:text>

        </xsl:if>



    </xsl:template>




    <!-- RECURSION WITH ENDCONDITON: adding style classes for all existing childs -->
    <xsl:template name='write-styleproperty-lines-for-children'>
        <xsl:param name="searchOnlyInAutomaticStyles"/>

        <xsl:variable name="parentStyleName"    select="@style:name"/>
        <xsl:variable name="parentStyleFamily"  select="@style:family"/>

        <xsl:if test="not(searchOnlyInAutomaticStyles)">
            <xsl:for-each select="../style:style[@style:family=$parentStyleFamily and @style:parent-style-name=$parentStyleName]">
                <xsl:call-template name="write-styleproperty-line"/>
                <xsl:call-template name="write-styleproperty-lines-for-children"/>
            </xsl:for-each>
        </xsl:if>
        <xsl:for-each select="$office:automatic-styles/style:style[@style:family=$parentStyleFamily and @style:parent-style-name=$parentStyleName]">
            <xsl:call-template name="write-styleproperty-line">
                <xsl:with-param name="searchOnlyInAutomaticStyles"/>
            </xsl:call-template>
            <xsl:call-template name="write-styleproperty-lines-for-children">
                <xsl:with-param name="searchOnlyInAutomaticStyles"/>
            </xsl:call-template>
        </xsl:for-each>
    </xsl:template>


    <xsl:template name="write-default-styles">

        <!-- some default attributes in xml have to be explicitly set in HTML (e.g. margin-top="0") -->
        <xsl:text>*.OOo_defaults</xsl:text>

                <xsl:for-each select="$office:styles/style:style">
                    <xsl:text>, </xsl:text>
                    <xsl:value-of select="concat('*.', translate(@style:name, '. %()/\', ''))"/>
                </xsl:for-each>

                <xsl:for-each select="$office:automatic-styles/style:style">
                    <xsl:text>, </xsl:text>
                    <xsl:value-of select="concat('*.', translate(@style:name, '. %()/\', ''))"/>
                </xsl:for-each>
        <!-- 2DO: the defaults might be better collected and written in a separated (XML) file -->
<xsl:text> {
                margin-top:0cm; margin-bottom:0cm; }
        </xsl:text>

        <xsl:for-each select="$office:styles/style:default-style">
            <xsl:call-template name="write-default-style"/>
        </xsl:for-each>

        <xsl:for-each select="$office:automatic-styles/style:default-style">
            <xsl:call-template name="write-default-style"/>
        </xsl:for-each>

    </xsl:template>



    <xsl:template name="write-default-style">
        <xsl:variable name="family-style" select="@style:family"/>

        <!-- some default attributes for format families (e.g. graphics, paragraphs, etc.) written as style:default-style -->
        <xsl:value-of select="concat('*.', translate($family-style, '. %()/\', ''), '_defaults')"/>

        <xsl:for-each select="$office:styles/style:style[@style:family = $family-style]">
            <xsl:text>, </xsl:text>
            <xsl:value-of select="concat('*.', translate(@style:name, '. %()/\', ''))"/>
        </xsl:for-each>

        <xsl:for-each select="$office:automatic-styles/style:style[@style:family = $family-style]">
            <xsl:text>, </xsl:text>
            <xsl:value-of select="concat('*.', translate(@style:name, '. %()/\', ''))"/>
        </xsl:for-each>


        <xsl:variable name="styleProperties">
            <xsl:call-template name="write-style-properties">
                <xsl:with-param name="styleAttributePath"   select="current()/style:properties/@*"/>
            </xsl:call-template>
        </xsl:variable>

        <!-- do not write styles with no css property -->
        <xsl:if test="not(string-length($styleProperties) = 0)">
        <!-- the style properties of the first written style (parent) is given out -->
        <xsl:text> {
                </xsl:text>
                <xsl:value-of select="$styleProperties"/>
        <xsl:text>}
        </xsl:text>
        </xsl:if>

    </xsl:template>


    <!--++
          The parent style will be written out!
          For each Style:family a prefix must be added
            <!ENTITY % styleFamily
            "(paragraph|text|section|table|table-column|table-row|table-cell|table-page|chart|graphics|default|drawing-page|presentation|control)">
        ++-->
    <xsl:template name="write-style-name">
        <xsl:param name="is-parent-style"/>

        <!-- This construct is for list elements. Whenever a paragraph element is being used as child of a list element the name paragraph style is been used for
            the list item. This can be switched as the paragaph style-name and the list-style-name are in the same element.
            Otherwise there would be formatting errors (e.g. margin-left will be used for the content in the list elment and not for the list element itself). -->
        <xsl:variable name="style-name">
            <xsl:choose>
                <xsl:when test="@style:list-style-name">
                    <xsl:value-of select="@style:list-style-name"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="@style:name"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:if test="not($is-parent-style)">
            <xsl:text>, </xsl:text>
        </xsl:if>

        <xsl:choose>
            <!-- normally 'p.' would be used as CSS element,
                 but header (h1, h2,...) are also from the style:family paragraph -->
            <xsl:when test="@style:family='paragraph'">
                <xsl:value-of select="concat('*.', translate($style-name, '. %()/\', ''))"/>
            </xsl:when>
            <xsl:when test="@style:family='text'">
                <xsl:value-of select="concat('*.', translate($style-name, '. %()/\', ''))"/>
            </xsl:when>
            <xsl:when test="@style:family='section'">
                <xsl:value-of select="concat('*.', translate($style-name, '. %()/\', ''))"/>
            </xsl:when>
            <xsl:when test="@style:family='table'">
                <xsl:value-of select="concat('table.', translate($style-name, '. %()/\', ''))"/>
            </xsl:when>
            <xsl:when test="@style:family='table-column'">
            <!-- as column styles have to be included as span styles AFTER the table (no two class attributes in TD allowed -->
                <xsl:value-of select="concat('*.', translate($style-name, '. %()/\', ''))"/>
            </xsl:when>
            <xsl:when test="@style:family='table-row'">
                <xsl:value-of select="concat('tr.', translate($style-name, '. %()/\', ''))"/>
            </xsl:when>
            <xsl:when test="@style:family='table-cell'">
                <xsl:value-of select="concat('*.', translate($style-name, '. %()/\', ''))"/>
            </xsl:when>
            <xsl:when test="@style:family='table-page'">
                <xsl:value-of select="concat('*.', translate($style-name, '. %()/\', ''))"/>
            </xsl:when>
            <xsl:when test="@style:family='chart'">
                <xsl:value-of select="concat('*.', translate($style-name, '. %()/\', ''))"/>
            </xsl:when>
            <xsl:when test="@style:family='graphics'">
                <xsl:value-of select="concat('*.', translate($style-name, '. %()/\', ''))"/>
            </xsl:when>
            <xsl:when test="@style:family='default'">
                <xsl:value-of select="concat('*.', translate($style-name, '. %()/\', ''))"/>
            </xsl:when>
            <xsl:when test="@style:family='drawing-page'">
                <xsl:value-of select="concat('*.', translate($style-name, '. %()/\', ''))"/>
            </xsl:when>
            <xsl:when test="@style:family='presentation'">
                <xsl:value-of select="concat('*.', translate($style-name, '. %()/\', ''))"/>
            </xsl:when>
            <xsl:when test="@style:family='control'">
                <xsl:value-of select="concat('*.', translate($style-name, '. %()/\', ''))"/>
            </xsl:when>
        </xsl:choose>
    </xsl:template>


    <!-- finding all style child of a section and give their styleIdentifier to the output -->
    <xsl:template name='write-children-style-names'>
        <xsl:param name="parentStyleName" select="@style:name"/>
        <xsl:param name="parentStyleFamily" select="@style:family"/>
        <xsl:param name="searchOnlyInAutomaticStyles"/>


        <!--** the names of all office:styles children will be written out
            ** (a automatic style can only have children in the office:automatic-style section) -->

        <!-- if NOT called from a office:automatic-style parent -->
        <xsl:if test="not(searchOnlyInAutomaticStyles)">
            <!-- for all children in the office:style section -->
            <xsl:for-each select="../style:style[@style:family=$parentStyleFamily and @style:parent-style-name=$parentStyleName]">
                <!-- write the style name in the css header -->
                <xsl:call-template name="write-style-name"/>

                <!-- search for child styles -->
                <xsl:call-template name="write-children-style-names">
                    <xsl:with-param name="parentStyleName" select="@style:name"/>
                    <xsl:with-param name="parentStyleFamily" select="@style:family"/>
                </xsl:call-template>

            </xsl:for-each>
        </xsl:if>

        <!--** the names of all office:automatic-styles children will be written out -->

        <!-- for all children in the office:automatic-style section -->
        <xsl:for-each select="$office:automatic-styles/style:style[@style:family=$parentStyleFamily and @style:parent-style-name=$parentStyleName]">
            <!-- write the style name in the css header -->
            <xsl:call-template name="write-style-name"/>

            <!-- search for child styles -->
            <xsl:call-template name="write-children-style-names">
                <xsl:with-param name="parentStyleName" select="@style:name"/>
                <xsl:with-param name="parentStyleFamily" select="@style:family"/>
                <xsl:with-param name="searchOnlyInAutomaticStyles"/>
            </xsl:call-template>

        </xsl:for-each>
    </xsl:template>

</xsl:stylesheet>
