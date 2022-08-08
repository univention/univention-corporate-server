/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2020-2022 Univention GmbH
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
 * @module umc/widgets/NotificationsButton
 */
define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/Deferred",
	"dojo/dom-class",
	"dojo/dom-construct",
	"dojo/on",
	"dijit/popup",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"dijit/_WidgetsInTemplateMixin",
	"dijit/layout/ContentPane",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Button",
	"umc/widgets/ToggleButton",
	"umc/headerButtons",
	"umc/tools",
	"put-selector/put",
	"umc/i18n!"
], function(
	declare, lang, Deferred, domClass, domConstruct, on, popup, _WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin,
	ContentPane, ContainerWidget, Button, ToggleButton, headerButtons, tools, put, _
) {
	var Notification = declare("umc.widgets.NotificationsButton.Notification",
			[_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {
		templateString: `
			<div class="ucsNotification">
				<div class="ucsNotification__header">
					<div
						class="ucsNotification__title"
						data-dojo-attach-point="titleNode"
					></div>
					<button
						class="ucsNotification__closeButton ucsIconButton"
						data-dojo-attach-point="closeButton"
						data-dojo-type="umc/widgets/Button"
						data-dojo-props="iconClass: 'x'"
					></button>
				</div>
				<div
					class="ucsNotification__content"
					data-dojo-type="dijit/layout/ContentPane"
					data-dojo-attach-point="contentPane"
				></div>
			</div>
		`,

		title: '',
		_setTitleAttr: { node: 'titleNode', type: 'innerHTML' },

		content: '',
		_setContentAttr: function(content) {
			if (typeof content !== 'string' && content.$factory$) {
				const factory = content.$factory$;
				delete content.$factory$;
				content = new factory(content);
			}
			this.contentPane.set('content', content);
			this._set('content', content);
		},

		type: '',
		_setTypeAttr: function(type) {
			domClass.remove(this.domNode, `ucsNotification--${this.type}`);
			if (type) {
				domClass.add(this.domNode, `ucsNotification--${type}`);
			}
			this._set('type', type);
		},

		postCreate: function() {
			this.inherited(arguments);
			this.closeButton.on('click', () => {
				this.onClose();
			});
		},

		onClose: function() {
			// evt stub
		},
	});

	var NotificationsPreview = declare("umc.widgets.NotificationsButton.NotificationsPreview",
			[_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {
		templateString: `
			<div class="ucsNotificationPreview dijitDisplayNone">
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
				clearTimeout(this._drainTimeout);
				clearTimeout(this._fadeOutTimeout);
				domClass.remove(this.domNode, 'ucsNotificationPreview--draining');
				domClass.add(this.domNode, 'ucsNotificationPreview--open');
			});

			this._mouseleave = on.pausable(this.domNode, 'mouseleave', () => {
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
			if (this._currentNot) {
				this._currentNot.destroyRecursive();
			}
			if (!item) {
				this._processingQueue = false;
				tools.toggleVisibility(this, false);
				return;
			}
			const notification = new Notification(item);
			put(notification.closeButton.domNode, domConstruct.toDom('<svg class="ucsNotification__close-svg" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><circle class="ucsNotification__close-circle" cx="50" cy="50" r="45"></circle></svg>'));
			this._currentNot = notification;
			this.domNode.appendChild(notification.domNode);
			notification.startup();
			this._drainDuration = 4000;
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
				domClass.remove(this.domNode, 'ucsNotificationPreview--draining');

				window.requestAnimationFrame(() => {
					this.domNode.style.transitionDuration = `${this._fadeDuration}ms`;
					domClass.add(this.domNode, 'ucsNotificationPreview--open');
					domClass.add(this.domNode, 'ucsNotificationPreview--draining');
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
		},

		advance: function() {
			this._currentNot.onClose();
		}
	});

	var NotificationsContainer = declare("umc.widgets.NotificationsButton.NotificationsContainer",
			[_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {
		templateString: `
			<div class="ucsNotifications ucsNotifications--empty">
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
			this.updateCount();

			notification.on('close', () => {
				notification.destroyRecursive();
				this.updateCount();
			});
		},

		updateCount: function() {
			const count = this.container.getChildren().length;
			if (count === 0) {
				this.set('title', _('No notifications'));
			} else {
				this.set('title', _('Notifications'));
			}
			domClass.toggle(this.domNode, 'ucsNotifications--empty', count === 0);
			this.onCountChanged(count);
		},
		onCountChanged: function() {}
	});


	var notificationsButtonCreatedDeferred = new Deferred();
	var NotificationsButton = declare("umc.widgets.NotificationsButton", [ToggleButton], {
		showLabel: false,
		iconClass: 'bell',

		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'ucsIconButton ucsNotificationsButton');
			this.counterNode = put(this.domNode, 'div.umcHeaderButton__counter.umcHeaderButton__counter--hidden');
		},

		_setCheckedAttr: function(checked) {
			this.notificationsContainer.set('open', checked);
			this.inherited(arguments);
		},

		addNotification: function(item) {
			this.notificationsContainer.addNotification(lang.clone(item));
			this.notificationsPreview.addNotification(item);
		},

		addWarning: function(item) {
			item.type = 'warning';
			this.addNotification(item);
		},

		advance: function() {
			this.notificationsPreview.advance();
		},

		postCreate: function() {
			this.inherited(arguments);

			this.notificationsPreview = new NotificationsPreview({});
			document.body.appendChild(this.notificationsPreview.domNode);
			this.notificationsPreview.startup();

			this.notificationsContainer = new NotificationsContainer({});
			headerButtons.createOverlay(this.notificationsContainer.domNode);
			this.notificationsContainer.startup();
			headerButtons.subscribe(this, 'notifications', this.notificationsContainer);

			on(this.notificationsContainer, 'countChanged', lang.hitch(this, function(count) {
				domClass.toggle(this.counterNode, 'umcHeaderButton__counter--hidden', count === 0);
				this.counterNode.innerHTML = count;
			}));

			notificationsButtonCreatedDeferred.resolve(this);
		}
	});

	NotificationsButton.addNotification = function(item) {
		notificationsButtonCreatedDeferred.then(function(notificationsButton) {
			notificationsButton.addNotification(item);
		});
	};

	NotificationsButton.addWarning = function(item) {
		notificationsButtonCreatedDeferred.then(function(notificationsButton) {
			notificationsButton.addWarning(item);
		});
	};

	return NotificationsButton;
});
