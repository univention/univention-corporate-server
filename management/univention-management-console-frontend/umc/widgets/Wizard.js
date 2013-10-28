/*
 * Copyright 2011-2013 Univention GmbH
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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/event",
	"dojo/dom-class",
	"dojo/when",
	"dojo/json",
	"dijit/layout/StackContainer",
	"umc/tools",
	"umc/widgets/Form",
	"umc/widgets/Page",
	"umc/widgets/StandbyMixin",
	"umc/i18n!umc/app"
], function(declare, lang, array, event, domClass, when, json, StackContainer, tools, Form, Page, StandbyMixin, _) {
	return declare("umc.widgets.Wizard", [ StackContainer, StandbyMixin ], {
		// summary:
		//		This wizard class allows to specify a list of pages which will be
		//		shown in a controlable manner.

		// pages: Object[]
		//		Array of page configuration objects. Each object consists of the following
		//		properties:
		//		* name: the page's identifier
		//		* helpText: see `umc.widgets.Page`
		//		* headerText: see `umc.widgets.Page`
		//		* widgets: see `umc.widgets.Form`
		//		* layout: see `umc.widgets.Form`
		//		* buttons: see `umc.widgets.Form`
		pages: null,

		// autoValidate: Boolean
		//		Whether the form of each page is checked before next()/finish()
		autoValidate: false,

		// autoFocus: Boolean
		//		Whether the first widget of the form should be focused upon show()
		autoFocus: false,

		_pages: null,

		buildRendering: function() {
			this.inherited(arguments);

			// render all pages
			this._pages = {};
			array.forEach(this.pages, function(ipage) {
				// setup the footer buttons
				var footerButtons = this.getFooterButtons(ipage.name);

				// render the page
				var pageConf = lang.clone(ipage);
				delete pageConf.widgets;
				delete pageConf.buttons;
				delete pageConf.layout;
				pageConf.footerButtons = footerButtons;
				pageConf.forceHelpText = true;
				var page = new Page(pageConf);

				// create the page form
				if (ipage.widgets || ipage.buttons) {
					page._form = new Form({
						widgets: ipage.widgets,
						buttons: ipage.buttons,
						layout: ipage.layout,
						scrollable: true,
						onSubmit: lang.hitch(this, function(e) {
							if (e && e.preventDefault) {
								e.preventDefault();
							}
							event.stop(e);
							if (this.hasNext(ipage.name)) {
								this._next(ipage.name);
							}
							else {
								this._finish(ipage.name);
							}
							return true;
						})
					});
					page.addChild(page._form);
				}
				
				// add page and remember it internally
				this.addChild(page);
				if (this.autoFocus) {
					page.on('show', lang.hitch(this, function() {
						this.focusFirstWidget(ipage.name);
					}));
				}
				this._pages[ipage.name] = page;
			}, this);
		},

		getFooterButtons: function(pageName) {
			return [{
				name: 'previous',
				label: _('Back'),
				align: 'right',
				callback: lang.hitch(this, '_previous', pageName)
			}, {
				name: 'next',
				defaultButton: true,
				label: _('Next'),
				callback: lang.hitch(this, '_next', pageName)
			}, {
				name: 'finish',
				defaultButton: true,
				label: _('Finish'),
				callback: lang.hitch(this, '_finish', pageName)
			}, {
				name: 'cancel',
				label: _('Cancel'),
				callback: lang.hitch(this, 'onCancel')
			}];
		},

		startup: function() {
			this.inherited(arguments);
			this._next(null);
		},

		_getPageIndex: function(/*String*/ pageName) {
			var idx = -1;
			array.some(this.pages, function(ipage, i) {
				if (ipage.name == pageName) {
					idx = i;
					return true;
				}
			});
			return idx;
		},

		getPage: function(name) {
			return this._pages[name];
		},

		getWidget: function(pageName, _widgetName) {
			var widgetName = _widgetName;
			if ( arguments.length >= 2 && pageName ) {
				return lang.getObject('_pages.' + pageName + '._form._widgets.' + widgetName, false, this);
			}

			// if no page name is given search on all pages
			if ( arguments.length == 1 ) {
				// in case only one parameter has been specified, it indicates the widget name
				widgetName = arguments[0];
			}
			var widget = false;
			array.forEach( this.pages, lang.hitch( this, function( page ) {
				var w = this.getWidget( page.name, widgetName );
				if ( undefined !== w ) {
					widget = w;
					return true; // FIXME
				}
			} ) );

			return widget;
		},

		_updateButtons: function(/*String*/ pageName) {
			var buttons = this._pages[pageName]._footerButtons;
			if (buttons.cancel) {
				domClass.toggle(buttons.cancel.domNode, 'dijitHidden', !this.canCancel(pageName));
			}
			if (buttons.next) {
				domClass.toggle(buttons.next.domNode, 'dijitHidden', !this.hasNext(pageName));
			}
			if (buttons.finish) {
				domClass.toggle(buttons.finish.domNode, 'dijitHidden', this.hasNext(pageName));
			}
			if (buttons.previous) {
				domClass.toggle(buttons.previous.domNode, 'dijitHidden', !this.hasPrevious(pageName));
			}
		},

		hasNext: function(/*String*/ pageName) {
			// summary:
			//		Specifies whether there exists a following page for the specified page name.
			//		By default any page but the last one has a follow-up.
			if (!this.pages.length) {
				return false;
			}
			return this.pages[this.pages.length - 1].name != pageName;
		},

		_next: function(/*String*/ currentPage) {
			// update visibilty of buttons and show next page
			if (this.autoValidate) {
				var page = this._pages[currentPage];
				if (page && page._form && !page._form.validate()) {
					return;
				}
			}
			when(this.next(currentPage), lang.hitch(this, function(nextPage) {
				if (!nextPage) {
					throw new Error('ERROR: received invalid page name [' + json.stringify(nextPage) + '] for Wizard.next(' + json.stringify(currentPage) + ')');
				}
				this._updateButtons(nextPage);
				var page = this._pages[nextPage];
				this.selectChild(page);
			}));
		},

		focusFirstWidget: function(pageName) {
			var page = this._pages[pageName];
			if (page && page._form) {
				tools.forIn(page._form._widgets, function(iname, iwidget) {
					if (iwidget.focus && iwidget.get('visible') && !iwidget.get('disabled')) {
						iwidget.focus();
						return false; // stop
					}
					return true;
				});
			}
		},

		next: function(/*String*/ pageName) {
			// summary:
			//		next() is called when the user requested to advance to the next page.
			//		The custom wizard logic can be implemented here. The method is
			//		expected to return the name of the next page. A pageName == null
			//		indicates that the start page is requested.
			//		By default the wizard implements a logic that takes the order as given
			//		by the `pages` property.
			if ((null === pageName || undefined === pageName) && this.pages.length) {
				return this.pages[0].name;
			}
			var i = this._getPageIndex(pageName);
			if (i < 0) {
				return pageName;
			}
			return this.pages[Math.min(i + 1, this.pages.length - 1)].name;
		},

		hasPrevious: function(/*String*/ pageName) {
			// summary:
			//		Specifies whether there exists a previous page for the specified page name.
			//		By default any page but the first one has a previous page.
			if (!this.pages.length) {
				return false;
			}
			return this.pages[0].name != pageName;
		},

		_previous: function(/*String*/ currentPage) {
			// update visibilty of buttons and show previous page
			when(this.previous(currentPage), lang.hitch(this, function(previousPage) {
				this._updateButtons(previousPage);
				this.selectChild(this._pages[previousPage]);
			}));
		},

		previous: function(/*String*/ pageName) {
			// summary:
			//		previous() is called when the user requested to go back to the previous page.
			//		The custom wizard logic can be implemented here. The method is
			//		expected to return the name of the next page.
			//		By default the wizard implements a logic that takes the order as given
			//		by the `pages` property.
			var i = this._getPageIndex(pageName);
			if (i < 0) {
				return pageName;
			}
			return this.pages[Math.max(i - 1, 0)].name;
		},

		_finish: function(/*String*/ pageName) {
			if (this.autoValidate) {
				var page = this._pages[pageName];
				if (page && page._form && !page._form.validate()) {
					return;
				}
			}
			// gather all values
			var values = this.getValues();
			if (this.canFinish(values, pageName)) {
				this.onFinished(values);
			}
		},

		getValues: function() {
			// summary:
			//		Collects all entered values and returns a dict.
			var values = {};
			array.forEach(this.pages, function(ipage) {
				if (this._pages[ipage.name]._form) {
					lang.mixin(values, this._pages[ipage.name]._form.get('value'));
				}
			}, this);
			return values;
		},

		canCancel: function(/*String*/ pageName) {
			// summary:
			//		Specifies per page whether a cancel button is visible.
			return true;
		},

		onFinished: function(/*Object*/ values) {
			// summary:
			//		This event is called when the wizard has been finished.
			//		The parameter `values` contains the values collected from all pages.
		},

		canFinish: function(/*Object*/ values, /*String*/ pageName) {
			// summary:
			//		Specifies whether the onFinished event can be called
			return true;
		},

		onCancel: function() {
			// summary:
			//		This event is triggered when the user clicks on the 'cancel' button.
		}
	});
});



