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
	"dojo/_base/array",
	"dijit/Dialog",
	"umc/dialog",
	"umc/tools",
	"umc/render",
	"umc/widgets/Module",
	"umc/widgets/Page",
	"umc/widgets/Wizard",
	"umc/widgets/StandbyMixin",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/widgets/CheckBox",
	"umc/widgets/ComboBox",
	"umc/widgets/PasswordBox",
	"umc/widgets/InfoUploader",
	"umc/i18n!umc/modules/adconnector"
], function(declare, lang, array, DijitDialog, dialog, tools, render, Module, Page, Wizard, StandbyMixin, Text, TextBox, CheckBox, ComboBox, PasswordBox, InfoUploader, _) {

	var ADConnectorWizard = declare("umc.modules._adconnector.Wizard", [ Wizard ], {
		pages: null,

		variables: null,

		constructor: function() {
			this.pages = [ {
				name: 'fqdn',
				helpText: _( 'The full qualified hostname of the Active Directory server is required' ),
				headerText: _( 'UCS Active Directory Connector configuration' ),
				widgets: [{
					name: 'LDAP_Host',
					type: TextBox,
					required: true,
					regExp: '.+',
					invalidMessage: _( 'The hostname of the Active Directory server is required' ),
					label: _( 'Active Directory Server' )
				}, {
					name: 'guess',
					type: CheckBox,
					label: _( 'Automatic determination of the LDAP configuration' )
				}],
				layout: [ 'LDAP_Host', 'guess' ]
			}, {
				name: 'ldap',
				helpText: _( 'LDAP und kerberos configuration of the Active Directory server needs to be specified for the synchronisation' ),
				headerText: _( 'LDAP and Kerberos' ),
				widgets: [{
					name: 'LDAP_Base',
					type: TextBox,
					required: true,
					sizeClass: 'OneAndAHalf',
					label: _( 'LDAP base' )
				}, {
					name: 'LDAP_BindDN',
					required: true,
					type: TextBox,
					sizeClass: 'OneAndAHalf',
					label: _( 'LDAP DN of the synchronisation user' )
				}, {
					name: 'LDAP_Password',
					type: PasswordBox,
					label: _( 'Password of the synchronisation user' )
				}, {
					name: 'KerberosDomain',
					type: TextBox,
					label: _( 'Kerberos domain' )
				}],
				layout: [ 'LDAP_Base', 'LDAP_BindDN', 'LDAP_Password', 'KerberosDomain' ]
			}, {
				name: 'sync',
				helpText: _( 'UCS Active Directory Connector supports three types of synchronisation.' ),
				headerText: _( 'Synchronisation mode' ),
				widgets: [ {
					name: 'MappingSyncMode',
					type: ComboBox,
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
					label: _( 'Synchronisation mode' )
				}, {
					name: 'MappingGroupLanguage',
					label: _( 'System language of Active Directory server' ),
					type: ComboBox,
					staticValues: [
						{
							id: 'de',
							label: _( 'German' )
						}, {
							id: 'en',
							label: _( 'English' )
						} ]
				} ],
				layout: [ 'MappingSyncMode', 'MappingGroupLanguage' ]
			}, {
				name: 'extended',
				helpText: _( 'The following settings control the internal behaviour of the UCS Active Directory connector. For all attributes reasonable default values are provided.' ),
				headerText: _( 'Extended settings' ),
				widgets: [ {
					name: 'PollSleep',
					type: TextBox,
					sizeClass: 'OneThird',
					label: _( 'Poll Interval (seconds)' )
				}, {
					name: 'RetryRejected',
					label: _( 'Retry interval for rejected objects' ),
					type: TextBox,
					sizeClass: 'OneThird'
				}, {
					name: 'DebugLevel',
					label: _( 'Debug level of Active Directory Connector' ),
					type: TextBox,
					sizeClass: 'OneThird'
				}, {
					name: 'DebugFunction',
					label: _( 'Add debug output for functions' ),
					type: CheckBox,
					sizeClass: 'OneThird'
				} ],
				layout: [ 'PollSleep', 'RetryRejected', 'DebugLevel', 'DebugFunction' ]
			} ];
		},

		next: function(/*String*/ currentID) {
			if ( !currentID ) {
				tools.forIn( this.variables, lang.hitch( this, function( option, value ) {
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
					tools.umcpCommand( 'adconnector/guess', { 'LDAP_Host' : server.get( 'value' ) } ).then( lang.hitch( this, function( response ) {
						if ( response.result.LDAP_Base ) {
							this.getWidget( 'ldap', 'LDAP_Base' ).set( 'value', response.result.LDAP_Base );
							this.getWidget( 'ldap', 'LDAP_BindDN' ).set( 'value', 'cn=Administrator,cn=users,' + response.result.LDAP_Base );
							this.getWidget( 'ldap', 'KerberosDomain' ).set( 'value', tools.explodeDn( response.result.LDAP_Base, true ).join( '.' ) );
						} else {
							dialog.notify( response.result.message );
						}
						this.standby( false );
					} ) );
				}
			} else if ( currentID == 'ldap' ) {
				var valid = true;
				array.forEach( [ 'LDAP_Base', 'LDAP_BindDN', 'LDAP_Password' ], lang.hitch( this, function( widgetName ) {
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
					dialog.alert( _( 'The password for the synchronisation account is required!' ) );
					return currentID;
				}
			}

			return this.inherited( arguments );
		},

		onFinished: function( values ) {
			this.standby( true );
			tools.umcpCommand( 'adconnector/save', values ).then( lang.hitch( this, function( response ) {
				if ( !response.result.success ) {
					dialog.alert( response.result.message );
				} else {
					dialog.notify( response.result.message );
				}
				this.standby( false );
			} ) );
		}
	});

	var ADConnectorWizardDialog = declare("umc.modules._adconnector.WizardDialog", [ DijitDialog, StandbyMixin ], {
		// summary:
		//		Dialog class for the configuration wizard

		'class' : 'umcPopup',

		_wizard: null,

		buildRendering: function() {
			this.inherited(arguments);

			tools.umcpCommand( 'adconnector/load' ).then( lang.hitch( this, function( response ) {
				this._wizard = new ADConnectorWizard( {
					style: 'width: 500px; height: 400px;',
					variables: response.result
				} );
				this.set( 'content', this._wizard );
				this._wizard.on('Finished', lang.hitch(this, function() {
					this.onSaved();
				} ));
				this._wizard.on('Cancel', lang.hitch(this, function() {
					this.hide();
					this.destroyRecursive();
				} ));
				this._wizard.startup();
			} ) );
		},

		onSaved: function() {
		}
	});

	return declare("umc.modules.adconnector", [ Module ], {

		standbyOpacity: 1.00,

		_widgets: null,

		_buttons: null,

		_page: null,

		buildRendering: function() {
			this.inherited(arguments);
			this.standby(true);

        	this._page = new Page({
            	helpText: _( "This module provides a configuration wizard for the UCS Active Directory Connector to simplify the setup." ),
            	headerText: _( "Configuration of the UCS Active Directory Connector" )
        	});
        	this.addChild(this._page);

			var widgets = [
				{
					name: 'configured',
					type: Text
				}, {
					name: 'running',
					type: Text
				}, {
					name: 'certificateUpload',
					type: InfoUploader,
					showClearButton: false,
					command: 'adconnector/upload/certificate',
					onUploaded: lang.hitch( this, function( result ) {
						if ( typeof  result  == "string" ) {
							return;
						}
						if ( result.success ) {
							dialog.notify( _( 'The certificate was imported successfully' ) );
							this.showHideElements();
						} else {
							dialog.alert( _( 'Failed to import the certificate' ) + ': ' + result.message );
						}
					} )
				}, {
					name: 'download',
					type: Text,
					content: lang.replace( '<a href="/univention-ad-connector/" target="_blank">{0}</a>', [ _( 'Download the password service for Windows and the UCS certificate' ) ] )
				}
			];
			var buttons = [
				{
					name: 'start',
					label: _( 'Start UCS Active Directory Connector' ),
					callback: lang.hitch( this, function() {
						tools.umcpCommand( 'adconnector/service', { action : 'start' } ).then( lang.hitch( this, function( response ) {
							this.showHideElements();
						} ) );
					} )
				}, {
					name: 'stop',
					label: _( 'Stop UCS Active Directory Connector' ),
					callback: lang.hitch( this, function() {
						tools.umcpCommand( 'adconnector/service', { action : 'stop' } ).then( lang.hitch( this, function( response ) {
							this.showHideElements();
						} ) );
					} )
				}, {
					name: 'configure',
					label: _( 'Configure UCS Active Directory Connector' ),
					callback: lang.hitch( this, function() {
						var dlg = new ADConnectorWizardDialog( {
							title: _( 'UCS Active Directory Connector Wizard' )
						} );
						dlg.show();
						dlg.on('saved', lang.hitch( this, function() {
							dlg.destroyRecursive();
							this.showHideElements();
						} ) );
					} )
				}
			];

			this._widgets = render.widgets( widgets );
			this._buttons = render.buttons( buttons );

			var _container = render.layout( [ {
				label: _( 'Configuration' ),
				layout: [ 'configured',  'configure' ]
			}, {
				label: _( 'UCS Active Directory Connector service' ),
				layout: [ 'running', 'start', 'stop' ]
			}, {
				label: _( 'Active Directory Server configuration' ),
				layout: [ 'certificateUpload', 'download' ]
			}  ], this._widgets, this._buttons );

			_container.set( 'style', 'overflow: auto' );
			this._page.addChild( _container );

			this.showHideElements();
			this.standby( false );
    	},

		showHideElements: function() {
			tools.umcpCommand( 'adconnector/state' ).then( lang.hitch( this, function( response ) {
				if ( response.result.configured ) {
					this._widgets.configured.set( 'content', _( 'The configuration process has been finished and all required settings for UCS Active Directory Connector are set.' ) );
				} else {
					this._widgets.configured.set( 'content', _( 'The configuration process has not been started yet or is incomplete.' ) );
				}
				if ( ! response.result.certificate ) {
					this._widgets.certificateUpload.set( 'value', _( 'The Active Directory certificate has not been installed yet.' ) );
				} else {
					this._widgets.certificateUpload.set( 'value', _( 'The Active Directory certificate has been successfully installed.' ) );
				}
				if ( response.result.running ) {
					this._widgets.running.set( 'content', _( 'UCS Active Directory Connector is currently running.' ) );
					this._buttons.start.set( 'visible', false );
					this._buttons.stop.set( 'visible', true );
				} else {
					var message = _( 'UCS Active Directory Connector is not running.' );
					if ( ! response.result.configured ) {
						message += _( ' The Configuation of UCS Active Directory Connector must be completed before the server can be started.' );
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

});
