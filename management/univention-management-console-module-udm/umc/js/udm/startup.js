/*
 * SPDX-FileCopyrightText: 2014-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/kernel",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/query",
	"dojo/Deferred",
	"dojo/topic",
	"dijit/registry",
	"umc/menu",
	"umc/tools",
	"umc/dialog",
	"management/widgets/ActivationPage!",  // page needs to be loaded as plugin
	"management/widgets/ActivationDialog",
	"umc/i18n!umc/modules/udm"
], function(declare, kernel, lang, array, query, Deferred, topic, registry, menu, tools, dialog, ActivationPage, ActivationDialog, _) {

	var ucr = {};

	var checkLicense = function() {
		tools.umcpCommand('udm/license', {}, false).then(function(data) {
			var msg = data.result.message;
			if (msg) {
				dialog.warn(msg);
			}
		}, function() {
			console.warn('WARNING: An error occurred while verifying the license. Ignoring error.');
		});
	};

	var _showActivationDialog = function() {
		// The following check is only for if this dialogue is opened via topic.publish()
		if (ucr['uuid/license']) {
			dialog.alert(_('The license has already been activated.'));
			return;
		}

		topic.publish('/umc/actions', 'menu', 'license', 'activation');
		new ActivationDialog({});
	};

	var addActivationMenu = function() {
		if (!ActivationPage.hasLicense) {
			// license has not been activated yet
			menu.addEntry({
				priority: 30,
				label: _('Activation of UCS'),
				onClick: _showActivationDialog,
				parentMenuId: 'umcMenuLicense'
			});
		}
	};

	topic.subscribe('/umc/license/activation', _showActivationDialog);

	return function() {
		checkLicense();
		tools.ucr(['uuid/license']).then(function(_ucr) {
			lang.mixin(ucr, _ucr);
			addActivationMenu();
		});
	};
});
