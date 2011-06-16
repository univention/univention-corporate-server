/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets._SelectMixin");

dojo.require("dojo.data.ItemFileWriteStore");
dojo.require("dojo.Stateful");
dojo.require("umc.tools");

dojo.declare("umc.widgets._SelectMixin", dojo.Stateful, {
	
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

	// searchAttr needs to specified, otherwise the values from the store will not be displayed.
	searchAttr: 'label',

	store: null,

	value: '',

	_setupStore: function() {
		// The store needs to be available already at construction time, otherwise an 
		// error will be thrown. We need to define it here, in order to create a new 
		// store for each instance.
		this.store = new dojo.data.ItemFileWriteStore({ 
			data: {
				identifier: 'id',
				label: 'label',
				items: []
			}
		});
	},

	_saveInitialValue: function() {
		// rember the intial value since it will be overridden by the dojo
		// methods since at initialization time the store is empty
		this._initialValue = this.value;
	},

	_populateStore: function() {
		// add all static values to the store
		umc.tools.assert(dojo.isArray(this.staticValues) || undefined === this.staticValues, "Static values needs to be an array of entries!");
		var staticValues = this.staticValues || [];
		var ids = {};
		dojo.forEach(staticValues, function(iitem) {
			umc.tools.assert('id' in iitem && 'label' in iitem, "One of the entries specified for static values does not have the properties 'id' and 'label': " + dojo.toJson(iitem));
			this.store.newItem(iitem);

			// cache the values in a dict
			ids[iitem.id] = iitem.label;
		}, this);

		// save the store in order for the changes to take effect and set the value
		this.store.save();
		this.set('value', this._initialValue);
		this._resetValue = this._initialValue;

		// add all dynamic values which need to be queried via UMCP asynchronously
		if (dojo.isString(this.dynamicValues) && this.dynamicValues) {
			umc.tools.umcpCommand(this.dynamicValues).then(dojo.hitch(this, function(data) {
				// get all items
				var items = [];
				dojo.forEach(data.result, function(iitem) {
					umc.tools.assert(!(iitem.id in ids), "Entry already previously defined: " + dojo.toJson(iitem));
					items.push(iitem);
				}, this);
				
				// sort items according to their displayed name
				items.sort(umc.tools.cmpObjects({
					attribute: 'label',
					ignoreCase: true
				}));
				
				// add items to the store
				dojo.forEach(items, function(i) {
					this.store.newItem(i);
				}, this);
			}));

			// save the store in order for the changes to take effect and set the value
			this.store.save();
			this.set('value', this._initialValue);
			this._resetValue = this._initialValue;
		}
	}
});


