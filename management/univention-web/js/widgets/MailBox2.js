/*
 * Copyright 2022 Univention GmbH
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
	"dojo/on",
	"dojo/when",
	"umc/widgets/ContainerWidget",
	"umc/widgets/TextBox",
	"umc/widgets/SuggestionBox",
	"umc/widgets/_FormWidgetMixin"
], function(declare, lang, on, when, ContainerWidget, TextBox, SuggestionBox, _FormWidgetMixin) {
	return declare("umc.widgets.MailBox2", [ ContainerWidget, _FormWidgetMixin ], {
		_setValueAttr: function(value) {
			const firstAtSign = value.indexOf('@')
			let mail = '';
			let domain = '';
			if (firstAtSign >= 0) {
				mail = value.slice(0, firstAtSign);
				domain = value.slice(firstAtSign+1);
			} else {
				mail = value;
			}
			this.pre.set('value', mail);
			this.suf.set('value', domain);
		},

		_getValueAttr: function() {
			let domain = this.suf.item2object(this.suf.item);
			domain = domain.label ?? '';
			return `${this.pre.get('value')}@${domain}`;
		},

		buildRendering: function() {
			this.inherited(arguments);
			this.domNode.style = 'display: flex; border: 1px solid var(--border-color); height: var(--inputfield-size); border-radius: var(--border-radius-interactable);';

			var pre = new TextBox({
				class: 'umcTextBoxOnBody',
				style: 'border: none; border-radius: 0.25rem 0 0 0.25rem; height: 100%',
				placeHolder: 'mail',
			});
			pre.on('input', lang.hitch(this, function(evt) {
				if (evt.key === '@') {
					evt.preventDefault();
					suf.focus();
				}
			}));

			var at = new TextBox({
				class: 'umcTextBoxOnBody atSign',
				value: '@',
				disabled: true,
				style: 'background: transparent; width: 3rem; height: 100%; border: none; border-radius: 0; border-top: 2px  solid var(--bgc-inputfield-on-body); border-bottom: 2px solid var(--bgc-inputfield-on-body);',
			});

			var suf = new SuggestionBox({
				class: 'umcTextBoxOnBody',
				dynamicValues: 'udm/syntax/choices',
				dynamicOptions: { syntax: 'MailDomains' },
				value: '',
				style: 'border: none; border-radius: 0 0.25rem 0.25rem 0; height: 100%;',
				placeHolder: 'example.com',
			});

			this.pre = pre;
			this.suf = suf;

			this.addChild(pre);
			this.addChild(at);
			this.addChild(suf);
		},
	});
});

