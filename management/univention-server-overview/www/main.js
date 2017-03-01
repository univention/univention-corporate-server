/*
 * Copyright 2017 Univention GmbH
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
	"dojo/dom",
	"dojo/dom-class",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"dijit/registry",
	"dojox/html/entities",
	"login",
	"umc/tools",
	"umc/json!/univention/meta.json",
	"umc/i18n!server-overview"
], function(declare, lang, array, kernel, dom, domClass, Memory, Observable, registry, entities, login, tools, meta, _) {
	var _regIPv4 =  /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))$/;
	var _regIPv6 = /^((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?$/;

	var _isIPAddress = function(ip) {
		ip = ip || '';
		var isIPv4Address = _regIPv4.test(ip);
		var isIPv6Address = _regIPv6.test(ip);
		return isIPv4Address || isIPv6Address;
	};

	return {
		standby: function(standby) {
			domClass.toggle(window.document.body, 'standby', standby);
		},

		start: function() {
			this.initLabels();
			login.start().then(lang.hitch(this, 'init'));
		},

		init: function() {
			this.initGallery();
			this.initLiveSearch();
		},

		initLabels: function() {
			var title = entities.decode(_('%s - Server overview', meta.ucr.domainname));
			window.document.title = title;

			title = entities.decode(_('Server overview for domain %s', meta.ucr.domainname));
			dom.byId('title').innerHTML = title;

			this.liveSearch = registry.byId('liveSearch');
			this.liveSearch._searchTextBox.set('inlineLabel', _('Search servers'));
		},

		initLiveSearch: function() {
			this.liveSearch.on('search', lang.hitch(this, function(pattern) {
				this.gallery.updateQuery(this.liveSearch.get('value'));
			}));
		},

		initGallery: function() {
			this.gallery = registry.byId('gallery');
			this.gallery.useFqdn = !_isIPAddress(window.location.hostname);
			tools.umcpCommand('serveroverview/query').then(lang.hitch(this, function(data) {
				var store = new Observable(new Memory({
					data: data.result,
					idProperty: 'dn'
				}));
				this.gallery.set('store', store);
				this.standby(false);
			}));
		}
	};
});
