/*
 * SPDX-FileCopyrightText: 2013-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"umc/modules/udm/wizards/computers/computer"
], function(declare, ComputerWizard) {
	return declare("umc.modules.udm.wizards.computers.ipmanagedclient", [ ComputerWizard ]);
});

