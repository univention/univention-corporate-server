/*global dojo dijit dojox umc console window */

dojo.provide("umc.help");

dojo.require("dojo.cookie");
dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("dojo.cache");

dojo.mixin(umc.help, new umc.i18n.Mixin({
	// use the framework wide translation file
	i18nClass: 'umc.app'
} ), {

	show: function() {
		var introduction = this._( 'Univention Management Console (UMC) is a modularly designed, web-based application to administrate local computers. The application allows the user to control services, check system utilisation, and check or adjust system parameters.  The web-based interface of UMC is described in detail the in current manual of Univention Corporate Server (UCS). Besides the manual, the homepage of Univention provides additional documentation for Univention Corporate Server. These documents assist in different topics like installation or administration.' );

		var lang = dojo.locale.slice( 0, 2 ).toLowerCase();
		var keys = {
			introduction : introduction,
			manual : this._( 'Current manual (PDF)' ),
			add_doc : this._( 'Additional documentation for UCS' ),
			sdb : this._( 'Univention support data base (SDB)' ),
			wiki : this._( 'Univention wiki site' ),
			forum : this._( 'Univention forum' ),
			support : this._( 'Univention support' ),
			supportURL : lang == 'de' ? 'http://www.univention.de/univention/kontakt/kontaktformular/' : 'http://www.univention.de/en/about-univention/contact/',
			titleDoc : this._( 'Manual and documentation' ),
			titleSup : this._( 'Supplementary information' ),
			titleAss : this._( 'Support and assistance' )
		};
		umc.dialog.templateDialog( "umc", "help.html", keys, this._( 'Help' ), this._( 'Close' ) );
	}
} );
