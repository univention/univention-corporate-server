/*
 * SPDX-FileCopyrightText: 2014-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/*global define*/
define([
	"dojo/_base/lang",
	"umc/tools",
	"umc/widgets/Text",
	"umc/widgets/CheckBox",
	"umc/i18n!management"
], function(lang, tools, Text, CheckBox, _) {
	return {
		name: 'feedback',
		headerText: _('Feedback via usage statistics'),
		'class': 'umcAppDialogPage umcAppDialogPage-feedback',
		navBootstrapClasses: 'col-xxs-12 col-xs-4',
		mainBootstrapClasses: 'col-xxs-12 col-xs-8',
		widgets: [{
			type: Text,
			name: 'text',
			content: _('<p>On UCS evaluation systems, anonymous usage statistics are created by default and sent to Univention. This allows to continuously adapt UCS to suit the practical needs of its users.</p><p>The information consists of UMC usage statistics and a one-time statistic on the hardware configuration. Details about the usage statistics and about its deactivation can be found in the <a href="https://docs.software-univention.de/manual-%(version)s.html#central-management-umc:piwik" target="_blank">UCS manual</a>.</p><p>Usage statistics are automatically deactivated when importing a commercial license.</p>', {
				version: tools.status('ucsVersion').split('-')[0]
			})
		}, {
			type: CheckBox,
			visible: false,
			name: 'enableHardwareStatistics',
			label: _('Enable one-time statistic on hardware configuration.'),
			value: true
		}]
	};
});
