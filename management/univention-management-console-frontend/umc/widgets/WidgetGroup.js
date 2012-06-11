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


