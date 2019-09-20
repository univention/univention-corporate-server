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
/*global define,require*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/kernel",
	"dojo/topic",
	"dojo/cookie",
	"dojo/query",
	"dojox/html/styles",
	"login",
	"umc/menu",
	"umc/tools",
	"umc/dialog",
	"umc/i18n/tools",
	"umc/widgets/Text",
	"umc/widgets/CheckBox",
	"umc/widgets/Button",
	"umc/i18n!"
], function(declare, lang, array, kernel, topic, cookie, query, styles, login, menu, tools, dialog, i18nTools, Text, CheckBox, Button, _) {
	setupMenus();

	function setupMenus() {
		setupSettingsContextMenu();
		setupCertificateMenu();
		setupLanguageMenu();
		setupHelpMenu();
		setupStartSiteLink();
		setupLoginAndLogoutButton();
		setupSupportNotification();
	}

	function setupSettingsContextMenu() {
		menu.addSubMenu({
			priority: 60,
			label: _('User settings'),
			id: 'umcMenuUserSettings'
		});
	}

	function setupCertificateMenu() {
		var _addEntries = function(masterURL) {
			var linkRootCa = masterURL + '/ucs-root-ca.crt';
			var linkRevocList = masterURL + '/ucsCA.crl';
			var currentRole = tools.status('server/role');
			if (currentRole === "domaincontroller_master" || currentRole === "domaincontroller_backup") {
				linkRootCa = '/ucs-root-ca.crt';
				linkRevocList = '/ucsCA.crl';
			}

			menu.addSubMenu({
				priority: 57,
				label: _('Certificates'),
				id: 'umcMenuCertificates'
			});

			menu.addEntry({
				parentMenuId: 'umcMenuCertificates',
				label: _('Root certificate'),
				onClick: function() {
					topic.publish('/umc/actions', 'menu', 'certificates', 'root');
					window.location.href = linkRootCa;
				}
			});

			menu.addEntry({
				parentMenuId: 'umcMenuCertificates',
				label: _('Certificate revocation list'),
				onClick: function() {
					topic.publish('/umc/actions', 'menu', 'certificates', 'revocation-list');
					window.location.href = linkRevocList;
				}
			});
		};

		if (tools.status('has_certificates')) {
			// we are on a DC master or backup system
			_addEntries('');
		}
		else {
			login.onInitialLogin(function() {
				// refer to the DC master
				_addEntries('//' + tools.status('ldap/master'));
			});
		}
	}

	function setupLanguageMenu() {
		var languageMenu = {
			priority: 55,
			label: _('Switch language'),
			id: 'umcMenuLanguage',
		};
		array.forEach(i18nTools.availableLanguages, function(language) {
			menu.addEntry({
				parentMenuId: 'umcMenuLanguage',
				label: language.label,
				disabled: language.id === i18nTools.defaultLang(),
				onClick: function() {
					topic.publish('/umc/actions', 'menu', 'switch-language', language.id);
					if (tools.status('loggedIn')) {
						dialog.confirm(_('<b>Warning</b>: The current session with all opened modules and unsaved settings gets lost and a page reload is done when switching the language.'), [{
							name: 'cancel',
							label: _('Cancel')
						}, {
							name: 'change',
							label: _('Switch language'),
							callback: function() {
								i18nTools.setLanguage(language.id);
							}
						}], _('Changing language'));
						return;
					}
					i18nTools.setLanguage(language.id);
				}
			});
		});

		if (i18nTools.availableLanguages.length > 1) {
			menu.addSubMenu(languageMenu);
		}
	}

	function setupHelpMenu() {
		// the help context menu
		menu.addSubMenu({
			priority: 50,
			label: _('Help'),
			id: 'umcMenuHelp'
		});

		var _openPage = function(url, key, query) {
			query = typeof query === 'string' ? query : '';
			topic.publish('/umc/actions', 'menu', 'help', key);
			var w = window.open(url + query);
			w.focus();
		};

		menu.addEntry({
			parentMenuId: 'umcMenuHelp',
			label: _('Univention Website'),
			priority: 120,
			onClick: lang.hitch(this, _openPage, _('https://www.univention.com/'), 'website')
		});
		menu.addEntry({
			parentMenuId: 'umcMenuHelp',
			label: _('Univention Forum "Help"'),
			priority: 110,
			onClick: lang.hitch(this, _openPage, _('https://help.univention.com/'), 'discourse')
		});
		menu.addEntry({
			parentMenuId: 'umcMenuHelp',
			label: _('Feedback'),
			priority: 100,
			onClick: function() {
				var page = location.pathname.replace(/^\/univention\/|\/[^/]*$/g, '');
				var query = '?umc=' + page;
				if ('umc/app' in (require.modules || {})) {
					try {
						query = '?umc=management/' + require('umc/app')._tabContainer.get('selectedChildWidget').title.toLowerCase();
					} catch(err) { }
				}
				_openPage(_('https://www.univention.com/feedback/'), 'feedback', query);
			}
		});
		menu.addEntry({
			parentMenuId: 'umcMenuHelp',
			label: _('Univention Blog'),
			priority: 90,
			onClick: lang.hitch(this, _openPage, _('https://www.univention.com/news/blog-en/'), 'blog')
		});
	}

	function setupStartSiteLink() {
		menu.addEntry({
			label: _('Back to start site'),
			priority: 0,
			onClick: function() {
				topic.publish('/umc/actions', 'menu', 'back-to-startsite');
				window.location.pathname = '/univention/';
			}
		});
	}

	function setupLoginAndLogoutButton() {
		var loginEntry = menu.addEntry({
			priority: -1,
			label: _('Login'),
			onClick: function() {
				topic.publish('/umc/actions', 'menu', 'login');
				login.start();
			}
		});
		if (tools.status('loggedIn')) {
			menu.hideEntry(loginEntry);
		}

		var logoutEntry = menu.addEntry({
			priority: -2,
			label: _('Logout'),
			onClick: function() {
				topic.publish('/umc/actions', 'menu', 'logout');
				login.logout();
			}
		});
		if (!tools.status('loggedIn')) {
			menu.hideEntry(logoutEntry);
		}

		login.onLogin(function() {
			menu.showEntry(logoutEntry);
			menu.hideEntry(loginEntry);
		});

		login.onLogout(function() {
			menu.hideEntry(logoutEntry);
			menu.showEntry(loginEntry);
		});
	}

	function setupSupportNotification() {
		// display a specific notification about the advantages of UCS subscriptions
		// for specific core edition users. The notification will pop up on each login.
		// There will also be a button on the head menu which links to our prices website.
		var targets = [
			"26f9a18b-cd20-4614-95b3-7150f040fb6e",
			"8b5a4c13-73b9-42e2-88f7-351a4f031b0d",
			"b12f0501-06b1-42ce-9383-295d104b7aab",
			"fead9e66-9393-467f-8b44-ad569d883719",
			"766857b8-685f-483d-8c01-a8ec03ff920d",
			"dcde6e6c-77ff-4279-b82c-c6a1494d80a2",
			"cac4f5e5-f3ef-454a-a074-046425679c07",
			"68e53c06-e25a-4436-b17b-498e8ac7d4d8",
			"3391a5a9-66e7-43df-897c-737229d27f41",
			"dd615bbf-5463-4506-ad3b-154e5ccf0731",
			"af5734ee-b484-46e8-a1b6-13fdd33d7ccb",
			"90366738-4473-4127-a7b0-83b451d3500e",
			"5af1252c-75c8-434f-be22-a2d3fac99b69",
			"5b72fb75-95b4-4a5c-9aa1-d5585305a67a",
			"21d97487-f178-421f-b122-3d9c47ab024d",
			"208c40ce-2216-48b8-b14e-eabfc1049b6f",
			"805effe2-3cc7-43b1-8592-2f623b6c1bcc",
			"dea72ddf-07ae-4182-9ec1-33a901bfacbd",
			"3c18fd68-27d0-44a8-8041-c604b12f20b5",
			"32defc48-428d-44dc-810b-6b57255e9eb7"
		];
		if (array.indexOf(targets, tools.status('uuid/license')) === -1) {
			return;
		}
		login.onLogin(function() {
		topic.subscribe('/umc/started', function() {
			var app = require('umc/app');
			if (!app.getModule('updater') && !app.getModule('schoolrooms') && !app.getModule('top')) {
				return;
			}
			query('.umcHeaderRight').forEach(function(w) {
				new Button({
					label: '<span style="color: white; background-color: rgba(0,0,0,0.178); padding: 0.5em; border-radius: 5px; text-transform: none;">' + _('Buy support package') + '</span>',
					style: 'box-shadow: none; margin: 0;',
					onClick: function() {
						topic.publish('/umc/actions', 'enterprise-subskription', 'click', 'button');
						window.open(_('https://www.univention.com/products/prices-and-subscriptions/'), '_blank');
					}
				}).placeAt(w, 'first');
			});
			if (cookie('univentionSubscriptionNotification') === 'no') {
				return;
			}

			var tickImage = 'iVBORw0KGgoAAAANSUhEUgAAAA8AAAANCAYAAAB2HjRBAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAAsSAAALEgHS3X78AAABHElEQVQoz5XRPUtcQRSH8d9e1y+glSS93EItBAtbyyFNKjtBEGEbS7n4VukYkIQUgYClgigWgt5CFHutbMJ8gTT7AZIi4EszFxZ1jZ5mGA7/ec48p+WNVdWlGJKqLgfwGWPFO4OD2MEPXLfeQR7CKabQiSHtFv8j5nMEx5jGXgxpF9pvGHUUl/iIQyw0/XYW8AG/Y0j3DS0HJ3GOYdxgHncNoI0OvmILGzGkhjyOkxz8g9UY0t8mGENSoJsfWa/q8iAHJ3CbR4VvMaSLp18rcISVfJ+t6vIMV2g2sR9DWqvq8tlmWj2ClrH9pP8LMzGk7ktSix6zX7DZ0/uH7+g2El8jN4Z/YhE1PsWQHvqts+i1l2sJe5iLIT30o8IjGRJl2q1xe4EAAAAASUVORK5CYII=';
			var message = '<ul style="list-style-position: inside; list-style-image: url(data:image/png;base64,' + tickImage + '); font-weight: bold; padding-left: 1em;">' +
				'<li>' + _('Support and Professional Services') + '</li>' +
				'<li>' + _('Up to 7 years of maintenance (LTS)') + '</li>' +
				'<li>' + _('Hard- and software certifications') + '</li>' +
				'<li>' + _('Manufacturer warranty with product liability') + '</li>' +
			'</ul>' +
			'<p>' + _('Starting at <b>290.- Euro/year</b> you can purchase a UCS Enterprise Edition. This license allows you to benefit from basic support services as well as individually bookable, additional support and professional services.') + '</p>' +
			'<p>' + _('You can extend the maintenance for your UCS version to up to 7 years and thanks to certifications and manufacturer warranty you are legally secured when operating your IT infrastructure.') + '</p>';
			var title = _('Advantages of the Enterprise Edition');
			var submit = _('Prices and support');

			styles.insertCssRule('.umcSubscriptionDialog > div', 'background-color: transparent!important;');
			topic.publish('/umc/actions', 'enterprise-subskription', 'show');
			dialog.confirmForm({
				title: title,
				style: 'background: #ffffff url(' + require.toUrl('dijit/themes/umc/images/checkmark-enterprise-subscription.png') + ') 80% 2.7em no-repeat; background-size: 120px;',
				'class': 'umcSubscriptionDialog',
				submit: submit,
				close: _('Close'),
				widgets: [{
					name: 'message',
					type: Text,
					content: message
				}, {
					name: 'unset',
					type: CheckBox,
					onChange: function(arg) {
						topic.publish('/umc/actions', 'enterprise-subskription', 'disable', arg);
						cookie('univentionSubscriptionNotification', arg ? 'no': 'yes');
					},
					label: _('Do not show this notification again')
				}],
				layout: ['message', 'unset']
			}).then(function() {
				topic.publish('/umc/actions', 'enterprise-subskription', 'click', 'dialog');
				window.open(_('https://www.univention.com/products/prices-and-subscriptions/'), '_blank');
			}, function() {
				topic.publish('/umc/actions', 'enterprise-subskription', 'cancel');
			});
		});
		});
	}
});
