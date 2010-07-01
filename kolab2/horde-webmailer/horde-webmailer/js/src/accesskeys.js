/**
 */
var AccessKeys = {

    macos: navigator.userAgent.indexOf('Mac') > -1,

    elements: [],

    replace: function()
    {
        $$('*[accesskey]').each(function(elm) {
            this.elements[elm.readAttribute('accesskey').toUpperCase()] = elm;
        }, this);
        document.observe('keydown', this.keydownHandler.bind(this));
    },

    keydownHandler: function(e)
    {
        if ((this.macos && e.ctrlKey) ||
            (!this.macos && e.altKey && !e.ctrlKey)) {
            var kc = String.fromCharCode(e.keyCode || e.charCode).toUpperCase();
            if (this.elements[kc]) {
                this.execute(this.elements[kc], e);
                e.stop();
            }
        }
    },

    execute: function(element, e)
    {
        if (!element) {
            return;
        }

        switch (element.tagName) {
        case 'A':
            element.focus();
            if (element.onclick) {
                if (element.onclick()) {
                    window.location.href = element.href;
                }
            } else {
                window.location.href = element.href;
            }
            return;
        case 'INPUT':
        case 'SELECT':
        case 'TEXTAREA':
            element.focus();
            switch (element.type.toUpperCase()) {
            case 'BUTTON':
            case 'RESET':
            case 'SUBMIT':
                element.click();
                break;
            }
            return;
        case 'LABEL':
            this.execute($(element.htmlFor));
            return;
        }

        if (typeof $(element)._prototypeEventID == 'undefined') {
            return;
        }
        var handlers = $H(Event.cache[$(element)._prototypeEventID.first()]);
        if (handlers.get('click')) {
            handlers.get('click').each(function(wrapper) { wrapper(e); });
        }
    }

}

Event.observe(window, 'load', AccessKeys.replace.bind(AccessKeys));
