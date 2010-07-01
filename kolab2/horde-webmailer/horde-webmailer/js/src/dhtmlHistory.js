/**
 * dhtmlHistory - An object that provides DHTML history, history data, and
 * bookmarking for AJAX applications.
 *
 * $Horde: horde/js/src/dhtmlHistory.js,v 1.4.2.7 2009-01-06 15:24:42 jan Exp $
 *
 * Original code (c) 2005, Brad Neuberg, bkn3@columbia.edu
 *   (http://codinginparadise.org)
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 * OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
 * IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
 * CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
 * OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
 * THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 *
 * This file has been altered from the original dhtmlHistory (v0.05) to
 * remove functionality not needed for DIMP and to provide bug fixes and
 * enhancements.
 *
 * Support from Safari adapted from code (c) 2007, Brian Dillard,
 *   bdillard@pathf.com (http://blogs.pathf.com/agileajax/)
 *
 * This file requires the Prototype Javscript Library v1.6.0+
 *
 * Additions Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 */

window.Horde = window.Horde || {};

Horde.dhtmlHistory = {
    /* Our current hash location, without the "#" symbol. */
    // currentLocation: null,

    /* Our history change listener. */
    // listener: null,

    /* A hidden IFrame we use in Internet Explorer to detect history
       changes. */
    // iframe: null,

    /* Indicates to the browser whether to ignore location changes. */
    // ignoreLocationChange: null,

    /* The amount of time in milliseconds that we should wait between add
       requests. Firefox is okay with 200 ms, but Internet Explorer needs
       400. */
    WAIT_TIME: 200,

    /* The amount of time in milliseconds an add request has to wait in line
       before being run on a setTimeout(). */
    currentWaitTime: 0,

    /* A flag that indicates that we should fire a history change event when
       we are ready, i.e. after we are initialized and we have a history
       change listener. This is needed due to an edge case in browsers other
       than Internet Explorer; if you leave a page entirely then return, we
       must fire this as a history change event. Unfortunately, we have lost
       all references to listeners from earlier, because JavaScript
       clears out. */
    // fireOnNewListener: null,

    /* A variable that indicates whether this is the first time this page has
       been loaded. If you go to a web page, leave it for another one, and
       then return, the page's onload listener fires again. We need a way to
       differentiate between the first page load and subsequent ones.  This
       variable works hand in hand with the pageLoaded variable we store into
       historyStorage. */
    // firstLoad: false,

    /* A variable to handle an important edge case in Internet Explorer. In
       IE, if a user manually types an address into their browser's location
       bar, we must intercept this by continiously checking the location bar
       with a timer interval. However, if we manually change the location
       bar ourselves programmatically, when using our hidden iframe, we need
       to ignore these changes. Unfortunately, these changes are not atomic,
       so we surround them with the variable 'ieAtomicLocationChange', that if
       true means we are programmatically setting the location and should
       ignore this atomic chunked change. */
    // ieAtomicLocationChange: null,

    /* Safari only variables. */
    // safariHistoryStartPoint: null,
    // safariStack: null,

    /* Initializes our DHTML history. You should call this after the page is
       finished loading. Returns true on success, false on failure. */
    initialize: function()
    {
        // TODO: This code is still buggy in Safari so disable for now.
        if (Prototype.Browser.Webkit) {
            return false;
        }

        Horde.historyStorage.init();

        if (Prototype.Browser.WebKit) {
            this.createSafari();
        }

        // Get our initial location
        this.currentLocation = this.getCurrentLocation();

        // Write out a hidden iframe for IE and set the amount of time to
        // wait between add() requests.
        if (Prototype.Browser.IE) {
            this.iframe = new Element('IFRAME', { name: 'DhtmlHistoryFrame', id: 'DhtmlHistoryFrame' }).hide();
            this.iframe.setAttribute('src', 'javascript:false;');
            $(document.body).insert(this.iframe);
            this.writeIframe(this.currentLocation);

            // Wait 400 milliseconds between history updates on IE
            this.WAIT_TIME = 400;

            this.ignoreLocationChange = true;
        }

        /* Add an unload listener for the page; this is needed for FF 1.5+
           because this browser caches all dynamic updates to the page, which
           can break some of our logic related to testing whether this is the
           first instance a page has loaded or whether it is being pulled from
           the cache. */
        Event.observe(window, 'unload', function() { this.firstLoad = false; }.bind(this));

        this.isFirstLoad();

        /* Other browsers can use a location handler that checks at regular
           intervals as their primary mechanism; we use it for IE as well to
           handle an important edge case; see checkLocation() for details. */
        new PeriodicalExecuter(this.checkLocation.bind(this), 0.3);

        return true;
    },

    /* Adds a history change listener. Note that only one listener is
       supported at this time. */
    addListener: function(callback)
    {
        this.listener = callback;

        /* If the page was just loaded and we should not ignore it, fire an
           event to our new listener now. */
        if (this.fireOnNewListener) {
            if (this.currentLocation) {
                this.fireHistoryEvent(this.currentLocation);
            }
            this.fireOnNewListener = false;
        }
    },

    add: function(newLoc, historyData)
    {
        if (Prototype.Browser.WebKit) {
            // TODO: This code is still buggy in Safari so disable for now.
            return false;
            newLoc = this.removeHash(newLoc);
            Horde.historyStorage.put(newLoc, historyData);
            var cl = this.currentLocation;
            this.currentLocation = newLoc;
            this.ignoreLocationChange = true;
            this.setLocation(newLoc);
            this.putSafariState(newLoc);
        } else {
            /* Most browsers require that we wait a certain amount of time
               before changing the location, such as 200 milliseconds; rather
               than forcing external callers to use setTimeout() to account for
               this to prevent bugs, we internally handle this detail by using
               a 'currentWaitTime' variable and have requests wait in line. */
            setTimeout(this.addImpl.bind(this, newLoc, historyData), this.currentWaitTime);
        }

        // Indicate that the next request will have to wait for awhile
        this.currentWaitTime += this.WAIT_TIME;
    },

    setLocation: function(loc)
    {
        location.hash = loc;
    },

    /* Gets the current hash value that is in the browser's location bar,
       removing leading # symbols if they are present. */
    getCurrentLocation: function()
    {
        if (Prototype.Browser.WebKit) {
            // TODO: This code is still buggy in Safari so disable for now.
            return false;
            return this.getSafariState();
        } else {
            return this.removeHash(unescape(location.hash));
        }
    },

    addImpl: function(newLoc, historyData)
    {
        // Indicate that the current wait time is now less
        if (this.currentWaitTime) {
            this.currentWaitTime -= this.WAIT_TIME;
        }

        /* IE has a strange bug; if the newLoc is the same as _any_
           preexisting id in the document, then the history action gets
           recorded twice; return immediately if there is an element with
           this ID. */
        if ($('newLoc')) {
            return;
        }

        // Remove any leading hash symbols on newLoc
        newLoc = this.removeHash(newLoc);

        // Store the history data into history storage
        Horde.historyStorage.put(newLoc, historyData);

        // Indicate to the browser to ignore this upcoming location change.
        // Indicate to IE that this is an atomic location change block.
        this.ignoreLocationChange = this.ieAtomicLocationChange = true;

        // Save this as our current location and change the browser location
        this.currentLocation = newLoc;
        this.setLocation(escape(newLoc));

        // Change the hidden iframe's location if on IE
        if (Prototype.Browser.IE) {
            this.writeIframe(newLoc);
        }

        // End of atomic location change block for IE
        this.ieAtomicLocationChange = false;
    },

    isFirstLoad: function()
    {
        if (Horde.historyStorage.hasKey("DhtmlHistory_pageLoaded") == false) {
            if (Prototype.Browser.IE) {
                this.fireOnNewListener = false;
            } else {
                this.ignoreLocationChange = true;
            }
            this.firstLoad = true;
            Horde.historyStorage.put("DhtmlHistory_pageLoaded", true);
        } else {
            if (Prototype.Browser.IE) {
                this.firstLoad = false;
            } else {
                /* Indicate that we want to pay attention to this location
                   change. */
                this.ignoreLocationChange = false;
            }

            /* For browser's other than IE, fire a history change event;
               on IE, the event will be thrown automatically when it's
               hidden iframe reloads on page load. Unfortunately, we don't
               have any listeners yet; indicate that we want to fire an
               event when a listener is added. */
            this.fireOnNewListener = true;
        }
    },

    /* Notify the listener of new history changes. */
    fireHistoryEvent: function(newHash)
    {
        if (this.listener) {
            // Extract the value from our history storage for this hash and
            // call our listener.
            this.listener.call(null, newHash, Horde.historyStorage.get(newHash));
        }
    },

    /* See if the browser has changed location.  This is the primary history
       mechanism for FF. For IE, we use this to handle an important edge case:
       if a user manually types in a new hash value into their IE location
       bar and press enter, we want to intercept this and notify any history
       listener. */
    checkLocation: function()
    {
        /* Ignore any location changes that we made ourselves for browsers
           other than IE. */
        if (!Prototype.Browser.IE) {
            if (this.ignoreLocationChange) {
                this.ignoreLocationChange = false;
                return;
            }
        } else if (this.ieAtomicLocationChange) {
            /* If we are dealing with IE and we are in the middle of making a
               location change from an iframe, ignore it. */
            return;
        }

        // Get hash location
        var hash = this.getCurrentLocation();

        // See if there has been a change or there is no hash location
        if (hash == this.currentLocation || Object.isUndefined(hash)) {
            return;
        }

        /* On IE, we need to intercept users manually entering locations into
           the browser; we do this by comparing the browsers location against
           the iframes location; if they differ, we are dealing with a manual
           event and need to place it inside our history, otherwise we can
           return. */
        this.ieAtomicLocationChange = true;

        if (Prototype.Browser.IE) {
            if (this.iframe.contentWindow.l == hash) {
                // The iframe is unchanged
                return;
            }
            this.writeIframe(hash);
        }

        // Save this new location
        this.currentLocation = hash;

        this.ieAtomicLocationChange = false;

        // Notify listeners of the change
        this.fireHistoryEvent(hash);
    },

    /* Removes any leading hash that might be on a location. */
    removeHash: function(h)
    {
        if (h === null || Object.isUndefined(h)) {
            return null;
        } else if (h.startsWith('#')) {
            if (h.length == 1) {
                return "";
            } else {
                return h.substring(1);
            }
        }
        return h;
    },

    // IE Specific Code
    /* For IE, says when the hidden iframe has finished loading. */
    iframeLoaded: function(newLoc)
    {
        // Ignore any location changes that we made ourselves
        if (this.ignoreLocationChange) {
            this.ignoreLocationChange = false;
            return;
        }

        // Get the new location
        this.setLocation(escape(newLoc));

        // Notify listeners of the change
        this.fireHistoryEvent(newLoc);
    },

    writeIframe: function(l)
    {
        var d = this.iframe.contentWindow.document;
        d.open();
        d.write('<html><script type="text/javascript">var l="' + l + '";function pageLoaded(){window.parent.Horde.dhtmlHistory.iframeLoaded(l);}</script><body onload="pageLoaded()"></body></html>');
        d.close();
    },

    // Safari specific code
    createSafari: function()
    {
        this.WAIT_TIME = 400;
        this.safariHistoryStartPoint = history.length;

        this.safariStack = new Element('INPUT', { id: 'DhtmlSafariHistory', type: 'text', value: '[]' }).hide();
        $(document.body).insert(this.safariStack);
    },

    getSafariStack: function()
    {
        return $F(this.safariStack).evalJSON();
    },

    getSafariState: function()
    {
        var stack = this.getSafariStack();
        return stack[history.length - this.safariHistoryStartPoint - 1];
    },

    putSafariState: function(newLoc)
    {
        var stack = this.getSafariStack();
        stack[history.length - this.safariHistoryStartPoint] = newLoc;
        this.safariStack.setValue(stack.toJSON());
    }
};

/* An object that uses a hidden form to store history state across page loads.
   The chief mechanism for doing so is using the fact that browsers save the
   text in form data for the life of the browser and cache, which means the
   text is still there when the user navigates back to the page. See
   http://codinginparadise.org/weblog/2005/08/ajax-tutorial-saving-session-across.html
   for full details. */
Horde.historyStorage = {
    /* Our hash of key name/values. */
    // storageHash: null,

    /* A reference to our textarea field. */
    // storageField: null,

    put: function(key, value)
    {
        this.loadHashTable();

        // Store this new key
        this.storageHash.set(key, value);

        // Save and serialize the hashtable into the form
        this.saveHashTable();
    },

    get: function(key)
    {
        // Make sure the hash table has been loaded from the form
        this.loadHashTable();

        var value = this.storageHash.get(key);
        return Object.isUndefined(value) ? null : value;
    },

    remove: function(key)
    {
        // Make sure the hash table has been loaded from the form
        this.loadHashTable();

        // Delete the value
        this.storageHash.unset(key);

        // Serialize and save the hash table into the form
        this.saveHashTable();
    },

    /* Clears out all saved data. */
    reset: function()
    {
        this.storageField.value = "";
        this.storageHash = $H();
    },

    hasKey: function(key)
    {
        // Make sure the hash table has been loaded from the form
        this.loadHashTable();
        return !(typeof this.storageHash.get(key) == undefined);
    },

    init: function()
    {
        // Write a hidden form into the page
        var form = new Element('FORM').hide();
        $(document.body).insert(form);

        this.storageField = new Element('TEXTAREA', { id: 'historyStorageField' });
        form.insert(this.storageField);
    },

    /* Loads the hash table up from the form. */
    loadHashTable: function()
    {
        if (!this.storageHash) {
            // Destringify the content back into a real JS object
            this.storageHash = (this.storageField.value) ? this.storageField.value.evalJSON() : $H();
        }
    },

    /* Saves the hash table into the form. */
    saveHashTable: function()
    {
        this.loadHashTable();
        this.storageField.value = this.storageHash.toJSON();
    }

};
