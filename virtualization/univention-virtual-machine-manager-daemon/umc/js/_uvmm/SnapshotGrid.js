/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._uvmm.SnapshotGrid");

dojo.require("dijit.Dialog");

dojo.require("umc.tools");
dojo.require("umc.dialog");
dojo.require("umc.i18n");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Form");

dojo.declare("umc.modules._uvmm.SnapshotGrid", [ umc.widgets.Grid, umc.i18n.Mixin ], {
	i18nClass: 'umc.modules.uvmm',

	domainURI: null,

	constructor: function() {
		dojo.mixin(this, {
			columns: [{
				name: 'label',
				label: this._('Name')
			}, {
				name: 'time',
				label: this._('Date')
			}],
			actions: [{
				name: 'delete',
				label: this._('Delete'),
				isMultiAction: true,
				isStandardAction: true,
				iconClass: 'umcIconDelete',
				callback: dojo.hitch(this, '_deleteSnapshots')
			}, {
				name: 'revert',
				label: this._('Revert'),
				isMultiAction: false,
				isStandardAction: true,
				callback: dojo.hitch(this, '_revertSnapshot')
			}, {
				name: 'add',
				label: this._('Create new snapshot'),
				isMultiAction: false,
				isContextAction: false,
				iconClass: 'umcIconAdd',
				callback: dojo.hitch(this, '_addSnapshot')
			}]
		});
	},

	_setDomainURIAttr: function(newURI) {
		this.domainURI = newURI;
		this.filter();
	},

	filter: function() {
		this.inherited(arguments, [{ domainURI: this.domainURI }]);
	},

	_addSnapshot: function() {
		var dialog = null, form = null;

		var _cleanup = function() {
			dialog.hide();
			dialog.destroyRecursive();
			form.destroyRecursive();
		};

		var _saveSnapshot = dojo.hitch(this, function(name) {
			// send the UMCP command
			this.onUpdateProgress(0, 1);
			umc.tools.umcpCommand('uvmm/snapshot/create', {
				domainURI: this.domainURI,
				snapshotName: name
			}).then(dojo.hitch(this, function() {
				this.moduleStore.onChange();
				this.onUpdateProgress(1, 1);
			}), dojo.hitch(this, function() {
				umc.dialog.alert(this._('An error ocurred during processing your request.'));
				this.moduleStore.onChange();
				this.onUpdateProgress(1, 1);
			}));
		});

		form = new umc.widgets.Form({
			widgets: [{
				name: 'name',
				type: 'TextBox',
				label: this._('Please enter the name for the snapshot:'),
				regExp: '^[^./][^/]*$',
				invalidMessage: this._('A valid snapshot name cannot contain "/" and may not start with "." .')
			}],
			buttons: [{
				name: 'submit',
				label: this._('Create'),
				style: 'float: right;',
				callback: function() {
					var nameWidget = form.getWidget('name');
					if (nameWidget.isValid()) {
						var name = nameWidget.get('value');
						_cleanup();
						_saveSnapshot(name);
					}
				}
			}, {
				name: 'cancel',
				label: this._('Cancel'),
				callback: _cleanup
			}],
			layout: [ 'name' ]
		});

		dialog = new dijit.Dialog({
			title: this._('Create new snapshot'),
			content: form
		});
		dialog.show();
	},

	_revertSnapshot: function(ids) {
		if (ids.length != 1) {
			// should not happen
			return;
		}

		// confirm removal of snapshot(s)
		umc.dialog.confirm(this._('Are you sure to revert to the selected snapshot?'), [{
			name: 'revert',
			label: this._('Revert')
		}, {
			name: 'cancel',
			'default': true,
			label: this._('Cancel')
		}]).then(dojo.hitch(this, function(response) {
			if (response != 'revert') {
				return;
			}

			// send the UMCP command
			this.onUpdateProgress(0, 1);
			umc.tools.umcpCommand('uvmm/snapshot/revert', {
				domainURI: this.domainURI,
				snapshotName: ids[0]
			}).then(dojo.hitch(this, function() {
				this.onUpdateProgress(1, 1);
			}), dojo.hitch(this, function() {
				this.onUpdateProgress(1, 1);
			}));
		}));
	},

	_deleteSnapshots: function(ids) {
		if (!ids.length) {
			// nothing selected
			umc.dialog.alert(this._('No snapshots have been selected!'));
			return;
		}

		// confirm removal of snapshot(s)
		var msg = this._('Are you sure to delete the selected {0} snapshots?', ids.length);
		if (ids.length == 1) {
			msg = this._('Are you sure to delete the selected snapshot?');
		}
		umc.dialog.confirm(msg, [{
			name: 'delete',
			label: this._('Delete')
		}, {
			name: 'cancel',
			'default': true,
			label: this._('Cancel')
		}]).then(dojo.hitch(this, function(response) {
			if (response != 'delete') {
				return;
			}

			// chain the UMCP commands for removing the snapshot(s)
			var deferred = new dojo.Deferred();
			deferred.resolve();
			dojo.forEach(ids, function(iid, i) {
				deferred = deferred.then(dojo.hitch(this, function() {
					this.onUpdateProgress(i, ids.length);
					return umc.tools.umcpCommand('uvmm/snapshot/remove', {
						domainURI: this.domainURI,
						snapshotName: iid
					});
				}));
			}, this);

			// finish the progress bar and add error handler
			deferred = deferred.then(dojo.hitch(this, function() {
				this.onUpdateProgress(ids.length, ids.length);
				this.moduleStore.onChange();
			}), dojo.hitch(this, function() {
				umc.dialog.alert(this._('An error ocurred during processing your request.'));
				this.onUpdateProgress(ids.length, ids.length);
				this.moduleStore.onChange();
			}));
		}));
	},

	onUpdateProgress: function(i, n) {
		// event stub
	}
});
