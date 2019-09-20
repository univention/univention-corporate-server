/*
 * Copyright 2011-2019 Univention GmbH
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
	"umc/modules/uvmm/types",
	"umc/modules/uvmm/snapshot",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, Deferred, Dialog, tools, dialog, Grid, Form, TextBox, types, snapshot, _) {
	return declare("umc.modules.uvmm.SnapshotGrid", [ Grid ], {

		domain: null,

		sortIndex: -2,

		postMixInProperties: function() {
			lang.mixin(this, {
				columns: [{
					name: 'label',
					label: _('Name')
				}, {
					width: '11em',
					name: 'time',
					label: _('Date')
				}],
				actions: [{
					name: 'delete',
					label: _('Delete'),
					isMultiAction: true,
					isStandardAction: true,
					iconClass: 'umcIconDelete',
					callback: lang.hitch(this, '_deleteSnapshots')
				}, {
					name: 'revert',
					label: _('Revert'),
					isMultiAction: false,
					isStandardAction: true,
					callback: lang.hitch(this, '_revertSnapshot')
				}, {
					name: 'add',
					label: _('Create new snapshot'),
					isMultiAction: false,
					isContextAction: false,
					iconClass: 'umcIconAdd',
					callback: lang.hitch(this, '_addSnapshot')
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

		_addSnapshot: function() {
			this.onUpdateProgress(0, 1);
			snapshot._addSnapshot(this.domain.domainURI, this.domain).then(lang.hitch(this, function() {
				this.onUpdateProgress(1, 1);
				this.moduleStore.onChange();
			}), lang.hitch(this, function() {
				this.onUpdateProgress(1, 1);
				this.moduleStore.onChange();
			}));
		},

		_revertSnapshot: function(ids) {
			if (ids.length != 1) {
				// should not happen
				return;
			}

			// confirm applying of snapshot
			dialog.confirm(_('Are you sure to revert to the selected snapshot?'), [{
				name: 'cancel',
				'default': true,
				label: _('Cancel')
			}, {
				name: 'revert',
				label: _('Revert')
			}]).then(lang.hitch(this, function(response) {
				if (response != 'revert') {
					return;
				}

				// send the UMCP command
				this.onUpdateProgress(0, 1);
				tools.umcpCommand('uvmm/snapshot/revert', {
					domainURI: this.domain.domainURI,
					snapshotName: ids[0]
				}).then(lang.hitch(this, function() {
					this.onUpdateProgress(1, 1);
				}), lang.hitch(this, function() {
					this.onUpdateProgress(1, 1);
				}));
			}));
		},

		_deleteSnapshots: function(ids) {
			if (!ids.length) {
				// nothing selected
				dialog.alert(_('No snapshots have been selected!'));
				return;
			}

			// confirm removal of snapshot(s)
			var msg = _('Are you sure to delete the selected %s snapshots?', ids.length);
			if (ids.length == 1) {
				msg = _('Are you sure to delete the selected snapshot?');
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

				// chain the UMCP commands for removing the snapshot(s)
				var deferred = new Deferred();
				deferred.resolve();
				array.forEach(ids, function(iid, i) {
					deferred = deferred.then(lang.hitch(this, function() {
						this.onUpdateProgress(i, ids.length);
						return tools.umcpCommand('uvmm/snapshot/remove', {
							domainURI: this.domain.domainURI,
							snapshotName: iid
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
