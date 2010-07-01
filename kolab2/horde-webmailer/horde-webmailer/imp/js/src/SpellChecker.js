/**
 * This spell checker was inspired by work done by Garrison Locke, but
 * was rewritten almost completely by Chuck Hagenbuch to use
 * Prototype/Scriptaculous.
 *
 * $Horde: imp/js/src/SpellChecker.js,v 1.36.2.13 2009-06-22 04:03:25 slusarz Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

var SpellChecker = Class.create({
    // Vars used and defaulting to null:
    //   bad, choices, choicesDiv, curWord, htmlArea, htmlAreaParent, locale,
    //   localeChoices, onAfterSpellCheck, onBeforeSpellCheck, onNoError,
    //   reviewDiv, statusButton, statusClass, suggestions, target, url
    options: {},
    resumeOnDblClick: true,
    state: 'CheckSpelling',

    // url = (string) URL of specllchecker handler
    // target = (string) DOM ID of message data
    // statusButton = (string/element) DOM ID or element of the status button
    // bs = (array) Button states
    // locales = (array) List of locales
    // sc = (string) Status class
    initialize: function(url, target, statusButton, bs, locales, sc)
    {
        var d, popdown, ul;

        this.url = url;
        this.target = target;
        this.statusButton = $(statusButton);
        this.buttonStates = bs;
        this.statusClass = sc || '';

        this.statusButton.observe('click', this.process.bindAsEventListener(this));
        this.options.onComplete = this.onComplete.bind(this);

        if (locales) {
            d = new Element('DIV', { className: 'autocomplete', id: 'spellcheckpopdown' }).setStyle({ position: 'absolute' }).hide();
            ul = new Element('UL');
            $H(locales).each(function(pair) {
                ul.insert({ bottom: new Element('LI', { lc: pair.key }).update(pair.value) });
            });
            d.insert({ bottom: ul });

            this.localeChoices = new KeyNavList(d, { onChoose: this.setLocale.bindAsEventListener(this) });

            popdown = new Element('A', { className: 'popdown' }).insert('&nbsp;').observe('click', function() {
                $('spellcheckpopdown').clonePosition(this.statusButton, {
                    setHeight: false,
                    setWidth: false,
                    offsetTop: this.statusButton.getHeight()
                });
                this.localeChoices.show();
            }.bind(this));

            this.statusButton.insert({ after: popdown });

            $(document.body).insert(d);
        }

        // We need to monitor clicks to know when to go out of
        // showSuggestions mode.
        document.observe('click', this.onClick.bindAsEventListener(this));

        this.status('CheckSpelling');
    },

    setLocale: function(e)
    {
        this.locale = e.readAttribute('lc');
    },

    targetValue: function()
    {
        var input = $(this.target);
        return (Object.isUndefined(input.value)) ? input.innerHTML : input.value;
    },

    process: function(e)
    {
        switch (this.state) {
        case 'CheckSpelling':
            this.spellCheck();
            break;

        case 'ResumeEdit':
            this.resume();
            break;
        }

        e.stop();
    },

    // noerror - (function) A callback function to run if no errors are
    //           identified. If not specified, will remain in spell check
    //           mode even if no errors are present.
    spellCheck: function(noerror)
    {
        if (this.onBeforeSpellCheck) {
            this.onBeforeSpellCheck();
        }

        var opts = Object.clone(this.options),
            p = $H(),
            url = this.url;

        this.status('Checking');
        this.removeChoices();

        this.onNoError = noerror;

        p.set(this.target, this.targetValue());
        opts.parameters = p.toQueryString();

        if (this.locale) {
            url += '/locale=' + this.locale;
        }
        if (this.htmlAreaParent) {
            url += '/html=1';
        }

        new Ajax.Request(url, opts);
    },

    onClick: function(e)
    {
        // If the language dropdown is currently active, and the click
        // got here, then we should hide the language dropdown.
        if (this.localeChoices) {
            this.localeChoices.hide();
        }

        // If we're not currently showing any choices, then we return
        // and let the click go.
        if (!this.choicesDiv) {
            return true;
        }

        // If the click was on the word that we're currently showing
        // results for, then we do nothing and let the list be
        // redisplayed by the link's own onclick handler.
        var link = e.findElement('SPAN');
        if (link && link == this.curWord) {
            return true;
        }

        // The KeyNavList will have already handled any valid clicks,
        // so that just leaves the rest of the window - in this case
        // we want to hide the KeyNavList and reset curWord without
        // changing anything.
        this.removeChoices();
        this.curWord = null;
    },

    onComplete: function(request)
    {
        var bad, content, d,
            i = 0,
            input = $(this.target),
            result = request.responseText.evalJSON(true);

        this.removeChoices();

        if (Object.isUndefined(result)) {
            this.status('Error');
            return;
        }

        this.suggestions = result.suggestions || [];

        if (this.onNoError && !this.suggestions.size()) {
            this.status('CheckSpelling');
            this.onNoError();
            return;
        }

        bad = result.bad || [];

        content = this.targetValue();
        content = this.htmlAreaParent
            ? content.replace(/\r?\n/g, '')
            : content.replace(/\r?\n/g, '~~~').escapeHTML();

        $A(bad).each(function(node) {
            var re_text = '<span index="' + (i++) + '" name="incorrect" class="incorrect">' + node + '</span>';
            content = content.replace(new RegExp("(?:^|\\b)" + RegExp.escape(node) + "(?:\\b|$)", 'g'), re_text);

            // Go through and see if we matched anything inside a tag (i.e.
            // class/name/incorrect is often matched if using a non-English
            // lang).
            content = content.replace(new RegExp("(<[^>]*)" + RegExp.escape(re_text) + "([^>]*>)", 'g'), '\$1' + node + '\$2');
        }, this);

        if (!this.reviewDiv) {
            this.reviewDiv = new Element('div', { className: input.readAttribute('className') + ' spellcheck' }).setStyle({ overflow: 'auto' });
            if (this.resumeOnDblClick) {
                this.reviewDiv.observe('dblclick', this.resume.bind(this));
            }
        }

        d = input.getDimensions();
        this.reviewDiv.setStyle({ width: d.width + 'px', height: d.height + 'px'});

        if (!this.htmlAreaParent) {
            content = content.replace(/~~~/g, '<br />');
        }
        this.reviewDiv.update(content);

        // Now attach results behavior to each link.
        this.reviewDiv.select('span[name="incorrect"]').invoke('observe', 'click', this.showSuggestions.bindAsEventListener(this));

        // Falsify links
        this.reviewDiv.select('A').invoke('observe', 'click', Event.stop);

        if (this.htmlAreaParent) {
            // Fix for Safari 3/fckeditor - Ticket #6909
            Element.hide(this.htmlArea);
            $(this.htmlAreaParent).insert({ bottom: this.reviewDiv });
        } else {
            input.hide().insert({ before: this.reviewDiv });
        }

        this.status('ResumeEdit');
    },

    showSuggestions: function(e)
    {
        var pos,
            elt = e.element(),
            ul = new Element('UL');

        try {
            pos = elt.viewportOffset();
        } catch (err) {
            // Fix for Safari 3/fckeditor - Ticket #6909
            pos = [ e.pointerX(), e.pointerY() ];
        }

        this.removeChoices();
        this.choicesDiv = new Element('DIV', { className: 'autocomplete' }).setStyle({ left: pos[0] + 'px', top: (pos[1] + 16) + 'px' }).hide();
        this.curWord = elt;

        $A(this.suggestions[this.curWord.readAttribute('index')]).each(function(node) {
            ul.insert({ bottom: new Element('LI').update(node) });
        });
        this.choicesDiv.insert({ bottom: ul });

        this.choices = new KeyNavList(this.choicesDiv, { onChoose: function(elt) { this.replaceWord(elt, this.curWord); }.bind(this) }).show();
        $(document.body).insert(this.choicesDiv);
    },

    replaceWord: function(li, word)
    {
        word.update(li.innerHTML).writeAttribute({ className: 'corrected' });
        this.removeChoices();
    },

    removeChoices: function()
    {
        if (this.choicesDiv) {
            this.choicesDiv.remove();
            this.choicesDiv = null;
        }
    },

    resume: function()
    {
        this.removeChoices();

        if (!this.reviewDiv) {
            return;
        }

        var input = $(this.target),
            t;

        this.reviewDiv.select('span[name="incorrect"]').each(function(n) {
            n.replace(n.innerHTML);
        });

        // Unfalsify links
        this.reviewDiv.select('A').invoke('stopObserving', 'click');

        t = this.reviewDiv.innerHTML;
        if (!this.htmlAreaParent) {
            t = t.replace(/<br *\/?>/gi, '~~~').unescapeHTML().replace(/~~~/g, "\n");
        }
        input.value = t;
        input.disabled = false;

        if (this.resumeOnDblClick) {
            this.reviewDiv.stopObserving('dblclick');
        }
        this.reviewDiv.remove();
        this.reviewDiv = null;

        this.status('CheckSpelling');

        if (this.htmlAreaParent) {
            // Fix for Safari 3/fckeditor - Ticket #6909
            Element.show(this.htmlArea);
        } else {
            input.show();
        }

        if (this.onAfterSpellCheck) {
            this.onAfterSpellCheck();
        }
    },

    status: function(state)
    {
        if (!this.statusButton) {
            return;
        }

        this.state = state;
        switch (this.statusButton.tagName) {
        case 'INPUT':
            this.statusButton.value = this.buttonStates[state];
            break;

        case 'A':
            this.statusButton.update(this.buttonStates[state]);
            break;
        }
        this.statusButton.className = this.statusClass + ' ' + state;
    },

    isActive: function()
    {
        return (this.reviewDiv);
    }

});
