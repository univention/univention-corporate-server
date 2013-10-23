/*
 * Copyright 2013 Univention GmbH
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
	"dojo/dom-construct",
	"dojo/dom-geometry",
	"dojo/store/Memory",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"umc/widgets/Button",
	"umc/widgets/Text",
	"umc/tools",
	"umc/i18n!umc/app"
], function(declare, lang, query, win, on, topic, fx, domStyle, domConstruct, domGeometry, Memory, _WidgetBase, _TemplatedMixin, Button, Text, tools, _) {
	var _getWrapper = function() {
		return query('.umcNotificationTopWrapper')[0];
	};

	var _NotificationBubble = declare([Text], {
		'class': 'umcNotificationBubble',

		postCreate: function() {
			this.inherited(arguments);
			this.placeAt(_getWrapper());
		},

		setNumOfNotifications: function(num) {
			this.set('content', '' + num);
			var displayValue = num > 0 ? 'block' : 'none';
			domStyle.set(this.domNode, 'display', displayValue);
		}
	});

	return declare([_WidgetBase, _TemplatedMixin], {
		// description:
		//		Combination of Widget and Container class.
		templateString: '' +
			'<div class="umcNotification" data-dojo-attach-point="domNode">' +
				'<div class="umcNotificationWrapper" data-dojo-attach-point="wrapperNode">' +
					'<div class="umcNotificationScroller" data-dojo-attach-point="scrollerNode"></div>' +
					'<div style="text-align: right;" data-dojo-attach-point="footerNode"></div>' +
				'</div>' +
			'</div>',

		query: {},

		queryOptions: {
			sort: [{
				attribute: 'time',
				descending: true
			}]
		},

		visible: false,

		// timeout: Number
		//		Timeout in seconds after which the notification is hidden again.
		timeout: 4,

		// view: String
		//		Can have the values 'all' (default) or 'new'.
		view: 'all',

		animation: null,

		store: null,

		_closeButton: null,
		_buttonContainer: null,
		_nNewNotifications: 0,
		_nextID: 1,
		_timeoutID: null,

		_setQueryAttr: function(value) {
			this.query = value;
			this.render();
			this._set('query', value);
		},

		_setViewAttr: function(value) {
			this.view = value;
			var newQuery = {};
			if (value == 'new') {
				newQuery = {
					seen: false
				};
			}
			this.set('query', newQuery);
			this._set('view', value);
		},

		_setVisibleAttr: function(value) {
			var cssVisibility = value ? 'block' : 'none';
			domStyle.set(this.domNode, 'display', cssVisibility);
			this._set('visible', value);
		},

		_stopActiveAnimation: function() {
			var anim = this.get('animation');
			if (anim) {
				anim.stop();
				this.set('animation', null);
			}
		},

		buildRendering: function() {
			this.inherited(arguments);

			this.store = new Memory();

			this._closeButton = new Button({
				label: _('Close'),
				iconClass: 'icon-umc-notifications-close',
				'class': 'umcNotificationCloseButton',
				callback: lang.hitch(this, 'confirm')
			});
			this._closeButton.placeAt(this.footerNode);

			this._notificationBubble = new _NotificationBubble({});
		},

		postCreate: function() {
			this.inherited(arguments);
			domConstruct.place(this.domNode, _getWrapper());

			on(this.domNode, 'mouseover,touch', lang.hitch(this, '_clearTimeout'));
			on(this.domNode, 'mouseout', lang.hitch(this, function(e) {
				if (this.get('view') != 'all') {
					this._addTimeout();
				}
			}));

			topic.subscribe('/umc/actions', lang.hitch(this, function(actionRootName) {
				if (actionRootName != 'startup-wizard') {
					this.wipeOut();
				}
			}));
		},

		startup: function() {
			this.inherited(arguments);
			if (this.store) {
				this.render();
			}
		},

		_resetAnimation: function() {
			this.set('animation', null);
		},

		_renderRow: function(item, options) {
			// create gallery item
			var cssClass = 'umcNotificationMessage';
			console.log('# _renderRow:', item.id, item.confirmed, this.get('view'));
			if (this.get('view') == 'all' && !item.confirmed) {
				cssClass += ' umcNewNotification';
			}
			var div = domConstruct.create('div', {
				'class': cssClass,
				innerHTML: item.message
			});

			var infoStr = lang.replace('{h}:{m}', {
				h: item.time.getHours(),
				m: item.time.getMinutes()
			});
			if (item.component) {
				infoStr = item.component + ' - ' + infoStr;
			}
			domConstruct.create('span', {
				'class': 'umcNotificationMessageInfo',
				innerHTML: lang.replace("[ {0} ]", [infoStr])
			}, div);

			return div;
		},

		render: function() {
			domConstruct.empty(this.scrollerNode);
			this.store.query(this.query, this.queryOptions).forEach(lang.hitch(this, function(iitem) {
				var node = this._renderRow(iitem);
				domConstruct.place(node, this.scrollerNode);
			}));
		},

		_updateMaxHeight: function() {
			var viewportHeight = win.getBox().h;
			domStyle.set(this.scrollerNode, 'max-height', viewportHeight / 2);
		},

		_getNeededHeight: function() {
			this._updateMaxHeight();
			var height = domGeometry.getMarginSize(this.wrapperNode).h;
			return height;
		},

		_getCurrentHeight: function() {
			return domGeometry.getMarginSize(this.domNode).h;
		},

		_updateBubble: function() {
			var nMessages = 0;
			if (tools.status('setupGui')) {
				nMessages = this.store.query({
					confirmed: false
				}).length;
			}
			this._notificationBubble.setNumOfNotifications(nMessages);
		},

		addMessage: function(message, component, autoClose) {
			this.store.add({
				id: this._nextID,
				message: message,
				component: component,
				time: new Date(),
				seen: false,
				confirmed: false,
				autoClose: Boolean(autoClose)
			});
			++this._nextID;
			this.render();
			this.wipeIn();

			++this._nNewNotifications;
			this._updateBubble();
		},

		_clearTimeout: function() {
			console.log('# _clearTimeout: ', this._timeoutID);
			if (this._timeoutID) {
				clearTimeout(this._timeoutID);
				this._timeoutID = null;
			}
		},

		_addTimeout: function() {
			this._clearTimeout();
			this._timeoutID = setTimeout(lang.hitch(this, function() {
				console.log('# timeout done -> close');
				this._timeoutID = null;
				this.wipeOut();
			}), this.timeout * 1000);
			console.log('# _addTimeout');
		},

		_addTimeoutIfOnlyAutoCloseMessages: function() {
			var nManualCloseMessages = this.store.query({
				seen: false,
				autoClose: false
			}).length;
			if (!nManualCloseMessages) {
				this._addTimeout();
			}
		},

		wipeIn: function(viewAll) {
			console.log('# wipeIn');
			this._stopActiveAnimation();
			this._clearTimeout();

			var viewMode = viewAll ? 'all' : 'new';
			this.set('view', viewMode);

			this.set('visible', true);

			var anim = fx.animateProperty({
				node: this.domNode,
				properties: {
					height: {
						start: this._getCurrentHeight(),
						end: this._getNeededHeight()
					}
				}
			});
			this.set('animation', anim);

			on(anim, 'End', lang.hitch(this, '_resetAnimation'));

			this._addTimeoutIfOnlyAutoCloseMessages();

			anim.play();
		},

		wipeOut: function() {
			console.log('# wipeOut');
			this._stopActiveAnimation();
			this._clearTimeout();
			var anim = fx.animateProperty({
				node: this.domNode,
				properties: {
					height: 0
				}
			});

			on(anim, 'End', lang.hitch(this, function() {
				this.set('visible', false);
				this._markMessagesAsSeen();
			}));
			on(anim, 'End', lang.hitch(this, '_resetAnimation'));

			anim.play();
		},

		_markMessages: function(property, currentValue, newValue) {
			console.log('# _markMessages: ', property, ' ', currentValue, ' ', newValue);
			var query = {};
			query[property] = currentValue;
			var newProperty = {};
			newProperty[property] = newValue;

			this.store.query(query).forEach(lang.hitch(this, function(imessage) {
				var newMessage = lang.mixin(imessage, newProperty);
				this.store.put(newMessage);
			}));
		},

		_markMessagesAsConfirmed: function() {
			this._markMessagesAsSeen();
			this._markMessages('confirmed', false, true);
		},

		_markMessagesAsSeen: function() {
			this._markMessages('seen', false, true);
		},

		confirm: function() {
			this.wipeOut();
			this._markMessagesAsConfirmed();
			this._updateBubble();
		}
	});

});

