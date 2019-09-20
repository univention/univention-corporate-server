/*
 * Copyright 2017-2019 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */
/*global define,Node,setTimeout*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/fx",
	"dojo/_base/window",
	"dojo/dom-class",
	"dojo/dom-geometry",
	"dojo/dom-style",
	"dojo/aspect",
	"dojo/on",
	"dojo/Deferred",
	"dojo/window",
	"dojo/fx",
	"dojo/fx/easing",
	"dojox/html/styles",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"dijit/_WidgetsInTemplateMixin",
	"dijit/_CssStateMixin",
	"dijit/form/DropDownButton",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Button",
	"put-selector/put",
	"umc/i18n!"
], function(declare, lang, array, baseFx, baseWindow, domClass, domGeometry, domStyle, aspect, on, Deferred, win, fx, fxEasing, styles, _WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin, _CssStateMixin, DropDownButton, ContainerWidget, Button, put, _) {
	var _Notification = declare('umc.widgets.NotificationDropDown.Notification', [_WidgetBase, _TemplatedMixin, _CssStateMixin], {
		// summary:
		// 		A single Notification inside the _NotificationDropDown widget

		templateString: '' +
			'<div class="umcDropDownNotification" data-dojo-attach-point="domNode">' +
				'<div class="umcNotificationInnerWrapper" data-dojo-attach-point="wrapperNode">' +
					'<div class="umcNotificationTitle" data-dojo-attach-point="titleNode"></div>' +
					'<div class="umcNotificationMessageContainer" data-dojo-attach-point="messageContainerNode">' +
						'<div class="umcNotificationMessage" data-dojo-attach-point="messageNode"></div>' +
						'<div class="umcNotificationMessageClone" data-dojo-attach-point="messageCloneNode"></div>' +
					'</div>' +
					'<div class="umcNotificationCloseContainer" data-dojo-attach-point="closeNode" data-dojo-attach-event="ondijitclick: _onCloseNodeClick" role="button">' +
						'<div class="umcNotificationCloseCircle"></div>' +
						'<div class="umcNotificationCloseCircleInk" data-dojo-attach-point="inkNode"></div>' +
						'<div class="umcNotificationCloseIcon"></div>' +
					'</div>' +
				'</div>' +
			'</div>',

		cssStateNodes: {
			closeNode: 'umcNotificationCloseContainer'
		},

		baseClass: 'umcDropDownNotification',

		// Only has one time effect when creating an instance
		truncate: true, // @postMixInProperties

		postMixInProperties: function() {
			this.inherited(arguments);
			this.title = this.title || _('Notification');
			this.message = this.message || _('No message');
			this.isWarning = (this.isWarning === undefined || this.isWarning === null) ? false : this.isWarning;
			this.truncate = (this.truncate === undefined || this.truncate === null) ? true : this.truncate;
		},

		buildRendering: function() {
			this.inherited(arguments);
			domClass.toggle(this.messageContainerNode, 'umcNotificationMessageContainer--truncated', this.truncate);
		},

		title: _('Notification'), // @postMixInProperties
		_setTitleAttr: { node: 'titleNode', type: 'innerHTML' },

		message: _('No message'), // @postMixInProperties
		_setMessageAttr: function(message) {
			this.messageNode.innerHTML = message;
			this.messageCloneNode.innerHTML = message;
			this._set('message', message);
		},

		// changing isWarning after the notification has been added
		// destroys the correct position for new notifications
		isWarning: false, // @postMixInProperties
		_setIsWarningAttr: function(isWarning) {
			domClass.toggle(this.domNode, 'umcDropDownNotificationWarning', isWarning);
			this._set('isWarning', isWarning);
		},

		_addMaxHeightCssStyles: function() {
			if (this._insertedCssStyle) {
				styles.removeCssRule(this._insertedCssStyle.selector, this._insertedCssStyle.declaration);
			}

			var fullMessageHeight = domGeometry.getContentBox(this.messageCloneNode).h;
			var selector = lang.replace('#{0}.{1}Hover .umcNotificationMessageContainer,#{0}.{1}Focused .umcNotificationMessageContainer', [this.id, this.baseClass]);
			var declaration = lang.replace('max-height: {0}px;', [fullMessageHeight]);
			styles.insertCssRule(selector, declaration);
			this._insertedCssStyle = {
				selector: selector,
				declaration: declaration
			};
		},

		_onCloseNodeClick: function(evt) {
			// ink effect is not visible due to fadeOut of Notification
			this._showInkEffect(evt);
			this.remove();
		},

		_showInkEffect: function(evt) {
			var closeNodePos = domGeometry.position(this.closeNode);
			var innerClickX = evt.clientX - closeNodePos.x;
			var innerClickY = evt.clientY - closeNodePos.y;
			var inkDiameter = Math.max(
				(closeNodePos.w - innerClickX),
				innerClickX,
				(closeNodePos.w - innerClickY),
				innerClickY
			) * 2;
			var inkRadius = inkDiameter / 2;
			var x = innerClickX - inkRadius;
			var y = innerClickY - inkRadius;
			domStyle.set(this.inkNode, {
				'transition': 'none',
				'opacity': '',
				'transform': '',
				'left': x + 'px',
				'top': y + 'px',
				'width': inkDiameter + 'px',
				'height': inkDiameter + 'px'
			});
			setTimeout(lang.hitch(this, function() {
				domStyle.set(this.inkNode, {
					'transition': '',
					'opacity': '0',
					'transform': 'scale(1)'
				});
			}), 10);
		},

		remove: function(evt) {
			this._keepFullMessageHeight = true;

			var fadeOut = baseFx.fadeOut({
				node: this.domNode,
				easing: fxEasing.quadInOut,
				duration: 150
			});
			var wipeOut = fx.wipeOut({
				node: this.domNode,
				easing: fxEasing.quadInOut,
				duration: 250
			});
			on(wipeOut, 'End', lang.hitch(this, 'onRemove', this));
			fx.combine([wipeOut, fadeOut]).play();
		},

		onRemove: function(notification) {
			// event stub
		}
	});

	var _NotificationDropDown = declare('umc.widgets.NotificationDropDown', [_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {
		// summary:
		// 		The dropDown for the NotificationDropDownButton widget.
		// 		Consists of a button to close all notification and a container
		// 		for the _Notification widgets.

		templateString: lang.replace('' +
			'<div class="umcNotificationDropDown" data-dojo-attach-point="domNode">' +
				'<div class="noNotificationsText">{noNotificationsText}</div>' +
				'<div class="removeAllNotificationsButton umcFlatButton" data-dojo-attach-point="removeAllNotificationsButton" data-dojo-type="umc/widgets/Button" data-dojo-attach-event="onClick: removeAllNotifications">{removeAllNotificationsButton}</div>' +
				'<div class="notificationsContainerWrapper" data-dojo-attach-point="notificationsContainerWrapperNode">' +
					'<div class="notificationsContainer" data-dojo-type="umc/widgets/ContainerWidget" data-dojo-attach-point="notificationsContainer"></div>' +
				'</div>' +
			'</div>', {
				'noNotificationsText': _('No messages'),
				'removeAllNotificationsButton': _('Close all')
			}),

		_firstNonWarningIndex: 0,

		addNotification: function(message, title, isWarning, truncate, playWipeInAnimation) {
			var notification = new _Notification({
				message: message,
				title: title,
				isWarning: isWarning,
				truncate: truncate
			});

			if (isWarning) {
				this._firstNonWarningIndex++;
			}
			var insertIndex = (isWarning) ? 0 : this._firstNonWarningIndex;
			this.notificationsContainer.addChild(notification, insertIndex);

			if (playWipeInAnimation) {
				domStyle.set(notification.domNode, 'height', '0');
				fx.wipeIn({
					node: notification.domNode,
					easing: fxEasing.linear,
					duration: 250
				}).play();
			}

			on.once(notification, 'remove', lang.hitch(this, function(notification) {
				if (notification.isWarning) {
					this._firstNonWarningIndex--;
				}
				this.destroyNotification(notification);
			}));

			return notification;
		},

		_truncateNotificationToTwoLines: function(notification) {
			var maxHeight = domGeometry.getContentBox(notification.messageContainerNode).h;
			var messageNode = notification.messageNode;
			if (domGeometry.getContentBox(messageNode).h > maxHeight) {
				var ellipsis = '...';

				// iterate over all text nodes of the message and remove one word at a time
				// until the message fits into two lines
				//
				// What are text nodes?
				// This node for example,
				// # var node = put('div $ a $ < $', 'Text before link', 'Link text', 'Text after link')
				// <div>
				// 		"Text before link"
				// 		<a href="">Link text</a>
				// 		"Text after link"
				// </div>
				//
				// has two text nodes and one element node,
				// # node.childNodes
				// -> [text, a, text]
				// and the 'a' node has one text node
				// # node.childNodes[1].childNodes
				// -> [text]
				//
				// We only want to change the textContent attribute of the text nodes
				// so that the links are kept intact.
				// Changing textContent of 'node' directly would break the link.
				var textNode = this._findLastTextNodeWithText(messageNode);
				while (textNode) {
					// remove one word at a time until the message fits into two lines
					// or the text of the current text node consists only of the ellipsis ('...')
					do {
						textNode.textContent = lang.replace('{0}{1}', [textNode.textContent.substring(0, textNode.textContent.lastIndexOf(' ')), ellipsis]);
					} while (textNode.textContent.length > ellipsis.length && domGeometry.getContentBox(messageNode).h > maxHeight);

					// if the message fits into two lines we are done
					if (domGeometry.getContentBox(messageNode).h <= maxHeight) {
						break;
					// else remove the ellipsis from the current text node and truncate the next text node
					} else {
						textNode.textContent = '';
						textNode = this._findLastTextNodeWithText(messageNode);
					}
				}
				notification._addMaxHeightCssStyles();
			}
		},

		_findLastTextNodeWithText: function(node) {
			for (var i = node.childNodes.length - 1; i >= 0; i--) {
				var lastNode = node.childNodes[i];
				if (lastNode.nodeType !== Node.TEXT_NODE) {
					var _node = this._findLastTextNodeWithText(lastNode);
					if (_node) {
						return _node;
					}
				} else if (lastNode.textContent) {
					return lastNode;
				}
			}
			return null;
		},

		destroyNotification: function(notification) {
			this.notificationsContainer.removeChild(notification);
			notification.destroyRecursive();

			this.onNotificationRemoved();
		},

		removeAllNotifications: function() {
			array.forEach(this.notificationsContainer.getChildren(), lang.hitch(this, function(notification) {
				notification.remove();
			}));
		},

		onNotificationRemoved: function() {
			// event stub
		},

		_scrollToFirstNotification: function() {
			if (this.notificationsContainerWrapperNode.scrollTop  === 0) {
				return;
			}

			new baseFx.Animation({
				duration: 250,
				easing: fxEasing.cubicOut,
				curve: [this.notificationsContainerWrapperNode.scrollTop, 0],
				onAnimate: function(val) {
					this.notificationsContainerWrapperNode.scrollTop = val;
				}
			}).play();
		}
	});

	var notificationDropDownButtonDeferred = new Deferred({});
	var NotificationDropDownButton = declare('umc.widgets.NotificationDropDownButton', DropDownButton, {
		// summary:
		// 		A DropDownButton that opens a _NotificationDropDown Widget.
		// 		There should only be one instance of this Widget.
		// description:
		// 		Use 'addNotification' for a normally styled notification.
		// 		Use 'addWarning' for a warning that is always on top of normal notifications.

		// maxHeight 0 for no native scrollbars
		// see dijit/_HasDropDown.js and the 'open' function from dijit/popup.js for more information
		maxHeight: 0,

		// _notificationCount: Integer
		// 		The count of the notifications in the _NotificationDropDown
		_notificationCount: 0,

		// _notificationCountNode: HTML span element
		// 		HTML element to show the amount of notifications.
		// 		Does not show when _notificationCount is 0.
		_notificationCountNode: null,

		// _lastWindowWidth: Integer
		// 		When opening the dropDown and the
		// 		window width changed, the message truncation for
		// 		all notifications is updated.
		_lastWindowWidth: null,

		// _lastOpenDropDownData: Object
		// 		The previous return value of this.openDropDown()
		_lastOpenDropDownData: null,

		_set_notificationCountAttr: function(count) {
			count = Math.min(count, 99);
			this._notificationCount = count;
			this._notificationCountNode.innerHTML = count;
			this._set('_notificationCount', count);
		},

		postMixInProperties: function() {
			this.dropDown = new _NotificationDropDown({});
			this.class += ' umcNotificationDropDownButton';
			this.inherited(arguments);
		},

		buildRendering: function() {
			this.inherited(arguments);
			this._notificationCountNode = put(this._buttonNode, 'span.notificationCountNode');
		},

		postCreate: function() {
			this.inherited(arguments);

			aspect.after(this, 'openDropDown', lang.hitch(this, function(dropDownData) {
				domClass.add(this.dropDown._popupWrapper, 'umcNotificationPopupWrapper');
				return dropDownData;
			}));

			this.dropDown.on('notificationRemoved', lang.hitch(this, '_updateNotificationCount', -1));

			notificationDropDownButtonDeferred.resolve(this);
		},

		addWarning: function(message, title, truncate) {
			return this._addNotification(message, title, true, truncate);
		},

		addNotification: function(message, title, truncate) {
			return this._addNotification(message, title, false, truncate);
		},

		_addNotification: function(message, title, isWarning, truncate) {
			this._updateNotificationCount(1);

			var notification = this.dropDown.addNotification(message, title, isWarning, truncate, this._opened);
			if (!this._opened) {
				var dropDownData = this.openDropDown();
				dropDownData.openDeferred.then(lang.hitch(this.dropDown, '_scrollToFirstNotification'));
			}
			this.dropDown._truncateNotificationToTwoLines(notification);
			return notification;
		},

		openDropDown: function() {
			domClass.replace(this.dropDown.domNode, 'openTransition', 'closeTransition');

			var dropDownData = this.inherited(arguments);
			dropDownData.openDeferred = new Deferred();

			var windowBox = win.getBox();

			// set max height so the drop down does not exceed the window size
			var dropDownMaxHeight = windowBox.h - (domGeometry.position(this.domNode).y + domGeometry.position(this.domNode).h) - 20;
			// domStyle.set(this.dropDown.domNode, 'max-height', maxHeight + 'px');
			var notificationWrapperMaxHeight = dropDownMaxHeight - domGeometry.getMarginExtents(this.dropDown.notificationsContainerWrapperNode).t;
			domStyle.set(this.dropDown.notificationsContainerWrapperNode, 'max-height', lang.replace('{0}px', [notificationWrapperMaxHeight]));

			// set 'right' instead of 'left' position when the right side
			// of the drop down aligns with the right side of the
			// drop down button so the width expands from the right
			// and not from the left. But only if the drop down fits
			// completely to the left.
			if (dropDownData.corner === 'TR' && !dropDownData.overflow) {
				domStyle.set(this.dropDown.domNode.parentElement, {
					'left': 'initial',
					'right': windowBox.w - (dropDownData.w + dropDownData.x) + 'px'
				});
			}

			if (windowBox.w !== this._lastWindowWidth) {
				this._lastWindowWidth = windowBox.w;
				array.forEach(this.dropDown.notificationsContainer.getChildren(), lang.hitch(this, function(notification) {
					notification.set('message', notification.messageCloneNode.innerHTML);
					this.dropDown._truncateNotificationToTwoLines(notification);
				}));
			}

			// We want a css transition to the height and with of the dropDown.
			// A css transition does not work from height/width auto
			// to a specific value (or the other way around)
			// so we explicitly set the height and width to 0
			// before setting height and width to the dimensions of the dropDown.
			domClass.add(this.dropDown.domNode, 'noTransition'); // no transition so opacity is instantly set
			domStyle.set(this.dropDown.domNode, {
				'width': dropDownData.overflow ? dropDownData.w + dropDownData.overflow + 'px' : '0',
				'height': '0',
				'opacity': '0'
			});
			domClass.remove(this.dropDown.domNode, 'noTransition');
			setTimeout(lang.hitch(this, function() {
				domStyle.set(this.dropDown.domNode, {
					'width': dropDownData.w + dropDownData.overflow + 'px',
					'height': dropDownData.h + 'px',
					'opacity': '1'
				});
			}), 0);

			// after the transition is done...
			setTimeout(lang.hitch(this, function() {
				// ...remove the set styles
				domStyle.set(this.dropDown.domNode, {
					'width': '',
					'height': '',
					'opacity': ''
				});

				// add a handler to close the dropDown on a click outside
				// of the dropDown if the dropDown was opened programmatically
				// (the dropDownButton was not clicked)
				if (!this.focused) {
					var closeHandler = on(baseWindow.doc, 'click', lang.hitch(this, function(evt) {
						var path = evt.path;
						if (!path) {
							path = [];
							currentElement = evt.target;
							while (currentElement) {
								path.push(currentElement);
								currentElement = currentElement.parentElement;
							}
						}

						var dropDownOrButtonCliked = array.some([this.domNode, this.dropDown.domNode], function(node) {
							return path.indexOf(node) !== -1;
						});

						if (dropDownOrButtonCliked) {
							closeHandler.remove();
						} else {
							this.closeDropDown();
							closeHandler.remove();
						}
					}));
				}

				dropDownData.openDeferred.resolve();
			}), 300);
			// 300ms linked to transition duration for opening and closing
			// .umcNotificationDropDown defined in header.styl

			this._lastOpenDropDownData = dropDownData;
			return dropDownData;
		},

		closeDropDown: function() {
			domClass.replace(this.dropDown.domNode, 'closeTransition', 'openTransition');
			domClass.toggle(this.dropDown.domNode, 'closeTransitionHeightOnly', this._lastOpenDropDownData.overflow);

			var closeDeferred = new Deferred();
			var origArgs = arguments;

			// We want a css transition to 0 height and with.
			// A css transition does not work from height/width auto
			// to a specific value so we explicitly set
			// the current height and width before setting
			// height and width to 0.
			var box = domGeometry.getContentBox(this.dropDown.domNode);
			domClass.add(this.dropDown.domNode, 'noTransition'); // no transition so opacity is instantly set
			domStyle.set(this.dropDown.domNode, {
				'width': box.w + 'px',
				'height': box.h + 'px',
				'opacity': '1'
			});
			domClass.remove(this.dropDown.domNode, 'noTransition');
			setTimeout(lang.hitch(this, function() {
				domStyle.set(this.dropDown.domNode, {
					'width': this._lastOpenDropDownData.overflow ? box.w + 'px' : '0',
					'height': '0',
					'opacity': '0'
				});
			}), 0);

			// after the transition is done...
			setTimeout(lang.hitch(this, function() {
				// ...remove the set styles
				domStyle.set(this.dropDown.domNode, {
					'width': '',
					'height': '',
					'opacity': ''
				});
				domClass.remove(this.dropDown.domNode, 'closeTransitionHeightOnly');

				this.inherited(origArgs);
				closeDeferred.resolve();
			}), 300);
			// 300ms linked to transition duration for opening and closing
			// .umcNotificationDropDown defined in header.styl

			return closeDeferred;
		},

		_updateNotificationCount: function(amount) {
			this.set('_notificationCount', this.get('_notificationCount') + amount);

			if (!this._notificationCount) {
				this.closeDropDown().then(lang.hitch(this, function() {
					this._updateNotificationCountCssClasses();
				}));
			} else {
				this._updateNotificationCountCssClasses();
			}
		},

		_updateNotificationCountCssClasses: function() {
			domClass.toggle(this.domNode, 'hasNotifications shake', this._notificationCount);
			domClass.toggle(this.dropDown.domNode, 'hasNotifications', this._notificationCount);

			domClass.remove(this.dropDown.domNode, 'hasMultipleNotifications hasSingleNotification');
			domClass.toggle(this.dropDown.domNode, (this._notificationCount > 1 ? 'hasMultipleNotifications' : 'hasSingleNotification'), this._notificationCount);
		}
	});

	NotificationDropDownButton.getInstance = function() {
		return notificationDropDownButtonDeferred;
	};

	return NotificationDropDownButton;
});
