/*
 * Copyright 2011 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
 */
/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.LabelPane");

dojo.require("dijit._Widget");
dojo.require("dijit._Templated");
dojo.require("dijit._Container");

dojo.declare("umc.widgets.LabelPane", [ dijit._Widget, dijit._Templated, dijit._Container ], {
	// summary:
	//		Simple widget that displays a widget/HTML code with a label above.

	// don't use float, use display:inline-block; we need a hack for IE7 here, see:
	//   http://robertnyman.com/2010/02/24/css-display-inline-block-why-it-rocks-and-why-it-sucks/
	templateString: '<div style="display:inline-block;vertical-align:top;zoom:1;*display:inline;" class="umcLabelPane">' +
		'<div class="umcLabelPaneLabelNode umcLabelPaneLabeNodeTop" style="display:block;"><label dojoAttachPoint="labelNodeTop" for=""></label></div>' +
		'<span dojoAttachPoint="containerNode,contentNode" style=""></span>' +
		'<span class="umcLabelPaneLabelNode umcLabelPaneLabeNodeRight" style=""><label dojoAttachPoint="labelNodeRight" for=""></label></span>' +
		'</div>',

	// content: String|dijit._Widget
	//		String which contains the text (or HTML code) to be rendered or
	//		a dijit._Widget instance.
	content: '',

	// disabled: Boolean
	//		if the content of the label pane should be disabled. the content widgets must support it
	disabled: false,

	// the widget's class name as CSS class
	'class': 'umcLabelPane',

	// label: String
	label: null,

	labelNodeTop: null,

	labelNodeRight: null,

	postMixInProperties: function() {
		this.inherited(arguments);

		// if we have a widget as content and label is not specified, use the widget's
		// label attribute
		if (null === this.label) {
			this.label = this.content.label || '';
		}
		// register watch handler for label and visibility changes
		if (dojo.getObject('content.watch', false, this)) {
			if (!umc.tools.inheritsFrom(this.content, 'umc.widgets.Button')) {
				// only watch the label and required property if widget is not a button
				this.content.watch('label', dojo.hitch(this, function(attr, oldVal, newVal) {
					this.set('label', newVal || '');
				}));
				this.content.watch('required', dojo.hitch(this, function(attr, oldVal, newVal) {
					this.set('label', this.content.get('label') || '');
				}));
			}
			this.content.watch('visible', dojo.hitch(this, function(attr, oldVal, newVal) {
				dojo.toggleClass(this.domNode, 'dijitHidden', !newVal);
			}));
		}
		else if (!dojo.isString(this.label)) {
			this.label = '';
		}
	},

	buildRendering: function() {
		this.inherited(arguments);

		dojo.toggleClass(this.domNode, 'dijitHidden', this.content.visible === false);
	}, 

	_setLabelAttr: function(label) {
		if (dojo.getObject('content.isLabelDisplayed', false, this)) {
			// the widget displays the label itself
			return;
		}

		// if we have a widget which is required, add the string ' (*)' to the label
		if (dojo.getObject('domNode', false, this.content) &&
				dojo.getObject('declaredClass', false, this.content) &&
				dojo.getObject('required', false, this.content)) {
			label = label + ' (*)';
		}
		this.label = label;

		// set the labels' 'for' attribute
		if (dojo.getObject('id', false, this.content) && dojo.getObject('declaredClass', false, this.content)) {
			dojo.attr(this.labelNodeRight, 'for', this.content.id);
			dojo.attr(this.labelNodeTop, 'for', this.content.id);
		}

		// only for check boxes, place the label right of the widget
		if (umc.tools.inheritsFrom(this.content, 'dijit.form.CheckBox')) {
			dojo.attr(this.labelNodeRight, 'innerHTML', label);
			if (label) {
				dojo.attr(this.labelNodeTop, 'innerHTML', '');
				dojo.addClass(this.domNode, 'umcLabelPaneCheckBox');
			}
		}
		else {
			dojo.attr(this.labelNodeTop, 'innerHTML', label);
		}
	},

	_setContentAttr: function(content) {
		this.content = content;

		// we have a string
		if (dojo.isString(content)) {
			this.contentNode.innerHTML = content;
		}
		// if we have a widget, clear the content and hook in the domNode directly
		else if (dojo.getObject('domNode', false, content) && dojo.getObject('declaredClass', false, content)) {
			this.contentNode.innerHTML = '';
			this.addChild(content);
		}
		this.set( 'disabled', this.disabled );
	},

	_setDisabledAttr: function( value ) {
		if ( this.content ) {
			this.content.set( 'disabled', value );
		}
	}
});

dojo.extend(dijit._Widget, {
    // isLabelDisplayed: Boolean?
    //		If specified as true, LabelPane assumes that the widget itself will take
	//		care of displaying the label correctly.
	//		This property is specified by `umc.widgets.LabelPane`.
    isLabelDisplayed: false,

	// visible: Boolean?
	//		If set to false, the label and widget will be hidden.
	visible: true
});
