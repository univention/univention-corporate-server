/*
 * Copyright 2013-2015 Univention GmbH
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
/*global define console */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/has",
	"dojo/Deferred",
	"dojo/dom-style",
	"dojo/dom-class",
	"dojo/dom-geometry",
	"dojo/mouse",
	"dojo/store/Memory",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"umc/widgets/ContainerWidget",
	"umc/tools",
	"umc/i18n!"
], function(declare, lang, has, Deferred, domStyle, domClass, domGeometry, mouse, Memory, _WidgetBase, _TemplatedMixin, ContainerWidget, tools, _) {
	var _Notification = declare([_WidgetBase, _TemplatedMixin], {
		templateString: '' +
			'<div class="umcNotification umcNotificationTransparent" data-dojo-attach-point="domNode">' +
				'<div class="umcNotificationTitle" data-dojo-attach-point="titleNode">${title}</div>' +
				'<div class="umcNotificationMessage" data-dojo-attach-point="messageNode"></div>' +
				'<div class="umcNotificationCloseIcon" data-dojo-attach-point="closeNode" data-dojo-attach-event="ondijitclick: remove" role="button"></div>' +
			'</div>',
		title: _('Notification'),
		message: _('No message'),
		autoClose: true,
		_hideDeferred: null,
		_lastShowed: 0,

		_setMessageAttr: function(value) {
			this.messageNode.innerHTML = value;
			this._set('message', value);
		},

		postMixInProperties: function() {
			this.inherited(arguments);
			this._lastShowed = new Date();
		},

		postCreate: function() {
			this.inherited(arguments);

			this._hideDeferred = new Deferred();
			this._hideDeferred.resolve();

			this.on('click', lang.hitch(this, function() {
				if (this.isHidden()) {
					this.show();
					if (has('touch')) {
						this._hideAfterTimeout();
					}
				}
				if (has('touch')) {
					this.remove();
				}
			}));

			if(has('touch')) {
				domClass.add(this.closeNode, 'dijitHidden');
			}

			if (!has('touch')) {
				this.on(mouse.enter, lang.hitch(this, 'show'));
				this.on(mouse.leave, lang.hitch(this, '_hideAfterTimeout'));
			}

			// hide notification automatically after timeout
			if (this.autoClose) {
				this._hideAfterTimeout();
			}
		},

		isHidden: function() {
			return domClass.contains(this.domNode, 'umcNotificationHidden');
		},

		_hideAfterTimeout: function() {
			if (!this._hideDeferred.isFulfilled()) {
				// cancel running deferred task
				this._hideDeferred.cancel();
			}
			this._hideDeferred = tools.defer(lang.hitch(this, 'hide'), this.timeout * 1000);
			this._hideDeferred.otherwise(function() { /* prevent logging of exception */ });
		},

		show: function() {
			if (this.isHidden()) {
				this._lastShowed = new Date();
				domClass.remove(this.domNode, 'umcNotificationHidden');
			}
		},

		hide: function() {
			domClass.add(this.domNode, 'umcNotificationHidden');
		},

		remove: function() {
			// only allow a removal after the notification has been visible
			// for a minimum amount of time
			var showedTime = new Date() - this._lastShowed;
			if (showedTime < 500) {
				return;
			}
			domClass.add(this.domNode, 'umcNotificationRemove');
			tools.defer(lang.hitch(this, 'onRemove'), 1000); // remove after CSS animation
		},

		startup: function() {
			this.inherited(arguments);

			// set the max-height property to allow to animate the height nicely
			var heightMessage = domGeometry.position(this.messageNode).h;
			domStyle.set(this.messageNode, 'maxHeight', heightMessage + 'px');
			var heightTotal = domGeometry.position(this.domNode).h;
			domStyle.set(this.domNode, 'maxHeight', heightTotal + 'px');

			// fade in notification
			domClass.remove(this.domNode, 'umcNotificationTransparent');
		},

		onRemove: function() {
			// event stub
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
			this.store.add({
				id: this._nextID,
				message: message,
				component: component,
				time: new Date(),
				autoClose: Boolean(autoClose)
			});
			++this._nextID;

			var notification = new _Notification({
				title: component || _('Notification'),
				message: message,
				autoClose: autoClose,
				timeout: this.timeout
			});
			this.addChild(notification);

			notification.on('Remove', lang.hitch(this, 'removeChild', notification));
		}
	});
});

