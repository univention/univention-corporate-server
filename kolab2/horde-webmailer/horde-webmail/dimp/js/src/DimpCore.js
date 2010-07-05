/**
 * DimpCore.js - Dimp UI application logic.
 * NOTE: ContextSensitive.js must be loaded before this file.
 *
 * $Horde: dimp/js/src/DimpCore.js,v 1.369.2.62 2009-06-08 20:43:13 slusarz Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

/* Trick some Horde js into thinking this is the parent Horde window. */
var frames = { horde_main: true },

/* DimpCore object. */
DimpCore = {
    // Vars used and defaulting to null/false:
    //   DMenu, inAjaxCallback, is_logout, onDoActionComplete
    view_id: 1,
    remove_gc: [],
    server_error: 0,

    buttons: [ 'button_reply', 'button_forward', 'button_spam', 'button_ham', 'button_deleted' ],

    debug: function(label, e)
    {
        if (!this.is_logout && DIMP.conf.debug) {
            alert(label + ': ' + (e instanceof Error ? e.name + '-' + e.message : Object.inspect(e)));
        }
    },

    // Builds an array of UIDs from a list of ViewPort data rows
    // vs = (ViewPort_Selection) A ViewPort_Selection object
    toUIDArray: function(vs)
    {
        return vs.get('dataob').collect(function(r) {
            return this.toUIDString(r.imapuid, r.view);
        }, this);
    },

    // id = (integer) IMAP UID
    // mbox = (string) Mailbox name
    toUIDString: function(id, mbox)
    {
        return id + DIMP.conf.idx_sep + mbox;
    },

    /* 'action' -> if action begins with a '*', the exact string will be used
     *  instead of sending the action to the IMP handler. */
    doAction: function(action, params, uids, callback, opts)
    {
        if (!this.doActionOpts) {
            this.doActionOpts = {
                onException: function(r, e) {
                    this.debug('onException', e);
                }.bind(this),
                onFailure: function(t, o) {
                    this.debug('onFailure', t);
                }.bind(this)
            };
        };

        opts = Object.extend(this.doActionOpts, opts || {});
        params = $H(params);
        action = action.startsWith('*')
            ? action.substring(1)
            : DIMP.conf.URI_IMP + '/' + action;
        if (uids && uids.size()) {
            params.set('uid', uids.toJSON());
        }
        if (DIMP.conf.SESSION_ID) {
            params.update(DIMP.conf.SESSION_ID.toQueryParams());
        }
        opts.parameters = params.toQueryString();
        opts.onComplete = function(t, o) { this.doActionComplete(t, callback); }.bind(this);
        new Ajax.Request(action, opts);
    },

    doActionComplete: function(request, callback)
    {
        this.inAjaxCallback = true;
        var error = false, r = {};

        if (!request.responseText || !request.responseText.length) {
            error = true;
        } else {
            try {
                r = request.responseText.evalJSON(true);
            } catch (e) {
                this.debug('doActionComplete', e);
                error = true;
            }
        }

        if (!r.msgs) {
            r.msgs = [];
        }

        if (error) {
            if (++this.server_error == 3) {
                this.showNotifications([ { type: 'horde.error', message: DIMP.text.ajax_timeout } ]);
            }
            this.inAjaxCallback = false;
            return;
        }

        if (r.response && Object.isFunction(callback)) {
            try {
                callback(r);
            } catch (e) {
                this.debug('doActionComplete callback', e);
            }
        }

        if (this.server_error >= 3) {
            r.msgs.push({ type: 'horde.success', message: DIMP.text.ajax_recover });
        }
        this.server_error = 0;

        if (!r.msgs_noauto) {
            this.showNotifications(r.msgs);
        }

        if (this.onDoActionComplete) {
            this.onDoActionComplete(r);
        }

        this.inAjaxCallback = false;
    },

    setTitle: function(title)
    {
        document.title = DIMP.conf.name + ' :: ' + title;
    },

    showNotifications: function(msgs)
    {
        if (!msgs.size() || this.is_logout) {
            return;
        }

        var alerts = $('alerts');
        if (!alerts) {
            alerts = new Element('DIV', { id: 'alerts' });
            $(document.body).insert(alerts);
        }

        msgs.find(function(m) {
            switch (m.type) {
            case 'dimp.timeout':
                this.is_logout = true;
                this.redirect(DIMP.conf.timeout_url);
                return true;

            case 'horde.error':
            case 'horde.message':
            case 'horde.success':
            case 'horde.warning':
            case 'imp.reply':
            case 'imp.forward':
            case 'imp.redirect':
            case 'dimp.request':
            case 'dimp.sticky':
                var clickdiv, fadeeffect, iefix, requestfunc,
                    div = new Element('DIV', { className: m.type.replace('.', '-') });
                if ($w('dimp.request dimp.sticky').indexOf(m.type) != -1) {
                    div.update(m.message);
                } else {
                    div.insert(m.message.unescapeHTML().unescapeHTML());
                }
                alerts.insert(div);

                // IE6 has a bug that does not allow the body of a div to be
                // clicked to trigger an onclick event for that div (it only
                // seems to be an issue if the div is overlaying an element
                // that itself contains an image).  However, the alert box
                // normally displays over the message list, and we use several
                // graphics in the default message list layout, so we see this
                // buggy behavior 99% of the time.  The workaround is to
                // overlay the div with a like sized div containing a clear
                // gif, which tricks IE into the correct behavior.
                if (DIMP.conf.is_ie6) {
                    iefix = new Element('DIV', { className: 'ie6alertsfix' }).clonePosition(div, { setLeft: false, setTop: false });
                    clickdiv = iefix;
                    iefix.insert(div.remove());
                    alerts.insert(iefix);
                } else {
                    clickdiv = div;
                }

                fadeeffect = Effect.Fade.bind(this, div, { duration: 1.5, afterFinish: this.removeAlert.bind(this) });

                clickdiv.observe('click', fadeeffect);

                if ($w('horde.error dimp.request dimp.sticky').indexOf(m.type) == -1) {
                    fadeeffect.delay(m.type == 'horde.warning' ? 10 : 5);
                }

                if (m.type == 'dimp.request') {
                    requestfunc = function() {
                        fadeeffect();
                        document.stopObserving('click', requestfunc)
                    };
                    document.observe('click', requestfunc);
                }
            }
        }, this);
    },

    removeAlert: function(effect)
    {
        try {
            var elt = $(effect.element),
                parent = elt.up();
            // We may have already removed this element from the DOM tree
            // (if the user clicked on the notification), so check parentNode
            // here - will return null if node is not part of DOM tree.
            if (parent && parent.parentNode) {
                this.addGC(elt.remove());
                if (!parent.childElements().size() &&
                    parent.hasClassName('ie6alertsfix')) {
                    this.addGC(parent.remove());
                }
            }
        } catch (e) {
            this.debug('removeAlert', e);
        }
    },

    compose: function(type, args)
    {
        var url = DIMP.conf.compose_url;
        args = args || {};
        if (type) {
            args.type = type;
        }
        this.popupWindow(this.addURLParam(url, args), 'compose' + new Date().getTime());
    },

    popupWindow: function(url, name)
    {
        if (!(window.open(url, name.replace(/\W/g, '_'), 'width=' + DIMP.conf.popup_width + ',height=' + DIMP.conf.popup_height + ',status=1,scrollbars=yes,resizable=yes'))) {
            this.showNotifications([ { type: 'horde.warning', message: DIMP.text.popup_block } ]);
        }
    },

    closePopup: function()
    {
        // Mozilla bug/feature: it will not close a browser window
        // automatically if there is code remaining to be performed (or, at
        // least, not here) unless the mouse is moved or a keyboard event
        // is triggered after the callback is complete. (As of FF 2.0.0.3 and
        // 1.5.0.11).  So wait for the callback to complete before attempting
        // to close the window.
        if (this.inAjaxCallback) {
            this.closePopup.bind(this).defer();
        } else {
            window.close();
        }
    },

    logout: function()
    {
        this.is_logout = true;
        this.redirect(DIMP.conf.URI_IMP + '/LogOut');
    },

    redirect: function(url)
    {
        url = this.addSID(url);
        if (parent.frames.horde_main) {
            parent.location = url;
        } else {
            window.location = url;
        }
    },

    /* Add/remove mouse events on the fly.
     * Parameter: object with the following names - id, type, offset
     *   (optional), left (optional), onShow (optional)
     * Valid types:
     *   'message', 'draft'  --  Message list rows
     *   'container', 'special', 'folder'  --  Folders
     *   'reply', 'forward', 'otheractions'  --  Message list buttons
     *   'contacts'  --  Linked e-mail addresses */
    addMouseEvents: function(p)
    {
        this.DMenu.addElement(p.id, 'ctx_' + p.type, p);
    },

    /* elt = DOM element */
    removeMouseEvents: function(elt)
    {
        this.DMenu.removeElement($(elt).readAttribute('id'));
        this.addGC(elt);
    },

    /* Add a popdown menu to a dimpactions button. */
    addPopdown: function(bid, ctx)
    {
        var bidelt = $(bid),
            parentelt = bidelt.up();
        parentelt.insert($($('popdown_img').cloneNode(false)).writeAttribute('id', bid + '_img').show());
        this.addMouseEvents({ id: bid + '_img', type: ctx, offset: parentelt, left: true });
    },

    /* Add dropdown menus to address links. */
    buildAddressLinks: function(id)
    {
        var acount = 0;
        $(id).select('.address').each(function(e) {
            e.writeAttribute({ id: 'addr' + acount++ });
            e.observe('mouseover', function() { this.addMouseEvents({ id: e.id, type: 'contacts', offset: e, left: true }); }.bind(this));
        }, this);
        $('msgHeadersContent').select('.largeaddrlist').each(function(a) {
           this.clickObserveHandler({ d: a, f: function() { a.up().down().toggle().next().toggle().next().toggle(); } });
        }, this);
    },

    /* Removes event handlers from address links. */
    removeAddressLinks: function(id)
    {
        [ $(id).select('.address'), $(id).select('.largeaddrlist') ].flatten().compact().each(this.removeMouseEvents.bind(this));
    },

    /* Add event observers to message output.  Adds observers used in both
     * the base page and the popup message window. */
    messageOnLoad: function()
    {
        var C = this.clickObserveHandler;

        if ($('partlist')) {
            C({ d: $('partlist_col').up(), f: function() { $('partlist', 'partlist_col', 'partlist_exp').invoke('toggle'); } });
        }
        if ($('msg_print')) {
            C({ d: $('msg_print'), f: function() { window.print(); } });
        }
        if ($('msg_view_source')) {
            C({ d: $('msg_view_source'), f: function() { view(DIMP.conf.msg_source_link.unescapeHTML(), DIMP.conf.msg_index + '|' + DIMP.conf.msg_folder) }.bind(this) });
        }
        C({ d: $('ctx_contacts_new'), f: function() { this.compose('new', { to: this.DMenu.element().readAttribute('address') }); }.bind(this), ns: true });
        C({ d: $('ctx_contacts_add'), f: function() { this.doAction('AddContact', { name: this.DMenu.element().readAttribute('personal'), email: this.DMenu.element().readAttribute('email') }, null, true); }.bind(this), ns: true });
    },

    /* Utility functions. */
    addGC: function(elt)
    {
        this.remove_gc = this.remove_gc.concat(elt);
    },

    // o: (object) Contains the following items:
    //    'd'  - (required) The DOM element
    //    'f'  - (required) The function to bind to the click event
    //    'ns' - (optional) If set, don't stop the event's propogation
    //    'p'  - (optional) If set, passes in the event object to the called
    //                      function
    clickObserveHandler: function(o)
    {
        return o.d.observe('click', DimpCore._clickFunc.curry(o));
    },

    _clickFunc: function(o, e)
    {
        o.p ? o.f(e) : o.f();
        if (!o.ns) {
            e.stop();
        }
    },

    addSID: function(url)
    {
        if (!DIMP.conf.SESSION_ID) {
            return url;
        }
        return this.addURLParam(url, DIMP.conf.SESSION_ID.toQueryParams());
    },

    addURLParam: function(url, params)
    {
        var q = url.indexOf('?');

        if (q != -1) {
            params = $H(url.toQueryParams()).merge(params).toObject();
            url = url.substring(0, q);
        }
        return url + '?' + Object.toQueryString(params);
    }
};

// Initialize DMenu now.  Need to init here because IE doesn't load dom:loaded
// in a predictable order.
if (typeof ContextSensitive != 'undefined') {
    DimpCore.DMenu = new ContextSensitive();
}

document.observe('dom:loaded', function() {
    /* Don't do additional onload stuff if we are in a popup. We need a
     * try/catch block here since, if the page was loaded by an opener
     * out of this current domain, this will throw an exception. */
    try {
        if (parent.opener &&
            parent.opener.location.host == window.location.host &&
            parent.opener.DimpCore) {
            DIMP.baseWindow = parent.opener.DIMP.baseWindow || parent.opener;
        }
    } catch (e) {}

    /* Remove unneeded buttons. */
    if (!DIMP.conf.spam_reporting) {
        DimpCore.buttons = DimpCore.buttons.without('button_spam');
    }
    if (!DIMP.conf.ham_reporting) {
        DimpCore.buttons = DimpCore.buttons.without('button_ham');
    }

    /* Init garbage collection function - runs every 10 seconds. */
    new PeriodicalExecuter(function() {
        if (DimpCore.remove_gc.size()) {
            try {
                $A(DimpCore.remove_gc.splice(0, 75)).compact().invoke('stopObserving');
            } catch (e) {
                DimpCore.debug('remove_gc[].stopObserving', e);
            }
        }
    }, 10);
});

/* Helper methods for setting/getting element text without mucking
 * around with multiple TextNodes. */
Element.addMethods({
    setText: function(element, text)
    {
        var t = 0;
        $A(element.childNodes).each(function(node) {
            if (node.nodeType == 3) {
                if (t++) {
                    Element.remove(node);
                } else {
                    node.nodeValue = text;
                }
            }
        });

        if (!t) {
            $(element).insert(text);
        }
    },

    getText: function(element, recursive)
    {
        var text = '';
        $A(element.childNodes).each(function(node) {
            if (node.nodeType == 3) {
                text += node.nodeValue;
            } else if (recursive && node.hasChildNodes()) {
                text += $(node).getText(true);
            }
        });
        return text;
    }
});

/* Create some utility functions. */
Object.extend(String.prototype, {
    // We define our own version of evalScripts() to make sure that all
    // scripts are running in the same scope and that all functions are
    // defined in the global scope. This is not the case when using
    // prototype's evalScripts().
    evalScripts: function()
    {
        var func, i = 0, length, scripts = this.extractScripts(), re = /function\s+([^\s(]+)/g;
        for (length = scripts.size(); i < length; ++i) {
            eval(scripts[i]);
            while (func = re.exec(scripts[i])) {
                window[func[1]] = eval(func[1]);
            }
        }
    }
});

/** Functions overriding IMP/Horde/prototypejs JS functions. **/

/* We need to replace the IMP javascript for this function with code that
 * calls the correct DIMP functions. */
function popup_imp(url, w, h, args)
{
    DimpCore.compose('new', args.toQueryParams().toObject());
}

/* Necessary includes for toggle divs. Needed for BC purposes. */
function toggleQuoteBlock(id, lines)
{
    var block = $('qb_' + id).toggle(),
        toggle = $('qt_' + id),
        tmp = toggle.down();

        tmp = toggle.down();
        if (tmp) {
            tmp.remove();
        }
        toggle.insert(new Element('A', { className: 'widget togglequote' }).setStyle({ fontSize: '70%' }).insert('[' + (block.visible() ? DIMP.text.hidetext : DIMP.text.showtext + ' - ' + lines + ' ' + DIMP.text.lines) + ']').observe('click', toggleQuoteBlock.curry(id, lines)));
}

/* For attachment viewing to work, replaces the function from
 * horde/templates/contents/open_view_win.js. */
function view(url, uniqid)
{
    window.open(url, ++DimpCore.view_id + uniqid.replace(/\W/g, '_'), 'menubar=yes,toolbar=no,location=no,status=no,scrollbars=yes,resizable=yes');
}

/* document.viewport.getDimensions() is broken on Opera 9.5 in
 * prototypejs 1.6.0.2 and totally prevents usage of ViewPort.
 * Redefine here. */
if (Prototype.Browser.Opera && opera.version() >= 9.5) {
    document.viewport.getDimensions = function() {
        return { width: document.documentElement['clientWidth'], height: document.documentElement['clientHeight'] };
    };
}

/* The SelectorsAPI seems to be broken (at least w/Prototype 1.6.0.3 and
 * certain versions of Webkit). Just disable and fallback to methods that
 * work. */
Prototype.BrowserFeatures.SelectorsAPI = false;
