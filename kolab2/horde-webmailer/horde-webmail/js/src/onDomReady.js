/**
 * onDomReady - An improvement on window.onload by firing events when page is
 * done loading instead of when all binary data is finished loading.
 *
 * Code from: http://agileweb.org/articles/2006/07/28/onload-final-update
 * Fixes/Improvements by: Michael Slusarz <slusarz@horde.org>
 *
 * $Horde: horde/js/src/onDomReady.js,v 1.4.2.1 2007-12-20 15:01:31 jan Exp $
 */
Object.extend(Event, {
    observe: function(element, name, observer, useCapture) {
        element = $(element);
        useCapture = useCapture || false;
        if ((name == 'keypress') &&
            (Prototype.Browser.WebKit || element.attachEvent)) {
            name = 'keydown';
        }
        if ((name == 'load') && element.screen) {
            this._observeLoad(element, name, observer, useCapture);
        } else {
            this._observeAndCache(element, name, observer, useCapture);
        }
    },

    _observeLoad: function(element, name, observer, useCapture) {
        if (this._ready) {
            this._ready.push(observer);
            return;
        }

        this._ready = [];
        var loader = this._onloadWindow.bind(this);

        if ($("__ie_onload")) {
            loader();
        } else if (Prototype.Browser.WebKit) {
            /* This currently doesn't seem to work in all instances because
               these browsers have unrealistically low function call maximums.
               Instead, simply default to regular onload behavior. */
            //this._safariTimer = setInterval(function() {
            //    if (/loaded|complete/.test(document.readyState)) {
            //        clearInterval(this._safariTimer);
            //        this._onloadWindow();
            //    }
            //}.bind(this), 10);
            this._observeAndCache(element, name, loader, useCapture);
        } else if (document.addEventListener) {
            // Mozilla and Opera
            this._useaEL = true;
            this._observeAndCache(document, 'DOMContentLoaded', loader, false);
        } else if (Prototype.Browser.IE) {
            document.write('<scr' + 'ipt id="__ie_onload" defer="true" src="//:"></script>');
            var script = $('__ie_onload');
            this._observeAndCache(script, 'readystatechange', function() {
                if (this.readyState == 'complete') {
                    Element.remove("__ie_onload");
                    loader();
                }
            }.bind(script), false);
        } else {
            this._observeAndCache(element, name, loader, useCapture);
        }
    },

    _onloadWindow: function() {
        if (arguments.callee.done) {
            return;
        }
        arguments.callee.done = true;
        this._ready.each(function(f) {
            try { f() }
            catch (e) { }
        });
        this._ready = null;
        if (this._useaEL) {
            document.removeEventListener('DOMContentLoaded', Event._onloadWindow, false);
        }
    }
});
