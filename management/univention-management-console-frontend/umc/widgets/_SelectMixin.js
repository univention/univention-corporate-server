/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets._SelectMixin");

dojo.require("dojo.data.ItemFileWriteStore");
dojo.require("dojo.Stateful");
dojo.require("umc.tools");

dojo.declare("umc.widgets._SelectMixin", dojo.Stateful, {
	// umcpCommand:
	//		Reference to the umcpCommand the widget should use.
	//		In order to make the widget send information such as module flavor
	//		etc., it can be necessary to specify a module specific umcpCommand
	//		method.
	umcpCommand: umc.tools.umcpCommand,
	
	// dynamicValues: String
	//		UMCP command to query data from. Can be mixed with staticValues 
	//		property. Command is expected to return an array in the same 
	//		format as for staticValues.
	dynamicValues: null,

	// dynamicOptions: Object?|Function?
	//		Reference to a dictionary containing options that are passed over to
	//		the UMCP command specified by `dynamicValues`. Instead of an dictionary,
	//		a reference of a function returning a dictionary can also be specified.
	dynamicOptions: null,

	// staticValues: Object[]
	//		Array of id/label objects containing predefined values, e.g.
	//		[ { id: 'de', label: 'German' }, { id: 'en', label: 'English' } ].
	//		Can be mixed with dynamicValues with the predefined values being
	//		displayed first.
	staticValues: [],

	// depends: String?|String[]?
	//		Specifies that values need to be loaded dynamically depending on
	//		other form fields.
	depends: null,

	// searchAttr needs to specified, otherwise the values from the store will not be displayed.
	searchAttr: 'label',

	store: null,

	value: '',

	// internal variable to keep track of which ids have already been added
	_ids: {},

	_setupStore: function() {
		// The store needs to be available already at construction time, otherwise an 
		// error will be thrown. We need to define it here, in order to create a new 
		// store for each instance.
		this.store = new dojo.data.ItemFileWriteStore({ 
			data: {
				identifier: 'id',
				label: 'label',
				items: []
			},
			clearOnClose: true
		});
	},

	_saveInitialValue: function() {
		// rember the intial value since it will be overridden by the dojo
		// methods since at initialization time the store is empty
		this._initialValue = this.value;
	},

	_clearValues: function() {
		// clear the store, see:
		//   http://mail.dojotoolkit.org/pipermail/dojo-interest/2011-January/052159.html
		this.store.save();
		this.store.data = {
			identifier: 'id',
			label: 'label',
			items: []
		};
		this.store.close();
	},

	_convertItems: function(_items) {
		// unify the items into the format:
		//   [{
		//       id: '...', 
		//       label: '...'
		//   }, ... ]
		var items = [];

		if (dojo.isArray(_items)) {
			dojo.forEach(_items, function(iitem) {
				// string
				if (dojo.isString(iitem)) {
					items.push({
						id: iitem,
						label: iitem
					});
				}
				// array of dicts
				else if (dojo.isObject(iitem)) {
					umc.tools.assert('id' in iitem && 'label' in iitem, "umc.widgets._SelectMixin: One of the entries specified does not have the properties 'id' and 'label': " + dojo.toJson(iitem));
					items.push(iitem);
				}
				// unknown format
				else {
					umc.tools.assert(false, "umc.widgets._SelectMixin: Given items are in incorrect format: " + dojo.toJson(_items));
				}
			});
		}
		else {
			umc.tools.assert(false, "umc.widgets._SelectMixin: Given items are in incorrect format: " + dojo.toJson(_items));
		}

		return items;
	},

	_setStaticValues: function() {
		// convert items to the correct format
		var staticValues = this._convertItems(this.staticValues);

		// add all static values to the store
		this._ids = {};
		dojo.forEach(staticValues, function(iitem) {
			// add item to store
			umc.tools.assert(!(iitem.id in this._ids), "umc.widgets._SelectMixin: Entry already previously defined: " + dojo.toJson(iitem));
			this.store.newItem(iitem);

			// cache the values in a dict
			this._ids[iitem.id] = iitem.label;
		}, this);

		// save the store in order for the changes to take effect and set the value
		this.store.save();
		this.set('value', this._initialValue);
		this._resetValue = this._initialValue;
	},

	_setDynamicValues: function(/*Object[]*/ values) {
		// convert items to the correct format
		var items = this._convertItems(values);

		// sort items according to their displayed name
		items.sort(umc.tools.cmpObjects({
			attribute: 'label',
			ignoreCase: true
		}));

		// add items to the store
		dojo.forEach(items, function(iitem) {
			if (iitem) {
				// add item to store
				umc.tools.assert(!(iitem.id in this._ids), "umc.widgets._SelectMixin: Entry already previously defined: " + dojo.toJson(iitem));
				this.store.newItem(iitem);

				// set pre-selected item
				if (iitem.preselected) {
                    this._initialValue = iitem.id;
                }
			}
		}, this);

		// save the store in order for the changes to take effect and set the value
		this.store.save();
		this.set('value', this._initialValue);
		this._resetValue = this._initialValue;
	},

	_loadValues: function(/*Object?*/ _dependValues) {
		this._clearValues();
		this._setStaticValues();

		// unify `depends` property to be an array
		var dependList = dojo.isArray(this.depends) ? this.depends : 
			(this.depends && dojo.isString(this.depends)) ? [ this.depends ] : [];

		// check whether all necessary values are specified
		var params = {};
		var nDepValues = 0;
		if (dependList.length && dojo.isObject(_dependValues)) {
			// check whether all necessary values are specified
			for (var i = 0; i < dependList.length; ++i) {
				if (_dependValues[dependList[i]]) {
					params[dependList[i]] = _dependValues[dependList[i]];
					++nDepValues;
				}
			}
		}

		// only load dynamic values in case all dependencies are fullfilled
		if (dependList.length != nDepValues) {
			return;
		}

		// mixin additional options for the UMCP command
		if (this.dynamicOptions && dojo.isObject(this.dynamicOptions)) {
			dojo.mixin(params, this.dynamicOptions);
		}
		else if (this.dynamicOptions && dojo.isFunction(this.dynamicOptions)) {
			var res = this.dynamicOptions();
			umc.tools.assert(res && dojo.isObject(res), 'The return type of a function specified by umc.widgets._SelectMixin.dynamicOptions() needs to return a dictionary: ' + dojo.toJson(res));
			dojo.mixin(params, res);
		}

		// add all dynamic values which need to be queried via UMCP asynchronously
		if (dojo.isString(this.dynamicValues) && this.dynamicValues) {
			this.umcpCommand(this.dynamicValues, params).then(dojo.hitch(this, function(data) {
				this._setDynamicValues(data.result);
				this.onDynamicValuesLoaded(data.result);
			}));
		}
	},

	onDynamicValuesLoaded: function(values) {
		// event stub
	}
});


