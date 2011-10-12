/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.ComplexInput");

dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.tools");
dojo.require("umc.render");

dojo.declare("umc.widgets.ComplexInput", umc.widgets.ContainerWidget, {
	// summary:
	//		Groups a set of widgets and returns the value of all widgets as a list

	// subtypes: Object[]
	//		Essentially an array of object that describe the widgets for one element
	//		of the MultiInput widget, the 'name' needs not to be specified, this
	//		property is passed to umc.render.widgets().
	subtypes: null,

	// the widget's class name as CSS class
	'class': 'umcComplexInput',

	_widgets: null,

	_container: null,

	_order: null,

	umcpCommand: umc.tools.umcpCommand,

	buildRendering: function() {
		this.inherited(arguments);

		var widgetConfs = [];
		this._order = [];

		dojo.forEach( this.subtypes, function( widget, i ) {
			// add the widget configuration dict to the list of widgets
			var iname = '__' + this.name + '-' + i;
			widgetConfs.push( dojo.mixin( {}, widget, {
				disabled: this.disabled,
				name: iname,
				value: '',
				dynamicValues: widget.dynamicValues,
				umcpCommand: this.umcpCommand
			}));

			// add the name of the widget to the list of widget names
			this._order.push(iname);
		}, this);

		// render the widgets and layout them
		this._widgets = umc.render.widgets( widgetConfs );
		this._container = umc.render.layout( [ this._order ], this._widgets );

		// register onChange event
		umc.tools.forIn( this._widgets, function( iname, iwidget ) {
			this.connect( iwidget, 'onChange', dojo.hitch( this, function( newValue ) {
				this.onChange( newValue, iname );
			} ) );
		}, this );

		// start processing the layout information
		this._container.placeAt(this.containerNode);
		this._container.startup();

		// call the _loadValues method by hand
		dojo.forEach( this._order, function( iname ) {
			var iwidget = this._widgets[ iname ];
			if ( '_loadValues' in iwidget ) {
				iwidget._loadValues( this._lastDepends );
			}
		}, this);

	},

	_getValueAttr: function() {
		var vals = [];
		dojo.forEach( this._order, function( iname ) {
			vals.push( this._widgets[ iname ].get( 'value' ) );
		}, this );

		return vals;
	},

	_setValueAttr: function( value ) {
		dojo.forEach( this._order, function( iname, i ) {
			this._widgets[ iname ].set( 'value', value[ i ] );
		}, this );
	},

	// provide 'onChange' method stub in case it does not exist yet
	onChange: function( newValue, widgetName ) {
		console.log( 'INFO: ComplexInput: onChange ' + newValue );
		// event stub
	},

	setValid: function(/*Boolean|Boolean[]*/ areValid, /*String?|String[]?*/ messages) {
		// summary:
		//		Set all child elements to valid/invalid.
		dojo.forEach( this._order, function( iname, i ) {
			var imessage = dojo.isArray(messages) ? messages[i] : messages;
			var iisValid = dojo.isArray(areValid) ? areValid[i] : areValid;
			this._widgets[ iname ].setValid( iisValid, imessage );
		}, this );
	}
});


