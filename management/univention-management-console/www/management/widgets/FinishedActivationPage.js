/*
 * SPDX-FileCopyrightText: 2014-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/*global define*/
define([
	"umc/widgets/Text",
	"umc/i18n!management"
], function(Text, _) {
	return {
		name: 'finished',
		'class': 'umcAppDialogPage umcAppDialogPage-finished',
		navBootstrapClasses: 'col-xxs-12 col-xs-4',
		mainBootstrapClasses: 'col-xxs-12 col-xs-8',
		headerText: '',
		widgets: [{
			type: Text,
			name: 'text',
			content: _('<p>The license has been updated successfully.</p><p>You can now continue to use UMC, all applications in the Univention App Center are now available for installation on this system.</p>')
		}]
	};
});
