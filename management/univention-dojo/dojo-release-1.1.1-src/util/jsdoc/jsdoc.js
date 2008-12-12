jsdoc = {nodes: {}};

dojo.addOnLoad(function(){
	dojo.query("#jsdoc-manage table").forEach(function(table){
		dojo.connect(dojo.byId("jsdoc-manage"), "onsubmit", function(e){
			var valid = true;
			dojo.query("select", table).forEach(function(select){
				if(select.options.length > 1 && select.selectedIndex == 0){
					valid = false;
				}
			});
			if(!valid){
				alert("All variables must either be marked as new, or used in a rename.");
				dojo.stopEvent(e);
			}
		});

		dojo.query("input", table).forEach(function(checkbox){
			var parts = checkbox.value.split("|");
			var node = {
				project: parts[0],
				resource: parts[1],
				title: parts[2],
				nid: parts[3],
				vid: parts[4]
			}
			jsdoc.nodes[node.nid + "_" + node.vid] = node;
			dojo.connect(checkbox, "onchange", function(){
				dojo.publish("/jsdoc/onchange", [checkbox.checked, node.nid + "_" + node.vid]);
			});
		});

		dojo.query("select", table).forEach(function(select){
			dojo.connect(select, "onchange", function(){
				if(select.selectedIndex == 0){
					dojo.publish("/jsdoc/onchange", [false, select.last, select]);
				}else if(select.selectedIndex > 0){
					var option = select.options[select.selectedIndex];
					select.last = option.value;
					dojo.publish("/jsdoc/onchange", [true, option.value, select]);
				}
			});
			dojo.subscribe("/jsdoc/onchange", null, function(checked, id, current){
				if(current === select){
					return;
				}
				var node = jsdoc.nodes[id];
				if(!checked){
					if(select.name.indexOf("modified[" + node.project + "]") == 0){
						var i = select.options.length++;
						select.options[i].value = id;
						select.options[i].text = node.title + " in " + node.resource;
					}
				}else{
					dojo.query("option[value=" + id + "]", select).orphan();
				}
			});
		});
	});
});