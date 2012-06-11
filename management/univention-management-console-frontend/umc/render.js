/*
 * Copyright 2011-2012 Univention GmbH
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
/*global dojo dijit dojox umc console window */

dojo.provide("umc.render");

dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.LabelPane");
dojo.require("umc.widgets.TitlePane");
dojo.require("umc.widgets.Tooltip");

dojo.mixin(umc.render, new umc.i18n.Mixin({
	// use the framework wide translation file
	i18nClass: 'umc.app'
}), {
	widgets: function(/*Object[]*/ widgetsConf) {
		// summary:
		//		Renders an array of widget config objects.
		// returns:
		//		A dictionary of widget objects.

		// iterate over all widget config objects
		var widgets = { };
		dojo.forEach(widgetsConf, function(iconf) {
			// ignore empty elements
			if (!iconf || !dojo.isObject(iconf)) {
				return true;
			}

			// copy the property 'id' to 'name'
			var conf = dojo.mixin({}, iconf);
			conf.name = iconf.id || iconf.name;

			// render the widget
			var widget = this.widget(conf, widgets);
			if (widget) {
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
			console.log(dojo.replace("WARNING in umc.render.widget: The type '{type}' of the widget '{name}' is invalid. Ignoring error.", widgetConf));
			return undefined;
		}

		// make a copy of the widget's config object and remove 'type'
		var conf = dojo.mixin({}, widgetConf);
		delete conf.type;

		// remove property 'id'
		delete conf.id;

		// register onChange event handler
		var onChangeCallback = null;
		if ('onChange' in conf) {
			onChangeCallback = umc.tools.stringOrFunction(conf.onChange);
			delete conf.onChange;
		}

		// get widgets' size class
		if (conf.size) {
			conf.sizeClass = conf.size;
			delete conf.size;
		}

		var WidgetClass = undefined;
		var path;
		try {
			// include the corresponding module for the widget
			path = widgetConf.type;
			if (path.indexOf('.') < 0) {
				// the name does not contain a dot, thus we need to add 'umc.widgets.' as path prefix
				path = 'umc.widgets.' + path;
			}
			dojo['require'](path);

			// create the new widget according to its type
			WidgetClass = dojo.getObject(path);
		}
		catch (error) { }
		if (!WidgetClass) {
			console.log(dojo.replace("WARNING in umc.render.widget: The widget class 'umc.widgets.{type}' defined by widget '{name}' cannot be found. Ignoring error.", widgetConf));
			return undefined;
		}
		var widget = new WidgetClass(conf); // Widget

		// register event handler
		if (onChangeCallback) {
			widget.connect(widget, 'onChange', function(newVal) {
				// hand over the changed value plus the dict of all widgets
				onChangeCallback(newVal, widgets);
			});
		}

		// create a tooltip if there is a description
		if (widgetConf.description) {
			var tooltip = new umc.widgets.Tooltip({
				label: widgetConf.description,
				connectId: [ widget.domNode ]
			});

			// destroy the tooltip when the widget is destroyed
			tooltip.connect(widget, 'destroy', 'destroy');
		}

		return widget; // dijit._Widget
	},

	buttons: function(/*Object[]*/ buttonsConf) {
		// summary:
		//		Renders an array of button config objects.
		// returns:
		//		A dictionary of button widgets.

		umc.tools.assert(dojo.isArray(buttonsConf), 'buttons: The list of buttons is expected to be an array.');

		// render all buttons
		var buttons = {
			$order$: [] // internal field to store the correct order of the buttons
		};
		dojo.forEach(buttonsConf, function(i) {
			var btn = this.button(i);
			buttons[i.name] = btn;
			buttons.$order$.push(btn);
		}, this);

		// return buttons
		return buttons; // Object
	},

	button: function(/*Object*/ _buttonConf) {
		// make a local copy of the config object
		var buttonConf = dojo.mixin({}, _buttonConf);

		// specific button types need special care: submit, reset
		var buttonClassName = 'Button';
		if ('submit' == buttonConf.name) {
			buttonClassName = 'SubmitButton';
		}
		if ('reset' == buttonConf.name) {
			buttonClassName = 'ResetButton';
		}

		// load the java script code for the button class
		dojo['require']('umc.widgets.' + buttonClassName);
		var ButtonClass = dojo.getObject('umc.widgets.' + buttonClassName);

		// get icon and label (these properties may be functions)
		var iiconClass = buttonConf.iconClass;
		var ilabel = buttonConf.label;
		buttonConf.iconClass = dojo.isFunction(iiconClass) ? iiconClass() : iiconClass;
		buttonConf.label = dojo.isFunction(ilabel) ? ilabel() : ilabel;

		// render the button
		var button = new ButtonClass(buttonConf);

		// done, return the button
		return button; // umc.widgets.Button
	},

	layout: function(/*Array*/ layout, /*Object*/ widgets, /*Object?*/ buttons, /*Integer?*/ _iLevel) {
		// summary:
		//		Render a widget containing a set of widgets as specified by the layout.

		var iLevel = 'number' == typeof(_iLevel) ? _iLevel : 0;

		// create a container
		var globalContainer = new umc.widgets.ContainerWidget({});

		// check whether the parameters are correct
		umc.tools.assert(dojo.isArray(layout),
				'umc.render.layout: Invalid layout configuration object!');

		// iterate through the layout elements
		for (var iel = 0; iel < layout.length; ++iel) {

			// element can be:
			//   String -> reference to widget
			//   Array  -> references to widgets
			//   Object -> grouped widgets -> recursive call of layout()
			var el = layout[iel];
			var elList = null;
			if (dojo.isString(el)) {
				elList = [el];
				layout[iel] = elList;
			}
			else if (dojo.isArray(el)) {
				elList = el;
			}

			// for single String / Array
			if (elList) {
				// see how many buttons and how many widgets there are in this row
				var nWidgetsWithLabel = 0;
				dojo.forEach(elList, function(jel) {
					nWidgetsWithLabel += jel in widgets && (widgets[jel].label ? 1 : 0);
				});

				// add current form widgets to layout
				var elContainer = new umc.widgets.ContainerWidget({});
				var label = null;
				dojo.forEach(elList, function(jel) {
					// make sure the reference to the widget/button exists
					if (!(widgets && jel in widgets) && !(buttons && jel in buttons)) {
						console.log(dojo.replace("WARNING in umc.render.layout: The widget '{0}' is not defined in the argument 'widgets'. Ignoring error.", [jel]));
						return true;
					}

					// make sure the widget/button has not been already rendered
					var widget = widgets ? widgets[jel] : null;
					var button = buttons ? buttons[jel] : null;
					if ((widget && widget.$isRendered$) || (button && button.$isRendered$)) {
						console.log(dojo.replace("WARNING in umc.render.layout: The widget '{0}' has been referenced more than once in the layout. Ignoring error.", [jel]));
						return true;
					}

					if (widget && umc.tools.inheritsFrom(widget, 'umc.widgets.HiddenInput')) {
						// do wrap HiddenInput field with LabelPane
						elContainer.addChild(widget);
						widget.$isRendered$ = true;
					}
					else if (widget) {
						// add show and hide function to widget
						dojo.mixin( widget, {
							show: function() {
								this.set( 'visible', true );
							},
							hide: function() {
								this.set( 'visible', false );
							}
						} );

						// add the widget or button surrounded with a LabelPane
						label = new umc.widgets.LabelPane({
							label: widget.label,
							content: widget,
							disabled: widget.disabled,
							style: (widget.align ? 'float: ' + widget.align +';' : '' ) + (widget.style || '')
						});
						widget.$refLabel$ = label;

						// add to layout
						elContainer.addChild( label );
						widget.$isRendered$ = true;
					} else if (button) {
						if (nWidgetsWithLabel) {
							// add show and hide function to widget
							dojo.mixin( button, {
								show: function() {
									this.set( 'visible', true );
								},
								hide: function() {
									this.set( 'visible', false );
								}
							} );

							// if buttons are displayed along with widgets, we need to add a '&nbps;'
							// as label in order to display them on the same height
							label = new umc.widgets.LabelPane({
								label: '&nbsp;',
								content: button,
								disabled: button.disabled,
								style: button.align ? 'float: ' + button.align : ''
							});
							button.$refLabel$ = label;
							elContainer.addChild(label);
						} else {
							// if there are only buttons in the row, we do not need a label
							if (button.align) {
								button.set('style', 'float: ' + button.align);
							}
							// but then we should have show/hide methods to be consistent
							dojo.mixin( button, {
								show: function() {
									this.set( 'visible', true );
								},
								hide: function() {
									this.set( 'visible', false );
								},
								_setVisibleAttr: function(newVal) {
									this.visible = newVal;
									dojo.toggleClass(this.domNode, 'dijitHidden', !newVal);
								}
							} );
							button._setVisibleAttr(button.visible); // make sure that the button is set correctly
							elContainer.addChild(button);
						}
						button.$isRendered$ = true;
					}
				}, this);
				globalContainer.addChild(elContainer);
			}
			// for Object (i.e., a grouping box)
			else if (dojo.isObject(el) && el.layout) {
				el.$refTitlePane$ = new umc.widgets.TitlePane({
					title: el.label,
					'class': 'umcFormLevel' + iLevel,
					toggleable: iLevel < 1,
					open: undefined === el.open ? true : el.open,
					content: this.layout(el.layout, widgets, buttons, iLevel + 1)
				});
				globalContainer.addChild( el.$refTitlePane$ );
			}
		}

		// add buttons if specified and if they have not been added in the layout already
		if (buttons && 0 === iLevel) {
			// add all buttons that have not been rendered so far to a separate container
			// and respect their correct order (i.e., using the interal array field $order$)
			var buttonContainer = new umc.widgets.ContainerWidget({});
			dojo.forEach(buttons.$order$, function(ibutton) {
				if (!ibutton.$isRendered$) {
					buttonContainer.addChild(ibutton);
					ibutton.$isRendered$ = true;
				}
			});
			globalContainer.addChild(buttonContainer);
		}

		// start processing the layout information
		globalContainer.startup();

		// return the container
		return globalContainer; // dojox.layout.TableContainer
	}
});

