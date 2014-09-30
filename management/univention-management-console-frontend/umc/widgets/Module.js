/*
 * Copyright 2011-2014 Univention GmbH
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
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/topic",
	"dojo/aspect",
	"dojo/dom-class",
	"dijit/layout/StackContainer",
	"dojox/html/entities",
	"umc/tools",
	"umc/render",
	"umc/widgets/_ModuleMixin",
	"umc/widgets/ContainerWidget",
	"umc/widgets/ModuleHeader",
	"umc/widgets/StandbyMixin",
	"umc/i18n!"
], function(declare, lang, array, topic, aspect, domClass, StackContainer, entities, tools, render, _ModuleMixin, ContainerWidget, ModuleHeader, StandbyMixin, _) {
	return declare("umc.widgets.Module", [ContainerWidget, _ModuleMixin, StandbyMixin], {
		// summary:
		//		Basis class for module classes.

		_top: null,
		_bottom: null,
		__container: null,
		headerButtons: null,

		// initial title set for the module
		defaultTitle: null,

		postMixInProperties: function() {
			this.headerButtons = [];
			this.inherited(arguments);
			this.defaultTitle = this.title;

			var headerButtons = [{
				name: 'help',
				label: _('Help'),
				iconClass: 'umcHelpIconWhite',
				'class': 'umcHelpButton',
				callback: lang.hitch(this, function() {
					topic.publish('/umc/tabs/help', this);
				})
			}];
			if (this.closable) {
				headerButtons.push({
					name: 'close',
					label: _('Close'),
					iconClass: 'umcCloseIconWhite',
					'class': 'umcCloseButton',
					callback: lang.hitch(this, 'closeModule')
				});
			}

			this.headerButtons = headerButtons.concat(this.headerButtons);

			this._registerHeaderButtonsHandling();

		},

		_registerHeaderButtonsHandling: function() {
			this._headerButtonsMap = {};
			aspect.after(this, 'addChild', lang.hitch(this, function(child) {
				if (child.headerButtons) {
					var container = new ContainerWidget({
						style: 'display: inline-block; margin: 0; padding: 0;'
					});
					child.own(container);
					array.forEach(render.buttons(child.headerButtons, container).$order$, function(btn) {
						container.addChild(btn);
					});
					this._top._right.addChild(container, 0);
					this._headerButtonsMap[child.id] = container;
				}
			}), true);

			this.watch('selectedChildWidget', lang.hitch(this, function(name, old, child) {
				tools.forIn(this._headerButtonsMap, lang.hitch(this, function(id, ctn) {
					if (!ctn.domNode) {
						// child has been removed
						delete this._headerButtonsMap[id];
						return;
					}
					domClass.toggle(ctn.domNode, 'dijitHidden', id !== child.id);
				}));
			}));
		},

		resetTitle: function() {
			this.set('title', this.defaultTitle);
		},

		_setTitleAttr: function(title) {
			// dont set html attribute title
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
				'class': 'umcModuleWrapper container'
			});

			this._top = new ModuleHeader({
				buttons: render.buttons(this.headerButtons, this),
				title: this.get('title')
			});

			this.__container = new StackContainer({
				'class': 'umcModuleContent',
				doLayout: false
			});
			this.__container.watch('selectedChildWidget', lang.hitch(this, function(name, oldV, newV) {
				this.set(name, newV);
			}));
			this._bottom.addChild(this.__container);

			ContainerWidget.prototype.addChild.apply(this, [this._top]);
			ContainerWidget.prototype.addChild.apply(this, [this._bottom]);
			this.__colorizeModuleHeader();

			// redirect childrens to stack container
			this.containerNode = this.__container.containerNode;
		},

		__colorizeModuleHeader: function() {
			var cls = this.moduleID;
			if (this.moduleFlavor) {
				cls = lang.replace('{moduleID}-{moduleFlavor}', this);
			}
			domClass.add(this._top.domNode, lang.replace('umcModuleHeader-{0}', [cls]).replace(/[^_a-zA-Z0-9\-]/g, '-'));
		},

		selectChild: function(child, animate) {
			return this.__container.selectChild(child, animate);
		},

		onClose: function() {
			return this.__container.onClose && this.__container.onClose() || true;
		},

		addChild: function(child, idx) {
			return this.__container.addChild(child, idx);
		},

		layout: function() {
			this.__container.layout();
		},

		closeModule: function() {
			topic.publish('/umc/tabs/close', this);
		},

		startup: function() {
			this.__container.startup();
			this.inherited(arguments);

			// FIXME: Workaround for refreshing problems with datagrids when they are rendered
			//        on an inactive tab.

			// iterate over all widgets
			array.forEach(this.getChildren(), function(iwidget) {
				if (tools.inheritsFrom(iwidget, 'dojox.grid._Grid')) {
					// hook to onShow event
					this.on('show', lang.hitch(this, function() {
						iwidget.startup();
					}));
				}
			}, this);
		}
	});
});
