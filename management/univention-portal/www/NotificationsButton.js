/*
 * Copyright 2020 Univention GmbH
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
/*global define*/

/**
 * @module portal/NotificationsButton
 */
define([
	"dojo/_base/declare",
	"dojo/dom-class",
	"dojo/on",
	"dijit/popup",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"dijit/_WidgetsInTemplateMixin",
	"dijit/form/Button",
	"dijit/form/ToggleButton",
	"umc/widgets/ContainerWidget",
	"umc/tools",
	"./portalContent",
	"umc/i18n!portal",
], function(
	declare, domClass, on, popup, _WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin, Button, ToggleButton,
	ContainerWidget, tools, portalContent, _
) {
	var Notification = declare("Notification", [_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {
		templateString: `
			<div class="ucsNotification">
				<div class="ucsNotification__header">
					<div
						class="ucsNotification__logoWrapper"
						data-dojo-attach-point="logoWrapperNode"
					>
						<img
							class="dijitDisplayNone"
							data-dojo-attach-point="logoNode"
						>
					</div>
					<div
						class="ucsNotification__title"
						data-dojo-attach-point="titleNode"
					></div>
					<button
						class="ucsNotification__closeButton ucsIconButton ucsIconButton--small"
						data-dojo-attach-point="closeButton"
						data-dojo-type="dijit/form/Button"
						data-dojo-props="iconClass: 'iconX'"
					></button>
				</div>
				<div
					class="ucsNotification__text"
					data-dojo-attach-point="textNode"
				></div>
			</div>
		`,

		logoUrl: '',
		_setLogoUrlAttr: function(logoUrl) {
			this.logoNode.src = logoUrl;
			tools.toggleVisibility(this.logoWrapperNode, !!logoUrl);
			this._set('logoUrl', logoUrl);
		},
		
		title: '',
		_setTitleAttr: { node: 'titleNode', type: 'innerHTML' },

		text: '',
		_setTextAttr: { node: 'textNode', type: 'innerHTML' },

		postCreate: function() {
			this.inherited(arguments);
			this.closeButton.on('click', () => {
				this.onClose();
			});
		},

		onClose: function() {
			// evt stub
		},

		startup: function() {
			this.inherited(arguments);
			console.log('startup of notification');
		}
	});

	var NotificationsPreview = declare("NotificationsPreview", [_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {
		templateString: `
			<div class="ucsNotificationPreview dijitDisplayNone">
				<div class="ucsNotificationPreview__triangle"></div>
				<div class="ucsNotificationPreview__background ucsNotificationPreview__background--drained">
					<div
						class="ucsNotificationPreview__background ucsNotificationPreview__background--full"
						data-dojo-attach-point="drainNode"
					></div>
				</div>
			</div>
		`,

		_queue: null,

		_fadeDuration: 150,

		constructor: function() {
			this._queue = [];
		},

		postCreate: function() {
			this.inherited(arguments);

			this._mouseenter = on.pausable(this.domNode, 'mouseenter', () => {
				console.log('mouseenter');
				clearTimeout(this._drainTimeout);
				clearTimeout(this._fadeOutTimeout);
				this.drainNode.style.transitionDuration = '';
				domClass.remove(this.drainNode, 'drained');
				this.domNode.style.transitionDuration = '';
				domClass.add(this.domNode, 'ucsNotificationPreview--open');
			});

			this._mouseleave = on.pausable(this.domNode, 'mouseleave', () => {
				console.log('mouseleave');
				this._show();
			});
		},

		_processingQueue: false,
		_processQueue: function() {
			if (this._processingQueue) {
				return;
			}
			this._processingQueue = true;
			window.requestAnimationFrame(() => {
				tools.toggleVisibility(this, true);
				this._showNextNotification();
			});
		},

		_currentNot: null,
		_showNextNotification: function() {
			const item = this._queue.shift();
			if (!item) {
				this._processingQueue = false;
				tools.toggleVisibility(this, false);
				return;
			}
			if (this._currentNot) {
				this._currentNot.destroyRecursive();
			}
			const notification = new Notification(item);
			this._currentNot = notification;
			this.domNode.appendChild(notification.domNode);
			notification.startup();
			this._drainDuration = 4000; // TODO
			this._show();

			// TODO this.own ?
			notification.on('close', () => {
				this._mouseenter.pause();
				this._mouseleave.pause();
				this.domNode.style.transitionDuration = `${this._fadeDuration}ms`;
				domClass.remove(this.domNode, 'ucsNotificationPreview--open');
				setTimeout(() => {
					this._showNextNotification();
					this._mouseenter.resume();
					this._mouseleave.resume();
				}, this._fadeDuration);
			});
		},

		_show: function() {
			window.requestAnimationFrame(() => {
				tools.toggleVisibility(this, true);
				this.drainNode.style.transitionDuration = '';
				domClass.remove(this.drainNode, 'drained');
				window.requestAnimationFrame(() => {
					this.domNode.style.transitionDuration = `${this._fadeDuration}ms`;
					this.drainNode.style.transitionDuration = `${this._drainDuration}ms`;
					domClass.add(this.domNode, 'ucsNotificationPreview--open');
					console.log('add dained');
					domClass.add(this.drainNode, 'drained');
				});
			});

			this._fadeOutTimeout = null;
			this._drainTimeout = setTimeout(() => {
				domClass.remove(this.domNode, 'ucsNotificationPreview--open');
				this._fadeOutTimeout = setTimeout(() => {
					this._showNextNotification();
				}, this._fadeDuration);
			}, this._drainDuration);
		},

		addNotification: function(item) {
			this._queue.push(item);
			this._processQueue();
		}
	});

	var NotificationsContainer = declare("NotificationsContainer", [_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {
		templateString: `
			<div class="ucsNotifications">
				<div
					class="ucsNotifications__title"
					data-dojo-attach-point="titleNode"
				></div>
				<div
					class="ucsNotifications__container"
					data-dojo-type="umc/widgets/ContainerWidget"
					data-dojo-attach-point="container"
				></div>
			</div>
		`,

		title: _('Notifications'),
		_setTitleAttr: { node: 'titleNode', type: 'innerHTML' },

		open: false,
		_setOpenAttr: function(open) {
			domClass.toggle(this.domNode, 'ucsNotifications--open', open);
			this._set('open', open);
		},

		addNotification: function(item) {
			const notification = new Notification(item);
			this.container.addChild(notification);

			notification.on('close', () => {
				notification.destroyRecursive();
			});
		}
	});


	return declare("NotificationsButton", [ToggleButton], {
		showLabel: false,
		iconClass: 'iconBell',

		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'ucsIconButton');
		},

		_setCheckedAttr: function(checked) {
			this.notificationsContainer.set('open', checked);
			this.inherited(arguments);
		},

		addNotification: function(item) {
			this.notificationsContainer.addNotification(item);
			this.notificationsPreview.addNotification(item);
		},

		postCreate: function() {
			this.inherited(arguments);

			this.notificationsPreview = new NotificationsPreview({});
			document.body.appendChild(this.notificationsPreview.domNode);
			this.notificationsPreview.startup();

			this.notificationsContainer = new NotificationsContainer({});
			document.body.appendChild(this.notificationsContainer.domNode);
			this.notificationsContainer.startup();
		}
	});
});



