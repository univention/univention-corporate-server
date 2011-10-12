/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.WidgetGroup");

dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.tools");
dojo.require("umc.render");

dojo.declare("umc.widgets.WidgetGroup", umc.widgets.ContainerWidget, {
	// summary:
	//		Groups a set of widgets and returns the value of all widgets as a dictionary

	// widgets: Object[]|dijit.form._FormWidget[]|Object
	//		Array of config objects that specify the widgets that are going to
	//		be used in the form. Can also be a list of dijit.form._FormWidget
	//		instances or a dictionary with name->Widget entries in which case
	//		no layout is rendered and `content` is expected to be specified.
	widgets: null,

	// layout: String[][]?
	//		Array of strings that specifies the position of each element in the
	//		layout. If not specified, the order of the widgets is used directly.
	//		You may specify a widget entry as `undefined` or `null` in order
	//		to leave a place free.
	layout: null,

	_widgets: null,

	_container: null,

	buildRendering: function() {
		this.inherited(arguments);

		// render the widgets and the layout if no content is given
		this._widgets = umc.render.widgets( this.widgets );
		this._container = umc.render.layout( this.layout, this._widgets );

		// register onChange event
		umc.tools.forIn( this._widgets, function( iname, iwidget ) {
			this.connect( iwidget, 'onChange', dojo.hitch( this, function( newValue ) {
				this.onChange( newValue, iname );
			} ) );
		}, this );
		// start processing the layout information
		this._container.placeAt(this.containerNode);
		this._container.startup();
	},

	_getValueAttr: function() {
		var vals = {};
		umc.tools.forIn( this._widgets, function( iname, iwidget ) {
			vals[ iname ] = iwidget.get( 'value' );
		}, this );

		return vals;
	},

	_setValueAttr: function( value ) {
		umc.tools.forIn( this._widgets, function( iname, iwidget ) {
			if (iname in value) {
				iwidget.set( 'value', value[ iname ] );
			}
		}, this );
	},

	// provide 'onChange' method stub in case it does not exist yet
	onChange: function( newValue, widgetName ) {
		// event stub
	}

});


