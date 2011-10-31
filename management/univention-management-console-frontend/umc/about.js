/*global dojo dijit dojox umc console window */

dojo.provide("umc.about");

dojo.require("dojo.cookie");
dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("dojo.cache");

dojo.mixin(umc.about, new umc.i18n.Mixin({
	// use the framework wide translation file
	i18nClass: 'umc.app'
} ), {

	show: function( info ) {
		var message = dojo.cache("umc", "about.html");
		message = dojo.replace( message, {
			labelServer : this._( 'Server' ),
			server : info.server,
			labelUCS_Version : this._( 'UCS version' ),
			UCS_Version : info.ucs_version,
			labelUMC_Version : this._( 'UMC version' ),
			UMC_Version : info.umc_version,
			labelSSL_ValidityDate : this._( 'Validity date of the SSL certificate' ),
			SSL_ValidityDate : info.ssl_validity_date
		} );
		umc.dialog.alert( message, this._( 'About UMC' ), this._( 'Close' ) );
	}
} );
