<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="xml" encoding="UTF-8" indent="yes" omit-xml-declaration="yes"/>
	<xsl:param name="src_bridge" select="'eth0'"/>
	<xsl:param name="dst_bridge" select="'br0'"/>

	<xsl:template match="node()" priority="-1" name="copy">
		<xsl:copy>
			<xsl:copy-of select="@*"/>
			<xsl:apply-templates select="node()|text()|comment()|processing-instruction()"/>
		</xsl:copy>
	</xsl:template>

	<!-- Convert network interface name -->
	<xsl:template match="/domain/devices/interface[@type='bridge']/source">
		<xsl:choose>
			<xsl:when test="@bridge=$src_bridge">
				<source bridge="{$dst_bridge}"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:call-template name="copy"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
</xsl:stylesheet>
<!-- vim:set ts=2 sw=2 noet foldmethod=marker: -->
