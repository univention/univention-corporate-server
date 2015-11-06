/*
 * Copyright 2015 Univention GmbH
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
/*global define require console window */

define([
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom",
	"put-selector/put",
	"./RadioButton",
	"./LabelPane",
	"./passwordchange",
	"./passwordreset",
	"./setcontactinformation",
	"./lib",
	"./i18n!."
], function(lang, array, dom, put, RadioButton, LabelPane, PasswordChange, PasswordReset, SetContactInformation, lib, _) {

	return {
		_createTitle: function() {
			var title = _('Password self-service');
			var siteDescription = _('Welcome to the Password self-service. On this site you can reset and change your password. Please select an option to get more information.');
			document.title = title;
			var titleNode = dom.byId('title');
			put(titleNode, 'h1', title);
			put(titleNode, 'p', siteDescription);
			put(titleNode, '!.dijitHidden');
		},

		_createContent: function() {
			var contentNode = dom.byId('content');

			var optionsNode = put(content, 'div[id=options]');
			var options = [{
				name: 'changePassword',
				content: PasswordChange._getFormNode(),
				label: _('I want to change my (expired) password.')
			},{
				name: 'resetPassword',
				content: PasswordReset._getFormNode(),
				label: _('I have forgotten my password.')
			},{
				name: 'setContactInformation',
				content: SetContactInformation._getFormNode(),
				label: _('I would like to set my contact information for resetting my password.')
			}];
			array.forEach(options, function(option) {
				var optNode = put(optionsNode, 'div');
				var radioButton = new RadioButton({
					name: option.name,
					label: option.label,
					checked: false,
					radioButtonGroup: 'options',
					_categoryID: 'options'
				});
				var label = new LabelPane({
					'class': 'ucsRadioButtonLabel',
					content: radioButton
				});
				put(optNode, label.domNode);
				if (option.content) {
					var height = lib.getNodeHeight(option.content);
					put(optNode, option.content, '.fadeInit');
					radioButton.watch('checked', function(attr, oldValue, newValue){
						if (newValue) { // radioButton is checked
							lib.fadeInNode({node: option.content, endHeight: height});
						} else {
							lib.fadeOutNode({ node: option.content, startHeight: height});
						}
					});
				}
			});
		},

		start: function() {
			this._createTitle();
			this._createContent();
		}
	};
});
