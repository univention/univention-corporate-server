dojo.provide("dojox.data.tests.stores.jsonPathStore");
dojo.require("dojox.data.jsonPathStore");

dojox.data.tests.stores.jsonPathStore.error = function(t, d, errData){
	//  summary:
	//		The error callback function to be used for all of the tests.
	d.errback(errData);	
}

dojox.data.tests.testData=dojo.toJson({"store": {"book": [{"category": "reference", "author": "Nigel Rees", "title": "Sayings of the Century", "price": 8.95}, {"category": "fiction", "author": "Evelyn Waugh", "title": "Sword of Honour", "price": 12.99}, {"category": "fiction", "author": "Herman Melville", "title": "Moby Dick", "isbn": "0-553-21311-3", "price": 8.99}, {"category": "fiction", "author": "J. R. R. Tolkien", "title": "The Lord of the Rings", "isbn": "0-395-19395-8", "price": 22.99}], "bicycle": {"color": "red", "price": 19.95}}});

dojox.data.tests.test_ID_Data=dojo.toJson({"gadgetList": {"myId": "product", "1000": {"name": "Gadget", "type": "Junk", "myId": "1000", "price": "19.99"}, "1001": {"name": "Gadget2", "type": "Junk", "myId": "1010", "price": "17.99"}, "1003": {"name": "Gadget3", "type": "Junk", "myId": "1009", "price": "15.99"}, "1004": {"name": "Gadget4", "type": "Junk", "myId": "1008", "price": "13.99"}, "1005": {"name": "Gadget5", "type": "Junk", "myId": "1007", "price": "11.99"}, "1006": {"name": "Gadget6", "type": "Junk", "myId": "1006", "price": "9.99"}}, "testList": {"a": {"name": "test", "type": "Junk", "myId": "3000", "price": "19.99"}, "b": {"name": "test2", "type": "Junk", "myId": "3010", "price": "17.99"}, "c": {"name": "test3", "type": "Junk", "myId": "3009", "price": "15.99"}, "d": {"name": "test4", "type": "Junk", "myId": "3008", "price": "13.99"}, "e": {"name": "test5", "type": "Junk", "myId": "3007", "price": "11.99"}, "f": {"name": "test6", "type": "Junk", "myId": "3006", "price": "9.99"}}, "bricknbrack": [{"name": "BrickNBrack", "type": "Junk", "myId": "2000", "price": "19.99"}, {"name": "BrickNBrack2", "type": "Junk", "myId": "2010", "price": "17.99"}, {"name": "BrickNBrack3", "type": "Junk", "myId": "2009", "price": "15.99"}, {"name": "BrickNBrack4", "type": "Junk", "myId": "2008", "price": "13.99"}, {"name": "BrickNBrack5", "type": "Junk", "myId": "2007", "price": "11.99"}, {"name": "BrickNBrack6", "type": "Junk", "myId": "2006", "price": "9.99"}]});

doh.register("dojox.data.tests.stores.jsonPathStore", 
	[
		{
			name: "Create, Index, Export: {clone: true, suppressExportMeta: true}", 
			options: {clone: true, suppressExportMeta: true},
			runTest: function(t) {
				var original= dojox.data.tests.test_ID_Data;
				var store= new dojox.data.jsonPathStore({
					data: original,
					mode: dojox.data.SYNC_MODE,
					idAttribute: "myId",
					indexOnLoad: true
				});

				//snapshot of the store after creation;	
				var storeWithMeta = dojo.toJson(store._data);
				var result = store.dump(this.options); 
				doh.assertEqual(storeWithMeta, result);
			}
		},
		{
			name: "Create, Index, Export: {cleanMeta: true, clone: true}", 
			options: {cleanMeta: true, clone: true, suppressExportMeta: true},
			runTest: function(t) {
				var original= dojox.data.tests.test_ID_Data;
				var store= new dojox.data.jsonPathStore({
					data: original,
					mode: dojox.data.SYNC_MODE,
					idAttribute: "myId",
					indexOnLoad: true
				});

				var result = store.dump(this.options); 
				doh.assertEqual(original, result);
			}
		},
		{
			name: "Create, Index, Export: {suppressExportMeta: true}", 
			options: {suppressExportMeta: true},
			runTest: function(t) {
				var original= dojox.data.tests.test_ID_Data;
				var store= new dojox.data.jsonPathStore({
					data: original,
					mode: dojox.data.SYNC_MODE,
					idAttribute: "myId",
					indexOnLoad: true
				});

				//snapshot of the store after creation;	
				var storeWithMeta = dojo.toJson(store._data);
				var result = store.dump(this.options); 
				doh.assertEqual(storeWithMeta, result);
			}
		},
		{
			name: "Create, Index, Export: {clone: true, type: 'raw',  suppressExportMeta: true}", 
			options: {clone: true, type: "raw", suppressExportMeta: true},
			runTest: function(t) {
				var original= dojox.data.tests.test_ID_Data;
				var store= new dojox.data.jsonPathStore({
					data: original,
					mode: dojox.data.SYNC_MODE,
					idAttribute: "myId",
					indexOnLoad: true
				});

				//snapshot of the store after creation;	
				var storeWithMeta = dojo.toJson(store._data);
				var result = dojo.toJson(store.dump(this.options)); 
				doh.assertEqual(storeWithMeta, result);
			}
		},
		{
			name: "Create, Index, Export: {clone: true, suppressExportMeta: true}", 
			options: {cleanMeta: true},
			runTest: function(t) {
				var original= dojox.data.tests.test_ID_Data;
				var store= new dojox.data.jsonPathStore({
					data: original,
					mode: dojox.data.SYNC_MODE,
					idAttribute: "myId",
					indexOnLoad: true
				});

				//snapshot of the store after creation;	
				var result = store.dump(this.options); 
				doh.assertEqual(original, result);
			}
		},
		{
			name: "Create, Index, Export: {type: raw}", 
			options: {type: "raw"},
			runTest: function(t) {
				var original= dojox.data.tests.test_ID_Data;
				var store= new dojox.data.jsonPathStore({
					data: original,
					mode: dojox.data.SYNC_MODE,
					idAttribute: "myId",
					indexOnLoad: true
				});

				//snapshot of the store after creation;	
				var result = dojo.toJson(store.dump(this.options)); 
				var storeWithMeta = dojo.toJson(store._data);
				doh.assertEqual(storeWithMeta, result);
			}
		},
		{
			name: "ReadAPI:  fetch() Empty Request Test [SYNC_MODE]",
			runTest: function(t) {
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.SYNC_MODE});
				var success = dojo.toJson([{"book": [{"category": "reference", "author": "Nigel Rees", "title": "Sayings of the Century", "price": 8.95, "_meta": {"path": "$['store']['book'][0]", "autoId": true, "referenceIds": ["_ref_1"]}, "_id": "_auto_3"}, {"category": "fiction", "author": "Evelyn Waugh", "title": "Sword of Honour", "price": 12.99, "_meta": {"path": "$['store']['book'][1]", "autoId": true, "referenceIds": ["_ref_2"]}, "_id": "_auto_4"}, {"category": "fiction", "author": "Herman Melville", "title": "Moby Dick", "isbn": "0-553-21311-3", "price": 8.99, "_meta": {"path": "$['store']['book'][2]", "autoId": true, "referenceIds": ["_ref_3"]}, "_id": "_auto_5"}, {"category": "fiction", "author": "J. R. R. Tolkien", "title": "The Lord of the Rings", "isbn": "0-395-19395-8", "price": 22.99, "_meta": {"path": "$['store']['book'][3]", "autoId": true, "referenceIds": ["_ref_4"]}, "_id": "_auto_6"}], "bicycle": {"color": "red", "price": 19.95, "_meta": {"path": "$['store']['bicycle']", "autoId": true, "referenceIds": ["_ref_5"]}, "_id": "_auto_2"}, "_meta": {"path": "$['store']", "autoId": true, "referenceIds": ["_ref_0"]}, "_id": "_auto_0"}, [{"category": "reference", "author": "Nigel Rees", "title": "Sayings of the Century", "price": 8.95, "_meta": {"path": "$['store']['book'][0]", "autoId": true, "referenceIds": ["_ref_1"]}, "_id": "_auto_3"}, {"category": "fiction", "author": "Evelyn Waugh", "title": "Sword of Honour", "price": 12.99, "_meta": {"path": "$['store']['book'][1]", "autoId": true, "referenceIds": ["_ref_2"]}, "_id": "_auto_4"}, {"category": "fiction", "author": "Herman Melville", "title": "Moby Dick", "isbn": "0-553-21311-3", "price": 8.99, "_meta": {"path": "$['store']['book'][2]", "autoId": true, "referenceIds": ["_ref_3"]}, "_id": "_auto_5"}, {"category": "fiction", "author": "J. R. R. Tolkien", "title": "The Lord of the Rings", "isbn": "0-395-19395-8", "price": 22.99, "_meta": {"path": "$['store']['book'][3]", "autoId": true, "referenceIds": ["_ref_4"]}, "_id": "_auto_6"}], {"color": "red", "price": 19.95, "_meta": {"path": "$['store']['bicycle']", "autoId": true, "referenceIds": ["_ref_5"]}, "_id": "_auto_2"}, {"category": "reference", "author": "Nigel Rees", "title": "Sayings of the Century", "price": 8.95, "_meta": {"path": "$['store']['book'][0]", "autoId": true, "referenceIds": ["_ref_1"]}, "_id": "_auto_3"}, {"category": "fiction", "author": "Evelyn Waugh", "title": "Sword of Honour", "price": 12.99, "_meta": {"path": "$['store']['book'][1]", "autoId": true, "referenceIds": ["_ref_2"]}, "_id": "_auto_4"}, {"category": "fiction", "author": "Herman Melville", "title": "Moby Dick", "isbn": "0-553-21311-3", "price": 8.99, "_meta": {"path": "$['store']['book'][2]", "autoId": true, "referenceIds": ["_ref_3"]}, "_id": "_auto_5"}, {"category": "fiction", "author": "J. R. R. Tolkien", "title": "The Lord of the Rings", "isbn": "0-395-19395-8", "price": 22.99, "_meta": {"path": "$['store']['book'][3]", "autoId": true, "referenceIds": ["_ref_4"]}, "_id": "_auto_6"}]);
				var result = dojo.toJson(store.fetch());
				doh.assertEqual(success, result);
				return true;
			}
		},

		{
			name: "ReadAPI:  fetch('$.store.book[*]') test [SYNC_MODE]",
			runTest: function(t) {
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.SYNC_MODE});
				var success = dojo.toJson([{"category": "reference", "author": "Nigel Rees", "title": "Sayings of the Century", "price": 8.95, "_meta": {"path": "$['store']['book'][0]", "autoId": true, "referenceIds": ["_ref_1"]}, "_id": "_auto_3"}, {"category": "fiction", "author": "Evelyn Waugh", "title": "Sword of Honour", "price": 12.99, "_meta": {"path": "$['store']['book'][1]", "autoId": true, "referenceIds": ["_ref_2"]}, "_id": "_auto_4"}, {"category": "fiction", "author": "Herman Melville", "title": "Moby Dick", "isbn": "0-553-21311-3", "price": 8.99, "_meta": {"path": "$['store']['book'][2]", "autoId": true, "referenceIds": ["_ref_3"]}, "_id": "_auto_5"}, {"category": "fiction", "author": "J. R. R. Tolkien", "title": "The Lord of the Rings", "isbn": "0-395-19395-8", "price": 22.99, "_meta": {"path": "$['store']['book'][3]", "autoId": true, "referenceIds": ["_ref_4"]}, "_id": "_auto_6"}]);
				var result = dojo.toJson(store.fetch({query:"$.store.book[*]"})); 	
				doh.assertEqual(success, result);
				return true;
			}
		},
		{
			name: "ReadAPI:  fetch('$.store.book[*]') test [ASYNC_MODE forced SYNC_MODE by string parameter]",
			runTest: function(t) {
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.ASYNC_MODE});
				var success = dojo.toJson([{"category": "reference", "author": "Nigel Rees", "title": "Sayings of the Century", "price": 8.95, "_meta": {"path": "$['store']['book'][0]", "autoId": true, "referenceIds": ["_ref_1"]}, "_id": "_auto_3"}, {"category": "fiction", "author": "Evelyn Waugh", "title": "Sword of Honour", "price": 12.99, "_meta": {"path": "$['store']['book'][1]", "autoId": true, "referenceIds": ["_ref_2"]}, "_id": "_auto_4"}, {"category": "fiction", "author": "Herman Melville", "title": "Moby Dick", "isbn": "0-553-21311-3", "price": 8.99, "_meta": {"path": "$['store']['book'][2]", "autoId": true, "referenceIds": ["_ref_3"]}, "_id": "_auto_5"}, {"category": "fiction", "author": "J. R. R. Tolkien", "title": "The Lord of the Rings", "isbn": "0-395-19395-8", "price": 22.99, "_meta": {"path": "$['store']['book'][3]", "autoId": true, "referenceIds": ["_ref_4"]}, "_id": "_auto_6"}]);
				var result = dojo.toJson(store.fetch("$.store.book[*]")); 	
				doh.assertEqual(success, result);
				return true;
			}
		},
		{
			name: "ReadAPI:  fetch({query: '$.store.book[*]', start: 2})",
			runTest: function(t) {
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.SYNC_MODE});
				var success = dojo.toJson([{"category": "fiction", "author": "Herman Melville", "title": "Moby Dick", "isbn": "0-553-21311-3", "price": 8.99, "_meta": {"path": "$['store']['book'][2]", "autoId": true, "referenceIds": ["_ref_3"]}, "_id": "_auto_5"}, {"category": "fiction", "author": "J. R. R. Tolkien", "title": "The Lord of the Rings", "isbn": "0-395-19395-8", "price": 22.99, "_meta": {"path": "$['store']['book'][3]", "autoId": true, "referenceIds": ["_ref_4"]}, "_id": "_auto_6"}]);
				var result = dojo.toJson(store.fetch({query: '$.store.book[*]', start: 2}));
				doh.assertEqual(success, result);
				return true;
			}
		},
		{
			name: "ReadAPI:  fetch({query: '$.store.book[*]', start: 2, count: 1})",
			runTest: function(t) {
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.SYNC_MODE});
				var result = store.fetch({query: "$.store.book[*]", start: 2, count: 1}); 	
				doh.assertEqual(result[0].author, 'Herman Melville');
				return true;
			}
		},

		{
			name: "ReadAPI: fetch(query: '$.store.book[0]'...callbacks...) [ASYNC_MODE]",
			runTest: function(datastore, t){
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData});
				var d = new doh.Deferred();
				function onBegin(count, args){
					doh.assertEqual(1, count);	
				}
				function onItem(item){
					doh.assertTrue(store.isItem(item));
				}

				function onComplete(results){
					doh.assertEqual(1, results.length);
					doh.assertEqual("Nigel Rees", results[0]["author"]);
					d.callback(true);
				}

				function onError(errData){
					t.assertTrue(false);
					d.errback(errData);
				}

				store.fetch({query: "$.store.book[0]", onBegin: onBegin, onItem: onItem, onError: onError, onComplete: onComplete});
				return d; // Deferred
			}
		},
		{
			name: "ReadAPI: isItem() test", 
			runTest: function(t) {
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.SYNC_MODE});
				var result = store.fetch("$.store.book[*].author"); 	
				doh.assertFalse(store.isItem(result[0]));
				result = store.fetch("$.store.book[*]"); 	
				doh.assertTrue(store.isItem(result[0]));
				return true;
			}
		},
		{
			name: "ReadAPI: getValue() test", 
			runTest: function(t) {
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.SYNC_MODE});
				var data = store.fetch("$.store.book[*]"); 	
				var result = store.getValue(data[0], "author");	
				doh.assertEqual("Nigel Rees", result);
				return true;
			}
		},
		{
			name: "ReadAPI: getValues() test", 
			runTest: function(t) {
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.SYNC_MODE});
				var result = store.fetch("$.store.book[*]"); 	
				doh.assertEqual(dojo.toJson(store.getValues(result[0], "author")),dojo.toJson(["Nigel Rees"]));
				return true;
			}
		},
		{
			name: "ReadAPI: getAttributes() test", 
			runTest: function(t) {
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.SYNC_MODE});
				var result = store.fetch("$.store.book[*]"); 	
				doh.assertEqual(dojo.toJson(store.getAttributes(result[0])),'["category","author","title","price","_meta","_id"]');
				return true;
			}
		},
		{
			name: "ReadAPI: getAttributes() test [hideMetaAttributes]", 
			runTest: function(t) {
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.SYNC_MODE, hideMetaAttributes: true});
				var result = store.fetch("$.store.book[*]"); 	
				doh.assertEqual('["category","author","title","price","_id"]',dojo.toJson(store.getAttributes(result[0])));
				return true;
			}
		},
		{
			name: "ReadAPI: hasAttribute() test", 
			runTest: function(t) {
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.SYNC_MODE});
				var result = store.fetch("$.store.book[*]"); 	
				doh.assertTrue(store.hasAttribute(result[0], "author"));
				doh.assertFalse(store.hasAttribute(result[0],"_im_invalid_fooBar"));
				return true;
			}
		},

		{
			name: "ReadAPI: containsValue() test", 
			runTest: function(t) {
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.SYNC_MODE});
				var result = store.fetch("$.store.book[*]"); 	
				doh.assertTrue(store.containsValue(result[0], "author", "Nigel Rees"));
				doh.assertFalse(store.containsValue(result[0], "author", "_im_invalid_fooBar"));
				return true;
			}
		},
		{
			name: "ReadAPI: getFeatures() test", 
			runTest: function(t) {
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.SYNC_MODE});
				//doh.debug("Store Features: ", dojo.toJson(store.getFeatures()));
				var success='{"dojo.data.api.Read":true,"dojo.data.api.Identity":true,"dojo.data.api.Write":true,"dojo.data.api.Notification":true}';
				doh.assertEqual(success,dojo.toJson(store.getFeatures()));
				return true;
			}
		},
		{
			name: "ReadAPI: getLabel(item) test [multiple label attributes]", 
			runTest: function(t) {
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.SYNC_MODE, labelAttribute: ["title", "author"]});
				var result = store.fetch("$.store.book[0]")[0]; 	
				doh.assertEqual("Sayings of the Century Nigel Rees",store.getLabel(result));
				return true;
			}
		},
		{
			name: "ReadAPI: getLabelAttributes(item) test [multiple label attributes]", 
			runTest: function(t) {
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.SYNC_MODE, labelAttribute: ["title", "author"]});
				var result = store.fetch("$.store.book[0]")[0]; 	
				doh.assertEqual('["title","author"]',dojo.toJson(store.getLabelAttributes(result)));
				return true;
			}
		},
		{
			name: "ReadAPI: getLabelAttributes(item) test [single label attribute]", 
			runTest: function(t) {
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.SYNC_MODE, labelAttribute: ["title"]});
				var result = store.fetch("$.store.book[0]")[0]; 	
				doh.assertEqual('["title"]',dojo.toJson(store.getLabelAttributes(result)));
				return true;
			}
		},
		{
			name: "jsonPathStore Feature: override createLabel", 
			runTest: function(t) {
				var createLabel = function(item){
					return item[this.labelAttribute[0]] + " By " + item[this.labelAttribute[1]];
				};

				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.SYNC_MODE, labelAttribute: ["title", "author"], createLabel: createLabel});
				var result = store.fetch("$.store.book[0]")[0]; 	
				doh.assertEqual('Sayings of the Century By Nigel Rees',store.getLabel(result));
				return true;
			}
		},
		{
			name: "jsonPathStore Feature: autoIdentity", 
			runTest: function(t) {
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.SYNC_MODE, idAttribute: "_id"});
				var result = dojo.toJson(store.fetch("$.store.book[0]")[0]); 	
				var success=dojo.toJson( {"category": "reference", "author": "Nigel Rees", "title": "Sayings of the Century", "price": 8.95, "_meta": {"path": "$['store']['book'][0]", "autoId": true, "referenceIds": ["_ref_1"]}, "_id": "_auto_3"});
				doh.assertEqual(success,result);
				return true;
			}
		},

		{
			name: "jsonPathStore Feature: autoIdentity [clean export removing added id attributes in addition to meta]", 
			runTest: function(t) {
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.SYNC_MODE, idAttribute: "_id"});
				//do a search to popuplate some of the itesm with autoId data
				var result = store.fetch("$.store.book[0]"); 	
				result = store.dump({cleanMeta: true});
				doh.assertEqual(dojox.data.tests.testData,result);
				return true;
			}
		},

		{
			name: "IdentityAPI: getIdentity(item)", 
			runTest: function(t) {
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.SYNC_MODE, idAttribute: "_id"});
				var data= store.fetch("$.store.book[0]")[0]; 	
				var result= store.getIdentity(data);
				var success="_auto_3";
				doh.assertEqual(success,result);
				return true;
			}
		},

		{
		
			name: "IdentityAPI: fetchItemByIdentity(item) [SYNC_MODE]", 
			runTest: function(t){
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.SYNC_MODE, idAttribute: "_id"});

				var data= store.fetch("$.store.book[0]")[0]; 	
				var id = store.getIdentity(data);
				var result = dojo.toJson(store.fetchItemByIdentity({identity:id}));
				var success = dojo.toJson(data);		
				doh.assertEqual(success,result);
				return true;
			}
		},
		{
		
			name: "jsonPathStore Feature: byId(item) [fetchItemByIdentity alias] [SYNC_MODE]", 
			runTest: function(t){
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.SYNC_MODE, idAttribute: "_id"});

				var data= store.fetch("$.store.book[0]")[0]; 	
				var id = store.getIdentity(data);
				var result = dojo.toJson(store.byId({identity:id}));
				var success = dojo.toJson(data);		
				doh.assertEqual(success,result);
				return true;
			}
		},

		{
			name: "IdentityAPI: fetchItemByIdentity(id) single Item [ASYNC_MODE]",
			timeout: 1000,
			runTest: function(datastore, t){
				//      summary:
				//              Simple test of the fetchItemByIdentity function of the store.
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, indexOnLoad: true});
				var d = new doh.Deferred();
				var query = {query: "$.store.book[0]", mode: dojox.data.SYNC_MODE};
				var data = store.fetch(query)[0];
				var id = store.getIdentity(data);

				function onItem(item){
					doh.assertTrue(store.isItem(item));
					doh.assertEqual(data["author"], item["author"]);
					d.callback(true);
				}

				function onError(errData){

					t.assertTrue(false);
					d.errback(errData);
				}

				store.fetchItemByIdentity({identity: id, onItem: onItem, onError: onError});

				return d; // Deferred
			}
		},
		{
			name: "IdentityAPI: getIdentityAttributes(item) ", 
			runTest: function(t) {
				var store= new dojox.data.jsonPathStore({data:dojox.data.tests.testData, mode: dojox.data.SYNC_MODE, idAttribute: "_id"});
				var data= store.fetch("$.store.book[0]")[0]; 	
				var result = dojo.toJson(store.getIdentityAttributes(data));
				var success = '["_id"]';
				doh.assertEqual(success,result);
				return true;
			}
		},
		{
			name: "WriteAPI: newItem(item) add to store root.",
			runTest: function(t) {
				var original = dojox.data.tests.testData;
				var store= new dojox.data.jsonPathStore({data:original, mode: dojox.data.SYNC_MODE, idAttribute: "_id"});

				var testObject = {
					propA: "foo",
					propB: "bar"
				}

				var testObject2 = {
					propA: "foo",
					propB: "bar"
				}

				var newItem = store.newItem(testObject);
				doh.assertTrue(store.isItem(newItem));	

				newItem = store.newItem(testObject2);
				doh.assertTrue(store.isItem(newItem));	

				return true; 
			}
		},
		{
			name: "WriteAPI: newItem(item) no idAttribute on data item, added only with pInfo",
			runTest: function(t) {
				var original = dojox.data.tests.testData;
				var store= new dojox.data.jsonPathStore({data:original, mode: dojox.data.SYNC_MODE});

				var parentItem = store.fetch("$.store.book[0]")[0];

				var testObject = {
					propA: "foo",
					propB: "bar"
				}

				var newItem = store.newItem(testObject,{parent: parentItem, attribute: "TEST_PROPERTY"});
				doh.assertTrue(store.isItem(newItem));	
				return true; 
			}
		},
		{
			name: "WriteAPI: newItem(item) given id, no parent Attribute",
			runTest: function(t) {
				var original = dojox.data.tests.testData;
				var store= new dojox.data.jsonPathStore({data:original, mode: dojox.data.SYNC_MODE, idAttribute: "_id"});

				var parentItem = store.fetch("$.store.book[0]")[0];

				var testObject = {
					_id: "99999",
					propA: "foo",
					propB: "bar"
				}

				var newItem = store.newItem(testObject,{parent: parentItem});
				doh.assertTrue(store.isItem(newItem));	
				return true; 
			}
		},
		{
			name: "WriteAPI: newItem(item) given id and  parent Attribute",
			runTest: function(t) {
				var original = dojox.data.tests.testData;
				var store= new dojox.data.jsonPathStore({data:original, mode: dojox.data.SYNC_MODE, idAttribute: "_id"});

				var parentItem = store.fetch("$.store.book[0]")[0];

				var testObject = {
					_id: "99999",
					propA: "foo",
					propB: "bar"
				}

				var newItem = store.newItem(testObject,{parent: parentItem, attribute: "TEST"});
				doh.assertTrue(store.isItem(newItem));	
				return true; 
			}
		},
		{
			name: "WriteAPI: newItem(item) adding to an array",
			runTest: function(t) {
				var original = dojox.data.tests.testData;
				var store= new dojox.data.jsonPathStore({data:original, mode: dojox.data.SYNC_MODE, idAttribute: "_id"});

				var parentItem = store.fetch("$.store")[0];

				var testObject = {
					_id: "99999",
					propA: "foo",
					propB: "bar"
				}

				var newItem = store.newItem(testObject,{parent: parentItem, attribute: "book"});
				doh.assertTrue(store.isItem(newItem));	
				return true; 
			}
		},
		{
			name: "WriteAPI: setValue(item, value)",
			runTest: function(t) {
				var original = dojox.data.tests.testData;
				var store= new dojox.data.jsonPathStore({data:original, mode: dojox.data.SYNC_MODE, indexOnLoad: true, idAttribute: "_id"});
				var item = store.fetch("$.store")[0];

				var snapshot = store.dump({clone:true, cleanMeta: false, suppressExportMeta: true});

				store.setValue(item, "Foo", "Bar");
				doh.assertEqual(store._data.store.Foo, "Bar");
				doh.assertTrue(store._data.store._meta.isDirty);
				store.save();
				doh.assertFalse(store._data.store._meta.isDirty);
				return true; 
			}
		},
		{
			name: "WriteAPI: setValues(item, value)",
			runTest: function(t) {
				var original = dojox.data.tests.testData;
				var store= new dojox.data.jsonPathStore({data:original, mode: dojox.data.SYNC_MODE, indexOnLoad: true, idAttribute: "_id"});
				var item = store.fetch("$.store")[0];

				var snapshot = store.dump({clone:true, cleanMeta: false, suppressExportMeta: true});

				store.setValues(item, "Foo", ["Bar", "Diddly", "Ar"]);
				doh.assertEqual(store._data.store.Foo[0], "Bar");
				doh.assertEqual(store._data.store.Foo.length, 3);
				doh.assertTrue(store._data.store._meta.isDirty);
				store.save();
				doh.assertFalse(store._data.store._meta.isDirty);
				return true; 
			}
		},
		{
			name: "WriteAPI: unsetAttribute(item, attribute)",
			runTest: function(t) {
				var original = dojox.data.tests.testData;
				var store= new dojox.data.jsonPathStore({data:original, mode: dojox.data.SYNC_MODE, indexOnLoad: true, idAttribute: "_id"});
				var item = store.fetch("$.store")[0];

				var snapshot = store.dump({clone:true, cleanMeta: false, suppressExportMeta: true});

				store.setValues(item, "Foo", ["Bar", "Diddly", "Ar"]);
				doh.assertEqual(store._data.store.Foo[0], "Bar");
				doh.assertEqual(store._data.store.Foo.length, 3);
				doh.assertTrue(store._data.store._meta.isDirty);
				store.save();
				doh.assertFalse(store._data.store._meta.isDirty);
				store.unsetAttribute(item,"Foo");
				doh.assertFalse(item.Foo);
				doh.assertTrue(store._data.store._meta.isDirty);
				store.save();
				doh.assertFalse(store._data.store._meta.isDirty);
				return true; 
			}
		},
		{
			name: "WriteAPI: revert()",
			runTest: function(t) {
				var original = dojox.data.tests.testData;
				var store= new dojox.data.jsonPathStore({data:original, mode: dojox.data.SYNC_MODE, indexOnLoad: true, idAttribute: "_id"});
				var item = store.fetch("$.store")[0];

				var snapshot = store.dump({clone:true, cleanMeta: false, suppressExportMeta: true});

				store.setValues(item, "Foo", ["Bar", "Diddly", "Ar"]);
				doh.assertEqual(store._data.store.Foo[0], "Bar");
				doh.assertEqual(store._data.store.Foo.length, 3);
				doh.assertTrue(store._data.store._meta.isDirty);
				store.revert();
				doh.assertFalse(store._data.store._meta.isDirty);
				doh.assertFalse(store._data.store.Foo);
				return true; 
			}
		}
	]
);
