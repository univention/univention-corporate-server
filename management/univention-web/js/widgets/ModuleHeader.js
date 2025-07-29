/*
 * SPDX-FileCopyrightText: 2014-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/dom-class",
	"dojo/dom-style",
	"put-selector/put",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Text",
	"umc/tools",
	"umc/i18n!"
], function(declare, domClass, domStyle, put, ContainerWidget, Text, tools, _) {
	return declare('umc.widgets.ModuleHeader', [ContainerWidget], {
		baseClass: 'umcModuleHeader',

		icon: '',
		iconBackgroundColor: '',
		isModuleTabSelected: false,

		_outerContainer: null, // ContainerWidget
		_right: null, // ContainerWidget
		_left: null, // ContainerWidget

		_title: null, // Text
		title: '',
		_setTitleAttr: function(title) {
			this._title.set('content', title);
			this._set('title', title);
		},

		_subTitle: null, // Text
		subTitle: '',
		_setSubTitleAttr: function(subTitle) {
			tools.toggleVisibility(this._subTitle, !!subTitle);
			this._subTitle.set('content', subTitle);
			domClass.toggle(this.domNode, this.baseClass + '--withSubTitle', !!subTitle);
			this._set('subTitle', subTitle);
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._outerContainer = new ContainerWidget({
				baseClass: 'umcModuleHeaderOuterContainer'
			});
			var container = new ContainerWidget({
				baseClass: 'umcModuleHeaderWrapper container'
			});
			this._left = new ContainerWidget({
				baseClass: 'umcModuleHeaderLeft'
			});
			this._right = new ContainerWidget({
				baseClass: 'umcModuleHeaderRight'
			});
			var titleWrapper = new ContainerWidget({
				baseClass: 'umcModuleTitleWrapper'
			});
			var logoWrapper = new ContainerWidget({
				baseClass: 'umcModuleLogoWrapper'
			});
			domStyle.set(logoWrapper.domNode, "background-color", this.iconBackgroundColor);
			var logo = new ContainerWidget({
				'class': tools.getIconClass(this.icon, 'scalable'),
				baseClass: 'umcModuleLogo'
			});
			domStyle.set(logo.domNode, "background-size", "contain");
			if (this.icon && this.icon.startsWith('apps-')) {
				domStyle.set(logoWrapper.domNode, "background-color", "var(--bgc-apptile-default)");
				domStyle.set(logo.domNode, {
					"background-position": "center",
					"background-size": "80%",
				});
			}
			this._title = new Text({
				content: this.get('title'),
				baseClass: 'umcModuleTitle'
			});
			this._subTitle = new Text({
				content: this.get('subTitle'),
				baseClass: 'umcModuleSubTitle',
				'class': 'dijitDisplayNone'
			});

			this.addChild(this._outerContainer);
			this._outerContainer.addChild(container);
			container.addChild(this._left);
			container.addChild(this._right);
			this._left.addChild(titleWrapper);
			titleWrapper.addChild(logoWrapper);
			logoWrapper.addChild(logo);
			titleWrapper.addChild(this._title);
			this._left.addChild(this._subTitle);
		}
	});
});
