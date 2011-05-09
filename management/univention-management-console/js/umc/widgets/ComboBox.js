/*global dojo dijit dojox umc2 console window */

dojo.provide("umc.widgets.ComboBox");

dojo.require("dijit.form.ComboBox");
dojo.require("dojo.data.ItemFileReadStore");

dojo.declare( 
	"umc.widgets.ComboBox",
	[ dijit.form.ComboBoxMixin, dijit.form.ComboBox ],
	{
		constructor: function( label, values, default_key ) {
			var choices = {
				identifer : 'id',
				label : 'text',
				items: []
			};
			var default_value = null;
			dojo.forEach( values, function ( item ) {
							  choices[ 'items' ].push( { id: item[ 0 ], text: item[ 1 ] } );
							  if ( default_key != null && default_key == item[ 0 ] ) {
								  default_value = item[ 1 ];
							  }
						  } );

			this.store = new dojo.data.ItemFileReadStore( { data: choices } );
			console.log( "constructor ComboBox finished" );
			// return new dijit.form.ComboBox( { store: new dojo.data.ItemFileReadStore( { data: choices } ) } );
		}
	} );


