/*
 * SPDX-FileCopyrightText: 2014-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/*global define*/
define([
	"umc/widgets/Text",
	"umc/i18n!management"
], function(Text, _) {
	return {
		name: 'help',
		headerText: _('Further Information'),
		'class': 'umcAppDialogPage umcAppDialogPage-help',
		navBootstrapClasses: 'col-xxs-12 col-xs-4',
		mainBootstrapClasses: 'col-xxs-12 col-xs-8',
		widgets: [{
			type: Text,
			name: 'text',
			content: _('<p>Detailed usage information on Univention Management Console can be found in the UCS manual. The manual as well as further important information are available via the following links:</p>')
		}, {
			type: Text,
			name: 'links',
			content: _('<ul><li><a href="https://docs.software-univention.de/" target="_blank">Online documentation</a></li><li><a href="https://www.univention.com/products/support/community-support/" target="_blank">Community and support</a></li></ul>')
		}]
	};
});
