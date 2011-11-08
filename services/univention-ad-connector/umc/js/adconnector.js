/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.adconnector");

dojo.require( "umc.i18n" );
dojo.require( "umc.render" );
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
				name: 'certificate',
				type: 'Text'
			}, {
				name: 'running',
				type: 'Text'
			}, {
				name: 'certificateUpload',
				type: 'Upload'
			}, {
				name: 'download',
				type: 'Text',
				content: dojo.replace( '<a href="/univention-ad-connector/" target="_blank">{0}</a>', [ this._( 'Download the password serivce for Windows and the UCS certificate' ) ] )
			}
		];
		var buttons = [
			{
				name: 'start',
				label: this._( 'Start UCS Active Directory Connector' ),
				callback: dojo.hitch( this, function() {
					umc.tools.umcpCommand( 'adconnector/service', { action : 'start' } ).then( dojo.hitch( this, function( response ) {
						this.hideShowElements();
					} ) );
				} )
			}, {
				name: 'stop',
				label: this._( 'Stop UCS Active Directory Connector' ),
				callback: dojo.hitch( this, function() {
					umc.tools.umcpCommand( 'adconnector/service', { action : 'stop' } ).then( dojo.hitch( this, function( response ) {
						this.hideShowElements();
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
			layout: [ 'certificate', 'download' ]
		}  ], this._widgets, this._buttons );

		// var container = new umc.widgets.ContainerWidget( {
		// 	scrollable: true
		// } );
		this._page.addChild( _container );

		// var titlePane = new dijit.TitlePane({
		// 	title: this._( 'Status' ),
		// 	content: _container
		// });
		// container.addChild( titlePane );
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
				this._widgets.certificate.set( 'content', this._( 'The Active Directory certificate has not been installed yet.' ) );
			} else {
				this._widgets.certificate.set( 'content', this._( 'The Active Directory certificate has been sucessfully installed.' ) );
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

	style: 'width: 400px; height: 80%',

	constructor: function() {
		this.pages = [ {
			name: 'fqdn',
			helpText: this._( 'The full qualified hostname of the Active Directory server is required' ),
			headerText: this._( 'UCS Active Directory Connector configuration' ),
			widgets: [{
				name: 'fqdnAD',
				type: 'TextBox',
				label: this._( 'Active Directory Server' )
			}, {
				name: 'guess',
				type: 'CheckBox',
				label: this._( 'Determine LDAP configuration' )
			}],
			layout: [ 'fqdnAD', 'guess' ]
		}, {
			name: 'ldap',
			helpText: this._( 'For the synchronisation a user account of the Active Directory server is required.' ),
			headerText: this._( 'Synchronisation account' ),
			widgets: [{
				name: 'baseLDAP',
				type: 'TextBox',
				label: this._( 'LDAP base' )
			}, {
				name: 'userLDAP',
				type: 'TextBox',
				label: this._( 'LDAP DN of the synchronisation user' )
			}, {
				name: 'passwordLDAP',
				type: 'PasswordBox',
				label: this._( 'Password of the synchronisation user' )
			}],
			layout: [ 'baseLDAP', 'userLDAP', 'passwordLDAP' ]
		}, {
			name: 'sync',
			helpText: this._( 'UCS Active Directory Connector supports three types of synchronisation.' ),
			headerText: this._( 'Synchronisation mode' ),
			widgets: [{
				name: 'syncMode',
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
			} ],
			layout: [ 'sync' ]
		} ];
	},

	next: function(/*String*/ currentID) {
		// if (!currentID) {
		// 	return 'fqdn';
		// }
		if (currentID == 'fqdn') {
			var guess = this.getWidget( 'fqdn', 'guess' );
			if ( guess.get( 'value' ) ) {
				console.log( 'Guess LDAP Base' );
			}
		}
		// if (currentID == 'second') {
		// 	this.getWidget('last', 'name').set('value', this.getWidget('first', 'name').get('value'));
		// 	return 'last';
		// }
		// return null;
		return this.inherited( arguments );
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

		this._wizard = new umc.modules._adconnector.Wizard({
			style: 'width: 400px; height: 400px;'
		} );
		this.set( 'content', this._wizard );
		this.connect( this._wizard, 'onFinished', function() {
			this.hide();
			this.destroyRecursive();
		} );
		this.connect( this._wizard, 'onCancel', function() {
			this.hide();
			this.destroyRecursive();
		} );
		this._wizard.startup();
	}
});
