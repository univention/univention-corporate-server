/*
 * Copyright 2017-2019 Univention GmbH
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
	"dojo/_base/array",
	"dojo/Deferred",
	"dijit/Dialog",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Grid",
	"umc/widgets/Form",
	"umc/widgets/TextBox",
	"umc/widgets/ComboBox",
	"umc/widgets/Button",
	"umc/modules/uvmm/types",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, Deferred, Dialog, tools, dialog, Grid, Form, TextBox, ComboBox, Button, types, _) {
	return declare("umc.modules.uvmm.TargetHostGrid", [ Grid ], {

		domain: null,

		postMixInProperties: function() {
			lang.mixin(this, {
				columns: [{
					name: 'label',
					label: _('Valid migration targethosts')
				}],
				actions: [{
					name: 'delete',
					label: _('Delete'),
					isMultiAction: true,
					isStandardAction: true,
					iconClass: 'umcIconDelete',
					callback: lang.hitch(this, '_deleteTargethost')
				}, {
					name: 'add',
					label: _('Add'),
					isMultiAction: false,
					isContextAction: false,
					iconClass: 'umcIconAdd',
					callback: lang.hitch(this, '_addTargethost')
				}]
			});
			this.inherited(arguments);
		},

		_setDomainAttr: function(newDomain) {
			this.domain = newDomain;
			this.filter();
		},

		filter: function() {
			this.inherited(arguments, [{ domainURI: this.domain.domainURI }]);
		},

		_addTargethost: function() {
			var _dialog = null, form = null;

			var _cleanup = function() {
				_dialog.hide();
				_dialog.destroyRecursive();
				form.destroyRecursive();
			};

			var _saveTargets = lang.hitch(this, function(name) {
				// send the UMCP command
				this.onUpdateProgress(0, 1);
				tools.umcpCommand('uvmm/targethost/add', {
					domainURI: this.domain.domainURI,
					targethostName: name
				}).then(lang.hitch(this, function() {
					this.moduleStore.onChange();
					this.onUpdateProgress(1, 1);
				}), lang.hitch(this, function() {
					dialog.alert(_('An error occurred during processing your request.'));
					this.moduleStore.onChange();
					this.onUpdateProgress(1, 1);
				}));
			});

			var _getMigrationTargetHosts = lang.hitch(this, function() {
				var curr_hosts = [];
				var deferred = tools.umcpCommand('uvmm/targethost/query', { domainURI: this.domain.domainURI });
				deferred.then(lang.hitch(this, function(current_targethosts) {
					array.forEach(current_targethosts.result, function(result) {
						curr_hosts.push(result.id);
					});
				}));
				return tools.umcpCommand('uvmm/node/query', { nodePattern: '' }).then(lang.hitch(this, function(results) {
					var servers = [];
					array.forEach(results.result, lang.hitch(this, function(iresult) {
						if (curr_hosts.indexOf(iresult.label) == -1) {
							servers.push(iresult.label);
						}
					}));
					return servers;
				}));
			});

			form = new Form({
				widgets: [{
					name: 'name',
					type: ComboBox,
					label: _('Please select the new migration targethost:'),
					dynamicValues: _getMigrationTargetHosts,
				}],
				buttons: [{
					name: 'submit',
					label: _('Add'),
					style: 'float: right;',
					callback: function() {
						var nameWidget = form.getWidget('name');
						if (nameWidget.isValid()) {
							var name = nameWidget.get('value');
							_cleanup();
							_saveTargets(name);
						}
					}
				}, {
					name: 'cancel',
					label: _('Cancel'),
					callback: _cleanup
				}],
				layout: [ 'name' ]
			});

			_dialog = new Dialog({
				title: _('Add new targethost'),
				content: form
			});
			_dialog.show();
		},

		_deleteTargethost: function(ids) {
			if (!ids.length) {
				// nothing selected
				dialog.alert(_('No target has been selected!'));
				return;
			}

			// confirm removal of snapshot(s)
			var msg = _('Are you sure to delete the selected %s targethosts?', ids.length);
			if (ids.length == 1) {
				msg = _('Are you sure to delete the selected targethost?');
			}
			dialog.confirm(msg, [{
				name: 'cancel',
				'default': true,
				label: _('Cancel')
			}, {
				name: 'delete',
				label: _('Delete')
			}]).then(lang.hitch(this, function(response) {
				if (response != 'delete') {
					return;
				}

				// chain the UMCP commands for removing the target hosts
				var deferred = new Deferred();
				deferred.resolve();
				array.forEach(ids, function(iid, i) {
					deferred = deferred.then(lang.hitch(this, function() {
						this.onUpdateProgress(i, ids.length);
						return tools.umcpCommand('uvmm/targethost/remove', {
							domainURI: this.domain.domainURI,
							targethostName: iid
						});
					}));
				}, this);

				// finish the progress bar and add error handler
				deferred = deferred.then(lang.hitch(this, function() {
					this.onUpdateProgress(ids.length, ids.length);
					this.moduleStore.onChange();
				}), lang.hitch(this, function() {
					dialog.alert(_('An error occurred during processing your request.'));
					this.onUpdateProgress(ids.length, ids.length);
					this.moduleStore.onChange();
				}));
			}));
		},

		onUpdateProgress: function(i, n) {
			// event stub
		}
	});
});
