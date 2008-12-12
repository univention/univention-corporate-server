dojo.provide("dojox.data.jsonPathStore");
dojo.require("dojox.jsonPath");
dojo.require("dojo.date");
dojo.require("dojo.date.locale");
dojo.require("dojo.date.stamp");

dojox.data.ASYNC_MODE = 0;
dojox.data.SYNC_MODE = 1;

dojo.declare("dojox.data.jsonPathStore",
	null,
	{
		mode: dojox.data.ASYNC_MODE,
		metaLabel: "_meta",
		hideMetaAttributes: false,
		autoIdPrefix: "_auto_",
		autoIdentity: true,
		idAttribute: "_id",
		indexOnLoad: true,
		labelAttribute: "",
		url: "",
		_replaceRegex: /\'\]/gi,
		
		constructor: function(options){
			//summary:
			//	jsonPathStore constructor, instantiate a new jsonPathStore 
			//
			//	Takes a single optional parameter in the form of a Javascript object
			//	containing one or more of the following properties. 
			//
			//	data: /*JSON String*/ || /* Javascript Object */, 
			//		JSON String or Javascript object this store will control
			//		JSON is converted into an object, and an object passed to
			//		the store will be used directly.  If no data and no url
			//		is provide, an empty object, {}, will be used as the initial
			//		store.
			//
			//	url: /* string url */ 	
			//		Load data from this url in JSON format and use the Object
			//		created from the data as the data source.
			//
			//	indexOnLoad: /* boolean */ 
			//		Defaults to true, but this may change in the near future.
			//		Parse the data object and set individual objects up as
			//		appropriate.  This will add meta data and assign
			//		id's to objects that dont' have them as defined by the
			//		idAttribute option.  Disabling this option will keep this 
			//		parsing from happening until a query is performed at which
			//		time only the top level of an item has meta info stored.
			//		This might work in some situations, but you will almost
			//		always want to indexOnLoad or use another option which
			//		will create an index.  In the future we will support a 
			//		generated index that maps by jsonPath allowing the
			//		server to take some of this load for larger data sets. 
			//
			//	idAttribute: /* string */
			//		Defaults to '_id'. The name of the attribute that holds an objects id.
			//		This can be a preexisting id provided by the server.  
			//		If an ID isn't already provided when an object
			//		is fetched or added to the store, the autoIdentity system
			//		will generate an id for it and add it to the index. There
			//		are utility routines for exporting data from the store
			//		that can clean any generated IDs before exporting and leave
			//		preexisting id's in tact.
			//
			//	metaLabel: /* string */
			//		Defaults to '_meta' overrides the attribute name that is used by the store
			//		for attaching meta information to an object while
			//		in the store's control.  Defaults to '_meta'. 
			//	
			//	hideMetaAttributes: /* boolean */
			//		Defaults to False.  When enabled, calls to getAttributes() will not 
			//		include the meta attribute.
			//
			//	autoIdPrefix: /*string*/
			//		Defaults to "_auto_".  This string is used as the prefix to any
			//		objects which have a generated id. A numeric index is appended
			//		to this string to complete the ID
			//
			//	mode: dojox.data.ASYNC_MODE || dojox.data.SYNC_MODE
			//		Defaults to ASYNC_MODE.  This option sets the default mode for this store.
			//		Sync calls return their data immediately from the calling function
			//		instead of calling the callback functions.  Functions such as 
			//		fetchItemByIdentity() and fetch() both accept a string parameter in addtion
			//		to the normal keywordArgs parameter.  When passed this option, SYNC_MODE will
			//		automatically be used even when the default mode of the system is ASYNC_MODE.
			//		A normal request to fetch or fetchItemByIdentity (with kwArgs object) can also 
			//		include a mode property to override this setting for that one request.

			//setup a byId alias to the api call	
			this.byId=this.fetchItemByIdentity;

			if (options){
				dojo.mixin(this,options);
			}

			this._dirtyItems=[];
			this._autoId=0;
			this._referenceId=0;
			this._references={};
			this._fetchQueue=[];
			this.index={};

			//regex to identify when we're travelling down metaObject (which we don't want to do) 
			var expr="("+this.metaLabel+"\'\])";
			this.metaRegex = new RegExp(expr);


			//no data or url, start with an empty object for a store
			if (!this.data && !this.url){
				this.setData({});
			}	

			//we have data, but no url, set the store as the data
			if (this.data && !this.url){
				this.setData(this.data);

				//remove the original refernce, we're now using _data from here on out
				delete this.data;
			}

			//given a url, load json data from as the store
			if (this.url){
				dojo.xhrGet({
					url: options.url,
					handleAs: "json",
					load: dojo.hitch(this, "setData"),
					sync: this.mode
				});
			}
		},

		_loadData: function(data){
			// summary:
			//	load data into the store. Index it if appropriate.
			if (this._data){
				delete this._data;
			}

			if (dojo.isString(data)){
				this._data = dojo.fromJson(data);
			}else{
				this._data = data;
			}
			
			if (this.indexOnLoad){
				this.buildIndex();		
			}	

			this._updateMeta(this._data, {path: "$"});

			this.onLoadData(this._data);
		},

		onLoadData: function(data){
			// summary
			//	Called after data has been loaded in the store.  
			//	If any requests happened while the startup is happening
			//	then process them now.

			while (this._fetchQueue.length>0){
				var req = this._fetchQueue.shift();
				this.fetch(req);
			}	

		},

		setData: function(data){
			// summary:
			//	set the stores' data to the supplied object and then 
			//	load and/or setup that data with the required meta info		
			this._loadData(data);
		},

		buildIndex: function(path, item){
			//summary: 
			//	parse the object structure, and turn any objects into
			//	jsonPathStore items. Basically this just does a recursive
			//	series of fetches which itself already examines any items
			//	as they are retrieved and setups up the required meta information. 
			//
			//	path: /* string */
			//		jsonPath Query for the starting point of this index construction.

			if (!this.idAttribute){
				throw new Error("buildIndex requires idAttribute for the store");
			}

			item = item || this._data;
			var origPath = path;
			path = path||"$";
			path += "[*]";
			var data = this.fetch({query: path,mode: dojox.data.SYNC_MODE});
			for(var i=0; i<data.length;i++){
				if(dojo.isObject(data[i])){
					var newPath = data[i][this.metaLabel]["path"];
					if (origPath){
						//console.log("newPath: ", newPath);
						//console.log("origPath: ", origPath);
						//console.log("path: ", path);
						//console.log("data[i]: ", data[i]);
						var parts = origPath.split("\[\'");
						var attribute = parts[parts.length-1].replace(this._replaceRegex,'');
						//console.log("attribute: ", attribute);
						//console.log("ParentItem: ", item, attribute);
						if (!dojo.isArray(data[i])){
							this._addReference(data[i], {parent: item, attribute:attribute});
							this.buildIndex(newPath, data[i]);
						}else{
							this.buildIndex(newPath,item);
						}
					}else{
						var parts = newPath.split("\[\'");
						var attribute = parts[parts.length-1].replace(this._replaceRegex,'');
						this._addReference(data[i], {parent: this._data, attribute:attribute});
						this.buildIndex(newPath, data[i]);
					}
				}
			}
		},

		_correctReference: function(item){
			// summary:
			//	make sure we have an reference to the item in the store
			//	and not a clone. Takes an item, matches it to the corresponding
			//	item in the store and if it is the same, returns itself, otherwise
			//	it returns the item from the store.
		
			if (this.index[item[this.idAttribute]][this.metaLabel]===item[this.metaLabel]){
				return this.index[item[this.idAttribute]];
			}
			return item;	
		},

		getValue: function(item, property){
			// summary:
			//	Gets the value of an item's 'property'
			//
			//	item: /* object */
			//	property: /* string */
			//		property to look up value for	
			item = this._correctReference(item);
			return item[property];
		},

		getValues: function(item, property){
			// summary:
			//	Gets the value of an item's 'property' and returns
			//	it.  If this value is an array it is just returned,
			//	if not, the value is added to an array and that is returned.
			//
			//	item: /* object */
			//	property: /* string */
			//		property to look up value for	
	
			item = this._correctReference(item);
			return dojo.isArray(item[property]) ? item[property] : [item[property]];
		},

		getAttributes: function(item){
			// summary:
			//	Gets the available attributes of an item's 'property' and returns
			//	it as an array. If the store has 'hideMetaAttributes' set to true
			//	the attributed identified by 'metaLabel' will not be included.
			//
			//	item: /* object */

			item = this._correctReference(item);
			var res = [];
			for (var i in item){
				if (this.hideMetaAttributes && (i==this.metaLabel)){continue;}
				res.push(i);
			}
			return res;
		},

		hasAttribute: function(item,attribute){
			// summary:
			//	Checks to see if item has attribute
			//
			//	item: /* object */
			//	attribute: /* string */
		
			item = this._correctReference(item);
			if (attribute in item){return true;}
			return false;	
		},

		containsValue: function(item, attribute, value){
			// summary:
			//	Checks to see if 'item' has 'value' at 'attribute'
			//
			//	item: /* object */
			//	attribute: /* string */
			//	value: /* anything */
			item = this._correctReference(item);

			if (item[attribute] && item[attribute]==value){return true}
			if (dojo.isObject(item[attribute]) || dojo.isObject(value)){
				if (this._shallowCompare(item[attribute],value)){return true}
			}
			return false;	
		},

		_shallowCompare: function(a, b){
			//summary does a simple/shallow compare of properties on an object
			//to the same named properties on the given item. Returns
			//true if all props match. It will not descend into child objects
			//but it will compare child date objects

			if ((dojo.isObject(a) && !dojo.isObject(b))|| (dojo.isObject(b) && !dojo.isObject(a))) {
				return false;
			}

			if ( a["getFullYear"] || b["getFullYear"] ){
				//confirm that both are dates
				if ( (a["getFullYear"] && !b["getFullYear"]) || (b["getFullYear"] && !a["getFullYear"]) ){
					return false;
				}else{
					if (!dojo.date.compare(a,b)){
						return true;
					}
					return false;
       				}
			}

			for (var i in b){	
				if (dojo.isObject(b[i])){
					if (!a[i] || !dojo.isObject(a[i])){return false}

					if (b[i]["getFullYear"]){
						if(!a[i]["getFullYear"]){return false}
						if (dojo.date.compare(a,b)){return false}	
					}else{
						if (!this._shallowCompare(a[i],b[i])){return false}
					}
				}else{	
					if (!b[i] || (a[i]!=b[i])){return false}
				}
			}

			//make sure there werent props on a that aren't on b, if there aren't, then
			//the previous section will have already evaluated things.

			for (var i in a){
				if (!b[i]){return false}
			}
			
			return true;
		},

		isItem: function(item){
			// summary:
			//	Checks to see if a passed 'item'
			//	is really a jsonPathStore item.  Currently
			//	it only verifies structure.  It does not verify
			//	that it belongs to this store at this time.
			//
			//	item: /* object */
			//	attribute: /* string */
		
			if (!dojo.isObject(item) || !item[this.metaLabel]){return false}
			if (this.requireId && this._hasId && !item[this._id]){return false}
			return true;
		},

		isItemLoaded: function(item){
			// summary:
			//	returns isItem() :)
			//
			//	item: /* object */

			item = this._correctReference(item);
			return this.isItem(item);
		},

		loadItem: function(item){
			// summary:
			//	returns true. Future implementatins might alter this 
			return true;
		},

		_updateMeta: function(item, props){
			// summary:
			//	verifies that 'item' has a meta object attached
			//	and if not it creates it by setting it to 'props'
			//	if the meta attribute already exists, mix 'props'
			//	into it.

			if (item && item[this.metaLabel]){
				dojo.mixin(item[this.metaLabel], props);
				return;
			}

			item[this.metaLabel]=props;
		},

		cleanMeta: function(data, options){
			// summary
			//	Recurses through 'data' and removes an
			//	meta information that has been attached. This
			//	function will also removes any id's that were autogenerated
			//	from objects.  It will not touch id's that were not generated

			data = data || this._data;

			if (data[this.metaLabel]){
				if(data[this.metaLabel]["autoId"]){
					delete data[this.idAttribute];
				}
				delete data[this.metaLabel];
			}

			if (dojo.isArray(data)){
				for(var i=0; i<data.length;i++){
					if(dojo.isObject(data[i]) || dojo.isArray(data[i]) ){
						this.cleanMeta(data[i]);
					}
				}
			} else if (dojo.isObject(data)){
				for (var i in data){
					this.cleanMeta(data[i]);
				}
			}
		}, 

		fetch: function(args){
			//console.log("fetch() ", args);
			// summary
			//	
			//	fetch takes either a string argument or a keywordArgs
			//	object containing the parameters for the search.
			//	If passed a string, fetch will interpret this string
			//	as the query to be performed and will do so in 
			//	SYNC_MODE returning the results immediately.
			//	If an object is supplied as 'args', its options will be 
			// 	parsed and then contained query executed. 
			//
			//	query: /* string or object */
			//		Defaults to "$..*". jsonPath query to be performed 
			//		on data store. **note that since some widgets
			//		expect this to be an object, an object in the form
			//		of {query: '$[*'], queryOptions: "someOptions"} is
			//		acceptable	
			//
			//	mode: dojox.data.SYNC_MODE || dojox.data.ASYNC_MODE
			//		Override the stores default mode.
			//
			//	queryOptions: /* object */
			//		Options passed on to the underlying jsonPath query
			//		system.
			//
			//	start: /* int */
			//		Starting item in result set
			//
			//	count: /* int */
			//		Maximum number of items to return
			//
			//	sort: /* function */
			//		Not Implemented yet
			//
			//	The following only apply to ASYNC requests (the default)
			//
			//	onBegin: /* function */
			//		called before any results are returned. Parameters
			//		will be the count and the original fetch request
			//	
			//	onItem: /*function*/
			//		called for each returned item.  Parameters will be
			//		the item and the fetch request
			//
			//	onComplete: /* function */
			//		called on completion of the request.  Parameters will	
			//		be the complete result set and the request
			//
			//	onError: /* function */
			//		colled in the event of an error

			// we're not started yet, add this request to a queue and wait till we do	
			if (!this._data){
				this._fetchQueue.push(args);
				return args;
			}	
			if(dojo.isString(args)){
					query = args;
					args={query: query, mode: dojox.data.SYNC_MODE};
					
			}

			var query;
			if (!args || !args.query){
				if (!args){
					var args={};	
				}

				if (!args.query){
					args.query="$..*";
					query=args.query;
				}

			}

			if (dojo.isObject(args.query)){
				if (args.query.query){
					query = args.query.query;
				}else{
					query = args.query = "$..*";
				}
				if (args.query.queryOptions){
					args.queryOptions=args.query.queryOptions
				}
			}else{
				query=args.query;
			}

			if (!args.mode) {args.mode = this.mode;}
			if (!args.queryOptions) {args.queryOptions={};}

			args.queryOptions.resultType='BOTH';
			var results = dojox.jsonPath.query(this._data, query, args.queryOptions);
			var tmp=[];
			var count=0;
			for (var i=0; i<results.length; i++){
				if(args.start && i<args.start){continue;}
				if (args.count && (count >= args.count)) { continue; }

				var item = results[i]["value"];
				var path = results[i]["path"];
				if (!dojo.isObject(item)){continue;}
				if(this.metaRegex.exec(path)){continue;}

				//this automatically records the objects path
				this._updateMeta(item,{path: results[i].path});

				//if autoIdentity and no id, generate one and add it to the item
				if(this.autoIdentity && !item[this.idAttribute]){
					var newId = this.autoIdPrefix + this._autoId++;
					item[this.idAttribute]=newId;
					item[this.metaLabel]["autoId"]=true;
				}

				//add item to the item index if appropriate
				if(item[this.idAttribute]){this.index[item[this.idAttribute]]=item}
				count++;
				tmp.push(item);
			}
			results = tmp;
			var scope = args.scope || dojo.global;

			if ("sort" in args){
				console.log("TODO::add support for sorting in the fetch");
			}	

			if (args.mode==dojox.data.SYNC_MODE){ 
				return results; 
			};

			if (args.onBegin){	
				args["onBegin"].call(scope, results.length, args);
			}

			if (args.onItem){
				for (var i=0; i<results.length;i++){	
					args["onItem"].call(scope, results[i], args);
				}
			}
 
			if (args.onComplete){
				args["onComplete"].call(scope, results, args);
			}

			return args;
		},

		dump: function(options){
			// summary:
			//
			//	exports the store data set. Takes an options
			//	object with a number of parameters
			//
			//	data: /* object */
			//		Defaults to the root of the store.
		 	//		The data to be exported.
			//	
			//	clone: /* boolean */
			//		clone the data set before returning it 
			//		or modifying it for export
			//
			//	cleanMeta: /* boolean */
			//		clean the meta data off of the data. Note
			//		that this will happen to the actual
			//		store data if !clone. If you want
			//		to continue using the store after
			//		this operation, it is probably better to export
			//		it as a clone if you want it cleaned.
			//
			//	suppressExportMeta: /* boolean */
			//		By default, when data is exported from the store
			//		some information, such as as a timestamp, is
			//		added to the root of exported data.  This
			//		prevents that from happening.  It is mainly used
			//		for making tests easier.
			//
			//	type: "raw" || "json"
			//		Defaults to 'json'. 'json' will convert the data into 
			//		json before returning it. 'raw' will just return a
			//		reference to the object	 

			var options = options || {};
			var d=options.data || this._data;
	
			if (!options.suppressExportMeta && options.clone){
				data = dojo.clone(d);
				if (data[this.metaLabel]){
					data[this.metaLabel]["clone"]=true;
				}
			}else{
				var data=d;
			}

			if (!options.suppressExportMeta &&  data[this.metaLabel]){
				data[this.metaLabel]["last_export"]=new Date().toString()
			}

			if(options.cleanMeta){
				this.cleanMeta(data);
			}

			//console.log("Exporting: ", options, dojo.toJson(data));	
			switch(options.type){
				case "raw":
					return data;
				case "json":
				default:
					return dojo.toJson(data);
			}
		},	

		getFeatures: function(){
			// summary:
			// 	return the store feature set

			return { 
				"dojo.data.api.Read": true,
				"dojo.data.api.Identity": true,
				"dojo.data.api.Write": true,
				"dojo.data.api.Notification": true
			}
		},

		getLabel: function(item){
			// summary
			//	returns the label for an item. The label
			//	is created by setting the store's labelAttribute 
			//	property with either an attribute name	or an array
			//	of attribute names.  Developers can also
			//	provide the store with a createLabel function which
			//	will do the actaul work of creating the label.  If not
			//	the default will just concatenate any of the identified
			//	attributes together.
			item = this._correctReference(item);
			var label="";

			if (dojo.isFunction(this.createLabel)){
				return this.createLabel(item);
			}

			if (this.labelAttribute){
				if (dojo.isArray(this.labelAttribute))	{
					for(var i=0; i<this.labelAttribute.length; i++){
						if (i>0) { label+=" ";}
						label += item[this.labelAttribute[i]];
					}
					return label;
				}else{
					return item[this.labelAttribute];
				}
			}
			return item.toString();
		},

		getLabelAttributes: function(item){
			// summary:
			//	returns an array of attributes that are used to create the label of an item
			item = this._correctReference(item);
			return dojo.isArray(this.labelAttribute) ? this.labelAttribute : [this.labelAttribute];
		},

		sort: function(a,b){
			console.log("TODO::implement default sort algo");
		},

		//Identity API Support

		getIdentity: function(item){
			// summary
			//	returns the identity of an item or throws
			//	a not found error.

			if (this.isItem(item)){
				return item[this.idAttribute];
			}
			throw new Error("Id not found for item");
		},

		getIdentityAttributes: function(item){
			// summary:
			//	returns the attributes which are used to make up the 
			//	identity of an item.  Basically returns this.idAttribute

			return [this.idAttribute];
		},

		fetchItemByIdentity: function(args){
			// summary: 
			//	fetch an item by its identity. This store also provides
			//	a much more finger friendly alias, 'byId' which does the
			//	same thing as this function.  If provided a string
			//	this call will be treated as a SYNC request and will 
			//	return the identified item immediatly.  Alternatively it
			// 	takes a object as a set of keywordArgs:
			//	
			//	identity: /* string */
			//		the id of the item you want to retrieve
			//	
			//	mode: dojox.data.SYNC_MODE || dojox.data.ASYNC_MODE
			//		overrides the default store fetch mode
			//	
			//	onItem: /* function */
			//		Result call back.  Passed the fetched item.
			//
			//	onError: /* function */
			//		error callback.	
			var id;	
			if (dojo.isString(args)){
				id = args;
				args = {identity: id, mode: dojox.data.SYNC_MODE}
			}else{
				if (args){
					id = args["identity"];		
				}
				if (!args.mode){args.mode = this.mode}	
			}

			if (this.index && (this.index[id] || this.index["identity"])){
				
				if (args.mode==dojox.data.SYNC_MODE){
					return this.index[id];
				}

				if (args.onItem){
					args["onItem"].call(args.scope || dojo.global, this.index[id], args);
				}

				return args;
			}else{
				if (args.mode==dojox.data.SYNC_MODE){
					return false;
				}
			}


			if(args.onError){
				args["onItem"].call(args.scope || dojo.global, new Error("Item Not Found: " + id), args);
			}
			
			return args;
		},

		//Write API Support
		newItem: function(data, options){
			// summary:
			//	adds a new item to the store at the specified point.
			//	Takes two parameters, data, and options. 
			//
			//	data: /* object */
			//		The data to be added in as an item.  This could be a
			//		new javascript object, or it could be an item that 
			//		already exists in the store.  If it already exists in the 
			//		store, then this will be added as a reference.  
			//
			//	options: /* object */
			//
			//		item: /* item */
			//			reference to an existing store item
			//
			//		attribute: /* string */
			//			attribute to add the item at.  If this is
			//			not provided, the item's id will be used as the
			//			attribute name. If specified attribute is an
			//			array, the new item will be push()d on to the
			//			end of it.
			//		oldValue: /* old value of item[attribute]
			//		newValue: new value item[attribute]

			var meta={};

			//default parent to the store root;
			var pInfo ={item:this._data};

			if (options){
				if (options.parent){
					options.item = options.parent;
				}

				dojo.mixin(pInfo, options);
			}

			if (this.idAttribute && !data[this.idAttribute]){
				if (this.requireId){throw new Error("requireId is enabled, new items must have an id defined to be added");}
				if (this.autoIdentity){
					var newId = this.autoIdPrefix + this._autoId++;
					data[this.idAttribute]=newId;
					meta["autoId"]=true;
				}
			}	

			if (!pInfo && !pInfo.attribute && !this.idAttribute && !data[this.idAttribute]){
				throw new Error("Adding a new item requires, at a minumum, either the pInfo information, including the pInfo.attribute, or an id on the item in the field identified by idAttribute");
			}

			//pInfo.parent = this._correctReference(pInfo.parent);
			//if there is no parent info supplied, default to the store root
			//and add to the pInfo.attribute or if that doestn' exist create an
			//attribute with the same name as the new items ID 
			if(!pInfo.attribute){pInfo.attribute = data[this.idAttribute]}

			pInfo.oldValue = this._trimItem(pInfo.item[pInfo.attribute]);
			if (dojo.isArray(pInfo.item[pInfo.attribute])){
				this._setDirty(pInfo.item);
				pInfo.item[pInfo.attribute].push(data);
			}else{
				this._setDirty(pInfo.item);
				pInfo.item[pInfo.attribute]=data;
			}

			pInfo.newValue = pInfo.item[pInfo.attribute];

			//add this item to the index
			if(data[this.idAttribute]){this.index[data[this.idAttribute]]=data}

			this._updateMeta(data, meta)

			//keep track of all references in the store so we can delete them as necessary
			this._addReference(data, pInfo);

			//mark this new item as dirty
			this._setDirty(data);

			//Notification API
			this.onNew(data, pInfo);

			//returns the original item, now decorated with some meta info
			return data;
		},

		_addReference: function(item, pInfo){
			// summary
			//	adds meta information to an item containing a reference id
			//	so that references can be deleted as necessary, when passed
			//	only a string, the string for parent info, it will only
			//	it will be treated as a string reference

			//console.log("_addReference: ", item, pInfo);	
			var rid = '_ref_' + this._referenceId++;
			if (!item[this.metaLabel]["referenceIds"]){
				item[this.metaLabel]["referenceIds"]=[];
			}

			item[this.metaLabel]["referenceIds"].push(rid);
			this._references[rid] = pInfo;				
		},

		deleteItem: function(item){	
			// summary
			//	deletes item and any references to that item from the store.
			//	If the desire is to delete only one reference, unsetAttribute or
			//	setValue is the way to go.

			item = this._correctReference(item);
			console.log("Item: ", item);
			if (this.isItem(item)){
				while(item[this.metaLabel]["referenceIds"].length>0){
					console.log("refs map: " , this._references);
					console.log("item to delete: ", item);
					var rid = item[this.metaLabel]["referenceIds"].pop();
					var pInfo = this._references[rid];

					console.log("deleteItem(): ", pInfo, pInfo.parent);
					parentItem = pInfo.parent;
					var attribute = pInfo.attribute;	
					if(parentItem && parentItem[attribute] && !dojo.isArray(parentItem[attribute])){
						this._setDirty(parentItem);
						this.unsetAttribute(parentItem, attribute);
						delete parentItem[attribute];
					}

					if (dojo.isArray(parentItem[attribute])){
						console.log("Parent is array");
						var oldValue = this._trimItem(parentItem[attribute]);
						var found=false;
						for (var i=0; i<parentItem[attribute].length && !found;i++){
							if (parentItem[attribute][i][this.metaLabel]===item[this.metaLabel]){
								found=true;	
							}			
						}	

						if (found){
							this._setDirty(parentItem);
							var del =  parentItem[attribute].splice(i-1,1);
							delete del;
						}

						var newValue = this._trimItem(parentItem[attribute]);
						this.onSet(parentItem,attribute,oldValue,newValue);	
					}
					delete this._references[rid];

				}
				this.onDelete(item);		
				delete item;
			}
		},

		_setDirty: function(item){
			// summary:
			//	adds an item to the list of dirty items.  This item
			//	contains a reference to the item itself as well as a
			//	cloned and trimmed version of old item for use with
			//	revert.

			//if an item is already in the list of dirty items, don't add it again
			//or it will overwrite the premodification data set.
			for (var i=0; i<this._dirtyItems.length; i++){
				if (item[this.idAttribute]==this._dirtyItems[i][this.idAttribute]){
					return; 
				}	
			}

			this._dirtyItems.push({item: item, old: this._trimItem(item)});
			this._updateMeta(item, {isDirty: true});
		},

		setValue: function(item, attribute, value){
			// summary:
			//	sets 'attribute' on 'item' to 'value'
			item = this._correctReference(item);

			this._setDirty(item);
			var old = item[attribute] | undefined;
			item[attribute]=value;
			this.onSet(item,attribute,old,value);

		},

		setValues: function(item, attribute, values){
			// summary:
			//	sets 'attribute' on 'item' to 'value' value
			//	must be an array.


			item = this._correctReference(item);
			if (!dojo.isArray(values)){throw new Error("setValues expects to be passed an Array object as its value");}
			this._setDirty(item);
			var old = item[attribute] || null;
			item[attribute]=values
			this.onSet(item,attribute,old,values);
		},

		unsetAttribute: function(item, attribute){
			// summary:
			//	unsets 'attribute' on 'item'

			item = this._correctReference(item);
			this._setDirty(item);
			var old = item[attribute];
			delete item[attribute];
			this.onSet(item,attribute,old,null);
		},

		save: function(kwArgs){
			// summary:
			//	Takes an optional set of keyword Args with
			//	some save options.  Currently only format with options
			//	being "raw" or "json".  This function goes through
			//	the dirty item lists, clones and trims the item down so that
			//	the items children are not part of the data (the children are replaced
			//	with reference objects). This data is compiled into a single array, the dirty objects
			//	are all marked as clean, and the new data is then passed on to the onSave handler.

			var data = [];
		
			if (!kwArgs){kwArgs={}}
			while (this._dirtyItems.length > 0){
				var item = this._dirtyItems.pop()["item"];
				var t = this._trimItem(item);
				var d;	
				switch(kwArgs.format){	
					case "json":
						d = dojo.toJson(t);	
						break;
					case "raw":
					default:
						d = t;
				}
				data.push(d);
				this._markClean(item);
			}

			this.onSave(data);
		},

		_markClean: function(item){
			// summary
			//	remove this meta information marking an item as "dirty"

			if (item && item[this.metaLabel] && item[this.metaLabel]["isDirty"]){
				delete item[this.metaLabel]["isDirty"];
			}	
		},

		revert: function(){
			// summary
			//	returns any modified data to its original state prior to a save();

			while (this._dirtyItems.length>0){
				var d = this._dirtyItems.pop();
				this._mixin(d.item, d.old);
			}
			this.onRevert();
		},

		_mixin: function(target, data){
			// summary:
			//	specialized mixin that hooks up objects in the store where references are identified.

			if (dojo.isObject(data)){
				if (dojo.isArray(data)){
					while(target.length>0){target.pop();}
					for (var i=0; i<data.length;i++){
						if (dojo.isObject(data[i])){
							if (dojo.isArray(data[i])){
								var mix=[];
							}else{
								var mix={};
								if (data[i][this.metaLabel] && data[i][this.metaLabel]["type"] && data[i][this.metaLabel]["type"]=='reference'){
									target[i]=this.index[data[i][this.idAttribute]];
									continue;
								}
							}

							this._mixin(mix, data[i]);
							target.push(mix);
						}else{
							target.push(data[i]);
						}
					}	
				}else{
					for (var i in target){
						if (i in data){continue;}
						delete target[i];
					}

					for (var i in data){
						if (dojo.isObject(data[i])){
							if (dojo.isArray(data[i])){
								var mix=[];
							}else{
								if (data[i][this.metaLabel] && data[i][this.metaLabel]["type"] && data[i][this.metaLabel]["type"]=='reference'){
									target[i]=this.index[data[i][this.idAttribute]];
									continue;
								}

								var mix={};
							}
							this._mixin(mix, data[i]);
							target[i]=mix;
						}else{
							target[i]=data[i];
						}
					}	

				}
			}
		},

		isDirty: function(item){
			// summary
			//	returns true if the item is marked as dirty.

			item = this._correctReference(item);
			return item && item[this.metaLabel] && item[this.metaLabel]["isDirty"];
		},

		_createReference: function(item){
			// summary
			// 	Create a small reference object that can be used to replace
			//	child objects during a trim

			var obj={};
			obj[this.metaLabel]={
				type:'reference'
			};

			obj[this.idAttribute]=item[this.idAttribute];
			return obj;
		},

		_trimItem: function(item){
			//summary:
			// 	copy an item recursively stoppying at other items that have id's
			//	and replace them with a refrence object;
			var copy;
			if (dojo.isArray(item)){
				copy = [];
				for (var i=0; i<item.length;i++){
					if (dojo.isArray(item[i])){
						copy.push(this._trimItem(item[i]))
					}else if (dojo.isObject(item[i])){
						if (item[i]["getFullYear"]){
							copy.push(dojo.date.stamp.toISOString(item[i]));
						}else if (item[i][this.idAttribute]){
							copy.push(this._createReference(item[i]));
						}else{
							copy.push(this._trimItem(item[i]));	
						}
					} else {
						copy.push(item[i]);	
					}
				}
				return copy;
			} 

			if (dojo.isObject(item)){
				copy = {};

				for (var attr in item){
					if (!item[attr]){ copy[attr]=undefined;continue;}
					if (dojo.isArray(item[attr])){
						copy[attr] = this._trimItem(item[attr]);
					}else if (dojo.isObject(item[attr])){
						if (item[attr]["getFullYear"]){
							copy[attr] =  dojo.date.stamp.toISOString(item[attr]);
						}else if(item[attr][this.idAttribute]){
							copy[attr]=this._createReference(item[attr]);
						} else {
							copy[attr]=this._trimItem(item[attr]);
						}
					} else {
						copy[attr]=item[attr];
					}
				}
				return copy;
			}
		},

		//Notifcation Support

		onSet: function(){
		},

		onNew: function(){

		},

		onDelete: function(){

		},	
	
		onSave: function(items){
			// summary:
			//	notification of the save event..not part of the notification api, 
			//	but probably should be.
			//console.log("onSave() ", items);
		},

		onRevert: function(){
			// summary:
			//	notification of the revert event..not part of the notification api, 
			//	but probably should be.

		}
	}
);

//setup an alias to byId, is there a better way to do this?
dojox.data.jsonPathStore.byId=dojox.data.jsonPathStore.fetchItemByIdentity;
