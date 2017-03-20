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
	"umc/tools",
	"umc/i18n/tools",
	// portal.json -> contains entries of this portal as specified in the LDAP directory
	"umc/json!/univention/portal/portal.json",
	// apps.json -> contains all locally installed apps
	"umc/json!/univention/portal/apps.json",
	"umc/i18n!/univention/i18n"
], function(declare, lang, array, kernel, registry, on, dom, PortalCategory, tools, i18nTools, portalContent, installedApps, _) {

	var _regEndsWithSVG = /\.svg$/;
	var hasSVGSuffix = function(path) {
		return path && _regEndsWithSVG.test(path);
	};

	var hasAbsolutePath = function(path) {
		return path && path.indexOf('/') === 0;
	};

	return {
		portalCategories: null,

		_createCategories: function() {
			this.portalCategories = [];

			var portal = portalContent.portal;
			var entries = portalContent.entries;
			var locale = i18nTools.defaultLang().replace(/-/, '_');
			var protocol = window.location.protocol;
			var host = window.location.host;
			var isIPv4 = tools.isIPv4Address(host);
			var isIPv6 = tools.isIPv6Address(host);

			var title = dom.byId('portalTitle');
			var portalName = lang.replace(portal.name[locale] || portal.name.en_US, tools._status);
			title.innerHTML = portalName;
			document.title = portalName;
			array.forEach(['admin', 'service'], lang.hitch(this, function(category) {
				var categoryEntries = array.filter(entries, function(entry) {
					// TODO: filter by entry.authRestriction (anonymous, authenticated, admin)
					return entry.category == category && entry.activated && entry.portals.indexOf(portal.dn) !== -1;
				});
				var apps = this._getApps(categoryEntries, locale, protocol, isIPv4, isIPv6);
				var heading;
				if (category == 'admin') {
					heading = _('Administration');
				} else if (category == 'service') {
					heading = _('Installed services');
				} else if (category == 'apps') {
					heading = _('Installed Apps');
				}
				this._addCategory(heading, apps, category == 'service');
			}));
			if (portal.showApps) {
				var apps = this._getApps(installedApps, locale, protocol, isIPv4, isIPv6);
				this._addCategory(_('Installed Apps'), apps);
			}
		},

		_getApps: function(categoryEntries, locale, protocol, isIPv4, isIPv6) {
			var apps = [];
			array.forEach(categoryEntries, function(entry) {
				var _getLogoName = function(logo) {
					if (logo) {
						if (hasAbsolutePath(logo)) {
							// make sure that the path starts with http[s]:// ...
							// just to make tools.getIconClass() leaving the URL untouched
							logo = window.location.origin + logo;

							if (!hasSVGSuffix(logo)) {
								// an URL starting with http[s]:// needs also to have a .svg suffix
								logo = logo + '.svg';
							}
						}
					}
					return logo;
				};

				var _entry = {
					name: entry.name[locale] || entry.name.en_US,
					description: entry.description[locale] || entry.description.en_US,
					logo_name: _getLogoName(entry.logo_name)
				};

				var myProtocolSupported = array.some(entry.links, function(link) {
					return link.indexOf(protocol) === 0;
				});
				var onlyOneKind = array.every(entry.links, function(link) {
					var _linkElement = document.createElement('a');
					_linkElement.setAttribute('href', link);
					var linkHost = _linkElement.hostname;
					return !tools.isIPAddress(linkHost);
				});
				onlyOneKind = onlyOneKind || array.every(entry.links, function(link) {
					var _linkElement = document.createElement('a');
					_linkElement.setAttribute('href', link);
					var linkHost = _linkElement.hostname;
					return tools.isIPAddress(linkHost);
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
							if (! tools.isIPv4Address(linkHost)) {
								return;
							}
						} else if (isIPv6) {
							if (! tools.isIPv6Address(linkHost)) {
								return;
							}
						} else {
							if (! tools.isFQDN(linkHost)) {
								return;
							}
						}
					}
					apps.push(lang.mixin({
						web_interface: link,
						host_name: linkHost
					}, _entry));
				});
			});
			return apps;
		},

		_addCategory: function(heading, apps, sorting) {
			if (!heading || !apps.length) {
				return;
			}
			var portalCategory = new PortalCategory({
				heading: heading,
				apps: apps,
				domainName: tools.status('domainname'),
				sorting: sorting || false
			});
			this.content.appendChild(portalCategory.domNode);
			portalCategory.startup();
			this.portalCategories.push(portalCategory);
		},

		start: function() {
			this.content = dom.byId('content');
			this.search = registry.byId('umcLiveSearch');
			this.search.on('search', lang.hitch(this, 'filterPortal'));
			this._createCategories();
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
