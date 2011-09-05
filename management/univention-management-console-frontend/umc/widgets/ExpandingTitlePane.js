/*global dojo dijit dojox umc console window */

dojo.provide("umc.widgets.ExpandingTitlePane");

dojo.require("dijit.layout.BorderContainer");

dojo.declare("umc.widgets.ExpandingTitlePane", dijit.layout.BorderContainer, {
	// summary:
	//		Widget visually similar to dijit.TitlePane which expands in height/width
	//		(e.g., in a dijit.layout.BorderContainer) and can display scollable	content.
	// description:
	//		This widget is visually similar to a (non-closable) dijit.TitlePane.
	//		However, it can be used in cases where the size of the widgets is
	//		adapted to a given layout (e.g., as a center element in a
	//		dijit.layout.BorderContainer), and where the content may be scrollable.

	// title: String
	//		Title displayed in the header element of the widget.
	title: '',

	// gutters are set to false by default
	gutters: false,

	// internal reference to the main container to which child elements are added
	_contentContainer: null,

	// internal reference to the ContentPane that holds the title
	_titlePane: null,

	_userProps: null,

	constructor: function(props) {
		// store the user defined properties
		this._userProps = dojo.mixin({}, props);
	},

	postMixInProperties: function() {
		this.inherited(arguments);

		this.design = 'sidebar';

		// remove title from the attributeMap
		delete this.attributeMap.title;
	},

	buildRendering: function() {
		this.inherited(arguments);

		// create the title element... style it to look like the head of a dijit.TitlePane
		this._titlePane = new dijit.layout.ContentPane({
			'class': 'dijitTitlePaneTitle',
			content: '<div class="dijitTitlePaneTitleFocus">' + this.title + '</div>',
			region: 'top'
		});
		this.inherited('addChild', [ this._titlePane ]);

		// create the container for the main content... add css classes to be similar
		// the dijit.TitlePane container
		var props = dojo.mixin({}, this._userProps, {
			region: 'center',
			gutters: false,
			'class': 'dijitTitlePaneContentOuter dijitTitlePaneContentInner'
		});
		this._contentContainer = new dijit.layout.BorderContainer(props);
		this.inherited('addChild', [ this._contentContainer ]);
	},

	addChild: function(child) {
		if (!child.region) {
			child.region = 'center';
		}
		this._contentContainer.addChild(child);
	},

	removeChild: function(child) {
		this._contentContainer.removeChild(child);
	},

	startup: function() {
		this.inherited(arguments);
		this._contentContainer.startup();
	},

	layout: function() {
		this.inherited(arguments);
		this._contentContainer.layout();
	},

	_setTitleAttr: function(newTitle) {
		this.title = newTitle;
		if (this._titlePane) {
			this._titlePane.set('content', '<div class="dijitTitlePaneTitleFocus">' + this.title + '</div>');
		}
	}
});


