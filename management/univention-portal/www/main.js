/*
 * Copyright 2016-2017 Univention GmbH
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
	"dijit/registry",
	"dojo/on",
	"dojo/dom",
	"./PortalCategory",
	"umc/i18n/tools",
	"umc/json!/univention/portal/portal.json",
	"umc/json!/univention/meta.json",
	"umc/i18n!/univention/i18n"
], function(declare, lang, array, kernel, registry, on, dom, PortalCategory, i18nTools, portalContent, meta, _) {
	return {
		portalCategories: null,

		_createCategories: function() {
			this.portalCategories = [];

			var portal = portalContent.portal;
			var entries = portalContent.entries;
			var locale = i18nTools.defaultLang().replace(/-/, '_');
			var protocol = window.location.protocol;
			var _regIPv4 =  /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))$/;
			var _regIPv6 = /^\[?((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\]?$/;
			var host = window.location.host;
			var isIPv4 = false;
			var isIPv6 = false;
			if (_regIPv4.test(host)) {
				isIPv4 = true;
			}
			if (_regIPv6.test(host)) {
				isIPv6 = true;
			}

			array.forEach(['admin', 'service'], lang.hitch(this, function(category) {
				var categoryEntries = array.filter(entries, function(entry) {
					// TODO: filter by entry.authRestriction (anonymous, authenticated, admin)
					return entry.category == category && entry.activated && entry.portals.indexOf(portal.dn) !== -1;
				});
				if (categoryEntries.length) {
					var apps = [];
					array.forEach(categoryEntries, function(entry) {
						var _entry = {
							name: entry.name[locale] || entry.name.en_US,
							description: entry.description[locale] || entry.description.en_US
						};
						var myProtocolSupported = array.some(entry.links, function(link) {
							return link.indexOf(protocol) === 0;
						});
						var onlyOneKind = array.every(entry.links, function(link) {
							var _linkElement = document.createElement('a');
							_linkElement.setAttribute('href', link);
							var linkHost = _linkElement.hostname;
							return !_regIPv4.test(linkHost) && !_regIPv6.test(linkHost);
						});
						onlyOneKind = onlyOneKind || array.every(entry.links, function(link) {
							var _linkElement = document.createElement('a');
							_linkElement.setAttribute('href', link);
							var linkHost = _linkElement.hostname;
							return _regIPv4.test(linkHost) || _regIPv6.test(linkHost);
						});
						array.forEach(entry.links, function(link) {
							var _linkElement = document.createElement('a');
							_linkElement.setAttribute('href', link);
							var linkHost = _linkElement.hostname;
							if (! onlyOneKind) {
								if (myProtocolSupported) {
									if (link.indexOf(protocol) !== 0) {
										return;
									}
								}
								if (isIPv4) {
									if (! _regIPv4.test(linkHost)) {
										return;
									}
								} else if (isIPv6) {
									if (! _regIPv6.test(linkHost)) {
										return;
									}
								} else {
									if (_regIPv4.test(linkHost) || _regIPv6.test(linkHost)) {
										return;
									}
								}
							}
							apps.push(lang.mixin({web_interface: link, host_name: linkHost}, _entry));
						});
					});
					var title;
					if (category == 'admin') {
						title = _('Administration');
					} else {
						title = _('Installed services');
					}
					if (apps.length) {
						this._addCategory(title, apps);
					}
				}
			}));
			array.forEach(portal, lang.hitch(this, function(category) {
				this._addCategory(category.title, category.apps);
			}));
		},

		_addCategory: function(title, apps) {
			var portalCategory = new PortalCategory({
				title: title,
				apps: apps,
				domainName: meta.ucr.domainname
			});
			this.content.appendChild(portalCategory.domNode);
			this.portalCategories.push(portalCategory);
		},

		start: function() {
			this.content = dom.byId('content');
			this.search = registry.byId('umcLiveSearch');
			this.search.on('search', lang.hitch(this, 'filterPortal'));
			this._createCategories();
			apps = [{
				id: 'umc',
				name: 'Management',
				description: 'Administrate the UCS domain and the local system',
				web_interface: '/univention/management',
				logo_name: 'univention-management-console',
				host_name: meta.ucr.hostname
			}];
			this._addCategory('Management', apps);
		},

		filterPortal: function() {
			var searchPattern = lang.trim(this.search.get('value'));
			var searchQuery = this.search.getSearchQuery(searchPattern);

			var query = function(app) {
				return searchQuery.test(app);
			};

			array.forEach(this.portalCategories, function(category) {
				category.set('query', query);
			});
		}
	};
});
