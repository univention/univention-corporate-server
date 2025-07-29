/*
 * SPDX-FileCopyrightText: 2020-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom-class",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"dijit/_WidgetsInTemplateMixin",
	"umc/i18n!umc/modules/appcenter",
	"umc/modules/appcenter/Tile",
	"umc/widgets/Button"
], function(declare, lang, array, domClass, _WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin, _) {
	return declare("umc.modules.appcenter.AppInfo", [_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {
		baseClass: 'umcAppInfo',
		templateString: `
			<div class="appDetailsSidebarElement">
				<div
					data-dojo-type="umc/modules/appcenter/Tile"
					data-dojo-props="
						bgc: this.bgc,
						logo: this.logo,
						name: this.name
					"
				></div>
				<div class="umcAppInfo__description">\${description}</div>
				<div class="umcAppInfo__buttonWrapper" data-dojo-attach-point="buttonNode">
					<div class="umcAppSidebarButton ucsPrimaryButton"
						data-dojo-type="umc/widgets/Button"
						data-dojo-attach-event="click:_onClick"
						data-dojo-props="
							name: 'installations',
							label: this.buttonLabel
						"
					>
					</div>
				</div>
			</div>
		`,
		buildRendering: function() {
			this.inherited(arguments);
			if (! this.buttonLabel) {
				domClass.add(this.buttonNode, 'dijitDisplayNone');
			}
		},
		_onClick: function() {
			this.callback();
		}
	});
});
