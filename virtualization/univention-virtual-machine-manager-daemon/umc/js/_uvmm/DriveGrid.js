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
				name: 'delete',
				label: this._('Delete'),
				isMultiAction: false,
				isStandardAction: true,
				iconClass: 'umcIconDelete',
				callback: dojo.hitch(this, '_removeDrive')
			},/* {
				name: 'edit',
				label: this._('Edit'),
				isMultiAction: false,
				isStandardAction: true,
				callback: dojo.hitch(this, '_edit Drive')
			}, */ {
				name: 'add',
				label: this._('Add drive'),
				isMultiAction: false,
				isContextAction: false,
				iconClass: 'umcIconAdd',
				callback: dojo.hitch(this, '_addDrive')
			}]
		});
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
			return umc.tools.umcpCommand('uvmm/storage/volume/deletable', {
				domainURI: this.domain.domainURI,
				volumeFilename: disk.volumeFilename,
				pool: disk.pool
			} );
		} ) );
		deferred = deferred.then( dojo.hitch( this, function( response ) {
			if ( disk.device == 'cdrom' ) {
				msg += ' ' + this._( 'The selected drive is a CD-ROM and should be detached from the virtual instance. If the volume is delete no other instance can use it anymore.' );
			} else if ( ! response.result ) {
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
					console.log( response.result );
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
