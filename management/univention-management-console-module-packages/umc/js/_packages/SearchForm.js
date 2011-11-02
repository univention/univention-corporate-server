/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._packages.SearchForm");

dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("umc.store");

dojo.require("umc.widgets.Form");

dojo.declare("umc.modules._packages.SearchForm",
		[
        	umc.widgets.Form,
        	umc.i18n.Mixin 
        ], {
	
	i18nClass:		'umc.modules.packages',
	
	postMixInProperties: function() {
		
		try
		{
			dojo.mixin(this, {
				widgets:
				[
					{
						name:					'section',
						label:					this._("Package categories"),
						type:					'ComboBox',
						staticValues:			[{ id: 'all', label: this._("--- all ---") }],
						sortStaticValues:		false,
						required:				true,
						dynamicValues:			'packages/sections',
						onDynamicValuesLoaded:	dojo.hitch(this, function() {
							this.allowSearchButton(true);
						}),
						sortDynamicValues:		true,
						onChange:				dojo.hitch(this, function() {
							this._check_submit_allow();
						})
					},
					{
						name:					'installed',
						label:					this._("Installed packages only"),
						type:					'CheckBox'
// doesn't make sense: a Bool on its own is always valid.
//						onChange:				dojo.hitch(this, function() {
//							this._check_submit_allow();
//						})
					},
					{
						name:					'key',
						label:					this._("Search key"),
						type:					'ComboBox',
						staticValues: [
		             		 { id: 'package',		label: this._("Package name") },
		             		 { id: 'description',	label: this._("Package description") }
						],
						sortStaticValues:		false,
						onChange:				dojo.hitch(this, function() {
							this._check_submit_allow();
						})
					},
					{
						name:					'pattern',
						label:					this._("Pattern"),
						type:					'TextBox',
						value:					'*',
						required:				true,
						onChange:				dojo.hitch(this, function() {
							this._check_submit_allow();
						})
					}
				],
				buttons:
				[
					{
						name:		'submit',
						label:		this._("Search")
					},
					{
						name:		'reset',
						label:		this._("Reset")
					}
				],
				layout:
				[
					[ 'section', 'installed' ],
					[ 'key', 'pattern' ],
					[ 'reset', 'submit']
				]
			});
		}
		catch(error)
		{
			console.error("SearchForm::postMixInProperties() ERROR: " + error.message);
		}
		
		this.inherited(arguments);
	},
	
	// TODO What is the correct way start the form with a disabled 'submit' button?
	
//	buildRendering: function() {
//		
//		this.inherited(arguments);
//		this.allowSearchButton(false);	// as long as the combobox is not ready
//	},
	
//	startup: function() {
//		this.inherited(arguments);
//		this.allowSearchButton(false);	// as long as the combobox is not ready
//	},
	
	_check_submit_allow: function() {
		
		var allow = true;
		for (var w in this._widgets)
		{
			if (w != 'installed')	// workaround for ComboBox
			{
				if (! this._widgets[w].isValid())
				{
					allow = false;
				}
			}
		}
		
		this.allowSearchButton(allow);
	},
	
	// while a query is pending the search button should be disabled. This function
	// is called from inside (onSubmit) and from outside (in the onFetchComplete
	// callback of the grid)
	allowSearchButton: function(on) {
		
		this._buttons['submit'].setDisabled(!on);
	},
	
	onSubmit: function() {
		
		this.allowSearchButton(false);
	}

});
