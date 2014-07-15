/*
 * Copyright 2014 Univention GmbH
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

/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dijit/form/RadioButton",
	"dijit/registry",
	"umc/tools",
	"umc/widgets/_FormWidgetMixin",
	"umc/widgets/ContainerWidget",
	"umc/widgets/LabelPane"
], function(declare, lang, array, RadioButton, registry, tools, _FormWidgetMixin, ContainerWidget, LabelPane) {
	return declare("umc.modules.uccsetup.RadioButton", [ RadioButton, _FormWidgetMixin ], {
		value: null,

		// name: String
		//		Should be different for each radio button, so that it can be layout
		//		idependently.
		name: null,

		// radioButtonGroup: String
		//		Specifies the group of radio buttons that shares one value.
		radioButtonGroup: null,

		// the widget's class name as CSS class
		'class': 'umcRadioButton',

		postMixInProperties: function() {
			if (!this.value) {
				this.value = this.name;
			}
			this.name = this.radioButtonGroup;
			this.inherited(arguments);
			this.valid = false;
			this.sizeClass = null;
		},

		_getRelateWidgets: function() {
			// summary:
			//		Return all widgets of the same radio button group.
			var form = registry.getEnclosingWidget(this.focusNode.form);
			var relatedWidgets = [];
			tools.forIn(form._widgets, function(key, widget) {
				if (widget.radioButtonGroup == this.radioButtonGroup) {
					relatedWidgets.push(widget);
				}
			}, this);
			return relatedWidgets;
		},

		_getValueAttr: function() {
			return Boolean(this.inherited(arguments));
		},

		_getValidAttr: function() {
			var checkButtons = array.filter(this._getRelateWidgets(), function(iwidget) {
				return iwidget.get('checked');
			});
			return checkButtons.length == 1;
		}
	});
});

