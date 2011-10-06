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

	queryWidgets: [],

	queryOptions: {},

	queryCommand: function(options) {
		// return a dojo.Deferred
		return umc.tools.umcpCommand('udm/query', options).then(function(data) {
			// transform query to array with id-label-dict entries
			return dojo.map(data.result, function(iobj) {
				return {
					id: iobj.$dn$, // the object's LDAP DN
					label: iobj.name // for now the label is the object's identity property
				};
			});
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
		var autoSearch = umc.modules._udm.ucr['directory/manager/web/modules/' + this.objectType + '/search/autosearch'] ||
			umc.modules._udm.ucr['directory/manager/web/modules/autosearch'];

		// specify the search form widgets
		this.queryWidgets = [{
			type: 'ComboBox',
			name: 'objectProperty',
			description: this._( 'The object property on which the query is filtered.' ),
			label: this._( 'Object property' ),
			dynamicValues: 'udm/properties',
			dynamicOptions: { searchable: true },
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
			umcpCommand: dojo.hitch(this, 'umcpCommand'),
			depends: [ 'objectProperty' ]
		}];
	},

	umcpCommand: function( /*String*/ commandStr, /*Object?*/ dataObj, /*Boolean?*/ handleErrors, /*String?*/ flavor ) {
		return umc.tools.umcpCommand( commandStr, dataObj, handleErrors, flavor || this.objectType );
	}
});
