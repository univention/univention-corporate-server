<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="xml" encoding="UTF-8" indent="yes" omit-xml-declaration="yes"/>
	<xsl:template match="node()" priority="-1">
		<xsl:copy>
			<xsl:copy-of select="@*"/>
			<xsl:apply-templates select="node()|text()|comment()|processing-instruction()"/>
		</xsl:copy>
	</xsl:template>

	<!-- Convert Xen into QEMU/kvm domain -->
	<xsl:template match="/domain">
		<domain type="kvm">
			<xsl:apply-templates select="*"/>
			<!-- Make sure ACPI is enabled -->
			<xsl:if test="not(features)">
				<features>
					<acpi/>
					<apic/>
				</features>
			</xsl:if>
		</domain>
	</xsl:template>

	<!-- Make sure domain is HVM -->
	<xsl:template match="/domain/os/type">
		<type>hvm</type>
	</xsl:template>

	<!-- Remove boot loader from Xen-PV domains -->
	<xsl:template match="/domain/bootloader"/>
	<xsl:template match="/domain/bootloader_args"/>

	<!-- Remove BIOS loader from Xen-HV domain -->
	<xsl:template match="/domain/os/loader"/>

	<!-- Change emulator to QEMU -->
	<xsl:template match="/domain/devices/emulator">
		<emulator>/usr/bin/kvm</emulator>
	</xsl:template>

	<!-- Convert Xen block-tap2 devices -->
	<xsl:template match="/domain/devices/disk/driver[@name='tap2']">
		<driver name="qemu" type="raw" cache="none">
			<xsl:copy-of select="@*[name()!='type' and name()!='name']"/>
		</driver>
	</xsl:template>
	<xsl:template match="/domain/devices/disk/target[@bus='xen']">
		<target bus="virtio" dev="vd{substring-after(@dev,'xvd')}">
			<xsl:copy-of select="@*[name()!='bus' and name()!='dev']"/>
		</target>
	</xsl:template>

	<!-- Convert Xen netfront devices -->
	<xsl:template match="/domain/devices/interface/model[@type='netfront']">
		<model type="virtio"/>
	</xsl:template>
	<xsl:template match="/domain/devices/interface/script"/>

	<!-- Convert Xen console -->
	<xsl:template match="/domain/devices/console/target[@type='xen']">
		<target type="serial">
			<xsl:copy-of select="@*[name()!='type']"/>
		</target>
	</xsl:template>

	<!-- Convert Xen specific input devices -->
	<xsl:template match="/domain/devices/input[@bus='xen']">
		<input bus="usb">
			<xsl:copy-of select="@*[name()!='bus']"/>
			<xsl:apply-templates select="*"/>
		</input>
	</xsl:template>
</xsl:stylesheet>
<!-- vim:set ts=2 sw=2 noet foldmethod=marker: -->
