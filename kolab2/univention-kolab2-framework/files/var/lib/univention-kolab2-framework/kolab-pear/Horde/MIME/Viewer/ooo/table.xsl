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


    <!-- table row handling -->
    <xsl:include href="table_rows.xsl"/>
    <!-- table column handling -->
    <xsl:include href="table_columns.xsl"/>
    <!-- table cell handling -->
    <xsl:include href="table_cells.xsl"/>



    <!-- ******************* -->
    <!-- *** main table  *** -->
    <!-- ******************* -->

    <xsl:template match="table:table | table:sub-table">
        <xsl:param name="collectedGlobalData"/>

        <!-- a table will only be created if the "scenario" is active -->
        <xsl:if test="string-length(table:scenario/@table:is-active) = 0">
            <!-- collecting all visible "table:table-row" elements of the table -->
            <xsl:variable name="allVisibleTableRows" select="table:table-row[not(@table:visibility = 'collapse' or @table:visibility = 'filter')]
                    |    table:table-header-rows/descendant::table:table-row[not(@table:visibility = 'collapse' or @table:visibility = 'filter')]
                    |    table:table-row-group/descendant::table:table-row[not(@table:visibility = 'collapse' or @table:visibility = 'filter')]"/>
            <xsl:choose>
                <!-- for all but WAP/WML devices a table border check is done (cp. "check-for-table-border") -->
                <xsl:when test="not($outputType = 'WML')">

                    <!-- As the alignment of a table is by 'align' attribut is deprecated and as the CSS 'float' attribute not well displayed,
                         we do a little trick by encapsulating the table with a aligned 'div' element-->
                    <xsl:variable name="table-alignment" select="$office:automatic-styles/style:style[@style:name = current()/@table:style-name]/style:properties/@table:align"/>

                    <xsl:choose>
                        <xsl:when test="string-length($table-alignment) != 0">
                            <xsl:element name="div">
                                <xsl:attribute name="align">
                                    <xsl:choose>
                                        <xsl:when test='$table-alignment="left" or $table-alignment="margins"'>
                                                <xsl:text>left</xsl:text>
                                        </xsl:when>
                                        <xsl:when test='$table-alignment="right"'>
                                            <xsl:text>right</xsl:text>
                                        </xsl:when>
                                        <xsl:when test='$table-alignment="center"'>
                                            <xsl:text>center</xsl:text>
                                        </xsl:when>
                                    </xsl:choose>
                                </xsl:attribute>
                                <xsl:element name="table">

                                    <xsl:apply-templates select="@table:style-name">
                                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                    </xsl:apply-templates>

                                    <!-- workaround, set table border attribut if any cell-border exists
                                    <xsl:call-template name="check-for-table-border">
                                        <xsl:with-param name="allVisibleTableRows" select="$allVisibleTableRows"/>
                                    </xsl:call-template> -->
                                    <xsl:call-template name="create-column-style-variable">
                                        <xsl:with-param name="allVisibleTableRows" select="$allVisibleTableRows"/>
                                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                    </xsl:call-template>
                                </xsl:element>
                            </xsl:element>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:element name="table">
                                <xsl:apply-templates select="@table:style-name">
                                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                </xsl:apply-templates>

                                <!-- workaround, set table border attribut if any cell-border exists
                                <xsl:call-template name="check-for-table-border">
                                    <xsl:with-param name="allVisibleTableRows" select="$allVisibleTableRows"/>
                                </xsl:call-template>  -->
                                <xsl:call-template name="create-column-style-variable">
                                    <xsl:with-param name="allVisibleTableRows" select="$allVisibleTableRows"/>
                                     <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                                </xsl:call-template>
                            </xsl:element>
                        </xsl:otherwise>
                    </xsl:choose>

                </xsl:when>
                <xsl:otherwise>
                <!-- for WML devices only ASCII table are written as tables are not implemented widley.
                     Beginning from 'repeat-write-row' the templates are handled by the table_wml.xsl stylesheet -->
                    <xsl:call-template name="create-column-style-variable">
                        <xsl:with-param name="collectedGlobalData"   select="$collectedGlobalData"/>
                        <xsl:with-param name="allVisibleTableRows"  select="$allVisibleTableRows"/>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:template>



    <xsl:template name="create-column-style-variable">
        <xsl:param name="collectedGlobalData"/>
        <xsl:param name="allVisibleTableRows"/>

        <!-- all columns of the table -->
        <xsl:variable name="allTableColumns" select="table:table-column |
                                                     table:table-column-group/descendant::table:table-column |
                                                     table:table-header-columns/descendant::table:table-column"/>
        <!-- allColumnStyleEntries: Containing all columns of the table, hidden and viewed.
            - if a column is hidden, it contains the hidden attribute, otherwise the style-properties will be stored
            - if a column is being repeated, each repeated column is explicitly written as entry in this variable.
              Later (during template "write-cell") the style of the column will be mixed with the cell-style by using
              the position() of the column entry and comparing it with the iterating cell number. -->
        <xsl:variable name="allColumnStyleEntries-RTF">
            <xsl:call-template name="adding-column-styles-entries">
                <xsl:with-param name="collectedGlobalData"   select="$collectedGlobalData"/>
                <xsl:with-param name="allTableColumns"      select="$allTableColumns"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:choose>
            <xsl:when test="function-available('xt:node-set')">
                <xsl:call-template name="create-table">
                    <xsl:with-param name="collectedGlobalData"       select="$collectedGlobalData"/>
                    <xsl:with-param name="allVisibleTableRows"      select="$allVisibleTableRows"/>
                    <xsl:with-param name="allColumnStyleEntries"    select="xt:node-set($allColumnStyleEntries-RTF)"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="function-available('xalan:nodeset')">
                <xsl:call-template name="create-table">
                    <xsl:with-param name="collectedGlobalData"       select="$collectedGlobalData"/>
                    <xsl:with-param name="allVisibleTableRows"      select="$allVisibleTableRows"/>
                    <xsl:with-param name="allColumnStyleEntries"    select="xalan:nodeset($allColumnStyleEntries-RTF)"/>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>

    </xsl:template>



    <xsl:template name="create-table">
        <xsl:param name="collectedGlobalData"/>
        <xsl:param name="allVisibleTableRows"/>
        <xsl:param name="allColumnStyleEntries"/>


        <!-- Some Office Calc documents simulate a background by repeating the last cell until end of space
             (The value of "table:number-columns-repeated" is enourmous). Writing out all these cells would be fatal.
             Therefore, this global variable shows us the longest row with content.

        Earlier only the viewable columns were listed, but it is easier to handle with all columns:
        <xsl:variable name="maxRowLength" select="count($allColumnStyleEntries/column-style-entry[not(@column-hidden-flag)])"/> -->
        <xsl:variable name="maxRowLength" select="count($allColumnStyleEntries/column-style-entry)"/>


        <!--isDebugMode-START-->
        <xsl:if test="$isDebugMode">
            <xsl:message>maxRowLength: <xsl:value-of select="$maxRowLength"/></xsl:message>
            <xsl:variable name="numberOfHiddenColumns" select="count($allColumnStyleEntries/column-style-entry[@column-hidden-flag])"/>
            <xsl:message>numberOfHiddenColumns: <xsl:value-of select="$numberOfHiddenColumns"/></xsl:message>
            <xsl:call-template name="table-debug-allColumnStyleEntries">
                <xsl:with-param name="allColumnStyleEntries" select="$allColumnStyleEntries"/>
            </xsl:call-template>
        </xsl:if>
        <!--isDebugMode-END-->
        <xsl:choose>
            <xsl:when test="$outputType = 'WML'">
                <!-- matching all rows - we can not use xsl:apply-template with a node-set parameter as by a bug in XT (James Clark)
                     (here: allColumnStyleEntries) will be interpreted as a result tree fragment, where no search expression (XPath) can be used
                     2DO:CHECK WITH XALAN-->
                <xsl:for-each select="$allVisibleTableRows">
                    <xsl:call-template name="wml-repeat-write-row">
                        <xsl:with-param name="collectedGlobalData"       select="$collectedGlobalData"/>
                        <xsl:with-param name="allColumnStyleEntries"    select="$allColumnStyleEntries"/>
                        <xsl:with-param name="number-rows-repeated"     select="@table:number-rows-repeated"/>
                        <xsl:with-param name="maxRowLength"             select="$maxRowLength"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <!-- matching all rows - we can not use xsl:apply-template with a node-set parameter as by a bug in XT (James Clark)
                     (here: allColumnStyleEntries) will be interpreted as a result tree fragment, where no search expression (XPath) can be used
                     2DO:CHECK WITH XALAN -->
                <xsl:for-each select="$allVisibleTableRows">
                    <xsl:call-template name="repeat-write-row">
                        <xsl:with-param name="collectedGlobalData"       select="$collectedGlobalData"/>
                        <xsl:with-param name="allColumnStyleEntries"    select="$allColumnStyleEntries"/>
                        <xsl:with-param name="number-rows-repeated"     select="@table:number-rows-repeated"/>
                        <xsl:with-param name="maxRowLength"             select="$maxRowLength"/>
                    </xsl:call-template>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>





    <!-- **************************** -->
    <!-- *** HELPER: table border *** -->
    <!-- **************************** -->

    <!-- only one table border for HTML4 or CSS devices which contain one or more 'fo:border-top' attributes (pars pro toto, if one exist the other usually exist, too) -->
    <!-- this was a work-around for the netscape 4.xx but not longer necessary for Mozilla -->
    <xsl:template name="check-for-table-border">
        <xsl:param name="allVisibleTableRows"/>

        <xsl:variable name="startTime">
            <xsl:if test="$isDebugMode and not($isJavaDisabled)">
                <xsl:choose>
                    <xsl:when test="function-available('system:current-time-millis')">
                        <xsl:value-of select="system:current-time-millis()"/>
                    </xsl:when>
                    <xsl:when test="function-available('java:java.lang.System.currentTimeMillis')">
                        <xsl:value-of select="java:java.lang.System.currentTimeMillis()"/>
                    </xsl:when>
                </xsl:choose>
            </xsl:if>
        </xsl:variable>

        <!-- checks if one cell (table:table-cell) of the rows of this table (allVisibleTableRows) contains a border style (i.e. fo:border-top)
             If only one single border element exist, the whole table will gets pre-defined borders (simple heuristic for better browser display) -->
        <xsl:if test="$allVisibleTableRows/table:table-cell[@table:style-name=/*/*/style:style[style:properties/@fo:border-top]/@style:name]">
            <xsl:attribute name="border">1</xsl:attribute>
            <xsl:attribute name="bordercolor">#000000</xsl:attribute>
            <xsl:attribute name="cellpadding">2</xsl:attribute>
            <xsl:attribute name="cellspacing">0</xsl:attribute>
            <xsl:attribute name="page-break-inside">page-break-inside:avoid</xsl:attribute>
        </xsl:if>


        <!-- check the time for borderchecking (debug)-->
        <xsl:if test="$isDebugMode and not($isJavaDisabled)">
            <xsl:variable name="endTime">
                <xsl:choose>
                    <xsl:when test="function-available('system:current-time-millis')">
                        <xsl:value-of select="system:current-time-millis()"/>
                    </xsl:when>
                    <xsl:when test="function-available('java:java.lang.System.currentTimeMillis')">
                        <xsl:value-of select="java:java.lang.System.currentTimeMillis()"/>
                    </xsl:when>
                </xsl:choose>
            </xsl:variable>
            <xsl:message>Time for checking BorderStyle: <xsl:value-of select="($endTime - $startTime)"/> ms</xsl:message>
        </xsl:if>
    </xsl:template>

</xsl:stylesheet>
