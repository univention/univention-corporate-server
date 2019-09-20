/*
 * Copyright 2014-2019 Univention GmbH
 *
 * https://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <https://www.gnu.org/licenses/>.
 */
/*global define,require,setTimeout*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/topic",
	"dojo/Deferred",
	"dojo/when",
	"dojox/html/styles",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/ProgressBar",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/widgets/PasswordBox",
	"umc/widgets/Module",
	"umc/widgets/Wizard",
	"umc/i18n!umc/modules/adtakeover"
], function(declare, lang, array, topic, Deferred, when, styles, tools, dialog, ProgressBar, Text, TextBox, PasswordBox, Module, Wizard, _) {
	// prepare CSS rules for module
	styles.insertCssRule('.umc-adtakeover-page .umcPageHeader', 'background-repeat: no-repeat; background-position: 10px 20px; padding-bottom: 160px; min-height: 160px;');
	array.forEach(['restart', 'start', 'copy', 'sysvol', 'takeover', 'finished'], function(ipage) {
		var imageUrl = require.toUrl(lang.replace('umc/modules/adtakeover/{0}.png', [ipage]));
		styles.insertCssRule(
			lang.replace('.umc-adtakeover-page-{0} .umcPageHeader', [ipage]),
			lang.replace('background-image: url({0})', [imageUrl])
		);
	});

	var TakeoverWizard = declare("umc.modules.adtakeover.Wizard", [ Wizard ], {
		autoValidate: true,
		autoFocus: true,

		constructor: function() {
			this.pages = [{
				'class': 'umc-adtakeover-page-restart umc-adtakeover-page',
				name: 'restart',
				headerText: _('Previous takeover detected'),
				widgets: [{
					type: Text,
					name: 'text',
					content: _('<p>A previous Active Directory takeover was detected.</p><p>In order to start another takeover process, click "Next".</p>')
				}]
			}, {
				'class': 'umc-adtakeover-page-start umc-adtakeover-page',
				name: 'start',
				headerText: _('Windows domain authentication'),
				helpText: _('This module guides through the migration from a Windows Active Directory domain to Univention Corporate Server. All user, group and computer accounts along with their passwords and group policies are transferred. After the migration, the Windows clients are directly operable without the need of a domain rejoin.'),
				widgets: [{
					type: TextBox,
					name: 'ip',
					required: true,
					label: _('Name or address of the Domain Controller')
				}, {
					type: TextBox,
					name: 'username',
					required: true,
					label: _('Active Directory Administrator account'),
					value: 'Administrator'
				}, {
					type: PasswordBox,
					name: 'password',
					required: true,
					label: _('Active Directory Administrator password')
				}]
			}, {
				'class': 'umc-adtakeover-page-copy umc-adtakeover-page',
				name: 'copy',
				headerText: _('Import statistics'),
				widgets: [{
					type: Text,
					name: 'text',
					content: 'TBA',
					textTemplate: _('<p>A <i>{ad_os}</i> Active Directory domain with the domainname <i>{ad_domain}</i> has been found. The server <i>{ad_hostname} ({ad_ip})</i> will be used as Active Directory Domain Controller for the takeover.</p><p>The following accounts have been found in the Active Directory domain:<ul><li>{users} users</li><li>{groups} groups</li><li>{computers} computers</li></ul>Click "Next" to start with the migration.</p>') +
						'<p><strong>{license_error}</strong></p>'
				}]
			}, {
				'class': 'umc-adtakeover-page-sysvol umc-adtakeover-page',
				name: 'sysvol',
				headerText: _('Transfer of group policies'),
				widgets: [{
					type: Text,
					name: 'text',
					content: 'TBA',
					textTemplate: _('<p>All Windows domain accounts have been successfully transferred.</p><p>As next step, group policies must be copied from the Active Directory SYSVOL share to Univention Corporate Server. We recommend using robocopy from a Windows client or Windows server which is joined to the domain:</p>') + '<pre>robocopy /mir /sec /z \\\\{ad_hostname}\\sysvol \\\\{ucs_hostname}\\sysvol</pre>'
				}]
			}, {
				'class': 'umc-adtakeover-page-takeover umc-adtakeover-page',
				name: 'takeover',
				headerText: _('Takeover of the Windows domain'),
				widgets: [{
					type: Text,
					name: 'text',
					content: _('<p>The group policies have been transferred successfully.</p><p>In order to complete the takeover process, all previous Active Directory Domain Controllers need to be switched off now. Click "Next" as soon as all Domain Controllers are shutdown completely.</p>')
				}]
			}, {
				'class': 'umc-adtakeover-page-finished umc-adtakeover-page',
				name: 'finished',
				headerText: _('Completion of the Active Directory Takeover'),
				widgets: [{
					type: Text,
					name: 'text',
					content: _('<p>Congratulations, the Active Directory Takeover wizard has been successfully completed and all Windows domain accounts have been transferred to Univention Corporate Server.</p><p>The domain is now ready for usage without any further changes.</p>')
				}]
			}];
		},

		startup: function() {
			this.inherited(arguments);
			var gettingFirstPage = tools.umcpCommand('adtakeover/check/status').then(lang.hitch(this, function(data) {
				var pageName = data.result;
				this._updateButtons(pageName);
				var page = this.getPage(pageName);
				var deferred = null;
				if (pageName == 'sysvol') {
					deferred = this.setSysvolInfo();
				}
				when(deferred, lang.hitch(this, function() {
					this.selectChild(page);
				}));
			}));
			this.standbyDuring(gettingFirstPage);
		},

		setSysvolInfo: function() {
			var deferred = tools.umcpCommand('adtakeover/sysvol_info').then(lang.hitch(this, function(data) {
				this.setText('sysvol', data.result);
			}));
			this.standbyDuring(deferred);
			return deferred;
		},

		setText: function(pageName, values) {
			var widget = this.getWidget(pageName, 'text');
			if (widget) {
				widget.set('content', lang.replace(widget.textTemplate, values));
			}
		},

		run: function(name, values, nextPageName) {
			var deferred = new Deferred();
			this.progressBar.reset();
			this.progressBar._progressBar.set('value', Infinity);
			var running = new Deferred();
			tools.umcpCommand(name, values, false).then(lang.hitch(this, function(data) {
				if (data.result) {
					this.setText(nextPageName, data.result);
				}
				running.resolve(true); // everything went fine
			}), function(data) {
				var error = tools.parseError(data);
				var statusMessage = tools._statusMessages[error.status];
				if (!statusMessage || error.status == 500) {
					// maybe a timeout (!statusMessage) in which case everything is fine
					// or a TakeoverError in which case the progressBar handles it
					running.resolve(false);
				} else {
					// uh, uh. real problem
					running.reject();
					deferred.reject();
					tools.handleErrorStatus(data);
				}
			});
			this.progressBar.auto('adtakeover/progress', {},
				lang.hitch(this, function() {
					running.then(lang.hitch(this, function() {
						var cb = lang.hitch(this, function() {
							var errorInfo = this.progressBar.getErrors();
							if (errorInfo.critical) {
								deferred.reject();
							} else {
								var preparePageDeferred = null;
								if (nextPageName == 'sysvol') {
									preparePageDeferred = this.setSysvolInfo();
								}
								when(preparePageDeferred, function() {
									deferred.resolve(nextPageName);
								});
							}
						});
						this.progressBar.stop(cb, undefined, true);
					}));
				}),
				undefined,
				undefined,
				true
			);
			this.standbyDuring(deferred, this.progressBar);
			return deferred;
		},

		next: function(pageName) {
			var nextPage = this.inherited(arguments);
			if (!pageName) {
				return nextPage;
			}
			this.progressBar.reset();
			this.progressBar._progressBar.set('value', Infinity);
			var fakeProgress = {
			};
			var fake = fakeProgress[pageName];
			if (fake) {
				var deferred = new Deferred();
				this.progressBar.feedFromDeferred(deferred);
				this.updateProgress(fake, deferred, nextPage);
				this.standbyDuring(deferred, this.progressBar);
				deferred.then(undefined, lang.hitch(this, function() {
					var errors = this.progressBar.getErrors().errors;
					var msg = 'Error during "' + this.progressBar._component.get('content') + '"!';
					if (errors.length == 1) {
						msg += '<p>' + errors[0] + '</p>';
					} else {
						msg += '<ul><li>' + errors.join('</li><li>') + '</li></ul>';
					}
					dialog.alert(msg);
				}));
				return deferred;
			} else {
				var command;
				var values;
				var form = this.getPage('start')._form;
				if (form) {
					values = form.get('value');
				}
				if (pageName == 'restart') {
					return 'start';
				}
				if (pageName == 'start') {
					command = 'adtakeover/connect';
				}
				if (pageName == 'copy') {
					command = 'adtakeover/run/copy';
				}
				if (pageName == 'sysvol') {
					command = 'adtakeover/check/sysvol';
				}
				if (pageName == 'takeover') {
					command = 'adtakeover/run/takeover';
				}
				return this.run(command, values, nextPage);
			}
		},

		updateProgress: function(progresses, deferred, nextPage) {
			if (progresses) {
				var nextProgress = progresses.shift();
				if (nextProgress) {
					if (nextProgress.errors) {
						var nextPageWidget = this.getPage(nextPage);
						if (nextPageWidget._hadErrors) {
							delete nextProgress.errors;
						} else {
							nextPageWidget._hadErrors = true;
							nextProgress.errors[0] += ' (This error is due to the mockup version. Just try again)';
						}
					}
					deferred.progress(nextProgress);
					if (nextProgress.errors) {
						setTimeout(function() { deferred.reject(nextPage); }, 1400);
					} else {
						setTimeout(lang.hitch(this, function() { this.updateProgress(progresses, deferred, nextPage); }), 700);
					}
				} else {
					deferred.resolve(nextPage);
				}
			}
		},

		hasPrevious: function(pageName) {
			return array.indexOf(['copy'], pageName) !== -1;
		},

		canCancel: function(pageName) {
			return pageName != 'finished';
		}
	});

	return declare("umc.modules.adtakeover", Module , {
		unique: true,

		buildRendering: function() {
			var progressBar = new ProgressBar({});
			this.inherited(arguments);

			this.wizard = new TakeoverWizard({
				progressBar: progressBar
			});
			this.addChild(this.wizard);
			this.wizard.on('Finished', lang.hitch(this, function() {
				tools.umcpCommand('adtakeover/status/done', {}, false).then(lang.hitch(this, function(data) {
					topic.publish('/umc/tabs/close', this);
				}));
			}));
			this.wizard.on('Cancel', lang.hitch(this, function() {
				topic.publish('/umc/tabs/close', this);
			}));
		}
	});
});
