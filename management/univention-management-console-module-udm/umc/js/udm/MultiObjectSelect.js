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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/tools",
	"umc/widgets/MultiObjectSelect",
	"umc/widgets/MixedInput",
	"umc/widgets/CheckBox",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, array, tools, MultiObjectSelect, MixedInput, CheckBox, _) {
	return declare("umc.modules.udm.MultiObjectSelect", [ MultiObjectSelect ], {
		// summary:
		//		This class extends the normal MultiObjectSelect in order to encapsulate
		//		some UDM specific behavior.

		objectType: '',

		autoSearch: true,

		umcpCommand: lang.hitch(tools, 'umcpCommand'),

		queryWidgets: [],

		queryOptions: {},

		queryCommand: function(options) {
			// return a Deferred
			options.syntax = this.syntax;
			return this.umcpCommand('udm/syntax/choices', options).then(function(data) {
				// return array of id-label-pairs
				return data.result;
			});
		},


		// our formatter converts a list of DNs to a list with id-label-dict entries
		formatter: function(entries) {
			var tmp = array.map(entries, function(ientry) {
				if (typeof ientry == 'string') {
					return {
						id: ientry,
						label: tools.explodeDn(ientry, true).shift() || ''
					};
				}
				if (ientry.id && !ientry.label) {
					return {
						id: ientry.id,
						label: tools.explodeDn(ientry.id, true).shift() || ''
					};
				}
				return ientry;
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

			// evaluate the UCR variables (from a global variable created by umc/modules/udm)
			var ucr = lang.getObject('umc.modules.udm.ucr', false) || {};
			var autoObjProperty = ucr['directory/manager/web/modules/' + this.objectType + '/search/default'] ||
				ucr['directory/manager/web/modules/default'];
			this.autoSearch = tools.isTrue(
				ucr['directory/manager/web/modules/' + this.objectType + '/search/autosearch'] ||
					ucr['directory/manager/web/modules/autosearch']
			);

			// specify the search form widgets
			this.queryWidgets = [{
				type: 'ComboBox',
				name: 'objectProperty',
				label: _( 'Object property' ),
				staticValues: [{id: 'None', label: _('Default properties')}],
				dynamicValues: 'udm/properties',
				dynamicOptions: { searchable: true, objectType : this.objectType },
				umcpCommand: lang.hitch(this, 'umcpCommand'),
				value: autoObjProperty, //TODO
				onChange: lang.hitch(this, function(newVal) {
					// get the current label of objectPropertyValue
					var widget = this.getQueryWidget('objectProperty');
					var label = _( 'Property value' );
					array.forEach(widget.getAllItems(), function(iitem) {
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
				type: MixedInput,
				name: 'objectPropertyValue',
				label: _( 'Property value' ),
				dynamicValues: 'udm/values',
				dynamicOptions: { objectType : this.objectType },
				umcpCommand: lang.hitch(this, 'umcpCommand'),
				depends: [ 'objectProperty' ]
			}, {
				type: CheckBox,
				name: 'hidden',
				visible: true,
				size: 'Two',
				label: _('Include hidden objects'),
				value: false
			}];
		}

		// _umcpCommand: function( /*String*/ commandStr, /*Object?*/ dataObj, /*Boolean?*/ handleErrors, /*String?*/ flavor ) {
		// 	return tools.umcpCommand( commandStr, dataObj, handleErrors, this.objectType );
		// }
	});
});

