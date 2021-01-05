/*
 * Copyright 2011-2021 Univention GmbH
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
/*global define,console*/
/*jshint -W089 */

// Form with some useful additions:
//
//	-	add the capability of passing options to the 'put' method
//		of the underlying store
//	-	add the capability of passing back the results of a 'put'
//		call to the 'onSaved' event handlers.
//	-	add a method that takes a dict of 'field' -> 'text' mappings
//		that have to be turned into 'not valid' indicators at the
//		corresponding fields
//

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/aspect",
	"umc/tools",
	"umc/widgets/Form",
	"umc/widgets/StandbyMixin",
	"umc/i18n!umc/modules/updater"
], function(declare, lang, aspect, tools, Form, StandbyMixin, _) {
	return declare("umc.modules.updater.Form", [ Form, StandbyMixin],
	{
		// can be called in the onSave hook to set error flags and messages
		// for individual fields.
		// can be called without args to clear all error indicators
		//
		// as a side effect, sets the focus either to the first invalid field (if any)
		// or the first field at all.
		applyErrorIndicators: function(values) {
			var firstname = '';
			var errname = '';
			for (var field in this._widgets) {
				if (firstname === '') {
					firstname = field;
				}
				try {
					var widget = this._widgets[field];
					if (typeof(widget.setValid) == 'function') {
						if ((values) && (values[field])) {
							widget.setValid(false, values[field]);
							if (errname === '') {
								errname = field;
							}
						} else {
							widget.setValid(null);
						}
					}
				} catch(error) {
					console.error("applyErrorIndicators failed for field '" + field + "': " + error.message);
				}
			}
			// set the focus to the given field.
			var focus = errname;
			// not really useful: depending on NEW or EDIT we would
			// want a different field to be focused.
			//if (focus == '') { focus = firstname; }

			if (focus !== '') {
				this._widgets[focus].focus();
				// Our focus is not kept... we see it and then something takes control...
				// Which event do we have to tack the focus() action on?
				//			this.on('whichEvent?', lang.hitch(this, function() {
				//				this._widgets[focus].focus();
				//			}));
			}
		},

		save: function(options) {
			// summary:
			//			  Gather all form values and send them to the server via UMCP.
			//			  For this, the field umcpSetCommand needs to be set.

			tools.assert(this.moduleStore, 'In order to save form data to the server, the umc.widgets.Form.moduleStore needs to be set');

			// sending the data to the server
			var values = this.get('value');

			// *** CHANGED *** propagate an 'options' dict to the 'put' call of the moduleStore
			// *** CHANGED *** propagate the result of the put operation to the 'onSaved' callback
			var deferred = this.moduleStore.put(values, options).then(lang.hitch(this, function(result) {
				this.onSaved(true, result);
			}), lang.hitch(this, function(result) {
				this.onSaved(false, result);
			}));

			return deferred;
		},

		buildRendering: function() {
			this.inherited(arguments);

			// It is important that error indicators get reset if data from
			// the store has been loaded, but also if setFormValues() is called
			// manually (e.g. to fill a 'new' form with initial values)
			this.own(aspect.after(this, 'setFormValues', lang.hitch(this, function() {
				this.applyErrorIndicators({});
			})));

			this.on('saved', lang.hitch(this, function(success, data) {
				if (success) { // this is only Python module result, not data validation result!
					var result = data;
					if (data instanceof Array) {
						result = data[0];
					}
					// *** CHANGED *** We don't display the message here since
					//		we don't have the detailed knowledge what the errors
					//		and error codes mean.
					if (result.status) {
						this.applyErrorIndicators(result.object);
					}
				}
			}));
		},

		// Two callbacks that are used by queries that want to propagate
		// their outcome to the main error handlers
		onQueryError: function(subject, data) {
		},
		onQuerySuccess: function(subject) {
		}
	});
});
