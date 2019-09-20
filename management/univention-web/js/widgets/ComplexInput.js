/*
 * Copyright 2011-2019 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/promise/all",
	"umc/tools",
	"umc/render",
	"umc/widgets/ContainerWidget"
], function(declare, lang, array, all, tools, render, ContainerWidget) {
	return declare("umc.widgets.ComplexInput", ContainerWidget, {
		// summary:
		//		Groups a set of widgets and returns the value of all widgets as a list

		baseClass: 'umcComplexInput',

		// subtypes: Object[]
		//		Essentially an array of object that describe the widgets for one element
		//		of the MultiInput widget, the 'name' needs not to be specified, this
		//		property is passed to render.widgets().
		subtypes: null,

		displayLabel: false,

		_widgets: null,

		_container: null,

		_order: null,

		umcpCommand: lang.hitch(tools, 'umcpCommand'),

		_allReady: null,

		constructor: function() {
			// initialize with empty list
			this._allReady = [];
		},

		buildRendering: function() {
			this.inherited(arguments);

			var widgetConfs = [];
			this._order = [];

			array.forEach( this.subtypes, function(widget, i) {
				// add the widget configuration dict to the list of widgets
				var iname = '__' + this.name + '-' + i;
				var iconf = lang.mixin({}, widget, {
					disabled: this.disabled,
					threshold: this.threshold, // for UDM-threshold
					name: iname,
					dynamicValues: widget.dynamicValues,
					umcpCommand: lang.hitch(this, 'umcpCommand'),
					required: this.required
				});

				// if no label is given, set the main label as label
				// of the first subwidget
				iconf.label = iconf.label || (i === 0 && this.label ? this.label : '&nbsp;');

				widgetConfs.push(iconf);

				// add the name of the widget to the list of widget names
				this._order.push(iname);
			}, this);

			// render the widgets and layout them
			this._widgets = render.widgets( widgetConfs, this );
			this._container = render.layout( [ this._order ], this._widgets );

			// register for value changes
			tools.forIn(this._widgets, function(iname, iwidget) {
				this.own(iwidget.watch('value', lang.hitch(this, function(name, oldValue, newValue) {
					this._set('value', this.get('value'));
				})));
			}, this);

			// start processing the layout information
			this._container.placeAt(this.containerNode);
			this._container.startup();

			this._updateAllReady();
		},

		_getValueAttr: function() {
			var vals = [];
			array.forEach( this._order, function( iname ) {
				vals.push( this._widgets[ iname ].get( 'value' ) );
			}, this );

			return vals;
		},

		_setValueAttr: function( value ) {
			array.forEach( this._order, function( iname, i ) {
				this._widgets[ iname ].set( 'value', value[ i ] );
			}, this );
			this._set('value', value);
		},

		setInitialValue: function(value, setValue) {
			setValue = undefined === setValue ? true : setValue;
			array.forEach(this._order, function(iname, i) {
				var widget = this._widgets[iname];
				if (widget.setInitialValue) {
					widget.setInitialValue(value[i], setValue);
				}
			}, this);
			if (setValue) {
				this.set('value', value);
			}
		},

		setValid: function(/*Boolean|Boolean[]*/ areValid, /*String?|String[]?*/ messages) {
			// summary:
			//		Set all child elements to valid/invalid.
			array.forEach( this._order, function( iname, i ) {
				var imessage = messages instanceof Array ? messages[i] : messages;
				var iisValid = areValid instanceof Array ? areValid[i] : areValid;
				this._widgets[ iname ].setValid( iisValid, imessage );
			}, this );
		},

		_updateAllReady: function() {
			// wait for all widgets to be ready
			this._allReady = [];
			tools.forIn(this._widgets, function(iname, iwidget) {
				this._allReady.push(iwidget.ready ? iwidget.ready() : null);
			}, this);
		},

		ready: function() {
			// update the internal list in order to wait until everybody is ready
			if (!this._allReady.length) {
				this._updateAllReady();
			}
			var ret = all(this._allReady);

			// empty list when all widgets are ready
			ret.then(lang.hitch(this, function() {
				this._allReady = [];
			}));
			return ret;
		}
	});
});

