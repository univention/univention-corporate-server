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
/*global define, window, location*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/query",
	"dojo/dom-class",
	"put-selector/put",
	"umc/tools",
	"umc/widgets/AppGallery"
], function(declare, lang, array, query, domClass, put, tools, AppGallery) {
	var _regIPv6Brackets = /^\[.*\]$/;

	var find = function(list, testFunc) {
		var results = array.filter(list, testFunc);
		return results.length ? results[0] : null;
	};

	var getHost = function(/*Array*/ ips, /*string*/ fqdn) {
		var host = window.location.host;

		if (tools.isIPv6Address(host)) {
			var ipv6 = find(ips, tools.isIPv6Address);
			if (ipv6 && !_regIPv6Brackets.test(ipv6)) {
					return '[' + ipv6 + ']';
			}
			if (ipv6) {
				return ipv6;
			}
			// use IPv4 as fallback
			return find(ips, tools.isIPv4Address);
		}
		if (tools.isIPv4Address(host)) {
			return find(ips, tools.isIPv4Address);
		}
		return fqdn;
	};

	return declare("PortalGallery", [ AppGallery ], {
		iconClassPrefix: 'umcPortal',

		domainName: null,

		postMixInProperties: function() {
			this.inherited(arguments);
			this.baseClass += ' umcPortalGallery';
		},

		postCreate: function() {
			// TODO: this changes with Dojo 2.0
			this.domNode.setAttribute("widgetId", this.id);

			// add specific DOM classes
			if (this.baseClass) {
				domClass.add(this.domNode, this.baseClass);
			}

			if (this.store) {
				this.set('store', this.store);
			}
		},

		getRenderInfo: function(item) {
			return lang.mixin(this.inherited(arguments), {
				itemSubName: item.host_name
			});
		},

		renderRow: function(item) {
			var domNode = this.inherited(arguments);
			put(domNode, 'a[href=$]', this._getWebInterfaceUrl(item), query('.umcGalleryItem', domNode)[0]);
			return domNode;
		},

		_getProtocolAndPort: function(app) {
			var protocol = window.location.protocol;
			var port = null;

			if (protocol === 'http:') {
				port = app.web_interface_port_http;
				if (!port && app.web_interface_port_https) {
					protocol = 'https:';
					port = app.web_interface_port_https;
				}
			} else if (protocol === 'https:') {
				port = app.web_interface_port_https;
				if (!port && app.web_interface_port_http) {
					protocol = 'http:';
					port = app.web_interface_port_http;
				}
			}

			if (port && app.auto_mod_proxy) {
				if (protocol === 'http:') {
					port = '80';
				} else if (protocol === 'https:') {
					port = '443';
				}
			}

			if (port === '80') {
				protocol = 'http:';
				port = null;
			} else if (port === '443') {
				protocol = 'https:';
				port = null;
			}
			if (port) {
				port = ':' + port;
			} else {
				port = '';
			}

			return {
				protocol: protocol,
				port: port
			};
		},

		_getWebInterfaceUrl: function(app) {
			if (!app.web_interface) {
				return "";
			}
			if (app.web_interface.indexOf('/') !== 0) {
				return app.web_interface;
			}

			var protocolAndPort = this._getProtocolAndPort(app);
			var protocol = protocolAndPort.protocol;
			var port = protocolAndPort.port;

			var fqdn = app.host_name + '.' + this.domainName;
			var host = (app.host_ips) ? getHost(app.host_ips, fqdn) : window.location.host;

			var url = lang.replace('{protocol}//{host}{port}{webInterface}', {
				protocol: protocol,
				host: host,
				port: port,
				webInterface: app.web_interface
			});

			return url;
		}
	});
});
