/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._uvmm.types");

dojo.require("umc.tools");


(function() {
	// translation function
	var i18n = new umc.i18n.Mixin({
		i18nClass: 'umc.modules.uvmm'
	});
	var _ = dojo.hitch(i18n, '_');

	var self = umc.modules._uvmm.types;
	dojo.mixin(self, {
		dict2list: function(dict) {
			var list = [];
			umc.tools.forIn(dict, function(ikey, ival) {
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
			{ id: 'utc', label: _('Coordinated Universal Time') },
			{ id: 'localtime', label: _('Local time zone') }
		],
		domainStates: {
			RUNNING : _( 'running' ),
			SHUTOFF : _( 'shut off' ),
			PAUSED : _( 'paused' ),
			IDLE : _( 'running (idle)' ),
			CRASHED : _( 'shut off (crashed)' )
		},
		getDomainStateDescription: function( domain ) {
			var text = self.domainStates[ domain.state ];
			if ( true === domain.suspended ) {
				text += ' ' + _( '(saved state)' );
			}
			return text;
		},
		virtualizationTechnology: [
			{ id: 'kvm-hvm', label: _( 'Full virtualization (KVM)' ) },
			{ id: 'xen-hvm', label: _( 'Full virtualization (XEN)' ) },
			{ id: 'xen-xen', label: _( 'Paravirtualization (XEN)' ) }
		],
		getVirtualizationTechnology: function(options) {
			// return all technologies that are supported by the corresponding
			// opertating system type (KVM/Xen)
			return dojo.filter(self.virtualizationTechnology, function(itech) {
				return itech.id.indexOf(options.domain_type) === 0;
			});
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
		getCPUs: function(options) {
			// query the domain's node and get its number of CPUs
			var nodeURI = options.nodeURI || options.domainURI.split('#')[0];
			return umc.tools.umcpCommand('uvmm/node/query', {
				nodePattern: nodeURI
			}).then(function(data) {
				// query successful
				var list = [ { id: 1, label: '1' } ];
				if (data.result.length) {
					// we got a result
					var nCPU = data.result[0].cpus;
					for (var i = 2; i <= nCPU; ++i) {
						list.push({ id: i, label: '' + i });
					}
				}
				return list;
			}, function() {
				// fallback
				return [ { id: 1, label: '1' } ];
			});
		},
		interfaceModels: {
			'rtl8139': _( 'Default (RealTek RTL-8139)' ),
			'e1000': _( 'Intel PRO/1000' ),
			'netfront': _( 'Paravirtual device (xen)' ),
			'virtio': _( 'Paravirtual device (virtio)' )
		},
		getInterfaceModels: function(options) {
			var list = [];
			umc.tools.forIn(self.interfaceModels, function(ikey, ilabel) {
				if (ikey == 'virtio') {
					 if (options.domain_type == 'kvm') {
						list.push({ id: ikey, label: ilabel });
					 }
				}
				else if (ikey == 'netfront') {
					 if (options.domain_type == 'xen') {
						list.push({ id: ikey, label: ilabel });
					 }
				}
				else {
					list.push({ id: ikey, label: ilabel });
				}
			});
			return list;
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
		getPools: function(options) {
			if (!options.nodeURI) {
				return [];
			}
			return umc.tools.umcpCommand('uvmm/storage/pool/query', {
				nodeURI: options.nodeURI
			}).then(function(data) {
				return dojo.map(data.result, function(iitem) {
					return iitem.name;
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
			return umc.tools.umcpCommand('uvmm/storage/volume/query', {
				nodeURI: options.nodeURI,
				pool: options.pool,
				type: options.type || null
			}).then(function(data) {
				return dojo.map(data.result, function(iitem) {
					return iitem.volumeFilename;
				});
			}, function() {
				// fallback
				return [];
			});
		},
		getImageFormat: function(options) {
			if (!options.domain_type) {
				return [];
			}
			var list = [ { id: 'raw', label: _('Simple format (raw)') } ];
			if (options.domain_type == 'kvm') {
				list.push({ id: 'qcow2', label: _('Extended format (qcow2)') });
			}
			return list;
		},
		getNodes: function() {
			return umc.tools.umcpCommand('uvmm/query', {
				type: 'node',
				nodePattern: '*'
			}).then(function(data) {
				return data.result;
			});
		},
		getProfiles: function(options) {
			return umc.tools.umcpCommand('uvmm/profile/query', {
				nodeURI: options.nodeURI
			}).then(function(data) {
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
	});
})();

