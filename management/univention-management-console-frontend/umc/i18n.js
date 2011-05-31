/*global console dojo dojox dijit umc */

dojo.provide("umc.i18n");

dojo.require("dojo.cache");
dojo.require("dojox.string.sprintf");

dojo.declare("umc.i18n.Mixin", null, {
	// summary:
	//		Mixin class for translation support.
	//		It tries to load the json translation file given the current language
	//		settings. Its URI is deducted as follows. Given the module name
	//		"domain.mymodule", the mixin will try to load the JSON i18n file from
	//		"domain/i18n/<language>/mymodule.json". The mixin provides a 
	//		gettext-like conversion method _().

	// _i18Translations: Object
	//		Internal dictionary of translation from English -> current language
	_i18Translations: { },

	// _modNameRegExp: RegExp
	//		Internal regular expression to split the module name into the module
	//		path and name.
	_modNameRegExp: /^([^\.]*)$|^(.*)\.([^\.]*)$/,

	// _localRegExp: RegExp
	//		Internal regular expression to split locales in to the language and
	//		the territory (which is ignored at the moment).
	_localRegExp: /^([a-z]{2,3})(_([a-z]{2,3}))?/i,

	_localeInitialized: false,

	_initLocale: function() {
		// get module path and module name
		// case1: no '.' is in the path: m[2] == undefined && m[3] == undefined
		// case2: there is a '.' in the path: m[1] == undefined
		var m = this._modNameRegExp.exec(this.declaredClass);
		var modPath = m[2] || '';
		var modName = m[3] || m[1];

		// detect the locale language (ignore territory)
		m = this._localRegExp.exec(dojo.locale);
		var lang = m[1] || 'en'; // default is English
		lang = lang.toLowerCase();
		
		// try to load the JSON translation file for the current language
		try {
			var json = dojo.cache(modPath, dojo.replace('i18n/{0}/{1}.json', [ lang, modName ]));
			this._i18Translations = dojo.fromJson(json);
		}
		catch (error) {
			console.log('INFO: Localization files for module ' + this.declaredClass + ' in language "' + lang + '" not available!');
		}

		this._localeInitialized = true;
	},
	
	_: function(/*String*/ _msg, /*Object*/ values) {
		// summary:
		//		A gettext-like method _() is provided that will return an Object which
		//		is convertible to String for printf-like variables ("%(var)s", "%d", 
		//		etc.) specified in the string. Simply call the object's method "sub()"
		//		provided with a dict or an array containing the variable values.

		// initialization
		if (!this._localeInitialized) {
			this._initLocale();
		}
		
		// get message to display (defaults to original message)
		var msg = this._i18Translations[_msg] || _msg;

		// get arguments for sprintf
		var args = [msg];
		for (var i = 1; i < arguments.length; ++i) {
			args.push(arguments[i]);
		}

		// call sprintf
		return dojox.string.sprintf.apply(this, args);
	}
});


