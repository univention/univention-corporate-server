/*
 * Copyright 2015-2017 Univention GmbH
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
/*global define, window */

define([
	"dojo/_base/lang",
	"dojo/_base/fx",
	"dojo/dom",
	"dojo/dom-geometry",
	"dojo/hash",
	"dojo/io-query",
	"dojox/html/entities",
	"put-selector/put",
	"dojo/request",
	"umc/i18n!."
], function(lang, fx, dom, domGeom, hash, ioQuery, htmlEntities, put, request, _) {

	return {
		getCurrentLanguageQuery: function() {
			return '?lang=' + (this.getQuery('lang') || 'en-US');
		},

		_getServerMsgNode: function() {
			var serverMsgNode = dom.byId("server_msg");
			if (serverMsgNode) {
				return serverMsgNode;
			}
			serverMsgNode = put(dom.byId('contentContainer'), 'div[id=server_msg]');
			return serverMsgNode;
		},

		/**
		 * Displays given message.
		 * @param {object} msg - Provides targetNode, class and content
		 * for the message.
		 */
		showMessage: function(msg) {
			var targetNode = msg.targetNode || this._getServerMsgNode();
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
			var targetNode = msg.targetNode || this._getServerMsgNode();
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

		/**
		 * Returns relative url from query string.
		 */
		_getUrlForRedirect: function() {
			var queryUrl = this.getQuery('url');
			if (queryUrl) {
				if (this._isUrlRelative(queryUrl)) {
					return queryUrl;
				} else {
					var msg = {
						content: lang.replace(_('Forbidden redirect to: {0}\n The url has to start with (only) one "/".', [queryUrl])),
						'class': 'error'
					};
					this.showMessage(msg);
				}
			}
			return;
		},

		/** Returns boolean if given url is relative.
		 * @param {string} url - url to test
		 * */
		_isUrlRelative: function(url) {
				var reg = /^\/([^\/]|$)/;
				var isUrlRelative = reg.test(url);
				return isUrlRelative;
		},

		_getUrlLabelForRedirect: function() {
			var label = this.getQuery('urlLabel');
			if (label) {
				label = htmlEntities.encode(label);
				return lang.replace(_("to '{0}'", [label]));
			} else {
				return '';
			}
		},

		/**
		 * Returns the value of the query string for a given key.
		 * */
		getQuery: function(key) {
			if (hash().split('?', 2).length !== 2) {
				return null;
			}
			var queryString = hash().split('?', 2)[1];
			var queryObject = ioQuery.queryToObject(queryString);
			return queryObject[key];
		},

		_removeMessage: function() {
			var msgNode = dom.byId('msg');
			if (msgNode) {
				put(msgNode, "!");
			}
		},

		/**
		 * Returns the needed backend information for the Password Service
		 * as a promise or as an object.
		 * The information is requested once and will be cached in
		 * this._backend_info.
		 * */
		getBackendInformation: function() {
			if (!this._backend_info) {
				var promise = request.get("/univention/self-service/entries.json");
				promise.then(lang.hitch(this, function(data){
					this._backend_info = data;
				}));
				return promise;
			} else {
				return this._backend_info;
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
