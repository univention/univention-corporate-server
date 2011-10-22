/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._pkgdb.SearchForm");

dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("umc.widgets.StandbyMixin");

// Search form as a seperate class, so the gory details are hidden from the main page.
//
dojo.declare("umc.modules._pkgdb.SearchForm", [
   	umc.widgets.Form, 
	umc.i18n.Mixin
	] , 
{

	i18nClass:			'umc.modules.pkgdb',
	
	// Some status variables
	_patterns_allowed:		false,		// true if operator is selectable
	_pattern_is_list:		false,		// true if pattern is ComboBox (not TextBox)
	
	postMixInProperties: function() {
		
		dojo.mixin(this,{
			widgets:
				[
					{
						type:					'ComboBox',
						name:					'key',
						label:					this._("Search for:"),
						style:					'width:250px;',
						staticValues:			[{id:'_', label: this._("--- Please select ---")}],
						sortDynamicValues:		false,
						dynamicValues:			'pkgdb/keys',
						dynamicOptions:			{page:this.pageKey},
						onDynamicValuesLoaded:	dojo.hitch(this, function(values) {
							this._set_selection_to_first_element('key');
						}),
						onChange:				dojo.hitch(this, function(value) {
							this.onQueryChanged('key',value);
						})
					},
					{
						type:					'ComboBox',
						name:					'operator',
						depends:				'key',
						label:					this._("Operator"),
						style:					'width:150px;',
						sortDynamicValues:		false,
						dynamicValues:			dojo.hitch(this, function() {
							return this._operators_query();
						}),
						onDynamicValuesLoaded:	dojo.hitch(this, function(values) {
							this._handle_operators(values);
						}),
						onChange:				dojo.hitch(this, function(value) {
							this.onQueryChanged('operator',value);
						})
					},
					{
						type:					'ComboBox',
						name:					'pattern_list',
						depends:				'key',
						label:					this._("Pattern"),
						style:					'width:350px;',
						sortDynamicValues:		false,
						dynamicValues:			dojo.hitch(this, function() {
							return this._proposals_query();
						}),
						onDynamicValuesLoaded:	dojo.hitch(this, function(values) {
							this._handle_proposals(values);
						}),
						onChange:				dojo.hitch(this, function(value) {
							this.onQueryChanged('pattern_list',value);
						})
					},
					{
						type:					'TextBox',
						name:					'pattern_text',
						label:					this._("Pattern"),
						style:					'width:350px;',
						onChange:				dojo.hitch(this, function(value) {
							this.onQueryChanged('pattern_text',value);
						}),
						// inherits from dijit.form.ValidationTextBox, so we can use its
						// validation abilities
						regExp:					'^[A-Za-z0-9_.*?-]+$',		// [:alnum:] and these: _ - . * ?
						required:				true						// force nonempty
					}
				],
			layout:
				[
					['key','operator','pattern_text','pattern_list'],
					['submit']
				],
			buttons:
				[
					{
						name:		'submit',
						label:		this._("Search"),
						disabled:	true
					}
				]
		});

		// call the postMixinProperties of inherited classes AFTER! we have
		// added our constructor args!
		this.inherited(arguments);

	},
	
	buildRendering: function() {
		
		this.inherited(arguments);
		
		this.showWidget('pattern_text',false);
		this.showWidget('pattern_list',false);
		this.showWidget('operator',false);
	},
	
	// ---------------------------------------------------------------------
	//
	//		functions to be called from outside
	//
	//		These are the functions that are called by the instance
	//		that created us (our ancestor).
	//
	// ---------------------------------------------------------------------
	
	// Will be called when the grid data is readily loaded.
	// Inside, we use this to show that a query is underway.
	enableSearchButton: function(on) {
		this._buttons['submit'].set('disabled',!on);
	},
	
	// switch dialog elements (ComboBoxes + TextBox) while a query
	// is underway, simply to inhibit weird things from impatient users
	enableEntryElements: function(on) {

		for (var w in this._widgets)
		{
			var widget = this._widgets[w];
			widget.set('disabled',!on);
		}
	},
	
	// Reads the corresponding dialog elements and returns the current query
	// as a dict with key, operand and pattern.
	//
	// If this is called even while the dialog state doesn't allow executing
	// a query -> return an empty dict.
	getQuery: function() {
		
		var query = {};
		
		var crit = this.getWidget('key').get('value');
		if (crit != '_')
		{
			query['key'] = crit;
			if (this._patterns_allowed)
			{
				query['operator'] = this.getWidget('operator').get('value');
				if (this._pattern_is_list)
				{
					query['pattern'] = this.getWidget('pattern_list').get('value');
				}
				else
				{
					query['pattern'] = this.getWidget('pattern_text').get('value');
				}
			}
		}
			
		return query;
	},

	// -------------------------------------------------------------------
	//
	//		dynamic queries
	//
	//		It is not enough to have 'dynamicValues' and 'dynamicOptions'
	//		at widget construction time; we need variable options while
	//		the widget is alive.
	//
	//		These functions can't return the dojo.Deferred as returned
	//		from umcpCommand since that would hand over the whole response
	//		(with 'status','message' and 'result' elements) to the ComboBox.
	//		Instead, we return a chained dojo.Deferred that extracts the
	//		'result' element from there.
	//
	// -------------------------------------------------------------------
	
	// dynamic options for the ComboBox that presents comparison operators
	// suitable for a given key
	_operators_query: function() {
		
		try
		{
			// While the query is underway I can always see the 'invalid' indicator
			// at the 'operator' ComboBox. So I try to set the ComboBox to a
			// neutral value.
			this.getWidget('operator').set('value',null);
			
			var value = this.getWidget('key').get('value');

			return umc.tools.umcpCommand('pkgdb/operators',{
				page:		this.pageKey,
				key:		value
			}).then(function(data) { return data.result; });
		}
		catch(error)
		{
			console.error("operators_query: " + error.message);
		}
		// What should I return if the combobox is invisible and the query
		// does not make sense at all?
		return null;
	},
	
	// returns proposals for the 'pattern' field for a given combination of
	// key and operator. (pageKey is added silently)
	_proposals_query: function() {
		
		try
		{
			// While the query is underway I can always see the 'invalid' indicator
			// at the 'pattern_list' ComboBox. So I try to set the ComboBox to a
			// neutral value.
			this.getWidget('pattern_list').set('value',null);

			var key = this.getWidget('key').get('value');
			
			return umc.tools.umcpCommand('pkgdb/proposals',{
				page:		this.pageKey,
				key:		key
			}).then(function(data) { return data.result; });
		}
		catch(error)
		{
			console.error("proposals_query: " + error.message);
		}
		return null;
	},

	// ------------------------------------------------------------
	//
	//		handlers for return values
	//
	// ------------------------------------------------------------
	
	// handles the result of the operators query. Special functions are:-
	//
	//	-	if the value is not an array: hide the operators combobox
	//		and use the returned value as 'label' property for the
	//		pattern entry, be it the ComboBox or the TextBox.
	//	-	if the result set is empty: hide operators AND patterns
	//		entirely.
	//
	_handle_operators: function(values) {
		if (dojo.isArray(values))
		{
			if (values.length)
			{
				this._set_selection_to_first_element('operator');
				this._allow_patterns(true);
			}
			else
			{
				this._allow_patterns(false);
			}
		}
		else
		{
			this._set_single_operator(values);
		}
	},
	
	// handles the result (and especially: the result type) of the
	// proposals returned by the 'pkgdb/proposals' query
	_handle_proposals: function(values) {
		
		if (! this._patterns_allowed) { return; }			// nothing to do here.
		
		var is_single = dojo.isString(values);
		this._pattern_is_list = !is_single;				// remember for later.
		if (is_single)
		{
			this.getWidget('pattern_text').set('value',values);
		}
		else
		{
			this._set_selection_to_first_element('pattern_list');
		}
		// values are set. now show/hide appropriately.
		this.showWidget('pattern_text',is_single);
		this.showWidget('pattern_list',!is_single);
	},
	
	// If we get a single operator we use it as a label for the
	// text input. Here is the function that switches the corresponding
	// status values.
	_set_single_operator: function(operator) {
		
		this._patterns_allowed = true;
		this.showWidget('operator',false);
		this._set_selection_to_first_element('operator');
		this.getWidget('operator').set('value',operator);
		
		this.getWidget('pattern_text').set('label',operator);
		this.getWidget('pattern_list').set('label',operator);

		this.showWidget('pattern_text',true);
		this.showWidget('pattern_list',false);
	},

	// switches exutability of this query on or off: shows or hides
	// the 'operator' and 'pattern' elements. Additionally remembers
	// the last given pattern so subsequent handlers know the state.
	_allow_patterns: function(allow) {
		this._patterns_allowed = allow;
		
		this.showWidget('operator',allow);
		
		// at least, if NOT allowed -> hide both 'pattern_*' widgets.
		// showing one of them depending on allowed values must
		// be deferred until we have the 'proposals' data back.
		if (! allow)
		{
			this.showWidget('pattern_text',false);
			this.showWidget('pattern_list',false);
		}
		else
		{
			this.getWidget('pattern_text').set('label',this._("Pattern"));
			this.getWidget('pattern_list').set('label',this._("Pattern"));
		}
	},
	
	_set_selection_to_first_element: function(name) {

		var widget = this.getWidget(name);
		if (widget)
		{
			widget.set('value',widget._firstValueInList);
		}
	},
	
	// We can't inhibit that onSubmit() is being called even if we have
	// explicitly set a widget to invalid... why do widgets have this
	// feature if the form doesn't honor it?
	onSubmit: function() {
		
		var keys = this.getWidget('key');
		var ok = ((keys.get('value') != '_') && (keys.getAllItems().length > 1));
		if (ok)
		{
			// this widget must not be honored since it is invisible
			var ignore = (this._pattern_is_list ? 'pattern_text' : 'pattern_list');
			for (var w in this._widgets)
			{
				var widget = this._widgets[w];
				if (widget.name != ignore)
				{
					if (! widget.isValid())
					{
						ok = false;
					}
				}
			}
		}
		if (ok)
		{
			this.onExecuteQuery(this.getQuery());
		}
	},
	
	// -----------------------------------------------------------------------
	//
	//		callbacks
	//
	//		These are stub functions that our ancestor is supposed to listen on.
	//
	
	// our follow-up of the submit event, called only if submit is allowed.
	// For the convenience of the caller, we pass the current query.
	onExecuteQuery: function(query) {
		this.enableSearchButton(false);
		this.enableEntryElements(false);
	},
	
	// invoked whenever a substantial dialog element is being changed. The
	// ancestor can listen here and clear (or switch invisible) the result
	// grid. Args are the name of the field being changed, and the new value.
	onQueryChanged: function(field,value) {
		if (field == 'key')
		{
			this.enableSearchButton(value != '_');
		}
	}
	
});