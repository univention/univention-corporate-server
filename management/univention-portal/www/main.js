/*
 * Copyright 2016-2017 Univention GmbH
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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/Deferred",
	"dojo/aspect",
	"dojo/when",
	"dojo/on",
	"dojo/query",
	"dojo/dom",
	"dojo/dom-class",
	"dojo/dom-geometry",
	"dojo/dom-style",
	"dojo/mouse",
	"dojo/promise/all",
	"dojox/string/sprintf",
	"dojox/widget/Standby",
	"dojox/html/styles",
	"dijit/focus",
	"dijit/a11y",
	"dijit/registry",
	"dijit/Dialog",
	"dijit/Tooltip",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"umc/tools",
	"umc/store",
	"umc/json",
	"umc/dialog",
	"umc/dialog/NotificationSnackbar",
	"umc/widgets/Button",
	"umc/widgets/Form",
	"umc/widgets/Wizard",
	"umc/widgets/ContainerWidget",
	"umc/widgets/ConfirmDialog",
	"umc/widgets/StandbyMixin",
	"umc/widgets/MultiInput",
	"put-selector/put",
	"./PortalCategory",
	"./tools",
	"umc/i18n/tools",
	// portal.json -> contains entries of this portal as specified in the LDAP directory
	"umc/json!/univention/portal/portal.json",
	// apps.json -> contains all locally installed apps
	"umc/json!/univention/portal/apps.json",
	"umc/i18n!portal"
], function(declare, lang, array, Deferred, aspect, when, on, dojoQuery, dom, domClass, domGeometry, domStyle, mouse, all, sprintf, Standby, styles, dijitFocus, a11y, registry, Dialog, Tooltip, _WidgetBase, _TemplatedMixin, tools, store, json, dialog, NotificationSnackbar, Button, Form, Wizard, ContainerWidget, ConfirmDialog, StandbyMixin, MultiInput, put, PortalCategory, portalTools, i18nTools, portalContent, installedApps, _) {

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

	var _PortalPropertiesDialog = declare('PortalPropertiesDialog', [ConfirmDialog, StandbyMixin]);
	var _WizardDialog = declare('WizardDialog', [Dialog, StandbyMixin]);

	var PortalEntryWizard = declare('PortalEntryWizard', [Wizard], {
		'class': 'portalEntryWizard',

		pageMainBootstrapClasses: 'col-xxs-12 col-xs-8',

		portalEntryProps: null,
		_getProps: function(id) {
			return array.filter(this.portalEntryProps, function(iProp) {
				return iProp.id === id;
			})[0];
		},

		postMixInProperties: function() {
			this.inherited(arguments);
			this.initialFormValues = {};
			this.dn = null;

			lang.mixin(this, {
				pages: [{
					name: 'name',
					widgets: [this._getProps('name')],
					layout: ['name'],
					headerText: ' ' // FIXME hacky workaround to get 'nav' to show so that Page.js adds the mainBootstrapClasses to 'main'
					// helpText: 'TODO',
					// helpTextRegion: 'main'
				}, {
					name: 'icon',
					widgets: [this._getProps('icon')],
					layout: ['icon'],
					headerText: ' '
					// helpText: 'TODO',
					// helpTextRegion: 'main'
				}, {
					name: 'displayName',
					widgets: [this._getProps('displayName')],
					layout: ['displayName'],
					headerText: ' '
					// helpText: 'TODO',
					// helpTextRegion: 'main'
				}, {
					name: 'link',
					widgets: [this._getProps('link')],
					layout: ['link'],
					headerText: ' '
					// helpText: 'TODO',
					// helpTextRegion: 'main'
				}, {
					name: 'description',
					widgets: [this._getProps('description')],
					layout: ['description'],
					headerText: ' '
					// helpText: 'TODO',
					// helpTextRegion: 'main'
				}]
			})
		},

		buildRendering: function() {
			this.inherited(arguments);

			// set the value of the displayName and description widget to
			// have the available languages (the ones that are available in the menu)
			// prefilled and do not allow the user to add or remove rows for languages
			var availableLanguageCodes = array.map(i18nTools.availableLanguages, function(ilanguage) {
				return ilanguage.id.replace(/-/, '_');
			});
			// shift current locale to the beginning
			availableLanguageCodes.splice(0, 0, availableLanguageCodes.splice(availableLanguageCodes.indexOf(locale), 1)[0]);

			var localizedPrefillValues = [];
			array.forEach(availableLanguageCodes, function(ilanguageCode) {
				localizedPrefillValues.push([ilanguageCode, '']);
			});
			array.forEach(['displayName', 'description'], lang.hitch(this, function(iname) {
				domClass.add(this.getWidget(iname).domNode, 'noRemoveButton');
				this.getWidget(iname).set('max', localizedPrefillValues.length);
				this.getWidget(iname).set('value', localizedPrefillValues);
				this.getWidget(iname).ready().then(lang.hitch(this, function() {
					array.forEach(this.getWidget(iname)._widgets, function(iwidget) {
						// disable the textbox for the language code
						iwidget[0].set('disabled', true);
					});
				}));
			}));

			// set initialFormValues
			array.forEach(this.pages, lang.hitch(this, function(ipage) {
				array.forEach(ipage.widgets, lang.hitch(this, function(iwidgetConf) {
					var widget = this.getWidget(iwidgetConf.id);
					var widgetReady = widget.ready ? widget.ready() : true;
					when(widgetReady).then(lang.hitch(this, function() {
						this.initialFormValues[iwidgetConf.id] = widget.get('value');
					}));
				}));
			}));
		},

		switchPage: function(pageName) {
			var scrollY = window.scrollY;
			this.inherited(arguments);
			window.scrollTo(0, scrollY);
		},

		getFooterButtons: function(pageName) {
			var footerbuttons = [{
				name: 'remove',
				label: _('Remove from this portal'),
				align: 'right',
				callback: lang.hitch(this, 'onRemove')
			}, {
				name: 'previous',
				label: _('Back'),
				align: 'right',
				callback: lang.hitch(this, '_previous', pageName)
			}, {
				name: 'next',
				align: 'right',
				label: _('Next'),
				callback: lang.hitch(this, '_next', pageName)
			}, {
				name: 'cancel',
				label: _('Cancel'),
				callback: lang.hitch(this, 'onCancel')
			}, {
				name: 'save',
				defaultButton: true,
				label: _('Save'),
				callback: lang.hitch(this, '_finish', pageName)
			}, {
				name: 'finish',
				defaultButton: true,
				label: _('Finish'),
				callback: lang.hitch(this, '_finish', pageName)
			}];

			return footerbuttons;
		},

		_updateButtons: function(pageName) {
			this.inherited(arguments);
			var buttons = this._pages[pageName]._footerButtons;
			if (buttons.next) {
				domClass.toggle(buttons.next.domNode, 'dijitDefaultButton', !this.dn || (this.dn && pageName === 'name') ? true : false);
			}
			if (buttons.remove) {
				domClass.toggle(buttons.remove.domNode, 'dijitDisplayNone', this.dn && pageName === 'name' ? false : true);
			}
			if (buttons.finish) {
				domClass.toggle(buttons.finish.domNode, 'dijitDisplayNone', this.dn ? true : false || this.hasNext(pageName));
			}
			if (buttons.save) {
				domClass.toggle(buttons.save.domNode, 'dijitDisplayNone', this.dn && pageName !== 'name' ? false : true);
			}
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

		__validateWidget: function(widget) {
			if (widget instanceof MultiInput) {
				// FIXME the MultiInput widget does not implement validate.
				// this goes trough all widgets in all rows and validates them
				// so that the tooltip with the error message is shown.
				var i, j;
				for (i = 0; i < widget._widgets.length; ++i) {
					for (j = 0; j < widget._widgets[i].length; ++j) {
						var iwidget = widget._widgets[i][j];
						if (!iwidget.get('visible')) {
							// ignore hidden widgets
							continue;
						}
						iwidget._hasBeenBlurred = true;
						if (iwidget.validate !== undefined) {
							if (iwidget._maskValidSubsetError !== undefined) {
								iwidget._maskValidSubsetError = false;
							}
							iwidget.validate();
						}
					}
				}
			} else {
				widget.validate();
			}
		},

		_validatePage: function(pageName) {
			var deferred = new Deferred();
			var firstInvalidWidget = null;
			var initialFormValues = this.initialFormValues;
			var form = this.getPage(pageName)._form;
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

			var alteredValuesNonEmpty = {};
			tools.forIn(alteredValues, function(iname, ivalue) {
				if (!this._isEmptyValue(ivalue)) {
					alteredValuesNonEmpty[iname] = ivalue;
				}
			}, this);

			// reset validation settings from last validation
			tools.forIn(form._widgets, function(iname, iwidget) {
				if (iwidget.setValid) {
					iwidget.setValid(null);
				}
			});
			form.validate(); // validate all widgets to mark invalid/required fields

			// see if there are widgets that are required and have no value
			var allValid = true;
			tools.forIn(form._widgets, function(iname, iwidget) {
				var isEmpty = this._isEmptyValue(iwidget.get('value'));
				if (iwidget.required && isEmpty) {
					allValid = false;
					iwidget.setValid(false, _('This value is required'));
				} else if (!isEmpty && iwidget.isValid && !iwidget.isValid()) {
					allValid = false;
				}

				this.__validateWidget(iwidget);
				if (!allValid && !firstInvalidWidget && a11y.getFirstInTabbingOrder(iwidget.domNode)) {
					firstInvalidWidget = iwidget;
				}
			}, this);
			if (!allValid) {
				deferred.reject(firstInvalidWidget);
				return deferred;
			}

			// validate the form values
			tools.umcpCommand('udm/validate', {
				objectType: 'settings/portal_entry',
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
					this.__validateWidget(widget);
					if (!allValid && !firstInvalidWidget && a11y.getFirstInTabbingOrder(widget.domNode)) {
						firstInvalidWidget = widget;
					}
				}));
				if (!allValid) {
					deferred.reject(firstInvalidWidget);
				} else {
					deferred.resolve();
				}
			}));
			return deferred;
		},

		loadEntry: function(dn) {
			var deferred = new Deferred();
			this.moduleStore.get(dn).then(lang.hitch(this, function(result) {
				this.dn = dn;
				this.loadedEntryPortals = result['portal'] || [];
				this.onLoadEntry();
				//// populate all widgets with the loaded portal entry data
				//// and store the initial form values
				array.forEach(this.pages, lang.hitch(this, function(ipage) {
					array.forEach(ipage.widgets, lang.hitch(this, function(iwidgetConf) {
						if (result[iwidgetConf.id]) {
							this.getWidget(iwidgetConf.id).set('value', result[iwidgetConf.id]);
							this.initialFormValues[iwidgetConf.id] = result[iwidgetConf.id];
						}
					}));
				}));

				//// we only want to show languages that are visible in the menu.
				//// seperate languages that are in the menu and other lanuages and
				//// merge them back when saving
				var availableLanguageCodes = array.map(i18nTools.availableLanguages, function(ilanguage) {
					return ilanguage.id.replace(/-/, '_');
				});
				// shift current locale to the beginning
				availableLanguageCodes.splice(0, 0, availableLanguageCodes.splice(availableLanguageCodes.indexOf(locale), 1)[0]);

				array.forEach(['displayName', 'description'], lang.hitch(this, function(iname) {
					var filteredName = [];
					array.forEach(availableLanguageCodes, lang.hitch(this, function(ilanguageCode) {
						var name = array.filter(this.initialFormValues[iname], function(iname) {
							return iname[0] === ilanguageCode;
						})[0];
						if (!name) {
							name = [ilanguageCode, ''];
						}
						filteredName.push(name);
					}));
					var remainingName = array.filter(this.initialFormValues[iname], function(iname) {
						return array.indexOf(availableLanguageCodes, iname[0]) === -1;
					});

					this.initialFormValues[iname] = filteredName;
					this.initialFormValues[iname + '_remaining'] = remainingName;

					this.getWidget(iname).set('value', filteredName);
				}));

				this.onEntryLoaded();
				this._updateButtons(this.selectedChildWidget.name);
				deferred.resolve();
			}));

			return deferred;
		},
		onLoadEntry: function() {
			// event stub
		},
		onEntryLoaded: function() {
			// event stub
		},
		onNameQuery: function() {
			// event stub
		},
		onNameQueryEnd: function() {
			// event stub
		},

		_next: function(currentPage) {
			if (!currentPage) {
				this.inherited(arguments);
			} else {
				var origArgs = arguments;
				this._validatePage(currentPage).then(lang.hitch(this, function() {
					if (currentPage === 'name') {
						var enteredName = this.getWidget('name').get('value');
						this.onNameQuery();
						this.moduleStore.query({
							'objectProperty': 'name',
							'objectPropertyValue': enteredName
						}).then(lang.hitch(this, function(result) {
							if (!result.length) {
								this.inherited(origArgs);
								this.onNameQueryEnd();
							} else {
								var entryToLoad = array.filter(result, function(ientry) {
									return ientry.name === enteredName;
								})[0];
								if (!entryToLoad || (entryToLoad && this.dn && this.dn === entryToLoad['$dn$'])) {
									this.inherited(origArgs);
									this.onNameQueryEnd();
								} else {
									dialog.confirm('A portal entry with the given name already exists.', [{
										'name': 'cancel',
										'label': _('Cancel'),
										'default': true
									}, {
										'name': 'load',
										'label': _('Load entry')
									}]).then(lang.hitch(this, function(choice) {
										if (choice === 'load') {
											this.loadEntry(entryToLoad['$dn$']).then(lang.hitch(this, function() {
												// if we load an existing portal entry we want to save the
												// portal and category attribute on the portal entry object
												// even if none of the loaded form values (e.g. displayName)
												// have changed.
												this._forceSave = true;
												this.inherited(origArgs);
											}));
										} else {
											this.onNameQueryEnd();
										}
									}));
								}
							}
						}));
					} else {
						this.inherited(origArgs);
					}
				}), function(firstInvalidWidget) {
					dijitFocus.focus(a11y.getFirstInTabbingOrder(firstInvalidWidget.domNode));
				});
			}
		},

		_finish: function(currentPage) {
			var origArgs = arguments;
			this._validatePage(currentPage).then(lang.hitch(this, function() {
				if (this.dn) {
					this.onSave(this.getValues());
				} else {
					this.onFinished(this.getValues());
				}
			}), function(firstInvalidWidget) {
				dijitFocus.focus(a11y.getFirstInTabbingOrder(firstInvalidWidget.domNode));
			});
		},

		onSave: function(values) {
			// event stub
		},

		onRemove: function() {
			// stub
		}
	});

	var PortalEntryWizardPreviewTile = declare('Tile', [_WidgetBase, _TemplatedMixin], {
		templateString: '' +
			'<div class="previewTile umcAppGallery col-xs-4" data-dojo-attach-point="domNode">' +
				'<div class="umcGalleryWrapperItem" data-dojo-attach-point="wrapperNode">' +
					'<div class="cornerPiece boxShadow bl">' +
						'<div class="hoverBackground"></div>' +
					'</div>' +
					'<div class="cornerPiece boxShadow tr">' +
						'<div class="hoverBackground"></div>' +
					'</div>' +
					'<div class="cornerPiece boxShadowCover bl"></div>' +
					'<div class="appIcon umcGalleryIcon" data-dojo-attach-point="iconNode">' +
						'<img data-dojo-attach-point="imgNode"/>' +
					'</div>' +
					'<div class="appInnerWrapper umcGalleryItem">' +
						'<div class="contentWrapper">' +
							'<div class="appContent">' +
								'<div class="umcGalleryName" data-dojo-attach-point="displayNameWrapperNode">' +
									'<div class="umcGalleryNameContent" data-dojo-attach-point="displayNameNode"></div>' +
								'</div>' +
								'<div class="umcGallerySubName" data-dojo-attach-point="linkNode"></div>' +
							'</div>' +
							'<div class="appHover">' +
								'<div data-dojo-attach-point="descriptionNode"></div>' +
							'</div>' +
						'</div>' +
					'</div>' +
				'</div>' +
			'</div>',

		currentPageClass: null,
		_setCurrentPageClassAttr: function(page) {
			domClass.toggle(this.wrapperNode, 'hover', page === 'description');
			domClass.replace(this.domNode, page, this.currentPageClass);
			this._set('currentPageClass', page);
		},

		icon: null,
		_setIconAttr: function(iconUri) {
			this.imgNode.src = iconUri;
			domClass.toggle(this.iconNode, 'iconLoaded', iconUri);
			this._set('icon', iconUri);
		},

		displayName: null,
		_setDisplayNameAttr: function(displayName) {
			this.set('displayNameClass', displayName ? 'hasName': null);
			this.displayNameNode.innerHTML = displayName;
			this._set('displayName', displayName);
		},
		displayNameClass: null,
		_setDisplayNameClassAttr: { node: 'displayNameWrapperNode', type: 'class' },

		link: null,
		_setLinkAttr: function(link) {
			this.set('linkClass', link ? 'hasLink' : null);
			this.linkNode.innerHTML = link;
			this._set('link', link);
		},
		linkClass: null,
		_setLinkClassAttr: { node: 'linkNode', type: 'class' },

		description: null,
		_setDescriptionAttr: function(description) {
			this.set('descriptionClass', description ? 'hasDescription' : null)	;
			this.descriptionNode.innerHTML = description;
			this._set('description', description);
		},
		descriptionClass: null,
		_setDescriptionClassAttr: { node: 'descriptionNode', type: 'class' }
	});

	// adjust white styling of header via extra CSS class
	if (lang.getObject('portal.fontColor', false, portalContent) === 'white') {
		try {
			domClass.add(dom.byId('umcHeader'), 'umcWhiteIcons');
		} catch(err) { }
	}

	// remove display=none from header
	try {
		domClass.remove(dom.byId('umcHeaderRight'), 'dijitDisplayNone');
	} catch(err) { }

	var locale = i18nTools.defaultLang().replace(/-/, '_');
	return {
		portalCategories: null,
		editMode: false,

		_initStyling: function() {
			on(dom.byId('portalLogo'), 'click', lang.hitch(this, function() {
				if (!this.editMode) {
					return;
				}

				this._editPortalProperties(['logo'], _('Portal logo'));
			}));
			on(dom.byId('portalTitle'), 'click', lang.hitch(this, function() {
				if (!this.editMode) {
					return;
				}

				this._editPortalProperties(['displayName'], _('Portal title'));
			}));
			this._portalLogoTooltip = new Tooltip({
				label: _('Portal logo'),
				connectId: [dom.byId('portalLogo')],
				position: ['below']
			});
			this._portalTitleTooltip = new Tooltip({
				label: _('Portal title'),
				connectId: [dom.byId('portalTitle')],
				position: ['below']
			});
		},

		_updateStyling: function() {
			// update global class for edit mode
			domClass.toggle(dom.byId('portal'), 'editMode', this.editMode);

			// update title
			var portal = portalContent.portal;
			var title = dom.byId('portalTitle');
			var portalName = lang.replace(portal.name[locale] || portal.name.en_US || '', tools._status);
			title.innerHTML = portalName;
			document.title = portalName;

			// update custom logo
			var logoNode = dom.byId('portalLogo');
			// FIXME? instead of reloading the portal logo,
			// use styles.insertCssRule to display the style
			// changes made after the first site load
			logoNode.src = portal.logo ? lang.replace('{0}?{1}', [portal.logo, Date.now()]) : '/univention/portal/portal-logo-dummy.svg';
			domClass.toggle(logoNode, 'dijitDisplayNone', (!portal.logo && !this.editMode));

			// update header tooltips
			this._portalLogoTooltip.set('connectId', (this.editMode ? dom.byId('portalLogo') : [] ));
			this._portalTitleTooltip.set('connectId', (this.editMode ? dom.byId('portalTitle') : [] ));

			// update color of header icons
			domClass.toggle(dom.byId('umcHeader'), 'umcWhiteIcons', lang.getObject('portal.fontColor', false, portalContent) === 'white');
		},

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
		_reloadPortalContent: function() {
			var loadDeferred = new Deferred();
			var counter = 0;

			var _load = function() {
				json.load('/univention/portal/portal.json', require, function(result) {
					if (++counter >= 3) {
						loadDeferred.resolve();
						return;
					}
					if (result && result.portal && result.entries) {
						if (tools.isEqual(result, portalContent)) {
							_load();
						} else {
							portalContent = result;
							loadDeferred.resolve();
						}
					} else {
						_load();
					}
				});
			};

			_load();
			return loadDeferred;
		},

		_refreshAfterPortalEdit: function() {
			var deferred = new Deferred();
			this._reloadPortalContent().then(lang.hitch(this, function() {
				this._updateStyling();
				this._reloadCss(); // FIXME only reload css if it is necessary (cssBackground / background / fontColor changed)
				deferred.resolve();
			}));
			return deferred;
		},

		_refreshAfterPortalEntryEdit: function() {
			var deferred = new Deferred();
			this._reloadPortalContent().then(lang.hitch(this, function() {
				array.forEach(this.portalCategories, function(iportalCategory) {
					iportalCategory.destroyRecursive();
				});
				this._createCategories();
				this._updateCategories();
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

		_editPortalProperties: function(propNames, dialogTitle) {
			// show standby animation
			var standbyWidget = this.standbyWidget;
			standbyWidget.show();
			var formDialog = null; // block scope variable

			// load all properties for a portal object
			this.moduleCache.getProperties('settings/portal', portalContent.portal.dn).then(lang.hitch(this, function(portalProps) {
				// filter all portal properties for the ones we want to edit
				var props = array.filter(lang.clone(portalProps), function(iprop) {
					return array.indexOf(propNames, iprop.id) >= 0;
				});
				var initialFormValues = {}; // set after form.load()

				// load the neccessary widgets to display the properties
				this._requireWidgets(props).then(lang.hitch(this, function() {
					props = this._prepareProps(props); // do this after requireWidgets because requireWidgets changes the type of the prop

					// create the form with the given properties
					var form = new Form({
						widgets: props,
						layout: propNames,
						moduleStore: this.moduleStore
					});

					// save altered values when form is submitted
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

						var alteredValuesNonEmpty = {};
						tools.forIn(alteredValues, function(iname, ivalue) {
							if (!this._isEmptyValue(ivalue)) {
								alteredValuesNonEmpty[iname] = ivalue;
							}
						}, this);

						// check if the values in the form have changed
						// and if not return and close without saving
						if (Object.keys(alteredValues).length === 0) {
							formDialog.close();
							return;
						}

						// reset validation settings from last validation
						tools.forIn(form._widgets, function(iname, iwidget) {
							if (iwidget.setValid) {
								iwidget.setValid(null);
							}
						});
						form.validate(); // validate all widgets to mark invalid/required fields

						// see if there are widgets that are required and have no value
						var allValid = true;
						tools.forIn(form._widgets, function(iname, iwidget) {
							var isEmpty = this._isEmptyValue(iwidget.get('value'));
							if (iwidget.required && isEmpty) {
								allValid = false;
								// TODO this is kind of doubled because form.validate()
								// is already called, but MultiInput widgets that are required
								// do not work correctly with validate
								iwidget.setValid(false, _('This value is required')); // TODO wording / translation
							} else if (!isEmpty && iwidget.isValid && !iwidget.isValid()) {
								allValid = false;
							}
						}, this);
						if (!allValid) {
							formDialog.standby(false);
							return;
						}

						// validate the form values
						tools.umcpCommand('udm/validate', {
							objectType: 'settings/portal',
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
								form._widgets[iprop.property].setValid(iprop.valid, iprop.details);
							}));
							if (!allValid) {
								formDialog.standby(false);
								return;
							}

							// save the altered values
							if (alteredValues.displayName) {
								alteredValues.displayName = alteredValues.displayName.concat(initialFormValues.displayName_remaining);
							}
							var putParams = lang.mixin(alteredValues, {
								'$dn$': portalContent.portal.dn
							});
							form.moduleStore.put(putParams).then(lang.hitch(this, function(result) {
								// see whether saving was successful
								if (result.success) {
									// everything ok, close dialog
									this._refreshAfterPortalEdit().then(function() {
										formDialog.hide().then(function() {
											formDialog.destroyRecursive();
											dialog.contextNotify(_('Changes saved'));
										});
									});
								} else {
									dialog.alert(_('The changes to the portal object could not be saved: %(details)s', result));
									formDialog.standby(false);
								}
							}), function() {
								dialog.alert(_('The changes to the portal object could not be saved'));
								formDialog.standby(false);
							});
						}));
					}));

					var formPreparationsDeferreds = [];
					form.startup();
					form.load(portalContent.portal.dn).then(function() {
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

							var formValuesAlteredDeferred = new Deferred();
							formPreparationsDeferreds.push(formValuesAlteredDeferred);
							if (initialFormValues.displayName) {
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
										formValuesAlteredDeferred.resolve();
									});
								}));
							} else {
								formValuesAlteredDeferred.resolve();
							}

							var portalComputersProp = array.filter(props, function(iprop) {
								return iprop.id === 'portalComputers';
							})[0];
							if (portalComputersProp) {
								form._widgets['portalComputers'].autoSearch = true;
							}

							// create dialog to show form
							all(formPreparationsDeferreds).then(function() {
								formDialog = new _PortalPropertiesDialog({
									'class': 'portalPropertiesDialog',
									closable: true, // so that the dialog is closable via esc key
									title: dialogTitle,
									message: form,
									options: [{
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
									}]
								});

								// go against the behaviour of ConfirmDialog to focus the confirm button
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

		_createCategories: function() {
			this.portalCategories = [];

			var portal = portalContent.portal;
			var entries = portalContent.entries;
			var protocol = window.location.protocol;
			var host = window.location.host;
			var isIPv4 = tools.isIPv4Address(host);
			var isIPv6 = tools.isIPv6Address(host);

			if (portal.showApps) {
				var apps = this._getApps(installedApps, locale, protocol, isIPv4, isIPv6);
				this._addCategory(_('Local Apps'), apps, 'localApps');
			}
			var userGroups = [];
			array.forEach(tools.status('userGroups'), function(group) {
				userGroups.push(group.toLowerCase());
			});
			array.forEach(['service', 'admin'], lang.hitch(this, function(category) {
				var categoryEntries = array.filter(entries, function(entry) {
					if (entry.category != category) {
						return false;
					}
					if (! entry.activated) {
						return false;
					}
					if (entry.user_group && userGroups.indexOf(entry.user_group.toLowerCase()) == -1) {
						return false;
					}
					if (!entry.portals || entry.portals.indexOf(portal.dn) == -1) {
						return false;
					}
					return true;
				});
				var apps = this._getApps(categoryEntries, locale, protocol, isIPv4, isIPv6);
				var heading;
				if (category === 'admin') {
					heading = _('Administration');
				} else if (category === 'service') {
					heading = _('Applications');
				}
				this._addCategory(heading, apps, category);
			}));
		},

		_getApps: function(categoryEntries, locale, protocol, isIPv4, isIPv6) {
			var apps = [];
			var appsMap = {};
			array.forEach(categoryEntries, function(entry) {
				var linkAndHostname = getBestLinkAndHostname(entry.links);
				var app = {
					name: entry.name[locale] || entry.name.en_US,
					dn: entry.dn,
					id: entry.dn,
					description: entry.description[locale] || entry.description.en_US,
					logo_name: _getLogoName(entry.logo_name),
					web_interface: linkAndHostname.link,
					host_name: linkAndHostname.hostname
				};
				apps.push(app);
			});
			var entryOrder = portalContent.portal.portalEntriesOrder;
			if (entryOrder.length) {
				var newapps = [];
				array.forEach(entryOrder, function() {
					newapps.push(null);
				});
				var remainingApps = [];
				array.forEach(apps, function(iapp) {
					var iappIndex = entryOrder.indexOf(iapp.dn);
					if (iappIndex >= 0) {
						newapps[iappIndex] = iapp;
					} else {
						remainingApps.push(iapp);
					}
				});
				newapps = array.filter(newapps, function(hasValue) {
					return hasValue;
				});
				newapps = newapps.concat(remainingApps);
				apps = newapps;
			}
			return apps;
		},

		_addCategory: function(heading, apps, category) {
			var portalCategory = new PortalCategory({
				heading: heading,
				apps: apps,
				domainName: tools.status('domainname'),
				useDnd: (category === 'service' || category === 'admin'),
				category: category
			});
			portalCategory.own(aspect.after(portalCategory.grid, 'onAddEntry', lang.hitch(this, function(category) {
				if (this.dndMode) {
					return;
				}
				this.editPortalEntry(category);
			}), true));
			portalCategory.own(aspect.after(portalCategory.grid, 'onEditEntry', lang.hitch(this, function(category, item) {
				if (this.dndMode) {
					return;
				}
				if (category === 'localApps') {
					dialog.alert(_('Local apps can not be edited'));
					return;
				}
				if (!item.dn) {
					dialog.alert(_('The dn for this entry could not be found'));
					return;
				}
				this.editPortalEntry(category, item.dn);
			}), true));
			this.content.appendChild(portalCategory.domNode);
			// resize the item names after adding the category to the site.
			// the grid items are already rendered at this point (by creating the portalCategory)
			// but they weren't in the dom tree yet
			portalCategory.grid._resizeItemNames();
			this.portalCategories.push(portalCategory);
		},

		// TODO copy pasted from udm/DetailPage.js
		_requireWidgets: function(properties) {
			var deferreds = [];

			// require MultiInput for multivalue properties that will
			// get rewritten by this._prepareProps()
			properties = lang.clone(properties); // clone beacuse properties is a reference to an array
			properties.push({ 'type': 'MultiInput' });

			// require the necessary widgets to display the given properties
			array.forEach(properties, function(prop) {
				if (typeof prop.type == 'string') {
					var path = prop.type.indexOf('/') < 0 ? 'umc/widgets/' + prop.type : prop.type;
					var errHandler;
					var deferred = new Deferred();
					var loaded = function() {
						deferred.resolve();
						errHandler.remove();
					};
					errHandler = require.on('error', loaded);
					require([path], loaded);
					deferreds.push(deferred);
				}
			});
			return all(deferreds);
		},

		editPortalEntry: function(category, dn) {
			var standbyWidget = this.standbyWidget;
			standbyWidget.show();
			var _initialDialogTitle = dn ? _('Edit entry') : _('Create entry');

			this.moduleCache.getProperties('settings/portal_entry').then(lang.hitch(this, function(portalEntryProps) {
				portalEntryProps = lang.clone(portalEntryProps);

				this._requireWidgets(portalEntryProps).then(lang.hitch(this, function() {
					portalEntryProps = this._prepareProps(portalEntryProps);
					var wizardWrapper = new ContainerWidget({});
					var tile = new PortalEntryWizardPreviewTile();
					var wizard = new PortalEntryWizard({
						portalEntryProps: portalEntryProps,
						moduleStore: this.moduleStore
					});

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
					})

					// add onChange listener for displayName and description
					// to update the preview tile if displayName or description
					// is changed
					var defaultValuesForResize = this.portalCategories[0].grid._getDefaultValuesForResize('.umcGalleryName');
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
							category: category,
							portal: [portalContent.portal.dn],
						});

						wizard.moduleStore.add(values, {
							objectType: 'settings/portal_entry'
						}).then(lang.hitch(this, function(result) {
							// see whether creating the portal entry was succesful
							if (result.success) {
								// everything ok, close the wizard
								this._refreshAfterPortalEntryEdit().then(function() {
									wizardDialog.hide().then(function() {
										wizardDialog.destroyRecursive();
										dialog.contextNotify('Portal entry was successfully created');
									});
								});
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

						// if the edited portal entry was not part of this portal before,
						// add it to this portal
						var portals = lang.clone(wizard.loadedEntryPortals);
						var entryIsPartOfPortal = array.some(portals, function(iportal) {
							return iportal === portalContent.portal.dn;
						});
						if (!entryIsPartOfPortal) {
							portals.push(portalContent.portal.dn);
						}

						// save changes
						var putParams = lang.mixin(alteredValues, {
							'$dn$': wizard.dn,
							category: category,
							portal: portals
						});
						wizard.moduleStore.put(alteredValues).then(lang.hitch(this, function(result) {
							// see whether creating the portal entry was succesful
							if (result.success) {
								// if the icon for the entry was changed we want a new iconClass
								// to display the new icon
								if (formValues.icon) {
									var entry = array.filter(portalContent.entries, function(ientry) {
										return ientry.dn === wizard.dn;
									})[0];
									if (entry) {
										portalTools.requestNewIconClass(entry.logo_name);
									}
								}

								// reload categories and close wizard dialog
								this._refreshAfterPortalEntryEdit().then(function() {
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
						});
					})));

					// remove portal entry object from this portal
					wizard.own(on(wizard, 'remove', lang.hitch(this, function() {
						wizardDialog.standby(true);

						var newPortals = array.filter(wizard.loadedEntryPortals, function(iportal) {
							return iportal !== portalContent.portal.dn;
						});
						wizard.moduleStore.put({
							'$dn$': wizard.dn,
							portal: newPortals
						}).then(lang.hitch(this, function(result) {
							if (result.success) {
								this._refreshAfterPortalEntryEdit().then(function() {
									wizardDialog.hide().then(function() {
										wizardDialog.destroyRecursive();
										dialog.contextNotify(_('Changes saved'));
									});
								});
							} else {
								dialog.alert(_('The entry could not be removed: %(details)s', result));
								wizardDialog.standby(false);
							}
						}));
					})));

					// create and show dialog with the wizard
					wizardWrapper.addChild(tile);
					wizardWrapper.addChild(wizard);

					var wizardDialog = null;
					var wizardReady = dn ? wizard.loadEntry(dn) : true;
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
						wizardDialog.startup();
						wizardDialog.show();
						standbyWidget.hide();
					});
				}));
			}));
		},

		start: function() {
			this.content = dom.byId('content');
			this.search = registry.byId('umcLiveSearch');
			this.search.on('search', lang.hitch(this, 'filterPortal'));
			this._setupEditMode();
			this._initStyling();
			this._updateStyling();
			this._createCategories();

			put(dojo.body(), new NotificationSnackbar({}).domNode);
		},

		_checkEditAuthorization: function() {
			var authDeferred = new Deferred();

			tools.umcpCommand('get/modules').then(function(result) {
				var isAuthorized = array.filter(result.modules, function(iModule) {
					return iModule.flavor === 'settings/portal_all';
				}).length >= 1;
				if (isAuthorized) {
					authDeferred.resolve();
				} else {
					authDeferred.reject();
				}
			});

			return authDeferred;
		},

		_setupEditMode: function() {
			this._checkEditAuthorization().then(lang.hitch(this, function() {
				// require cache only here because member servers and slaved do not have
				// the univention-management-console-module-udm installed
				require(['umc/modules/udm/cache'], lang.hitch(this, function(cache) {
					this.moduleCache = cache.get('settings/portal_all');
					this.moduleStore = store('$dn$', 'udm', 'settings/portal_all');

					// create standby widget that covers the whole screen when loading form dialogs
					this.standbyWidget = new Standby({
						target: dom.byId('portal'),
						zIndex: 100,
						image: require.toUrl("dijit/themes/umc/images/standbyAnimation.svg").toString(),
						duration: 200
					});
					put(dom.byId('portal'), this.standbyWidget.domNode);
					this.standbyWidget.startup();

					// create floating button to enter edit mode
					this.portalEditFloatingButton = put(dom.byId('portal'), 'div.portalEditFloatingButton div.icon <');
					// TODO is tooltip necessary? it is kind of unaesthetic
					new Tooltip({
						label: _("Edit this portal"),
						connectId: [this.portalEditFloatingButton],
						position: ['above']
					});
					on(this.portalEditFloatingButton, 'click', lang.hitch(this, 'setEditMode', true));

					// create toolbar at bottom to exit edit mode
					// and have options to edit portal properties
					this.portalEditBar = new ContainerWidget({
						'class': 'portalEditBar'
					});
					var entryOrderButton = new Button({
						iconClass: '',
						'class': 'portalEditBarEntryOrderButton umcFlatButton',
						description: _('Change order of portal entries via drag and drop'),
						// callback: lang.hitch(this, 'setDndMode', true)
						callback: lang.hitch(this, function() {
							saveEntryOrderButton.focus();
							entryOrderButton._tooltip.close();
							setTimeout(lang.hitch(this, function() {
								this.setDndMode(true);
							}), 200);
						})
					});
					var allocationButton = new Button({
						iconClass: '',
						'class': 'portalEditBarAllocationButton umcFlatButton',
						description: _('Portal visibility'),
						callback: lang.hitch(this, '_editPortalProperties', ['portalComputers'], _('Portal visibility'))
					});
					var headerButton = new Button({
						iconClass: '',
						'class': 'portalEditBarHeaderButton umcFlatButton',
						description: _('Portal header'),
						callback: lang.hitch(this, '_editPortalProperties', ['logo', 'displayName'], _('Portal header'))
					});
					var appearanceButton = new Button({
						iconClass: '',
						'class': 'portalEditBarAppearanceButton umcFlatButton',
						description: _('Portal appearance'),
						callback: lang.hitch(this, '_editPortalProperties', ['fontColor', 'background', 'cssBackground'], _('Portal appearance'))
					});
					var closeButton = new Button({
						iconClass: 'umcCrossIcon',
						'class': 'portalEditBarCloseButton umcFlatButton',
						callback: lang.hitch(this, 'setEditMode', false)
					});
					this.portalEditBar.addChild(entryOrderButton);
					this.portalEditBar.addChild(allocationButton);
					this.portalEditBar.addChild(headerButton);
					this.portalEditBar.addChild(appearanceButton);
					this.portalEditBar.addChild(closeButton);

					// create bar to save entry order and leave dnd mode
					this.portalEntryOrderBar = new ContainerWidget({
						'class': 'portalEntryOrderBar'
					});
					var cancelEntryOrderButton = new Button({
						label: _('Cancel'),
						'class': 'portalEntryOrderBarCancelButton umcFlatButton',
						callback: lang.hitch(this, function() {
							this.setDndMode(false);
						})
					});
					var saveEntryOrderButton = new Button({
						label: _('Save entry order'),
						'class': 'portalEntryOrderBarSaveButton umcFlatButton',
						callback: lang.hitch(this, function() {
							this.saveEntryOrder();
						})
					});
					this.portalEntryOrderBar.addChild(cancelEntryOrderButton);
					this.portalEntryOrderBar.addChild(saveEntryOrderButton);

					put(dom.byId('portal'), this.portalEditBar.domNode);
					put(dom.byId('portal'), this.portalEntryOrderBar.domNode);
				}));
			}));
		},

		setEditMode: function(active) {
			this.editMode = active;
			this._updateStyling();
			this._updateCategories();
		},

		setDndMode: function(active) {
			if (this.dndMode === active) {
				return;
			}

			var scrollY = window.scrollY;
			this.dndMode = active;
			domClass.toggle(dom.byId('portal'), 'dndMode', this.dndMode);


			// hide the local apps category in dnd mode
			var localAppsCategory = array.filter(this.portalCategories, function(iPortalCategory) {
				return iPortalCategory.category === 'localApps';
			})[0];
			if (localAppsCategory) {
				domClass.toggle(localAppsCategory.domNode, 'dijitDisplayNone', this.dndMode);
			}

			// populate dndSource of the category with the shown apps
			var categories = array.filter(this.portalCategories, function(iPortalCategory) {
				return array.indexOf(['service', 'admin'], iPortalCategory.category) >= 0;
			});
			array.forEach(categories, lang.hitch(this, function(iCategory) {
				domClass.toggle(iCategory.grid.contentNode, 'dijitOffScreen', this.dndMode);
				if (this.dndMode) {
					var apps = iCategory.grid.store.query(function(app) {
						return !app.portalEditAddEntryDummy;
					});
					array.forEach(apps, function(iapp) {
						lang.mixin(iapp, {
							id: iapp.dn
						});
					});
					iCategory.grid.insertDndData(apps);
				} else {
					iCategory.grid.dndSource.store.setData([]);
					iCategory.grid.dndSource.parent.innerHTML = '';
					iCategory.grid.dndSource.clearItems();
				}
			}));

			window.scrollTo(0, scrollY);
		},

		saveEntryOrder: function() {
			this.standbyWidget.show();

			var categories = array.filter(this.portalCategories, function(iPortalCategory) {
				return array.indexOf(['service', 'admin'], iPortalCategory.category) >= 0;
			});

			var entriesToUpdate = {};
			array.forEach(categories, function(iCategory) {
				lang.mixin(entriesToUpdate, iCategory.grid.dndSource.externalDropMap);
			});
			var deferreds = [];
			tools.forIn(entriesToUpdate, lang.hitch(this, function(dn, newCategory) {
				var deferred = new Deferred();
				deferreds.push(deferred);
				this.moduleStore.put({
					'$dn$': dn,
					category: newCategory
				}).then(lang.hitch(this, function(result) {
					deferred.resolve({
						success: result.success,
						dn: dn,
						category: newCategory
					});
				}));
			}));

			all(deferreds).then(lang.hitch(this, function(result) {
				var msg = '';
				var success = true;
				msg = '<p>' + _('The new category for the following portal entries could not be saved:') + '</p><ul>';
				array.forEach(result, function(iresult) {
					success = success && iresult.success;
					if (!iresult.success) {
						msg += lang.replace('<li>{0}</li>', [iresult.dn]);
					}
				});
				if (!success) {
					this.standbyWidget.hide();
					dialog.alert(msg);
					return;
				}

				var portalEntriesOrder = [];
				array.forEach(categories, lang.hitch(this, function(iCategory) {
					var orderInCategory = [];
					var dndSource = iCategory.grid.dndSource;
					dndSource.getAllNodes().forEach(lang.hitch(this, function(inode) {
						orderInCategory.push(dndSource.getItem(inode.id).data.dn);
					}));
					portalEntriesOrder = portalEntriesOrder.concat(orderInCategory);
				}));

				var portalEntriesOrderDeferred = new Deferred();
				this.moduleStore.put({
					'$dn$': portalContent.portal.dn,
					portalEntriesOrder: []
				}).then(lang.hitch(this, function(result) {
					if (result.success) {
						this.moduleStore.put({
							'$dn$': portalContent.portal.dn,
							portalEntriesOrder: portalEntriesOrder
						}).then(lang.hitch(this, function(result) {
							if (result.success) {
								portalEntriesOrderDeferred.resolve();
							} else {
								portalEntriesOrderDeferred.reject();
							}
						}));
					} else {
						portalEntriesOrderDeferred.reject();
					}
				}));
				portalEntriesOrderDeferred.then(lang.hitch(this, function() {
					this._refreshAfterPortalEntryEdit().then( lang.hitch(this, function() {
						this.standbyWidget.hide();
						this.setDndMode(false);
						dialog.contextNotify(_('Changes saved'));
					}));
				}, function() {
					dialog.alert(_('Saving entry order failed'));
					this.setDndMode(false);
					this.standbyWidget.hide();
				}));
			}));
		},

		_updateCategories: function() {
			var scrollY = window.scrollY;
			var categories = array.filter(this.portalCategories, function(iPortalCategory) {
				return array.indexOf(['service', 'admin'], iPortalCategory.category) >= 0;
			});

			// FIXME this could only be done once and then use filterPortal do not show dummyNode
			// add/remove tile to categories for adding portal entries
			array.forEach(categories, lang.hitch(this, function(iCategory) {
				if (this.editMode) {
					iCategory.grid.store.add({
						portalEditAddEntryDummy: true,
						category: iCategory.category,
						id: '$portalEditAddEntryDummy$'
					});
				} else {
					iCategory.grid.store.remove('$portalEditAddEntryDummy$');
				}
			}));

			array.forEach(this.portalCategories, lang.hitch(this, function(iPortalCategory) {
				iPortalCategory.grid.editMode = this.editMode;
			}));
			this.filterPortal();
			window.scrollTo(0, scrollY);
		},

		filterPortal: function() {
			var searchPattern = lang.trim(this.search.get('value'));
			var searchQuery = this.search.getSearchQuery(searchPattern);

			var query = function(app) {
				return app.portalEditAddEntryDummy || searchQuery.test(app);
			};

			array.forEach(this.portalCategories, function(category) {
				category.set('query', query);
			});
		},

		getHighestRankedLink: getHighestRankedLink,
		canonicalizeIPAddress: canonicalizeIPAddress,
		getLocalLinks: getLocalLinks,
		getFQDNHostname: getFQDNHostname
	};
});
