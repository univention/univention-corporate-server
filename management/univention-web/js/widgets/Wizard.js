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
/*global define,window*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/event",
	"dojo/dom-class",
	"dojo/dom-geometry",
	"dojo/aspect",
	"dojo/when",
	"dojo/json",
	"dojox/html/styles",
	"dijit/layout/StackContainer",
	"dijit/focus",
	"../tools",
	"./Form",
	"./Page",
	"./StandbyMixin",
	"./_RegisterOnShowMixin",
	"../i18n!"
], function(declare, lang, array, event, domClass, geometry, aspect, when, json, styles, StackContainer, dijitFocus, tools, Form, Page, StandbyMixin, _RegisterOnShowMixin, _) {
	return declare("umc.widgets.Wizard", [ StackContainer, StandbyMixin, _RegisterOnShowMixin ], {
		// summary:
		//		This wizard class allows to specify a list of pages which will be
		//		shown in a controlable manner.

		baseClass: StackContainer.prototype.baseClass + ' umcWizard',

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

		// autoHeight: Boolean
		//		If set, a min height is computed across all wizard pages in order
		//		to leave the footer with buttons fixed.
		autoHeight: false,

		pageNavBootstrapClasses: null,

		pageMainBootstrapClasses: null,

		_pages: null,

		_cssRule: null,

		headerButtons: null,

		/* StandbyMixin properties */
		standbyColor: '#fff',

		buildRendering: function() {
			this.inherited(arguments);

			// render all pages
			this._pages = {};
			array.forEach(this.pages, function(ipage) {
				// setup the footer buttons
				var footerButtons = this.getFooterButtons(ipage.name);
				var headerButtons = this.getHeaderButtons(ipage.name);

				// render the page
				var pageConf = lang.clone(ipage);
				delete pageConf.widgets;
				delete pageConf.buttons;
				delete pageConf.layout;
				pageConf = lang.mixin({
					footerButtons: footerButtons,
					headerButtons: headerButtons,
					navBootstrapClasses: this.pageNavBootstrapClasses || Page.prototype.navBootstrapClasses,
					mainBootstrapClasses: this.pageMainBootstrapClasses || Page.prototype.mainBootstrapClasses
				}, pageConf);
				var page = new Page(pageConf);

				// create the page form
				if (ipage.widgets || ipage.buttons) {
					page._form = new Form({
						widgets: ipage.widgets,
						buttons: ipage.buttons,
						layout: ipage.layout,
						standby: ipage.standby,
						standbyDuring: ipage.standbyDuring,
						standbyContent: ipage.standbyContent,
						standbyOptions: ipage.standbyOptions,
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
					aspect.after(page, '_onShow', lang.hitch(this, function() {
						this.focusFirstWidget(ipage.name);
					}));
				}
				this._pages[ipage.name] = page;
			}, this);
			this.watch('selectedChildWidget', lang.hitch(this, function(name, old, page) {
				this.set('headerButtons', page.headerButtons);
			}));
		},

		getHeaderButtons: function(pageName) {
			return this.headerButtons || [];
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

		_getMaxHeight: function() {
			if (!this.pages.length) {
				return 0;
			}

			var pageHeights = array.map(this.pages, lang.hitch(this, function(ipageConf) {
				var ipage = this._pages[ipageConf.name];
				var iwrapper = ipage.domNode.parentNode;  // each child is wrapped into a wrapper node
				var isVisible = ipage == this.selectedChildWidget;
				if (!isVisible) {
					// display page offscreen to determine the height
					domClass.remove(iwrapper, 'dijitHidden');
				}
				var iheight = geometry.position(ipage._main.domNode).h;
				if (!isVisible) {
					// restore original state
					domClass.add(iwrapper, 'dijitHidden');
				}
				return iheight;
			}));

			var maxHeight = Math.max.apply(null, pageHeights);
			return maxHeight;
		},

		_removeCssRule: function() {
			if (this._cssRule) {
				styles.removeCssRule.apply(styles, this._cssRule);
				this._cssRule = null;
			}
		},

		_adjustWizardHeight: function() {
			this._removeCssRule();
			this._cssRule = [lang.replace('.umc #{id} .umcPageMain', this), lang.replace('min-height: {0}px; ', [this._getMaxHeight()])];
			styles.insertCssRule.apply(styles, this._cssRule);
		},

		startup: function() {
			this.inherited(arguments);
			this._next(null);
			if (this.autoHeight) {
				this._adjustWizardHeight();
				this._registerAtParentOnShowEvents(lang.hitch(this, '_adjustWizardHeight'));
			}
			this.set('headerButtons', this.get('selectedChildWidget').headerButtons);
		},

		destroy: function() {
			this._removeCssRule();
			this.inherited(arguments);
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
			if (arguments.length >= 2 && pageName) {
				return lang.getObject('_pages.' + pageName + '._form._widgets.' + widgetName, false, this);
			}

			// if no page name is given search on all pages
			if (arguments.length == 1) {
				// in case only one parameter has been specified, it indicates the widget name
				widgetName = arguments[0];
			}
			var widget = false;
			array.forEach(this.pages, lang.hitch(this, function(page) {
				var w = this.getWidget(page.name, widgetName);
				if (undefined !== w) {
					widget = w;
					return true; // FIXME
				}
			}));

			return widget;
		},

		_updateButtons: function(/*String*/ pageName) {
			var buttons = this._pages[pageName]._footerButtons;
			if (buttons.cancel) {
				domClass.toggle(buttons.cancel.domNode, 'dijitDisplayNone', !this.canCancel(pageName));
			}
			if (buttons.next) {
				domClass.toggle(buttons.next.domNode, 'dijitDisplayNone', !this.hasNext(pageName));
			}
			if (buttons.finish) {
				domClass.toggle(buttons.finish.domNode, 'dijitDisplayNone', this.hasNext(pageName));
			}
			if (buttons.previous) {
				domClass.toggle(buttons.previous.domNode, 'dijitDisplayNone', !this.hasPrevious(pageName));
			}
		},

		hasNext: function(/*String*/ pageName) {
			// summary:
			//		Specifies whether there exists a following page for the specified page name.
			//		By default any page which has a visible follower has a follow-up.
			if (!this.pages.length) {
				return false;
			}
			var pageIndex = this._getPageIndex(pageName);
			return array.some(this.pages, lang.hitch(this, function(page, i) {
				if (i <= pageIndex) {
					return false;
				}
				return this.isPageVisible(page.name);
			}));
		},

		_next: function(/*String*/ currentPage) {
			// update visibilty of buttons and show next page
			if (this.autoValidate) {
				var page = this._pages[currentPage];
				if (page && page._form && !page._form.validate()) {
					page._form.focusFirstInvalidWidget();
					return;
				}
			}
			when(this.next(currentPage), lang.hitch(this, function(nextPage) {
				if (!nextPage) {
					throw new Error('ERROR: received invalid page name [' + json.stringify(nextPage) + '] for Wizard.next(' + json.stringify(currentPage) + ')');
				}
				this.switchPage(nextPage);
			}));
		},

		switchPage: function(pageName) {
			this._updateButtons(pageName);
			this.selectChild(this._pages[pageName]);
			window.scrollTo(0, 0);
		},

		focusFirstWidget: function(pageName) {
			var page = this._pages[pageName];
			var firstWidgetOnPage = null;
			if (page && page._form) {
				tools.forIn(page._form._widgets, function(iname, iwidget) {
					if (iwidget.focus && iwidget.get('visible') && !iwidget.get('disabled')) {
						firstWidgetOnPage = iwidget;
						return false; // stop
					}
					return true;
				});
				if (firstWidgetOnPage) {
					firstWidgetOnPage.focus();
				}
			}
			if (!firstWidgetOnPage && dijitFocus.curNode) {
				// make sure no previous button has the focus...
				// this might re-execute an action when pressing enter/space
				dijitFocus.curNode.blur();
			}
		},

		isPageVisible: function(/*String*/ pageName) {
			// summary:
			//		Specifies whether a page is visible or not. The method will
			//		be evaluated automatically next() and previous(). Defaults
			//		to true.
			return true;
		},

		next: function(/*String*/ pageName) {
			// summary:
			//		next() is called when the user requested to advance to the next page.
			//		The custom wizard logic can be implemented here. The method is
			//		expected to return the name of the next page. A pageName == null
			//		indicates that the start page is requested.
			//		By default the wizard implements a logic that takes the order as given
			//		by the `pages` property.

			// no pageName defined
			if ((null === pageName || undefined === pageName) && this.pages.length) {
				if (!this.isPageVisible(this.pages[0].name)) {
					return this.next(this.pages[0].name);
				}
				return this.pages[0].name;
			}

			var i = this._getPageIndex(pageName);
			if (i < 0) {
				// pageName does not exist
				return pageName;
			}

			// find the next visible page
			for (++i; i < this.pages.length && !this.isPageVisible(this.pages[i].name); ++i) { }
			return this.pages[Math.min(i, this.pages.length - 1)].name;
		},

		hasPrevious: function(/*String*/ pageName) {
			// summary:
			//		Specifies whether there exists a previous page for the specified page name.
			//		By default any page which has a visible page before has a previous page.
			if (!this.pages.length) {
				return false;
			}
			var pageIndex = this._getPageIndex(pageName);
			return array.some(this.pages, lang.hitch(this, function(page, i) {
				if (i >= pageIndex) {
					return false;
				}
				return this.isPageVisible(page.name);
			}));
		},

		_previous: function(/*String*/ currentPage) {
			// update visibilty of buttons and show previous page
			when(this.previous(currentPage), lang.hitch(this, function(previousPage) {
				this.switchPage(previousPage);
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

			// find the previous visible page
			for (--i; i >= 0 && !this.isPageVisible(this.pages[i].name); --i) { }
			var previous = this.pages[Math.max(i, 0)].name;
			if (!this.isPageVisible(previous)) {
				return pageName;
			}
			return previous;
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
