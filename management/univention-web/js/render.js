/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2011-2022 Univention GmbH
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
/*global define,require*/

define([
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom-class",
	"dojo/Deferred",
	"dojo/promise/all",
	"dojox/html/entities",
	"umc/tools",
	"umc/widgets/ContainerWidget",
	"umc/widgets/LabelPane",
	"umc/widgets/TitlePane",
	"umc/widgets/Tooltip",
	"umc/widgets/HiddenInput",
	"umc/widgets/CheckBox",
	"umc/widgets/Button",
	"umc/widgets/SubmitButton",
	"umc/widgets/ResetButton",
	"umc/widgets/Text"
], function(lang, array, domClass, Deferred, all, entities, tools, ContainerWidget, LabelPane, TitlePane, Tooltip, HiddenInput, CheckBox, Button, SubmitButton, ResetButton, Text) {
	var render = {};
	lang.mixin(render, {
		requireWidgets: function(/*Object[]*/ widgetConfs) {
			// summary:
			//		loads the widget modules necessary to render the widgets described in widgetConfs
			// returns:
			//		dojo/promise/Promise
			var widgetTypes = [];
			widgetConfs.forEach(function(widgetConf) {
				widgetTypes.push(widgetConf.type);
				if (widgetConf.type === 'MultiInput') {
					widgetTypes = widgetTypes.concat(widgetConf.subtypes.map(function(subtype) {
						return subtype.type;
					}));
				}
			});

			var deferreds = [];
			widgetTypes.forEach(function(type) {
				if (typeof type !== 'string') { // this shouldn't be necessary
					return;
				}

				var path = type.indexOf('/') >= 0 ? type : 'umc/widgets/' + type;
				var errHandler;
				var deferred = new Deferred();
				var loaded = function() {
					deferred.resolve();
					errHandler.remove();
				};
				errHandler = require.on('error', loaded);
				require([path], loaded);
				deferreds.push(deferred);
			});
			return all(deferreds);
		},

		widgets: function(/*Object[]*/ widgetsConf, owner) {
			// summary:
			//		Renders an array of widget config objects.
			// returns:
			//		A dictionary of widget objects.

			// iterate over all widget config objects
			var widgets = { };
			array.forEach(widgetsConf, function(iconf) {
				// ignore empty elements
				if (!iconf || typeof iconf != "object") {
					return;
				}

				// copy the property 'id' to 'name'
				var conf = lang.mixin({}, iconf);
				conf.name = iconf.id || iconf.name;

				// render the widget
				var widget = this.widget(conf, widgets);
				if (widget) {
					if (owner) {
						owner.own(widget);
					}
					widgets[conf.name] = widget;
				}
			}, this);

			return widgets; // Object
		},

		widget: function(/*Object*/ widgetConf, /*Object[]*/ widgets) {
			if (!widgetConf) {
				return undefined;
			}
			if (!widgetConf.type) {
				console.log(lang.replace("WARNING in render.widget: The type '{type}' of the widget '{name}' is invalid. Ignoring error.", widgetConf));
				return undefined;
			}

			// make a copy of the widget's config object and remove 'type'
			var conf = lang.mixin({}, widgetConf);
			delete conf.type;

			// remove property 'id'
			delete conf.id;

			// register onChange event handler
			var onChangeCallback = null;
			if ('onChange' in conf) {
				onChangeCallback = tools.stringOrFunction(conf.onChange);
				delete conf.onChange;
			}

			// get widgets' size class
			if (conf.size) {
				conf.sizeClass = conf.size;
				delete conf.size;
			}

			var WidgetClass;
			if (widgetConf.type && typeof widgetConf.type != 'string') {
				// assume that we got the class directly
				WidgetClass = widgetConf.type;
			}
			else if (typeof widgetConf.type == 'string') {
				try {
					// include the corresponding module for the widget
					var path = widgetConf.type;
					if (path.indexOf('/') < 0) {
						// the name does not contain a slash, thus we need to add 'umc/widgets.' as path prefix
						path = 'umc/widgets/' + path;
					}
					WidgetClass = require(path);
				}
				catch (err) { }
			}
			if (!WidgetClass || WidgetClass === 'not-a-module') {
				console.log(lang.replace("WARNING in render.widget: The widget class '{type}' defined by widget '{name}' cannot be found. Ignoring error.", widgetConf));
				return undefined;
			}
			var widget = new WidgetClass(conf); // Widget
			if (widget) {
				if ('syntax' in conf && typeof conf.syntax === 'string') {
					domClass.add(widget.domNode, 'syntax' + conf.syntax);
				}
			}

			// register event handler
			if (onChangeCallback) {
				widget.own(widget.watch('value', function(attr, oldVal, newVal) {
					// hand over the changed value plus the dict of all widgets
					onChangeCallback(newVal, widgets);
				}));
			}

			return widget; // dijit._WidgetBase
		},

		buttons: function(/*Object[]*/ buttonsConf, owner) {
			// summary:
			//		Renders an array of button config objects.
			// returns:
			//		A dictionary of button widgets.

			tools.assert(buttonsConf instanceof Array, 'buttons: The list of buttons is expected to be an array.');

			// render all buttons
			var buttons = {
				$order$: [] // internal field to store the correct order of the buttons
			};
			array.forEach(buttonsConf, function(i) {
				var btn = this.button(i);
				if (owner) {
					owner.own(btn);
				}
				buttons[i.name] = btn;
				buttons.$order$.push(btn);
			}, this);

			// return buttons
			return buttons; // Object
		},

		button: function(/*Object*/ _buttonConf) {
			// make a local copy of the config object
			var buttonConf = lang.mixin({}, _buttonConf);

			// specific button types need special care: submit, reset
			var ButtonClass = Button;
			if ('submit' == buttonConf.name) {
				ButtonClass = SubmitButton;
			}
			if ('reset' == buttonConf.name) {
				ButtonClass = ResetButton;
			}

			// get icon and label (these properties may be functions)
			if (buttonConf.iconClass) {
				buttonConf.iconClass = typeof buttonConf.iconClass === "function"
					? buttonConf.iconClass()
					: buttonConf.iconClass;
			}
			if (buttonConf.label) {
				buttonConf.label = typeof buttonConf.label === "function"
					? buttonConf.label()
					: buttonConf.label;
			}

			// render the button
			var button = new ButtonClass(buttonConf);

			// done, return the button
			return button; // umc.widgets.Button
		},

		layout: function(/*Array*/ layout, /*Object*/ widgets, /*Object?*/ buttons, /*Integer?*/ _iLevel, /*ContainerWidget?*/ container) {
			// summary:
			//		Render a widget containing a set of widgets as specified by the layout.

			var iLevel = 'number' == typeof(_iLevel) ? _iLevel : 0;

			// create a container
			var globalContainer = container || new ContainerWidget({
				'class': 'umcLayoutContainer'
			});

			// check whether the parameters are correct
			tools.assert(layout instanceof Array,
					'render.layout: Invalid layout configuration object!');

			// iterate through the layout elements
			for (var iel = 0; iel < layout.length; ++iel) {

				// element can be:
				//   String -> reference to widget
				//   Array  -> references to widgets
				//   Object -> grouped widgets -> recursive call of layout()
				//
				//   Object -> in form of { 'layoutRowClass': 'myclass', 'layout': layout }
				//             where 'layout' is one of the above. The 'layoutRowClass' will be added to the
				//             'umcLayoutRow' ContainerWidget in the form of 'umcLayoutRow--myclass'
				var el = layout[iel];
				var elList = null;
				var layoutRowClass = '';
				if (typeof el === 'object' && el.layoutRowClass) {
					layoutRowClass = el.layoutRowClass;
					el = el.layout;
				}

				if (typeof el == "string") {
					elList = [el];
					layout[iel] = elList;
				}
				else if (el instanceof Array) {
					elList = el;
				}

				var betweenNonCheckBoxes = array.some(elList, function(el) {
					var widget = widgets[el];
					var button = buttons && buttons[el];
					return button || (widget && !widget.isInstanceOf(CheckBox));
				});
				// for single String / Array
				if (elList) {
					// add current form widgets to layout
					var elContainer = new ContainerWidget({
						'class': 'umcLayoutRow'
					});
					if (layoutRowClass) {
						domClass.add(elContainer.domNode, `umcLayoutRow--${layoutRowClass}`);
					}
					var label = null;
					array.forEach(elList, function(jel) {
						// make sure the reference to the widget/button exists
						if (!(widgets && jel in widgets) && !(buttons && jel in buttons)) {
							console.log(lang.replace("WARNING in render.layout: The widget '{0}' is not defined in the argument 'widgets'. Ignoring error.", [jel]));
							return;
						}

						// make sure the widget/button has not been already rendered
						var widget = widgets ? widgets[jel] : null;
						var button = buttons ? buttons[jel] : null;
						if ((widget && widget.$isRendered$) || (button && button.$isRendered$)) {
							console.log(lang.replace("WARNING in render.layout: The widget '{0}' has been referenced more than once in the layout. Ignoring error.", [jel]));
							return;
						}

						if (widget && widget.isInstanceOf(HiddenInput)) {
							// do wrap HiddenInput field with LabelPane
							elContainer.addChild(widget);
							widget.$isRendered$ = true;
						}
						else if (widget) {
							// add the widget or button surrounded with a LabelPane
							label = new LabelPane({
								label: widget.label,
								betweenNonCheckBoxes: betweenNonCheckBoxes,
								content: widget,
								style: (widget.align ? 'float: ' + widget.align +';' : '' ) + (widget.style || '')
							});
							widget.$refLabel$ = label;

							// add to layout
							elContainer.addChild( label );
							widget.$isRendered$ = true;
						} else if (button) {
							label = new LabelPane({
								label: '&nbsp;',
								content: button,
								style: button.align ? 'float: ' + button.align : ''
							});
							button.$refLabel$ = label;
							button.$isRendered$ = true;
							elContainer.addChild(label);
						}
					}, this);
					globalContainer.addChild(elContainer);
				}
				// for Object (i.e., a grouping box)
				else if (typeof el == "object" && el.layout) {
					el.$refTitlePane$ = new TitlePane({
						title: el.label,
						'class': 'umcFormLevel' + iLevel + (el.class ? (' ' + el.class) : ''),
						toggleable: el.toggleable === undefined ? (iLevel < 1) : el.toggleable,
						open: undefined === el.open ? true : el.open,
						content: this.layout(el.layout, widgets, buttons, iLevel + 1)
					});
					if (el.description) {
						el.$refTitlePane$.addChild(new Text({content: entities.decode(el.description), style: 'margin-bottom: 1em;'}), 0);
					}
					globalContainer.addChild( el.$refTitlePane$ );
				}
			}

			// add buttons if specified and if they have not been added in the layout already
			if (buttons && 0 === iLevel) {
				// add all buttons that have not been rendered so far to a separate container
				// and respect their correct order (i.e., using the internal array field $order$)

				var buttonContainer = null;
				var buttonContainerLeft = null;
				var buttonContainerRight = null;
				var createButtonContainer = function() {
					if (buttonContainer !== null) {
						return;
					}

					buttonContainer = new ContainerWidget({
						'class': 'umcLayoutRow umcLayoutRow--buttons'
					});
					buttonContainerLeft = new ContainerWidget({
						'class': 'umcLayoutRow--buttonsleft'
					});
					buttonContainerRight = new ContainerWidget({
						'class': 'umcLayoutRow--buttonsright'
					});
					buttonContainer.addChild(buttonContainerLeft);
					buttonContainer.addChild(buttonContainerRight);
				};

				var buttonsAdded = false;
				array.forEach(buttons.$order$, function(ibutton) {
					if (!ibutton.$isRendered$) {
						createButtonContainer();
						if (ibutton.align === 'left') {
							buttonContainerLeft.addChild(ibutton);
						} else {
							buttonContainerRight.addChild(ibutton);
						}
						ibutton.$isRendered$ = true;
						buttonsAdded = true;
					}
				});
				if (buttonsAdded) {
					tools.toggleVisibility(buttonContainerLeft, buttonContainerLeft.hasChildren());
					tools.toggleVisibility(buttonContainerRight, buttonContainerRight.hasChildren());
					globalContainer.addChild(buttonContainer);
				}
			}

			// return the container
			return globalContainer;
		}
	});

	return render;
});
