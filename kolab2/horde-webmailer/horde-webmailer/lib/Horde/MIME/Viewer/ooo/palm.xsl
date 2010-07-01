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

    <xsl:output cdata-section-elements="meta"/>


    <!-- **************************** -->
    <!-- *** specific palm header *** -->
    <!-- **************************** -->

    <xsl:template name='palm-header-properties'>
        <xsl:element name="meta">
            <xsl:attribute name="name">PalmComputingPlatform</xsl:attribute>
            <xsl:attribute name="content">true</xsl:attribute>
        </xsl:element>
        <xsl:element name="meta">
            <xsl:attribute name="name">HandheldFriendly</xsl:attribute>
            <xsl:attribute name="content">true</xsl:attribute>
        </xsl:element>
        <xsl:element name="meta">
            <xsl:attribute name="name">HistoryListText</xsl:attribute>
            <xsl:attribute name="content">Dateimanager&#10;: &amp;date &amp;time</xsl:attribute>
        </xsl:element>
        <xsl:element name="meta">
            <xsl:attribute name="name">description</xsl:attribute>
            <xsl:attribute name="content">StarPortal</xsl:attribute>
        </xsl:element>
        <xsl:element name="meta">
            <xsl:attribute name="name">keywords</xsl:attribute>
            <xsl:attribute name="content">starportal, staroffice, software</xsl:attribute>
        </xsl:element>
        <xsl:element name="meta">
            <xsl:attribute name="http-equiv">Content-Type</xsl:attribute>
            <xsl:attribute name="content">text/html; charset=iso-8859-1</xsl:attribute>
        </xsl:element>
    </xsl:template>


    <!-- ********************************* -->
    <!-- *** creating table attributes *** -->
    <!-- ********************************* -->

    <!-- table data (td) and table header (th) attributes -->
    <xsl:template name="create-attribute-ALIGN">
        <xsl:param name="styleProperties"/>

        <xsl:if test="contains($styleProperties, 'align')">
            <xsl:attribute name="align">
                 <xsl:choose>
                    <xsl:when test="contains($styleProperties, 'align:left')">
                        <xsl:text>left</xsl:text>
                    </xsl:when>
                    <xsl:when test="contains($styleProperties, 'align:right')">
                        <xsl:text>right</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>center</xsl:text>
                    </xsl:otherwise>
                 </xsl:choose>
            </xsl:attribute>
        </xsl:if>
    </xsl:template>


    <!-- ********************************* -->
    <!-- *** creating List attributes  *** -->
    <!-- ********************************* -->
<!--
    <xsl:template name="create-list-attributes">
        <xsl:param name="styleProperties"/>


!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
2 be implemented
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


    </xsl:template>
-->

    <!-- ************************************************ -->
    <!-- *** creating nested format tags (PALM & WML) *** -->
    <!-- ************************************************ -->

    <!-- Italic -->
    <xsl:template name="create-nested-format-tags">
        <xsl:param name="collectedGlobalData"/>
        <xsl:param name="styleProperties"/>
        <xsl:choose>
            <xsl:when test="contains($styleProperties, 'italic')">
                <xsl:element name="i">
                    <xsl:call-template name="bold">
                        <xsl:with-param name="styleProperties" select="$styleProperties"/>
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    </xsl:call-template>
                </xsl:element>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="bold">
                    <xsl:with-param name="styleProperties" select="$styleProperties"/>
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


    <!-- Bold -->
    <xsl:template name="bold">
        <xsl:param name="collectedGlobalData"/>
        <xsl:param name="styleProperties"/>

        <xsl:choose>
            <xsl:when test="contains($styleProperties, 'bold')">
                <xsl:element name="b">
                    <xsl:call-template name="underline">
                        <xsl:with-param name="styleProperties" select="$styleProperties"/>
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    </xsl:call-template>
                </xsl:element>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="underline">
                    <xsl:with-param name="styleProperties" select="$styleProperties"/>
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


    <!-- Underline : last format attribute, which is also used from WML - WML ends here! -->
    <xsl:template name="underline">
        <xsl:param name="collectedGlobalData"/>
        <xsl:param name="styleProperties"/>

        <xsl:choose>
            <xsl:when test="$outputType = 'PALM'">
                <xsl:choose>
                    <xsl:when test="contains($styleProperties, 'underline')">
                        <xsl:element name="u">
                            <xsl:call-template name="strikethrough">
                                <xsl:with-param name="styleProperties" select="$styleProperties"/>
                                <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                            </xsl:call-template>
                        </xsl:element>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="strikethrough">
                            <xsl:with-param name="styleProperties" select="$styleProperties"/>
                            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="contains($styleProperties, 'underline')">
                        <xsl:element name="u">
                            <xsl:apply-templates>
                                <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                            </xsl:apply-templates>
                        </xsl:element>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:apply-templates>
                            <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                        </xsl:apply-templates>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


    <!-- strikethrough -->
    <xsl:template name="strikethrough">
        <xsl:param name="collectedGlobalData"/>
        <xsl:param name="styleProperties"/>

        <xsl:choose>
            <xsl:when test="contains($styleProperties, 'strike')">
                <xsl:element name="strike">
                    <xsl:call-template name="align">
                        <xsl:with-param name="styleProperties" select="$styleProperties"/>
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    </xsl:call-template>
                </xsl:element>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="align">
                    <xsl:with-param name="styleProperties" select="$styleProperties"/>
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


    <!-- Alignment -->
    <xsl:template name="align">
        <xsl:param name="collectedGlobalData"/>
        <xsl:param name="styleProperties"/>

        <xsl:choose>
            <xsl:when test="contains($styleProperties, 'align')">
                <xsl:element name="div">
                    <xsl:attribute name="align">
                         <xsl:choose>
                            <xsl:when test="contains($styleProperties, 'align:left')">
                                <xsl:text>left</xsl:text>
                            </xsl:when>
                            <xsl:when test="contains($styleProperties, 'align:right')">
                                <xsl:text>right</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>center</xsl:text>
                            </xsl:otherwise>
                         </xsl:choose>
                    </xsl:attribute>
                    <xsl:call-template name="font_combined">
                        <xsl:with-param name="styleProperties" select="$styleProperties"/>
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    </xsl:call-template>
                </xsl:element>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="font_combined">
                    <xsl:with-param name="styleProperties" select="$styleProperties"/>
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


    <!-- Both size and Color for font -->
    <xsl:template name="font_combined">
        <xsl:param name="collectedGlobalData"/>
        <xsl:param name="styleProperties"/>

        <xsl:choose>
            <xsl:when test="contains($styleProperties, 'color') and contains($styleProperties, 'size')">
                <xsl:element name="font">

                    <xsl:attribute name="color">
                         <xsl:choose>
                            <xsl:when test="contains($styleProperties, 'color:#000000')">
                                <xsl:text>#000000</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>#FFFFFF</xsl:text>
                            </xsl:otherwise>
                         </xsl:choose>
                    </xsl:attribute>

                    <xsl:attribute name="size">
                        <xsl:value-of select="substring-after(substring-before($styleProperties ,':size'), 'size:')"/>
                    </xsl:attribute>

                    <!-- get the embedded content -->
                    <xsl:apply-templates>
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    </xsl:apply-templates>
                </xsl:element>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="font_simple">
                    <xsl:with-param name="styleProperties" select="$styleProperties"/>
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


    <!-- size or Color for font -->
    <xsl:template name="font_simple">
        <xsl:param name="collectedGlobalData"/>
        <xsl:param name="styleProperties"/>

        <xsl:choose>
            <xsl:when test="contains($styleProperties, 'color')">
                <xsl:element name="font">
                    <xsl:attribute name="color">
                         <xsl:choose>
                            <xsl:when test="contains($styleProperties, 'color:#000000')">
                                <xsl:text>#000000</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>#FFFFFF</xsl:text>
                            </xsl:otherwise>
                         </xsl:choose>
                    </xsl:attribute>

                    <!-- get the embedded content -->
                    <xsl:apply-templates>
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    </xsl:apply-templates>
                </xsl:element>
            </xsl:when>

            <xsl:when test="contains($styleProperties, 'size')">
                <xsl:element name="font">
                    <xsl:attribute name="size">
                        <xsl:value-of select="substring-after(substring-before($styleProperties ,':size'), 'size:')"/>
                    </xsl:attribute>

                    <!-- get the embedded content -->
                    <xsl:apply-templates>
                        <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                    </xsl:apply-templates>
                </xsl:element>
            </xsl:when>

            <xsl:otherwise>
                <!-- get the embedded content -->
                <xsl:apply-templates>
                    <xsl:with-param name="collectedGlobalData" select="$collectedGlobalData"/>
                </xsl:apply-templates>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


</xsl:stylesheet>
