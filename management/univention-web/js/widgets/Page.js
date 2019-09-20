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
	"dojo/_base/kernel",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom-class",
	"dojox/html/entities",
	"../dialog",
	"../render",
	"./Text",
	"./ContainerWidget"
], function(declare, kernel, lang, array, domClass, entities, dialog, render, Text, ContainerWidget) {
	return declare("umc.widgets.Page", [ContainerWidget], {
		// summary:
		//		Class that abstracts a displayable page for a module.
		//		The widget itself is also a container such that children widgets
		//		may be added via the 'addChild()' method.

		// helpText: String
		//		Text that describes the module, will be displayed at the top of a page.
		helpText: '',
		helpTextRegion: 'nav',
		helpTextAllowHTML: true,  // FIXME: should be false

		// headerText: String
		//		Text that will be displayed as header title.
		headerText: null,
		headerTextRegion: 'nav',
		headerTextAllowHTML: false,

		// footerButtons: Object[]?
		//		Optional array of dicts that describes buttons that shall be added
		//		to the footer. The default button will be displayed on the right
		footerButtons: null,

		navButtons: null,

		// title: String
		//		Title of the page. This option is necessary for tab pages.
		title: '',
		titleAllowHTML: false,

		// noFooter: Boolean
		//		Disable the page footer.
		noFooter: false,

		// fullWidth: Boolean
		//		Let the page take the full width, the navigation element will always be
		//		displayed above the content element.
		fullWidth: false,

		addNotification: function(/*innerHTML*/ message, /*function (optional)*/ action, /*String*/ actionLabel) {
			dialog.contextNotify(message, action, actionLabel);
		},

		navBootstrapClasses: 'col-xs-12 col-sm-12 col-md-4 col-lg-4',
		mainBootstrapClasses: 'col-xs-12 col-sm-12 col-md-8 col-lg-8',
		_initialBootstrapClasses: 'col-xs-12 col-sm-12 col-md-12 col-lg-12',

		// the widget's class name as CSS class
		baseClass: 'umcPage',

		i18nClass: 'umc.app',

		_nav: null,
		_main: null,
		_footer: null,
		_helpTextPane: null,
		_headerTextPane: null,
		_footerButtons: null,
		_navButtons: null,

		_onShow: function() {
			// empty method
		},

		_setTitleAttr: function(title) {
			// don't set html attribute title
			// (looks weird)
			this._set('title', this.titleAllowHTML ? title : entities.encode(title));
		},

		_setHelpTextAttr: function(newVal) {
			if (!newVal && !this._helpTextPane) {
				return;
			}
			if (!this._helpTextPane) {
				this._helpTextPane = new Text({
					region: this.helpTextRegion,
					baseClass: 'umcPageHelpText'
				});
				try {
					this.addChild(this._helpTextPane, 1);  // insert underneath of headerText
				} catch (error) {
					this.addChild(this._helpTextPane);
				}
			}
			domClass.toggle(this._helpTextPane.domNode, 'dijitDisplayNone', !newVal);
			this._helpTextPane.set('content', this.helpTextAllowHTML ? newVal : entities.encode(newVal));
			this._set('helpText', newVal);
		},

		_setHeaderTextAttr: function(newVal) {
			if (!newVal && !this._headerTextPane) {
				return;
			}
			if (!this._headerTextPane) {
				this._headerTextPane = new Text({
					region: this.headerTextRegion,
					baseClass: 'umcPageHeader'
				});
				this.addChild(this._headerTextPane, 0);
			}
			// hide header if empty string
			domClass.toggle(this._headerTextPane.domNode, 'dijitDisplayNone', !newVal);
			this._headerTextPane.set('content', '<h1>' + (this.headerTextAllowHTML ? newVal : entities.encode(newVal)) + '</h1>');
			this._set('headerText', newVal);
		},

		_setNavButtonsAttr: function(navButtons) {
			this._set('navButtons', navButtons);
			if (this._navButtons) {
				this.removeChild(this._navButtons);
				this._navButtons.destroyRecursive();
				this._navButtons = null;
			}
			if (this.navButtons) {
				this._navButtons = new ContainerWidget({
					region: 'nav'
				});
				var buttons = render.buttons(this.navButtons);
				array.forEach(buttons.$order$, lang.hitch(this._navButtons, 'addChild'));
				this.own(this._navButtons);
				this.addChild(this._navButtons);
			}
		},

		postMixInProperties: function() {
			this.inherited(arguments);

			if (this.fullWidth) {
				this.navBootstrapClasses = this._initialBootstrapClasses;
				this.mainBootstrapClasses = this._initialBootstrapClasses;
			}

			// remove title from the attributeMap
			delete this.attributeMap.title;
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._nav = new ContainerWidget({
				baseClass: 'umcPageNav',
				'class': 'dijitDisplayNone'
			});
			this._main = new ContainerWidget({
				baseClass: 'umcPageMain',
				'class': this._initialBootstrapClasses
			});
			ContainerWidget.prototype.addChild.apply(this, [this._nav]);
			ContainerWidget.prototype.addChild.apply(this, [this._main]);

			this._footer = new ContainerWidget({
				region: 'footer',
				baseClass: 'umcPageFooter',
				'class': this._initialBootstrapClasses
			});
			ContainerWidget.prototype.addChild.apply(this, [this._footer]);

			// add the header
			if (this.headerText) {
				this.set('headerText', this.headerText);
			}

			if (this.helpText) {
				this.set('helpText', this.helpText);
			}

			if (!this.noFooter) {
				// create the footer container(s)
				var footerLeft = new ContainerWidget({
					style: 'float: left'
				});
				this._footer.addChild(footerLeft);
				var footerRight = new ContainerWidget({
					style: 'float: right'
				});
				this._footer.addChild(footerRight);

				// render all buttons and add them to the footer
				if (this.footerButtons && this.footerButtons instanceof Array && this.footerButtons.length) {
					this._footerButtons = render.buttons(this.footerButtons);
					array.forEach(this._footerButtons.$order$, function(ibutton) {
						if ('submit' == ibutton.type || ibutton.defaultButton || 'right' == ibutton.align) {
							footerRight.addChild(ibutton);
						}
						else {
							footerLeft.addChild(ibutton);
						}
					}, this);
				}
			}

		},

		addChild: function(widget, position) {
			if (!widget.region || widget.region == 'center' || widget.region == 'right') {
				widget.region = 'main';
			} else if (widget.region == 'top' || widget.region == 'left') {
				widget.region = 'nav';
			} else if (widget.region == 'bottom') {
				widget.region = 'footer';
			}

			if (widget.region == 'nav') {
				this._nav.addChild.apply(this._nav, arguments);
			} else if (widget.region == 'footer') {
				this._footer.addChild.apply(this._footer, arguments);
			} else {
				this._main.addChild.apply(this._main, arguments);
			}
			if (this._started) {
				this._adjustSizes();
			}
		},

		addNote: function(message) {
			// summary:
			//		Show a notification. This is a deprecated method, use dialog.notify(),
			//		dialog.warn(), Module.addNotification(), or Module.addWarning() instead.
			kernel.deprecated('umc/widgets/Page:addNote()', 'use dialog.notify(), dialog.warn(), Module.addNotification(), or Module.addWarning() instead!');
			this.addNotification(message);
		},

		clearNotes: function() {
			// summary:
			//		Deprecated method.
			kernel.deprecated('umc/widgets/Page:clearNotes()', 'remove it, it has no effect!');
		},

		_adjustSizes: function() {
			domClass.remove(this._nav.domNode);
			domClass.remove(this._main.domNode);
			domClass.add(this._nav.domNode, this._nav['class'] + ' ' + this._nav.baseClass);
			domClass.add(this._main.domNode, this._main['class'] + ' ' + this._main.baseClass);

			var hasNav = this._nav.getChildren().length;
			if (hasNav) {
				domClass.toggle(this._nav.domNode, 'dijitDisplayNone', false);
				domClass.remove(this._nav.domNode, this._initialBootstrapClasses);
				domClass.add(this._nav.domNode, this.navBootstrapClasses);
				domClass.remove(this._main.domNode, this._initialBootstrapClasses);
				domClass.add(this._main.domNode, this.mainBootstrapClasses);
			}

			if (!hasNav || this.fullWidth) {
				domClass.add(this.domNode, this.baseClass + '--fullWidth');
			}
		},

		startup: function() {
			this.inherited(arguments);
			this._adjustSizes();
		}
	});
});
