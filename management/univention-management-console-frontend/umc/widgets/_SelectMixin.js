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

	_setStaticValues: function() {
		// add all static values to the store
		umc.tools.assert(dojo.isArray(this.staticValues) || !this.staticValues, "Static values needs to be an array of entries: " + dojo.toJson(this.staticValues));
		var staticValues = this.staticValues || [];
		this._ids = {};
		dojo.forEach(staticValues, function(iitem) {
			umc.tools.assert('id' in iitem && 'label' in iitem, "One of the entries specified for static values does not have the properties 'id' and 'label': " + dojo.toJson(iitem));
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
		// get all items
		var items = [];
		dojo.forEach(values, function(iitem) {
			umc.tools.assert(!(iitem.id in this._ids), "Entry already previously defined: " + dojo.toJson(iitem));
			items.push(iitem);
		}, this);
		
		// sort items according to their displayed name
		items.sort(umc.tools.cmpObjects({
			attribute: 'label',
			ignoreCase: true
		}));
		
		// add items to the store
		dojo.forEach(items, function(i) {
			if (i) {
				this.store.newItem(i);
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

		// add dynamic values if all necessary dependency values are given
		var dependValues = {};
		if (dependList.length && dojo.isObject(_dependValues)) {
			// check whether all necessary values are specified
			for (var i = 0; i < dependList.length; ++i) {
				if (_dependValues[dependList[i]]) {
					dependValues[dependList[i]] = _dependValues[dependList[i]];
				}
				else {
					// necessary value not given, don't populate the store
					return;
				}
			}
		}

		// add all dynamic values which need to be queried via UMCP asynchronously
		if (dojo.isString(this.dynamicValues) && this.dynamicValues) {
			this.umcpCommand(this.dynamicValues, dependValues).then(dojo.hitch(this, function(data) {
				this._setDynamicValues(data.result);
			}));
		}
	}
});


