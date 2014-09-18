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
/*global define*/

define([
	'dojo/_base/declare',
	'dojo/_base/lang',
	'umc/dialog',
	'umc/tools',
	'umc/widgets/Form',
	'umc/widgets/Page',
	'umc/widgets/Text',
	'umc/widgets/TextArea',
	'umc/widgets/StandbyMixin',
	'umc/i18n!umc/modules/diagnostic'
], function(declare, lang, dialog, tools, Form, Page, Text, TextArea, StandbyMixin, _) {
	return declare('umc.modules.diagnostic.DetailPage', [Page, StandbyMixin], {
		
		moduleStore: null,
		timestampFormatter: null,
		summaryFormatter: null,
		resultFormatter: null,
		_form: null,

		postMixInProperties: function() {
			this.inherited(arguments);

			this.standbyOpacity = 1;

			this.headerText = _('Details of last test result');
			this.helpText = _('All available information about the test and the result of its last execution');

			this.footerButtons = [{
				name: 'back',
				label: _('Back to overview'),
				callback: lang.hitch(this, 'onClose')
			}];
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._form = new Form({
				widgets: [{
					type: TextArea,
					name: 'output',
					disabled: true,
					rows: 12,
					style: 'width: 100%;'
				}],
				layout: [{
					label: _('Test output'),
					layout: ['output']
				}],
				region: 'main',
				moduleStore: this.moduleStore,
				scrollable: true
			});

//			this._infos = new Text({
//				content: '',
//				region: 'nav'
//			});

//			this.addChild(this._infos);
			this.addChild(this._form);

			this.standbyDuring(this.moduleStore.get(this.plugin)).then(lang.hitch(this, function(object) {
				var content = lang.replace('<p><b>{0}: </b>{1}</p><p><b>{2}: </b>{3}</p><p><b>{4}: </b>{5}</p><p><b>{6}: </b>{7}</p><p><b>{8}: </b>{9}</p>', [
					_('Title'), object.title,
					_('Description'), object.description,
					_('Last executed'), this.timestampFormatter(object.timestamp),
					_('Result'), this.resultFormatter(object.result),
					_('Problem summary'), this.summaryFormatter(object.summary)
				]);

//				this._infos.set('content', content);
				this.set('helpText', content);
				this._form.getWidget('output').set('value', object.output || '');
			}));
		},

		onClose: function() {
			// event stub
		}
	});
});
