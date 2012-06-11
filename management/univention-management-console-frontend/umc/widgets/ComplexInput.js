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
				this.onChange( this.get( 'value' ), iname );
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


