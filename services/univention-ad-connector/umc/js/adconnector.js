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
/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.adconnector");

dojo.require( "umc.i18n" );
dojo.require( "umc.dialog" );
dojo.require( "umc.render" );
dojo.require( "umc.tools" );
dojo.require( "umc.widgets.Module" );
dojo.require( "umc.widgets.Page" );
dojo.require( "umc.widgets.Wizard" );

dojo.declare("umc.modules.adconnector", [ umc.widgets.Module, umc.i18n.Mixin ], {

	standbyOpacity: 1.00,

	_widgets: null,

	_buttons: null,

	_page: null,

	i18nClass: 'umc.modules.adconnector',

	buildRendering: function() {
		this.inherited(arguments);
		this.standby(true);

        this._page = new umc.widgets.Page({
            helpText: this._( "This module provides a configuration wizard for the UCS Active Directory Connector to simplify the setup." ),
            headerText: this._( "Configuration of the UCS Active Directory Connector" )
        });
        this.addChild(this._page);

		var widgets = [
			{
				name: 'configured',
				type: 'Text'
			}, {
				name: 'running',
				type: 'Text'
			}, {
				name: 'certificateUpload',
				type: 'InfoUploader',
				showClearButton: false,
				command: 'adconnector/upload/certificate',
				onUploaded: dojo.hitch( this, function( result ) {
					if ( dojo.isString( result ) ) {
						return;
					}
					if ( result.success ) {
						umc.dialog.notify( this._( 'The certificate was imported successfully' ) );
						this.showHideElements();
					} else {
						umc.dialog.alert( this._( 'Failed to import the certificate' ) + ': ' + result.message );
					}
				} )
			}, {
				name: 'download',
				type: 'Text',
				content: dojo.replace( '<a href="/univention-ad-connector/" target="_blank">{0}</a>', [ this._( 'Download the password service for Windows and the UCS certificate' ) ] )
			}
		];
		var buttons = [
			{
				name: 'start',
				label: this._( 'Start UCS Active Directory Connector' ),
				callback: dojo.hitch( this, function() {
					umc.tools.umcpCommand( 'adconnector/service', { action : 'start' } ).then( dojo.hitch( this, function( response ) {
						this.showHideElements();
					} ) );
				} )
			}, {
				name: 'stop',
				label: this._( 'Stop UCS Active Directory Connector' ),
				callback: dojo.hitch( this, function() {
					umc.tools.umcpCommand( 'adconnector/service', { action : 'stop' } ).then( dojo.hitch( this, function( response ) {
						this.showHideElements();
					} ) );
				} )
			}, {
				name: 'configure',
				label: this._( 'Configure UCS Active Directory Connector' ),
				callback: dojo.hitch( this, function() {
					var dlg = new umc.modules._adconnector.WizardDialog( {
						title: this._( 'UCS Active Directory Connector Wizard' )
					} );
					dlg.show();
					this.connect( dlg, 'onSaved', dojo.hitch( this, function() {
						dlg.destroyRecursive();
						this.showHideElements();
					} ) );
				} )
			}
		];

		this._widgets = umc.render.widgets( widgets );
		this._buttons = umc.render.buttons( buttons );

		var _container = umc.render.layout( [ {
			label: this._( 'Configuration' ),
			layout: [ 'configured',  'configure' ]
		}, {
			label: this._( 'UCS Active Directory Connector service' ),
			layout: [ 'running', 'start', 'stop' ]
		}, {
			label: this._( 'Active Directory Server configuration' ),
			layout: [ 'certificateUpload', 'download' ]
		}  ], this._widgets, this._buttons );

		_container.set( 'style', 'overflow: auto' );
		this._page.addChild( _container );

		this.showHideElements();
		this.standby( false );
    },

	showHideElements: function() {
		umc.tools.umcpCommand( 'adconnector/state' ).then( dojo.hitch( this, function( response ) {
			if ( response.result.configured ) {
				this._widgets.configured.set( 'content', this._( 'The configuration process has been finished and all required settings for UCS Active Directory Connector are set.' ) );
			} else {
				this._widgets.configured.set( 'content', this._( 'The configuration process has not been started yet or is incomplete.' ) );
			}
			if ( ! response.result.certificate ) {
				this._widgets.certificateUpload.set( 'value', this._( 'The Active Directory certificate has not been installed yet.' ) );
			} else {
				this._widgets.certificateUpload.set( 'value', this._( 'The Active Directory certificate has been successfully installed.' ) );
			}
			if ( response.result.running ) {
				this._widgets.running.set( 'content', this._( 'UCS Active Directory Connector is currently running.' ) );
				this._buttons.start.set( 'visible', false );
				this._buttons.stop.set( 'visible', true );
			} else {
				var message = this._( 'UCS Active Directory Connector is not running.' );
				if ( ! response.result.configured ) {
					message += this._( ' The Configuation of UCS Active Directory Connector must be completed before the server can be started.' );
					this._buttons.start.set( 'visible', false );
					this._buttons.stop.set( 'visible', false );
				} else {
					this._buttons.start.set( 'visible', true );
					this._buttons.stop.set( 'visible', false );
				}
				this._widgets.running.set( 'content', message );
			}
		} ) );
	}
} );

dojo.declare("umc.modules._adconnector.Wizard", [ umc.widgets.Wizard, umc.i18n.Mixin ], {
	i18nClass: 'umc.modules.adconnector',

	pages: null,

	variables: null,

	constructor: function() {
		this.pages = [ {
			name: 'fqdn',
			helpText: this._( 'The full qualified hostname of the Active Directory server is required' ),
			headerText: this._( 'UCS Active Directory Connector configuration' ),
			widgets: [{
				name: 'LDAP_Host',
				type: 'TextBox',
				required: true,
				regExp: '.+',
				invalidMessage: this._( 'The hostname of the Active Directory server is required' ),
				label: this._( 'Active Directory Server' )
			}, {
				name: 'guess',
				type: 'CheckBox',
				label: this._( 'Automatic determination of the LDAP configuration' )
			}],
			layout: [ 'LDAP_Host', 'guess' ]
		}, {
			name: 'ldap',
			helpText: this._( 'LDAP und kerberos configuration of the Active Directory server needs to be specified for the synchronisation' ),
			headerText: this._( 'LDAP and Kerberos' ),
			widgets: [{
				name: 'LDAP_Base',
				type: 'TextBox',
				required: true,
				sizeClass: 'OneAndAHalf',
				label: this._( 'LDAP base' )
			}, {
				name: 'LDAP_BindDN',
				required: true,
				type: 'TextBox',
				sizeClass: 'OneAndAHalf',
				label: this._( 'LDAP DN of the synchronisation user' )
			}, {
				name: 'LDAP_Password',
				type: 'PasswordBox',
				label: this._( 'Password of the synchronisation user' )
			}, {
				name: 'KerberosDomain',
				type: 'TextBox',
				label: this._( 'Kerberos domain' )
			}],
			layout: [ 'LDAP_Base', 'LDAP_BindDN', 'LDAP_Password', 'KerberosDomain' ]
		}, {
			name: 'sync',
			helpText: this._( 'UCS Active Directory Connector supports three types of synchronisation.' ),
			headerText: this._( 'Synchronisation mode' ),
			widgets: [ {
				name: 'MappingSyncMode',
				type: 'ComboBox',
				staticValues: [
					{
						id: 'sync',
						label: 'AD <-> UCS'
					},{
						id: 'read',
						label: 'AD -> UCS'
					}, {
						id: 'write',
						label: 'UCS -> AD'
					} ],
				label: this._( 'Synchronisation mode' )
			}, {
				name: 'MappingGroupLanguage',
				label: this._( 'System language of Active Directory server' ),
				type: 'ComboBox',
				staticValues: [
					{
						id: 'de',
						label: this._( 'German' )
					}, {
						id: 'en',
						label: this._( 'English' )
					} ]
			} ],
			layout: [ 'MappingSyncMode', 'MappingGroupLanguage' ]
		}, {
			name: 'extended',
			helpText: this._( 'The following settings control the internal behaviour of the UCS Active Directory connector. For all attributes reasonable default values are provided.' ),
			headerText: this._( 'Extended settings' ),
			widgets: [ {
				name: 'PollSleep',
				type: 'TextBox',
				sizeClass: 'OneThird',
				label: this._( 'Poll Interval (seconds)' )
			}, {
				name: 'RetryRejected',
				label: this._( 'Retry interval for rejected objects' ),
				type: 'TextBox',
				sizeClass: 'OneThird'
			}, {
				name: 'DebugLevel',
				label: this._( 'Debug level of Active Directory Connector' ),
				type: 'TextBox',
				sizeClass: 'OneThird'
			}, {
				name: 'DebugFunction',
				label: this._( 'Add debug output for functions' ),
				type: 'CheckBox',
				sizeClass: 'OneThird'
			} ],
			layout: [ 'PollSleep', 'RetryRejected', 'DebugLevel', 'DebugFunction' ]
		} ];
	},

	next: function(/*String*/ currentID) {
		if ( !currentID ) {
			umc.tools.forIn( this.variables, dojo.hitch( this, function( option, value ) {
				var w = this.getWidget( null, option );
				if ( w ) {
					w.set( 'value', value );
				}
			} ) );
			// of no LDAP_base is set activate the automatic determination
			if ( !this.variables.LDAP_base ) {
				this.getWidget( 'fqdn', 'guess' ).set( 'value', true );
			}
		} else if (currentID == 'fqdn') {
			var nameWidget = this.getWidget( 'LDAP_Host' );
			if ( ! nameWidget.isValid() ) {
				nameWidget.focus();
				return null;
			}

			var guess = this.getWidget( 'fqdn', 'guess' );
			if ( guess.get( 'value' ) ) {
				this.standby( true );
				var server = this.getWidget( 'fqdn', 'LDAP_Host' );
				umc.tools.umcpCommand( 'adconnector/guess', { 'LDAP_Host' : server.get( 'value' ) } ).then( dojo.hitch( this, function( response ) {
					if ( response.result.LDAP_Base ) {
						this.getWidget( 'ldap', 'LDAP_Base' ).set( 'value', response.result.LDAP_Base );
						this.getWidget( 'ldap', 'LDAP_BindDN' ).set( 'value', 'cn=Administrator,cn=users,' + response.result.LDAP_Base );
						this.getWidget( 'ldap', 'KerberosDomain' ).set( 'value', umc.tools.explodeDn( response.result.LDAP_Base, true ).join( '.' ) );
					} else {
						umc.dialog.notify( response.result.message );
					}
					this.standby( false );
				} ) );
			}
		} else if ( currentID == 'ldap' ) {
			var valid = true;
			dojo.forEach( [ 'LDAP_Base', 'LDAP_BindDN', 'LDAP_Password' ], dojo.hitch( this, function( widgetName ) {
				if ( ! this.getWidget( widgetName ).isValid() ) {
					this.getWidget( widgetName ).focus();
					valid = false;
					return false;
				}
			} ) );
			if ( !valid ) {
				return null;
			}

			var password = this.getWidget( 'ldap', 'LDAP_Password' );
			if ( ! this.variables.passwordExists && ! password.get( 'value' ) ) {
				umc.dialog.alert( this._( 'The password for the synchronisation account is required!' ) );
				return currentID;
			}
		}

		return this.inherited( arguments );
	},

	onFinished: function( values ) {
		this.standby( true );
		umc.tools.umcpCommand( 'adconnector/save', values ).then( dojo.hitch( this, function( response ) {
			if ( !response.result.success ) {
				umc.dialog.alert( response.result.message );
			} else {
				umc.dialog.notify( response.result.message );
			}
			this.standby( false );
		} ) );
	}
});

dojo.declare("umc.modules._adconnector.WizardDialog", [ dijit.Dialog, umc.widgets.StandbyMixin, umc.i18n.Mixin ], {
	// summary:
	//		Dialog class for the configuration wizard

	// use i18n information from umc.modules.udm
	i18nClass: 'umc.modules.adconnector',

	'class' : 'umcPopup',

	_wizard: null,

	buildRendering: function() {
		this.inherited(arguments);

		umc.tools.umcpCommand( 'adconnector/load' ).then( dojo.hitch( this, function( response ) {
			this._wizard = new umc.modules._adconnector.Wizard( {
				style: 'width: 500px; height: 400px;',
				variables: response.result
			} );
			this.set( 'content', this._wizard );
			this.connect( this._wizard, 'onFinished', function() {
				this.onSaved();
			} );
			this.connect( this._wizard, 'onCancel', function() {
				this.hide();
				this.destroyRecursive();
			} );
			this._wizard.startup();
		} ) );
	},

	onSaved: function() {
	}
});
