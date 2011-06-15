/*global dojo dijit dojox umc console window */

dojo.provide('umc.app');

dojo.require("dijit.Dialog");
dojo.require("dijit.layout.BorderContainer");
dojo.require("dijit.layout.ContentPane");
dojo.require("dijit.layout.TabContainer");
dojo.require("dijit.form.DropDownButton");
dojo.require("dijit.form.Button");
dojo.require("dijit.Menu");
dojo.require("dojo.cookie");
dojo.require("dojox.html.styles");
dojo.require("umc.widgets.Toaster");
dojo.require("umc.widgets.ConfirmDialog");
dojo.require("umc.widgets.LoginDialog");
dojo.require("umc.widgets.ContainerPane");
dojo.require("umc.widgets.CategoryPane");
dojo.require("umc.i18n");

// start the application when everything has been loaded
dojo.addOnLoad(function() {
	umc.app.start();

	// register application-wide error handler
	/*window.onerror = function (msg, url, num) {
		console.log(msg + ';' + url + ';' + num);
		umc.app.alert('An error occurred:\n' + msg);
		return true;
	};*/
});

dojo.mixin(umc.app, new umc.i18n.Mixin({
	// use the framework wide translation file
	i18nClass: 'umc.app'
}), {
	// loggingIn: Boolean
	//		True if the user is in the process of loggin in.
	loggingIn: false,

	_loginDialog: null,
	_alertDialog: null,
	_toaster: null,
	_userPreferences: null,

	defaultPreferences: {
		tooltips: true,
		moduleDescription: true,
		confirm: true
	},

	notify: function(/*String*/ message) {
		// summary:
		//		Show a toaster notification with the given message string.

		// show the toaster
		this._toaster.setContent(message, 'message');
	},

	alert: function(/*String*/ message) {
		// summary:
		//		Popup an alert dialog with the given message string. The users needs to
		//		confirm the dialog by clicking on the 'OK' button.

		// show the confirmation dialog
		this._alertDialog.set('message', message);
		this._alertDialog.show();
	},

	confirm: function(/*String*/ message, /*Object*/ options) {
		// summary:
		//		Popup an confirmation dialog with the given message string. The user needs
		//		to confirm by clicking on one of multiple defined buttons.
		// message:
		//		The message that is displayed in the dialog.
		// options:
		//		Array of all possible choices that is passed to umc.widgets.ConfirmDialog
		//		as 'options' parameter. The following properties need to be specified:
		//		label; the properties 'callback', 'name' are optional.
		//		If an item is specified with the option 'default: true' and confirmations
		//		are switched off in the user preferences, the dialog is not shown and the
		//		callback function for this default option is executed directly.

		// if the user has switched off confirmations, try to find a default option
		if (!this.preferences('confirm')) {
			var cb = undefined;
			var response = undefined;
			dojo.forEach(options, function(i, idx) {
				// check for default option
				if (true === i['default']) {
					cb = i.callback;
					response = i.name || idx;
					return false; // break loop
				}
			});
			if (cb && dojo.isFunction(cb)) {
				// we found a default item .. call the callback and exit
				cb(response);
				return;
			}
		}

		// create confirmation dialog
		var confirmDialog = new umc.widgets.ConfirmDialog({
			title: this._('Confirmation'),
			style: 'max-width: 400px;',
			message: message,
			options: options
		});

		// connect to 'onConfirm' event to close the dialog in any case
		dojo.connect(confirmDialog, 'onConfirm', function(response) {
			confirmDialog.close();
		});

		// show the confirmation dialog
		confirmDialog.show();
	},

//	standby: function(/*Boolean*/ enable) {
//		if (enable === true) {
//			this._standbyWidget.show();
//		}
//		else {
//			this._standbyWidget.hide();
//		}
//	},

	login: function() {
		// summary: 
		//		Show the login dialog.
		this.loggingIn = true;
		this._loginDialog.show();
	},

	start: function() {
		// create a standby widget
//		this._standbyWidget = new dojox.widget.Standby({
//			target: dojo.body(),
//			timeout: 0,
//			zIndex: 99999999,
//			color: '#FFF'
//		});
//		dojo.body().appendChild(this._standbyWidget.domNode);
//		this._standbyWidget.startup();

		// create login dialog
		this._loginDialog = umc.widgets.LoginDialog({});
		this._loginDialog.startup();
		dojo.connect(this._loginDialog, 'onLogin', this, 'onLogin');

		// create alert dialog 
		this._alertDialog = new umc.widgets.ConfirmDialog({
			title: this._('Notification'),
			style: 'max-width: 400px;',
			options: [{
				label: this._('Ok'),
				callback: dojo.hitch(this, function() {
					// hide dialog upon confirmation by click on 'OK'
					this._alertDialog.hide();
				})
			}]
		});

		// create toaster
		this._toaster = new umc.widgets.Toaster({});

		// check whether we still have a app cookie
		var sessionCookie = dojo.cookie('UMCSessionId');
		if (undefined === sessionCookie) {
			this.login();
		}
		else {
			this.onLogin(dojo.cookie('UMCUsername'));
			console.log(this._('Login is still valid (cookie: %(cookie)s, username: %(user)s).', { cookie: sessionCookie, user: this.username }));
		}
	},

	closeSession: function() {
		dojo.cookie('UMCSessionId', null, {
			expires: -1,
			path: '/'
		});
	},

	username: null,
	onLogin: function(username) {
		this.username = username;
		dojo.cookie('UMCUsername', username, { expires: 100, path: '/' });
		this.loggingIn = false;
		this._loginDialog.hide();
		umc.tools.umcpCommand('set', {
			locale: dojo.locale
		} ).then( dojo.hitch( this, function( data ) { 
			this.loadModules(); 
		} ) );
	},

	onModulesLoaded: function() {
		this.setupGui();
	},

	// _tabContainer:
	//		Internal reference to the TabContainer object
	_tabContainer: null,

	openModule: function(/*String*/ module) {
		// summary:
		//		Open a new tab for the given module.
		// module:
		//		Module ID as string

		////console.log('### openModule');
		//console.log(module);

		// get the object in case we have a string
		if (typeof(module) == 'string') {
			module = this.getModule(module);
		}
		if (undefined === module) {
			return;
		}

		// create a new tab
		var tab = new module.BaseClass({
			title: module.title,
			iconClass: 'icon16-' + module.id,
			closable: true
			//items: [ new module.BaseClass() ],
			//layout: 'fit',
			//closable: true,
			//autoScroll: true
			//autoWidth: true,
			//autoHeight: true
		});
		tab.startup();
		umc.app._tabContainer.addChild(tab);
		umc.app._tabContainer.selectChild(tab, true);
	},

	isSetupGUI: false,
	setupGui: function() {
		// make sure that we have not build the GUI before
		if (this.isSetupGUI) {
			return;
		}

		// set up fundamental layout parts
		var topContainer = new dijit.layout.BorderContainer( {
			style: "height: 100%; width: 100%; margin-left: auto; margin-right: auto;",
			//height: 100%,
			//width: 100%,
			gutters: false
		}).placeAt(dojo.body());

		// container for all modules tabs
		umc.app._tabContainer = new dijit.layout.TabContainer({
			//style: "height: 100%; width: 100%;",
			region: "center"
		});
		topContainer.addChild(umc.app._tabContainer);

		// the container for all category panes
		// NOTE: We add the icon here in the first tab, otherwise the tab heights
		//	   will not be computed correctly and future tabs will habe display
		//	   problems.
		var overviewPage = new umc.widgets.ContainerPane({ 
			//style: "overflow:visible; width: 80%"
			title: this._('Overview'),
			iconClass: 'icon16-univention' 
		});

		// add an CategoryPane for each category
		dojo.forEach(this.getCategories(), dojo.hitch(this, function(icat) {
			// ignore empty categories
			var modules = this.getModules(icat.id);
			if (0 === modules.length) {
				return;
			}

			// create a new category pane for all modules in the given category
			var categoryPane = new umc.widgets.CategoryPane({
				modules: modules,
				title: icat.title,
				open: ('favorites' == icat.id)
			});

			// register to requests for opening a module
			dojo.connect(categoryPane, 'onOpenModule', dojo.hitch(this, this.openModule));

			// add category pane to overview page
			overviewPage.addChild(categoryPane);
		}));
		umc.app._tabContainer.addChild(overviewPage);
		
		// the header
		var header = new umc.widgets.ContainerPane({
			title: '',
			'class': 'umcHeader',
			region: 'top'
		});
		topContainer.addChild( header );

		// add some buttons
		header.addChild(new dijit.form.Button({
			label: this._('Help'),
			'class': 'umcHeaderButton'
		}));
		header.addChild(new dijit.form.Button({
			label: this._('About UMC'),
			'class': 'umcHeaderButton'
		}));

		// the user context menu
		var menu = new dijit.Menu({});
		menu.addChild(new dijit.CheckedMenuItem({
			label: this._('Tooltips'),
			checked: umc.app.preferences('tooltips'),
			onClick: function() {
				umc.app.preferences('tooltips', this.checked);
			}
		}));
		menu.addChild(new dijit.CheckedMenuItem({
			label: this._('Confirmations'),
			checked: true,
			checked: umc.app.preferences('confirm'),
			onClick: function() {
				umc.app.preferences('confirm', this.checked);
			}
		}));
		menu.addChild(new dijit.CheckedMenuItem({
			label: this._('Module help description'),
			checked: true,
			checked: umc.app.preferences('moduleDescription'),
			onClick: function() {
				umc.app.preferences('moduleDescription', this.checked);
			}
		}));
		header.addChild(new dijit.form.DropDownButton({
			label: this._('User: %s', this.username),
			'class': 'umcHeaderButton',
			dropDown: menu
		}));

		// add logout button
		header.addChild(new dijit.form.Button({
			label: '<img src="images/logout.png">',
			'class': 'umcHeaderButton',
			onClick: function() {
				umc.app.closeSession();
				window.location.reload();
			}
		}));

		// put everything together
		topContainer.startup();

		// set a flag that GUI has been build up
		umc.app.isSetupGUI = true;
	},

	preferences: function(/*String|Object?*/ param1, /*AnyType?*/ value) {
		// summary:
		//		Convenience function to set/get user preferences. 
		//		All preferences will be store in a cookie (in JSON format).
		// returns:
		//		If no parameter is given, returns dictionary with all preference
		//		entries. If one parameter of type String is given, returns the
		//		preference for the specified key. If one parameter is given which
		//		is an dictionary, will set all key-value pairs as specified by
		//		the dictionary. If two parameters are given and
		//		the first is a String, the function will set preference for the
		//		key (paramater 1) to the value as specified by parameter 2.

		// make sure the user preferences are cached internally
		var cookieStr = '';
		if (!this._userPreferences) {
			// not yet cached .. get all preferences via cookies
			this._userPreferences = dojo.clone(this.defaultPreferences);
			cookieStr = dojo.cookie('UMCPreferences') || '{}';
			dojo.mixin(this._userPreferences, dojo.fromJson(cookieStr));
		}

		// no arguments, return full preference object
		if (0 === arguments.length) {
			return this._userPreferences; // Object
		}
		// only one parameter, type: String -> return specified preference
		if (1 == arguments.length && dojo.isString(param1)) {
			return this._userPreferences[param1]; // Boolean|String|Integer
		}
		
		// backup the old preferences
		var oldPrefs = dojo.clone(this._userPreferences);
		
		// only one parameter, type: Object -> set all parameters as specified in the object
		if (1 == arguments.length) {
			// only consider keys that are defined in defaultPreferences
			umc.tools.forIn(this.defaultPreferences, dojo.hitch(this, function(key, val) {
				if (key in param1) {
					this._userPreferences[key] = param1[key];
				}
			}));
		}
		// two parameters, type parameter1: String -> set specified user preference
		else if (2 == arguments.length && dojo.isString(param1)) {
			// make sure preference is in defaultPreferences
			if (param1 in this.defaultPreferences) {
				this._userPreferences[param1] = value;
			}
		}
		// otherwise throw error due to incorrect parameters
		else {
			umc.tools.assert(false, 'umc.app.preferences(): Incorrect parameters: ' + arguments);
		}

		// publish changes in user preferences
		umc.tools.forIn(this._userPreferences, function(key, val) {
			if (val != oldPrefs[key]) {
				// entry has changed
				dojo.publish('/umc/preferences/' + key, [val]);
			}
		});

		// set the cookie with all preferences
		cookieStr = dojo.toJson(this._userPreferences);
		dojo.cookie('UMCPreferences', cookieStr, { expires: 100, path: '/' } );
		return; // undefined
	},

	_modules: [],
	_categories: [],
	loadModules: function() {
		umc.tools.umcpCommand('get/modules/list').then(dojo.hitch(this, function(data) {
			// get all categories
			dojo.forEach(dojo.getObject('categories', false, data), dojo.hitch(this, function(i) {
				var cat = {
					id: i.id,
					description: i.name,
					title: i.name
				};
				this._categories.push(cat); 
			}));

			// hack a specific order
			//TODO: remove this hack
			//var cats1 = [];
			//var cats2 = this._categories;
			//dojo.forEach(['favorites', 'ucsschool'], function(id) {
			//	var tmpCats = cats2;
			//	cats2 = [];
			//	dojo.forEach(tmpCats, function(icat) {
			//		if (id == icat.id) {
			//			cats1.push(icat);
			//		}
			//		else {
			//			cats2.push(icat);
			//		}
			//	});
			//});
			//this._categories = cats1.concat(cats2);
			//console.log(cats1);
			//console.log(cats2);
			//console.log(this._categories);
			// end of hack :)

			// get all modules
			dojo.forEach(dojo.getObject('modules', false, data), dojo.hitch( this, function(module) {
				// try to load the module
				try {
					dojo['require']('umc.modules.' + module.id);
				}
				catch (error1) {
					// log as warning and continue with the next element in the list
					console.log('WARNING: Loading of module ' + module.id + ' failed. Ignoring it for now!');
					return true; 
				}

				// load the module
				// add module config class to internal list of available modules
				this._modules.push(dojo.mixin({
					BaseClass: dojo.getObject('umc.modules.' + module.id), 
					title: module.name
				}, module));

				// try to add dynamic style sheet information for module icons
				try {
					dojo.forEach([16, 24, 32, 64], function(isize) {
						var values = {
							s: isize,
							icon: module.icon
						};
						var css = dojo.replace(
							'background: no-repeat;' +
							'width: {s}px; height: {s}px;' +
							'background-image: url("images/icons/{s}x{s}/{icon}.png")',
							values);
						var rule = dojo.replace('.icon{s}-{icon}', values);
						dojox.html.insertCssRule(rule, css);
					});
				}
				catch (error2) {
					console.log(dojo.replace('ERROR: Could not create CSS information for module {id} using the icon name: {icon}', module));
				}
			}));

			// loading is done
			this.onModulesLoaded();
		}));
	},

	getModules: function(/*String?*/ category) {
		// summary:
		//		Get modules, either all or the ones for the specific category.
		//		The returned array contains objects with the properties
		//		{ BaseClass, id, title, description, categories }.
		// categoryID:
		//		Optional category name.

		var modules = this._modules;
		if (undefined !== category) {
			// find all modules with the given category
			modules = [];
			for (var imod = 0; imod < this._modules.length; ++imod) {
				// iterate over all categories for the module 
				var categories = this._modules[imod].categories;
				for (var icat = 0; icat < categories.length; ++icat) {
					// check whether the category matches the query
					if (category == categories[icat]) {
						modules.push(this._modules[imod]);
						break;
					}
				}
			}
		}

		// return all modules
		return modules; // Object[]
	},

	getModule: function(/*String*/ id) {
		// summary:
		//		Get the module object for a given module ID.
		//		The returned object has the following properties:
		//		{ BaseClass, id, description, category }.
		// id:
		//		Module ID as a string.

		var i;
		for (i = 0; i < this._modules.length; ++i) {
			if (this._modules[i].id == id) {
				return this._modules[i]; // Object
			}
		}
		return undefined; // undefined
	},

	getCategories: function() {
		// summary:
		//		Get all categories as an array. Each entry has the following properties:
		//		{ id, description }.
		return this._categories; // Object[]
	}
});


