/*
 * Copyright 2011-2012 Univention GmbH
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
/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.Wizard");

dojo.require("dijit.layout.StackContainer");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Page");
dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.StandbyMixin");

dojo.declare("umc.widgets.Wizard", [ dijit.layout.StackContainer, umc.widgets.StandbyMixin, umc.i18n.Mixin ], {
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

	i18nClass: 'umc.app',

	_pages: null,

	buildRendering: function() {
		this.inherited(arguments);

		// render all pages
		this._pages = {};
		dojo.forEach(this.pages, function(ipage) {
			// setup the footer buttons
			var footerButtons = [{
				name: 'previous',
				label: this._('Back'),
				align: 'right',
				callback: dojo.hitch(this, '_previous', ipage.name)
			}, {
				name: 'next',
				defaultButton: true,
				label: this._('Next'),
				callback: dojo.hitch(this, '_next', ipage.name)
			}, {
				name: 'finish',
				defaultButton: true,
				label: this._('Finish'),
				callback: dojo.hitch(this, '_finish', ipage.name)
			}, {
				name: 'cancel',
				label: this._('Cancel'),
				callback: dojo.hitch(this, 'onCancel')
			}];

			// render the page
			var pageConf = dojo.clone(ipage);
			delete pageConf.widgets;
			delete pageConf.buttons;
			delete pageConf.layout;
			pageConf.footerButtons = footerButtons;
			pageConf.forceHelpText = true;
			var page = new umc.widgets.Page(pageConf);

			// create the page form
			if (ipage.widgets || ipage.buttons) {
				page._form = new umc.widgets.Form({
					widgets: ipage.widgets,
					buttons: ipage.buttons,
					layout: ipage.layout,
					scrollable: true,
					onSubmit: dojo.hitch(this, function(e) {
						if (e && e.preventDefault) {
							e.preventDefault();
						}
						dojo.stopEvent(e);
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
			this._pages[ipage.name] = page;
		}, this);
	},

	postCreate: function() {
		this.inherited(arguments);

		this._next(null);
	},

	_getPageIndex: function(/*String*/ pageName) {
		var idx = -1;
		dojo.forEach(this.pages, function(ipage, i) {
			if (ipage.name == pageName) {
				idx = i;
				return false;
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
			return dojo.getObject('_pages.' + pageName + '._form._widgets.' + widgetName, false, this);
		}

		// if no page name is given search on all pages
		if ( arguments.length == 1 ) {
			// in case only one parameter has been specified, it indicates the widget name
			widgetName = arguments[0];
		}
		var widget = false;
		dojo.forEach( this.pages, dojo.hitch( this, function( page ) {
			var w = this.getWidget( page.name, widgetName );
			if ( undefined !== w ) {
				widget = w;
				return true;
			}
		} ) );

		return widget;
	},

	_updateButtons: function(/*String*/ pageName) {
		var buttons = this._pages[pageName]._footerButtons;
		dojo.toggleClass(buttons.cancel.domNode, 'dijitHidden', !this.canCancel(pageName));
		dojo.toggleClass(buttons.next.domNode, 'dijitHidden', !this.hasNext(pageName));
		dojo.toggleClass(buttons.finish.domNode, 'dijitHidden', this.hasNext(pageName));
		dojo.toggleClass(buttons.previous.domNode, 'dijitHidden', !this.hasPrevious(pageName));
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
		dojo.when(this.next(currentPage), dojo.hitch(this, function(nextPage) {
			if (!nextPage) {
				throw new Error('ERROR: received invalid page name [' + dojo.toJson(nextPage) + '] for Wizard.next(' + dojo.toJson(currentPage) + ')');
			}
			this._updateButtons(nextPage);
			this.selectChild(this._pages[nextPage]);
		}));
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
		dojo.when(this.previous(currentPage), dojo.hitch(this, function(previousPage) {
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
		// gather all values
		var values = this.getValues();
		if (this.canFinish(values)) {
			this.onFinished(values);
		}
	},

	getValues: function() {
		// summary:
		//		Collects all entered values and returns a dict.
		var values = {};
		dojo.forEach(this.pages, function(ipage) {
			if (this._pages[ipage.name]._form) {
				dojo.mixin(values, this._pages[ipage.name]._form.gatherFormValues());
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

	canFinish: function(/*Object*/ values) {
		// summary:
		//		Specifies whether the onFinished event can be called
		return true;
	},

	onCancel: function() {
		// summary:
		//		This event is triggered when the user clicks on the 'cancel' button.
	}
});




