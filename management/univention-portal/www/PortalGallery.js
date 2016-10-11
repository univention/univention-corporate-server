/*
 * Copyright 2016 Univention GmbH
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
	"dojo/dom-class",
	"dojo/on",
	"dojo/mouse",
	"umc/tools",
	"management/modules/appcenter/AppCenterGallery",
	"put-selector/put"
], function(declare, lang, domClass, on, mouse, tools, AppCenterGallery, put) {
	var _regIPv4 =  /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))$/;
	var _regIPv6 = /^\[?((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\]?$/;
	var _regIPv6Brackets = /^\[.*\]$/;
	var findIPv6 = function(ip) {
		return _regIPv6.test(ip);
	};
	var findIPv4 = function(ip) {
		return _regIPv4.test(ip);
	};

	var getHost = function(/*Array*/ ips, /*string*/ fqdn) {
		var host = window.location.host;

		if (_regIPv6.test(host)) {
			var ipv6 = ips.find(findIPv6);
			if (ipv6 && !_regIPv6Brackets.test(ipv6)) {
				ipv6 = '[' + ipv6 + ']';
			}
			return ipv6 || ips.find(findIPv4);
		}
		if (_regIPv4.test(host)) {
			return ips.find(findIPv4);
		}
		return fqdn;
	};

	return declare("PortalGallery", [AppCenterGallery], {
		domainName: null,

		getIconClass: function(iconName) {
			return tools.getIconClass(iconName, 'scalable', 'portal');
		},

		renderRow: function(item) {
			var div = this.inherited(arguments);

			put(div, 'div.boxShadow.bl div.hoverBackground << div.boxShadow.tr div.hoverBackground');

			// clone the old node to remove eventListeners
			var _appInnerWrapper = div.querySelector('.appInnerWrapper');
			appInnerWrapper = dojo.clone(_appInnerWrapper);
			dojo.destroy(_appInnerWrapper);

			put(div, appInnerWrapper.querySelector('.appIcon'));
			put(appInnerWrapper.querySelector('.border'), '!');
			put(appInnerWrapper.querySelector('.umcGalleryVendor'), '!');
			put(appInnerWrapper.querySelector('.umcGalleryName'), '+ div.umcGalleryHost', item.host_name);
			put(appInnerWrapper, 'div.contentWrapper', appInnerWrapper.querySelector('.appContent'), '+', appInnerWrapper.querySelector('.appHover'));
			put(div, 'a[href=$]', this._getWebInterfaceUrl(item), appInnerWrapper);

			on(div, mouse.enter, function() {
				domClass.add(div, 'hover');
			});
			on(div, mouse.leave, function() {
				domClass.remove(div, 'hover');
			});

			return div;
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
