/*
 * Copyright 2016-2019 Univention GmbH
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

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/window",
	"dojo/Deferred",
	"dojo/aspect",
	"dojo/when",
	"dojo/on",
	"dojo/query",
	"dojo/dom",
	"dojo/dom-class",
	"dojo/dom-attr",
	"dojo/dom-geometry",
	"dojo/dom-style",
	"dojo/dom-construct",
	"dojo/mouse",
	"dojo/dnd/Source",
	"dojo/promise/all",
	"dojox/string/sprintf",
	"dojox/widget/Standby",
	"dijit/focus",
	"dijit/a11y",
	"dijit/registry",
	"dijit/Dialog",
	"dijit/Tooltip",
	"dijit/DropDownMenu",
	"dijit/MenuItem",
	"dijit/form/DropDownButton",
	"umc/tools",
	"umc/render",
	"umc/store",
	"umc/json",
	"umc/dialog",
	"umc/widgets/Button",
	"umc/widgets/Form",
	"umc/widgets/ContainerWidget",
	"umc/widgets/ConfirmDialog",
	"umc/widgets/StandbyMixin",
	"umc/widgets/MultiInput",
	"put-selector/put",
	"dompurify/purify",
	"login/main",
	"./PortalCategory",
	"./PortalEntryWizard",
	"./PortalEntryWizardPreviewTile",
	"./tools",
	"umc/i18n/tools",
	"umc/json!/univention/portal/portal.json", // -> contains entries of this portal as specified in the LDAP directory
	"umc/json!/univention/portal/apps.json", // -> contains all locally installed apps
	"umc/i18n!portal"
], function(declare, lang, array, win, Deferred, aspect, when, on, dojoQuery, dom, domClass, domAttr, domGeometry, domStyle, domConstruct, mouse, Source, all, sprintf, Standby, dijitFocus, a11y, registry, Dialog, Tooltip, DropDownMenu, MenuItem, DropDownButton, tools, render, store, json, dialog, Button, Form, ContainerWidget, ConfirmDialog, StandbyMixin, MultiInput, put, purify, login, PortalCategory, PortalEntryWizard, PortalEntryWizardPreviewTile, portalTools, i18nTools, portalJson, installedApps, _) {

	// convert IPv6 addresses to their canonical form:
	//   ::1:2 -> 0000:0000:0000:0000:0000:0000:0001:0002
	//   1111:2222::192.168.1.1 -> 1111:2222:0000:0000:0000:0000:c0a8:0101
	// but this can also be used for IPv4 addresses:
	//   192.168.1.1 -> c0a8:0101
	var canonicalizeIPAddress = function(address) {
		if (tools.isFQDN(address)) {
			return address;
		}

		// remove leading and trailing ::
		address = address.replace(/^:|:$/g, '');

		// split address into 2-byte blocks
		var parts = address.split(':');

		// replace IPv4 address inside IPv6 address
		if (tools.isIPv4Address(parts[parts.length - 1])) {
			// parse bytes of IPv4 address
			var ipv4Parts = parts[parts.length - 1].split('.');
			for (var i = 0; i < 4; ++i) {
				var byte = parseInt(ipv4Parts[i], 10);
				ipv4Parts[i] = sprintf('%02x', byte);
			}

			// remove IPv4 address and append bytes in IPv6 style
			parts.splice(-1, 1);
			parts.push(ipv4Parts[0] + ipv4Parts[1]);
			parts.push(ipv4Parts[2] + ipv4Parts[3]);
		}

		// expand grouped zeros "::"
		var iEmptyPart = array.indexOf(parts, '');
		if (iEmptyPart >= 0) {
			parts.splice(iEmptyPart, 1);
			while (parts.length < 8) {
				parts.splice(iEmptyPart, 0, '0');
			}
		}

		// add leading zeros
		parts = array.map(parts, function(ipart) {
			return sprintf('%04s', ipart);
		});

		return parts.join(':');
	};

	var getAnchorElement = function(uri) {
		var _linkElement = document.createElement('a');
		_linkElement.setAttribute('href', uri);
		return _linkElement;
	};

	var getURIHostname = function(uri) {
		return getAnchorElement(uri).hostname.replace(/^\[|\]$/g, '');
	};

	var getURIProtocol = function(uri) {
		return getAnchorElement(uri).protocol;
	};

	var _getAddressType = function(link) {
		if (tools.isFQDN(link)) {
			return 'fqdn';
		}
		if (tools.isIPv6Address(link)) {
			return 'ipv6';
		}
		if (tools.isIPv4Address(link)) {
			return 'ipv4';
		}
		return '';
	};

	var _getProtocolType = function(link) {
		if (link.indexOf('//') === 0) {
			return 'relative';
		}
		if (link.indexOf('https') === 0) {
			return 'https';
		}
		if (link.indexOf('http') === 0) {
			return 'http';
		}
		return '';
	};

	var _regExpRelativeLink = /^\/([^/].*)?$/;
	var _isRelativeLink = function(link) {
		return _regExpRelativeLink.test(link);
	};

	// return 1 if link is a relative link, otherwise 0
	var _scoreRelativeURI = function(link) {
		return link.indexOf('/') === 0 && link.indexOf('//') !== 0 ? 1 : 0;
	};

	// score according to the following matrix
	//               Browser address bar
	//              | FQDN | IPv4 | IPv6
	//       / FQDN |  4   |  1   |  1
	// link <  IPv4 |  2   |  4   |  2
	//       \ IPv6 |  1   |  2   |  4
	var _scoreAddressType = function(browserLinkType, linkType) {
		var scores = {
			fqdn: { fqdn: 4, ipv4: 2, ipv6: 1 },
			ipv4: { fqdn: 1, ipv4: 4, ipv6: 2 },
			ipv6: { fqdn: 1, ipv4: 2, ipv6: 4 }
		};
		try {
			return scores[browserLinkType][linkType] || 0;
		} catch(err) {
			return 0;
		}
	};

	// score according to the following matrix
	//              Browser address bar
	//               | https | http
	//       / "//"  |   4   |  4
	// link <  https |   2   |  1
	//       \ http  |   1   |  2
	var _scoreProtocolType = function(browserProtocolType, protocolType) {
		var scores = {
			https: { relative: 4, https: 2, http: 1 },
			http:  { relative: 4, https: 1, http: 2 }
		};
		try {
			return scores[browserProtocolType][protocolType] || 0;
		} catch(err) {
			return 0;
		}
	};

	// score is computed as the number of matched characters
	var _scoreAddressMatch = function(browserHostname, hostname, matchBackwards) {
		if (matchBackwards) {
			// match not from the beginning of the string, but from the end
			browserHostname = browserHostname.split('').reverse().join('');
			hostname = hostname.split('').reverse().join('');
		}
		var i;
		for (i = 0; i < Math.min(browserHostname.length, hostname.length); ++i) {
			if (browserHostname[i] !== hostname[i]) {
				break;
			}
		}
		return i;
	};

	// Given the browser URI and a list of links, each link is ranked via a
	// multi-part score. This effectively allows to chose the best matching
	// link w.r.t. the browser session.
	var _rankLinks = function(browserURI, links) {
		// score all links
		var browserHostname = getURIHostname(browserURI);
		var browserLinkType = _getAddressType(browserHostname);
		var canonicalizedBrowserHostname = canonicalizeIPAddress(browserHostname);
		var browserProtocolType = _getProtocolType(browserURI);
		links = array.map(links, function(ilink) {
			var linkHostname = getURIHostname(ilink);
			var canonicalizedLinkHostname = canonicalizeIPAddress(linkHostname);
			var linkType = _getAddressType(linkHostname);
			var linkProtocolType = _getProtocolType(ilink);
			var addressMatchScore = 0;
			if (browserLinkType === linkType) {
				// FQDNs are matched backwards, IP addresses forwards
				var matchBackwards = linkType === 'fqdn' ? true : false;
				addressMatchScore = _scoreAddressMatch(canonicalizedBrowserHostname, canonicalizedLinkHostname, matchBackwards);
			}
			return {
				scores: [
					_scoreRelativeURI(ilink),
					addressMatchScore,
					_scoreAddressType(browserLinkType, linkType),
					_scoreProtocolType(browserProtocolType, linkProtocolType)
				],
				link: ilink
			};
		});

		function _cmp(x, y) {
			for (var i = 0; i < x.scores.length; ++i) {
				if (x.scores[i] === y.scores[i]) {
					continue;
				}
				if (x.scores[i] < y.scores[i]) {
					return 1;
				}
				return -1;
			}
		}

		// sort links descending w.r.t. their scores
		links.sort(_cmp);

		// return the best match
		return links;
	};

	var getHighestRankedLink = function(browserURI, links) {
		return _rankLinks(browserURI, links)[0].link || '#';
	};

	var getLocalLinks = function(browserHostname, serverFQDN, links) {
		// check whether there is any relative link
		var relativeLinks = array.filter(links, function(ilink) {
			return _isRelativeLink(ilink);
		});
		if (relativeLinks.length) {
			return relativeLinks;
		}

		// check whether there is a link containing the FQDN of the local server
		var localLinks = [];
		array.forEach(links, function(ilink) {
			var uri = getAnchorElement(ilink);
			if (uri.hostname === serverFQDN) {
				uri.hostname = browserHostname;
				localLinks.push(uri.href);
			}
		});
		return localLinks;
	};

	var getFQDNHostname = function(links) {
		// check for any relative link
		var hasRelativeLink = array.some(links, function(ilink) {
			return _isRelativeLink(ilink);
		});
		if (hasRelativeLink) {
			return tools.status('fqdn');
		}

		// look for any links that refer to an FQDN
		var fqdnLinks = [];
		array.forEach(links, function(ilink) {
			var linkHostname = getURIHostname(ilink);
			if (tools.isFQDN(linkHostname)) {
				fqdnLinks.push(linkHostname);
			}
		});
		if (fqdnLinks.length) {
			return fqdnLinks[0];
		}
		return null;
	};

	var getBestLinkAndHostname = function(links) {
		var browserHostname = getURIHostname(document.location.href);
		// get the best link to be displayed
		var localLinks = getLocalLinks(browserHostname, tools.status('fqdn'), links);
		localLinks = localLinks.concat(links);
		var bestLink = getHighestRankedLink(document.location.href, localLinks);

		// get the hostname to be displayed on the tile
		var hostname = getFQDNHostname(links) || getURIHostname(bestLink);

		return {
			link: bestLink,
			hostname: hostname
		};
	};


	var _getLogoName = function(logo) {
		if (logo && !hasImageSuffix(logo)) {
			logo = logo + '.svg'; // the logos for the entries from apps.json do not have a suffix
		}
		return logo;
	};

	var _regHasImageSuffix = /\.(svg|jpg|jpeg|png|gif)$/i;
	var hasImageSuffix = function(path) {
		return path && _regHasImageSuffix.test(path);
	};

	var _Button = declare([Button], {
		_setDescriptionAttr: function(description) {
			this.inherited(arguments);
			this._tooltip.showDelay = 0;
			this._tooltip.hideDelay = 0;
		}
	});

	var _PortalPropertiesDialog = declare('PortalPropertiesDialog', [ConfirmDialog, StandbyMixin]);
	var _WizardDialog = declare('WizardDialog', [Dialog, StandbyMixin]);

	var locale = i18nTools.defaultLang().replace(/-/, '_');
	return {
		// always
		_search: null,
		_categoryIndex: null,
		_portalCategories: null,
		_globalEntryIndex: null,
		_contentNode: null,
		_cleanupList: null,

		// edit
		_standby: null,
		_moduleCache: null,
		_moduleStore: null,

		_reloadCss: function() {
			// FIXME? instead of reloading the portal.css file,
			// use styles.insertCssRule to display the style
			// changes made after the first site load

			// reload the portal.css file
			var re = /.*\/portal.css\??\d*$/;
			var links = document.getElementsByTagName('link');
			var link = array.filter(links, function(ilink) {
				return re.test(ilink.href);
			})[0];
			if (!link) {
				return;
			}
			var href = link.href;
			if (href.indexOf('?') !== -1) {
				href = href.substr(0, href.indexOf('?'));
			}
			href += lang.replace('?{0}', [Date.now()]);
			link.href = href;
		},

		// FIXME reloading the portal.json to update the content
		// depends on the portal.py listener and that the new data
		// is written to portal.json before it is reloaded.
		// Maybe it would be better to save changes made after the
		// initial load into a cache and if cached data is available
		// use that instead of the initial portal.json data
		_reloadPortalContent: function(admin_mode) {
			var loadDeferred = new Deferred();

			var headers = null;
			if (admin_mode) {
				headers = {
					'X-Univention-Portal-Admin-Mode': 'yes'
				};
			}
			var waitedTime = 0;
			var waitTime = 200;

			var previousPortalJson = lang.clone(portalJson);

			var _load = function() {
				if (waitedTime >= 3000) {
					loadDeferred.resolve();
					return;
				}

				setTimeout(function() {
					json.load('/univention/portal/portal.json', require, function(result) {
						if (result && result.portal && result.entries && result.categories) {
							if (tools.isEqual(result, previousPortalJson)) {
								_load();
							} else {
								portalJson = result;
								loadDeferred.resolve();
							}
						} else {
							_load();
						}
					}, headers);
				}, waitTime);
				waitedTime += waitTime;
			};

			_load();
			return loadDeferred;
		},

		_refresh: function(renderModeAfterRefresh) {
			var deferred = new Deferred();
			this._reloadPortalContent(renderModeAfterRefresh != portalTools.RenderMode.NORMAL).then(lang.hitch(this, function() {
				domClass.toggle(dom.byId('umcHeader'), 'umcWhiteIcons', lang.getObject('portal.fontColor', false, portalJson) === 'white');
				this._reloadCss(); // FIXME only reload css if it is necessary (cssBackground / background / fontColor changed)
				this._render(renderModeAfterRefresh);
				deferred.resolve();
			}));
			return deferred;
		},

		// TODO copy pasted partially from udm/DetailPage - _prepareWidgets
		_prepareProps: function(props) {
			array.forEach(props, function(iprop) {
				if (iprop.type.indexOf('MultiObjectSelect') >= 0) {
					iprop.multivalue = false;
					iprop.umcpCommand = store('$dn$', 'udm', 'settings/portal_all').umcpCommand;
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

		_isEmptyValue: function(value) {
			if (typeof value === 'string' || value instanceof Array) {
				return value.length === 0;
			} else if (typeof value === 'object') {
				return Object.keys(value).length === 0;
			} else {
				return false;
			}
		},

		_editProperties: function(type, dn, propNames, dialogTitle, categoryIndex /*optional*/) {
			var standbyWidget = this._standby;
			standbyWidget.show();
			var formDialog = null; // block scope variable
			var _this = this;

			this._moduleCache.getProperties(type, dn).then(lang.hitch(this, function(props) {
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

					on(form, 'submit', lang.hitch(this, function() {
						formDialog.standby(true);
						var formValues = form.get('value');

						var alteredValues = {};
						tools.forIn(formValues, function(iname, ivalue) {
							if (iname === '$dn$') {
								return;
							}
							if (!tools.isEqual(ivalue, initialFormValues[iname])) {
								alteredValues[iname] = ivalue;
							}
						});

						// reset validation settings from last validation
						tools.forIn(form._widgets, function(iname, iwidget) {
							if (iwidget.setValid) {
								iwidget.setValid(null);
							}
						});
						// see if there are widgets that are required and have no value
						var allValid = true;
						var firstInvalidWidget = null;
						tools.forIn(form._widgets, function(iname, iwidget) {
							var isEmpty = this._isEmptyValue(iwidget.get('value'));
							if (iwidget.required && isEmpty) {
								allValid = false;
								// TODO this is kind of doubled because form.validate()
								// is already called, but MultiInput widgets that are required
								// do not work correctly with validate
								iwidget.setValid(false, _('This value is required')); // TODO wording / translation
							} else if (iwidget.isValid && !iwidget.isValid()) {
								allValid = false;
							}
							if (!allValid && !firstInvalidWidget && a11y.getFirstInTabbingOrder(iwidget.domNode)) {
								firstInvalidWidget = iwidget;
							}
						}, this);
						if (!allValid) {
							dijitFocus.focus(a11y.getFirstInTabbingOrder(firstInvalidWidget.domNode));
							formDialog.standby(false);
							return;
						}

						// check if the values in the form have changed
						// and if not return and close without saving
						if (Object.keys(alteredValues).length === 0) {
							formDialog.close();
							return;
						}

						var alteredValuesNonEmpty = {};
						tools.forIn(alteredValues, function(iname, ivalue) {
							if (!this._isEmptyValue(ivalue)) {
								alteredValuesNonEmpty[iname] = ivalue;
							}
						}, this);
						// validate the form values
						tools.umcpCommand('udm/validate', {
							objectType: type,
							properties: alteredValuesNonEmpty
						}).then(lang.hitch(this, function(response) {
							// parse response and mark widgets with invalid values
							var allValid = true;
							array.forEach(response.result, lang.hitch(this, function(iprop) {
								if (iprop.valid instanceof Array) {
									array.forEach(iprop.valid, function(ivalid, index) {
										if (ivalid) {
											iprop.valid[index] = null;
										} else {
											allValid = false;
										}
									});
								} else {
									if (iprop.valid) {
										iprop.valid = null;
									} else {
										allValid = false;
									}
								}

								var widget = form.getWidget(iprop.property);
								widget.setValid(iprop.valid, iprop.details);
								if (!allValid && !firstInvalidWidget && a11y.getFirstInTabbingOrder(widget.domNode)) {
									firstInvalidWidget = widget;
								}
							}));
							if (!allValid) {
								dijitFocus.focus(a11y.getFirstInTabbingOrder(firstInvalidWidget.domNode));
								formDialog.standby(false);
								return;
							}

							// save the altered values
							if (alteredValues.displayName) {
								alteredValues.displayName = alteredValues.displayName.concat(initialFormValues.displayName_remaining);
							}

							var moduleStoreFunc = dn ? 'put' : 'add';
							var moduleStoreParams = dn ? lang.mixin(alteredValues, {'$dn$': dn}) : formValues;
							var moduleStoreOptions = dn ? null : {'objectType': type};
							form.moduleStore[moduleStoreFunc](moduleStoreParams, moduleStoreOptions).then(lang.hitch(this, function(result) {
								if (result.success) {
									formDialog.close();
									dialog.contextNotify(_('Changes saved'));
									if (!dn) {
										var content = lang.clone(portalJson.portal.content);
										content.push([result.$dn$, []]);
										this._saveEntryOrder(content);
									} else {
										this._refresh(portalTools.RenderMode.EDIT);
									}
								} else {
									var errmsg = '';
									if (!dn) {
										errmsg = _('The creation failed: %(details)s', result);
									} else {
										errmsg = _('The changes could not be saved: %(details)s', result);
									}
									dialog.alert(errmsg);
									formDialog.standby(false);
								}
							}), function() {
								// TODO different error message
								var errmsg = '';
								if (!dn) {
									errmsg = _('The creation failed');
								} else {
									errmsg = _('The changes could not be saved');
								}
								dialog.alert(errmsg);
								formDialog.standby(false);
							});
						}));
					}));

					var formPreparationsDeferreds = [];
					form.startup();
					var formLoaded = dn ? form.load(dn) : true;
					when(formLoaded).then(function() {
						form.ready().then(function() {
							// preload images from ImageUploader widgets so that the
							// dialog is correctly centered
							var propNamesWithImages = array.map(array.filter(props, function(iprop) {
								return iprop.type === 'ImageUploader';
							}), function(iprop) {
								return iprop.id;
							});
							array.forEach(propNamesWithImages, function(ipropName) {
								var deferred = new Deferred();
								formPreparationsDeferreds.push(deferred);

								var imageWidget = form.getWidget(ipropName)._image;
								var img = new Image();
								var loaded = function() {
									deferred.resolve();
									img.remove();
								};
								on(img, ['load', 'error'], loaded);
								img.src = lang.replace('data:image/{imageType};base64,{value}', {
									imageType: imageWidget._getImageType(),
									value: imageWidget.value
								});
							});

							// save initial form values
							array.forEach(propNames, function(ipropName) {
								initialFormValues[ipropName] = form._widgets[ipropName].get('value');
							});

							if (initialFormValues.displayName) {
								var deferred = new Deferred();
								formPreparationsDeferreds.push(deferred);
								// if we edit the displayName property of the portal
								// we only want to show the available languages (the languages that are also in the menu)
								// with the language codes prefilled.
								var availableLanguageCodes = array.map(i18nTools.availableLanguages, function(ilanguage) {
									return ilanguage.id.replace(/-/, '_');
								});
								// shift current locale to the beginning
								availableLanguageCodes.splice(0, 0, availableLanguageCodes.splice(availableLanguageCodes.indexOf(locale), 1)[0]);

								array.forEach(['displayName'], lang.hitch(this, function(iname) {
									var filteredName = [];
									array.forEach(availableLanguageCodes, function(ilanguageCode) {
										var name = array.filter(initialFormValues[iname], function(iname) {
											return iname[0] === ilanguageCode;
										})[0];
										if (!name) {
											name = [ilanguageCode, ''];
										}
										filteredName.push(name);
									});
									var remainingName = array.filter(initialFormValues[iname], function(iname) {
										return array.indexOf(availableLanguageCodes, iname[0]) === -1;
									});

									initialFormValues[iname] = filteredName;
									initialFormValues[iname + '_remaining'] = remainingName;

									// clear all rows then set max and then set filtered displayName
									form._widgets[iname].set('value', []);
									domClass.add(form._widgets[iname].domNode, 'noRemoveButton');
									form._widgets[iname].set('max', filteredName.length);
									form._widgets[iname].set('value', initialFormValues[iname]);
									// disable language code textboxes
									form._widgets[iname].ready().then(function() {
										array.forEach(form._widgets[iname]._widgets, function(iwidget) {
											iwidget[0].set('disabled', true);
										});
										deferred.resolve();
									});
								}));
							}

							var portalComputersProp = array.filter(props, function(iprop) {
								return iprop.id === 'portalComputers';
							})[0];
							if (portalComputersProp) {
								form._widgets.portalComputers.autoSearch = true;
							}

							if (type === 'settings/portal_category' && dn) {
								form._widgets.name.set('disabled', true);
							}

							var options = [{
								name: 'cancel',
								label: _('Cancel'),
								callback: function(r) {
									formDialog.close();
								}
							}, {
								name: 'submit',
								label: _('Save'),
								default: true,
								callback: function() {
									form.submit();
								}
							}];
							if (type === 'settings/portal_category' && dn) {
								options.splice(1, 0, {
									'name': 'remove',
									'label': _('Remove from this portal'),
									'callback': lang.hitch(this, function() {
										formDialog.close();
										var content = lang.clone(portalJson.portal.content);
										content.splice(categoryIndex, 1);
										_this._saveEntryOrder(content);
									})
								});
							}

							// create dialog to show form
							all(formPreparationsDeferreds).then(function() {
								formDialog = new _PortalPropertiesDialog({
									'class': 'portalPropertiesDialog', // TODO generic classname
									closable: true, // so that the dialog is closable via esc key
									title: dialogTitle,
									message: form,
									options: options
								});

								// go against the behavior of ConfirmDialog to focus the confirm button
								// and focus the first focusable widget in the dialog instead
								// @FIXME cleanup (flag in ConfirmDialog or use normal Dialog instead of ConfirmDialog)
								on(formDialog, 'focus', function() {
									formDialog.focus();
								});
								formDialog.startup();
								formDialog.show();
								standbyWidget.hide();
							});
						});
					});
				}));
			}));
		},

		_renderCategory: function(category, renderMode) {
			var portalCategory = new PortalCategory({
				heading: category.heading,
				entries: category.entries,
				domainName: tools.status('domainname'),
				renderMode: renderMode,
				category: category.dn,
				categoryIndex: category.dn === 'localApps' ? null : this._categoryIndex++,
				$notInPortalJSON$: category.$notInPortalJSON$,
				defaultLinkTarget: portalJson.portal.defaultLinkTarget,
			});
			this._cleanupList.widgets.push(portalCategory);

			switch (renderMode) {
				case portalTools.RenderMode.EDIT:
					portalCategory.own(on(portalCategory, 'addEntry', lang.hitch(this, function() {
						this.editPortalEntry(portalCategory);
					})));
					portalCategory.own(on(portalCategory, 'editEntry', lang.hitch(this, function(entry) {
						if (!entry.dn) {
							dialog.alert(_('The dn for this entry could not be found'));
							return;
						}
						this.editPortalEntry(portalCategory, entry);
					})));
					portalCategory.own(on(portalCategory, 'entryNotInPortalJSON', lang.hitch(this, function(entry) {
						dialog.confirm(_("<p>The entry with the dn '%s' should be shown at this position but it could not be found.</p><p>Try refreshing or calling<br><pre>univention-directory-listener-ctrl resync portal\nunivention-directory-listener-ctrl resync portal_entry\nunivention-directory-listener-ctrl resync portal_category</pre></p>", entry.dn), [{
							label: _('Remove from this portal'),
							callback: lang.hitch(this, function() {
								var content = lang.clone(portalJson.portal.content);
								content[portalCategory.categoryIndex][1].splice(entry.index, 1);
								this._saveEntryOrder(content);
							})
						}, {
							label: 'OK',
							default: true
						}], 'title');
					})));
					portalCategory.own(on(portalCategory, 'editCategory', lang.hitch(this, function() {
						this._editProperties('settings/portal_category', portalCategory.category, ['name', 'displayName'], 'Edit category', portalCategory.categoryIndex);
					})));
					portalCategory.own(on(portalCategory, 'categoryNotInPortalJSON', lang.hitch(this, function() {
						dialog.confirm(_("<p>The category with the dn '%s' should be shown at this position but it could not be found.</p><p>Try refreshing the page or calling<br><pre>univention-directory-listener-ctrl resync portal\nunivention-directory-listener-ctrl resync portal_entry\nunivention-directory-listener-ctrl resync portal_category</pre></p>", portalCategory.category), [{
							label: _('Remove from this portal'),
							callback: lang.hitch(this, function() {
								var content = lang.clone(portalJson.portal.content);
								content.splice(portalCategory.categoryIndex, 1);
								this._saveEntryOrder(content);
							})
						}, {
							label: 'OK',
							default: true
						}], 'title');
					})));
					break;
			}

			this._portalCategories.push(portalCategory);
			return portalCategory;
		},

		_renderAddCategoryButton: function() {
			var menu = new DropDownMenu({});
			var menuItem_createNew = new MenuItem({
				label: _('Create new category'),
				onClick: lang.hitch(this, function() {
					this._editProperties('settings/portal_category', null, ['name', 'displayName'], _('Create new category'));
				})
			});
			var menuItem_fromExisting = new MenuItem({
				label: _('Add existing category'),
				onClick: lang.hitch(this, function() {
					require(['umc/modules/udm/ComboBox'], lang.hitch(this, function() {
						dialog.confirmForm({
							'title': _('Add category'),
							'submit': _('Add'),
							'widgets': [{
								'name': 'category',
								'label': _('Category'),
								'dynamicValues': 'udm/syntax/choices',
								'dynamicOptions': {
									'syntax': 'PortalCategoryV2'
								},
								'type': 'umc/modules/udm/ComboBox',
								'size': 'Two',
								'threshold': 2000
							}],
							'layout': ['category']
						}).then(lang.hitch(this, function(result) {
							var content = lang.clone(portalJson.portal.content);
							content.push([result.category, []]);
							this._saveEntryOrder(content);
						}), lang.hitch(this, function() {
							// error stub (prevent error log when dialog is canceled)
						}));
					}));
				})
			});
			menu.addChild(menuItem_createNew);
			menu.addChild(menuItem_fromExisting);
			menu.startup();

			this.newCategoryButton = new DropDownButton({
				label: _('Add category'),
				'class': 'newCategory',
				dropDown: menu
			});
			this.newCategoryButton.startup();
			this._cleanupList.widgets.push(this.newCategoryButton);
			put(this._contentNode, this.newCategoryButton.domNode);
		},

		editPortalEntry: function(portalCategory, item) {
			var standbyWidget = this._standby;
			standbyWidget.show();
			var _initialDialogTitle = item ? _('Edit entry') : _('Create entry');

			this._moduleCache.getProperties('settings/portal_entry').then(lang.hitch(this, function(portalEntryProps) {
				portalEntryProps = lang.clone(portalEntryProps);

				render.requireWidgets(portalEntryProps).then(lang.hitch(this, function() {
					portalEntryProps = this._prepareProps(portalEntryProps);
					var wizardWrapper = new ContainerWidget({});
					var tile = new PortalEntryWizardPreviewTile({});
					var wizard = new PortalEntryWizard({
						portalEntryProps: portalEntryProps,
						moduleStore: this._moduleStore,
						locale: locale
					});
					var wizardDialog = null;

					wizard.own(on(wizard, 'loadEntry', function() {
						// FIXME this is not really clear
						// if we click on a tile of an existing portal entry,
						// loadEntry is called before the wizardDialog exists.
						// This case is for when we click on the tile
						// to create a new portal entry and then load an
						// existing entry by entering an existing portal entry name.
						if (wizardDialog) {
							wizardDialog._initialTitle = _('Edit entry');
						}
						domClass.toggle(tile.domNode, 'editMode', wizard.dn ? true : false);
						on(tile.domNode, mouse.enter, function() {
							domClass.add(tile.wrapperNode, 'hover');
						});
						on(tile.domNode, mouse.leave, function() {
							domClass.remove(tile.wrapperNode, 'hover');
						});
					}));
					wizard.startup();
					wizard.ready().then(lang.hitch(this, function() {
						// adjust wizardDialog title when the page of the wizard changes
						tile.set('currentPageClass', wizard.selectedChildWidget.name);
						wizard.own(wizard.watch('selectedChildWidget', function(name, oldPage, newPage) {
							// focus the first focusable element for the current page
							wizardDialog.focus();

							tile.set('currentPageClass', newPage.name);
							var subtext = {
								'icon': ': Icon',
								'displayName': ': Display Name',
								'link': ': Link',
								'description': ': Description',
								'name': ''
							}[newPage.name];
							wizardDialog.set('title', lang.replace('{0}{1}', [wizardDialog._initialTitle, subtext]));
						}));


						// watch the icon on the icon page and update the preview tile accordingly
						wizard.getWidget('icon')._image.watch('value', function(name, oldVal, newVal) {
							var iconUri = '';
							if (newVal) {
								iconUri = lang.replace('data:image/{0};base64,{1}', [this._getImageType(), newVal]);
							}
							tile.set('icon', iconUri);
						});

						// add onChange listener for displayName and description
						// to update the preview tile if displayName or description
						// is changed
						var defaultValuesForResize = this._portalCategories[0].grid._getDefaultValuesForResize('.umcGalleryName');
						array.forEach(['displayName', 'description'], function(ipropName) {
							var widget = wizard.getWidget(ipropName);
							widget.ready().then(function() {
								array.forEach(widget._widgets, function(iwidget) {
									iwidget[1].set('intermediateChanges', true);
									wizard.own(on(iwidget[1], 'change', function() {
										var previewText = '';
										var ipropValues = widget.get('value');
										// ipropValues has the following format where
										// the current locale (selected language for the portal)
										// is the first entry
										//   [
										//   	['de_DE', 'Text']
										//   	['fr_FR', '']
										//   	['en_EN', 'Text']
										//   ]
										//
										// if text for current locale exists
										// we use it for the preview tile else
										// we use the first locale with text
										if (ipropValues[0][1].length) {
											previewText = ipropValues[0][1];
										} else {
											// FIXME use some short circuiting
											var ipropValuesWithText = array.filter(ipropValues, function(ipropValue) {
												return ipropValue[1];
											});
											if (ipropValuesWithText.length) {
												previewText = ipropValuesWithText[0][1];
											}
										}
										tile.set(ipropName, previewText);
										// resize the displayName
										if (ipropName === 'displayName') {
											var fontSize = parseInt(defaultValuesForResize.fontSize, 10) || 16;
											domStyle.set(tile.displayNameNode, 'font-size', fontSize + 'px');
											while (domGeometry.position(tile.displayNameNode).h > defaultValuesForResize.height) {
												fontSize--;
												domStyle.set(tile.displayNameNode, 'font-size', fontSize + 'px');
											}
										}
									}));
								});
							});
						});

						// add onChange listener for link to update
						// the preview tile if link is changed
						var widget = wizard.getWidget('link');
						var __addLinkOnChangeListener = function(rowIndex) {
							var rowWidget = widget._widgets[rowIndex];
							rowWidget[0].set('intermediateChanges', true);
							wizard.own(on(rowWidget[0], 'change', function() {
								var link = '';
								var entryLinks = wizard.getWidget('link').get('value');
								if (entryLinks.length) {
									link = getBestLinkAndHostname(entryLinks).hostname;
								}
								tile.set('link', link);
							}));
						};
						widget.ready().then(function() {
							array.forEach(widget._widgets, function(iwidget, rowIndex) {
								__addLinkOnChangeListener(rowIndex);
							});
						});
						aspect.after(widget, '__appendRow', function(rowIndex) {
							widget.ready().then(__addLinkOnChangeListener(rowIndex));
						}, true);


						//// listener for save / finish / cancel
						// close wizard on cancel
						wizard.own(on(wizard, 'cancel', lang.hitch(this, function() {
							wizardDialog.hide().then(function() {
								wizardDialog.destroyRecursive();
							});
						})));

						// create a new portal entry object
						wizard.own(on(wizard, 'finished', lang.hitch(this, function(values) {
							wizardDialog.standby(true);

							lang.mixin(values, {
								activated: true,
							});

							wizard.moduleStore.add(values, {
								objectType: 'settings/portal_entry'
							}).then(lang.hitch(this, function(result) {
								if (result.success) {
									var content = lang.clone(portalJson.portal.content);
									content[portalCategory.categoryIndex][1].push(result.$dn$);
									wizardDialog.hide().then(lang.hitch(this, function() {
										wizardDialog.destroyRecursive();
										dialog.contextNotify(_('Portal entry was successfully created'));
										this._saveEntryOrder(content);
									}));
								} else {
									dialog.alert(_('The portal entry object could not be saved: %(details)s', result));
									wizardDialog.standby(false);
								}
							}), function() {
								dialog.alert(_('The portal entry object could not be saved.'));
								wizardDialog.standby(false);
							});
						})));

						// save changes made to an existing portal entry object
						wizard.own(on(wizard, 'save', lang.hitch(this, function(formValues) {
							wizardDialog.standby(true);

							// TODO the error message from the backend if the internal name was
							// altered is not really expressive
							var alteredValues = {};
							tools.forIn(formValues, function(iname, ivalue) {
								if (iname === '$dn$') {
									return;
								}
								if (!tools.isEqual(ivalue, wizard.initialFormValues[iname])) {
									alteredValues[iname] = ivalue;
								}
							});

							var alteredValuesNonEmpty = {};
							tools.forIn(alteredValues, function(iname, ivalue) {
								if (!this._isEmptyValue(ivalue)) {
									alteredValuesNonEmpty[iname] = ivalue;
								}
							}, this);

							// check if the values in the form have changed
							// and we do not force saving.
							// In that case return and close without saving
							if (!wizard._forceSave && Object.keys(alteredValues).length === 0) {
								wizardDialog.hide().then(function() {
									wizardDialog.destroyRecursive();
								});
								return;
							}

							//// save the altered values
							// concatenate the altered form values for displayName and description
							// with the ones filtered out when loading the portal entry object
							array.forEach(['displayName', 'description'], lang.hitch(this, function(ipropName) {
								if (alteredValues[ipropName]) {
									alteredValues[ipropName] = alteredValues[ipropName].concat(wizard.initialFormValues[ipropName + '_remaining']);
								}
							}));

							// save changes
							var putParams = lang.mixin(alteredValues, {
								'$dn$': wizard.dn
							});
							wizard.moduleStore.put(putParams).then(lang.hitch(this, function(result) {
								// see whether creating the portal entry was successful
								if (result.success) {
									// if the icon for the entry was changed we want a new iconClass
									// to display the new icon
									if (formValues.icon) {
										var entry = array.filter(portalJson.entries, function(ientry) {
											return ientry.dn === wizard.dn;
										})[0];
										if (entry) {
											portalTools.requestNewIconClass(entry.logo_name);
										}
									}

									// reload categories and close wizard dialog
									this._refresh(portalTools.RenderMode.EDIT).then(function() {
										wizardDialog.hide().then(function() {
											wizardDialog.destroyRecursive();
											dialog.contextNotify(_('Changes saved'));
										});
									});
								} else {
									dialog.alert(_('The editing of the portal entry object failed: %(details)s', result));
									wizardDialog.standby(false);
								}
							}), function() {
								dialog.alert(_('The editing of the portal entry object failed.'));
								wizardDialog.standby(false);
							}).then(lang.hitch(this, function() {
								if (!item || wizard.dn !== item.dn) {
									var content = lang.clone(portalJson.portal.content);
									if (!item) {
										content[portalCategory.categoryIndex][1].push(wizard.dn);
									} else {
										content[portalCategory.categoryIndex][1][item.index] = wizard.dn;
									}
									this._saveEntryOrder(content);
								}
							}));
						})));

						// remove portal entry object from this portal
						wizard.own(on(wizard, 'remove', lang.hitch(this, function() {
							wizardDialog.hide().then(function() {
								wizardDialog.destroyRecursive();
							});
							var content = lang.clone(portalJson.portal.content);
							content[portalCategory.categoryIndex][1].splice(item.index, 1);
							this._saveEntryOrder(content);
						})));

						// create and show dialog with the wizard
						wizardWrapper.addChild(tile);
						wizardWrapper.addChild(wizard);

						var wizardReady = item ? wizard.loadEntry(item.dn) : true;
						when(wizardReady).then(function() {
							wizardDialog = new _WizardDialog({
								_initialTitle: _initialDialogTitle,
								title: _initialDialogTitle,
								'class': 'portalEntryDialog',
								content: wizardWrapper
							});
							on(wizard, 'nameQuery', function() {
								wizardDialog.standby(true);
							});
							on(wizard, 'nameQueryEnd', function() {
								wizardDialog.standby(false);
							});
							on(wizard, 'entryLoaded', function() {
								wizardDialog.standby(false);
							});
							wizardDialog.show();
							standbyWidget.hide();
						});
					}));
				}));
			}));
		},

		start: function() {
			if (portalJson.portal.ensureLogin && !tools.status('loggedIn')) {
				login.start();
				return;
			}

			this._initProperties();
			this._registerEventHandlerForSearch();
			this._setupEditModeIfAuthorized();
			this._render(portalTools.RenderMode.NORMAL);
			this._addLinks();
			if (tools.status('username')) {
				dojoQuery('body').addClass('logged-in');
			}

			on(window, 'resize', lang.hitch(this, function() {
				this._handleWindowResize();
			}));
		},

		_initProperties: function() {
			this._search = registry.byId('umcLiveSearch');
			this._categoryIndex = 0;
			this._portalCategories = [];
			this._globalEntryIndex = 0;
			this._contentNode = dom.byId('content');
			this._cleanupList = {
				handlers: [],
				widgets: []
			};
		},

		_registerEventHandlerForSearch: function() {
			this._search.on('search', lang.hitch(this, 'filterPortal'));
		},

		_setupEditModeIfAuthorized: function() {
			this._checkEditAuthorization().then(lang.hitch(this, function(canEdit) {
				if (canEdit) {
					this._setupEditMode();
				}
			}));
		},

		_checkEditAuthorization: function() {
			var deferred = new Deferred();
			tools.umcpCommand('get/modules').then(function(result) {
				var isAuthorized = result.modules.some(function(module) {
					return module.flavor === 'settings/portal_all';
				});
				deferred.resolve(isAuthorized);
			});
			return deferred;
		},

		_setupEditMode: function() {
			// require cache only here and not at the beginning of the file
			// because member servers and slaves do not have
			// the univention-management-console-module-udm package installed.
			// This method is only called when it is available
			require(['umc/modules/udm/cache'], lang.hitch(this, function(cache) {
				this._moduleCache = cache.get('settings/portal_all');
				this._moduleStore = store('$dn$', 'udm', 'settings/portal_all');

				this._createStandbyWidget();
				this._createEnterEditModeButton();
				this._createToolbar();
			}));
		},

		_createStandbyWidget: function() {
			this._standby = new Standby({
				target: dom.byId('portal'),
				zIndex: 100,
				image: require.toUrl("dijit/themes/umc/images/standbyAnimation.svg").toString(),
				duration: 200
			});
			put(dom.byId('portal'), this._standby.domNode);
			this._standby.startup();
		},

		_createEnterEditModeButton: function() {
			var portalEditFloatingButton = put(dom.byId('portal'), 'div.portalEditFloatingButton div.icon <');
			new Tooltip({
				label: _('Edit this portal'),
				showDelay: 0,
				hideDelay: 0,
				connectId: [portalEditFloatingButton],
				position: ['above']
			});
			on(portalEditFloatingButton, 'click', lang.hitch(this, '_refresh', portalTools.RenderMode.EDIT));
		},

		_createToolbar: function() {
			var toolbar = new ContainerWidget({
				'class': 'portalEditBar'
			});
			var entryOrderButton = new _Button({
				iconClass: '',
				'class': 'portalEditBarEntryOrderButton',
				label: _('Order'),
				description: _('Change order of portal entries via drag and drop'),
				callback: lang.hitch(this, function() {
					saveEntryOrderButton.focus();
					this._render(portalTools.RenderMode.DND);
				})
			});
			var visibilityButton = new _Button({
				iconClass: '',
				'class': 'portalEditBarVisibilityButton',
				label: _('Visibility'),
				description: _('Edit the visibility of this portal'),
				callback: lang.hitch(this, '_editProperties', 'settings/portal', portalJson.portal.dn, ['portalComputers'], _('Portal visibility'))
			});
			var appearanceButton = new _Button({
				iconClass: '',
				'class': 'portalEditBarAppearanceButton',
				label: _('Appearance'),
				description: _('Edit the font color and background for this portal'),
				callback: lang.hitch(this, '_editProperties', 'settings/portal', portalJson.portal.dn, ['fontColor', 'background', 'cssBackground'], _('Portal appearance'))
			});
			var closeButton = new _Button({
				iconClass: 'umcCrossIconWhite',
				'class': 'portalEditBarCloseButton umcIconButton',
				description: _('Stop editing this portal'),
				callback: lang.hitch(this, function() {
					this._refresh(portalTools.RenderMode.NORMAL);
					if (closeButton.focusNode.blur) {
						closeButton.focusNode.blur();
					}
				})
			});
			toolbar.addChild(entryOrderButton);
			toolbar.addChild(visibilityButton);
			toolbar.addChild(appearanceButton);
			toolbar.addChild(closeButton);

			//
			var dndbar = new ContainerWidget({
				'class': 'portalEntryOrderBar'
			});
			var cancelEntryOrderButton = new _Button({
				label: _('Cancel'),
				'class': 'portalEntryOrderBarCancelButton',
				callback: lang.hitch(this, function() {
					this._render(portalTools.RenderMode.EDIT);
				})
			});
			var saveEntryOrderButton = new _Button({
				label: _('Save entry order'),
				'class': 'portalEntryOrderBarSaveButton',
				callback: lang.hitch(this, function() {
					this.saveEntryOrder();
				})
			});
			dndbar.addChild(cancelEntryOrderButton);
			dndbar.addChild(saveEntryOrderButton);

			//
			put(dom.byId('portal'), toolbar.domNode);
			put(dom.byId('portal'), dndbar.domNode);
		},

		_render: function(renderMode) {
			this._renderMode = renderMode;
			this._cleanupPreviousRender();
			this._updateCssClassForCurrentRenderMode(renderMode);
			this._renderHeader(renderMode);
			this._renderContent(renderMode);
			this._updateSearch(renderMode);

			this._rearrangeCategories();
		},

		_cleanupPreviousRender: function() {
			while (this._cleanupList.handlers.length) {
				this._cleanupList.handlers.pop().remove();
			}
			while (this._cleanupList.widgets.length) {
				var widget = this._cleanupList.widgets.pop();
				if (widget.destroyRecursive) {
					widget.destroyRecursive();
				} else if (widget.destroy) {
					widget.destroy();
				}
			}
			this._globalEntryIndex = 0;
			this._categoryIndex = 0;
			this._portalCategories = [];
		},

		_updateCssClassForCurrentRenderMode: function(renderMode) {
			tools.forIn(portalTools.RenderMode, function(renderMode, name) {
				domClass.remove(dom.byId('portal'), name);
			});
			domClass.add(dom.byId('portal'), renderMode);
		},

		_renderHeader: function(renderMode) {
			domClass.remove(dom.byId('umcHeaderRight'), 'dijitDisplayNone');

			// font color
			domClass.toggle(dom.byId('umcHeader'), 'umcWhiteIcons', lang.getObject('portal.fontColor', false, portalJson) === 'white');

			// logo
			var logoSrc = portalJson.portal.logo ? lang.replace('{0}?{1}', [portalJson.portal.logo, Date.now()]) : '/univention/portal/portal-logo-dummy.svg';
			dom.byId('portalLogo').src = logoSrc;

			// title
			var portalName = lang.replace(portalJson.portal.name[locale] || portalJson.portal.name.en_US || '', tools._status);
			dom.byId('portalTitle').innerHTML = portalName;
			document.title = portalName;

			switch (renderMode) {
				case portalTools.RenderMode.DND:
				case portalTools.RenderMode.NORMAL:
					domClass.toggle(dom.byId('portalLogo'), 'dijitDisplayNone', !portalJson.portal.logo);
					break;
				case portalTools.RenderMode.EDIT:
					domClass.remove(dom.byId('portalLogo'), 'dijitDisplayNone');
					this._registerEventHandlerForHeader();
					break;
			}
		},

		_registerEventHandlerForHeader: function() {
			var editPortalLogo = lang.hitch(this, function() {
				this._editProperties('settings/portal', portalJson.portal.dn, ['logo'], _('Portal logo'));
			});
			this._cleanupList.handlers.push(
				on(dom.byId('portalLogoEdit'), 'click', editPortalLogo)
			);
			this._cleanupList.handlers.push(
				on(dom.byId('portalLogo'), 'click', editPortalLogo)
			);

			this._cleanupList.handlers.push(
				on(dom.byId('portalTitle'), 'click', lang.hitch(this, function() {
					this._editProperties('settings/portal', portalJson.portal.dn, ['displayName'], _('Portal title'));
				}))
			);
		},

		_renderContent: function(renderMode) {
			this._renderCategories(renderMode);
			if (renderMode === portalTools.RenderMode.EDIT) {
				this._renderAddCategoryButton();
			}
		},

		_renderCategories: function(renderMode) {
			var categories = this._getCategories(renderMode);

			domClass.toggle(this._search.domNode, 'dijitDisplayNone', !categories.length);
			if (!categories.length && !tools.status('loggedIn')) {
				this._renderAnonymousEmptyMessage();
				return;
			}

			if (!tools.status('loggedIn')) {
				registry.byId('umcLoginButton').emphasise();
			}

			switch (renderMode) {
				case portalTools.RenderMode.NORMAL:
				case portalTools.RenderMode.EDIT:
					categories.forEach(lang.hitch(this, function(category) {
						var portalCategory = this._renderCategory(category, renderMode);
						this._contentNode.appendChild(portalCategory.domNode);
					}));
					break;
				case portalTools.RenderMode.DND:
					this._createDndSource();
					this.dndSource.insertNodes(false, categories);
					break;
			}
			this._portalCategories.forEach(function(portalCategory) {
				portalCategory.startup();
			});
		},

		_renderAnonymousEmptyMessage: function() {
			var loginButton = new Button({
				'class': 'anonymousEmpty__Login umcFlatButton',
				label: _('Login'),
				callback: function() {
					login.start();
				}
			});
			var text = put('div.anonymousEmpty__Text');
			var defaultText = _('Welcome to the portal of %s.<br><br>To be able to use all functions of this portal, please log in.', window.location.hostname);
			text.innerHTML = purify.sanitize(portalJson.portal.anonymousEmpty[locale] || portalJson.portal.anonymousEmpty.en_US || defaultText);
			put(this._contentNode, 'div.anonymousEmpty', text, '< div.anonymousEmpty__ButtonRow', loginButton.domNode);
		},

		_getCategories: function(renderMode) {
			var categories = [];

			if (renderMode === portalTools.RenderMode.NORMAL && portalJson.portal.showApps) {
				var entries = this._getEntries(installedApps, renderMode);
				if (entries.length) {
					categories.push({
						heading: _('Local Apps'),
						entries: entries,
						dn: 'localApps',
						renderMode: renderMode
					});
				}
			}

			array.forEach(portalJson.portal.content, lang.hitch(this, function(category) {
				var categoryDN = category[0];
				var entryDNs = category[1];
				category = portalJson.categories[categoryDN];
				if (!category) {
					categories.push({
						$notInPortalJSON$: true,
						heading: '',
						entries: this._getEntries(entryDNs, renderMode),
						dn: categoryDN,
						renderMode: renderMode
					});
				} else {
					var entries = this._getEntries(entryDNs, renderMode);
					var heading = category.display_name[locale] || category.display_name.en_US;
					categories.push({
						$notInPortalJSON$: false,
						heading: category.display_name[locale] || category.display_name.en_US,
						entries: this._getEntries(entryDNs, renderMode),
						dn: categoryDN,
						renderMode: renderMode
					});
				}
			}));

			return categories;
		},

		_getEntries: function(entries, renderMode) {
			entries = this._sanitizeEntries(entries);
			entries = this._filterEntries(entries, renderMode);
			entries = this._prepareEntriesForPortalGallery(entries, renderMode);
			return entries;
		},

		_sanitizeEntries: function(entries) {
			return entries.map(function(entry) {
				if (typeof entry === 'string') {
					entry = portalJson.entries[entry] || {
						$notInPortalJSON$: true,
						dn: entry
					};
				}
				return entry;
			});
		},

		_filterEntries: function(entries, renderMode) {
			return entries.filter(function(entry) {
				if (renderMode === portalTools.RenderMode.NORMAL) {
					if (entry.$notInPortalJSON$) {
						return false;
					}
				}
				return true;
			});
		},

		_prepareEntriesForPortalGallery: function(entries, renderMode) {
			var localEntryIndex = 0;
			entries = entries.map(lang.hitch(this, function(entry) {
				if (entry.$notInPortalJSON$) {
					return {
						dn: entry.dn,
						id: (this._globalEntryIndex++).toString() + '_$entryNotInPortalJSON$',
						index: localEntryIndex++
					};
				}

				var linkAndHostname = getBestLinkAndHostname(entry.links);
				return {
					name: entry.name[locale] || entry.name.en_US,
					dn: entry.dn,
					// We need globally unique id for portalTools.RenderMode.DND
					// so that we can drag an entry to a different category without
					// an id collision
					id: (this._globalEntryIndex++).toString() + '_' + entry.dn,
					// We need the index of an entry within a category for portalTools.RenderMode.EDIT.
					// We can't identify the correct portalJson.portal.content position with only
					// the dn of the entry since an entry can be in the same category multiple times.
					index: localEntryIndex++,
					description: entry.description[locale] || entry.description.en_US,
					logo_name: _getLogoName(entry.logo_name),
					web_interface: linkAndHostname.link,
					host_name: linkAndHostname.hostname,
					activated: entry.activated,
					linkTarget: entry.linkTarget,
				};
			}));
			if (renderMode === portalTools.RenderMode.EDIT) {
				entries.push({
					id: '$addEntryTile$'
				});
			}
			return entries;
		},

		_updateSearch: function(renderMode) {
			this._search.set('disabled', renderMode === portalTools.RenderMode.DND);
			switch (renderMode) {
				case portalTools.RenderMode.NORMAL:
				case portalTools.RenderMode.EDIT:
					this._search.set('value', this._lastSearch);
					this._search.expandSearch();
					this._search.focus();
					this._search.search();
					break;
				case portalTools.RenderMode.DND:
					this._search.set('value', '');
					this._search.collapseSearch();
					break;
			}
		},

		_createDndSource: function() {
			put(this._contentNode, '.dojoDndSource_PortalCategories');
			this.dndSource = new Source(this._contentNode, {
				copyState: function() {
					return false; // do not allow copying
				},
				type: ['PortalCategories'],
				accept: ['PortalCategory'],
				withHandles: true,
				creator: lang.hitch(this, function(item, hint) {
					var portalCategory = this._renderCategory(item, item.renderMode);

					if (hint === 'avatar') {
						return { node: portalCategory.domNode }; 
					}

					return {
						node: portalCategory.domNode,
						data: item,
						type: ['PortalCategory']
					};
				})
			});

			var onDndStartHandler = aspect.after(this.dndSource, 'onDndStart', lang.hitch(this, function(source) {
				if (source === this.dndSource) {
					dojoQuery('.dojoDndItem_dndCover', this._contentNode).removeClass('dijitDisplayNone');
				}
			}), true);
			var onDndCancelHandler = aspect.after(this.dndSource, 'onDndCancel', lang.hitch(this, function() {
				dojoQuery('.dojoDndItem_dndCover', this._contentNode).addClass('dijitDisplayNone');
			}));

			this._cleanupList.widgets.push(this.dndSource);
			this._cleanupList.handlers.push(onDndStartHandler);
			this._cleanupList.handlers.push(onDndCancelHandler);
		},

		_addLinks: function() {
			var links = portalJson.links;
			if (! links) {
				return;
			}
			array.forEach(links.footer, function(link) {
				if (link.locale != locale) {
					return;
				}
				var name = link.name;
				var a = put(dom.byId('portal-footer'), 'a', name);
				a.href = link.href;
			});
		},

		saveEntryOrder: function() {
			var newContent = [];
			this.dndSource.getAllNodes().forEach(lang.hitch(this, function(portalCategoryNode) {
				var portalCategory = dijit.byId(domAttr.get(portalCategoryNode, 'widgetId'));
				var portalEntries = array.map(portalCategory.grid.dndSource.getAllNodes(), function(portalEntryNode) {
					var portalEntryItem = portalCategory.grid.dndSource.getItem(portalEntryNode.id);
					return portalEntryItem.data.dn;
				});
				newContent.push([portalCategory.category, portalEntries]);
			}));

			this._saveEntryOrder(newContent);
		},

		_saveEntryOrder: function(newContent) {
			if (tools.isEqual(portalJson.portal.content, newContent)) {
				return;
			}

			this._standby.show();
			this._moduleStore.put({
				'$dn$': portalJson.portal.dn,
				content: newContent
			}).then(lang.hitch(this, function(result) {
				if (result.success) {
					this._refresh(portalTools.RenderMode.EDIT).then(lang.hitch(this, function() {
						this._standby.hide();
						dialog.contextNotify(_('Changes saved'));
					}));
				} else {
					this._render(portalTools.RenderMode.EDIT);
					this._standby.hide();
					dialog.alert(_('Saving entry order failed'));
				}
			}));
		},

		filterPortal: function() {
			var searchPattern = lang.trim(this._search.get('value'));
			var searchQuery = this._search.getSearchQuery(searchPattern);

			var query = function(app) {
				return app.id === '$addEntryTile$' || searchQuery.test(app);
			};

			array.forEach(this._portalCategories, function(category) {
				category.set('query', query);
			});

			this._rearrangeCategories();

			this._lastSearch = searchPattern;
		},

		_rearrangeCategories: function() {
			if (!portalJson.portal.autoLayoutCategories) {
				return;
			}
			if (!this._portalCategories.length) {
				return;
			}

			// reset previous _rearrangeCategories
			this._portalCategories.forEach(function(category) {
				domStyle.set(category.domNode, 'display', 'block');
				domStyle.set(category.domNode, 'width', '');
				domStyle.set(category.domNode, 'margin-right', '');
			});

			if (this._renderMode === portalTools.RenderMode.DND) {
				return;
			}

			window.requestAnimationFrame(lang.hitch(this, function() {
				var winBox = win.getBox();
				if (winBox.w <= 549) {
					// we are in the mobile view. returning
					return;
				}

				var bodyBox = domGeometry.getContentBox(dojo.body());
				if (bodyBox.h === winBox.h) {
					// there is no scrollbar, so no rearrange necassary
					return;
				}

				var contentBox = domGeometry.getContentBox(this._contentNode);
				var availableHeight = winBox.h - contentBox.t;
				var itemWidth = 155;
				var itemMarginWidth = 40;
				var itemWidthPlusMargin = itemWidth + itemMarginWidth;
				var minMarginBetweenCategories = 40;
				var maxColumns = 2;

				var tilesWidth = function(n) {
					return (n * itemWidthPlusMargin) - itemMarginWidth;
				};
				var categoryWidth = function(c) {
					var width = tilesWidth(c.getRenderedTiles().length);
					var headerWidth = Math.ceil(domGeometry.getMarginSize(c.headingNode).w);
					if (headerWidth > width) {
						var nextFittingWidthToGrid = (Math.ceil((headerWidth + itemMarginWidth) / itemWidthPlusMargin) * itemWidthPlusMargin) - itemMarginWidth;
						width = nextFittingWidthToGrid;
					}
					return width;
				};

				var getRows = lang.hitch(this, function() {
					var rows = [];
					var rowsi = 0;
					var row;

					this._portalCategories.forEach(function(c) {
						if (!c.get('visible')) {
							return;
						}

						row = rows[rowsi] = rows[rowsi] || [];
						var widthAvailable = contentBox.w;
						row.forEach(function(cir) {
							widthAvailable -= cir.w + minMarginBetweenCategories;
						});

						var w = categoryWidth(c);
						var fits = w <= widthAvailable;
						var r = widthAvailable - w;

						if (!fits && row.length > 0) {
							rowsi++;
						}
						row = rows[rowsi] = rows[rowsi] || [];
						row.push({
							c: c,
							r: r,
							w: w,
							h: domGeometry.getMarginBox(c.domNode).h
						});
						if (row.length === maxColumns) {
							rowsi++;
						}
					});

					return rows;
				});

				var isDone = function() {
					var heightTaken = 0;
					rows.forEach(function(row) {
						heightTaken += row[0].h;
					});

					if (heightTaken > availableHeight) {
						var layout = '';
						rows.forEach(function(row) {
							layout += row.length.toString();
						});
						if (layout !== lastLayout) {
							maxColumns++;
							lastLayout = layout;
						} else {
							return true;
						}
					} else {
						return true;
					}
					return false;
				};


				var lastLayout = '';
				var done = false;
				var rows;
				while (!done) {
					rows = getRows();
					done = isDone(rows);
				}

				rows.forEach(function(row) {
					if (row.length === 1) {
						return;
					}

					row.forEach(function(c, index) {
						domStyle.set(c.c.domNode, 'display', 'inline-block');
						domStyle.set(c.c.domNode, 'width', c.w + 'px');
						if (index === row.length - 1) {
							domStyle.set(c.c.domNode, 'margin-right', c.r + 'px');
						} else {
							domStyle.set(c.c.domNode, 'margin-right', minMarginBetweenCategories + 'px');
						}
					});
				});
			}));
		},

		_resizeDeferred: null,
		_handleWindowResize: function() {
			if (this._resizeDeferred && !this._resizeDeferred.isFulfilled()) {
				this._resizeDeferred.cancel();
			}

			this._resizeDeferred = tools.defer(lang.hitch(this, function() {
				this._rearrangeCategories();
			}), 200);

			this._resizeDeferred.otherwise(function() { /* prevent logging of exception */ });
		},

		// these functions are used in management/univention-portal/test/test.js
		getHighestRankedLink: getHighestRankedLink,
		canonicalizeIPAddress: canonicalizeIPAddress,
		getLocalLinks: getLocalLinks,
		getFQDNHostname: getFQDNHostname
	};
});
