/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._pkgdb.Page");

dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("umc.widgets.StandbyMixin");
dojo.require("umc.widgets.Grid");

dojo.require("umc.modules._pkgdb.SearchForm");
dojo.require("umc.modules._pkgdb.KeyTranslator");

// Page with a unified layout
//
//	-	whole thing stuffed into an ExpandingTitlePane
//	-	one-line search form (for now...?)
//	-	results grid
//
// Which page ('flavor') to show is determined by the 'pageKey'
// attribute being set by the constructor call.
//
dojo.declare("umc.modules._pkgdb.Page", [
   	umc.widgets.Page, 
    umc.widgets.StandbyMixin,
	umc.i18n.Mixin,
	umc.modules._pkgdb.KeyTranslator
	] , 
{

	i18nClass:			'umc.modules.pkgdb',
	
	_grid:						null,			// holds the results grid if query was invoked at least once
	_last_table_structure:		null,			// remember last table structure
	_current_query:				null,			// what is being executed right now

	buildRendering: function() {
		
		this.inherited(arguments);
		
		this._pane = new umc.widgets.ExpandingTitlePane({
			title:			this.title
		});
		this.addChild(this._pane);
		
		this._searchform = new umc.modules._pkgdb.SearchForm({
			region:			'top',
			pageKey:		this.pageKey
		});
		this._pane.addChild(this._searchform);
		
		// Listen to the submit event
		dojo.connect(this._searchform,'onExecuteQuery',dojo.hitch(this, function(query) {
			this._execute_query(query);
		}));
		
	},
	
	// fetches the structure of the result grid. The callback returns
	// the current query to us.
	_execute_query: function(query) {
		
		this._current_query = query;
		
		try
		{
			umc.tools.umcpCommand('pkgdb/columns',{
				page: this.pageKey,
				key: this._current_query['key']
			}).then(dojo.hitch(this, function(data) {
				this._create_table(data.result);
			}));
		}
		catch(error)
		{
			console.error('execute_query: ' + error.message);
		}
	},
	
	// Creates the given result table. 'fields' is an array of column names.
	// The corresponding query is already stored in this._current_query. 
	_create_table: function(fields) {
		
		try
		{
			// determine if we have already a grid structured like that
			var grid_usable = false;
			var sig = fields.join(':');
			if (this._grid)
			{
				if (this._last_table_structure && (this._last_table_structure == sig))
				{
					grid_usable = true;
				}
			}			
			this._last_table_structure = sig;
			
			if (! grid_usable)
			{			
				var columns = [];
				
				for (var f in fields)
				{
					var fname = fields[f];
					var entry = {
							name:	fname,
							label:	fname
						};
					var props = this._field_options(fname);
					if (props)
					{
						dojo.mixin(entry,props);
					}
					columns.push(entry);
				}
					
				var newgrid = new umc.widgets.Grid({
					region:			'center',
					actions:		[],
					columns:		columns,
					moduleStore:	umc.store.getModuleStore(fields[0],'pkgdb')
				});
				
				if (this._grid)
				{
					// detach and free old grid instance
					this._pane.removeChild(this._grid);
					this._grid.uninitialize();
					this._grid = null;
				}
				this._grid = newgrid;
				this._pane.addChild(this._grid);

				// No time to debug why this Grid does not call 'onFilterDone()'
				dojo.connect(this._grid,'onFilterDone',dojo.hitch(this, function(success) {
					this._searchform.enableSearchButton(true);
					this._searchform.enableEntryElements(true);
				}));
				dojo.connect(this._grid._grid,'_onFetchComplete',dojo.hitch(this, function() {
					this._searchform.enableSearchButton(true);
					this._searchform.enableEntryElements(true);
				}));
				dojo.connect(this._grid._grid,'_onFetchError',dojo.hitch(this, function() {
					this._searchform.enableSearchButton(true);
					this._searchform.enableEntryElements(true);
				}));
			}
			
			dojo.toggleClass(this._grid.domNode,'dijitHidden',false);

			// Execute the given query (a.k.a. filter) on the grid
			this._grid.filter(
				dojo.mixin({
					page:	this.pageKey
				},
				this._current_query)
			);
			
		}
		catch(error)
		{
			console.error('create_table: ' + error.message);
		}
	}
	
	
});

