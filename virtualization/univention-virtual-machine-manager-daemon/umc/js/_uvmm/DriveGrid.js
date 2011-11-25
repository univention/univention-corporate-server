/*
 * Copyright 2011 Univention GmbH
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
/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._uvmm.DriveGrid");

dojo.require("dijit.Dialog");

dojo.require("umc.tools");
dojo.require("umc.dialog");
dojo.require("umc.i18n");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Form");
dojo.require("umc.modules._uvmm.DriveWizard");

dojo.declare("umc.modules._uvmm.DriveGrid", [ umc.widgets.Grid, umc.i18n.Mixin ], {
	moduleStore: null,

	domain: null,

	i18nClass: 'umc.modules.uvmm',

	query: {},

	sortIndex: null,

	style: 'width: 100%; height: 200px;',

	constructor: function() {
		dojo.mixin(this, {
			columns: [{
				name: 'device',
				label: this._('Type'),
				formatter: dojo.hitch(this, function(dev) {
					return umc.modules._uvmm.types.blockDevices[dev] || this._('unknown');
				})
			}, {
				name: 'volumeFilename',
				label: this._('Image')
			}, {
				name: 'size',
				label: this._('Size')
			}, {
				name: 'pool',
				label: this._('Pool')
			}],
			actions: [{
				name: 'edit',
				label: this._('Edit'),
				iconClass: 'umcIconEdit',
				isMultiAction: false,
				isStandardAction: true,
				callback: dojo.hitch(this, '_editDrive')
			}, {
				name: 'change_medium',
				label: this._('Change medium'),
				isMultiAction: false,
				isStandardAction: false,
				callback: dojo.hitch(this, '_changeMedium'),
				canExecute: function( item ) {
					return item.device == 'cdrom' || item.device == 'floppy';
				}
			}, {
				name: 'delete',
				label: this._('Delete'),
				isMultiAction: false,
				isStandardAction: true,
				iconClass: 'umcIconDelete',
				callback: dojo.hitch(this, '_removeDrive')
			}, {
				name: 'add',
				label: this._('Add drive'),
				isMultiAction: false,
				isContextAction: false,
				iconClass: 'umcIconAdd',
				callback: dojo.hitch(this, '_addDrive')
			}]
		});
	},

	buildRendering: function() {
		this.inherited( arguments );

		// deactivate sorting
		this._grid.canSort = function( col ) {
			return false;
		};
	},

	_changeMedium: function( ids, items ) {
		var old_cdrom = items[ 0 ];
		var dialog = null, wizard = null;

		var _cleanup = function() {
			dialog.hide();
			dialog.destroyRecursive();
			wizard.destroyRecursive();
		};

		var _finished = dojo.hitch( this, function( values ) {
			_cleanup();
			this.moduleStore.remove( ids[ 0 ] );
			values.target_dev = old_cdrom.target_dev;
			values.target_bus = old_cdrom.target_bus;
			this.moduleStore.add( values );
		} );

		wizard = new umc.modules._uvmm.DriveWizard({
			style: 'width: 450px; height:450px;',
			domain: this.domain,
			onFinished: _finished,
			onCancel: _cleanup,
			driveType: old_cdrom.device
		});

		dialog = new dijit.Dialog({
			title: this._('Change medium'),
			content: wizard
		});
		dialog.show();
	},

	_editDrive: function( ids, items ) {
		var disk = items[ 0 ];

		var types = umc.modules._uvmm.types;
		var intro_msg = this._( 'All image files are stored in so-called storage pools. They can be stored in a local directory, an LVM partition or a share (e.g. using iSCSI, NFS or CIFS).' );
		var kvm_msg = this._( 'Hard drive images can be administrated in two ways on KVM systems; by default images are saved in the <i>Extended format (qcow2)</i>. This format supports copy-on-write which means that changes do not overwrite the original version, but store new versions in different locations. The internal references of the file administration are then updated to allow both access to the original and the new version. This technique is a prerequisite for efficiently managing snapshots of virtual machines. Alternatively, you can also access a hard drive image in <i>Simple format (raw)</i>. Snapshots can only be created when using hard drive images in <i>Extended format</i>. Only the <i>Simple format</i> is available on Xen systems.' );
		var pv_msg = this._( 'Paravirtualisation is a special variant of virtualisation in which the virtualised operating system is adapted to the underlying virtualisation technology. This improves the performance. Linux systems usually support paravirtualisation out of the box. For Windows systems additional support drivers need to be installed, see the <a href="http://wiki.univention.de/index.php?title=UVMM_Technische_Details"> Univention wiki </a> for details (currently only available in German).' );

		var msg = '<p>' + intro_msg + '</p>';
		if ( types.getNodeType( this.domain.domainURI ) == 'qemu' ) {
			msg += '<p>' + kvm_msg + '</p>';
		}
		msg = '<p>' + pv_msg + '</p>';

		var dialog = null, form = null;

		var _cleanup = function() {
			dialog.hide();
			dialog.destroyRecursive();
			form.destroyRecursive();
		};

		var _saveDrive = dojo.hitch(this, function() {
			var values = form.gatherFormValues();
			disk.paravirtual = values.paravirtual;
			this.moduleStore.put( disk );
			_cleanup();
		});

		form = new umc.widgets.Form({
			widgets: [
			{
				type: 'Text',
				name: '__message',
				content: msg,
				label: ''
			}, {
				name: 'device',
				type: 'ComboBox',
				value: disk.device,
				disabled: true,
				staticValues: types.dict2list(types.blockDevices)
			}, {
				name: 'pool',
				type: 'ComboBox',
				label: this._( 'Pool' ),
				description: this._('Each image is located within a so called storage pool, which might be a local directory, a device, an LVM volume or any type of share (e.g. mounted via iSCSI, NFS or CIFS).'),
				dynamicOptions: dojo.hitch( this, function( options ) {
					return {
						nodeURI: this.domain.domainURI.slice( 0, this.domain.domainURI.indexOf( '#' ) )
					};
				} ),
				dynamicValues: types.getPools,
				disabled: true
			}, {
				name: 'volumeFilename',
				type: 'TextBox',
				value: disk.volumeFilename,
				label: this._( 'Filename' ),
				disabled: true
			}, {
				type: 'CheckBox',
				name: 'paravirtual',
				value: disk.paravirtual,
				label: this._( 'Paravirtual drive' )
			} ],
			buttons: [{
				name: 'submit',
				label: this._('Save'),
				style: 'float: right;',
				callback: function() {
					_saveDrive();
				}
			}, {
				name: 'cancel',
				label: this._('Cancel'),
				callback: _cleanup
			}],
			layout: [ '__message', 'device', 'pool', 'volumeFilename', 'paravirtual' ]
		});

		// hide pool for block devices
		form._widgets.pool.set( 'visible', disk.type != 'block' );

		dialog = new dijit.Dialog({
			title: this._('Edit drive'),
			content: form,
			'class' : 'umcPopup',
			style: 'max-width: 400px;'
		});
		dialog.show();
	},

	_removeDrive: function( ids, items ) { 
		var disk = items[ 0 ];

		var buttons = [ {
			name: 'detach',
			label: this._('Detach')
		}, {
			name: 'delete',
			label: this._('Delete')
		}, {
			name: 'cancel',
			'default': true,
			label: this._('Cancel')
		} ];

		// confirm removal of drive
		var msg = this._( 'Should the selected drive be deleted or detached from the virtual instance?' );
		// chain the UMCP commands for removing the drive
		var deferred = new dojo.Deferred();
		deferred.resolve();
		deferred = deferred.then( dojo.hitch( this, function() {
			return umc.tools.umcpCommand('uvmm/storage/volume/deletable', [ {
				domainURI: this.domain.domainURI,
				volumeFilename: disk.volumeFilename,
				pool: disk.pool
			} ] );
		} ) );
		deferred = deferred.then( dojo.hitch( this, function( response ) {
			if ( disk.device == 'cdrom' ) {
				msg += ' ' + this._( 'The selected drive is a CD-ROM and should be detached from the virtual instance. If the volume is delete no other instance can use it anymore.' );
			} else if ( ! response.result[ 0 ].deletable ) {
				msg += ' ' + this._( 'The selected drive seems to be attached to other virtual instances and therefor should not be deleted.' );
			}
			return umc.dialog.confirm( msg, buttons );
		} ) );

		deferred = deferred.then( dojo.hitch( this, function( action ) {
			if ( action != 'delete' & action != 'detach' ) { 
				return;
			}
			this.onUpdateProgress( 0, 1 );

			// detach the drive from the domain
			this.moduleStore.remove( ids[ 0 ] );

			if ( action == 'delete' ) {
				umc.tools.umcpCommand('uvmm/storage/volume/remove', {
					nodeURI: this.domain.domainURI.slice( 0, this.domain.domainURI.indexOf( '#' ) ),
					volumes: [ { pool: disk.pool, volumeFilename: disk.volumeFilename } ],
				pool: disk.pool
				} ).then( dojo.hitch( this, function( response ) {
					this.onUpdateProgress( 1, 1 );
					this.moduleStore.onChange();
				} ) );
			} else {
				this.onUpdateProgress( 1, 1 );
				this.moduleStore.onChange();
			}
		} ) );
	},

	_addDrive: function() {
		var dialog = null, wizard = null;

		var _cleanup = function() {
			dialog.hide();
			dialog.destroyRecursive();
			wizard.destroyRecursive();
		};

		var _finished = dojo.hitch(this, function(values) {
			_cleanup();
			this.moduleStore.add(values);
		});

		wizard = new umc.modules._uvmm.DriveWizard({
			style: 'width: 450px; height:450px;',
			domain: this.domain,
			onFinished: _finished,
			onCancel: _cleanup
		});

		dialog = new dijit.Dialog({
			title: this._('Add a new drive'),
			content: wizard
		});
		dialog.show();
	},

	filter: function() {
		this.inherited(arguments, [{}]);
	},

	onUpdateProgress: function(i, n) {
		// event stub
	}
});
