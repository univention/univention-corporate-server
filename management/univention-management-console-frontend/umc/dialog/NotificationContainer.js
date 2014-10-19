/*
 * Copyright 2013-2014 Univention GmbH
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
/*global define console window setTimeout clearTimeout */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/query",
	"dojo/window",
	"dojo/on",
	"dojo/topic",
	"dojo/_base/fx",
	"dojo/dom-style",
	"dojo/dom-class",
	"dojo/dom-construct",
	"dojo/dom-geometry",
	"dojo/store/Memory",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"dojox/string/sprintf",
	"umc/widgets/ContainerWidget",
	"umc/tools",
	"umc/i18n!"
], function(declare, lang, query, win, on, topic, fx, domStyle, domClass, domConstruct, domGeometry, Memory, _WidgetBase, _TemplatedMixin, sprintf, ContainerWidget, tools, _) {
	var _Notification = declare([_WidgetBase, _TemplatedMixin], {
		templateString: '' +
			'<div class="umcNotification" data-dojo-attach-point="domNode">' +
				'<div class="umcNotificationTitle" data-dojo-attach-point="titleNode">${title}</div>' +
				'<div class="umcNotificationMessage" data-dojo-attach-point="messageNode"></div>' +
				'<div class="umcNotificationCloseIcon" data-dojo-attach-point="closeNode"></div>' +
			'</div>',
		title: _('Notification'),
		message: _('No message'),

		_setMessageAttr: function(value) {
			this.messageNode.innerHTML = value;
			this._set('message', value);
		}
	});

	return declare(ContainerWidget, {
		'class': 'umcNotificationContainer',

		query: {},

		_nextID: 0,

		queryOptions: {
			sort: [{
				attribute: 'time',
				descending: true
			}]
		},

		_wipedInTimestamp: 0,

		// timeout: Number
		//		Timeout in seconds after which the notification is hidden again.
		timeout: 4,

		store: null,

		_setQueryAttr: function(value) {
			this.query = value;
			this._set('query', value);
		},

		buildRendering: function() {
			this.inherited(arguments);
			this.store = new Memory();
		},


		startup: function() {
			this.inherited(arguments);
		},

		addMessage: function(message, component, autoClose) {
			var messageObj = this.store.add({
				id: this._nextID,
				message: message,
				component: component,
				time: new Date(),
				seen: false,
				confirmed: false,
				autoClose: Boolean(autoClose)
			});
			++this._nextID;

			var notification = new _Notification({
				title: component || _('Notification'),
				message: message
			});
			this.addChild(notification);

			notification.on('click', lang.hitch(this, function() {
				this.removeChild(notification);
			}));

			// hide notification automatically after timeout
			if (autoClose) {
				tools.defer(lang.hitch(this, function() {
					domClass.add(notification.domNode, 'umcNotificationHidden');
				}), this.timeout * 1000);
			}
		}
	});
});

