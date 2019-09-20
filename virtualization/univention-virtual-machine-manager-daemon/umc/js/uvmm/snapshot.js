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
	"dojo/_base/array",
	"dojo/_base/lang",
	"dojo/Deferred",
	"dijit/Dialog",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Form",
	"umc/widgets/TextBox",
	"umc/widgets/ProgressInfo",
	"umc/i18n!umc/modules/uvmm"
], function(declare, array, lang, Deferred, Dialog, tools, dialog, Form, TextBox, ProgressInfo, _) {
	var self = {
		_addSnapshot: function(domainURI, domain) {
			var deferred = new Deferred();
			var _dialog = null, form = null;

			if (domain.suspended) {
					dialog.alert(_('Creating a snapshot is not possible, because the domain is currently suspended!'));
					deferred.cancel();
					return deferred.promise;
			}

			var qcow2_images = 0;
			var snapshots_possible = array.every(domain.disks, function(disk) {
				if (!disk.source) {
					return true;
				}
				if (disk.readonly) {
					return true;
				}
				if (disk.driver_type == 'qcow2') {
					++qcow2_images;
					return true;
				}
				return false;
			});
			if (!snapshots_possible) {
				dialog.alert(_('Creating a snapshot is not possible, because the domain contains writeable raw images!'));
				deferred.cancel();
				return deferred.promise;
			} else if (qcow2_images === 0) {
				dialog.alert(_('Creating a snapshot is not possible, because the domain does not have at least one qcow2 image!'));
				deferred.cancel();
				return deferred.promise;
			}

			var _cleanup = function() {
				_dialog.hide();
				_dialog.destroyRecursive();
				form.destroyRecursive();
			};

			var _saveSnapshot = lang.hitch(this, function(name) {
				tools.umcpCommand('uvmm/snapshot/create', {
					domainURI: domainURI,
					snapshotName: name
				}).then(lang.hitch(this, function() {
					deferred.resolve();
				}));
			});

			form = new Form({
				widgets: [{
					name: 'name',
					type: TextBox,
					label: _('Please enter the name for the snapshot:'),
					pattern: '^[^./&<][^/&<]*$',
					invalidMessage: _('A valid snapshot name cannot contain "/", "&" or "<", and may not start with "." .')
				}],
				buttons: [{
					name: 'submit',
					label: _('Create'),
					style: 'float: right;',
					callback: function() {
						var nameWidget = form.getWidget('name');
						if (nameWidget.isValid()) {
							var name = nameWidget.get('value');
							_saveSnapshot(name);
							_cleanup();
						}
					}
				}, {
					name: 'cancel',
					label: _('Cancel'),
					callback: function() {
						_cleanup();
						deferred.cancel();
						return deferred.promise;
					}
				}],
				layout: [ 'name' ]
			});

			_dialog = new Dialog({
				title: _('Create new snapshot'),
				content: form
			});
			_dialog.show();
			return deferred.promise;
		}
	};
	return self;
});
