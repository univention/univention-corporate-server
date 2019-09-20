/*
 * Copyright 2017-2019 Univention GmbH
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
/*global define,dojo,*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/xhr",
	"dojo/dom",
	"dojo/dom-class",
	"dojo/dom-style",
	"dijit/focus",
	"dojo/topic",
	"dojo/promise/all",
	"dojox/html/styles",
	"dijit/layout/ContentPane",
	"login",
	"umc/tools",
	"umc/widgets/Text",
	"umc/widgets/Button",
	"umc/widgets/ProgressBar",
	"umc/widgets/StandbyMixin",
	"umc/widgets/ContainerWidget",
	"./ApplianceWizard",
	"umc/json!/univention/setup/privacy_statement.json",
	"umc/i18n/tools",
	"umc/i18n!setup"
], function(declare, lang, array, xhr, dom, domClass, domStyle, focusUtil, topic, all, styles, ContentPane, login, tools, Text, Button, ProgressBar, Standby, ContainerWidget, ApplianceWizard, privacyStatementContent, i18nTools, _) {
	return {
		_container: null,
		wizard: null,
		moduleFlavor: 'wizard',
		local_mode: false,

		start: function(props) {
			login.onInitialLogin(lang.hitch(this, '_initWizard'));
			login.start(props.username, props.password);
		},

		standby: function(standby) {
			domClass.toggle(document.body, 'standby', standby);
		},

		umcpCommand: function( /*String*/ commandStr, /*Object?*/ dataObj, /*Boolean?*/ handleErrors, /*String?*/ flavor, /*Object?*/ longPollingOptions ) {
			return tools.umcpCommand( commandStr, dataObj, handleErrors, flavor || this.moduleFlavor, longPollingOptions );
		},

		umcpProgressCommand: function( /*Object*/ progressBar, /*String*/ commandStr, /*Object?*/ dataObj, /*Boolean?*/ handleErrors, /*String?*/ flavor, /*Object?*/ longPollingOptions ) {
			return tools.umcpProgressCommand( progressBar, commandStr, dataObj, handleErrors, flavor || this.moduleFlavor, longPollingOptions );
		},

		_initWizard: function() {
			this.local_mode = tools.status('username') === '__systemsetup__';
			var _Container = declare([ContainerWidget, Standby]);
			this._container = new _Container({
			}, 'content');

			// load some ucr variables
			var deferred_ucr = tools.ucr([
				'server/role',
				'system/setup/boot/select/role',
				'system/setup/boot/pages/whitelist',
				'system/setup/boot/pages/blacklist',
				'system/setup/boot/fields/blacklist',
				'system/setup/boot/minimal_memory',
				'system/setup/boot/installer',
				'system/setup/boot/start',
				'docker/container/uuid',
				'umc/modules/setup/network/disabled/by',
				'umc/web/appliance/*'
			]);

			all({
				ucr: deferred_ucr,
				values: this.umcpCommand('setup/load')
			}).then(lang.hitch(this, function(data) {
				this._progressBar = new ProgressBar();
				var values = data.values.result;

				// save current values
				this._orgValues = lang.clone(values);

				this._renderWizard(values, data.ucr);
				this._renderPrivacyStatementOverlay();

				tools.defer(lang.hitch(this, 'standby', false), 500);
			}));
		},

		_renderWizard: function(values, ucr) {
			var partOfInstaller = tools.isTrue(ucr['system/setup/boot/installer']);

			// add blacklist for pages. The pages will be removed without any replacement.
			// empty lists are treated as if they were not defined at all (show all pages). list names should
			// match the names in this.pages and can be separated by a ' '.
			var fieldBlacklist = (ucr['system/setup/boot/fields/blacklist'] || '').split(' ');
			var pageBlacklist = (ucr['system/setup/boot/pages/blacklist'] || '').split(' ');
			if (!tools.isTrue(ucr['system/setup/boot/select/role'])) {
				pageBlacklist.push('SystemRolePage');
			}

			pageBlacklist = array.map(pageBlacklist, function(page) {
				var replacements = {
					'SoftwarePage': 'software',
					'SystemRolePage': 'role'
				};
				return replacements[page] || page;
			});
			var rolePageDisabled = array.indexOf('role', pageBlacklist) === -1;
			if (rolePageDisabled) {
				// make sure to disable all pages linked to role selection
				pageBlacklist.push('role-nonmaster-ad');
			}

			this.wizard = new ApplianceWizard({
				//progressBar: progressBar
				moduleID: this.moduleID,
				disabledPages: pageBlacklist,
				disabledFields: fieldBlacklist,
				local_mode: this.local_mode,
				umcpCommand: lang.hitch(this, 'umcpCommand'),
				umcpProgressCommand: lang.hitch(this, 'umcpProgressCommand'),
				partOfInstaller: partOfInstaller,
				values: values,
				ucr: ucr
				//standby: lang.hitch(this, 'standby'),
				//standbyDuring: lang.hitch(this, 'standbyDuring')
			});
			if (!tools.status('overview')) {
				this.wizard.watch('selectedChildWidget', lang.hitch(this, function(name, old, child) {
					this.set('title', child.get('headerText'));
				}));
				this.set('title', this.wizard.get('selectedChildWidget').get('headerText'));
				styles.insertCssRule(lang.replace('#{id} .umcPageHeader', this.wizard), 'display: none!important;');
			}
			this.wizard.on('Finished', lang.hitch(this, function(newValues) {
				// wizard is done -> call cleanup command and redirect browser to new web address
				topic.publish('/umc/actions', this.moduleID, 'wizard', 'done');
				tools.checkSession(false);
				if (this.wizard.local_mode) {
					this._showDummyProgressbar();

					this.umcpCommand('setup/closebrowser').then(function(data) {
						if (!data.result) {
							window.close();
						}
					}, function() {
						window.close();
					});
				} else {
					this._redirectBrowser(newValues.interfaces, newValues['interfaces/primary']);
				}
			}));
			this.wizard.on('Reload', lang.hitch(this, '_reloadWizard', values, ucr));
			this._container.addChild(this.wizard);
			this._container.startup();
		},

		_renderPrivacyStatementOverlay: function() {
			var previousFocusNode;
			var overlay = new ContainerWidget({
				'class': 'privacyStatementOverlay privacyStatementOverlayHidden',
				show: lang.hitch(this, function() {
					previousFocusNode = focusUtil.curNode;
					domClass.remove(overlay.domNode, 'privacyStatementOverlayHidden');
					focusUtil.focus(closeButton);
					if (this.local_mode) {
						window.scrollTo(0, 0);
						domStyle.set(dojo.body(), 'overflow', 'hidden');
					}
				})
			});
			var title = new Text({
				'class': 'privacyStatementOverlayTitle',
				content: _('Privacy Statement')
			});
			var content = new ContentPane({
				'class': 'privacyStatementOverlayContent',
				content: privacyStatementContent[i18nTools.defaultLang()] || privacyStatementContent['en-US']
			});
			var footer = new ContainerWidget({
				'class': 'privacyStatementOverlayFooter'
			});
			var closeButton = new Button({
				'class': 'privacyStatementOverlayFooterButton umcFlatButton',
				defaultButton: true,
				label: _('Close'),
				callback: function() {
					domClass.add(overlay.domNode, 'privacyStatementOverlayHidden');
					domStyle.set(dojo.body(), 'overflow', '');
					focusUtil.focus(previousFocusNode);
				}
			});

			overlay.addChild(title);
			overlay.addChild(content);
			overlay.addChild(footer);
			footer.addChild(closeButton);

			domClass.toggle(overlay.domNode, 'privacyStatementOverlayLocalMode', this.local_mode);
			var target = this.local_mode ? this._container : this.wizard;
			target.domNode.appendChild(overlay.domNode);

			var link = lang.replace('<a href="javascript:require(\'dijit/registry\').byId(\'{0}\').show();">{1}</a>', [overlay.id, _('privacy statement')]);
			var content = _('With the activation of UCS you agree to our %s.', link);
			this.wizard.getWidget('privacyStatement').set('content', content);

			this.privacyStatementOverlay = overlay;
		},

		_reloadWizard: function(values, ucr, newLocale) {
			// update internal locale settings
			var _setLocale = lang.hitch(this, function() {
				dojo.locale = newLocale;
				var locale = newLocale.replace('-', '_');
				var deferreds = [];
				deferreds.push(this.umcpCommand('set', {
					locale: locale
				}, false));
				deferreds.push(this.umcpCommand('setup/set_locale', {
					locale: locale
				}, false));
				deferreds.push(_.load());
				return all(deferreds);
			});

			// remove wizard and render it again
			var _cleanup = lang.hitch(this, function() {
				this._container.removeChild(this.wizard);
				this.wizard.destroy();
				this._renderWizard(this._orgValues, ucr);
				this.privacyStatementOverlay.destroy();
				this._renderPrivacyStatementOverlay();
			});

			// chain tasks with some time in between to allow a smooth standby animation
			this.standby(true);
			var self = this;
			tools.defer(_setLocale, 200).then(function() {
				return tools.defer(_cleanup, 200);
			}).then(function() {
				return tools.defer(lang.hitch(self, 'standby', false), 200);
			});
		},

		_showDummyProgressbar: function() {
			this._progressBar.reset();
			this._progressBar.setInfo(_('Restarting server components...'), _('This may take a few seconds...'), Number.POSITIVE_INFINITY);
			this._container.standby(true, this._progressBar);
		},

		_redirectBrowser: function(interfaces, primary_interface) {
			// redirect to new UMC address and set username to Administrator
			this._container.standby(true);
			var target = '/univention/management/?username=Administrator';
			if (this._orgValues.system_activation_installed && this.wizard._isRoleMaster()) {
				// redirect to '/' as the system activation service is enabled
				// (Note: For roles other than DC master, the system activation service
				// will not be enabled as they may only join into a domain with an
				// already activated license.)
				// Add a random digit at the end to avoid caching effects
				target = '/?_rnd=' + Math.floor(Math.random() * 10e10);
			}
			target = window.location.href.replace(new RegExp( "/univention/setup/.*", "g" ), target);

			// Consider IP changes, replace old ip in url by new ip
			var newIp = this._getNewIpAddress(interfaces, primary_interface || 'eth0');
			if (newIp) {
				var oldIp = window.location.host;
				target = target.replace(oldIp, newIp);
			}

			// give the restart/services function 10 seconds time to restart the services
			setTimeout(function () {
				window.location.replace(target);
			}, 2000);
		},

		_getNewIpAddress: function(interfaces, primary_interface) {
			interfaces = interfaces || {};
			var newIpAddress = null;

			var currentIP = window.location.host;
			currentIP = currentIP.replace('[', '').replace(']', '');

			var prim = interfaces[primary_interface];
			var primIp4 = prim && prim.ip4[0] && prim.ip4[0][0];
			var primIp6 = prim && prim.ip6[0] && prim.ip6[0][0];

			tools.forIn(this._orgValues.interfaces, function(ikey, iface) {
				// 1. check if value is equal to the current IP
				// 2. check if a new value was set or use IP from new primary interface
				var oldIp4 = iface.ip4[0] && iface.ip4[0][0];
				var oldIp6 = iface.ip6[0] && iface.ip6[0][0];
				var newIp4 = interfaces[ikey] && interfaces[ikey].ip4[0] && interfaces[ikey].ip4[0][0];
				var newIp6 = interfaces[ikey] && interfaces[ikey].ip6[0] && interfaces[ikey].ip6[0][0];
				if (oldIp4 === currentIP) {
					newIpAddress = newIp4 || primIp4 || newIp6 || primIp6;
				} else if (oldIp6 === currentIP) {
					newIpAddress = newIp6 || primIp6 || newIp4 || primIp4;
				}
			});
			if (newIpAddress === currentIP) {
				newIpAddress = null;
			}
			if (newIpAddress && !(/[.]/).test(newIpAddress)) {
				// ipv6
				newIpAddress = '[' + newIpAddress + ']';
			}
			return newIpAddress;
		},


	};
});
