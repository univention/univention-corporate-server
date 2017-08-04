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
/*global define setTimeout */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/fx",
	"dojo/dom-class",
	"dojo/dom-geometry",
	"dojo/dom-style",
	"dojo/on",
	"dojo/Deferred",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"umc/i18n!"
], function(declare, lang, baseFx, domClass, domGeometry, domStyle, on, Deferred, _WidgetBase, _TemplatedMixin, _) {
	var notificationSnackbarDeferred = new Deferred({});
	var NotificationSnackbar = declare('umc.widgets.NotificationSnackbar', [_WidgetBase, _TemplatedMixin], {
		templateString: '' +
			'<div class="umcNotificationSnackbar" data-dojo-attach-point="domNode">' +
				'<div class="umcSnackbarNotification dijitOffScreen" data-dojo-attach-point="notificationNode">' +
					'<div class="umcNotificationFlexContainer">' +
						'<span class="umcNotificationMessage" data-dojo-attach-point="messageNode"></span>' +
						'<button type="button" class="umcNotificationActionButton dijitDisplayNone" data-dojo-attach-point="actionButtonNode" data-dojo-attach-event="onclick: onNotificationActionClick"></button>' +
					'</div>' +
				'</div>' +
			'</div>',

		// notificationMessage: innerHTML
		// 		The message that is shown in the notification.
		notificationMessage: null,
		_setNotificationMessageAttr: { node: 'messageNode', type: 'innerHTML' },

		// notificationAction: function
		// 		A notification can have a single action
		// 		that is performed when the action button is pressed.
		notificationAction: null,

		// notificationActionLabel: String
		// 		The label for the action button.
		notificationActionLabel: null,
		_setNotificationActionLabelAttr: { node: 'actionButtonNode', type: 'innerHTML' },

		// _queue: Object[{ message: innerHTML, action: function, actionLabel: String, isWarning: boolean }]
		// 		Array containing all the messages that need to be shown.
		// 		The first item is the currently shown notification.
		_queue: null,

		// _oneLineHeight: Integer
		// 		The height of a notification where the message fits on one line.
		// 		When setting a message and the height of the notification is higher than
		// 		this value, special css classes are set.
		_oneLineHeight: null,

		// _notificationHeight: Integer
		// 		The current height of the notification.
		_notificationHeight: null,

		// _maxVisibleTimeReached: Integer (in ms)
		// 		The maximum amount of time (in ms) a notification
		// 		stays on screen.
		_maxVisibleTime: 4000,

		// _maxVisibleTimeTimeout: return value of Window.setTimeout
		// 		A timeout with the delay of this._maxVisibleTime.
		// 		If it reaches zero it resolves _maxVisibleTimeReached.
		_maxVisibleTimeTimeout: null,

		// _maxVisibleTimeReached: Deferred
		// 		Gets resolved after this._maxVisibleTime milliseconds.
		// 		When this deferred is resolved it wipes out the current notification
		// 		and plays the next one in the _queue, if there is one.
		_maxVisibleTimeReached: null,

		// _minVisibleTime: Integer (in ms)
		// 		The minimum amount of time (in ms) a notification
		// 		stays on screen.
		_minVisibleTime: 1000,

		// _maxVisibleTimeReached: Deferred
		// 		Gets resolved after this._minVisibleTime milliseconds.
		// 		When resolved and there are new notifications waiting in the _queue,
		// 		_maxVisibleTimeReached gets resolved early to speed up the _queue.
		// 		Also, used for a check when a new notification is added and the current
		// 		notification is between _minVisibleTime and _maxVisibleTime, _maxVisibleTimeReached
		// 		gets resolved early.
		_minVisibleTimeReached: null,

		// _wipeIn: dojo/_base/fx.animateProperty
		// 		Dojo fx animation for wiping in the notification.
		_wipeIn: null,

		// _wipeOut: dojo/_base/fx.animateProperty
		// 		Dojo fx animation for wiping out the notification.
		_wipeOut: null,

		postMixInProperties: function() {
			this.inherited(arguments);
			this._queue = [];
		},

		postCreate: function() {
			this.inherited(arguments);
			notificationSnackbarDeferred.resolve(this);

			this._createAnimations();
			// initial set of deferreds for first wipeIn
			this._refreshMinVisibleTimeReached();
			this._refreshMaxVisibleTimeReached();
		},

		_createAnimations: function() {
			this._wipeIn = baseFx.animateProperty({
				node: this.notificationNode,
				properties: {
					'bottom': '0'
				},
				duration: 250
			});

			this._wipeOut = baseFx.animateProperty({
				node: this.notificationNode,
				properties: {
					'bottom': lang.hitch(this, function() {
						return -this._notificationHeight;
					})
				},
				duration: 250
			});

			this.own(on(this._wipeIn, 'End', lang.hitch(this, function() {
				setTimeout(lang.hitch(this, function() {
					this._minVisibleTimeReached.resolve();
				}), this._minVisibleTime);

				if (!this.isWarningShown) {
					this._maxVisibleTimeTimeout = setTimeout(lang.hitch(this, function() {
						this._maxVisibleTimeReached.resolve();
					}), this._maxVisibleTime);
				}
			})));

			this.own(on(this._wipeOut, 'End', lang.hitch(this, function() {
				this._refreshMinVisibleTimeReached();
				this._refreshMaxVisibleTimeReached();
				this.isWarningShown = false;

				this._queue.shift(); // remove first (current) notification from _queue
				if (this._queue.length) {
					this.wipeIn(this._queue[0]);
				}
			})));
		},

		_refreshMinVisibleTimeReached: function() {
			this._minVisibleTimeReached = new Deferred();
			this._minVisibleTimeReached.then(lang.hitch(this, function() {
				if (this._queue.length > 1) {
					this._maxVisibleTimeReached.resolve();
				}
			}));
		},

		_refreshMaxVisibleTimeReached: function() {
			this._maxVisibleTimeReached = new Deferred();
			this._maxVisibleTimeReached.then(lang.hitch(this, function() {
				// We clear the _maxVisibleTimeTimeout in case _maxVisibleTimeReached did not
				// get resolved by the _maxVisibleTimeTimeout itself but by other means.
				// If we do not clear it and _maxVisibleTimeTimeout did not finish
				// the wipe out timing of the next notifications is wrong.
				clearTimeout(this._maxVisibleTimeTimeout);
				this._wipeOut.play();
			}));
		},

		warn: function(message, action, actionLabel) {
			this._notify(message, action, actionLabel, true);
		},

		notify: function(message, action, actionLabel) {
			this._notify(message, action, actionLabel, false);
		},

		_notify: function(message, action, actionLabel, isWarning) {
			this._queue.push({
				message: message,
				action: action,
				actionLabel: actionLabel,
				isWarning: isWarning || false
			});

			if (this._minVisibleTimeReached.isResolved()) {
				this._maxVisibleTimeReached.resolve();
			}

			// If this is the first notification in the queue (or rather the queue was
			// empty before) then show this notification.
			// Showing notifications added to the queue while the queue is not empty
			// is handled by this._minVisibleTimeReached and this._maxVisibleTimeReached
			if (this._queue.length === 1) {
				this.wipeIn(this._queue[0]);
			}
		},

		wipeIn: function(notification) {
			this._prepareNotification(notification);
			this._wipeIn.play();
		},

		_prepareNotification: function(notification) {
			if (!this._oneLineHeight) {
				this._oneLineHeight = domGeometry.getMarginBox(this.notificationNode).h;
			}

			// hide notification offscreen (new message text could make notification higher
			// then before and the set 'bottom' style would not be enough)
			domClass.add(this.notificationNode, 'dijitOffScreen');
			// remove bottom style to get correct dimension from getMarginBox
			// since dijitOffScreen sets 'top'
			domStyle.set(this.notificationNode, 'bottom', '');

			// reset to default styling
			domClass.remove(this.notificationNode, 'multiLineWithActionButton');

			// set notification data
			this.set('isWarningShown', notification.isWarning);
			this.set('notificationMessage', notification.message);
			this.set('notificationAction', notification.action);
			this.set('notificationActionLabel', (this.isWarningShown && !notification.action) ? _('OK') : notification.actionLabel);

			// set warning css class
			domClass.toggle(this.notificationNode, 'umcSnackbarNotificationWarning', this.isWarningShown);

			// show or hide action button
			var showActionButton = this.isWarningShown || !!this.notificationAction;
			domClass.toggle(this.actionButtonNode, 'dijitDisplayNone', !showActionButton);

			// set styling class for notification with action button if higher than one line
			this._notificationHeight = domGeometry.getMarginBox(this.notificationNode).h;
			if (showActionButton && this._notificationHeight > this._oneLineHeight) {
				domClass.add(this.notificationNode, 'multiLineWithActionButton');
				this._notificationHeight = domGeometry.getMarginBox(this.notificationNode).h;
			}

			// put notification just under bottom of screen
			domStyle.set(this.notificationNode, 'bottom', -this._notificationHeight + 'px');
			domClass.remove(this.notificationNode, 'dijitOffScreen');
		},

		onNotificationActionClick: function() {
			if (this.notificationAction) {
				this.notificationAction();
			}

			this._maxVisibleTimeReached.resolve();
		}
	});

	NotificationSnackbar.getInstance = function() {
		return notificationSnackbarDeferred;
	};

	return NotificationSnackbar;
});
