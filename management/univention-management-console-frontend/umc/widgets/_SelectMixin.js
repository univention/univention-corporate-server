/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets._SelectMixin");

dojo.require("dojo.data.ItemFileWriteStore");
dojo.require("dojo.Stateful");
dojo.require("umc.tools");

dojo.declare("umc.widgets._SelectMixin", dojo.Stateful, {
	
	// umcpValues: String
	//		UMCP command to query data from.
	//		Can be mixed with staticValues property.
	umcpValues: null,

	// staticValues: Array
	//		Dict of id-label pairs containing predefined values, e.g.
	//		{ 'de': 'German', 'en': 'English' }.
	//		Can be mixed with dynamicValues where the predefined values are
	//		visible first.
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
		umc.tools.assert(dojo.isObject(this.staticValues) || undefined === this.staticValues, "Static values needs to be a dictionary of entries!");
		var staticValues = this.staticValues || {};
		umc.tools.forIn(staticValues, function(id, label) {
			this.store.newItem({
				id: id,
				label: label
			});
		}, this);

		// save the store in order for the changes to take effect and set the value
		this.store.save();
		this.set('value', this._initialValue);
		this._resetValue = this._initialValue;

		// add all dynamic values which need to be queried via UMCP asynchronously
		if (dojo.isString(this.umcpValues) && this.umcpValues) {
			umc.tools.umcpCommand(this.umcpValues).then(dojo.hitch(this, function(data) {
				// get all items
				var items = [];
				dojo.forEach(data.result, function(i) {
					umc.tools.assert(!(i.id in staticValues), "Entry already defined by static values: " + i.id);
					items.push({
						id: i.id,
						label: i.name
					});
				}, this);
				
				// sort items according to their displayed name
				items.sort(function(a, b) {
					var l1 = a.label.toLowerCase();
					var l2 = b.label.toLowerCase();
					return l1 < l2 ? -1 : l1 > l2 ? 1 : 0;
				});

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


