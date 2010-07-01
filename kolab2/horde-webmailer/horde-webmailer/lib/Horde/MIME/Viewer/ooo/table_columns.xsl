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


    <!-- ******************************************** -->
    <!-- *** Create table columns style variable  *** -->
    <!-- ******************************************** -->

    <xsl:template name="adding-column-styles-entries">
        <xsl:param name="collectedGlobalData"/>
        <xsl:param name="allTableColumns"/>

        <xsl:for-each select="$allTableColumns">

            <xsl:variable name="column-style-entry" select="$collectedGlobalData/allstyles/*[name() = translate(current()/@table:style-name, '. %()/\', '')]"/>
            <xsl:choose>
                <xsl:when test="not(@table:number-columns-repeated)">
                    <!-- writes an entry of a column in the columns-variable -->
                    <xsl:call-template name="adding-column-style-entry">
                        <xsl:with-param name="column-style-entry" select="$column-style-entry"/>
                    </xsl:call-template>
                </xsl:when>
                <!-- No higher repetition of cells greater than 4 for the last and second last column -->
                <!-- a hack for the sample document 'Waehrungsumrechner.sxc having 230 repeated columns in the second last column -->
                <!-- ??? <xsl:when test="(position() = last() or (position() = (last() - 1)) and @table:number-columns-repeated &lt; 5)"> ???-->
                <xsl:when test="position() = last() or position() = (last() - 1)">
                    <xsl:if test="@table:number-columns-repeated &lt; 5">
                        <!-- writes an entry of a column in the columns-variable -->
                        <xsl:call-template name="repeat-adding-column-style-entry">
                            <xsl:with-param name="column-style-entry"       select="$column-style-entry"/>
                            <xsl:with-param name="number-columns-repeated"  select="1"/>
                        </xsl:call-template>
                    </xsl:if>
                </xsl:when>
                <xsl:otherwise>
                    <!-- repeated colums will be written explicit several times in the variable-->
                    <xsl:call-template name="repeat-adding-column-style-entry">
                        <xsl:with-param name="column-style-entry"           select="$column-style-entry"/>
                        <xsl:with-param name="number-columns-repeated"      select="@table:number-columns-repeated"/>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:for-each>
     </xsl:template>


    <!-- WRITES THE REPEATED COLUMN STYLE EXPLICIT AS AN ELEMENT IN THE COLUMNS-VARIABLE -->
    <xsl:template name="repeat-adding-column-style-entry">
        <xsl:param name="column-style-entry"/>
        <xsl:param name="number-columns-repeated"/>

        <xsl:choose>
            <xsl:when test="$number-columns-repeated > 1">
                <!-- writes an entry of a column in the columns-variable -->
                <xsl:call-template name="adding-column-style-entry">
                    <xsl:with-param name="column-style-entry"   select="$column-style-entry"/>
                </xsl:call-template>
                <!-- repeat calling this method until all elements written out -->
                <xsl:call-template name="repeat-adding-column-style-entry">
                    <xsl:with-param name="column-style-entry"       select="$column-style-entry"/>
                    <xsl:with-param name="number-columns-repeated"  select="$number-columns-repeated - 1"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <!-- writes an entry of a column in the columns-variable -->
                <xsl:call-template name="adding-column-style-entry">
                    <xsl:with-param name="column-style-entry"   select="$column-style-entry"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


    <!-- THE COLUMN-STYLE WRITE-PATTERN FOR EACH COLUMN WRITTEN IN A VARIABLE -->
    <xsl:template name="adding-column-style-entry">
        <xsl:param name="column-style-entry"/>

        <xsl:element name="column-style-entry">
            <xsl:choose>
                <xsl:when test="@table:visibility = 'collapse' or @table:visibility = 'filter'">
                    <xsl:attribute name="column-hidden-flag">true</xsl:attribute>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:variable  name="table:style-name"         select="translate(@table:style-name, '. %()/\', '')"/>
                    <xsl:attribute name="style-name"><xsl:value-of select="$table:style-name"/></xsl:attribute>
                    <xsl:value-of select="$column-style-entry"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:element>
    </xsl:template>



    <!--isDebugMode-START-->
    <!-- giving out the 'allColumnStyle' variable:
        For each 'column-style-entry' of the 'allColumnStyleEntries' variable the style-name is given out.
        In case of 'column-hidden-flag' attribute the text 'Column is hidden is given out.-->
    <xsl:template name="table-debug-allColumnStyleEntries">
        <xsl:param name="allColumnStyleEntries"/>

        <!-- debug output as table summary attribut in html -->
        <xsl:attribute name="summary">
            <xsl:call-template name="table-debug-column-out">
                <xsl:with-param name="allColumnStyleEntries" select="$allColumnStyleEntries"/>
            </xsl:call-template>
        </xsl:attribute>
        <!-- debug output to console -->
        <xsl:message>
            <xsl:call-template name="table-debug-column-out">
                <xsl:with-param name="allColumnStyleEntries" select="$allColumnStyleEntries"/>
            </xsl:call-template>
        </xsl:message>
    </xsl:template>


    <xsl:template name="table-debug-column-out">
        <xsl:param name="allColumnStyleEntries"/>
            <xsl:text>
            DebugInformation: For each 'column-style-entry' of the 'allColumnStyleEntries' variable the style-name is given out.
                              In case of 'column-hidden-flag' attribute the text 'column is hidden' is given out.
            </xsl:text>
                <xsl:for-each select="$allColumnStyleEntries/column-style-entry">
                <xsl:choose>
                <xsl:when test="@column-hidden-flag">
            <xsl:text>  </xsl:text><xsl:value-of select="@style-name"/><xsl:text>column is hidden</xsl:text><xsl:text>
            </xsl:text>
                </xsl:when>
                <xsl:otherwise>
            <xsl:text>  </xsl:text><xsl:value-of select="@style-name"/><xsl:text> = </xsl:text><xsl:value-of select="."/><xsl:text>
            </xsl:text>
                </xsl:otherwise>
                </xsl:choose>
                           </xsl:for-each>
    </xsl:template>
    <!--isDebugMode-END-->

</xsl:stylesheet>
