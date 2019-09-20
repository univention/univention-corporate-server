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
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/widgets/CheckBox",
	"umc/widgets/ComboBox",
	"umc/widgets/Button",
	"umc/modules/uvmm/DriveWizard",
	"umc/modules/uvmm/types",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, Deferred, Dialog, tools, dialog, Grid, Form, Text, TextBox, CheckBox, ComboBox, Button, DriveWizard, types, _) {

	return declare("umc.modules.uvmm.DriveGrid", [ Grid ], {
		moduleStore: null,

		domain: null,

		domainActive: false,

		query: {},

		sortIndex: null,

		style: 'width: 100%;',

		postMixInProperties: function() {
			lang.mixin(this, {
				columns: [{
					name: 'device',
					label: _('Type'),
					formatter: function(dev) {
						return types.blockDevices[dev] || _('unknown');
					}
				}, {
					name: 'volumeFilename',
					label: _('Image')
				}, {
					name: 'size',
					label: _('Size'),
					formatter: types.prettyCapacity
				}, {
					name: 'pool',
					label: _('Pool')
				}],
				actions: [{
					name: 'edit',
					label: _('Edit'),
					iconClass: 'umcIconEdit',
					isMultiAction: false,
					isStandardAction: true,
					callback: lang.hitch(this, '_editDrive'),
					canExecute: lang.hitch( this, function( item ) {
						// when creating an machine drives can not be edited
						return !this.domainActive && undefined !== this.domain.domainURI;
					} )
				}, {
					name: 'delete',
					label: _('Delete'),
					isMultiAction: false,
					isStandardAction: true,
					iconClass: 'umcIconDelete',
					callback: lang.hitch(this, '_removeDrive'),
					canExecute: lang.hitch(this, function(item) {
						return !this.domainActive;
					})
				}, {
					name: 'change_medium',
					label: _('Change medium'),
					isMultiAction: false,
					isStandardAction: true,
					callback: lang.hitch(this, '_changeMedium'),
					canExecute: function(item) {
						return item.device == 'cdrom' || item.device == 'floppy';
					}
				}, {
					name: 'add',
					label: _('Add'),
					isContextAction: false,
					iconClass: 'umcIconAdd',
					callback: lang.hitch(this, '_addDrive')
				}]
			});
			this.inherited(arguments);
		},

		footerFormatter: function() {
			return '';
		},

		_setDomainActiveAttr: function(value) {
				this.domainActive = value;
				this._grid.update();

				// disable actions in toolbar
				array.forEach(this._toolbar.getChildren(), lang.hitch(this, function(widget) {
					if (widget instanceof Button) {
						widget.set('disabled', value);
					}
				}));
		},

		buildRendering: function() {
			this.inherited( arguments );

			// deactivate sorting
			this._grid.canSort = function( col ) {
				return false;
			};
		},

		_nextID: function() {
			var newID = this.moduleStore.data.length + 1;

			array.forEach( this.moduleStore.data, function( item ) {
				if ( item.$id$ >= newID ) {
					newID = item.$id$ + 1;
				}
			} );

			return newID;
		},

		_changeMedium: function( ids, items ) {
			var old_cdrom = items[ 0 ];
			var _dialog = null, wizard = null;

			var _cleanup = function() {
				_dialog.hide();
				_dialog.destroyRecursive();
				wizard.destroyRecursive();
			};

			var _finished = lang.hitch( this, function( values ) {
				_cleanup();
				if ( undefined !== old_cdrom.target_dev ) {
					values.target_dev = old_cdrom.target_dev;
				}
				if ( undefined !== old_cdrom.target_bus ) {
					values.target_bus = old_cdrom.target_bus;
				}
				this.moduleStore.put( lang.mixin( {
					$id$: ids[ 0 ]
				}, values ) );
				this.filter();
			} );

			wizard = new DriveWizard({
				domain: this.domain,
				onFinished: _finished,
				onCancel: _cleanup,
				driveType: old_cdrom.device
			});

			_dialog = new Dialog({
				title: _('Change medium'),
				'class': 'umcLargeDialog',
				content: wizard
			});
			_dialog.show();
		},

		_editDrive: function( ids, items ) {
			var disk = items[ 0 ];

			var intro_msg = _( 'All image files are stored in so-called storage pools. They can be stored in a local directory, an LVM partition or a share (e.g. using iSCSI, NFS or CIFS).' );
			var kvm_msg = _('Hard drive images can be administrated in two ways on KVM systems; by default images are saved in the <i>Extended format (qcow2)</i>. This format supports copy-on-write which means that changes do not overwrite the original version, but store new versions in different locations. The internal references of the file administration are then updated to allow both access to the original and the new version. This technique is a prerequisite for efficiently managing snapshots of virtual machines. Alternatively, you can also access a hard drive image in <i>Simple format (raw)</i>. Snapshots can only be created when using hard drive images in <i>Extended format</i>.');
			var pv_msg = _( 'Paravirtualization is a special variant of virtualization in which the virtualized operating system is adapted to the underlying virtualization technology. This improves the performance. Linux systems usually support paravirtualization out of the box. For Windows systems additional support drivers need to be installed, see the <a href="https://wiki.univention.de/index.php?title=UVMM_Technische_Details">Univention wiki</a> for details (currently only available in German).' );

			var msg = '<p>' + intro_msg + '</p>';
			msg += '<p>' + kvm_msg + '</p>';
			msg = '<p>' + pv_msg + '</p>';

			var _dialog = null, form = null;

			var _cleanup = function() {
				_dialog.hide();
				_dialog.destroyRecursive();
				form.destroyRecursive();
			};

			var _saveDrive = lang.hitch(this, function() {
				var values = form.get('value');
				// reset target if setting paravirtual has changed
				if ( disk.paravirtual != values.paravirtual ) {
					disk.target_bus = null;
					disk.target_dev = null;
				}
				disk.readonly = values.readonly;
				disk.paravirtual = values.paravirtual;
				disk.driver_cache = values.driver_cache;
				this.moduleStore.put( disk );
				_cleanup();
				this.filter();
			});

			form = new Form({
				widgets: [
				{
					type: Text,
					name: '__message',
					content: msg,
					size: 'Two',
					label: ''
				}, {
					name: 'device',
					type: ComboBox,
					size: 'Two',
					value: disk.device,
					disabled: true,
					staticValues: types.dict2list(types.blockDevices)
				}, {
					name: 'pool',
					type: ComboBox,
					size: 'Two',
					label: _( 'Pool' ),
					description: _('Each image is located within a so called storage pool, which might be a local directory, a device, an LVM volume or any type of share (e.g. mounted via iSCSI, NFS or CIFS).'),
					dynamicOptions: lang.hitch( this, function( options ) {
						return {
							nodeURI: this.domain.nodeURI
						};
					} ),
					dynamicValues: types.getPools,
					disabled: true
				}, {
					name: 'volumeFilename',
					type: TextBox,
					size: 'Two',
					value: disk.source || '',
					label: _( 'Filename' ),
					disabled: true
				}, {
					name: 'readonly',
					type: CheckBox,
					size: 'Two',
					value: disk.readonly || false,
					label: _('Read only'),
					description: _('The device cannot be modified by the guest.')
				}, {
					type: CheckBox,
					size: 'Two',
					name: 'paravirtual',
					value: disk.paravirtual === undefined ? false : disk.paravirtual,
					label: _( 'Paravirtual drive' )
				}, {
					name: 'driver_cache',
					type: ComboBox,
					size: 'Two',
					value: disk.driver_cache || 'default',
					label: _('Caching'),
					description: _('Configure cache behavior of host.'),
					staticValues: types.dict2list(types.driverCache)
				} ],
				buttons: [{
					name: 'submit',
					label: _('Save'),
					style: 'float: right;',
					callback: function() {
						_saveDrive();
					}
				}, {
					name: 'cancel',
					label: _('Cancel'),
					callback: _cleanup
				}],
				layout: ['__message', 'device', 'pool', 'volumeFilename', 'readonly', 'paravirtual', 'driver_cache']
			});

			// hide pool for block devices
			form._widgets.pool.set( 'visible', disk.type != 'block' );

			_dialog = new Dialog({
				title: _('Edit drive'),
				content: form,
				'class' : 'umcLargeDialog'
			});
			_dialog.show();
		},

		_removeDrive: function( ids, items ) {
			var disk = items[ 0 ];

			var buttons = [ {
				name: 'cancel',
				'default': true,
				label: _('Cancel')
			}, {
				name: 'detach',
				label: _('Detach')
			}, {
				name: 'delete',
				label: _('Delete')
			} ];

			// confirm removal of drive
			var msg = _( 'Should the selected drive be deleted or detached from the virtual machine?' );
			// chain the UMCP commands for removing the drive
			var deferred = new Deferred();
			deferred.resolve();
			// just of a domain URI is available we need to detach/delete it otherwise we just remove it from the grid
			if (undefined !== this.domain.domainURI && disk.pool && disk.source) {
				deferred = deferred.then( lang.hitch( this, function() {
					return tools.umcpCommand('uvmm/storage/volume/deletable', [ {
						domainURI: this.domain.domainURI,
						source: disk.source,
						pool: disk.pool
					} ] );
				} ) );
				deferred = deferred.then( lang.hitch( this, function( response ) {
					if (null === response.result[0].deletable) {
						// not in a pool or pool is not manageable
						return 'detach';
					} else if ( disk.device == 'cdrom' ) {
						msg += ' ' + _( 'The selected drive is a CD-ROM and should be detached from the virtual machine. If the volume is delete no other machine can use it anymore.' );
					} else if (disk.device == 'floppy') {
						msg += ' ' + _( 'The selected drive is a floppy and should be detached from the virtual machine. If the volume is delete no other machine can use it anymore.' );
					} else if ( ! response.result[ 0 ].deletable ) {
						msg += ' ' + _( 'The selected drive seems to be attached to other virtual machines and therefore should not be deleted.' );
					}
					return dialog.confirm( msg, buttons );
				} ) );

				deferred = deferred.then( lang.hitch( this, function( action ) {
					if ( action != 'delete' && action != 'detach' ) {
						return;
					}
					this.onUpdateProgress( 0, 1 );

					// detach the drive from the domain
					this.moduleStore.remove( ids[ 0 ] );
					// the moduleStore is filled using setData which seems to sometimes break the remove event
					// -> call filter manually
					this.filter();

					if ( action == 'delete' ) {
						tools.umcpCommand('uvmm/storage/volume/remove', {
							nodeURI: this.domain.nodeURI,
							volumes: [{source: disk.source}]
						} ).then( lang.hitch( this, function( response ) {
							this.onUpdateProgress( 1, 1 );
						} ) );
					} else {
						this.onUpdateProgress( 1, 1 );
					}
				} ) );
			} else {
				// detach the drive from the domain
				this.moduleStore.remove( ids[ 0 ] );
				// the moduleStore is filled using setData which seems to sometimes break the remove event
				// -> call filter manually
				this.filter();
				this.onUpdateProgress( 1, 1 );
			}
		},

		_addDrive: function() {
			var _dialog = null, wizard = null;

			var _cleanup = function() {
				_dialog.hide();
				_dialog.destroyRecursive();
				wizard.destroyRecursive();
			};

			var _finished = lang.hitch(this, function(values) {
				var paravirtual = false;
				var driver_cache = values.device == 'disk' ? 'none' : 'default';
				var readonly = values.device != 'disk'; // floppy cdrom
				var id = this._nextID();

				_cleanup();
				if ( this.domain.profileData ) {
					if ( values.device == 'cdrom' && this.domain.profileData.pvcdrom ) {
						paravirtual = true;
					} else if ( values.device == 'disk' && this.domain.profileData.pvdisk ) {
						paravirtual = true;
					}
					if (undefined !== this.domain.profileData.drivercache && values.device == 'disk') {
						driver_cache = this.domain.profileData.drivercache || driver_cache;
					}
				}
				this.moduleStore.add( lang.mixin( {
					$id$: id,
					driver_cache: driver_cache,
					readonly: readonly,
					paravirtual: paravirtual
				}, values ) );
			});

			wizard = new DriveWizard({
				domain: this.domain,
				onFinished: _finished,
				onCancel: _cleanup
			});

			_dialog = new Dialog({
				title: _('Add a new drive'),
				'class': 'umcLargeDialog',
				content: wizard
			});
			_dialog.show();
		},

		filter: function() {
			this.inherited(arguments, [{}]);
		},

		onUpdateProgress: function(i, n) {
			// event stub
		}
	});
});
