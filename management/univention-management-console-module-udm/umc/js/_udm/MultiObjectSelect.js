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
/*global dojo dijit dojox umc console */

dojo.provide('umc.modules._udm.MultiObjectSelect');

dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.MultiObjectSelect");

dojo.declare("umc.modules._udm.MultiObjectSelect", [ umc.widgets.MultiObjectSelect, umc.i18n.Mixin ], {
	// summary:
	//		This class extends the normal MultiObjectSelect in order to encapsulate
	//		some UDM specific behaviour.

	i18nClass: 'umc.modules.udm',

	objectType: '',

	autoSearch: true,

	umcpCommand: umc.tools.umcpCommand,

	queryWidgets: [],

	queryOptions: {},

	umcpCommand: umc.tools.ucmpCommand,

	queryCommand: function(options) {
        // return a dojo.Deferred
        options.syntax = this.syntax;
        return this.umcpCommand('udm/syntax/choices', options).then(function(data) {
            // return array of id-label-pairs directly
            return data.result
        });
    },


	// our formatter converts a list of DNs to a list with id-label-dict entries
	formatter: function(dnList) {
		var tmp = dojo.map(dnList, function(idn) {
			return {
				id: idn,
				label: umc.tools.explodeDn(idn, true).shift() || ''
			};
		});
		return tmp;
	},

	postMixInProperties: function() {
		this.inherited(arguments);

		// the default query options, all others will be read from the popup's search from
		this.queryOptions = {
			objectType: this.objectType,
			container: 'all'
		};

		// evaluate the UCR variables (from a global variable created by umc.modules.udm)
		var autoObjProperty = umc.modules._udm.ucr['directory/manager/web/modules/' + this.objectType + '/search/default'] || 
			umc.modules._udm.ucr['directory/manager/web/modules/default'];
		this.autoSearch = umc.tools.isTrue( 
			umc.modules._udm.ucr['directory/manager/web/modules/' + this.objectType + '/search/autosearch'] ||
				umc.modules._udm.ucr['directory/manager/web/modules/autosearch']
		);

		// specify the search form widgets
		this.queryWidgets = [{
			type: 'ComboBox',
			name: 'objectProperty',
			description: this._( 'The object property on which the query is filtered.' ),
			label: this._( 'Object property' ),
			dynamicValues: 'udm/properties',
			dynamicOptions: { searchable: true, objectType : this.objectType },
			umcpCommand: dojo.hitch(this, 'umcpCommand'),
			value: autoObjProperty, //TODO
			onChange: dojo.hitch(this, function(newVal) {
				// get the current label of objectPropertyValue
				var widget = this.getQueryWidget('objectProperty');
				var label = this._( 'Property value' );
				dojo.forEach(widget.getAllItems(), function(iitem) {
					if (newVal == iitem.id) {
						label = iitem.label;
						return false;
					}
				});

				// update the label of objectPropertyValue
				widget = this.getQueryWidget('objectPropertyValue');
				widget.set('label', label);
			})
		}, {
			type: 'MixedInput',
			name: 'objectPropertyValue',
			description: this._( 'The value for the specified object property on which the query is filtered.' ),
			label: this._( 'Property value' ),
			dynamicValues: 'udm/values',
			dynamicOptions: { objectType : this.objectType },
			umcpCommand: dojo.hitch(this, 'umcpCommand'),
			depends: [ 'objectProperty' ]
		}];
	}

	// _umcpCommand: function( /*String*/ commandStr, /*Object?*/ dataObj, /*Boolean?*/ handleErrors, /*String?*/ flavor ) {
	// 	return umc.tools.umcpCommand( commandStr, dataObj, handleErrors, this.objectType );
	// }
});
