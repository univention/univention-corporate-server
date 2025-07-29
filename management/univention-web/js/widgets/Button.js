/*
 * SPDX-FileCopyrightText: 2011-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define,console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/dom-class",
	"dojo/dom-construct",
	"dijit/form/Button",
	"dijit/Tooltip",
	"./Icon",
	"put-selector/put"
], function(declare, lang, domClass, domConstruct, Button, Tooltip, Icon, put) {
	var Button = declare("umc.widgets.Button", [ Button ], {
		//// overwrites
		iconClass: '',
		_setIconClassAttr: function(iconClass) {
			if (iconClass) {
				if (this.iconNode) {
					Icon.setIconOfNode(this.iconNode, iconClass);
				} else {
					this.iconNode = Icon.createNode(iconClass);
					domConstruct.place(this.iconNode, this.titleNode, 'first');
				}
			} else {
				if (this.iconNode) {
					this.iconNode.remove();
					this.iconNode = null;
				}
			}
			this._set('iconClass', iconClass);
		},


		//// self
		// defaultButton: Boolean
		//		If set to 'true', button will be rendered as default, i.e., submit button.
		defaultButton: false,

		// callback: Function
		//		Convenience property for onClick callback handler.
		callback: null,

		visible: true,
		_setVisibleAttr: function(newVal) {
			this._set('visible', newVal);
			domClass.toggle(this.domNode, 'dijitDisplayNone', !newVal);
		},
		show: function() {
			this.set( 'visible', true );
		},
		hide: function() {
			this.set( 'visible', false );
		},

		handlesTooltips: true, // digested by widgets/LabelPane
		displayLabel: false, // digested by widgets/LabelPane - do not display button labels via the LabelPane

		description: '', // show 'description' in a dijit/Tooltip widget on hover
		_setDescriptionAttr: function(description) {
			if (!this._tooltip) {
				// create the tooltip for the first time
				this._tooltip = new Tooltip({
					label: description,
					connectId: [ this.domNode ]
				});
				this.own(this._tooltip);
			}
			this._tooltip.set('label', description || '');
			this._set('description', description);
		},
		_tooltip: null, // dijit/Tooltip widget for the 'description'


		//// lifecycle
		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'ucsButton');
			put(this.iconNode, '!');
			this.iconNode = null;
		},

		postCreate: function() {
			this.inherited(arguments);

			var addPrimaryClass = this.defaultButton
				&& !domClass.contains(this.domNode, 'ucsIconButton')
				&& !domClass.contains(this.domNode, 'ucsIconButtonHighlighted');
			if (addPrimaryClass) {
				domClass.remove(this.domNode, 'ucsNormalButton ucsTextButton');
				domClass.add(this.domNode, 'ucsPrimaryButton');
			}

			if (typeof this.callback === "function") {
				this.on('click', lang.hitch(this, 'callback'));
			}
		}
	});

	Button.simpleIconButtonNode = function(iconName, claz) {
		// performant rendering of a simple stateless IconButton
		var buttonNode = document.createElement('span');
		buttonNode.className = `ucsSimpleIconButton ${claz || ''}`;

		var svgNode = Icon.createNode(iconName);

		buttonNode.appendChild(svgNode);
		return buttonNode;
	};

	return Button;
});
