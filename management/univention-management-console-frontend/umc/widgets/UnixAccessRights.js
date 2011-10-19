/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.UnixAccessRights");

dojo.require( "dijit.form.CheckBox" );
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets._FormWidgetMixin");
dojo.require("umc.tools");
dojo.require("umc.i18n");
dojo.require("umc.render");

dojo.declare("umc.widgets.UnixAccessRights", [ umc.widgets.ContainerWidget, umc.widgets._FormWidgetMixin, umc.i18n.Mixin ], {
	// summary:
	//		Displays a matrix of UNIX access rights

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

	i18nClass: 'umc.app',

	disabled: false,

	_widgets: null,

	_container: null,

	buildRendering: function() {
		this.inherited(arguments);

		// create widgets
		this.widgets = [
			{ type: 'Text', name: 'ownerLabel', content: this._( 'Owner' ) },
			{ type: 'Text', name: 'groupLabel', content: this._( 'Group' ) },
			{ type: 'Text', name: 'otherLabel', content: this._( 'Others' ) }
		];
		dojo.forEach( [ 'owner', 'group', 'other' ], dojo.hitch( this, function( item ) {
			this.widgets.push( { type: 'CheckBox', name: item + 'Read', disabled: this.disabled } );
			this.widgets.push( { type: 'CheckBox', name: item + 'Write', disabled: this.disabled } );
			this.widgets.push( { type: 'CheckBox', name: item + 'Execute', disabled: this.disabled } );
		} ) );

		this.widgets = this.widgets.concat( [
			{
				type: 'Text',
				name: 'read',
				content: this._( 'Read' )
			},
			{
				type: 'Text',
				name: 'write',
				content: this._( 'Write' )
			},
			{
				type: 'Text',
				name: 'access',
				content: this._( 'Access' )
			},
			{
				type: 'Text',
				name: 'empty',
				content: ''
			}
		] );
		this._widgets = umc.render.widgets( this.widgets );

		this._container = new dojox.layout.TableContainer( { cols : 4, customClass: 'umcUNIXAccessRights', showLabels: false } );

		// first row
		this._container.addChild( this._widgets.empty );
		this._container.addChild( this._widgets.read );
		this._container.addChild( this._widgets.write );
		this._container.addChild( this._widgets.access );
		// other rows
		dojo.forEach( [ 'owner', 'group', 'other' ], dojo.hitch( this, function( item ) {
			this._container.addChild( this._widgets[ item + 'Label' ] );
			this._container.addChild( this._widgets[ item + 'Read' ] );
			this._container.addChild( this._widgets[ item + 'Write' ] );
			this._container.addChild( this._widgets[ item + 'Execute' ] );
		} ) );

		// register onChange event
		umc.tools.forIn( this._widgets, function( iname, iwidget ) {
			if ( 'Text' == iwidget.type ) { // ignore labels
				return;
			}
			this.connect( iwidget, 'onChange', dojo.hitch( this, function( newValue ) {
				this.onChange( newValue, iname );
			} ) );
		}, this );
		// start processing the layout information
		this._container.placeAt(this.containerNode);
		this._container.startup();
	},

	_getValueAttr: function() {
		var rights = 0;

		dojo.forEach( [ 'owner', 'group', 'other' ], dojo.hitch( this, function( item ) {
			rights += this._widgets[ item + 'Execute' ].get( 'checked' ) ? 1 : 0;
			rights += this._widgets[ item + 'Write' ].get( 'checked' ) ? 2 : 0;
			rights += this._widgets[ item + 'Read' ].get( 'checked' ) ? 4 : 0;
			rights <<= 3;
		} ) );

		rights >>= 3;

		return '0' + rights.toString( 8 );
	},

	_setValueAttr: function( value ) {
		var rights = parseInt( value, 8 );

		dojo.forEach( [ 'other', 'group', 'owner' ], dojo.hitch( this, function( item ) {
			this._widgets[ item + 'Execute' ].set( 'checked', rights & 1 );
			this._widgets[ item + 'Write' ].set( 'checked', rights & 2 );
			this._widgets[ item + 'Read' ].set( 'checked', rights & 4 );
			rights >>= 3;
		} ) );
	},

	// provide 'onChange' method stub in case it does not exist yet
	onChange: function( newValue, widgetName ) {
		// event stub
	}

});


