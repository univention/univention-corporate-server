/*
 * Copyright 2018-2019 Univention GmbH
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
	"dijit/form/MappedTextBox",
	"umc/widgets/TextBoxMaxLengthChecker",
	"umc/modules/uvmm/types",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, MappedTextBox, TextBoxMaxLengthChecker, types, _) {
	return declare("umc.widgets.Text", [MappedTextBox], {
		// summary:
		//		A dojo mapped text box checks that a formatted value can be parsed back.
		//		That is often not possible from the formatted memory value, because the
		//		formatting is not lossless. In that case the box would reject the value.
		//		Workaround: a lossless cache

		cache: null,
		softMaxMessage: null,
		softMax: null,

		resetCache: function() {
			this.cache = {pretty2bytes: {}, bytes2pretty: {}};
		},

		postMixInProperties: function() {
			this.resetCache();
			this.inherited(arguments);
		},

		buildRendering: function() {
			this.inherited(arguments);
			if (this.softMax) {
				this.lengthChecker = new TextBoxMaxLengthChecker({
					usernameTooLong: lang.hitch(this, function() {
						return this.softMax <= types.parseCapacity(this.get('value'), this.defaultUnit);
					}),
					maxLength: this.softMax,
					warningMessage: this.softMaxMessage,
					textBoxWidget: this
				});
				//this.own(this.lengthChecker);
			}
		},

		constraints: {min: 4*1024*1024, max: 4*1024*1024*1024*1024},  // 4 MiB .. 4 TiB

		defaultUnit: null,

		format: function(val) {
			if (this.cache.bytes2pretty.hasOwnProperty(val)) {
				return this.cache.bytes2pretty[val];
			}
			var pretty = types.prettyCapacity(val, this.defaultUnit);
			this.cache.bytes2pretty[val] = pretty;
			this.cache.pretty2bytes[pretty] = val;
			return pretty;
		},

		parse: function(size) {
			if (this.cache.pretty2bytes.hasOwnProperty(size)) {
				return this.cache.pretty2bytes[size];
			}
			var mem = types.parseCapacity(size, this.defaultUnit);
			this.cache.pretty2bytes[size] = mem;
			this.cache.bytes2pretty[mem] = size;
			return mem;
		},

		validator: function(value, constraints) {
			var size = types.parseCapacity(value, this.defaultUnit);
			if (size === null) {
				return false;
			}
			if (constraints.min && size < constraints.min) {
				return false;
			}
			if (constraints.max && size > constraints.max) {
				return false;
			}
			return true;
		},

		invalidMessage: _('The memory size is invalid (e.g. 3GB or 1024 MB), minimum 4 MB, maximum 4 TB'),
	});
});
