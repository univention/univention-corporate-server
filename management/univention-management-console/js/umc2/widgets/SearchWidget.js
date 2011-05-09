/*global dojo dijit dojox umc2 console window */

dojo.provide("umc2.widgets.SearchWidget");

dojo.require("dijit.layout.ContentPane");
dojo.require("dijit._Widget");
dojo.require("dijit.form.TextBox");
dojo.require("dijit.form.Button");
dojo.require("dojox.layout.TableContainer");
dojo.require("umc2.widgets.ContainerForm");
dojo.require("umc2.widgets.ContainerWidget");
dojo.require("umc2.widgets.FilteringSelect");

dojo.declare('umc2.widgets.SearchWidget', dijit.layout.ContentPane, {
	_layoutContainer: null,
	_form: null,
	_connects: [],
	_formWidgets: {},
	region: 'top',
	open: true,

	// fields: [Object|null|undefined]
	//		Array of property maps used to render the search form.
	//		For a select box, a map needs to have the properties 
	//		{ id, store, labelAttr, label, value };
	//		For a text box, a map needs only to have the properties 
	//		{ id, label, value }.
	//		Note that value is optional and defaults to an empty string.
	fields: [],

	// description:
	//		Given a property map, render the particular search element which
	//		can be an empty field, a text field, a select box.
	// obj:
	//		Null or undefined renders as empty element, otherwise a property map.
	//		Elements from this.fields are handed over to this method.
	_renderFormElement: function(/*null|undefined|Object*/ obj) {
		// if null/undefined, we create an empty field
		if (!obj) {
			return new dijit._Widget(); // return dijit._Widget
		}

		// if we have a store object, we create a FilteringSelect widget
		var widget;
		if ('store' in obj) {
			// create the widget
			widget = new umc2.widgets.FilteringSelect({
				_key: obj.id,
				label: obj.label,
				style: 'width: 300px',
				store: obj.store,
				searchAttr: obj.labelAttr
			});

			// try to get the corresponding item for the given default value;
			// if the value does not exist, use the first value in the list.
			var onFetchComplete = dojo.hitch(widget, function(items, request) {
				// iterate through all items and try to match the specified
				// default value (== obj.value)
				var matchedItem = null;
				for (var i = 0; i < items.length; ++i) {
					var item = items[i];
					var itemID = this.store.getIdentity(item);
					if (!matchedItem && itemID == obj.value) {
						matchedItem = item;
						break;
					}
				}

				// if the specified value could not be matched, take the first item
				if (!matchedItem) {
					matchedItem = items[0];
				}

				// update the widget's selected item
				this.set('defaultItem', matchedItem);
				this.set('item', matchedItem);
			});
			// fetch data elements in store
			widget.store.fetch({
				onComplete: onFetchComplete, 
				onError: function(e, r) { 
					console.log(e); 
				} 
			});

			// return the FilteringSelect widget
			this._formWidgets[obj.id] = widget;
			return widget; // dijit._Widget
		}

		// otherwise create a TextBox
		widget = new dijit.form.TextBox({
			_key: obj.id,
			label: obj.label,
			//style: 'width: 300px',
			value: obj.value
		});
		this._formWidgets[obj.id] = widget;
		return widget; // dijit._Widget
	},

	buildRendering: function() {
		// call superclass' postCreate()
		this.inherited(arguments);

		// embed layout container within a form-element
		this._form = new umc2.widgets.ContainerForm({
			onSubmit: dojo.hitch(this, function(evt) {
				dojo.stopEvent(evt);
				console.log('### submit search form');
				this.onSubmit(this.getValues());
				console.log('### search submitted');
			})
		}).placeAt(this.containerNode);

		// first create a table container which contains all search elements
		this._layoutContainer = new dojox.layout.TableContainer({
			cols: 2,
			showLabels: true,
			orientation: 'vert'
		});
		this._form.addChild(this._layoutContainer);

		// add the different search fields to the container
		dojo.forEach(this.fields, function(field) {
			this._layoutContainer.addChild(this._renderFormElement(field));
		}, this);

		// add 'search' button
		var buttonContainer = new umc2.widgets.ContainerWidget();
		buttonContainer.addChild(new dijit.form.Button({
			label: 'Search',
			type: 'submit',
			'class': 'submitButton'
		}));
	
		// add 'clear' button
		buttonContainer.addChild(new dijit.form.Button({
			label: 'Cancel',
			type: 'reset'
		}));

		// add an empty field and the two buttons (sharing one field)
		this._layoutContainer.addChild(new dijit._Widget());
		this._layoutContainer.addChild(buttonContainer);
		
		// call startup to make sure everything is rendered correctly
		this._layoutContainer.startup();
	},

	postCreate: function() {
		// call superclass' postCreate()
		this.inherited(arguments);
	},

	reset: function() {
		// description:
		//		Reset all form entries to their initial values.
		for (var el in this._formWidgets) {
			if ('reset' in this._formWidgets[el]) {
				el.reset();
			}
		}
	},

	getValues: function() {
		// description:
		//		Collect a property map of all currently entered/selected values.
		var map = {};
		console.log('### getValues');
		for (var el in this._formWidgets) {
			console.log(el);
			if ('value' in this._formWidgets[el]) {
				map[el] = this._formWidgets[el].get('value');
			}
		}
		console.log('### return');
		return map; // Object
	},

	onSubmit: function(/*Obj*/ properties) { 
		// description:
		//		Event handler for submission of the search formular.
		// properties:
		//		Property map where all current values of the search form are stored.
	}
});


