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
	"dojo/_base/array",
	"dojo/_base/lang",
	"dojox/string/sprintf",
	"umc/tools",
	"umc/i18n!umc/modules/uvmm"
], function(array, lang, sprintf, tools, _) {
	var self = {
		dict2list: function(dict) {
			var list = [];
			tools.forIn(dict, function(ikey, ival) {
				list.push({
					id: ikey,
					label: ival
				});
			});
			return list;
		},
		architecture: [
			{ id: 'i686', label: '32 bit' },
			{ id: 'x86_64', label: '64 bit' }
		],
		bootDevices: [
			{ id: 'hd', label: _('Hard drive') },
			{ id: 'cdrom', label: _( 'CDROM drive' ) },
			{ id: 'network', label: _( 'Network' ) }
		],
		rtcOffset: [
			{ id: 'utc', label: _('Coordinated Universal Time'), vt: ['kvm-hvm'] },
			{ id: 'localtime', label: _('Local time zone'), vt: ['kvm-hvm'] },
			{ id: 'variable', label: _('Guest controlled'), vt: ['kvm-hvm'] }
		],
		domainStates: {
			RUNNING : _( 'running' ),
			SHUTOFF : _( 'shut off' ),
			PAUSED : _( 'paused' ),
			SUSPENDED : _( 'suspended' ),
			IDLE : _( 'running (idle)' ),
			CRASHED : _( 'shut off (crashed)' ),
			TERMINATED : _( 'terminated' ),
			PENDING : _( 'pending' ),
			PMSUSPENDED : _( 'suspended' )
		},
		getDomainStateDescription: function( domain ) {
			var text = self.domainStates[ domain.state ];
			if ( true === domain.suspended ) {
				text += ' ' + _( '(saved state)' );
			}
			return text;
		},
		activeStates: {'RUNNING': true, 'IDLE': true, 'PAUSED': true},
		isActive: function(domain) {
			return Boolean(domain.state in self.activeStates || domain.suspended);
		},
		patternCapacity: /^([0-9]+(?:[,.][0-9]+)?)[ \t]*(([KkMmGgTtPp])(?:[Ii]?[Bb])?|[Bb])?$/,
		parseCapacity: function(size, defaultUnit) {
			var match = self.patternCapacity.exec(size);
			if (match === null) {
				return null;
			}
			var mem = parseFloat(match[1].replace(',', '.'));
			var unit = (match[2] ? match[3] : defaultUnit) || '';
			switch (unit) {
				case 'P': case 'p':
					mem *= 1024;
					/* falls through */
				case 'T': case 't':
					mem *= 1024;
					/* falls through */
				case 'G': case 'g':
					mem *= 1024;
					/* falls through */
				case 'M': case 'm':
					mem *= 1024;
					/* falls through */
				case 'K': case 'k':
					mem *= 1024;
			}
			return Math.floor(mem);
		},
		prettyCapacity: function(val) {
			// convert storage capacity to pretty human readable text
			var unit;
			if (undefined === val || null === val || "" === val) {
				return '';
			} else if (val < 1024) {
				return sprintf('%d B', val);
			} else if (val < (1024 * 1024)) {
				unit = 'KiB';
				val /= 1024.0;
			} else if (val < (1024 * 1024 * 1024)) {
				unit = 'MiB';
				val /= 1024.0 * 1024.0;
			} else if (val < (1024 * 1024 * 1024 * 1024)) {
				unit = 'GiB';
				val /= 1024.0 * 1024.0 * 1024.0;
			} else if (val < (1024 * 1024 * 1024 * 1024 * 1024)) {
				unit = 'TiB';
				val /= 1024.0 * 1024.0 * 1024.0 * 1024.0;
			} else {
				unit = 'PiB';
				val /= 1024.0 * 1024.0 * 1024.0 * 1024.0 * 1024.0;
			}
			return sprintf('%2.2lf %s', val, unit);
		},
		keyboardLayout: [
			{ id: 'ar', label: _('Arabic') },
			{ id: 'da', label: _('Danish') },
			{ id: 'de', label: _('German') },
			{ id: 'de-ch', label: _('German-Switzerland') },
			{ id: 'en-gb', label: _('English-Britain') },
			{ id: 'en-us', label: _('English-America') },
			{ id: 'es', label: _('Spanish') },
			{ id: 'et', label: _('Estonian') },
			{ id: 'fi', label: _('Finnish') },
			{ id: 'fo', label: _('Faroese') },
			{ id: 'fr', label: _('French') },
			{ id: 'fr-be', label: _('French-Belgium') },
			{ id: 'fr-ca', label: _('French-Canada') },
			{ id: 'fr-ch', label: _('French-Switzerland') },
			{ id: 'hr', label: _('Croatian') },
			{ id: 'hu', label: _('Hungarian') },
			{ id: 'is', label: _('Icelandic') },
			{ id: 'it', label: _('Italian') },
			{ id: 'ja', label: _('Japanese') },
			{ id: 'lt', label: _('Lithuanian') },
			{ id: 'lv', label: _('Latvian') },
			{ id: 'mk', label: _('Macedonian') },
			{ id: 'nl', label: _('Dutch') },
			{ id: 'nl-be', label: _('Dutch-Belgium') },
			{ id: 'no', label: _('Norwegian') },
			{ id: 'pl', label: _('Polish') },
			{ id: 'pt', label: _('Portuguese') },
			{ id: 'pt-br', label: _('Portuguese-Brasil') },
			{ id: 'ru', label: _('Russian') },
			{ id: 'sl', label: _('Slovene') },
			{ id: 'sv', label: _('Swedish') },
			{ id: 'th', label: _('Thai') },
			{ id: 'tr', label: _('Turkish') }
		],
		setCPUs: function(cpus, widget) {
			var list = [{id: 1, label: '1'}];
			for (var i = 2; i <= cpus; ++i) {
				list.push({id: i, label: '' + i});
			}
			widget.set('staticValues', list);
			widget._clearValues();
			widget._setStaticValues();
		},
		interfaceModels: {
			'rtl8139': _( 'Default (RealTek RTL-8139)' ),
			'e1000': _( 'Intel PRO/1000' ),
			'virtio': _( 'Paravirtual device (virtio)' )
		},
		interfaceTypes: [
			{ id: 'bridge', label: _( 'Bridge' ) },
			{ id: 'network:default', label: _( 'NAT' ) }
		],
		blockDevices: {
			'cdrom': _( 'CD/DVD-ROM drive' ),
			'disk': _( 'Hard drive' ),
			'floppy': _( 'Floppy drive' )
		},
		blockDevicePath: {
			disk: '/dev/',
			cdrom: '/dev/cdrom',
			floppy: '/dev/fd0'
		},
		diskChoice: [
			{ id: 'new', label: _('Create a new image') },
			{ id: 'exists', label: _('Choose existing image') },
			{ id: 'block', label: _('Use a local device') },
			{ id: 'empty', label: _('No media') }
		],
		cpuModels: [
			{ id: "", label: _("Default") },

			{ id: "qemu32", label: "QEMU 32" },
			{ id: "qemu64", label: "QEMU 64" },
			{ id: "kvm32", label: "QEMU 32 [KVM]" },
			{ id: "kvm64", label: "QEMU 64 [KVM]" },
			{ id: "cpu64-rhel5", label: "QEMU 64 [RHEL5]" },
			{ id: "cpu64-rhel6", label: "QEMU 64 [RHEL6]" },

			{ id: "486", label: "Intel 486" },
			{ id: "pentium", label: "Intel Pentium" },
			{ id: "pentium2", label: "Intel Pentium 2" },
			{ id: "pentium3", label: "Intel Pentium 3" },
			{ id: "pentiumpro", label: "Intel Pentium Pro" },
			{ id: "coreduo", label: "Intel Core Duo" },
			{ id: "core2duo", label: "Intel Core 2 Duo" },
			{ id: "Conroe", label: "Intel Conroe" },
			{ id: "Penryn", label: "Intel Penryn" },

			{ id: "Nehalem", label: "Intel Nehalem" },
			{ id: "Nehalem-IBRS", label: "Intel Nehalem [IBRS]" },
			{ id: "Westmere", label: "Intel Westmere" },
			{ id: "Westmere-IBRS", label: "Intel Westmere [IBRS]" },
			{ id: "SandyBridge", label: "Intel Sandy Bridge" },
			{ id: "SandyBridge-IBRS", label: "Intel Sandy Bridge [IBRS]" },
			{ id: "IvyBridge", label: "Intel Ivy Bridge" },
			{ id: "IvyBridge-IBRS", label: "Intel Ivy Bridge [IBRS]" },
			{ id: "Haswell", label: "Intel Haswell" },
			{ id: "Haswell-IBRS", label: "Intel Haswell [IBRS]" },
			{ id: "Haswell-noTSX", label: "Intel Haswell [noTSX]" },
			{ id: "Haswell-noTSX-IBRS", label: "Intel Haswell [noTSX,IBRS]" },
			{ id: "Broadwell", label: "Intel Broadwell" },
			{ id: "Broadwell-IBRS", label: "Intel Broadwell [IBRS]" },
			{ id: "Broadwell-noTSX", label: "Intel Broadwell [noTSX]" },
			{ id: "Broadwell-noTSX-IBRS", label: "Intel Broadwell [noTSX,IBRS]" },
			{ id: "Skylake-Client", label: "Intel Skylake Client" },
			{ id: "Skylake-Client-IBRS", label: "Intel Skylake Client [IBRS]" },

			{ id: "athlon", label: "AMD Athlon" },
			{ id: "phenom", label: "AMD Phenom" },
			{ id: "Opteron_G1", label: "AMD Opteron G1" },
			{ id: "Opteron_G2", label: "AMD Opteron G2" },
			{ id: "Opteron_G3", label: "AMD Opteron G3" },
			{ id: "Opteron_G4", label: "AMD Opteron G4" },
			{ id: "Opteron_G5", label: "AMD Opteron G5"}

			// { id: "n270", label: "Intel Atom N270" },
		],
		driverCache: {
			'default': _('Hypervisor default'),
			'none': _('No host caching, no forced sync (none)'),
			'writethrough': _('Read caching, forced sync (write-through)'),
			'writeback': _('Read/write caching, no forced sync (write-back)'),
			'directsync': _('No host caching, forced sync (direct-sync)'),
			'unsafe': _('Read/write caching, sync filtered out (unsafe)')
		},
		POOLS_FILE: { // storage pools which contain files
			dir: true,
			fs: true,
			netfs: true
		},
		getPools: function(options) {
			if (!options.nodeURI) {
				return [];
			}
			// volumes can be created in these pools
			return tools.umcpCommand('uvmm/storage/pool/query', {
				nodeURI: options.nodeURI
			}).then(function(data) {
				return array.map(array.filter(data.result, function(iitem) {
						return options.create ? iitem.available > 0 : true;
					}), function(iitem) {
						var label = iitem.name;
						if (options.create) {
							label += lang.replace(_(' ({avail} free)'), {avail: self.prettyCapacity(iitem.available)});
						}
						return {
							id: iitem.name,
							type: iitem.type,
							available: iitem.available,
							label: label
						};
				});
			}, function() {
				// fallback
				return [];
			});
		},
		getVolumes: function(options) {
			if (!options.nodeURI || !options.pool) {
				return [];
			}
			return tools.umcpCommand('uvmm/storage/volume/query', {
				nodeURI: options.nodeURI,
				pool: options.pool,
				type: options.type || null
			}).then(function(data) {
				return array.map(data.result, function(iitem) {
					return {
						id: iitem.source,
						type: iitem.driver_type,
						label: iitem.volumeFilename
					};
				});
			}, function() {
				// fallback
				return [];
			});
		},
		ISO: {id: 'iso', label: _('ISO format (iso)')},
		RAW: {id: 'raw', label: _('Simple format (raw)')},
		QCOW2: {id: 'qcow2', label: _('Extended format (qcow2)'), preselected: true},
		getImageFormat: function(options) {
			var list = [];
			if (!self.POOLS_FILE[options.pool_type]) {
				list.push(self.RAW);
			} else if (options.type == 'cdrom') {
				list.push(self.ISO);
			} else if (options.type == 'floppy') {
				list.push(self.RAW);
			} else {
				list.push(self.RAW);
				list.push(self.QCOW2);
			}
			if (list.length === 1) {
				list = lang.clone(list);
				list[0].preselected = true;
			}
			return list;
		},
		getNodes: function() {
			return tools.umcpCommand('uvmm/node/query', {
				nodePattern: ''
			}).then(function(data) {
				return array.filter( data.result, function( node ) {
					return node.available;
				} );
			});
		},
		getProfiles: function(options) {
			return tools.umcpCommand('uvmm/profile/query', {
				nodeURI: options.nodeURI
			}).then(function(data) {
				return data.result;
			});
		},
		getCloudListKeypair: function(options) {
			return tools.umcpCommand('uvmm/cloud/list/keypair', options).then(function(data) {
				return data.result;
			});
		},
		getCloudListSize: function(options) {
			return tools.umcpCommand('uvmm/cloud/list/size', options).then(function(data) {
				return data.result;
			});
		},
		getCloudListImage: function(options) {
			return tools.umcpCommand('uvmm/cloud/list/image', options).then(function(data) {
				return data.result;
			});
		},
		getCloudListSecgroup: function(options) {
			return tools.umcpCommand('uvmm/cloud/list/secgroup', options).then(function(data) {
				return data.result;
			});
		},
		getCloudListNetwork: function(options) {
			return tools.umcpCommand('uvmm/cloud/list/network', options).then(function(data) {
				return data.result;
			});
		},
		getCloudListSubnet: function(options) {
			return tools.umcpCommand('uvmm/cloud/list/subnet', options).then(function(data) {
				return data.result;
			});
		},
		getNodeType: function( uri ) {
			var colon = uri.indexOf( ':' );
			if ( colon == -1 ) {
				return null;
			}
			return uri.slice( 0, colon );
		}
	};
	return self;
});
