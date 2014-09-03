/*
 * Copyright 2011-2014 Univention GmbH
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
	'umc/i18n!umc/modules/supphealth'
], function(declare, lang, dialog, tools, Form, Page, Text, TextArea, StandbyMixin, _) {
	return declare('umc.modules.supphealth.DetailPage', [ Page, StandbyMixin ], {
		
		// UMC API helper class for backend communication
		moduleStore: null,

		timestampFormatter: null,

		summaryFormatter: null,
		
		resultFormatter: null,

		_form: null,

		postMixInProperties: function() {
			// is called after all inherited properties/methods have been mixed
			// into the object (originates from dijit._Widget)

			// it is important to call the parent's postMixInProperties() method
			this.inherited(arguments);

			// Set the opacity for the standby animation to 100% in order to mask
			// GUI changes when the module is opened. Call this.standby(true|false)
			// to enable/disable the animation.
			this.standbyOpacity = 1;

			// set the page header
			this.headerText = _('Details of last test result');
			this.helpText = _('All available information about the test and the result of it\'s last execution');

			// configure buttons for the footer of the detail page
			this.footerButtons = [{
				name: 'back',
				label: _('Back to overview'),
				callback: lang.hitch(this, 'onClose')
			}];
		},

		buildRendering: function() {
			// is called after all DOM nodes have been setup
			// (originates from dijit._Widget)

			// it is important to call the parent's postMixInProperties() method
			this.inherited(arguments);
			this.renderDetailPage();
		},

		renderDetailPage: function() {
			// render the form containing all detail information that may be edited

			// specify all widgets
			var widgets = [{
				type: Text,
				name: 'test_header',
				disabled: true
			}, {
				type: TextArea,
				name: 'output',
				disabled: true,
				style: 'width: 100%; height: 500px'
			}];

			// specify the layout... additional dicts are used to group form elements
			// together into title panes
			var layout = [{
				label: _('Test information'),
				layout: ['test_header']
			}, {
				label: _('Test output'),
				layout: ['output']
			}];

			// create the form
			this._form = new Form({
				widgets: widgets,
				layout: layout,
				moduleStore: this.moduleStore,
				// alows the form to be scrollable when the window size is not large enough
				scrollable: true
			});

			// add form to page... the page extends a BorderContainer, by default
			// an element gets added to the center region
			this.addChild(this._form);
		},

		load: function(id) {
			// run load animation
			this.standby(true);

			this.moduleStore.get(id).then(lang.hitch(this, function(object) {
				// stop load animation
				this.standby(false);

				// fill test header child widget with request result
				this._form._widgets['test_header'].set('content','<p><b>'+_('Title')+': </b>'+object.title+'</p><p><b>'+_('Description')+': </b>'+object.description+'<p><p><b>'+_('Last executed')+': </b>'+this.timestampFormatter(object.timestamp)+'</p><p><b>'+_('Result')+': </b>'+this.resultFormatter(object.result)+'</p><br/><p><b>'+_('Problem summary')+': </b>'+this.summaryFormatter(object.summary)+'</p>');

				if(object.output)
					this._form._widgets['output'].set('value', object.output);
				else
					this._form._widgets['output'].set('value', '');

			}), lang.hitch(this, function() {
				// error handler: switch of the standby animation
				// error messages will be displayed automatically
				this.standby(false);
			}));
		},

		onClose: function() {
			// event stub
		}
	});
});
