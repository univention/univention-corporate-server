/*
 * Copyright 2020 Univention GmbH
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
/*global define*/

define([
	"dojo/_base/lang",
	"dojo/Deferred",
	"umc/i18n/tools",
	"umc/tools",
	"umc/json",
	"./links",
	"umc/json!/univention/portal/portal.json" // -> contains entries of this portal as specified in the LDAP directory
], function(lang, Deferred, i18nTools, tools, json, portalLinks, portalJson) {
	var locale = i18nTools.defaultLang().replace(/-/, '_');
	return {
		_portalJson: portalJson,

		reload(admin_mode) {
			var loadDeferred = new Deferred();

			var headers = null;
			if (admin_mode) {
				headers = {
					'X-Univention-Portal-Admin-Mode': 'yes'
				};
			}
			var waitedTime = 0;
			var waitTime = 200;

			var previousPortalJson = lang.clone(portalJson);

			var _load = () => {
				if (waitedTime >= 3000) {
					loadDeferred.resolve();
					return;
				}

				setTimeout(() => {
					json.load('/univention/portal/portal.json', require, result => {
						if (result && result.portal && result.entries && result.categories) {
							if (tools.isEqual(result, previousPortalJson)) {
								_load();
							} else {
								this._portalJson = result;
								loadDeferred.resolve();
							}
						} else {
							_load();
						}
					}, headers);
				}, waitTime);
				waitedTime += waitTime;
			};

			_load();
			return loadDeferred;
		},

		logo() {
			return this._portalJson.portal.logo;
		},

		title() {
			return this._portalJson.portal.name[locale] || this._portalJson.portal.name.en_US || 'Portal';
			// TODO do we want a fallback? we need something that is clickable (as home button)
		},

		portal() {
			return this._portalJson.portal;
		},

		content() {
			const toFrontendEntry = entry => ({
				type: 'entry',
				dn: entry.dn,
				name: entry.name[locale] || entry.name.en_US,
				description: entry.description[locale] || entry.description.en_US,
				href: portalLinks.getBestLinkAndHostname(entry.links).link,
				bgc: entry.bgc || 'var(--color-grey40)',
				logo: entry.logo_name || '/univention/portal/questionMark.svg',
				linkTarget: entry.linkTarget === 'useportaldefault'
					? this._portalJson.portal.defaultLinkTarget
					: entry.linkTarget,
			});

			const toFrontendFolder = folder => ({
				type: 'folder',
				dn: folder.dn,
				name: folder.name[locale] || folder.name.en_US,
				entries: folder.entries.map(entryDn => toFrontendEntry(this._portalJson.entries[entryDn])),
			});

			const toFrontendCategory = category => ({
				title: category.display_name[locale] || category.display_name.en_US,
				entries: category.entries.map(
					entryDn =>
					entryDn in this._portalJson.entries
					? toFrontendEntry(this._portalJson.entries[entryDn])
					: toFrontendFolder(this._portalJson.folders[entryDn])
				),
			});

			return this._portalJson.portal.categories.map(categoryDn => 
				toFrontendCategory(this._portalJson.categories[categoryDn]));
		},

		links() {
			const toFrontendLink = link => ({
				priority: link.$priority,
				dn: link.dn,
				name: link.name[locale] || link.name.en_US,
				description: link.description[locale] || link.description.en_US,
				href: portalLinks.getBestLinkAndHostname(link.links).link,
				logo: link.logo_name || '/univention/portal/questionMark.svg',
				linkTarget: link.linkTarget === 'useportaldefault'
					? this._portalJson.portal.defaultLinkTarget
					: link.linkTarget,
			});
			return {
				user: this._portalJson.user_links.map(link => toFrontendLink(link)),
				misc: this._portalJson.menu_links.map(link => toFrontendLink(link)),
			};
		}
	};
});

