/*
 * SPDX-FileCopyrightText: 2015-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/dom-class",
	"dojo/dom-construct",
	"umc/widgets/TextBox",
	"umc/widgets/Button"
], function(declare, lang, domClass, domConstruct, TextBox, Button) {
	return declare("umc.widgets.SearchBox", TextBox, {
		//// self
		onSearch: function() {
			// event stub
		},


		//// lifecycle
		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'umcSearchBox');

			// create search button
			var button = new Button({
				'class': 'ucsIconButton umcSearchBox__searchButton',
				iconClass: 'search',
				tabIndex: '-1',
				onClick: lang.hitch(this, function() {
					if (this.disabled) {
						return;
					}
					this.focus();
					this.onSearch();
				})
			});
			domConstruct.place(button.domNode, this.domNode, 'first');
		}
	});
});


