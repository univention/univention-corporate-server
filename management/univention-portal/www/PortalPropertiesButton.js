/*
 * Copyright 2020 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */
/*global define*/

/**
 * @module portal/PortalPropertiesButton
 */
define([
	"dojo/_base/declare",
	"dojo/_base/array",
	"dojo/_base/lang",
	"dojo/dom-class",
	"dojo/on",
	"dijit/popup",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"dijit/_WidgetsInTemplateMixin",
	"dijit/form/Button",
	"dijit/form/ToggleButton",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Form",
	"umc/render",
	"umc/tools",
	"put-selector/put",
	"./portalContent",
	"umc/i18n!portal",
], function(
	declare, array, lang, domClass, on, popup, _WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin, Button, ToggleButton,
	ContainerWidget, Form, render, tools, put, portalContent, _
) {
	var PortalPropertiesContainer = declare("PortalProperties", [_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {
		templateString: `
			<div class="portalProperties">
				<h1
					class="portalProperties__title"
					data-dojo-attach-point="titleNode"
				></h1>
				<div
					class="portalProperties__form"
					data-dojo-type="umc/widgets/ContainerWidget"
					data-dojo-attach-point="formNode"
				></div>
			</div>
		`,

		title: _('Settings'),
		_setTitleAttr: { node: 'titleNode', type: 'innerHTML' },

		open: false,
		_setOpenAttr: function(open) {
			domClass.toggle(this.domNode, 'portalProperties--open', open);
			this._set('open', open);
		},

		_moduleCache: null,
		_moduleStore: null,
		constructor: function() {
			// this._moduleCache = cache.get('portals/all');
			// this._moduleStore = store('$dn$', 'udm', 'portals/all');
		},

		postCreate: function() {
			this.inherited(arguments);

			var propNames = ['displayName'];
			this._moduleCache.getProperties('portals/portal', portalContent.portal().dn).then(lang.hitch(this, function(props) {
				props = array.filter(lang.clone(props), function(iprop) {
					return array.indexOf(propNames, iprop.id) >= 0;
				});
				var initialFormValues = {}; // set after form.load()

				render.requireWidgets(props).then(lang.hitch(this, function() {
					props = this._prepareProps(props); // do this after requireWidgets because requireWidgets changes the type of the prop

					var form = new Form({
						widgets: props,
						layout: propNames,
						moduleStore: this._moduleStore
					});

					put(this.formNode.domNode, form.domNode);
					form.startup();
				}));
			}));
		},

		// TODO copy pasted partially from udm/DetailPage - _prepareWidgets
		_prepareProps: function(props) {
			array.forEach(props, function(iprop) {
				if (iprop.type.indexOf('MultiObjectSelect') >= 0) {
					iprop.multivalue = false;
					iprop.umcpCommand = store('$dn$', 'udm', 'portals/all').umcpCommand;
				} else if (iprop.multivalue && iprop.type !== 'MultiInput') {
					iprop.subtypes = [{
						type: iprop.type,
						dynamicValues: iprop.dynamicValues,
						dynamicValuesInfo: iprop.dynamicValuesInfo,
						dynamicOptions: iprop.dynamicOptions,
						staticValues: iprop.staticValues,
						size: iprop.size,
						depends: iprop.depends
					}];
					iprop.type = 'MultiInput';
				}
			});
			return props;
		},
	});


	return declare("PortalPropertiesButton", [ToggleButton], {
		showLabel: false,
		iconClass: 'iconGear',

		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'ucsIconButton');
		},

		_setCheckedAttr: function(checked) {
			this.portalPropertiesContainer.set('open', checked);
			this.inherited(arguments);
		},

		postCreate: function() {
			this.inherited(arguments);

			this.portalPropertiesContainer = new PortalPropertiesContainer({
				_moduleCache: this._moduleCache,
				_moduleStore: this._moduleStore
			});
			document.body.appendChild(this.portalPropertiesContainer.domNode);
			this.portalPropertiesContainer.startup();
		}
	});
});




