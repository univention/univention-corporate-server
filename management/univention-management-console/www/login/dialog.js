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
/*global define,dojo,getQuery,require*/

define([
	"login",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/query",
	"dojo/dom",
	"dojo/dom-construct",
	"dojo/dom-attr",
	"dojo/has",
	"dojox/html/entities",
	"umc/json!/univention/meta.json",
	"umc/i18n!login,umc/app"
], function(login, lang, array, query, dom, domConstruct, domAttr, has, entities, meta, _) {

	return {
		renderLoginDialog: function() {
			this.addLinks();
			this.translateDOM();
			login.renderLoginDialog();
		},

		addLinks: function() {
			array.forEach(this.getLinks(), function(link) {
				domConstruct.place(domConstruct.toDom(link), dom.byId('umcLoginLinks'));
			});
		},

		getLinks: function() {
			// FIXME: show password forgot link only if self-service is installed?!
			var links = [
				'<a href="javascript:void(0);" onclick="require(\'login/dialog\')._showLoginTooltip(event);" data-i18n="Wie melde ich mich an?"></a>',
				'<a target="_blank" href="/univention/self-service/" data-i18n="Password vergessen?"></a>'
			];

			// Show warning if connection is unsecured
			if (window.location.protocol === 'http:' && window.location.host !== 'localhost') {
				links.push(lang.replace('<a style="color: red;" href="https://{url}" title="{tooltip}">{text}</a>', {
					url: entities.encode(window.location.href.slice(7)),
					tooltip: entities.encode(_('This network connection is not encrypted. All personal or sensitive data will be transmitted in plain text. Please follow this link to use a secure SSL connection.')),
					text: entities.encode(_('Encrypted connection'))
				}));
			}
			return links;
		},

		translateDOM: function() {
			query('*[data-i18n]').forEach(function(inode) {
				var value = domAttr.get(inode, 'data-i18n');
				var translation = _(value, meta.ucr);
				domAttr.set(inode, 'innerHTML', translation);
			
			});
		},

		_fillUsernameField: function(username) {
			dom.byId('umcLoginUsername').value = username;
			dom.byId('umcLoginPassword').focus();

			//fire change event manually for internet explorer
			if (has('ie') < 10) {
				var event = document.createEvent("HTMLEvents");
				event.initEvent("change", true, false);
				dom.byId('umcLoginUsername').dispatchEvent(event);
			}
		},

		_showLoginTooltip: function(evt) {
			require(["dojo/on", "dojo/_base/event", "dijit/Tooltip",  "umc/i18n!umc/app"], function(on, dojoEvent, Tooltip, _) {
				var node = evt.target;
				var helpText = _('Please login with a valid username and password.') + ' ';
				if (getQuery('username') === 'root') {
					helpText += _('Use the %s user for the initial system configuration.', '<b><a href="javascript:void();" onclick="_fillUsernameField(\'root\')">root</a></b>');
				} else {
					helpText += _('The default username to manage the domain is %s.', '<b><a href="javascript:void();" onclick="_fillUsernameField(\'Administrator\')">Administrator</a></b>');
				}
				Tooltip.show(helpText, node);
				if (evt) {
					dojoEvent.stop(evt);
				}
				on.once(dojo.body(), 'click', function(evt) {
					Tooltip.hide(node);
					dojoEvent.stop(evt);
				});
			});
		}
	};
});
