/*
 * Copyright 2013-2019 Univention GmbH
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
/*global define require console */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/has",
	"dojo/Deferred",
	"dojo/dom-construct",
	"dojo/regexp",
	"umc/tools",
	"umc/widgets/CheckBox",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Form",
	"umc/widgets/SearchBox",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, array, has, Deferred, domConstruct, regexp, tools, CheckBox, ContainerWidget, Form, SearchBox, _) {
	return declare("umc.modules.appcenter.AppLiveSearchSidebar", [ContainerWidget], {
		// summary:
		//		Offers a side bar for live searching, a set of categories can be defined.

		searchLabel: _('Search term'),

		baseClass: 'umcLiveSearchSidebar',

		// searchableAttributes: String[]
		//		Array of strings that shall be searched.
		//		defaults to ['name', 'description', 'categories', 'keywords']
		searchableAttributes: null,

		_lastValue: '',

		constructor: function() {
			this.inherited(arguments);

			this.searchableAttributes = ['name', 'description', 'categories', 'keywords'];
			this._selected = {};
			this._filterForms = {};
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._searchTextBox = new SearchBox({
				inlineLabel: this.searchLabel
			});
			this.addChild(this._searchTextBox);
		},

		postCreate: function() {
			this.inherited(arguments);

			this.own(this._searchTextBox.on('keyup', lang.hitch(this, function() {
				// ignore empty search strings
				if (this.get('value') || this._lastValue) {
					this._lastValue = this.get('value');
					this.onSearch();
				}
			})));
		},

		getFilterValues: function() {
			var values = {};
			tools.forIn(this._filterForms, function(id, formContainer) {
				values[id] = formContainer.$form.get('value');
			});
			return values;
		},

		// this will trigger onSearch for every single checkbox. maybe clean that up
		setFilterValues: function(values) {
			tools.forIn(values, lang.hitch(this, function(id, _values) {
				if (Object.prototype.hasOwnProperty.call(this._filterForms, id)) {
					this._filterForms[id].$form.setFormValues(_values);
					// don't use set('value', _values)
					// the _setValueAttr implementation of dijit/form/_FormMixin
					// does not work with the _getValueAttr implementation of
					// umc/widgets/Form
				}
			}));
		},

		_isInSearchMode: function() {
			return Boolean(lang.trim(this.get('value')));
		},

		_getValueAttr: function() {
			return this._searchTextBox.get('value');
		},

		_setValueAttr: function(value) {
			return this._searchTextBox.set('value', value);
		},

		_setCategoriesAttr: function(categories) {
			this._addFilter('categories', _('App Categories'), categories);
		},

		_setBadgesAttr: function(badges) {
			this._addFilter('badges', _('App Badges'), badges);
		},

		_setLicensesAttr: function(licenses) {
			this._addFilter('licenses', _('App License'), licenses);
		},

		_setVoteForAppsAttr: function(voteForApps) {
			var choices = [];
			if (voteForApps) {
				choices.push({
					id: 'yes',
					description: _('Vote Apps')
				});
			}
			this._addFilter('voteForApps', '', choices);
		},

		getSelected: function(id) {
			return this._selected[id] || [];
		},

		_addFilter: function(id, title, choices) {
			var formContainer = this._filterForms[id];
			if (formContainer) {
				this.removeChild(formContainer);
				formContainer.destroyRecursive();
			}
			this._selected[id] = [];
			if (!choices.length) {
				return;
			}
			formContainer = this._filterForms[id] = new ContainerWidget({'class': 'appLiveSearchSidebarElement'});
			if (title) {
				domConstruct.create('span', {
					innerHTML: title,
					'class': 'mainHeader'
				}, formContainer.domNode);
			}
			this.own(formContainer);
			this.addChild(formContainer);

			var widgets = [];
			array.forEach(choices, lang.hitch(this, function(choice) {
				var label = choice.description;
				if (!title && choices.length === 1) {
					label = '<span class="searchFilterSingle">' + choice.description + '</span>';
				}
				widgets.push({
					type: CheckBox,
					name: choice.id,
					label: label,
					onChange: lang.hitch(this, function(arg) {
						if (arg == true) {
							this._selected[id].push(choice.id);
						} else {
							this._selected[id] = this._selected[id].filter(
								function(x) {return x != choice.id;}
							);
						}
						this.onSearch();  // Trigger the refresh of the displayed Apps
					})
				});
			}));
			var form = new Form({
				widgets: widgets,
			});
			formContainer.addChild(form);
			formContainer.$form = form;
			formContainer.own(form);
		},

		getSearchQuery: function(searchPattern) {
			// sanitize the search pattern
			searchPattern = regexp.escapeString(searchPattern);
			searchPattern = searchPattern.replace(/\\\*/g, '.*');
			searchPattern = searchPattern.replace(/ /g, '\\s+');

			// build together the search function
			var regex  = new RegExp(searchPattern, 'i');
			var searchableAttributes = this.searchableAttributes;
			var query = {
				test: function(value, obj) {
					var string = '';
					array.forEach(searchableAttributes, function(attr) {
						var val = obj[attr] || '';
						if (val instanceof Array) {
							val = val.join(' ');
						}
						string += val + ' ';
					});
					return regex.test(string);
				}
			};
			return query;
		},

		focus: function() {
			this._searchTextBox.focus();
		},

		onSearch: function() {
			// event stub
		},
	});
});

