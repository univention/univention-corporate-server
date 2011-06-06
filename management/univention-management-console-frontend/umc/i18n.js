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

	// i18nClass: String
	//		If given, the locale information for the specified class is loaded instead
	//		of the default class. The default class is the class as specified by 
	//		declaredClass, i.e., the class name as specified for dojo.declare().
	//		Using this property, multiple classes can share one i18n translation file.
	i18nClass: '',

	// _i18nTranslations: Object
	//		Internal dictionary of translation from English -> current language
	_i18nTranslations: { },

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

		// get module path and module name
		// case1: no '.' is in the path: m[2] == undefined && m[3] == undefined
		// case2: there is a '.' in the path: m[1] == undefined
		this.i18nClass = this.i18nClass || this.declaredClass;
		var m = this._i18nModNameRegExp.exec(this.i18nClass);
		var modPath = m[2] || '';
		var modName = m[3] || m[1];

		// detect the locale language (ignore territory)
		m = this._i18nLocalRegExp.exec(dojo.locale);
		var lang = m[1] || 'en'; // default is English
		lang = lang.toLowerCase();
		
		// try to load the JSON translation file for the current language
		try {
			var json = dojo.cache(modPath, dojo.replace('i18n/{0}/{1}.json', [ lang, modName ]));
			this._i18nTranslations = dojo.fromJson(json);
		}
		catch (error) {
			console.log('INFO: Localization files for module ' + this.declaredClass + ' in language "' + lang + '" not available!');
		}

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
		var msg = this._i18nTranslations[_msg] || _msg;

		// get arguments for sprintf
		var args = [msg];
		for (var i = 1; i < arguments.length; ++i) {
			args.push(arguments[i]);
		}

		// call sprintf
		return dojox.string.sprintf.apply(this, args);
	}
});


