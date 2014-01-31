/*
 * Copyright 2011-2014 Univention GmbH
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
	"dojo/_base/array",
	"dojo/when",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Wizard",
	"umc/modules/uvmm/types",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, when, tools, dialog, Wizard, types, _) {

	return declare("umc.modules.uvmm.DriveWizard", [ Wizard ], {

		domain: null,

		_volumes: null,

		driveType: null, // pre-defined drive will automatically set the drive type and start on page 'drive'

		constructor: function(props) {
			props = props || {};
			lang.mixin(this, {
				pages: [{
					name: 'driveType',
					headerText: _('Add drive'),
					helpText: _('What type of drive should be created?'),
					widgets: [{
						name: 'driveType',
						type: 'ComboBox',
						staticValues: types.dict2list(types.blockDevices)
					}]
				}, {
					name: 'drive',
					headerText: _('Add a new drive'),
					helpText: _('For the drive a new image can be created or an existing one can be chosen. An existing image should only be used by one virtual machine at a time.'),
					widgets: [{
						name: 'driveType',
						type: 'HiddenInput',
						value: ''
					}, {
						name: 'volumeType',
						type: 'ComboBox',
						depends: ['driveType'],
						label: _('Drive type'),
						sortDynamicValues: false,
						dynamicValues: lang.hitch(this, function(options) {
							// show depending on the drive type only specific values
							return array.filter(types.diskChoice, lang.hitch(this, function(iitem) {
								if (this.domain.domain_type === 'xen' && this.domain.os_type === 'xen' && iitem.id === 'empty') {
									return false;
								}
								if (options.driveType == 'disk') {
									return iitem.id != 'empty';
								} else { // cdrom floppy
									return iitem.id != 'new';
								}
							}));
						}),
						onChange: lang.hitch(this, '_updateDriveWidgets')
					}, {
						name: 'pool_new',
						type: 'ComboBox',
						label: _('Pool'),
						description: _('Each image is located within a so called storage pool, which might be a local directory, a device, an LVM volume or any type of share (e.g. mounted via iSCSI, NFS or CIFS).'),
						dynamicOptions: lang.hitch(this, function(options) {
							return {
								create: true,
								nodeURI: this._getNodeURI()
							};
						}),
						dynamicValues: types.getPools
					}, {
						name: 'driver_type_new',
						type: 'ComboBox',
						label: _('Image format'),
						depends: ['driveType'],
						dynamicOptions: lang.hitch(this, function(options) {
							return {
								type: options.driveType,
								domain_type: this.domain.domain_type
							};
						}),
						dynamicValues: types.getImageFormat
					}, {
						name: 'volumeFilename_new',
						type: 'TextBox',
						required: true,
						label: _('Filename'),
						validator: lang.hitch(this, function(val) {
							var regExp = /^[^.\/][^\/]*$/;
							return regExp.test(val) && (!this._volumes || !(val in this._volumes));
						}),
						invalidMessage: _('A valid filename cannot contain "/", may not start with "." and may not already exist in the storage pool.'),
						depends: [ 'pool_new', 'driver_type_new' ],
						dynamicValue: lang.hitch(this, function(options) {
							return when(types.getVolumes({
								nodeURI: this._getNodeURI(),
								pool: options.pool_new
							}), lang.hitch(this, function(volumes) {
								// create a map of volumes that exist in the domain and
								// the storage pool
								this._volumes = {};
								array.forEach(this.volumes, function(ivol) {
									this._volumes[ivol] = true;
								}, this);
								array.forEach(this.domain.disks, function(idisk) {
									this._volumes[idisk.volumeFilename] = true;
								}, this);

								// suggest a filename that does not already exist in the pool
								var pattern = '{name}-{i}.{format}';
								var i = 0;
								var fname = '';
								do {
									fname = lang.replace(pattern, {
										name: this.domain.name,
										i: i,
										format: options.driver_type_new
									});
									++i;
								} while (fname in this._volumes);

								// found one
								return fname;
							}));
						})
					}, {
						name: 'size_new',
						type: 'TextBox',
						required: true,
						label: _('Size (default unit MB)'),
						value: lang.getObject('domain.profileData.diskspace', false, props) || '12.0 GB'
					}, {
						name: 'pool_exists',
						type: 'ComboBox',
						label: _('Pool'),
						description: _('Each image is located within a so called storage pool, which might be a local directory, a device, an LVM volume or any type of share (e.g. mounted via iSCSI, NFS or CIFS). When selecting a storage pool the list of available images is updated.'),
						dynamicOptions: lang.hitch(this, function(options) {
							return {
								create: false,
								nodeURI: this._getNodeURI()
							};
						}),
						dynamicValues: types.getPools,
						onChange: lang.hitch(this, function(newVal) {
							// File type is only relevant for file pools
							var poolWidget = this._pages.drive._form.getWidget('pool_exists');
							var drvTypeWidget = this._pages.drive._form.getWidget('driver_type_exists');
							var items = array.filter(poolWidget.getAllItems(), function(iitem) {
								return iitem.id == newVal;
							});
							if (items.length && types.POOLS_FILE[items[0].type]) {
								drvTypeWidget.set('visible', true);
							} else {
								drvTypeWidget.set('value', 'raw');
								drvTypeWidget.set('visible', false);
							}
						})
					}, {
						name: 'volumeFilename_exists',
						type: 'ComboBox',
						label: _('Drive image'),
						description: _('If the required image is not found it might be added by copying the file into the storage pool, e.g. to /var/lib/libvirt/images/ which is the directory of the storage pool local directory. After that go to the previous page an return to this one. The image should now be listed.'),
						depends: [ 'pool_exists', 'driveType' ],
						dynamicOptions: lang.hitch(this, function(options) {
							return {
								nodeURI: this._getNodeURI(),
								pool: options.pool_exists,
								type: options.driveType
							};
						}),
						dynamicValues: types.getVolumes,
						onChange: lang.hitch(this, function(newVal) {
							var volFileWidget = this._pages.drive._form.getWidget('volumeFilename_exists');
							var drvTypeWidget = this._pages.drive._form.getWidget('driver_type_exists');
							var items = array.filter(volFileWidget.getAllItems(), function(iitem) {
								return iitem.id == newVal;
							});
							if (items.length) {
								drvTypeWidget.set('value', items[0].type);
							} else {
								drvTypeWidget.set('value', 'raw');
							}
						})
					}, {
						name: 'driver_type_exists',
						type: 'ComboBox',
						label: _('Image format'),
						depends: ['driveType'],
						dynamicOptions: lang.hitch(this, function(options) {
							return {
								type: options.driveType,
								domain_type: this.domain.domain_type
							};
						}),
						dynamicValues: types.getImageFormat
					}, {
						name: 'volumeFilename_block',
						type: 'TextBox',
						label: _('Device filename'),
						required: true,
						description: _('To bind the drive to a local device the filename of the associated block device must be specified.'),
						depends: ['driveType'],
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
			var mode = _values.volumeType; // Mode of operation: new exists block empty
			var values = {
				device: _values.driveType,
				volumeFilename: _values['volumeFilename_' + mode] || '',
				pool: _values['pool_' + mode] || '',
				size: _values['size_' + mode] || '',
				driver_type: _values['driver_type_' + mode] || '',
				volumeType: mode
			};
			if (mode === 'new') {
				values.source = null; // trigger volume creation
			} else {
				values.source = values.volumeFilename;
			}
			return values;
		},

		canFinish: function(values) {
			//var volumeType = this.getWidget('volumeType').getValue('value');
			var valid = true;
			tools.forIn(this._pages.drive._form._widgets, function(iname, iwidget) {
				valid = valid && (!iwidget.get('visible') || false !== iwidget.isValid());
				return valid;
			}, this);
			if (!valid) {
				dialog.alert(_('The entered data is not valid. Please correct your input.'));
			}
			return valid;
		},

		next: function(pageName) {
			var nextName = this.inherited(arguments);
			if ( pageName === null && this.driveType ) {
				this.getWidget( 'driveType', 'driveType' ).set( 'value', this.driveType );
				nextName = 'drive';
				pageName = 'driveType';
				this.getPage( 'drive' ).set( 'headerText', _( 'Change medium' ) );
			}
			if (pageName == 'driveType') {
				// update the device type of the drive page
				// ... will cause the ComboBoxes to update themselves
				this.getWidget('drive', 'driveType').set('value', this.getWidget('driveType', 'driveType').get('value'));
			}
			return nextName;
		},

		hasPrevious: function(pageName) {
			if (this.driveType) {
				return false;
			} else {
				return this.inherited(arguments);
			}
		},

		_updateDriveWidgets: function(volumeType) {
			// update visibility
			tools.forIn(this._pages.drive._form._widgets, function(iname, iwidget) {
				var visible = iname.indexOf('_') < 0 || (volumeType && iname.indexOf(volumeType) >= 0);
				iwidget.set('visible', visible);
			}, this);
		}
	});
});
