/*
 * Copyright 2015 Univention GmbH
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
/*global define require console window */

define([
	"dojo/_base/lang",
	"dojo/_base/kernel",
	"dojo/_base/array",
	"dojo/io-query",
	"dojo/query",
	"dojo/dom",
	"dojo/dom-construct",
	"dojo/dom-attr",
	"dojo/dom-style",
	"dojo/dom-class",
	"dojo/dom-geometry",
	"../ucs/text!/ucs-overview/welcome.json",
	"../ucs/i18n!welcome,ucs"
], function(lang, kernel, array, ioQuery, query, dom, domConstruct, domAttr, domStyle, domClass, domGeometry, data, _) {
	return {
		start: function() {
			this.replaceTitle();
			this.addApplianceLogo();
			this.insertLinks();

		},

		replaceTitle: function() {
			if (data['umc/web/appliance/name']) {
				var title = _('Welcome to the {0} appliance with Univention Corporate Server', [data['umc/web/appliance/name']]);
				var titleNode = query('h1', 'title')[0];
				domAttr.set(titleNode, 'data-i18n', title);
				titleNode.innerHTML = title;
				query('title')[0].innerHTML = title;
			}
		},

		addApplianceLogo: function() {
			if (data['umc/web/appliance/logo']) {
				var path = data['umc/web/appliance/logo'];
				if (path[0] !== '/') {
					path = '/univention-management-console/js/dijit/themes/umc/' + path;
				}
				domStyle.set('welcome-appliance-logo', 'background-image', lang.replace('url({0})', [path]));
			}
		},

		insertLinks: function() {
			var alternatives = dom.byId('welcome-url-alternative');
			array.forEach(data['ip_addresses'].concat([data['hostname'] + '.' + data['domainname']]).concat(data['ip6_addresses']), function(address, i, arr) {
				address = this.formatUrl(address, data['ip6_addresses'].indexOf(address) !== -1);
				if (i == 0) {
					dom.byId('welcome-url').innerHTML = address;
				} else {
					domClass.toggle(alternatives, 'dijitHidden', false);
					domConstruct.create('span', {innerHTML: address}, alternatives);
				}
			}, this);
		
		},

		formatUrl: function(url, ip6) {
			if (ip6) {
				url = '[' + url + ']';
			}
			return 'https://' + url + '/';
		}
	};
});
