/*global console dojo dojox dijit umc */

dojo.provide("umc.modules.roomadmin");

dojo.require("umc.modules.Module");
dojo.require("umc.widgets.FormWidget");
dojo.require("dojox.grid.EnhancedGrid");

dojo.declare("umc.modules.roomadmin", umc.modules.Module, {

	buildRendering: function() {
		this.inherited(arguments);

		var widgets = [{
			type: 'TextBox',
			name: 'myinput',
			value: 'some text',
			description: 'You can write some text here if you want to',
			label: 'My input field'
			// required: true
		}, {
			type: 'ComboBox',
			name: 'mychoice',
			value: 'choice1',
			description: 'Here you can make your personal choice!',
			label: 'My choice',
			// required: true
			staticValues: {
				choice1: 'first choice',
				choice2: 'second choice',
				choice3: 'third choice'
			}
		}, {
			type: 'TextBox',
			name: 'myinput2',
			value: 'some more text',
			description: 'You can write some more text here if you want to',
			label: 'My other input field'
			// required: true
		}, {
			type: 'ComboBox',
			name: 'mychoice2',
			value: 'choice2',
			description: 'Here you can make your personal choice a second time!',
			label: 'My next choice',
			// required: true
			staticValues: {
				choice2: 'A choice',
				choice3: 'B choice',
				choice1: 'C choice'
			}
		}];

		var buttons = [{
			name: 'submit',
			label: 'Speichern',
			callback: dojo.hitch(this, function() {
				console.log('### submit button');
				console.log(arguments);
				umc.tools.forIn(this._form.gatherFormValues(), function(val, key) {
					console.log('  ' + key + ': ' + val);
				});
				return false;
			})
		}, {
			name: 'reset',
			label: 'Werte zurueck setzen',
			callback: dojo.hitch(this, function() {
				console.log('### reset button');
				console.log(arguments);
				return true;
			})
		//}, {
		//	name: 'cancel',
		//	label: 'Abbrechen'
		}, {
			name: 'tralala',
			label: 'Tolle Wurst',
			callback: function() {
				console.log("hello world");
			}
		}];

		var layout = [
			[ 'myinput', 'mychoice' ],
			[ 'myinput2', 'mychoice2' ]
		];

		this._form = new umc.widgets.FormWidget({
			region: 'top',
			widgets: widgets,
			buttons: buttons,
			layout: layout
		});
		this.addChild(this._form);

		this._grid = new dojox.grid.EnhancedGrid({
			//id: 'ucrVariables',
			region: 'center',
			query: { object: '*', path: '*' },
			queryOptions: { ignoreCase: true },
			structure: layout,
			clientSort: true,
			store: new dojo.data.ItemFileReadStore({ data: {
				identifier: 'id',
				label: 'object',
				items: [
					{ id: 'id1', object: 'Administrator', path: 'univention.qa:/users/' },
					{ id: 'id2', object: 'join-backup', path: 'univention.qa:/users/' },
					{ id: 'id3', object: 'join-slave', path: 'univention.qa:/users/' },
					{ id: 'id4', object: 'spam', path: 'univention.qa:/users/' }
				]
			}}),
			rowSelector: '2px'
			//sortFields: {
			//	attribute: 'variable',
			//	descending: true
			//},
		});
		this.addChild(this._grid);

		/*dojo.connect(form, 'onSubmit', function() {
			console.log('### submitted');
			umc.tools.forIn(form.gatherFormValues(), function(val, key) {
				console.log('  ' + key + ': ' + val);
			});
		});*/


	}
});


