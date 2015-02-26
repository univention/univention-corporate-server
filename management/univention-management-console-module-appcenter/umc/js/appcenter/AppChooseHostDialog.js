/*
 * Copyright 2013-2014 Univention GmbH
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
	"dojo/topic",
	"dojo/Deferred",
	"umc/widgets/Form",
	"umc/widgets/Page",
	"umc/widgets/Text",
	"umc/widgets/ComboBox",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, topic, Deferred, Form, Page, Text, ComboBox, _) {
	return declare("umc.modules.appcenter.AppChooseHostDialog", [ Page ], {
		app: null,
		_form: null,
		_page: null,
		_continueDeferred: null,
		noFooter: true,

		title: _('App management'),

		postMixInProperties: function() {
			this.inherited(arguments);
			this.headerButtons = [{
				name: 'close',
				iconClass: 'umcCloseIconWhite',
				label: _('Back'),
				align: 'left',
				callback: lang.hitch(this, 'onBack')
			}];
		},

		reset: function(title, hosts, removedDueToInstalled, removedDueToRole) {
			if (this._continueDeferred) {
				this._continueDeferred.reject();
			}
			this._continueDeferred = new Deferred();
			this.set('headerText', title);
			var buttons = [{
				name: 'cancel',
				'default': true,
				label: _('Cancel'),
				callback: lang.hitch(this, function() {
					topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, this.app.id, 'user-cancel');
					this._continueDeferred.reject();
				})
			}, {
				name: 'submit',
				label: _('Next'),
				callback: lang.hitch(this, function() {
					if (this._form.isValid()) {
						var values = this._form.get('value');
						this._continueDeferred.resolve(values);
					}
				})
			}];
			if (this._page) {
				this.removeChild(this._page);
				this._page.destroyRecursive();
			}
			this._page = new Page({
				footerButtons: buttons
			});
			this.addChild(this._page);
			var removeExplanation = '';
			if (removedDueToInstalled.length === 1) {
				removeExplanation += '<p>' + _('%s was removed from the list because the application is installed on this host.', removedDueToInstalled[0]) + '</p>';
			} else if (removedDueToInstalled.length > 1) {
				removeExplanation += '<p>' + _('%d hosts were removed from the list because the application is installed there.', removedDueToInstalled.length) + '</p>';
			}
			if (removedDueToRole.length === 1) {
				removeExplanation += '<p>' + _('%s was removed from the list because the application requires a different server role than the one this host has.', removedDueToRole[0]) + '</p>';
			} else if (removedDueToRole.length > 1) {
				removeExplanation += '<p>' + _('%d hosts were removed from the list because the application requires a different server role than these hosts have.', removedDueToRole.length) + '</p>';
			}
			if (removeExplanation) {
				removeExplanation = '<strong>' + _('Not all hosts are listed above') + '</strong>' + removeExplanation;
			}
			this._form = new Form({
				widgets: [{
					type: ComboBox,
					label: _('Select the host where you want to install the application'),
					name: 'host',
					required: true,
					size: 'Two',
					staticValues: hosts
				}, {
					type: Text,
					name: 'remove_explanation',
					content: removeExplanation
				}]
			});
			this._page.addChild(this._form);
		},

		showUp: function() {
			this.onShowUp();
			this._continueDeferred.then(lang.hitch(this, 'onBack'), lang.hitch(this, 'onBack'));
			return this._continueDeferred;
		},

		onShowUp: function() {
		},

		onNext: function() {
		},

		onBack: function() {
		}

	});
});

