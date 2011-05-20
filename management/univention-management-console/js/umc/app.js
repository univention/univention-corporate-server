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
dojo.require("umc.widgets.Toaster");
dojo.require("umc.widgets.LoginDialog");
dojo.require("umc.widgets.ContainerPane");
dojo.require("umc.widgets.OverviewWidget");

// start the application when everything has been loaded
dojo.addOnLoad(function() {
	umc.app.start();
	/*window.onerror = function (msg, url, num) {
		console.log(msg + ';' + url + ';' + num);
		return true;
	};*/
});

dojo.mixin(umc.app, {

	notify: function(message) {
		this.toaster.setContent(message, 'message');
	},

	alert: function(message) {
		this.alertDialog.set('content', message);
		this.alertDialog.show();
	},

	confirm: function(message) {

	},

//	standby: function(/*Boolean*/ enable) {
//		if (enable === true) {
//			this._standbyWidget.show();
//		}
//		else {
//			this._standbyWidget.hide();
//		}
//	},

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
		this.loggingIn = true;
		this.loginDialog = umc.widgets.LoginDialog({});
		this.loginDialog.startup();
		dojo.connect(this.loginDialog, 'onLogin', this, 'onLogin');

		// create alert dialog
		this.alertDialog = new dijit.Dialog({
			content: '',
			title: 'UMC2-Alert'
		});

		// create toaster
		this.toaster = new umc.widgets.Toaster({ });

		// check whether we still have a app cookie
		var sessionCookie = dojo.cookie('UMCSessionId');
		if (undefined === sessionCookie) {
			this.loginDialog.show();
		}
		else {
			this.onLogin(dojo.cookie('univention.umc.username'));
			console.log('Login is still valid (cookie: ' + sessionCookie + ', username: ' + this.username + ').');
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
		dojo.cookie('univention.umc.username', username, { expires: 100, path: '/' });
		this.loginDialog.hide();
		this.loadModules();
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
		//console.log('#A1');
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
		var overviewContainer = new umc.widgets.ContainerPane({ 
			//style: "overflow:visible; width: 80%"
			title: 'Overview',
			iconClass: 'icon16-univention' 
		});

		// add an OverviewWidget for each category
		dojo.forEach(this.getCategories(), dojo.hitch(this, function(icat) {
			// create a new overview widget for all modules in the given category
			//console.log('### add category: ' + icat);
			var overviewWidget = new umc.widgets.OverviewWidget({
				modules: this.getModules(icat.id),
				title: icat.title
			});

			// register to requests for opening a module
			dojo.connect(overviewWidget, 'onOpenModule', dojo.hitch(this, this.openModule));

			// add overview widget to container
			overviewContainer.addChild(overviewWidget);
		}));
		umc.app._tabContainer.addChild(overviewContainer);
		
		// the header
		var header = new umc.widgets.ContainerPane({
			title: '',
			'class': 'umcHeader',
			region: 'top'
		});
		topContainer.addChild( header );

		// add some buttons
		header.addChild(new dijit.form.Button({
			label: 'Hilfe',
			'class': 'umcHeaderButton'
		}));
		header.addChild(new dijit.form.Button({
			label: 'Ueber UMC',
			'class': 'umcHeaderButton'
		}));

		// the user context menu
		var menu = new dijit.Menu({});
		menu.addChild(new dijit.CheckedMenuItem({
			label: 'Tooltips',
			checked: umc.app.tooltipsVisible(),
			onClick: function() {
				umc.app.showTooltips(this.checked);
			}
		}));
		menu.addChild(new dijit.CheckedMenuItem({
			label: 'Nachfragen',
			checked: true
		}));
		//menu.startup();
		header.addChild(new dijit.form.DropDownButton({
			label: 'Benutzer: ' + this.username,
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
		umc.widgets.isSetupGUI = true;
	},

	showTooltips: function(visible) {
		if (!visible) {
			dojo.cookie('univention.umc.tooltips', 'false', { expires: 100, path: '/' } );
			this.alert('Tooltips sind ausgeschaltet.');
		}
		else {
			dojo.cookie('univention.umc.tooltips', null, { expires: -1, path: '/' });
			this.alert('Tooltips werden angezeigt.');
		}
	},

	tooltipsVisible: function() {
		var cookie = dojo.cookie('univention.umc.tooltips');
		return undefined === cookie || 'true' == cookie;
	},

	_modules: [],
	_categories: [],
	loadModules: function() {
		//console.log('### loadModules');
		umc.tools.xhrPostJSON(
			{}, 
			'/umcp/get/modules/list',
			dojo.hitch(this, function(data, ioargs) {
				if (200 != dojo.getObject('xhr.status', false, ioargs)) {
					return;
				}

				//console.log('### loadModules response');
				//console.log(data);

				// get all given categories
				dojo.forEach(dojo.getObject('categories', false, data), dojo.hitch(this, function(i) {
					var cat = {
						id: i.id,
						description: i.name,
						title: i.name
					};
					this._categories.push(cat); 
				}));

				// get all given modules
				for (var imod in dojo.getObject('modules', false, data)) {
					if (data.modules.hasOwnProperty(imod)) {
						//console.log('### load module data: umc.modules.' + imod);
						dojo.require('umc.modules.' + imod);
						//console.log('### module data loaded');
						this._modules.push({
							BaseClass: dojo.getObject('umc.modules.' + imod), 
							id: imod, 
							title: data.modules[imod].name,
							description: data.modules[imod].description,
							categories: data.modules[imod].categories //['all'] // TODO: bug in server, wrong categories
						});
					}
				}

				// loading is done
				this.onModulesLoaded();
			})
		);
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


