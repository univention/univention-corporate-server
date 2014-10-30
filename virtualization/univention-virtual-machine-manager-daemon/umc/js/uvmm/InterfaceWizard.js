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
	"dojo/dom-class",
	"umc/widgets/Wizard",
	"umc/widgets/ComboBox",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/modules/uvmm/types",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, domClass, Wizard, ComboBox, Text, TextBox, types, _) {

	return declare("umc.modules.uvmm.InterfaceWizard", [ Wizard ], {
		autoHeight: true,

		constructor: function(props, values) {
			values = values || {};
			// mixin the page structure
			lang.mixin(this, {
				pages: [{
					name: 'interface',
					widgets: [{
						name: 'helpText',
						type: Text,
						content: _('Two types of network interfaces are support. The first one is <i>Bridge</i> that requires a static network connection on the physical server that is configurated to be used for bridging. By default the network interface called eth0 is setup for such a case on each UVMM node. If a virtual machine should have more than one bridging network interface, additional network interfaces on the physical server must be configured first. The second type is <i>NAT</i> provides a private network for virtual machines on the physical server and permits access to the external network. This network typ is useful for computers with varying network connections like notebooks. For such an interface the network configuration of the UVMM node needs to be modified. This is done automatically by the UVMM service when starting the virtual machine. Further details about the network configuration can be found in <a target="_blank" href="http://docs.univention.de/manual-4.0.html#uvmm:networkinterfaces">the manual</a>.')
					}, {
						name: 'type',
						type: ComboBox,
						sizeClass: 'OneThird',
						label: _('Type'),
						staticValues: types.interfaceTypes,
						onChange: lang.hitch( this, '_typeDescription' ),
						value: values.type || 'bridge'
					}, {
						name: 'typeDescription',
						type: Text,
						style: 'width: auto;',
						label: '',
						content: ''
					}, {
						name: 'model',
						sizeClass: 'One',
						type: ComboBox,
						label: _('Driver'),
						staticValues: types.interfaceModels,
						value: values.model || 'rtl8139'
					}, {
						name: 'source',
						sizeClass: 'OneThird',
						type: TextBox,
						label: _('Source'),
						description: _('The source is the name of the network interface on the phyiscal server that is configured for bridging. By default it is eth0.'),
						value: values.source || 'eth0',
						required: true
					}, {
						name: 'mac_address',
						sizeClass: 'One',
						type: TextBox,
						regExp: '^([0-9A-Fa-f]?[02468AaCcEe])([:-]?[0-9A-Fa-f]{1,2}){5}$',
						invalidMessage: _('Invalid MAC address: The address must be unicast and should have the form "02:23:45:67:89:AB".'),
						label: _('MAC address'),
						value: values.mac_address || ''
					}],
					layout: [
						['type', 'model'],
						'typeDescription',
						['source', 'mac_address']
					]
				}]
			});
		},

		_typeDescription: function() {
			var widget = this.getWidget( 'typeDescription' );
			if ( this.getWidget( 'type' ).get( 'value' ).indexOf( 'network:' ) === 0 ) {
				widget.set( 'content' , 'By default the private network is 192.168.122.0/24' );
				domClass.add( widget.domNode, 'umcPageNote' );
				this.getWidget( 'source' ).set( 'visible', false );
			} else {
				widget.set( 'content' , '' );
				domClass.remove( widget.domNode, 'umcPageNote' );
				this.getWidget( 'source' ).set( 'visible', true );
			}
		},

		canFinish: function(values) {
			return this.getWidget('source').isValid() && this.getWidget('mac_address').isValid();
		}
	});
});
