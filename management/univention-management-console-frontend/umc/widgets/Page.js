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
	"dojo/_base/kernel",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/fx",
	"dojo/on",
	"dojo/mouse",
	"dojo/query",
	"dojo/dom-style",
	"dojo/dom-class",
	"dojo/topic",
	"umc/tools",
	"umc/dialog",
	"umc/render",
	"umc/widgets/Text",
	"umc/widgets/ContainerWidget",
	"umc/i18n!"
], function(declare, kernel, lang, array, baseFX, on, mouse, query, style, domClass, topic, tools, dialog, render, Text, ContainerWidget, _) {
	return declare("umc.widgets.Page", ContainerWidget, {
		// summary:
		//		Class that abstracts a displayable page for a module.
		//		Offers the possibility to enter a help text that is shown or not
		//		depending on the user preferences.
		//		The widget itself is also a container such that children widgets
		//		may be adde via the 'addChild()' method.

		// helpText: String
		//		Text that describes the module, will be displayed at the top of a page.
		helpText: '',
		helpTextRegion: 'nav',

		// headerText: String
		//		Text that will be displayed as header title.
		headerText: null,
		headerTextRegion: 'nav',

		// footerButtons: Object[]?
		//		Optional array of dicts that describes buttons that shall be added
		//		to the footer. The default button will be displayed on the right
		footerButtons: null,

		// title: String
		//		Title of the page. This option is necessary for tab pages.
		title: '',

		// noFooter: Boolean
		//		Disable the page footer.
		noFooter: false,

		// forceHelpText: Boolean
		//		If set to true, forces the help text to be shown.
		forceHelpText: false,

		addNotification: lang.hitch(dialog, 'notify'),

		// the widget's class name as CSS class
		'class': 'umcPage',

		i18nClass: 'umc.app',

		_helpTextPane: null,
		_headerTextPane: null,
		_subscriptionHandle: null,
		_footer: null,
		_footerButtons: null,

		_setTitleAttr: function(title) {
			// dont set html attribute title
			// (looks weird)
			this._set('title', title);
		},

		_setHelpTextAttr: function(newVal) {
			this.helpText = newVal;
			if (this._helpTextPane) {
				this._helpTextPane.set('content', newVal);
				//this.layout();
			}
		},

		_setHeaderTextAttr: function(newVal) {
			if (this._headerTextPane) {
				// hide header if empty string
				style.set(this._headerTextPane.domNode, {
					display: newVal ? 'block' : 'none'
				});
				this._headerTextPane.set('content', '<h1>' + newVal + '</h1>');
				//this.layout();
			}
			this._set('headerText', newVal);
		},

		postMixInProperties: function() {
			this.inherited(arguments);

			// remove title from the attributeMap
			delete this.attributeMap.title;
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._nav = new ContainerWidget({
				'class': 'umcPageNav dijitHidden'
			});
			this._main = new ContainerWidget({
				'class': 'umcPageMain col-xs-12'
			});
			ContainerWidget.prototype.addChild.apply(this, [this._nav]);
			ContainerWidget.prototype.addChild.apply(this, [this._main]);

			this._footer = new ContainerWidget({
				region: 'footer',
				'class': 'umcPageFooter col-xs-12'
			});
			ContainerWidget.prototype.addChild.apply(this, [this._footer]);

			// add the header
			if (this.headerText) {
				this._headerTextPane = new Text({
					region: this.headerTextRegion,
					'class': 'umcPageHeader'
				});
				this.addChild(this._headerTextPane);
				this.set('headerText', this.headerText);
			}

			if (tools.preferences('moduleHelpText') && this.helpText) {
				// display the module helpText
				this._createHelpTextPane();
				this.addChild(this._helpTextPane);
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
					var buttons = render.buttons(this.footerButtons);
					array.forEach(buttons.$order$, function(ibutton) {
						if ('submit' == ibutton.type || ibutton.defaultButton || 'right' == ibutton.align) {
							footerRight.addChild(ibutton);
						}
						else {
							footerLeft.addChild(ibutton);
						}
					}, this);
					this._footerButtons = buttons;
				}
			}
		},

		postCreate: function() {
			this.inherited(arguments);

			if (this.forceHelpText) {
				// help text should be displayed in any case
				this.showDescription();
			}
			else {
				// register for events to hide the help text information
				this._subscriptionHandle = topic.subscribe('/umc/preferences/moduleHelpText', lang.hitch(this, function(show) {
					if (false === show) {
						this.hideDescription();
					}
					else {
						this.showDescription();
					}
				}));
			}
		},

		uninitialize: function() {
			// unsubscribe upon destruction
			if (this._subscriptionHandle) {
				this._subscriptionHandle.remove();
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
		},

		_createHelpTextPane: function() {
			this._helpTextPane = new Text({
				region: this.helpTextRegion,
				content: this.helpText,
				'class': 'umcPageHelpText'
			});
		},

		showDescription: function() {
			// if we don't have a help text, ignore call
			if (this._helpTextPane || !this.helpText) {
				return;
			}

			// put the help text in a Text widget and then add it to the container
			// make the node transparent, yet displayable
			this._createHelpTextPane();
			style.set(this._helpTextPane.domNode, {
				opacity: 0,
				display: 'block'
			});
			var position = this._headerTextPane && this._headerTextPane == this._nav.getChildren()[0] ? 1 : 0;
			this.addChild(this._helpTextPane, position);
			//this.layout();

			// fade in the help text
			baseFX.fadeIn({
				node: this._helpTextPane.domNode,
				duration: 500
			}).play();
		},

		hideDescription: function() {
			// if we don't have a help text visible, ignore call
			if (!this._helpTextPane) {
				return;
			}

			// fade out the help text
			baseFX.fadeOut({
				node: this._helpTextPane.domNode,
				duration: 500,
				onEnd: lang.hitch(this, function() {
					// remove the text from the layout and destroy widget
					this.removeChild(this._helpTextPane);
					this._helpTextPane.destroyRecursive();
					this._helpTextPane = null;
					//this.layout();
				})
			}).play();
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

		startup: function() {
			this.inherited(arguments);

			domClass.remove(this._nav.domNode);
			domClass.remove(this._main.domNode);
			domClass.add(this._nav.domNode, this._nav['class']);
			domClass.add(this._main.domNode, this._main['class']);

			var hasNav = this._nav.getChildren().length;
			if (hasNav) {
				domClass.toggle(this._nav.domNode, "dijitHidden", false);
				domClass.add(this._nav.domNode, "col-xs-12 col-md-4");
				domClass.add(this._main.domNode, "col-sm-12 col-md-8");
			}

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

