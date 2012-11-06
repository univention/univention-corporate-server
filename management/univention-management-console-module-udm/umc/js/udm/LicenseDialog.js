/*
 * Copyright 2011-2012 Univention GmbH
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
	"dijit/Dialog",
	"umc/tools",
	"umc/dialog",
	"umc/render",
	"umc/widgets/ContainerWidget",
	"umc/widgets/StandbyMixin",
	"umc/widgets/Button",
	"dojo/text!umc/modules/udm/license.html",
	"dojo/text!umc/modules/udm/license_v2.html",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, Dialog, tools, dialog, render, ContainerWidget, StandbyMixin, Button, licenseHtml, license_v2Html, _) {

	return declare('umc.modules.udm.LicenseDialog', [ Dialog, StandbyMixin ], {
		// summary:
		//		Class that provides the license Dialog for UCS. It shows details about the current license and support importing a new one.

		// the widget's class name as CSS class
		'class': 'umcPopup',

		_widgets: null,

		_container: null,

		licenseInfo: null,

		buildRendering: function() {
			this.inherited(arguments);

			// put buttons into separate container
			var _buttonContainer = new ContainerWidget({
				style: 'text-align: center;',
				'class': 'umcButtonRow'
			});
			_buttonContainer.addChild( new Button( {
				label: _( 'Close' ),
				defaultButton: true,
				onClick: lang.hitch( this, function() {
					this.hide();
				} )
				} ) );

			var widgets = [
				{
					type : 'Text',
					name : 'message',
					style : 'width: 100%',
					content : ''
				}, {
					type : 'TextArea',
					name : 'licenseText',
					label : _( 'License text' )
				}, {
					type : 'Uploader',
					name : 'licenseUpload',
					label : _( 'License upload' ),
					command: 'udm/license/import',
					onUploaded: lang.hitch( this, function( result ) {
						if ( typeof  result  == "string" ) {
							return;
						}
						if ( result.success ) {
							dialog.notify( _( 'License was imported successfully' ) );
						} else {
							dialog.alert( _( 'Failed to import license' ) + ': ' + result.message );
						}
					} )
				}, {
					type : 'Text',
					name : 'ffpu',
					content : ''
				}, {
					type : 'Text',
					name : 'titleImport',
					style : 'width: 100%',
					content : lang.replace( '<h1>{title}</h1>', { title: _( 'License import' ) } )
				} ];
			var buttons = [  {
				type : 'Button',
				name : 'btnLicenseText',
				label : _( 'Upload' ),
				callback: lang.hitch( this, function() {
					this.standby( true );
					tools.umcpCommand( 'udm/license/import', {
						'license': this._widgets.licenseText.get( 'value' )
					} ).then( lang.hitch( this, function( response ) {
						this.standby( false );
						if ( ! response.result  instanceof Array || false === response.result[ 0 ].success ) {
							dialog.alert( _( 'The import of the license has failed: ' ) + response.result[ 0 ].message );
						} else {
							dialog.alert( _( 'The license has been imported succussfully' ) );
						}
					} ),
					lang.hitch( this, function( response ) {
						this.standby( false );
					} ) );
				} )
			} ];

			this._widgets = render.widgets( widgets );
			var _buttons = render.buttons( buttons );
			var _container = render.layout( [ 'message', 'titleImport', 'licenseUpload', [ 'licenseText', 'btnLicenseText' ], 'ffpu' ], this._widgets, _buttons );

			var _content = new ContainerWidget({});
			_content.addChild( _container );

			// put the layout together
			this._container = new ContainerWidget({
				style: 'width: 600px'
			});
			this._container.addChild( _content );
			this._container.addChild( _buttonContainer );
			this.addChild(this._container);
			this.on('hide', lang.hitch(this, function() {
				this.destroyRecursive();
			}));

			// attach layout to dialog
			// this.set( 'content', this._container );
			this.set( 'title', _( 'UCS license' ) );

			this.updateLicense();
		},

		_limitInfo: function( limit ) {
			if ( this.licenseInfo.licenses[ limit ] === null ) {
				return  _( 'unlimited' );
			} else {
				return _( '%s (used: %s)', this.licenseInfo.licenses[ limit ], this.licenseInfo.real[ limit] );
			}
		},

		updateLicense: function() {
			this.standby( true );
			tools.umcpCommand( 'udm/license/info' ).then( lang.hitch( this, function( response ) {
				this.licenseInfo = response.result;
				this.showLicense();
				this.standby( false );
			} ), lang.hitch( this, function() {
				this.standby( false );
				dialog.alert( _( 'Updating the license information has failed' ) );
			} ) );
		},

		showLicense: function() {
			if ( ! this.licenseInfo ) {
				return;
			}
			// content: license info and upload widgets
			var product = '';
			if ( this.licenseInfo.oemProductTypes.length === 0 ) {
				product = this.licenseInfo.licenseTypes.join( ', ' );
			} else {
				product = this.licenseInfo.oemProductTypes.join( ', ' );
			}
			var free_license_info = '';
			if ( this.licenseInfo.baseDN == 'Free for personal use edition' ) {
				free_license_info = _( '<p>The "free for personal use" edition of Univention Corporate Server is a special software license which allows users free use of the Univention Corporate Server and software products based on it for private purposes acc. to § 13 BGB (German Civil Code).</p><p>In the scope of this license, UCS can be downloaded, installed and used from our servers. It is, however, not permitted to make the software available to third parties to download or use it in the scope of a predominantly professional or commercial usage.</p><p>The license of the "free for personal use" edition of UCS occurs in the scope of a gift contract. We thus exclude all warranty and liability claims, except in the case of deliberate intention or gross negligence. We emphasise that the liability, warranty, support and maintance claims arising from our commercial software contracts do not apply to the "free for personal use" edition.</p><p>We wish you a lot of happiness using the "free for personal use" edition of Univention Corporate Server and look forward to receiving your feedback. If you have any questions, please consult our forum, which can be found on the Internet at http://forum.univention.de/.</p>' );
			}

			var keys, message;
			if ( this.licenseInfo.licenseVersion === '1' ) {

				// substract system accounts
				if ( this.licenseInfo.real.account >= this.licenseInfo.sysAccountsFound ) {
					this.licenseInfo.real.account -= this.licenseInfo.sysAccountsFound;
				}

				keys = {
					title : _( 'Current license' ),
					labelBase : _( 'LDAP base' ),
					base: this.licenseInfo.baseDN,
					labelUser : _( 'User accounts' ),
					user: this._limitInfo( 'account' ),
					labelClients : _( 'Clients' ),
					clients: this._limitInfo( 'client' ),
					labelDesktops : _( 'Desktops' ),
					desktops: this._limitInfo( 'desktop' ),
					labelEndDate : _( 'Expiry date' ),
					endDate: _( this.licenseInfo.endDate ),
					labelProduct : _( 'Valid product types' ),
					product: product
				};

				message = licenseHtml;

			} else {

				// substract system accounts
				if ( this.licenseInfo.real.users >= this.licenseInfo.sysAccountsFound ) {
					this.licenseInfo.real.users -= this.licenseInfo.sysAccountsFound;
				}

				keys = {
					title : _( 'Current license' ),
					labelBase : _( 'LDAP base' ),
					base: this.licenseInfo.baseDN,
					labelUser : _( 'User accounts' ),
					user: this._limitInfo( 'users' ),
					labelServers : _( 'Servers' ),
					servers: this._limitInfo( 'servers' ),
					labelManagedClients : _( 'Managed Clients' ),
					managedclients: this._limitInfo( 'managedclients' ),
					labelCorporateClients : _( 'Corporate Clients' ),
					corporateclients: this._limitInfo( 'corporateclients' ),
					labelDVSUsers : _( 'DVS Users' ),
					dvsusers: this._limitInfo( 'virtualdesktopusers' ),
					labelDVSClients : _( 'DVS Clients' ),
					dvsclients: this._limitInfo( 'virtualdesktopclients' ),
					labelSupport : _( 'Server with standard support' ),
					support: this.licenseInfo.support,
					labelPremiumSupport : _( 'Server with premium support' ),
					premiumsupport: this.licenseInfo.premiumSupport,
					labelKeyID : _( 'Key ID' ),
					keyID: _( this.licenseInfo.keyID ),
					labelEndDate : _( 'Expiry date' ),
					endDate: _( this.licenseInfo.endDate ),
					labelProduct : _( 'Valid product types' ),
					product: product
				};

				message = license_v2Html;
			}

			this._widgets.message.set( 'content', lang.replace( message, keys ) );
			this._widgets.ffpu.set( 'content', this.licenseInfo.baseDN == 'Free for personal use edition' ? free_license_info : '' );

			// recenter dialog
			this._size();
			this._position();
		}

	});
});

