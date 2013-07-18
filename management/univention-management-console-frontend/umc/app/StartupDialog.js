/*
 * Copyright 2013 Univention GmbH
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
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/kernel",
	"dojo/_base/array",
	"dojo/parser",
	"dojo/dom-class",
	"dojo/Deferred",
	"dojo/when",
	"dijit/Dialog",
	"dijit/layout/StackContainer",
	"umc/tools",
	"umc/widgets/Text",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Button",
	"umc/i18n!umc/app"
], function(declare, lang, kernel, array, parser, domClass, Deferred, when, Dialog, StackContainer, tools, Text, ContainerWidget, Button, _) {
	var _lang = kernel.locale.split('-')[0];
	var _getDocumentDependency = function(key) {
		return lang.replace('dojo/text!umc/app/{key}.{lang}.html', {
			key: key,
			lang: _lang
		});
	};

	// pre-load HTML template documents
	var _docDeferred = new Deferred();
	var _docDependencies = array.map(['welcome', 'feedback', 'help'], _getDocumentDependency);
	require(_docDependencies, function(/*...*/) {
		_docDeferred.resolve(arguments);
	});

	var _replaceVariablesInDocument = function(piwikDisabled, doc) {
		return lang.replace(doc, {
			path: require.toUrl('umc/app'),
			feedbackUrl: _('umcFeedbackUrl'),
			enablePiwikChecked: piwikDisabled ? '' : 'checked'
		});
	};

	return declare(Dialog, {
		// summary:
		//		The dialog which is shown during the first login of Administrator.

		title: 'Willkommen bei UMC',

		_stackContainer: null,

	   _pages: null,

		_gotoPage: function(idx) {
			this._stackContainer.selectChild(this._pages[idx]);
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._stackContainer = new StackContainer({
				'class': 'umcPopup'
			});

			this._pages = [];
			when(_docDeferred, lang.hitch(this, function(_docs) {
				// note that way can only access 'piwikDisabled' here, as we cannot
				// be sure that the variable has been set before (in umc/app)
				var docs = array.map(_docs, lang.hitch(this, _replaceVariablesInDocument, tools.status('piwikDisabled')));
				array.forEach(docs, function(idoc, idx) {
					// build footer
					var footer = new ContainerWidget({
						'class': 'umcPageFooter',
						style: 'overflow:auto;'
					});

					// 'next' button
					if (idx < docs.length - 1) {
						footer.addChild(new Button({
							label: _('Next'),
							callback: lang.hitch(this, '_gotoPage', idx + 1),
							style: 'float:right',
							defaultButton: true
						}));
					}

					// 'close' button
					if (idx == docs.length - 1) {
						footer.addChild(new Button({
							label: _('Close'),
							callback: lang.hitch(this, 'close'),
							style: 'float:right',
							defaultButton: true
						}));
					}

					// 'back' button
					if (idx > 0) {
						footer.addChild(new Button({
							label: _('Back'),
							callback: lang.hitch(this, '_gotoPage', idx - 1),
							style: 'float:right'
						}));
					}

					// 'cancel' button
					if (idx < docs.length - 1) {
						footer.addChild(new Button({
							label: _('Cancel'),
							callback: lang.hitch(this, 'close'),
							style: 'float:left'
						}));
					}

					// create 'page'
					var page = new ContainerWidget({
					});
					var html = new Text({
						content: idoc,
						style: 'width:600px; max-height:280px; overflow-y:auto; overflow-x:hidden;'
					});
					parser.parse(html.domNode);
					page.addChild(html);
					page.addChild(footer);
					this._pages.push(page);
					this._stackContainer.addChild(page);
				}, this);

				this.set('content', this._stackContainer);
			}));

			this.on('hide', lang.hitch(this, function() {
				setTimeout(lang.hitch(this, 'destroyRecursive'), 0);
			}));
		},

		close: function() {
			when(this.hide(), lang.hitch(this, function() {
				setTimeout(lang.hitch(this, 'destroyRecursive'), 0);
			}));
		},

		destroyRecursive: function() {
			this.inherited(arguments);
		}

	});
});

