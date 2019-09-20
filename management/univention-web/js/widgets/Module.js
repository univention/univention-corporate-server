/*
 * Copyright 2011-2019 Univention GmbH
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
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/topic",
	"dojo/aspect",
	"dojo/dom-class",
	"dojo/dom-geometry",
	"dojo/window",
	"dojo/on",
	"dijit/layout/StackContainer",
	"dojox/html/entities",
	"umc/render",
	"umc/widgets/_ModuleMixin",
	"umc/widgets/ContainerWidget",
	"umc/widgets/ModuleHeader",
	"umc/widgets/StandbyMixin",
	"umc/i18n!"
], function(declare, lang, array, topic, aspect, domClass, domGeom, win, on, StackContainer, entities, render, _ModuleMixin, ContainerWidget, ModuleHeader, StandbyMixin, _) {
	return declare("umc.widgets.Module", [ContainerWidget, _ModuleMixin, StandbyMixin], {
		// summary:
		//		Basis class for module classes.

		_top: null,
		_bottom: null,
		__container: null,

		// initial title set for the module
		defaultTitle: null,

		selectablePagesToLayoutMapping: null,

		postMixInProperties: function() {
			this.inherited(arguments);
			this.defaultTitle = this.title;

			this.__container = new declare([StackContainer, StandbyMixin])({
				baseClass: StackContainer.prototype.baseClass + ' umcModuleContent',
				doLayout: false
			});
			this.__container.watch('selectedChildWidget', lang.hitch(this, function(name, oldV, newV) {
				this.set(name, newV);
			}));

			this.__container.watch('selectedChildWidget', lang.hitch(this, '__refreshButtonVisibility'));
			this.own(aspect.before(this.__container, 'addChild', lang.hitch(this, function(child) {
				this._addHeaderButtonsToChild(child);
				child.own(child.watch('headerButtons', lang.hitch(this, function() {
					this._addHeaderButtonsToChild(child);
				})));
			}), true));
		},

		resetTitle: function() {
			this.set('title', this.defaultTitle);
		},

		_setTitleAttr: function(title) {
			// don't set html attribute title
			// (looks weird)
			this._set('title', title);
			if (this._top) {
				this._top.set('title', title);
			}
		},

		_setTitleDetailAttr: function(detail) {
			var title = this.defaultTitle;
			if (detail) {
				title += ': ' + entities.encode(detail);
			}
			this.set('title', title);
			this._set('titleDetail', detail);
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._bottom = new ContainerWidget({
				'class': 'umcModuleWrapperWrapper'
			});
			var wrapper = new ContainerWidget({
				baseClass: 'umcModuleWrapper',
				'class': 'container'
			});
			wrapper.addChild(this.__container);
			this._bottom.addChild(wrapper);

			this._top = new ModuleHeader({
				//buttons: render.buttons(this.headerButtons, this),
				title: this.get('title')
			});

			this.own(on(this._bottom.domNode, 'scroll', lang.hitch(this, function(evt) {
				domClass.toggle(this.domNode, 'umcModule--scrolled', evt.target.scrollTop > 0);
			})));

			ContainerWidget.prototype.addChild.apply(this, [this._top]);
			ContainerWidget.prototype.addChild.apply(this, [this._bottom]);

			// redirect childrens to stack container
			this.containerNode = this.__container.containerNode;
		},

		selectChild: function(child, animate) {
			return this.__container.selectChild(child, animate);
		},

		onClose: function() {
			if (this.__container && this.__container.onClose) {
				/*return*/ this.__container.onClose();
			}
			return true;
		},

		addChild: function(child, idx) {
			return this.__container.addChild(child, idx);
		},

		removeChild: function(child) {
			return this.__container.removeChild(child);
		},

		_addHeaderButtonsToChild: function(child) {
			// some default buttons (e.g. close)
			var headerButtons = [/*{
				name: 'help',
				label: _('Help'),
				iconClass: 'umcHelpIconWhite',
				'class': 'umcHelpButton',
				callback: lang.hitch(this, function() {
					topic.publish('/umc/tabs/help', this);
				})
			}*/];
			if (this.closable) {
				headerButtons.push({
					name: 'close',
					label: _('Close'),
					callback: lang.hitch(this, 'closeModule')
				});
			}

			if (child.headerButtons) {
				headerButtons = child.headerButtons.concat(headerButtons);
			}

			if (child.$headerButtons$) {
				this._top._right.removeChild(child.$headerButtons$);
				child.$headerButtons$.destroyRecursive();
				delete child.$headerButtons$;
			}

			// make sure no icons are shown in the module header
			array.forEach(headerButtons, function(btn) {
				delete btn.iconClass;
			});

			child._headerButtons = null;
			if (headerButtons && headerButtons.length) {
				var container = new ContainerWidget({});
				child.own(container);

				child._headerButtons = render.buttons(headerButtons.reverse(), container);
				array.forEach(child._headerButtons.$order$.reverse(), function(btn) {
					container.addChild(child._headerButtons[btn.name]); // important! allow overwriting of button names (e.g close)
					btn.on('mouseEnter', function() {
						domClass.add(btn.domNode, 'dijitButtonHover');
						var labelBox = domGeom.getMarginBox(btn.containerNode);
						var buttonBox = domGeom.position(btn.focusNode);
						var halfWidth = (labelBox.w - buttonBox.w) / 2;
						var distanceToBrowserWindow = win.getBox().w - buttonBox.x;
						var offset = Math.max(halfWidth, labelBox.w - distanceToBrowserWindow + 5);
						domGeom.setMarginBox(btn.containerNode, {l: -offset});
					});
				});

				this._top._right.addChild(container, 0);
				child.$headerButtons$ = container;
				container.$child$ = child;
			}
			if (this._started) {
				this.__refreshButtonVisibility();
			}
		},

		__refreshButtonVisibility: function() {
			var child = this.__container.get('selectedChildWidget');
			array.forEach(this._top._right.getChildren(), lang.hitch(this, function(ctn) {
				if (ctn.$child$) {
					domClass.toggle(ctn.domNode, 'dijitDisplayNone', ctn.$child$ !== child);
				}
			}));
		},

		layout: function() {
			this.__container.layout();
		},

		closeModule: function() {
			if (this.closable) {
				topic.publish('/umc/tabs/close', this);
			}
		},

		startup: function() {
			this.__container.startup();
			if (this.__container.selectedChildWidget) {
				this.set('selectedChildWidget', this.__container.selectedChildWidget);
				this.__refreshButtonVisibility();
			}
			this.inherited(arguments);
		}
	});
});
