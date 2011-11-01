/*global dojo dijit dojox umc console window */

dojo.provide("umc.license");

dojo.require("dojo.cookie");
dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("dojo.cache");

dojo.mixin(umc.license, new umc.i18n.Mixin({
	// use the framework wide translation file
	i18nClass: 'umc.app'
} ), {

	show: function( info ) {
		if ( info.oemProductTypes.length === 0 ) {
			product = info.licenseTypes.join( ', ' );
		} else {
			product = info.oemProductTypes.join( ', ' );
		}
		var keys = {
			title : this._( 'License' ),
			labelBase : this._( 'LDAP base' ),
			base: info.baseDN,
			labelUser : this._( 'User accounts' ),
			user: this._( '%s (used: %s)', info.licenses.account === null ? this._( 'unlimited' ) : info.licenses.account, info.real.account ),
			labelClients : this._( 'Clients' ),
			clients: this._( '%s (used: %s)', info.licenses.client === null ? this._( 'unlimited' ) : info.licenses.client, info.real.client ),
			labelDesktops : this._( 'Desktops' ),
			desktops: this._( '%s (used: %s)', info.licenses.desktop === null ? this._( 'unlimited' ) : info.licenses.desktop, info.real.desktop ),
			labelEndDate : this._( 'Expiry date' ),
			endDate: this._( info.endDate ),
			labelProduct : this._( 'Valid product types' ),
			product: product,
			freeLicenseInfo: info.baseDN == 'Free for personal use edition' ? this._( 'FREE LICENSE INFO' ) : ''
		};
		umc.dialog.templateDialog( "umc", "license.html", keys, this._( 'About UMC' ), this._( 'Close' ) );
	}
} );
