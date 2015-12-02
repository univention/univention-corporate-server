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
	"dojo/_base/fx",
	"dojo/dom",
	"dojo/dom-geometry",
	"dojo/io-query",
	"put-selector/put",
	"./i18n!."
], function(lang, fx, dom, domGeom, ioQuery, put, _) {

	return {
		getCurrentLanguageQuery: function() {
			return '?lang=' + (this.getQuery('lang') || 'en-US');
		},

		showMessage: function(msg) {
			var targetNode = msg.targetNode || dom.byId("content");
			var msgNode = dom.byId('msg');

			if (msgNode) {
				this._removeMessage();
				setTimeout(lang.hitch(this, 'showMessage', msg), 500);
			} else {
				msgNode = put('div[id=msg]');
				put(targetNode, 'div', msgNode);
				if (msg['class']) {
					put(msgNode, msg['class']);
				}
				// replace newlines with BR tags
				// msg = msg.replace(/\n/g, '<br/>');
				msgNode.innerHTML = msg.content;
			}
		},

		showLastMessage: function(msg) {
			var targetNode = msg.targetNode || dom.byId("title");
			var msgNode = dom.byId('msg');

			if (msgNode) {
				this._removeMessage();
				setTimeout(lang.hitch(this, 'showLastMessage', msg), 500);
			} else {
				var message = this._prepareLastMessage(msg);

				msgNode = put('div[id=msg]');
				put(targetNode, 'div', msgNode);
				if (msg['class']) {
					put(msgNode, msg['class']);
				}
				msgNode.innerHTML = message;
			}
		},

		_prepareLastMessage: function(msg) {
			var message = msg.content;
			var redirect = {
				url: this._getUrlForRedirect(),
				label: this._getUrlLabelForRedirect(),
				timer: this.getQuery('timer')
			};
			if (redirect.url) {
				var timer = redirect.timer || msg.timer || 5;
				message += lang.replace(_("</br><div>You will be redirected {0} in <a id='redirectTimer'> {1} </a> second(s).</div>", [redirect.label, timer]));
				var redirectInterval = setInterval(function() {
					timer--;
					if (timer === 0) {
						clearInterval(redirectInterval);
						window.location.href = redirect.url;
					}
					var redirectTimerNode = dom.byId("redirectTimer");
					redirectTimerNode.innerHTML = timer;
				}, 1000);
			} else {
				message += lang.replace(_("</br><a href='/{0}'>Back to the overview.</a>", [this.getCurrentLanguageQuery()]));
			}
			return message;
		},

		_getUrlForRedirect: function() {
			var queryUrl = this.getQuery('url');
			if (queryUrl) {
				// checking if queryUrl is relative = has to start wit only one '/'
				var reg = /^\/([^\/]|$)/;
				var isUrlRelative = reg.test(queryUrl);
				if (isUrlRelative) {
					return queryUrl;
				} else {
					// forbidden to provide absolute urls
					console.error(lang.replace(_('Forbidden redirect to: {0}\n The url has to start with (only) one "/".', [queryUrl])));
				}
			}
			return;
		},

		_getUrlLabelForRedirect: function() {
			var label = this.getQuery('urlLabel');
			if (label) {
				label = this._sanitizeHtmlTags(label);
				return lang.replace(_("to '{0}'", [label]));
			} else {
				return '';
			}
		},

		getQuery: function(key) {
			var queryString = window.location.search.substring(1);
			var queryObject = ioQuery.queryToObject(queryString);
			return queryObject[key];
		},

		_sanitizeHtmlTags: function(str) {
			return str.replace(/<(.|\n)*?>/g, '');
		},

		_removeMessage: function() {
			var msgNode = dom.byId('msg');
			if (msgNode) {
				put(msgNode, "!");
			}
		},

		wipeInNode: function(conf) {
			var endHeight = domGeom.getMarginBox(conf.node).h;
			fx.animateProperty({
				node: conf.node,
				duration: conf.duration || 500,
				properties: {
					height: { start: conf.startHeight || 0, end: conf.endHeight , units: 'px'}
				}
			}).play();
		},

		wipeOutNode: function(conf) {
			var currentHeight = domGeom.getMarginBox(conf.node).h;
			fx.animateProperty({
				node: conf.node,
				duration: conf.duration || 500,
				properties: {
					height: { end: 0, units: 'px'}
				},
				onEnd: conf.callback
			}).play();
		},

		getNodeHeight: function(node) {
			put(node, '.offScreen');
			put(document.body, node);
			var height = domGeom.position(node).h;
			put(node, '!offScreen');
			put(node, '!');
			return height;
		}
	};
});
