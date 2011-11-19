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

dojo.provide("umc.modules._uvmm.DriveWizard");

dojo.require("umc.widgets.Wizard");
dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.modules._uvmm.types");

dojo.declare("umc.modules._uvmm.DriveWizard", [ umc.widgets.Wizard, umc.i18n.Mixin ], {
	
	domain: null,

	i18nClass: 'umc.modules.uvmm',

	_volumes: null,

	constructor: function() {
		var types = umc.modules._uvmm.types;

		dojo.mixin(this, {
			pages: [{
				name: 'driveType',
				headerText: this._('Add drive'),
				helpText: this._('What type of drive should be created?'),
				widgets: [{
					name: 'driveType',
					type: 'ComboBox',
					staticValues: types.dict2list(types.blockDevices)
				}]
			}, {
				name: 'drive',
				headerText: this._('Add a new drive'),
				helpText: this._('For the drive a new image can be created or an existing one can be chosen. An existing image should only be used by one virtual instance at a time.'),
				widgets: [{
					name: 'driveType',
					type: 'HiddenInput',
					value: ''
				}, {
					name: 'volumeType',
					type: 'ComboBox',
					depends: 'driveType',
					label: this._('Drive type'),
					sortDynamicValues: false,
					dynamicValues: function(options) {
						// show depending on the drive type only specific values
						return dojo.filter(types.diskChoice, function(iitem) {
							return	(options.driveType != 'disk' && iitem.id != 'new') ||
									(options.driveType == 'disk' && iitem.id != 'empty');
						});
					},
					onChange: dojo.hitch(this, '_updateDriveWidgets')
				}, {
					name: 'pool_new',
					type: 'ComboBox',
					label: this._('Pool'),
					description: this._('Each image is located within a so called storage pool, which might be a local directory, a device, an LVM volume or any type of share (e.g. mounted via iSCSI, NFS or CIFS).'),
					dynamicOptions: dojo.hitch(this, function(options) {
						return {
							nodeURI: this._getNodeURI()
						};
					}),
					dynamicValues: types.getPools
				}, {
					name: 'driver_type_new',
					type: 'ComboBox',
					label: this._('Image format'),
					dynamicOptions: dojo.hitch(this, function(options) {
						return {
							domain_type: this.domain.domain_type
						};
					}),
					dynamicValues: types.getImageFormat
				}, {
					name: 'volumeFilename_new',
					type: 'TextBox',
					required: true,
					label: this._('Filename'),
					validator: dojo.hitch(this, function(val) {
						var regExp = /^[^./][^/]*$/;
						return regExp.test(val) && (!this._volumes || !(val in this._volumes));
					}), 
					invalidMessage: this._('A valid filename cannot contain "/", may not start with "." and may not already exist in the storage pool.'),
					depends: [ 'pool_new', 'driver_type_new' ],
					dynamicValue: dojo.hitch(this, function(options) {
						return dojo.when(types.getVolumes({
							nodeURI: this._getNodeURI(),
							pool: options.pool_new
						}), dojo.hitch(this, function(volumes) {
							// create a map of volumes that exist in the domain and
							// the storage pool
							this._volumes = {};
							dojo.forEach(this.volumes, function(ivol) {
								this._volumes[ivol] = true;
							}, this);
							dojo.forEach(this.domain.disks, function(idisk) {
								this._volumes[idisk.volumeFilename] = true;
							}, this);

							// suggest a filename that does not already exist in the pool
							var pattern = '{name}-{i}.{format}';
							var i = 0;
							var fname = '';
							do {
								fname = dojo.replace(pattern, {
									name: this.domain.name,
									i: i,
									format: options.driver_type_new
								});
								++i;
							} while (fname in this._volumes);
							
							// found one :)
							return fname;
						}));
					})
				}, {
					name: 'size_new',
					type: 'TextBox',
					required: true,
					label: this._('Size (default unit MB)'),
					value: this.domain.profileData && this.domain.profileData.diskspace ? this.domain.profileData.diskspace : '12.0 GB'
				}, {
					name: 'pool_exists',
					type: 'ComboBox',
					label: this._('Pool'),
					description: this._('Each image is located within a so called storage pool, which might be a local directory, a device, an LVM volume or any type of share (e.g. mounted via iSCSI, NFS or CIFS). When selecting a storage pool the list of available images is updated.'),
					dynamicOptions: dojo.hitch(this, function(options) {
						return {
							nodeURI: this._getNodeURI()
						};
					}),
					dynamicValues: types.getPools
				}, {
					name: 'volumeFilename_exists',
					type: 'ComboBox',
					label: this._('Drive image'),
					description: this._('If the required image is not found it might be added by copying the file into the storage pool, e.g. to /var/lib/libvirt/images/ which is the directory of the storage pool local directory. After that go to the previous page an return to this one. The image should now be listed.'),
					depends: [ 'pool_exists', 'driveType' ],
					dynamicOptions: dojo.hitch(this, function(options) {
						return {
							nodeURI: this._getNodeURI(),
							pool: options.pool_exists,
							type: options.driveType
						};
					}),
					dynamicValues: types.getVolumes
				}, {
					name: 'volumeFilename_block',
					type: 'TextBox',
					label: this._('Device filename'),
					required: true,
					description: this._('To bind the drive to a local device the filename of the associated block device must be specified.'),
					depends: 'driveType',
					dynamicValue: function(options) {
						return types.blockDevicePath[options.driveType] || '';
					}
				}]
			}]
		});
	},

	_getNodeURI: function() {
		if (this.domain.nodeURI) {
			return this.domain.nodeURI;
		}
		return this.domain.domainURI.split('#')[0];
	},

	getValues: function() {
		var _values = this.inherited(arguments);
		var values = { 
			device: _values.driveType,
			volumeFilename: _values['volumeFilename_' + _values.volumeType] || '',
			pool: _values['pool_' + _values.volumeType] || '',
			size: _values['size_' + _values.volumeType] || '',
			driver_type: _values['driver_type_' + _values.volumeType] || '',
			volumeType: _values.volumeType
		};
		return values;
	},

	canFinish: function(values) {
		//var volumeType = this.getWidget('volumeType').getValue('value');
		var valid = true;
		umc.tools.forIn(this._pages.drive._form._widgets, function(iname, iwidget) {
			valid = valid && (!iwidget.get('visible') || false !== iwidget.isValid());
			return valid;
		}, this);
		if (!valid) {
			umc.dialog.alert(this._('The entered data is not valid. Please correct your input.'));
		}
		return valid;
	},

	next: function(pageName) {
		var nextName = this.inherited(arguments);
		if (pageName == 'driveType') {
			// update the device type of the drive page
			// ... will cause the ComboBoxes to update themselves
			this.getWidget('drive', 'driveType').set('value', this.getWidget('driveType', 'driveType').get('value'));
		}
		return nextName;
	},

	_updateDriveWidgets: function(driveType) {
		// update visibility
		var volumeType = this.getWidget('volumeType').getValue('value');
		umc.tools.forIn(this._pages.drive._form._widgets, function(iname, iwidget) {
			var visible = iname.indexOf('_') < 0 || (volumeType && iname.indexOf(volumeType) >= 0);
			iwidget.set('visible', visible);
		}, this);
	}
});





