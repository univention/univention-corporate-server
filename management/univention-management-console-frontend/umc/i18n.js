/*
 * Copyright 2011 Univention GmbH
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
/*global console dojo dojox dijit umc */

dojo.provide("umc.i18n");

dojo.require("dojo.cache");
dojo.require("dojox.string.sprintf");

dojo.declare("umc.i18n.Mixin", null, {
	// summary:
	//		Mixin class for translation support.
	// description:
	//		This mixin tries to load the json translation file given the current 
	//		language settings. Its URI is deducted as follows. Given the module name
	//		"domain.mymodule", the mixin will try to load the JSON i18n file from
	//		"domain/i18n/<language>/mymodule.json". The mixin provides a 
	//		gettext-like conversion method _().

	// i18nClass: String | String[]
	//		If given, the locale information for the specified class is loaded instead
	//		of the default class. The default class is the class as specified by 
	//		declaredClass, i.e., the class name as specified for dojo.declare().
	//		Using this property, multiple classes can share one i18n translation file.
	//		It is also possible to specify a list of translation domains.
	i18nClass: '',

	// _i18nTranslations: Object
	//		Internal dictionary of translation from English -> current language
	_i18nTranslations: null,

	// _i18nModNameRegExp: RegExp
	//		Internal regular expression to split the module name into the module
	//		path and name.
	_i18nModNameRegExp: /^([^\.]*)$|^(.*)\.([^\.]*)$/,

	// _i18nLocalRegExp: RegExp
	//		Internal regular expression to split locales in to the language and
	//		the territory (which is ignored at the moment).
	_i18nLocalRegExp: /^([a-z]{2,3})(_([a-z]{2,3}))?/i,

	// _i18nInitialized: Boolean
	//		Internal flag that indicates whether or not the locale information has
	//		already been loaded for the module.
	_i18nInitialized: false,

	constructor: function(params) {
		dojo.mixin(this, params);
	},

	_i18nInit: function() {
		// summary:
		//		Internal method to initialize the the locale information for the
		//		module.
		// returns:
		//		Translated message, defaults to the original message.
		// tags:
		//		protected

		// initiate the translation classes as array
		this._i18nTranslations = [];
		this.i18nClass = this.i18nClass || this.declaredClass;
		if (!dojo.isArray(this.i18nClass)) {
			// convert strings to array of strings
			this.i18nClass = [ this.i18nClass ];
		}

		// use the classname and 'umc.app' as backup path to allow other class to
		// override a UMC base class without loosing its translations (see Bug #24864)
		this.i18nClass.push('umc.app');
		dojo.forEach(this.i18nClass, function(iclass) {
			// get module path and module name
			// case1: no '.' is in the path: m[2] == undefined && m[3] == undefined
			// case2: there is a '.' in the path: m[1] == undefined
			var m = this._i18nModNameRegExp.exec(iclass);
			var modPath = m[2] || '';
			var modName = m[3] || m[1];

			// detect the locale language (ignore territory)
			m = this._i18nLocalRegExp.exec(dojo.locale);
			var lang = m[1] || 'en'; // default is English
			lang = lang.toLowerCase();
			
			// try to load the JSON translation file for the current language
			try {
				var json = dojo.cache(modPath, dojo.replace('i18n/{0}/{1}.json', [ lang, modName ]));
				this._i18nTranslations.push(dojo.fromJson(json));
			}
			catch (error) {
				console.log('INFO: Localization files for module ' + this.declaredClass + ' in language "' + lang + '" not available!');
			}
		}, this);

		this._i18nInitialized = true;
	},
	
	_: function(/*String*/ _msg, /*mixed...*/ filler) {
		// summary:
		//		A gettext-like translation method.
		// description:
		//		A gettext-like method that will translate the given message string
		//		A printf-like syntax for the string is possible, simply provide the
		//		function with a dict or more arguments containing referenced variables.
		// example:
		//		Some examples of how the method can be used:
		// |	var msg = this._('Translate me!');
		// |	var msg = this._('The total cost was %.2f EUR!', 10.2353);
		// |	var msg = this._('Hello %s %s!', 'John', 'Miller');
		// |	var msg = this._('Hello %(last)s, %(first)s!', { first: 'John', last: 'Miller' });

		// initialization
		if (!this._i18nInitialized) {
			this._i18nInit();
		}
		
		// get message to display (defaults to original message)
		var msg = _msg;
		var i = 0;
		for (i = 0; i < this._i18nTranslations.length; ++i) {
			if (this._i18nTranslations[i][_msg]) {
				// we found a translation... take it and break the loop
				msg = this._i18nTranslations[i][_msg];
				break;
			}
		}
		 
		// get arguments for sprintf
		var args = [msg];
		for (i = 1; i < arguments.length; ++i) {
			args.push(arguments[i]);
		}

		// call sprintf
		return dojox.string.sprintf.apply(this, args);
	}
});


