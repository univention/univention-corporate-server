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
		var free_license_info = this._( '<p>The "free for personal use" edition of Univention Corporate Server is a special software license which allows users free use of the Univention Corporate Server and software products based on it for private purposes acc. to § 13 BGB (German Civil Code).</p><p>In the scope of this license, UCS can be downloaded, installed and used from our servers. It is, however, not permitted to make the software available to third parties to download or use it in the scope of a predominantly professional or commercial usage.</p><p>The license of the "free for personal use" edition of UCS occurs in the scope of a gift contract. We thus exclude all warranty and liability claims, except in the case of deliberate intention or gross negligence. We emphasise that the liability, warranty, support and maintance claims arising from our commercial software contracts do not apply to the "free for personal use" edition.</p><p>We wish you a lot of happiness using the "free for personal use" edition of Univention Corporate Server and look forward to receiving your feedback. If you have any questions, please consult our forum, which can be found on the Internet at http://forum.univention.de/.</p>' );
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
			freeLicenseInfo: info.baseDN == 'Free for personal use edition' ? free_license_info : ''
		};
		umc.dialog.templateDialog( "umc", "license.html", keys, this._( 'About UMC' ), this._( 'Close' ) );
	}
} );
