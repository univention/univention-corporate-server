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


    <!-- *********************************** -->
    <!-- *** write repeating table cells *** -->
    <!-- *********************************** -->


    <!-- matching cells to give out -> covered table cells are not written out -->
    <xsl:template match="table:table-cell">
        <xsl:param name="collectedGlobalData"/>
        <!-- position of the current input cell to get the correct colum style (hidden are also counted)-->
        <xsl:param name="allColumnStyleEntries"/>
        <xsl:param name="maxRowLength"/>

        <xsl:if test="$isDebugMode">
            <xsl:message>
--------------> table:table-cell has been entered with node value: <xsl:value-of select="."/></xsl:message>
            <xsl:message>table:number-columns-repeated: -<xsl:value-of select="@table:number-columns-repeated"/>-</xsl:message>
        </xsl:if>

        <xsl:call-template name="create-column-position-variable">
            <!-- position of the current input cell to get the correct colum style (hidden are also counted)-->
            <xsl:with-param name="allColumnStyleEntries"    select="$allColumnStyleEntries"/>
            <xsl:with-param name="collectedGlobalData"       select="$collectedGlobalData"/>
            <xsl:with-param name="maxRowLength"             select="$maxRowLength"/>
        </xsl:call-template>

    </xsl:template>



    <xsl:template name="create-column-position-variable">
        <!-- position of the current input cell to get the correct colum style (hidden are also counted)-->
        <xsl:param name="allColumnStyleEntries"/>
        <xsl:param name="collectedGlobalData"/>
        <xsl:param name="maxRowLength"/>

        <!-- column position needed for styles, esp. for column-hidden-flag -->
        <xsl:variable name="preceding-columns">
            <xsl:for-each select="preceding-sibling::*">
                <xsl:element name="quantity">
                    <xsl:choose>
                        <xsl:when test="string-length(@table:number-columns-repeated) = 0">1</xsl:when>
                        <xsl:otherwise><xsl:value-of select="@table:number-columns-repeated"/></xsl:otherwise>
                    </xsl:choose>
                </xsl:element>
            </xsl:for-each>
        </xsl:variable>

        <xsl:choose>
            <xsl:when test="function-available('xt:node-set')">
                <xsl:call-template name="create-table-cell">
                    <!-- position of the current input cell to get the correct colum style (hidden are also counted)-->
                    <xsl:with-param name="allColumnStyleEntries"    select="$allColumnStyleEntries"/>
                    <xsl:with-param name="maxRowLength"             select="$maxRowLength"/>
                    <xsl:with-param name="column-position"          select="sum(xt:node-set($preceding-columns)/quantity) + 1"/>
                    <xsl:with-param name="collectedGlobalData"      select="$collectedGlobalData"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="function-available('xalan:nodeset')">
                <xsl:call-template name="create-table-cell">
                    <!-- position of the current input cell to get the correct colum style (hidden are also counted)-->
                    <xsl:with-param name="allColumnStyleEntries"    select="$allColumnStyleEntries"/>
                    <xsl:with-param name="maxRowLength"             select="$maxRowLength"/>
                    <xsl:with-param name="column-position"          select="sum(xalan:nodeset($preceding-columns)/quantity) + 1"/>
                    <xsl:with-param name="collectedGlobalData"      select="$collectedGlobalData"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:element name="NodeSetFunctionNotAvailable"/>
                <xsl:call-template name="create-table-cell"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>



    <xsl:template name="create-table-cell">
        <!-- position of the current input cell to get the correct colum style (hidden are also counted)-->
        <xsl:param name="allColumnStyleEntries"/>
        <xsl:param name="collectedGlobalData"/>
        <xsl:param name="maxRowLength"/>
        <xsl:param name="column-position"/>


        <xsl:if test="$isDebugMode">
            <xsl:message>NEW VALUE: column-position: -<xsl:value-of select="$column-position"/>-</xsl:message>
        </xsl:if>


        <!-- a hidden column will give out nothing -->
        <xsl:if test="not($allColumnStyleEntries/column-style-entry[position() = $column-position]/@column-hidden-flag)">
            <xsl:choose>
                <!-- when the columns are not repeated the next column-positions raises up to 1, otherwise up to the amount of repeated columns -->
                <xsl:when test="@table:number-columns-repeated">
                    <!-- writes multiple entries of a cell -->
                    <xsl:call-template name="repeat-write-cell">
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                        <xsl:with-param name="allColumnStyleEntries"    select="$allColumnStyleEntries"/>
                        <xsl:with-param name="column-position"          select="$column-position"/>
                        <xsl:with-param name="maxRowLength"             select="$maxRowLength"/>
                        <xsl:with-param name="number-columns-repeated"  select="@table:number-columns-repeated"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <!-- writes an entry of a cell -->
                    <xsl:call-template name="write-cell">
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                        <xsl:with-param name="allColumnStyleEntries"    select="$allColumnStyleEntries"/>
                        <xsl:with-param name="column-position"          select="$column-position"/>
                        <xsl:with-param name="maxRowLength"             select="$maxRowLength"/>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>

    </xsl:template>



    <xsl:template name="repeat-write-cell">
        <xsl:param name="collectedGlobalData"/>
        <xsl:param name="allColumnStyleEntries"/>
        <xsl:param name="column-position"/>
        <xsl:param name="maxRowLength"/>
        <xsl:param name="number-columns-repeated"/>

        <xsl:choose>
            <!-- 2DO: This is the current workaround against the background simulation by an 'endless' repeating cell -->
            <xsl:when test="$number-columns-repeated > 1 and $maxRowLength > $column-position">

                <xsl:if test="$isDebugMode">
                    <xsl:message>+++++++++ starting cell writing +++++++++</xsl:message>
                    <xsl:message>number-columns-repeated: -<xsl:value-of select="$number-columns-repeated"/>-</xsl:message>
                    <xsl:message>maxRowLength: -<xsl:value-of select="$maxRowLength"/>-</xsl:message>
                    <xsl:message>column-position: -<xsl:value-of select="$column-position"/>-</xsl:message>
                </xsl:if>

                <!-- writes an entry of a cell -->
                <xsl:call-template name="write-cell">
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    <xsl:with-param name="allColumnStyleEntries"    select="$allColumnStyleEntries"/>
                    <xsl:with-param name="column-position"          select="$column-position"/>
                    <xsl:with-param name="maxRowLength"             select="$maxRowLength"/>
                </xsl:call-template>
                <!-- repeat calling this method until all elements written out -->
                <xsl:if test="$isDebugMode">
                    <xsl:message>+++++++++ cell repetition +++++++++</xsl:message>
                </xsl:if>
                <xsl:call-template name="repeat-write-cell">
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    <xsl:with-param name="allColumnStyleEntries"    select="$allColumnStyleEntries"/>
                    <xsl:with-param name="column-position"          select="$column-position + 1"/>
                    <xsl:with-param name="maxRowLength"             select="$maxRowLength"/>
                    <xsl:with-param name="number-columns-repeated"  select="$number-columns-repeated - 1"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <!-- 2DO: This is the current workaround against the background simulation by an 'endless' repeating cell -->
                <!--      When the maxRowLength is reached a last entry of a cell is written -->
                <xsl:call-template name="write-cell">
                    <xsl:with-param name="collectedGlobalData"       select="$collectedGlobalData"/>
                    <xsl:with-param name="allColumnStyleEntries"    select="$allColumnStyleEntries"/>
                    <xsl:with-param name="column-position"          select="$column-position"/>
                    <xsl:with-param name="maxRowLength"             select="$maxRowLength"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>



    <xsl:template name="write-cell">
        <xsl:param name="collectedGlobalData"/>
        <xsl:param name="allColumnStyleEntries"/>
        <xsl:param name="column-position"/>
        <xsl:param name="maxRowLength"/>


        <xsl:if test="$isDebugMode">
            <xsl:message>WriteTest -> If nothing between '-' write cell -<xsl:value-of select="$allColumnStyleEntries/column-style-entry[position() = $column-position]/@column-hidden-flag"/>-</xsl:message>
        </xsl:if>

            <xsl:if test="$allColumnStyleEntries/column-style-entry[position() = $column-position]/@column-hidden-flag">
                <xsl:if test="$isDebugMode">
                    <xsl:message>TABLE COLUMN is hidden!</xsl:message>
                </xsl:if>
            </xsl:if>

        <xsl:choose>
            <!-- a hidden column will give out nothing -->
            <xsl:when test="$allColumnStyleEntries/column-style-entry[position() = $column-position]/@column-hidden-flag">
                <xsl:if test="$isDebugMode">
                    <xsl:message>TABLE COLUMN is hidden!</xsl:message>
                </xsl:if>
            </xsl:when>

            <!-- NOT a hidden column -->
            <xsl:otherwise>

                <!-- a table is a table header, when it has a "table:table-header-rows" ancestor -->
                <xsl:variable name="tableDataType">
                    <xsl:choose>
                        <xsl:when test="ancestor::table:table-header-rows">
                            <xsl:text>th</xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>td</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>

                <xsl:choose>
                    <!--+++++ CSS (CASCADING STLYE SHEET) HEADER STYLE WAY +++++-->
                    <xsl:when test="$outputType = 'CSS_HEADER'">
                        <xsl:element name="{$tableDataType}">

                            <xsl:if test="$isDebugMode">
                                <xsl:message>
*****************************************'<xsl:value-of select="$tableDataType"/>' element has been added!</xsl:message>
                            </xsl:if>

                            <xsl:if test="@table:number-columns-spanned">
                                <xsl:attribute name="colspan">
                                    <xsl:value-of select="@table:number-columns-spanned"/>
                                </xsl:attribute>
                            </xsl:if>
                            <xsl:if test="@table:number-rows-spanned">
                                <xsl:attribute name="rowspan">
                                    <xsl:value-of select="@table:number-rows-spanned"/>
                                </xsl:attribute>
                            </xsl:if>



                            <!-- *** the cell-style *** -->
                            <!-- The cell style has no conclusion with the column style, so we switch the order/priorities due to browser issues

                                The cell-style depends on two attributes:

                                1) table:style-name - the style properties of cell. When they exist, a default alignement (cp. below) will be added for the
                                                      case of no alignment in the style exist.

                                2) table:value-type - the value type of the table-cell giving the default alignments.
                                                      By default a string value is left aligned, all other are aligned:right.
                            -->
                            <xsl:choose>
                                <xsl:when test="@table:style-name">
                                    <xsl:attribute name="style">

                                        <!-- CELL-STYLE: alignment by table:value-type (without existing table:style-name)-->
                                        <xsl:variable name="cellStyle" select="$collectedGlobalData/allstyles/*[name()=current()/@table:style-name]"/>
                                        <xsl:choose>
                                            <xsl:when test="string-length($cellStyle) > 0 and not(contains($cellStyle, 'text-align'))">
                                                <!-- CELL-STYLE: alignment by table:value-type -->
                                                <!-- no alignment in the cell style, the alignment based on the table:value-type will be added -->
                                                <xsl:choose>
                                                    <xsl:when test="@table:value-type and not(@table:value-type = 'string')">
                                                        <xsl:value-of select="concat($collectedGlobalData/allstyles/*[name()=current()/@table:style-name], 'text-align:right; ')"/>
                                                    </xsl:when>
                                                    <xsl:otherwise>
                                                        <xsl:value-of select="concat($collectedGlobalData/allstyles/*[name()=current()/@table:style-name], 'text-align:left; ')"/>
                                                    </xsl:otherwise>
                                                </xsl:choose>
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <!-- CELL-STYLE: alignment by table:value-type -->
                                                <!-- no CSS style properties exist, only alignment from the table:value-type will be used -->
                                                <xsl:choose>
                                                    <xsl:when test="@table:value-type and not(@table:value-type = 'string')">text-align:right; </xsl:when>
                                                    <xsl:otherwise>text-align:left; </xsl:otherwise>
                                                </xsl:choose>
                                            </xsl:otherwise>
                                        </xsl:choose>

                                         <!-- column-style (disjunct of cell style -->
                                         <!-- 2DO: only absolut styles are supported, relative styles (i.e. 'style:rel-column-width' e.g. with value "8933*" are ignored.
                                              Issue: browsers (not sure if CSS) does not support the '*' relationship, only the '%', where the sum is always '100'!
                                              For this, it is easier to work on with the absolute values, instead of calculating the values for 100% -->
                                         <xsl:value-of select="$allColumnStyleEntries/column-style-entry[position()=$column-position]"/>
                                    </xsl:attribute>
                                    <!-- CELL-STYLE: table:style-name -->
                                    <xsl:attribute name="class">
                                        <xsl:value-of select="translate(@table:style-name, '. %()/\', '')"/>
                                    </xsl:attribute>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:attribute name="style">
                                        <!-- CELL-STYLE: alignment by table:value-type (without existing table:style-name)-->
                                        <!-- no table:style-name exist, only alignment from the table:value-type will be used -->
                                        <xsl:choose>
                                            <xsl:when test="@table:value-type and not(@table:value-type = 'string')">
                                                text-align:right;
                                            </xsl:when>
                                            <xsl:otherwise>
                                                text-align:left;
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    </xsl:attribute>
                                </xsl:otherwise>
                            </xsl:choose>

                            <xsl:choose>
                                <!-- In case of no cell content a non-breakable space will be inserted
                                     to make the browser show the table-cell grid -->
                                <xsl:when test="not(child::text()) and not(child::*)">
                                    <xsl:text> &#160;</xsl:text>
                                </xsl:when>
                                <xsl:otherwise>
                                    <!-- *** the column-style *** -->
                                    <!--  the column style has no conclusion with the cell style, so we switch the order/priorities due to browser issues-->
                                    <xsl:element name="span">
                                        <xsl:attribute name="class">
                                            <xsl:value-of select="$allColumnStyleEntries/column-style-entry[position() = $column-position]/@style-name"/>
                                        </xsl:attribute>
                                        <xsl:apply-templates>
                                            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                        </xsl:apply-templates>
                                    </xsl:element>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:element>
                    </xsl:when>

                    <!--+++++ HTML 4.0 INLINED WAY  +++++-->
                    <xsl:when test="$outputType = 'CSS_INLINED'">
                        <xsl:element name="{$tableDataType}">

                            <xsl:if test="@table:number-columns-spanned">
                                <xsl:attribute name="colspan">
                                    <xsl:value-of select="@table:number-columns-spanned"/>
                                </xsl:attribute>
                            </xsl:if>
                            <xsl:if test="@table:number-rows-spanned">
                                <xsl:attribute name="rowspan">
                                    <xsl:value-of select="@table:number-rows-spanned"/>
                                </xsl:attribute>
                            </xsl:if>

                            <xsl:attribute name="style">
                                <!-- cell-style -->
                                <xsl:value-of select="$collectedGlobalData/allstyles/*[name()=current()/@table:style-name]"/>
                                <!-- column-style -->
                                <xsl:value-of select="$allColumnStyleEntries/column-style-entry[position()=$column-position]"/>
                                <!-- TABLE:VALUE-TYPE - the value of a table-cell will be aligned left by default only exlicit non-string is aligned:right-->
                                <xsl:choose>
                                    <xsl:when test="@table:value-type and not(@table:value-type = 'string')">
                                        <xsl:text>text-align:right;</xsl:text>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:text>text-align:left;</xsl:text>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:attribute>

                            <!-- &#160 is a non-breakable space, necessary to make to the browser show the table-cell grid -->
                            <xsl:if test="not(child::text()) and not(child::*)"> &#160;</xsl:if>
                            <xsl:apply-templates>
                                <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                            </xsl:apply-templates>
                        </xsl:element>
                    </xsl:when>
                    <!--+++++ PALM INLINED WAY  +++++-->
                    <xsl:when test="$outputType = 'PALM'">
                        <xsl:element name="{$tableDataType}">
                            <xsl:if test="@table:number-columns-spanned">
                                <xsl:attribute name="colspan">
                                    <xsl:value-of select="@table:number-columns-spanned"/>
                                </xsl:attribute>
                            </xsl:if>

                            <xsl:if test="@table:number-rows-spanned">
                                <xsl:attribute name="rowspan">
                                    <xsl:value-of select="@table:number-rows-spanned"/>
                                </xsl:attribute>
                            </xsl:if>
                            <xsl:apply-templates>
                                <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                            </xsl:apply-templates>
                        </xsl:element>
                    </xsl:when>
                    <!--+++++ WML WAY  +++++-->
                    <xsl:when test="$outputType = 'WML'">
                        <xsl:choose>
                            <xsl:when test="not($allColumnStyleEntries/column-style-entry[last() = $column-position])">
                                <xsl:apply-templates>
                                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                </xsl:apply-templates>
                                <xsl:text>, </xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:apply-templates>
                                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                </xsl:apply-templates>
                                <xsl:text>; </xsl:text>
                                <xsl:element name="br"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
</xsl:stylesheet>
