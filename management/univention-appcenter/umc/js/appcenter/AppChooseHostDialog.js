/*
 * Copyright 2013-2019 Univention GmbH
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
	"dojox/html/entities",
	"dojo/topic",
	"dojo/Deferred",
	"umc/widgets/Form",
	"umc/widgets/Page",
	"umc/widgets/Text",
	"umc/widgets/ComboBox",
	"./_AppDialogMixin",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, entities, topic, Deferred, Form, Page, Text, ComboBox, _AppDialogMixin, _) {
	return declare("umc.modules.appcenter.AppChooseHostDialog", [ Page, _AppDialogMixin ], {
		_form: null,
		_continueDeferred: null,
		title: _('App management'),
		headerTextAllowHTML: false,
		helpTextAllowHTML: false,

		postMixInProperties: function() {
			this.inherited(arguments);
			this.headerButtons = [{
				name: 'close',
				label: _('Cancel installation'),
				align: 'left',
				callback: lang.hitch(this, 'onBack')
			}];
		},

		reset: function(hosts, removedDueToInstalled, removedDueToRole) {
			this._clearWidget('_form', true);

			this.set('headerText', _('Installation of %s', this.app.name));
			this.set('helpText', _('In order to proceed with the installation of %s, please select the host on which the application is going to be installed.', this.app.name));

			if (this._continueDeferred) {
				this._continueDeferred.reject();
			}
			this._continueDeferred = new Deferred();

			if (hosts.length === 1 && !removedDueToRole.length && !removedDueToInstalled.length) {
				// safely resolve the deferred object of the dialog if there is
				// only a single choice to be made
				this._continueDeferred.resolve(hosts[0].id);
			}

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
			var removeExplanation = '';
			if (removedDueToInstalled.length === 1) {
				removeExplanation += '<p>' + _('%s was removed from the list because the application is installed on this host.', entities.encode(removedDueToInstalled[0])) + '</p>';
			} else if (removedDueToInstalled.length > 1) {
				removeExplanation += '<p>' + _('%d hosts were removed from the list because the application is installed there.', removedDueToInstalled.length) + '</p>';
			}
			if (removedDueToRole.length === 1) {
				removeExplanation += '<p>' + _('%s was removed from the list because the application requires a different server role than the one this host has.', entities.encode(removedDueToRole[0])) + '</p>';
			} else if (removedDueToRole.length > 1) {
				removeExplanation += '<p>' + _('%d hosts were removed from the list because the application requires a different server role than these hosts have.', removedDueToRole.length) + '</p>';
			}
			if (removeExplanation) {
				removeExplanation = '<strong>' + _('Not all hosts are listed above') + '</strong>' + removeExplanation;
			}
			this._form = new Form({
				widgets: [{
					type: ComboBox,
					label: _('Host for installation of application'),
					name: 'host',
					required: true,
					size: 'Two',
					staticValues: hosts
				}, {
					type: Text,
					name: 'remove_explanation',
					content: removeExplanation
				}],
				buttons: buttons
			});
			this.addChild(this._form);
		},

		showUp: function() {
			this.onShowUp();
			this._continueDeferred.then(lang.hitch(this, 'onBack'), lang.hitch(this, 'onBack'));
			return this._continueDeferred;
		}
	});
});
