/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/on",
	"dojo/aspect",
	"dijit/Tooltip"
], function(declare, lang, on, aspect, Tooltip) {
	/*dojo.extend(dijit._MasterTooltip, {
		buildRendering: function() {
			if(!this.domNode){
				// Create root node if it wasn't created by _Templated
				this.domNode = this.srcNodeRef || domConstruct.create('div');
			}

			// hide the tooltip
			this.own(on(this.domNode, 'click', lang.hitch(this, 'hide')));
		}
	});*/

	// connect to the primary tooltip's domNode onlick event in order to
	// trigger the fade out animation.
	var hdl = aspect.after(Tooltip, 'show', function() {
		on(Tooltip._masterTT.domNode, 'click', lang.hitch(Tooltip._masterTT.fadeOut, 'play'));

		// disconnect from 'Tooltip.show', we only need to register the handler once
		hdl.remove();
	});

	Tooltip.defaultPosition = ['below', 'above', 'after', 'before'];

	return declare("umc.widgets.Tooltip", Tooltip, {});
});


