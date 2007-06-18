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
    <!-- *** hard attributed (inlined) properties  *** -->
    <!-- ********************************************* -->


    <!-- RESTRICTIONS:
            1)  As the styles-node-variables are NOT global, the style variables are not global, either!!
            2)  As a list of elements can only be added to a variable as a result tree fragment the
                extension is neccessary!!
    -->

    <!-- 2DO: Inline styles do not inherit from XML office defaults nor font:family defaults as the style header does
              (cp. stylesheet 'style_header.xsl' and the 'write-default-styles' template) -->

    <xsl:template name='create-all-inline-styles'>

        <!--** traversee all style trees and their branches collecting style properties **-->
        <xsl:element name="allstyles">
        <!--** traversee all office:styles trees beginning with the top-level styles**-->
            <xsl:for-each select="$office:styles/style:style[not(@style:parent-style-name)]">

                <!--** give out the style properties of the parent node **-->
                <xsl:call-template name='write-current-and-inherited-style-properties'>
                    <xsl:with-param name="styles-node"                  select="$office:styles"/>
                    <xsl:with-param name="style-family"                 select="@style:family"/>
                    <xsl:with-param name="style-name-tokenized"         select="translate(@style:name, '. %()/\', '')"/>
                </xsl:call-template>

                <!--** all office:styles children of the current top-level office:styles **-->
                <xsl:call-template name='for-all-templates-child-styles'>
                    <xsl:with-param name="parentStyleName"              select="@style:name"/>
                    <xsl:with-param name="parentStyleFamily"            select="@style:family"/>
                    <xsl:with-param name="style-name-tokenized"         select="translate(@style:name, '. %()/\', '')"/>
                </xsl:call-template>

                <!--** all office:automatic-styles children of the current top-level style **-->
                <xsl:call-template name='for-all-automatic-child-styles'>
                    <xsl:with-param name="parentStyleName"              select="@style:name"/>
                    <xsl:with-param name="parentStyleFamily"            select="@style:family"/>
                    <xsl:with-param name="style-name-tokenized"         select="translate(@style:name, '. %()/\', '')"/>
                </xsl:call-template>
            </xsl:for-each>

        <!--** traversee all office:automatic-styles trees beginning with the top-level styles **-->
            <xsl:for-each select="$office:automatic-styles/style:style[not(@style:parent-style-name)]">
                <!--** give out the style properties of the parent node **-->
                <xsl:call-template name='write-current-and-inherited-style-properties'>
                    <xsl:with-param name="styles-node"                  select="$office:automatic-styles"/>
                    <xsl:with-param name="style-family"                 select="@style:family"/>
                    <xsl:with-param name="style-name-tokenized"         select="translate(@style:name, '. %()/\', '')"/>
                </xsl:call-template>

                <!--** all children of the top-level office:automatic-styless  **-->
                <xsl:call-template name='for-all-automatic-child-styles'>
                    <xsl:with-param name="parentStyleName"              select="@style:name"/>
                    <xsl:with-param name="parentStyleFamily"            select="@style:family"/>
                    <xsl:with-param name="style-name-tokenized"         select="translate(@style:name, '. %()/\', '')"/>
                </xsl:call-template>
            </xsl:for-each>
        </xsl:element>
    </xsl:template>



    <xsl:template name='for-all-templates-child-styles'>
        <xsl:param name="parentStyleName"/>
        <xsl:param name="parentStyleFamily"/>
        <xsl:param name="style-name-tokenized"/>

        <xsl:for-each select="../style:style[@style:family=$parentStyleFamily and @style:parent-style-name=$parentStyleName]">
            <!--** give out the style properties of the current node **-->
            <xsl:element name="{$style-name-tokenized}">
                <xsl:call-template name='write-current-and-inherited-style-properties'>
                    <xsl:with-param name="styles-node"                  select="$office:styles"/>
                    <xsl:with-param name="style-family"                 select="@style:family"/>
                    <xsl:with-param name="style-name-tokenized"         select="translate(@style:name, '. %()/\', '')"/>
                </xsl:call-template>
            </xsl:element>

            <!--** for all template-children of the current office:styles  **-->
            <xsl:call-template name='for-all-templates-child-styles'>
                <xsl:with-param name="styles-node"                  select="$office:styles"/>
                <xsl:with-param name="parentStyleName"              select="@style:name"/>
                <xsl:with-param name="parentStyleFamily"            select="@style:family"/>
                <xsl:with-param name="style-name-tokenized"         select="translate(@style:name, '. %()/\', '')"/>
            </xsl:call-template>

            <!--** for all automatic-children of the current office:styles  **-->
            <xsl:call-template name='for-all-automatic-child-styles'>
                <xsl:with-param name="styles-node"                  select="$office:automatic-styles"/>
                <xsl:with-param name="parentStyleName"              select="@style:name"/>
                <xsl:with-param name="parentStyleFamily"            select="@style:family"/>
                <xsl:with-param name="style-name-tokenized"         select="translate(@style:name, '. %()/\', '')"/>
            </xsl:call-template>

        </xsl:for-each>
    </xsl:template>



    <xsl:template name='for-all-automatic-child-styles'>
        <xsl:param name="styles-node"/>
        <xsl:param name="parentStyleName"/>
        <xsl:param name="parentStyleFamily"/>
        <xsl:param name="style-name-tokenized"/>

        <xsl:for-each select="$office:automatic-styles/style:style[@style:family=$parentStyleFamily and @style:parent-style-name=$parentStyleName]">
            <!--** give out the style properties of the current node **-->
            <xsl:element name="{$style-name-tokenized}">
                <xsl:call-template name='write-current-and-inherited-style-properties'>
                    <xsl:with-param name="styles-node"                  select="$office:automatic-styles"/>
                    <xsl:with-param name="style-family"                 select="@style:family"/>
                    <xsl:with-param name="style-name-tokenized"         select="translate(@style:name, '. %()/\', '')"/>
                </xsl:call-template>
            </xsl:element>

            <!--** for all automatic-children of the current office:automatic-styles  **-->
            <xsl:call-template name='for-all-automatic-child-styles'>
                <xsl:with-param name="styles-node"                  select="$office:automatic-styles"/>
                <xsl:with-param name="parentStyleName"              select="@style:name"/>
                <xsl:with-param name="parentStyleFamily"            select="@style:family"/>
                <xsl:with-param name="style-name-tokenized"         select="translate(@style:name, '. %()/\', '')"/>
            </xsl:call-template>
        </xsl:for-each>
    </xsl:template>


    <xsl:template name='write-current-and-inherited-style-properties'>
        <xsl:param name="style-family"/>
        <xsl:param name="styles-node"/>
        <xsl:param name="style-name-tokenized"/>

        <xsl:element name="{$style-name-tokenized}">
            <xsl:variable name="current-style-name" select="@style:name"/>
            <xsl:variable name="parent-style-name" select="@style:parent-style-name"/>

            <xsl:variable name="new-property-list">
                <!--*** COLLECT STYLE ATTRIBUTES (only toplevel) ***-->
                <xsl:call-template name="write-style-properties">
                    <xsl:with-param name="styleAttributePath"   select="$styles-node/style:style[@style:family=$style-family and @style:name=$current-style-name]/style:properties/@*"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:choose>
                <!--*** @End: GIVE OUT All COLLECTED STYLE ATTRIBUTES (only toplevel) ***-->
                <xsl:when test="string-length($parent-style-name)=0">
                <!--** if no styleParent is given, the properties are given out at once **-->
                    <xsl:value-of select="normalize-space($new-property-list)"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:variable name="new-property-names">
                        <xsl:for-each select="$styles-node/style:style[@style:family=$style-family and @style:name=$current-style-name]/style:properties/@*">
                            <xsl:value-of select="name()"/>
                        </xsl:for-each>
                    </xsl:variable>
                    <!--** further attributes of the parent style must be collected **-->
                    <xsl:call-template name="add-parent-style-attributes">
                        <xsl:with-param name="property-name-list"       select="$new-property-names"/>
                        <xsl:with-param name="complete-property-list"   select="normalize-space($new-property-list)"/>
                        <xsl:with-param name="current-style-name"       select="$current-style-name"/>
                        <xsl:with-param name="parent-style-name"        select="$parent-style-name"/>
                        <xsl:with-param name="style-family"             select="$style-family"/>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:element>
    </xsl:template>



    <xsl:template name="add-parent-style-attributes">
        <xsl:param name="property-name-list"/>
        <xsl:param name="complete-property-list"/>
        <xsl:param name="current-style-name"/>
        <xsl:param name="parent-style-name"/>
        <xsl:param name="style-family"/>

        <!--*** New two be added property names will be collected (only one variable per template) ***-->
        <xsl:variable name="new-property-names">
            <xsl:call-template name="get-new-style-names">
                <xsl:with-param name="property-name-list"       select="$property-name-list"/>
                <xsl:with-param name="parent-style-name"        select="$parent-style-name"/>
                <xsl:with-param name="current-style-name"       select="$current-style-name"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:choose>
            <!--*** check if the new parent style exist in the office:automatic-styles section (defined by name and family) ***-->
            <xsl:when test="$office:automatic-styles/style:style[@style:family='paragraph' and @style:name=$current-style-name]">
                <!--*** RECURSION: adding new parent style attributes to the current style ***-->
                <xsl:variable name="new-property-attributes">
                    <xsl:call-template name="get-new-style-attributes">
                        <xsl:with-param name="new-property-names"           select="$new-property-names"/>
                        <xsl:with-param name="current-style-name"           select="$current-style-name"/>
                        <xsl:with-param name="parent-style-name"            select="$parent-style-name"/>
                    </xsl:call-template>
                </xsl:variable>
                <!--*** End CONDITION: the last style parent has already been executed ***-->
                <xsl:variable name="new-parent-style-name"  select="$office:automatic-styles/style:style[@style:family='paragraph' and @style:name=$parent-style-name]/@style:parent-style-name"/>
                <xsl:choose>
                    <xsl:when test="string-length($new-parent-style-name)=0">
                    <!--** no further parent is found, the given parameter property-node is the final style -->
                        <xsl:value-of select="concat($complete-property-list,$new-property-attributes)"/>
                    </xsl:when>
                    <xsl:otherwise>
                    <!--** further attributes of the parent style must be collected **-->
                        <xsl:call-template name="add-parent-style-attributes">
                            <xsl:with-param name="property-name-list"       select="concat($property-name-list, $new-property-names)"/>
                            <xsl:with-param name="complete-property-list"   select="concat($complete-property-list,$new-property-attributes)"/>
                            <xsl:with-param name="current-style-name"       select="$parent-style-name"/>
                            <xsl:with-param name="parent-style-name"        select="$new-parent-style-name"/>
                            <xsl:with-param name="style-family"             select="$style-family"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>

            <!--** the specific style (defined by name and family) must be found in the office:styles section -->
            <xsl:otherwise>
                <!--*** RECURSION: adding new parent style attributes to the current style ***-->
                <!--*** adding new parent style attributes to the current style ***-->
                <xsl:variable name="new-property-attributes">
                    <xsl:call-template name="get-new-style-attributes">
                        <xsl:with-param name="new-property-names"           select="$new-property-names"/>
                        <xsl:with-param name="current-style-name"           select="$current-style-name"/>
                        <xsl:with-param name="parent-style-name"            select="$parent-style-name"/>
                    </xsl:call-template>
                </xsl:variable>
                <!--*** End CONDITION: the last style parent has already been executed ***-->
                <xsl:variable name="new-parent-style-name"  select="$office:styles/style:style[@style:family='paragraph' and @style:name=$parent-style-name]/@style:parent-style-name"/>
                <xsl:choose>
                    <xsl:when test="string-length($new-parent-style-name)=0">
                    <!--** no further parent is found, the given parameter property-node is the final style -->
                        <xsl:value-of select="concat($complete-property-list,$new-property-attributes)"/>
                    </xsl:when>
                    <xsl:otherwise>
                    <!--** further attributes of the parent style must be collected **  -->
                        <xsl:call-template name="add-parent-style-attributes">
                            <xsl:with-param name="property-name-list"       select="concat($property-name-list, $new-property-names)"/>
                            <xsl:with-param name="complete-property-list"   select="concat($complete-property-list,$new-property-attributes)"/>
                            <xsl:with-param name="current-style-name"       select="$parent-style-name"/>
                            <xsl:with-param name="parent-style-name"        select="$new-parent-style-name"/>
                            <xsl:with-param name="style-family"             select="$style-family"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>



    <xsl:template name="get-new-style-names">
        <xsl:param name="property-name-list"/>
        <xsl:param name="parent-style-name"/>
        <xsl:param name="current-style-name"/>
        <!--** where to find the specific style (defined by name and family) wheter in office:automatic-styles or office:styles section -->
        <xsl:choose>
            <!--** if the specific style (defined by name and family) can be found in the office:automatic-styles section -->
            <xsl:when test="$office:automatic-styles/style:style[@style:family='paragraph' and @style:name=$parent-style-name]">
                <xsl:variable name="parent-property-node" select="$office:automatic-styles/style:style[@style:family='paragraph' and @style:name=$parent-style-name]/style:properties"/>

                <xsl:variable name="new-property-name-list">
                    <xsl:for-each select="$parent-property-node/@*[not(contains($property-name-list, name()))]">
                        <xsl:value-of select="name()"/>
                    </xsl:for-each>
                </xsl:variable>
                <xsl:value-of select="$new-property-name-list"/>
            </xsl:when>
            <!--** the specific style (defined by name and family) should be found in the office:styles section -->
            <xsl:otherwise>
                <xsl:variable name="parent-property-node" select="$office:styles/style:style[@style:family='paragraph' and @style:name=$parent-style-name]/style:properties"/>
                <xsl:variable name="new-property-name-list">
                    <xsl:for-each select="$parent-property-node/@*[not(contains($property-name-list, name()))]">
                        <xsl:value-of select="name()"/>
                    </xsl:for-each>
                </xsl:variable>
                <xsl:value-of select="$new-property-name-list"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>



    <xsl:template name="get-new-style-attributes">
        <xsl:param name="new-property-names"/>
        <xsl:param name="current-style-name"/>
        <xsl:param name="parent-style-name"/>

        <!--** where to find the specific style (defined by name and family) whether in office:automatic-styles or office:styles section -->
        <xsl:choose>
            <!--** if the specific style (defined by name and family) can be found in the office:automatic-styles section -->
            <xsl:when test="$office:automatic-styles/style:style[@style:family='paragraph' and @style:name=$parent-style-name]">
                <xsl:variable name="parent-property-node" select="$office:automatic-styles/style:style[@style:family='paragraph' and @style:name=$parent-style-name]/style:properties"/>
                <xsl:variable name="new-property-name-list">
                    <xsl:call-template name="write-style-properties">
                        <xsl:with-param name="styleAttributePath"   select="$parent-property-node/@*[contains($new-property-names, name())]"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:value-of select="normalize-space($new-property-name-list)"/>
            </xsl:when>
            <!--** otherwise the specific style (defined by name and family) should be found in the office:styles section -->
            <xsl:otherwise>
                <xsl:variable name="parent-property-node" select="$office:styles/style:style[@style:family='paragraph' and @style:name=$parent-style-name]/style:properties"/>
                <xsl:variable name="new-property-name-list">
                    <xsl:call-template name="write-style-properties">
                        <xsl:with-param name="styleAttributePath"   select="$parent-property-node/@*[contains($new-property-names, name())]"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:value-of select="normalize-space($new-property-name-list)"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


</xsl:stylesheet>
