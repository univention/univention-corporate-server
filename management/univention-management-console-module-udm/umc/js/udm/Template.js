/*
 * Copyright 2011-2019 Univention GmbH
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
/*global define,console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/promise/all",
	"umc/tools",
	"umc/widgets/CheckBox"
], function(declare, lang, array, all, tools, CheckBox) {

	return declare('umc.modules.udm.Template', null, {
		// summary:
		//		Class that provides a template functionality for LDAP objects.
		// description:
		//		This class registers event handlers and monitors user input in order to
		//		update LDAP object values for a specified template. Template values may
		//		be static values (i.e., strings) or values containing references to other
		//		form fields. References are indicated by using tags '<variable>'.
		//		Additionally, modifiers can be applied to the content of a variable (e.g.,
		//		to convert values to upper or lower case) and an index operator enables
		//		accessing particular character ranges. Global functions in the form of
		//		'<:command>' are applied in the order they appear. Their position in the
		//		string does not matter.
		// example:
		//		Here some valid examples for variable expansion.
		//	|	simple:
		//	|	  <var>  -> 'Univention'
		//	|	  <var2> -> 'Süß'
		//	|	  <var3> -> '  Foo bar  '
		//	|	with modifiers:
		//	|	  <var:lower>          -> 'univention'
		//	|	  <var:upper>          -> 'UNIVENTION'
		//	|	  <var:umlauts,upper>  -> 'UNIVENTION'
		//	|	  <var2:umlauts>       -> 'Suess'
		//	|	  <var2:umlauts,upper> -> 'SUESS'
		//	|	  <var2:upper,umlauts> -> 'SUEss'
		//	|	with index operator:
		//	|	  <var>[0]   -> 'U'
		//	|	  <var>[-2]  -> 'o'
		//	|	  <var>[0:2] -> 'Un'
		//	|	  <var>[1:]  -> 'nivention'
		//	|	  <var>[:3]  -> 'Uni'
		//	|	  <var>[:-3] -> 'Univent'
		//	|	with trim:
		//	|	  <var3:trim>    -> 'Foo bar'
		//	|	global functions:
		//	|	  <var3> <:trim> -> 'Foo bar'
		//

		// widgets: Object
		//		Dict of (key -> widget) pairs containing all form widgets of
		//		the edited object.
		widgets: null,

		// template: Object
		//		Dict of (key -> value) pairs specifying template values for each UDM
		//		property.
		template: null,

		whitelist: null,

		_inverseReferences: null,

		_userChanges: null,

		_focusedWidget: '',

		_lastValues: null,

		// mappings to convert umlauts  and special basic latin letters to standard ones
		// basic latin letters with no real equivalent
		// 'Ð' U+00D0 - LATIN CAPITIAL LETTER ETH
		// 'Þ' U+00DE - LATIN CAPITAL LETTER THORN
		// 'ð' U+00F0 - LATIN SMALL LETTER ETH
		// 'þ' U+00FE - LATIN SMALL LETTER THORN
		_umlauts: { 'À': 'A', 'Á': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'Ae', 'Å': 'A', 'Æ': 'AE', 'Ç': 'C', 'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E', 'Ì': 'I', 'Í': 'I', 'Î': 'I', 'Ï': 'I', 'Ð': 'D', 'Ñ': 'N', 'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'Oe', 'Ø': 'O', 'Ù': 'U', 'Ú': 'U', 'Û': 'U', 'Ü': 'Ue', 'Ý': 'Y', 'Þ': 'P', 'ß': 'ss', 'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'ae', 'å': 'a', 'æ': 'ae', 'ç': 'c', 'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e', 'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i', 'ð': 'o', 'ñ': 'n', 'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'oe', 'ø': 'o', 'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'ue', 'ý': 'y', 'þ': 'p', 'ÿ': 'y'},

		// regular expression for matching variable references in the template
		_regVar: /<(\w*)(:([\w,]*))?>(\[(-?\d*)(:(-?\d*))?\])?/g,

		constructor: function(props) {
			// mixin the props
			lang.mixin(this, props);
			var deferred = {tool_ucr: tools.ucr('directory/manager/templates/alphanum/whitelist')};
			if (this.operation === 'copy') {
				tools.forIn(this.widgets, lang.hitch(this, function(ikey, ival) {
					if (ikey in this.widgets && this.widgets[ikey].ready) {
						deferred[ikey] = this.widgets[ikey].ready();
					}
				}));
			}
			all(deferred).then(lang.hitch(this, function(result) {
				this.whitelist = result.tool_ucr['directory/manager/templates/alphanum/whitelist'] || '';
				this._constructor();
			}));
		},

		_constructor: function() {
			var isEmptyValue = function(val) {
				if (typeof val === 'string') {
					return val === "";
				}
				if (val instanceof Array) {
					return val.length === 0;
				}
				return false;
			};

			// initiate the dict of the last known values
			this._lastValues = {};

			// iterate over all template values
			// * set static values directly to the form
			// * register dynamic values to react on user input
			var updaters = [];
			tools.forIn(this.template, function(ikey, ival) {
				// ignore values that do not have a widget
				if (!(ikey in this.widgets)) {
					console.log('WARNING: The property "' + ikey + '" as specified by the template does not exist. Ignoring error.');
					return true;
				}

				// object for updating the field
				var updater = {
					key: ikey,
					selfReference: this.widgets[ikey],
					templateVal: lang.clone(ival),
					references: [], // ordered list of widgets that are referenced
					modifiers: [], // ordered list of string modifiers per reference
					globalModifiers: [], // string modifiers that are applied on the final string
					getNewVal: function() {
						// collect all necessary values
						var vals = [];
						array.forEach(this.references, function(iwidget, i) {
							vals.push(this.modifiers[i](iwidget.get('value')));
						}, this);

						// the value might be a simple string or an array of strings
						var newVal;
						if (typeof this.templateVal == "string") {
							newVal = this.process(this.templateVal, vals);
						}
						else if (this.templateVal instanceof Array) {
							newVal = [];
							array.forEach(this.templateVal, function(istr) {
								newVal.push(this.process(istr, vals));
							}, this);
						}

						return newVal;
					},
					update: function() {
						var newVal = this.getNewVal();
						this.selfReference.set('value', newVal);
						if (this.selfReference.setInitialValue) {
							this.selfReference.setInitialValue(newVal, false);
						}
					},
					process: function(templateStr, vals) {
						// replace marks in the template string
						var newStr = lang.replace(templateStr, vals);

						// apply global modifiers
						array.forEach(this.globalModifiers, function(imodifier) {
							newStr = imodifier(newStr);
						});
						return newStr;
					}
				};

				// match all variable references
				this._parse(updater);

				// Use the template mechanism only for empty values and copied values that are equal to the template value.
				// If the copied value differs from the template value it will not be updated by the template.
				if (this.operation === 'copy') {
					var widget = this.widgets[ikey];
					var doNotUseTemplate;
					if (widget instanceof CheckBox) {
						doNotUseTemplate = widget._initialValue != widget.get('value');
					} else {
						doNotUseTemplate = !isEmptyValue(widget.get('value')) && !tools.isEqual(updater.getNewVal(), widget.get('value'));
					}
					if (doNotUseTemplate) {
						return;
					}
				}

				if (updater.references.length) {
					// we have a dynamic value with variable references
					updaters.push(updater);
				}
				else {
					// we have a static value, try to set the given key
					if (ikey in this.widgets) {
						this.widgets[ikey].set('value', ival);
						if (this.widgets[ikey].setInitialValue) {
							this.widgets[ikey].setInitialValue(ival, false);
						}
					}
				}
			}, this);

			// build an inverse map to the reference... i.e., we want to know for a field
			// that is being changed, which other templated fields depend on its value
			this._inverseReferences = {};
			array.forEach(updaters, function(iupdater) {
				// get inverse references
				array.forEach(iupdater.references, function(iref) {
					// when we have the first entry for this reference, initiate with an empty dict
					if (!(iref.name in this._inverseReferences)) {
						this._inverseReferences[iref.name] = {};
					}

					// register the reference
					this._inverseReferences[iref.name][iupdater.key] = iupdater;
				}, this);

				// update field for the first time
				iupdater.update();
			}, this);

			// register user changes
			this._userChanges = {};
			tools.forIn(this.widgets, function(ikey, iwidget) {
				// monitor value changes... onChange for changes made automatically and
				// onKeyUp for changes made by the user
				iwidget.on('keyup', lang.hitch(this, 'onChange', iwidget));
				iwidget.own(iwidget.watch('value', lang.hitch(this, 'onChange', iwidget)));

				// save initial value
				this._lastValues[iwidget.name] = iwidget.get('value');
			}, this);
		},

		_parse: function(updater) {
			// templateVal can be a string, an array, or a multi-dimensional array
			// ... iterate over its elements
			updater.templateVal = tools.mapWalk(updater.templateVal, function(istr) {
				// do not modify dicts
				if (typeof istr != "string") {
					return istr;
				}

				// search for references
				var matches = istr.match(this._regVar);
				array.forEach(matches, function(imatch) {
					// parse the matched reference
					this._regVar.lastIndex = 0; // start matching in any case from the string beginning
					var match = this._regVar.exec(imatch);

					// we have a value with variable reference...
					// parse the variable reference and get the correct indices
					var refKey = match[1];
					var modifier = match[3];
					var startIdx = 0;
					var endIdx = Infinity;
					try {
						startIdx = !match[5] ? 0 : parseInt(match[5], 10);
					}
					catch (err1) { }

					// check whether the user specified an end index
					if (!match[6] && typeof match[5] == "string" && match[5].length) {
						// nope... index points to one single character
						endIdx = startIdx + 1;
						if (0 === endIdx) {
							// startIdx == -1
							endIdx = Infinity;
						}
					}
					else if (match[6]) {
						try {
							endIdx = !match[7] && match[7] !== '0' ? Infinity : parseInt(match[7], 10);
						}
						catch (err2) { }
					}

					if (!refKey) {
						// we have a global modifier (i.e., no reference) ... register the modifier
						updater.globalModifiers.push(this._getModifiers(modifier, startIdx, endIdx));

						// update the template string
						istr = istr.replace(imatch, '');
					}
					else if (refKey in this.widgets) {
						// valid reference... register the reference
						updater.references.push(this.widgets[refKey]);

						// update the template string
						istr = istr.replace(imatch, '{' + (updater.references.length - 1) + '}');

						// register the modifier
						updater.modifiers.push(this._getModifiers(modifier, startIdx, endIdx));
					}
				}, this);

				// return modified string
				return istr;
			}, this);
		},

		_getModifiers: function(modifierString, startIdx, endIdx) {
			// get the correct string modifiers (can be a list of modifiers)
			var modifierNames = typeof modifierString == "string" ? modifierString.toLowerCase().split(',') : [''];
			var modifiers = [];
			array.forEach(modifierNames, function(iname) {
				switch(lang.trim(iname)) {
				case 'lower':
					modifiers.push(function(str) {
						return typeof str == "string" ? str.toLowerCase() : str;
					});
					break;
				case 'upper':
					modifiers.push(function(str) {
						return typeof str == "string" ? str.toUpperCase() : str;
					});
					break;
				case 'umlaut':
				case 'umlauts':
					modifiers.push(lang.hitch(this, function(str) {
						if (typeof str != "string") {
							return str;
						}
						var newStr = '';
						for (var i = 0; i < str.length; ++i) {
							newStr += this._umlauts[str[i]] || str[i];
						}
						return newStr;
					}));
					break;
				case 'trim':
				case 'strip':
					modifiers.push(function(str) {
						return lang.trim(str);
					});
					break;
				case 'alphanum':
					modifiers.push(lang.hitch(this, function(str) {
						var result = '';
						for (var i = 0; i < str.length; ++i) {
							var char = str.charAt(i);
							if (/[a-zA-Z0-9]/.test(char) || this.whitelist.indexOf(char) >= 0 || typeof this._umlauts[char] == 'string') {  // TODO: Use unicode regex if IE11 not supported anymore
								result = result.concat(char);
							}
						}
						return result;
					}));
					break;
				default:
					// default modifier is a dummy function that does nothing
					modifiers.push(function(str) { return str; });
				}
			}, this);

			// add index operator as last modifier
			modifiers.push(function(str) {
				return str.slice(startIdx, endIdx);
			});

			// return function that applies all modifiers
			return function(str) {
				array.forEach(modifiers, function(imod) {
					str = imod(str);
				});
				return str;
			};
		},

		onChange: function(widget) {
			// make sure that the widget's value really has been altered
			var lastVal = this._lastValues[widget.name];
			var newVal = widget.get('value');
			if (lastVal == newVal) {
				return;
			}
			this._lastValues[widget.name] = newVal;

			// register that the user has changed this field manually in case the
			// focus was on this field
			if (widget.get('focused')) {
				this._userChanges[widget.name] = true;
			}

			// see whether we can update other fields that have not been changed manually
			var references = this._inverseReferences[widget.name] || {};
			tools.forIn(references, function(iRefKey, iUpdater) {
				if (!this._userChanges[iRefKey]) {
					iUpdater.update();
				}
			}, this);
		}
	});
});


