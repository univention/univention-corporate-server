/*global dojo dijit dojox umc console window */

dojo.provide("umc.modules._udm.LicenseDialog");

dojo.require("dojo.cache");
dojo.require("dijit.Dialog");
dojo.require("dijit.layout.ContentPane");
dojo.require("dojox.widget.Dialog");
dojo.require("umc.dialog");
dojo.require("umc.i18n");
dojo.require("umc.render");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.StandbyMixin");

dojo.declare('umc.modules._udm.LicenseDialog', [ dijit.Dialog, umc.widgets.StandbyMixin, umc.i18n.Mixin ], {
	// summary:
	//		Class that provides the license Dialog for UCS. It shows details about the current license and support importing a new one.

	// translation
	i18nClass: 'umc.modules.udm',

	// the widget's class name as CSS class
	'class': 'umcPopup',

	style: 'width: 600px;',

	_widgets: null,

	_container: null,

	licenseInfo: null,

	_limitInfo: function( limit ) {
		return this._( '%s (used: %s)', this.licenseInfo.licenses[ limit ] === null ? this._( 'unlimited' ) : this.licenseInfo.licenses[ limit ], this.licenseInfo.real[ limit] );
	},

	buildRendering: function() {
		this.inherited(arguments);

		// put buttons into separate container
		var _buttonContainer = new umc.widgets.ContainerWidget({
			style: 'text-align: center;',
			'class': 'umcButtonRow'
		});
		_buttonContainer.addChild( new umc.widgets.Button( {
			label: this._( 'Close' ),
			defaultButton: true,
			onClick: dojo.hitch( this, function() {
				this.close();
			} )
			} ) );

		// content: license info and upload widgets
		var product = '';
		if ( this.licenseInfo.oemProductTypes.length === 0 ) {
			product = this.licenseInfo.licenseTypes.join( ', ' );
		} else {
			product = this.licenseInfo.oemProductTypes.join( ', ' );
		}
		var free_license_info = '';
		if ( this.licenseInfo.baseDN == 'Free for personal use edition' ) {
			free_license_info = this._( '<p>The "free for personal use" edition of Univention Corporate Server is a special software license which allows users free use of the Univention Corporate Server and software products based on it for private purposes acc. to § 13 BGB (German Civil Code).</p><p>In the scope of this license, UCS can be downloaded, installed and used from our servers. It is, however, not permitted to make the software available to third parties to download or use it in the scope of a predominantly professional or commercial usage.</p><p>The license of the "free for personal use" edition of UCS occurs in the scope of a gift contract. We thus exclude all warranty and liability claims, except in the case of deliberate intention or gross negligence. We emphasise that the liability, warranty, support and maintance claims arising from our commercial software contracts do not apply to the "free for personal use" edition.</p><p>We wish you a lot of happiness using the "free for personal use" edition of Univention Corporate Server and look forward to receiving your feedback. If you have any questions, please consult our forum, which can be found on the Internet at http://forum.univention.de/.</p>' );
		}

		// substract system accounts
		this.licenseInfo.real.account -= this.licenseInfo.sysAccountsFound;
		var keys = {
			title : this._( 'Current license' ),
			labelBase : this._( 'LDAP base' ),
			base: this.licenseInfo.baseDN,
			labelUser : this._( 'User accounts' ),
			user: this._limitInfo( 'account' ),
			labelClients : this._( 'Clients' ),
			clients: this._limitInfo( 'client' ),
			labelDesktops : this._( 'Desktops' ),
			desktops: this._limitInfo( 'desktop' ),
			labelEndDate : this._( 'Expiry date' ),
			endDate: this._( this.licenseInfo.endDate ),
			labelProduct : this._( 'Valid product types' ),
			product: product
		};

		var message = dojo.cache( "umc.modules._udm", "license.html" );
		var widgets = [
			{
				type : 'Text',
				name : 'message',
				style : 'width: 100%',
				content : dojo.replace( message, keys )
			}, {
				type : 'TextArea',
				name : 'licenseText',
				label : this._( 'License text' )
			}, {
				type : 'Text',
				name : 'ffpu',
				content : this.licenseInfo.baseDN == 'Free for personal use edition' ? free_license_info : ''
			}, {
				type : 'Text',
				name : 'titleImport',
				style : 'width: 100%',
				content : dojo.replace( '<h1>{title}</h1>', { title: this._( 'License import' ) } )
			} ];
		var buttons = [  {
			type : 'Button',
			name : 'btnLicenseText',
			label : this._( 'Upload' ),
			callback: dojo.hitch( this, function() {
				this.standby( true );
				var defered = umc.tools.umcpCommand( 'udm/license/import', { 'license' : this._widgets.licenseText.get( 'value' ) } );
				defered.then( dojo.hitch( this, function( response ) {
					this.standby( false );
					if ( false === response.result.success ) {
						umc.dialog.alert( this._( 'The import of the license has failed: ' ) + response.result.message );
					} else {
						umc.dialog.alert( this._( 'The license has been imported succussfully' ) );
					}
				} ) );
			} )
		} ];

		this._widgets = umc.render.widgets( widgets );
		var _buttons = umc.render.buttons( buttons );
		var _container = umc.render.layout( [ 'message', 'titleImport', [ 'licenseText', 'btnLicenseText' ], 'ffpu' ], this._widgets, _buttons );

		var _content = new umc.widgets.ContainerWidget( {
			scrollable: true,
			style: 'max-height: 500px'
		} );
		_content.addChild( _container );
		// put the layout together
		this._container = new umc.widgets.ContainerWidget();
		this._container.addChild( _content );
		this._container.addChild( _buttonContainer );
		this._container.startup();

		// attach layout to dialog
		this.set( 'content', this._container );
		this.set( 'title', this._( 'UCS license' ) );
	},

	close: function() {
		// summary:
		//		Hides the dialog and destroys it after the fade-out animation.
		this.hide().then(dojo.hitch(this, function() {
			this.destroyRecursive();
		}));
	},

	destroy: function() {
		this.inherited(arguments);
		this._container.destroyRecursive();
	}
});
