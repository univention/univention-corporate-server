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
/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.MultiObjectSelect");

dojo.require("umc.widgets.Button");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.MultiSelect");
dojo.require("umc.widgets.SearchForm");
dojo.require("umc.widgets.LabelPane");
dojo.require("tools");
dojo.require("render");
dojo.require("umc.widgets._FormWidgetMixin");
dojo.require("umc.widgets._WidgetsInWidgetsMixin");

dojo.require("dojo.store.DataStore");

/*REQUIRE:"dojo/_base/declare"*/ /*TODO*/return declare([ umc.widgets.ContainerWidget, umc.i18n.Mixin, umc.widgets._FormWidgetMixin ], {
	// summary:
	//		???

	queryWidgets: [],

	queryCommand: '',

	queryOptions: {},

	// 'javascript:functionName'
	// function(ids) { ... }
	// may return /*REQUIRE:"dojo/Deferred"*/ Deferred
	formatter: function(ids) {
		/*REQUIRE:"dojo/_base/array"*/ array.forEach(ids, function(id, i) {
			if (typeof id == "string") {
				ids[i] = {label: id, id: id};
			}
		});
		return ids;
	},

	// autoSearch: String
	//	  Specifies whether or not a query is executed as soon as the dialog is
	//	  opened for the first time.
	autoSearch: true,

	// dialogTitle: String
	//	  Specifies the title of the dialog to add new entries.
	dialogTitle: null,

	name: '',

	value: null,

	i18nClass: 'umc.app',

	// the widget's class name as CSS class
	'class': 'umcMultiObjectSelect',

	// internal reference to the parsed formatter function
	_formatter: function(ids) { return ids; },

	// object store adapter for the data store of the MultiSelect widget
	_objectStore: null,

	// reference to the MultiSelect widget
	_multiSelect: null,

	// reference to the detail dialog
	_detailDialog: null,

	// encapsulate the data store fo the multi select widget
	postMixInProperties: function() {
		this.inherited(arguments);

		// in case 'value' is not specified, generate a new array
		if (!this.value instanceof Array) {
			this.value = [];
		}

		// convert 'formatter' to a function
		this._formatter = tools.stringOrFunction(this.formatter);
	},

	_attachObjectStore: function() {
		this._objectStore = new dojo.store.DataStore( {
			store: this._multiSelect.store
		} );
	},

	buildRendering: function() {
		this.inherited(arguments);

		// add the MultiSelect widget
		this._multiSelect = new umc.widgets.MultiSelect({});
		this._attachObjectStore();
		if ( 'setStore' in this._multiSelect ) {
			/*REQUIRE:"dojo/on"*/ /*TODO*/ on( this._multiSelect, 'setStore', this, '_attachObjectStore' );
		}
		var container = new umc.widgets.ContainerWidget({});
		container.addChild(this._multiSelect);
		this.addChild(container);

		// add the Buttons
		container = new umc.widgets.ContainerWidget({});
		container.addChild(new umc.widgets.Button({
			label: _('Add'),
			iconClass: 'umcIconAdd',
			onClick: /*REQUIRE:"dojo/_base/lang"*/ lang.hitch(this, function() {
				if (!this._detailDialog) {
					// dialog does not exist, create a new one
					this._detailDialog = new umc.widgets._MultiObjectSelectDetailDialog({
						widgets: this.queryWidgets,
						queryCommand: /*REQUIRE:"dojo/_base/lang"*/ lang.hitch( this, 'queryCommand' ),
						queryOptions: this.queryOptions || {},
						autoSearch: this.autoSearch,
						title: this.dialogTitle
					});

					// register the event handler
					/*REQUIRE:"dojo/on"*/ /*TODO*/ this.own(this.on(this._detailDialog, 'onAdd', '_addElements');
					this.onCreateDialog( this._detailDialog );
				}
				this.onShowDialog( this._detailDialog );
				this._detailDialog.show();
			})
		}));
		container.addChild(new umc.widgets.Button({
			label: _('Remove'),
			iconClass: 'umcIconDelete',
			onClick: /*REQUIRE:"dojo/_base/lang"*/ lang.hitch(this, '_removeSelectedElements'),
			style: 'float: right;'
		}));
		this.addChild(container);
	},

	_setValueAttr: function(_values) {
		// handle possible /*REQUIRE:"dojo/Deferred"*/ Deferred object returned by the formatter
		/*REQUIRE:"dojo/when"*/ when(this._formatter(_values), /*REQUIRE:"dojo/_base/lang"*/ lang.hitch(this, function(values) {
			// sort the array according to the labels
			values.sort(tools.cmpObjects('label'));

			// callback handler
			this._multiSelect.set('staticValues', values);
		}));
	},

	_getValueAttr: function() {
		// return a copy
		var values = [];
		this._objectStore.query( {} ).map( function( item ) {
			values.push( item.id );
		} );
		return values;
	},

	getQueryWidget: function(name) {
		// summary:
		//		Return the widget according to the specified name.
		return this._detailDialog._form.getWidget(name);
	},

	_addElements: function( ids ) {
		// only add elements that do not exist already
		var dialog_store = dojo.store.DataStore( { store: this._detailDialog._multiSelect.store } );
		/*REQUIRE:"dojo/_base/array"*/ array.forEach( ids , /*REQUIRE:"dojo/_base/lang"*/ lang.hitch( this, function( id ) {
			var item = dialog_store.get( id );
			try {
				this._objectStore.get( id );
			} catch( e ) {
				// object does not exist ...
				this._objectStore.put( item );
			}
		} ) );
		this._multiSelect.store.save();
	},

	_removeSelectedElements: function() {
		// create a dict for all selected elements
		/*REQUIRE:"dojo/_base/array"*/ array.forEach(this._multiSelect.getSelectedItems(), /*REQUIRE:"dojo/_base/lang"*/ lang.hitch( this, function( iid ) {
			this._objectStore.remove( iid.id );
		} ) );
		this._multiSelect.selection.clear();
		this._multiSelect.store.save();
	},

	uninitialize: function() {
		if (this._detailDialog) {
			this._detailDialog.destroy();
		}
	},

	onCreateDialog: function( dialog ) {
		// event stub
	},

	onShowDialog: function( dialog ) {
		// event stub
	}
});

/*REQUIRE:"dojo/_base/declare"*/ /*TODO*/return declare([ dijit.Dialog, umc.widgets.StandbyMixin, umc.i18n.Mixin ], {
	widgets: [],

	queryCommand: '',

	queryOptions: {},

	autoSearch: true,

	i18nClass: 'umc.app',

	'class': 'umcMultiObjectSelectDetailDialog',

	_form: null,

	_multiSelect: null,

	_container: null,

	uninitialize: function() {
		// make sure that the container widget is destroyed correctly
		this._container.destroyRecursive();
	},

	postMixInProperties: function() {
		this.inherited(arguments);
		if (!this.title) {
			this.title = _('Add objects');
		}
	},

	buildRendering: function() {
		this.inherited(arguments);

		// create a container for all widgets
		this._container = new umc.widgets.ContainerWidget({});
		this._container.placeAt(this.containerNode);

		// for the layout, all Elements should be below each other
		var layout = /*REQUIRE:"dojo/_base/array"*/ array.map(this.widgets, function(iwidget) {
			return iwidget.name;
		});
		this._form = new umc.widgets.SearchForm({
			widgets: this.widgets,
			layout: layout,
			onSearch: /*REQUIRE:"dojo/_base/lang"*/ lang.hitch(this, 'search'),
			onValuesInitialized: /*REQUIRE:"dojo/_base/lang"*/ lang.hitch(this, function() {
				// trigger the search if autoSearch is specified and as soon as all form
				// elements have been initialized
				if (this.autoSearch) {
					this.search(this._form.gatherFormValues());
				}
			})
		});
		this._container.addChild(this._form);

		// for visualizing the search results, use a MultiSelect
		this._multiSelect = new umc.widgets.MultiSelect({
			height: '250px',
			label: _('Search results:')
		});
		this._container.addChild(new umc.widgets.LabelPane({ 
			content: this._multiSelect,
			style: 'display: block;' // do not allow for floating
		}));

		// add the final buttons to close the dialog
		this._container.addChild(new umc.widgets.Button({
			label: _('Add'),
			iconClass: 'umcIconAdd',
			style: 'float: right;',
			onClick: /*REQUIRE:"dojo/_base/lang"*/ lang.hitch(this, function() {
				// get all elements an trigger onAdd event
				var ids = this._multiSelect.get('value');
				if (ids.length) {
					// only trigger event if there are more then 0 entries
					this.onAdd(ids);
				}

				// hide the dialog
				this.hide();

				// unselect all elements
				this._multiSelect.set('value', []);
			})
		}));
		this._container.addChild(new umc.widgets.Button({
			label: _('Cancel'),
			defaultButton: true,
			onClick: /*REQUIRE:"dojo/_base/lang"*/ lang.hitch(this, function() {
				// hide the dialog
				this.hide();

				// unselect all elements
				this._multiSelect.set('value', []);

			})
		}));

		// put focus to last widget in the SearchForm
		/*REQUIRE:"dojo/on"*/ /*TODO*/ this.own(this.on(this, 'onFocus', function() {
			if (this.widgets.length) {
				var lastConf = this.widgets[this.widgets.length - 1];
				var lastName = lastConf.id || lastConf.name;
				var widget = this._form.getWidget(lastName);
				if (/*REQUIRE:"dojo/_base/lang"*/ lang.getObject('focus', false, widget)) {
					widget.focus();
				}
			}
		});
	},

	search: function(_values) {
		// set dynamicOptions which will trigger a reload
		var values = /*REQUIRE:"dojo/_base/lang"*/ lang.mixin({}, this.queryOptions, _values);
		this._multiSelect.set('dynamicOptions', values);

		if (!this._multiSelect.dynamicValues) {
			// the first time we need to set dynamicValues
			this._multiSelect.set('dynamicValues', this.queryCommand);
		}
	},

	onAdd: function(ids) {
		// event stub
	}
});


