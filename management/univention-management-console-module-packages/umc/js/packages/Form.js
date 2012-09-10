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
/*global define console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/on",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Form",
	"umc/i18n!umc/modules/packages" // not used atm
], function(declare, lang, on, tools, dialog, Form, _) {
	return declare("umc.modules.packages.Form", [ Form ], {
		save: function() {
			tools.assert(this.moduleStore, 'In order to save form data to the server, the umc.widgets.Form.moduleStore needs to be set');

			var values = this.gatherFormValues();
			var deferred = null;
			if (this._loadedID === null || this._loadedID === undefined || this._loadedID === '') {
				deferred = this.moduleStore.add(values);
			}
			else {
				var options = {};
				var idProperty = lang.getObject('moduleStore.idProperty', false, this);
				if (idProperty) {
					options[idProperty] = this._loadedID;
				}
				deferred = this.moduleStore.put(values, options);
			}
			deferred = deferred.then(lang.hitch(this, function(data) {
				/*
				 * BEGIN CHANGED
				 * if validation error status (400)
				 * trigger onValidationError event
				 */
				if (data && parseInt(data.status, 10) == 400) {
					this.onValidationError(data.result);
					return data;
				} else {
					this.onSaved(true);
					return data;
				}
				/*
				 * END CHANGED
				 */

			}), lang.hitch(this, function() {
				this.onSaved(false);
			}));

			return deferred;
		},

		/*
		 * NEW
		 */
		onValidationError: function(/*Object*/ data) {
			// naive implementation
			var focus_set = false;
			tools.forIn(data, lang.hitch(this, function(iwidget, error_msg) {
				var worked = false;
				try {
					// TODO: return true in setValid
					// except for our checkBox
					// or (better) implement setValid for checkBox
					var widget = this.getWidget(iwidget);
					if (widget && widget['class'] != 'umcCheckBox') {
						widget.setValid(false, error_msg);
						//if (!focus_set) {
						//	widget.focus();
						//	focus_set = true;
						//}
						//on.once('keyup', function() {
						//	widget.setValid(true);
						//});
						worked = true;
					}
				} catch(e) {
					console.log(iwidget, e);
				}
				if (!worked) {
					// notify is buggy (adding messages
					// during animation). maybe use <ul> in alert?
					dialog.notify(error_msg);
				}
			}));
			this.onSaved(false);
		}

	});
});
