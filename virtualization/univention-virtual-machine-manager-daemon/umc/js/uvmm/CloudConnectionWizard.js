/*
 * Copyright 2014-2019 Univention GmbH
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
	"umc/dialog",
	"umc/widgets/TextBox",
	"umc/widgets/PasswordBox",
	"umc/widgets/ComboBox",
	"umc/widgets/CheckBox",
	"umc/widgets/HiddenInput",
	"umc/widgets/Wizard",
	"umc/widgets/Form",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, tools, dialog, TextBox, PasswordBox, ComboBox, CheckBox, HiddenInput, Wizard, Form, _) {

	return declare("umc.modules.uvmm.CloudConnectionWizard", [ Wizard ], {

		buildRendering: function() {
			this.pages.push({
				name: 'pre_finish',
				widgets: []
			});
			this.inherited(arguments);
		},

		postMixInProperties: function() {
			this.inherited(arguments);

			this.headerButtons = [{
				name: 'close',
				iconClass: 'umcCloseIconWhite',
				label: _('Back to overview'),
				callback: lang.hitch(this, 'onCancel')
			}];
		},

		getFooterButtons: function(pageName) {
			var buttons = this.inherited(arguments);
			var pages = this.pages;
			//if (pageName === pages[pages.length - 2].name) {
			//	buttons.next.label = _('Finish');
			//}
			return array.map(buttons, function(button) {
				if (pageName === pages[pages.length - 2].name && button.name == 'next') {
					button.label = _('Finish');
				}
				return button;
			});
		},

		_testConnection: function(values) {
			this.standby(true);
			return tools.umcpCommand('uvmm/cloud/add', {
				cloudtype: values.cloudtype,
				name: values.name,
				testconnection: true,
				parameter: values
			}).then(lang.hitch(this, function(response) {
				this.moduleStore.onChange();
				this.standby(false);
				this.onFinished(response, values);
			}), lang.hitch(this, function(errormsg) {
				this.standby(false);
				dialog.alert('Error: ' + errormsg);
				return 'credentials';
			}));
		},

		next: function(currentPage) {
			var nextPage = this.inherited(arguments);
			if (nextPage === 'pre_finish') {
				return this._testConnection(this.getValues());
			}
			return nextPage;
		}

	});
});
