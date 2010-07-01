/**
 * Provides the javascript for the compose.php script.
 *
 * $Horde: imp/js/src/compose.js,v 1.15.2.15 2009-03-30 23:08:41 slusarz Exp $
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

/*
 * Variables defined in compose.php:
 *    cancel_url, compose_spellcheck, cursor_pos, identities, max_attachments,
 *    popup, redirect, rtemode, smf_check
 */

var display_unload_warning = true,
    textarea_ready = true,
    skip_spellcheck = false;

/**
 * Retrieve the editor object.
 */
function _getXinha()
{
    var ed = Try.these(
        function() { return __editors.message; },
        function() { return _editors.message; },
        function() { return _editors[$('message')]; }
    );

    if (!ed) {
        throw 'Unable to find the HTML Editor object, cannot continue.';
    }

    return ed;
}

function confirmCancel(event)
{
    if (window.confirm(IMP.text.compose_cancel)) {
        display_unload_warning = false;
        if (popup) {
            if (cancel_url) {
                self.location = cancel_url;
            } else {
                self.close();
            }
        } else {
            window.location = cancel_url;
        }
        return true;
    } else {
        Event.extend(event);
        event.stop();
        return false;
    }
}

/**
 * Sets the cursor to the given position.
 */
function setCursorPosition(input, position)
{
    if (input.setSelectionRange) {
        /* This works in Mozilla */
        Field.focus(input);
        input.setSelectionRange(position, position);
    } else if (input.createTextRange) {
        /* This works in IE */
        var range = input.createTextRange();
        range.collapse(true);
        range.moveStart('character', position);
        range.moveEnd('character', 0);
        Field.select(range);
        range.scrollIntoView(true);
    }
}

function redirectSubmit(event)
{
    if ($F('to') == '') {
        alert(IMP.text.compose_recipient);
        $('to').focus();
        Event.extend(event);
        event.stop();
        return false;
    }

    $('redirect').setStyle({ cursor: 'wait' });
    display_unload_warning = false;

    return true;
}

function change_identity(id)
{
    var last = identities[$F('last_identity')],
        next = identities[id],
        msg, ed, lastSignature, nextSignature;

    // If the rich text editor is on, we'll use a regexp to find the
    // signature comment and replace its contents.
    if (rtemode) {
        switch (IMP.conf.js_editor) {
        case 'xinha':
            ed = _getXinha();
            msg = ed.getHTML();
            break;

        case 'fckeditor':
            ed = FCKeditorAPI.GetInstance('message');
            msg = ed.GetHTML();
            break;
        }

        msg = msg.replace(/\r\n/g, '\n');

        lastSignature = '<p><!--begin_signature--><!--end_signature--></p>';
        nextSignature = '<p><!--begin_signature-->' + next[0].replace(/^ ?<br \/>\n/, '').replace(/ +/g, ' ') + '<!--end_signature--></p>';

        // Dot-all functionality achieved with [\s\S], see:
        // http://simonwillison.net/2004/Sep/20/newlines/
        msg = msg.replace(/<p class="imp-signature">\s*<!--begin_signature-->[\s\S]*?<!--end_signature-->\s*<\/p>/, lastSignature);
    } else {
        msg = $F('message').replace(/\r\n/g, '\n');

        lastSignature = last[0].replace(/^\n/, '');
        nextSignature = next[0].replace(/^\n/, '');
    }

    var pos = (last[1]) ? msg.indexOf(lastSignature) : msg.lastIndexOf(lastSignature);
    if (pos != -1) {
        if (next[1] == last[1]) {
            msg = msg.substring(0, pos) + nextSignature + msg.substring(pos + lastSignature.length, msg.length);
        } else if (next[1]) {
            msg = nextSignature + msg.substring(0, pos) + msg.substring(pos + lastSignature.length, msg.length);
        } else {
            msg = msg.substring(0, pos) + msg.substring(pos + lastSignature.length, msg.length) + nextSignature;
        }

        msg = msg.replace(/\r\n/g, '\n').replace(/\n/g, '\r\n');

        $('last_identity').setValue(id);
        window.status = IMP.text.compose_sigreplace;
    } else {
        window.status = IMP.text.compose_signotreplace;
    }

    if (rtemode) {
        switch (IMP.conf.js_editor) {
        case 'xinha':
            ed.setHTML(msg);
            break;

        case 'fckeditor':
            ed.SetHTML(msg);
            break;
        }
    } else {
        $('message').setValue(msg);
    }

    var smf = $('sent_mail_folder');
    if (smf_check) {
        var i = 0;
        $A(smf.options).detect(function(f) {
            if (f.value == next[2]) {
                smf.selectedIndex = i;
                return true;
            }
            ++i;
        });
    } else {
        if (smf.firstChild) {
            smf.replaceChild(document.createTextNode(next[2]), smf.firstChild);
        } else {
            smf.appendChild(document.createTextNode(next[2]));
        }
    }

    var save = $('ssm');
    if (save) {
        save.checked = next[3];
    }
    var bcc = $('bcc');
    if (bcc) {
        bccval = bcc.value;

        if (last[4]) {
            var re = new RegExp(last[4] + ",? ?", 'gi');
            bccval = bccval.replace(re, "");
            if (bccval) {
                bccval = bccval.replace(/, ?$/, "");
            }
        }

        if (next[4]) {
            if (bccval) {
                bccval += ', ';
            }
            bccval += next[4];
        }

        bcc.setValue(bccval);
    }
}

function uniqSubmit(actionID, event)
{
    if (event) {
        Event.extend(event);
        event.stop();
    }

    if (actionID == 'send_message') {
        if (($F('subject') == '') &&
            !window.confirm(IMP.text.compose_nosubject)) {
            return;
        }

        if (!skip_spellcheck &&
            compose_spellcheck &&
            IMP.SpellCheckerObject &&
            !IMP.SpellCheckerObject.isActive()) {
            IMP.SpellCheckerObject.spellCheck(onNoSpellError.curry(actionID, event));
            return;
        }
    }

    skip_spellcheck = false;

    if (IMP.SpellCheckerObject) {
        IMP.SpellCheckerObject.resume();
    }

    // Ticket #6727; this breaks on WebKit w/FCKeditor.
    if (!Prototype.Browser.WebKit) {
        $('compose').setStyle({ cursor: 'wait' });
    }
    display_unload_warning = false;
    $('actionID').setValue(actionID);
    _uniqSubmit();
}

function _uniqSubmit()
{
    if (textarea_ready) {
        $('compose').submit();
    } else {
        _uniqSubmit.defer();
    }
}

function onNoSpellError(actionID, e)
{
    skip_spellcheck = true;
    uniqSubmit(actionID, e);
}

function attachmentChanged()
{
    var fields = [], usedFields = 0;

    $('upload_atc').select('input[type="file"]').each(function(i) {
        fields[fields.length] = i;
    });

    if (max_attachments !== null &&
        fields.length == max_attachments) {
        return;
    }

    fields.each(function(i) {
        if (i.value.length > 0) {
            usedFields++;
        }
    });

    if (usedFields == fields.length) {
        var lastRow = $('attachment_row_' + usedFields);
        if (lastRow) {
            var td = new Element('TD', { align: 'left' }).insert(new Element('STRONG').insert(IMP.text.compose_file + ' ' + (usedFields + 1) + ':')).insert('&nbsp;')

            var file = new Element('INPUT', { type: 'file', name: 'upload_' + (usedFields + 1), size: 25 });
            file.observe('change', attachmentChanged);
            td.insert(file);

            var select = new Element('SELECT', { name: 'upload_disposition_' + (usedFields + 1) });
            select.options[0] = new Option(IMP.text.compose_attachment, 'attachment', true);
            select.options[1] = new Option(IMP.text.compose_inline, 'inline');

            var newRow = new Element('TR', { id: 'attachment_row_' + (usedFields + 1) }).insert(td).insert(new Element('TD', { align: 'left' }).insert(select));

            lastRow.parentNode.insertBefore(newRow, lastRow.nextSibling);
        }
    }
}

function initializeSpellChecker()
{
    if (typeof IMP.SpellCheckerObject != 'object') {
        // If we fired before the onload that initializes the
        // spellcheck, wait.
        initializeSpellChecker.defer();
        return;
    }

    IMP.SpellCheckerObject.onBeforeSpellCheck = function() {
        IMP.SpellCheckerObject.htmlAreaParent = 'messageParent';
        switch (IMP.conf.js_editor) {
        case 'xinha':
            var ed = _getXinha();
            IMP.SpellCheckerObject.htmlArea = ed._htmlArea;
            ed._textArea.setValue(ed.outwardHtml(ed.getHTML()));
            break;

        case 'fckeditor':
            IMP.SpellCheckerObject.htmlArea = $('message').adjacent('iframe[id*=message]').first();
            $('message').setValue(FCKeditorAPI.GetInstance('message').GetHTML());
            textarea_ready = false;
            break;
        }
    }
    IMP.SpellCheckerObject.onAfterSpellCheck = function() {
        var ed;
        IMP.SpellCheckerObject.htmlArea = IMP.SpellCheckerObject.htmlAreaParent = null;
        switch (IMP.conf.js_editor) {
        case 'xinha':
            ed = _getXinha();
            ed.setHTML(ed.inwardHtml(ed._textArea.value));
            break;

        case 'fckeditor':
            ed = FCKeditorAPI.GetInstance('message');
            ed.SetHTML($('message').value);
            ed.Events.AttachEvent('OnAfterSetHTML', function() { textarea_ready = true; });
            break;
        }
    }
}

/**
 * Code to run on window load.
 */
document.observe('dom:loaded', function() {
    /* Prevent Return from sending messages - it should bring us out of
     * autocomplete, not submit the whole form. */
    $$('INPUT').each(function(i) {
        /* Attach to everything but button and submit elements. */
        if (i.type != 'submit' && i.type != 'button') {
            i.observe('keydown', function(e) {
                if (e.keyCode == 10 || e.keyCode == Event.KEY_RETURN) {
                    e.stop();
                    return false;
                }
            });
        }
    });

    if (cursor_pos !== null && $('message')) {
        setCursorPosition($('message'), cursor_pos);
    }

    if (redirect) {
        $('to').focus();
    } else {
        if (Prototype.Browser.IE) {
            $('subject').observe('keydown', function(e) {
                if (e.keyCode == Event.KEY_TAB && !e.shiftKey) {
                    e.stop();
                    $('message').focus();
                }
            });
        }

        if (rtemode) {
            initializeSpellChecker();
        }

        if ($('to') && !$F('to')) {
            $('to').focus();
        } else if (!$F('subject')) {
            if (rtemode) {
                $('subject').focus();
            } else {
                $('message').focus();
            }
        }
    }
});

Event.observe(window, 'load', function() {
    if (compose_popup && !reloaded) {
        var d, e = redirect ? $('redirect') : $('compose');
        d = Math.min(e.getHeight(), screen.height - 100) - document.viewport.getHeight();
        if (d > 0) {
            window.resizeBy(0, d);
        }
    }
});

/**
 * Warn before closing the window.
 */
Event.observe(window, 'beforeunload', function() {
    if (display_unload_warning) {
        return IMP.text.compose_discard;
    }
});
