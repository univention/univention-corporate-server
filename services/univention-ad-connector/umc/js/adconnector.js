/*
 * SPDX-FileCopyrightText: 2014-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/topic",
	"umc/app",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Module",
	"./adconnector/SetupWizard",
	"./adconnector/ConfigPage",
	"umc/i18n!umc/modules/adconnector",
], function(declare, lang, topic, app, tools, dialog, Module, SetupWizard, ConfigPage, _) {
	app.registerOnStartup(function() {
		tools.umcpCommand('adconnector/admember/check_dcmaster_srv_rec').then(function(response) {
			if (!response.result.success) {
				dialog.notify(_('<p><b>Caution!</b> The DNS service record for the UCS Primary was not found in the DNS server.</p>') + ' ' +  _('<p>Details are explained in the <a href="http://sdb.univention.de/1299">Support Database</a>.</p>'), _('DNS Check'));
			}
		});
	});

	return declare("umc.modules.adconnector", Module, {

		standbyOpacity: 1.00,

		wizard: null,

		configPage: null,

		buildRendering: function() {
			this.inherited(arguments);
			this.standbyDuring(tools.umcpCommand('adconnector/state')).then(lang.hitch(this, function(response) {
				var state = response.result;
				if (!state.configured) {
					this.wizard = new SetupWizard({});
					this.addChild(this.wizard);
					this.wizard.on('Finished', lang.hitch(this, function() {
						topic.publish('/umc/actions', 'adconnector', 'wizard', 'finish');
						topic.publish('/umc/tabs/close', this);
					}));
					this.wizard.on('Cancel', lang.hitch(this, function() {
						topic.publish('/umc/actions', 'adconnector', 'wizard', 'cancel');
						topic.publish('/umc/tabs/close', this);
					}));
				}
				else {
					this.configPage = new ConfigPage({
						initialState: state
					});
					this.addChild(this.configPage);
				}
			}));
		}
	});
});
