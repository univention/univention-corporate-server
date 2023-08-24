/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2020-2023 Univention GmbH
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
/*global define console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Text",
	"umc/widgets/TitlePane",
	"./AppSettingsForm",
], function(declare, lang, array, ContainerWidget, Text, TitlePane, AppSettingsForm) {
	return declare("umc.modules.appcenter.AppSettingsFormAdvanced", [ ContainerWidget ], {
		_forms: null,

		buildRendering: function() {
			this.inherited(arguments);

			this._forms = [];

			array.forEach(this.groups, lang.hitch(this, function(group) {
				var pane = new TitlePane({
					title: group.title,
				});
				this.addChild(pane);

				if (group.description) {
					pane.addChild(new Text({
						content: group.description,
						'class': 'appSettingsGroupDescription'
					}));
				}

				var form = new AppSettingsForm({widgets: group.widgets});
				this._forms.push(form);
				pane.addChild(form);
			}));
		},

		validate: function() {
			var success = true;
			array.forEach(this._forms, function(form) {
				if (! form.validate()) {
					success = false;
				}
			});
			return success;
		},

		focusFirstInvalidWidget: function() {
			array.forEach(this._forms.toReversed(), function(form) {
				form.focusFirstInvalidWidget();
			});
		},

		_getValueAttr: function() {
			var values = {};
			array.forEach(this._forms, function(form) {
				values = {...values, ...form.get('value')};
			});
			return values;
		},
	});
});

