/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define,console,require */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/window",
	"dojo/has",
	"dojo/Deferred",
	"dojo/dom-construct",
	"dijit/_WidgetBase",
	"umc/widgets/Standby"
], function(declare, lang, array, baseWindow, has, Deferred, construct, _WidgetBase, Standby) {
	return declare("umc.widgets.StandbyMixin", _WidgetBase, {
		// summary:
		//		Mixin class to make a widget "standby-able"

		standingBy: false,

		_standbyWidget: null,

		standbyOpacity: 0.8,

		standbyColor: 'var(--bgc-content-body)',

		_lastContent: null,

		_standbyStartedDeferred: null,

		postMixInProperties: function() {
			this.inherited(arguments);

			this._standbyStartedDeferred = new Deferred();
			this._standbyDuringID = 0;
			this._standbyDuringQueue = [];
		},

		buildRendering: function() {
			this.inherited(arguments);

			// create a standby widget targeted at this module
			this._standbyWidget = this.own(new Standby({
				centerIndicator: 'svg',
				target: this.domNode,
				duration: 200,
				opacity: this.standbyOpacity,
				color: this.standbyColor
			}))[0];
			this.domNode.appendChild(this._standbyWidget.domNode);
			this._standbyWidget.startup();
		},

		startup: function() {
			this.inherited(arguments);
			this._standbyStartedDeferred.resolve();
		},

		_cleanUp: function() {
			if (this._lastContent && this._lastContent.declaredClass && this._lastContent.domNode) {
				// we got a widget as last element, remove it from the DOM
				try {
					this._standbyWidget._textNode.removeChild(this._lastContent.domNode);
				}
				catch(e) {
					console.log('Could remove standby widget from DOM:', e);
				}
				this._lastContent = null;
			}
		},

		_updateContent: function(content, options) {
			options = options || {};
			// type check of the content
			if (typeof content === "string") {
				// string
				this._cleanUp();
				this._standbyWidget.set('text', content);
				this._standbyWidget.set('centerIndicator', 'text');
				this._standbyWidget.set('opacity', options.standbyOpacity || this.standbyOpacity);
			}
			else if (typeof content === "object" && content.declaredClass && content.domNode) {
				// widget
				if (!this._lastContent || this._lastContent != content) {
					// we only need to add a new widget to the DOM
					this._cleanUp();
					this._standbyWidget.set('text', '');
					this._standbyWidget.set('centerIndicator', 'text');
					this._standbyWidget.set('opacity', options.standbyOpacity || this.standbyOpacity);

					// hook the given widget to the text node
					construct.place(content.domNode, this._standbyWidget._textNode);
					content.startup();
				}
			}
			else {
				// set default image
				this._cleanUp();
				this._standbyWidget.set('centerIndicator', 'svg');
				this._standbyWidget.set('opacity', options.standbyOpacity || this.standbyOpacity);
			}

			// cache the widget
			this._lastContent = content;
		},

		standby: function(/*Boolean*/ doStandby, /*mixed?*/ content, /*object?*/options) {
			if (doStandby) {
				this.set('standingBy', true);
			}
			this._standbyStartedDeferred.then(lang.hitch(this, function() {
				if (doStandby) {
					// update the content of the standby widget
					this._updateContent(content, options);

					// place the standby widget last in the body
					// to ensure correct z-indexing
					construct.place(this._standbyWidget.domNode, baseWindow.body(), 'last');

					// show standby widget
					this._standbyWidget.show();
					this.set('standingBy', doStandby);
				} else {
					// hide standby widget
					this._standbyWidget.hide();
					this.set('standingBy', doStandby);
				}
			}));
		},

		standbyDuring: function(deferred, content, options) {
			if (options && options.delay) { // FIXME: remove me one day... replace with something better
				setTimeout(lang.hitch(this, function() {
					this.standbyDuring(deferred, content);
				}), options.delay);
				return;
			}
			if (!deferred.isFulfilled()) {
				// don't standby if already finished
				var id = this._standbyDuringID += 1;
				var thisEntry = [id, content];
				this._standbyDuringQueue.push(thisEntry);
				this.standby(true, content, options);
				var finish = lang.hitch(this, function() {
					this._standbyDuringQueue = array.filter(this._standbyDuringQueue, function(entry) {
						return id !== entry[0];
					});
					if (this._standbyDuringQueue.length) {
						var oldContent = this._standbyDuringQueue[this._standbyDuringQueue.length - 1][1];
						this.standby(true, oldContent, options);
					} else {
						this.standby(false);
					}
				});
				deferred.then(finish, finish);
			}
			return deferred;
		}
	});
});
