/*
 * Copyright 2014-2017 Univention GmbH
 *
 * http://www.univention.de/
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
 * <http://www.gnu.org/licenses/>.
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/kernel",
	"dojo/topic",
	"login",
	"umc/menu",
	"umc/tools",
	"umc/dialog",
	"umc/i18n/tools",
	"umc/i18n!"
], function(declare, lang, array, kernel, topic, login, menu, tools, dialog, i18nTools, _) {
	setupMenus();

	function setupMenus() {
		setupSettingsContextMenu();
		setupCertificateMenu();
		setupLanguageMenu();
		setupHelpMenu();
		setupStartSiteLink();
		setupLoginAndLogoutButton();
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
			if (currentRole == "domaincontroller_master" || currentRole == "domaincontroller_backup") {
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
							name: 'change',
							label: _('Switch language'),
							callback: function() {
								i18nTools.setLanguage(language.id);
							}
						}, {
							name: 'cancel',
							label: _('Cancel')
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
			query = typeof query == 'string' ? query : '';
			topic.publish('/umc/actions', 'menu', 'help', key);
			var w = window.open(url + query);
			w.focus();
		};

		menu.addEntry({
			parentMenuId: 'umcMenuHelp',
			label: _('Univention Website'),
			priority: 120,
			onClick: lang.hitch(this, _openPage, _('http://www.univention.com'), 'website')
		});
		menu.addEntry({
			parentMenuId: 'umcMenuHelp',
			label: _('Univention Help'),
			priority: 110,
			onClick: lang.hitch(this, _openPage, _('http://help.univention.com'), 'discourse')
		});
		menu.addEntry({
			parentMenuId: 'umcMenuHelp',
			label: _('Feedback'),
			priority: 100,
			onClick: function() {
				var page = location.pathname.replace(/^\/univention\/|\/[^/]*$/g, '');
				var query = '?umc=' + page;
				if ('umc/app' in require.modules) {
					try {
						query = '?umc=management/' + require('umc/app')._tabContainer.get('selectedChildWidget').title.toLowerCase();
					} catch(err) { }
				}
				_openPage(_('https://www.univention.com/feedback/'), 'feedback', query);
			}
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
});
