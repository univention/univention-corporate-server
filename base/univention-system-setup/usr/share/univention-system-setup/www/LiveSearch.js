/*
 * SPDX-FileCopyrightText: 2012-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define,require*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/event",
	"dojo/dom-construct",
	"dojo/dom-class",
	"dojo/on",
	"dojo/keys",
	"dojo/topic",
	"dojox/html/styles",
	"dijit/form/ComboBox",
	"umc/widgets/TextBox",
	"umc/widgets/Button",
	"umc/widgets/StandbyCircle",
	"umc/i18n!setup"
], function(declare, lang, dojoEvent, domConstruct, domClass, on, keys, topic, styles, DijitComboBox, TextBox, Button, StandbyCircle, _) {
	return declare('umc.modules.setup.LiveSearch', [DijitComboBox, TextBox], {
		searchAttr: 'label',
		hasDownArrow: false,
		autoComplete: false,
		highlightMatch: 'none',
		store: null,
		_currentNode: null,
		_searchNode: null,
		_searchingNode: null,
		inlineLabel: null,

		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'setupCitySearch');

			this._currentNode = this._buttonNode;

			this._searchNode = Button.simpleIconButtonNode('search', 'setupCitySearch__searchIcon');
			this.own(on(this._searchNode, 'click', lang.hitch(this, 'loadDropDown')));

			var standbyCircle = new StandbyCircle({
				'class': 'setupCitySearch__standbyCircle'
			});
			this.own(standbyCircle);
			this._searchingNode = standbyCircle.domNode;

			this._setState('search');
		},

		postCreate: function() {
			this.inherited(arguments);

			this.store.on('searching', lang.hitch(this, '_setState', 'searching'));
			this.store.on('searchFinished', lang.hitch(this, '_setState', 'search'));
		},

		_setState: function(state) {
			var newNode = this._currentNode;
			if (state === 'searching') {
				newNode = this._searchingNode;
			} else {
				newNode = this._searchNode;
			}
			domConstruct.place(newNode, this._currentNode, 'replace');
			this._currentNode = newNode;
		},

		loadDropDown: function() {
			this._startSearch(this.get('value'));
		},

		_autoSelect: function() {
			var lastResult = this.store.lastResult;
			if (this.state != 'searching' && lastResult.length && this._opened && !this.dropDown.selected) {
				// select first item
				this.set('item', lastResult[0]);
				this.closeDropDown();
				return true;
			}
			return false;
		},

		_onBlur: function(evt) {
			this._autoSelect();
			this.inherited(arguments);
		},

		_onKey: function(evt) {
			if (evt.keyCode == keys.ENTER) {
				var selected = this._autoSelect();
				if (selected || this.state == 'searching' || !this.get('item')) {
					// stop processing key event
					dojoEvent.stop(evt);
					return;
				}
			}
			if (evt.keyCode == keys.TAB) {
				// when pressing tab key, auto select the first entry from result list
				// and continue processing event
				this._autoSelect();
			}
			this.inherited(arguments);
		}
	});
});
