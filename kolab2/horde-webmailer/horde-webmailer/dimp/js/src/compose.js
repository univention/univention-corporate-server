/**
 * compose.js - Javascript code used in the DIMP compose view.
 *
 * $Horde: dimp/js/src/compose.js,v 1.84.2.35 2009-10-06 23:16:09 slusarz Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

var DimpCompose = {
    // Variables defaulting to empty/false:
    //   auto_save_interval, button_pressed, compose_cursor, compose_loaded,
    //   dbtext, editor_on, mp_padding, resizebcc, resizecc, resizeto,
    //   row_height, sbtext, uploading
    last_msg: '',
    textarea_ready: true,

    confirmCancel: function()
    {
        if (window.confirm(DIMP.text_compose.cancel)) {
            if (DIMP.conf_compose.auto_save_interval_val) {
                DimpCore.doAction('DeleteDraft', { index: $F('index') });
            }
            return this._closeCompose();
        }
    },

    _closeCompose: function()
    {
        if (DIMP.conf_compose.qreply) {
            this.closeQReply();
        } else if (DIMP.baseWindow || DIMP.conf_compose.popup) {
            DimpCore.closePopup();
        } else {
            DimpCore.redirect(DIMP.conf.URI_DIMP_INBOX);
        }
    },

    closeQReply: function()
    {
        var al = $('attach_list').childElements();
        this.last_msg = '';

        if (al.size()) {
            this.removeAttach(al);
        }

        $('draft_index', 'messageCache').invoke('setValue', '');
        $('qreply', 'sendcc', 'sendbcc').invoke('hide');
        [ $('msgData'), $('togglecc').up(), $('togglebcc').up() ].invoke('show');
        if (this.editor_on) {
            this.toggleHtmlEditor();
        }
        $('compose').reset();

        // Disable auto-save-drafts now.
        if (this.auto_save_interval) {
            this.auto_save_interval.stop();
        }
    },

    change_identity: function()
    {
        var lastSignature, msg, nextSignature, pos,
            id = $F('identity'),
            last = this.get_identity($F('last_identity')),
            msgval = $('message'),
            next = this.get_identity(id),
            ssm = $('save_sent_mail');

        $('sent_mail_folder_label').setText(next.id[5]);
        $('bcc').setValue(next.id[6]);
        if (ssm) {
            ssm.writeAttribute('checked', next.id[4]);
        }

        // Finally try and replace the signature.
        if (this.editor_on) {
            switch (DIMP.conf_compose.js_editor) {
            case 'xinha':
                msg = _editors.message.getHTML();
                break;

            case 'fckeditor':
                msg = FCKeditorAPI.GetInstance('message').GetHTML();
                break;
            }

            msg = msg.replace(/\r\n/g, '\n');
            lastSignature = '<p><!--begin_signature--><!--end_signature--></p>';
            nextSignature = '<p><!--begin_signature-->' + next.sig.replace(/^ ?<br \/>\n/, '').replace(/ +/g, ' ') + '<!--end_signature--></p>';

            // Dot-all functionality achieved with [\s\S], see:
            // http://simonwillison.net/2004/Sep/20/newlines/
            msg = msg.replace(/<p>\s*<!--begin_signature-->[\s\S]*?<!--end_signature-->\s*<\/p>/, lastSignature);
        } else {
            msg = $F(msgval).replace(/\r\n/g, '\n');
            lastSignature = last.sig;
            nextSignature = next.sig;
        }

        pos = (last.id[2])
            ? msg.indexOf(lastSignature)
            : msg.lastIndexOf(lastSignature);

        if (pos != -1) {
            if (next.id[2] == last.id[2]) {
                msg = msg.substring(0, pos) + nextSignature + msg.substring(pos + lastSignature.length, msg.length);
            } else if (next.id[2]) {
                msg = nextSignature + msg.substring(0, pos) + msg.substring(pos + lastSignature.length, msg.length);
            } else {
                msg = msg.substring(0, pos) + msg.substring(pos + lastSignature.length, msg.length) + nextSignature;
            }

            msg = msg.replace(/\r\n/g, '\n').replace(/\n/g, '\r\n');
            if (this.editor_on) {
                switch (DIMP.conf_compose.js_editor) {
                case 'xinha':
                    _editors.message.setHTML(msg);
                    break;

                case 'fckeditor':
                    FCKeditorAPI.GetInstance('message').SetHTML(msg);
                    break;
                }
            } else {
                msgval.setValue(msg);
            }
            $('last_identity').setValue(id);
        }
    },

    get_identity: function(id, editor_on)
    {
        editor_on = Object.isUndefined(editor_on) ? this.editor_on : editor_on;
        return {
            id: DIMP.conf_compose.identities[id],
            sig: DIMP.conf_compose.identities[id][(editor_on ? 1 : 0)].replace(/^\n/, '')
        };
    },

    uniqueSubmit: function(action)
    {
        var db, params, sb,
            c = $('compose');

        if (DIMP.SpellCheckerObject) {
            DIMP.SpellCheckerObject.resume();
            if (!this.textarea_ready) {
                this.uniqueSubmit.bind(this, action).defer();
                return;
            }
        }

        c.setStyle({ cursor: 'wait' });

        if (action == 'send_message' || action == 'save_draft') {
            this.button_pressed = true;

            switch (action) {
            case 'send_message':
                if (($F('subject') == '') &&
                    !window.confirm(DIMP.text_compose.nosubject)) {
                    return;
                }

                if (!this.sbtext) {
                    sb = $('send_button');
                    this.sbtext = sb.getText();
                    sb.setText(DIMP.text_compose.sending);
                }
                break;

            case 'save_draft':
                if (!this.dbtext) {
                    db = $('draft_button');
                    this.dbtext = db.getText();
                    db.setText(DIMP.text_compose.saving);
                }
                break;
            }

            // Don't send/save until uploading is completed.
            if (this.uploading) {
                (function() { if (this.button_pressed) { this.uniqueSubmit(action); } }).bind(this).delay(0.25);
                return;
            }
        }
        $('action').setValue(action);

        if (action == 'add_attachment') {
            // We need a submit action here because browser security models
            // won't let us access files on user's filesystem otherwise.
            this.uploading = true;
            c.submit();
        } else {
            // Move HTML text to textarea field for submission.
            if (this.editor_on) {
                switch (DIMP.conf_compose.js_editor) {
                case 'xinha':
                    // This onsubmit() is needed because xinha sets an onsubmit
                    // handler to set the value of the textarea, and since we
                    // are overloading the default onsubmit handler, we need
                    // to make sure we explicitly call the function.
                    c.onsubmit();
                    break;

                case 'fckeditor':
                    FCKeditorAPI.GetInstance('message').UpdateLinkedField();
                    break;
                }
            }

            // Use an AJAX submit here so that we can do javascript-y stuff
            // before having to close the window on success.
            params = c.serialize(true);
            if (!DIMP.baseWindow) {
                params.nonotify = true;
            }
            DimpCore.doAction('*' + DIMP.conf.compose_url, params, [], this.uniqueSubmitCallback.bind(this));
        }
    },

    uniqueSubmitCallback: function(r)
    {
        var elt,
            d = r.response;

        if (!d) {
            return;
        }

        if (d.imp_compose) {
            $('messageCache').setValue(d.imp_compose);
        }

        if (d.success || d.action == 'add_attachment') {
            switch (d.action) {
            case 'auto_save_draft':
                this.button_pressed = false;
                $('draft_index').setValue(d.draft_index);
                break;

            case 'save_draft':
                this.button_pressed = false;
                if (DIMP.baseWindow) {
                    DIMP.baseWindow.DimpBase.pollFolders();
                    DIMP.baseWindow.DimpCore.showNotifications(r.msgs);
                }
                if (DIMP.conf_compose.close_draft) {
                    return this._closeCompose();
                }
                break;

            case 'send_message':
                this.button_pressed = false;
                if (DIMP.baseWindow) {
                    if (d.reply_type == 'reply') {
                        DIMP.baseWindow.DimpBase.flag('answered', d.index, d.reply_folder);
                    }

                    if (d.folder) {
                        DIMP.baseWindow.DimpBase.createFolder(d.folder);
                    }

                    if (d.draft_delete) {
                        DIMP.baseWindow.DimpBase.pollFolders();
                    }

                    DIMP.baseWindow.DimpCore.showNotifications(r.msgs);
                }
                return this._closeCompose();

            case 'add_attachment':
                this.uploading = false;
                if (d.success) {
                    this.addAttach(d.info.number, d.info.name, d.info.type, d.info.size);
                } else {
                    this.button_pressed = false;
                }
                if (DIMP.conf_compose.attach_limit != -1 &&
                    $('attach_list').childElements().size() > DIMP.conf_compose.attach_limit) {
                    $('upload').writeAttribute('disabled', false);
                    elt = new Element('DIV', [ DIMP.text_compose.attachment_limit ]);
                } else {
                    elt = new Element('INPUT', { type: 'file', name: 'file_1' });
                    elt.observe('change', this.uploadAttachment.bind(this));
                }
                $('upload_wait').replace(elt.writeAttribute('id', 'upload'));
                this.resizeMsgArea();
                break;
            }
        } else {
            this.button_pressed = false;
        }

        $('compose').setStyle({ cursor: null });

        // Re-enable buttons if needed.
        if (!this.button_pressed) {
            if (this.sbtext) {
                $('send_button').setText(this.sbtext);
            }
            if (this.dbtext) {
                $('draft_button').setText(this.dbtext);
            }
            this.dbtext = this.sbtext = null;
        }

        DimpCore.showNotifications(r.msgs);
    },

    toggleHtmlEditor: function(noupdate)
    {
        if (!DIMP.conf_compose.rte_avail) {
            return;
        }
        noupdate = noupdate || false;
        if (DIMP.SpellCheckerObject) {
            DIMP.SpellCheckerObject.resume();
        }

        var msg, text;

        if (this.editor_on) {
            this.editor_on = false;

            switch (DIMP.conf_compose.js_editor) {
            case 'xinha':
                msg = _editors.message;
                text = msg.getHTML();
                $(msg._htmlArea).remove();
                msg = _editors = null;
                break;

            case 'fckeditor':
                text = FCKeditorAPI.GetInstance('message').GetHTML();
                $('messageParent').childElements().invoke('hide');
                $('message').show();
                break;
            }

            DimpCore.doAction('Html2Text', { text: text }, [], this.setMessageText.bind(this), { asynchronous: false });
        } else {
            this.editor_on = true;
            if (!noupdate) {
                DimpCore.doAction('Text2Html', { text: $F('message') }, [], this.setMessageText.bind(this), { asynchronous: false });
            }

            switch (DIMP.conf_compose.js_editor) {
            case 'xinha':
                this._RTELoading('show');
                xinha_init();
                this._hideXinhaLoading();
                break;

            case 'fckeditor':
                oFCKeditor.Height = this.getMsgAreaHeight();
                // Try to reuse the old fckeditor instance.
                try {
                    FCKeditorAPI.GetInstance('message').SetHTML($F('message'));
                    $('messageParent').childElements().invoke('show');
                    $('message').hide();
                } catch (e) {
                    this._RTELoading('show');
                    FCKeditor_OnComplete = this._RTELoading.curry('hide');
                    oFCKeditor.ReplaceTextarea();
                }
                break;
            }
        }
        $('htmlcheckbox').checked = this.editor_on;
        $('html').setValue(this.editor_on ? 1 : 0);
    },

    _RTELoading: function(cmd)
    {
        var o, r;
        if (!$('rteloading')) {
            r = new Element('DIV', { id: 'rteloading' }).clonePosition($('messageParent'));
            $(document.body).insert(r);
            o = r.viewportOffset();
            $(document.body).insert(new Element('SPAN', { id: 'rteloadingtxt' }).setStyle({ top: (o.top + 15) + 'px', left: (o.left + 15) + 'px' }).insert(DIMP.text.loading));
        }
        $('rteloading', 'rteloadingtxt').invoke(cmd);
    },

    _hideXinhaLoading: function()
    {
        if (_editors && _editors.message) {
            _editors.message._onGenerate = this._RTELoading.curry('hide');
        } else {
            this._hideXinhaLoading.bind(this).delay(.05);
        }
    },

    toggleHtmlCheckbox: function()
    {
        if (!this.editor_on || window.confirm(DIMP.text_compose.toggle_html)) {
            this.toggleHtmlEditor();
        }
    },

    getMsgAreaHeight: function()
    {
        if (!this.mp_padding) {
            this.mp_padding = $('messageParent').getHeight() - $('message').getHeight();
        }

        return document.viewport.getHeight() - $('messageParent').cumulativeOffset()[1] - this.mp_padding;
    },

    initializeSpellChecker: function()
    {
        if (!DIMP.conf_compose.rte_avail) {
            return;
        }

        if (typeof DIMP.SpellCheckerObject != 'object') {
            // If we fired before the onload that initializes the spellcheck,
            // wait.
            this.initializeSpellChecker.bind(this).defer();
            return;
        }

        DIMP.SpellCheckerObject.onBeforeSpellCheck = function() {
            if (!this.editor_on) {
                return;
            }
            DIMP.SpellCheckerObject.htmlAreaParent = 'messageParent';
            switch (DIMP.conf_compose.js_editor) {
            case 'xinha':
                DIMP.SpellCheckerObject.htmlArea = _editors.message._htmlArea;
                _editors.message._textArea.setValue(_editors.message.outwardHtml(_editors.message.getHTML()));
                break;

            case 'fckeditor':
                DIMP.SpellCheckerObject.htmlArea = $('message').adjacent('iframe[id*=message]').first();
                $('message').setValue(FCKeditorAPI.GetInstance('message').GetHTML());
                this.textarea_ready = false;
                break;
            }
        }.bind(this);
        DIMP.SpellCheckerObject.onAfterSpellCheck = function() {
            if (!this.editor_on) {
                return;
            }
            DIMP.SpellCheckerObject.htmlArea = DIMP.SpellCheckerObject.htmlAreaParent = null;
            switch (DIMP.conf_compose.js_editor) {
            case 'xinha':
                _editors.message.setHTML(_editors.message.inwardHtml($F(_editors.message._textArea)));
                break;

            case 'fckeditor':
                var ed = FCKeditorAPI.GetInstance('message');
                ed.SetHTML($F('message'));
                ed.Events.AttachEvent('OnAfterSetHTML', function() { this.textarea_ready = true; }.bind(this));
                break;
            }
        }.bind(this);
    },

    setMessageText: function(r)
    {
        var ta = $('message');
        if (!ta) {
            $('messageParent').insert(new Element('TEXTAREA', { id: 'message', name: 'message', style: 'width:100%;' }).insert(r.response.text));
        } else {
            ta.setValue(r.response.text);
        }

        if (!this.editor_on) {
            this.resizeMsgArea();
        }
    },

    fillForm: function(msg, header, focus, noupdate)
    {
        // On IE, this can get loaded before DOM;loaded. Check for an init
        // value and don't load until it is available.
        if (!this.resizeto) {
            this.fillForm.bind(this, msg, header, focus, noupdate).defer();
            return;
        }

        var bcc_add, fo,
            identity = this.get_identity($F('last_identity')),
            msgval = $('message');

        if (!this.last_msg.empty() &&
            this.last_msg != $F(msgval).replace(/\r/g, '') &&
            !window.confirm(DIMP.text_compose.fillform)) {
            return;
        }

        // Set auto-save-drafts now if not already active.
        if (DIMP.conf_compose.auto_save_interval_val && !this.auto_save_interval) {
            this.auto_save_interval = new PeriodicalExecuter(function() {
                var cur_msg;
                if (this.editor_on) {
                    switch (DIMP.conf_compose.js_editor) {
                    case 'xinha':
                        cur_msg = _editors.message.getHTML();
                        break;

                    case 'fckeditor':
                        cur_msg = FCKeditorAPI.GetInstance('message').GetHTML();
                        break;
                    }
                } else {
                    cur_msg = $F(msgval);
                }
                cur_msg = cur_msg.replace(/\r/g, '');
                if (!cur_msg.empty() && this.last_msg != cur_msg) {
                    this.uniqueSubmit('auto_save_draft');
                    this.last_msg = cur_msg;
                }
            }.bind(this), DIMP.conf_compose.auto_save_interval_val * 60);
        }

        if (this.editor_on) {
            switch (DIMP.conf_compose.js_editor) {
            case 'xinha':
                _editors.message.setHTML(msg);
                this.last_msg = _editors.message.getHTML();
                break;

            case 'fckeditor':
                fo = FCKeditorAPI.GetInstance('message');
                fo.SetHTML(msg);
                this.last_msg = fo.GetHTML();
                break;
            }
            this.last_msg = this.last_msg.replace(/\r/g, '');
        } else {
            msgval.setValue(msg);
            this.setCursorPosition(msgval);
            this.last_msg = $F(msgval).replace(/\r/g, '');
        }

        $('to').setValue(header.to);
        this.resizeto.resizeNeeded();
        if (header.cc) {
            $('cc').setValue(header.cc);
            this.resizecc.resizeNeeded();
        }
        if (DIMP.conf_compose.cc) {
            this.toggleCC('cc');
        }
        if (header.bcc) {
            $('bcc').setValue(header.bcc);
            this.resizebcc.resizeNeeded();
        }
        if (identity.id[6]) {
            bcc_add = $F('bcc');
            if (bcc_add) {
                bcc_add += ', ';
            }
            $('bcc').setValue(bcc_add + identity.id[6]);
        }
        if (DIMP.conf_compose.bcc) {
            this.toggleCC('bcc');
        }
        $('subject').setValue(header.subject);
        $('in_reply_to').setValue(header.in_reply_to);
        $('references').setValue(header.references);
        $('reply_type').setValue(header.replytype);

        Field.focus(focus || 'to');
        this.resizeMsgArea();

        if (DIMP.conf_compose.show_editor) {
            if (!this.editor_on) {
                this.toggleHtmlEditor(noupdate || false);
            }
            if (focus == 'message') {
                this.focusEditor();
            }
        }
    },

    focusEditor: function()
    {
        try {
            switch (DIMP.conf_compose.js_editor) {
            case 'xinha':
                _editors.message.focusEditor();
                break;

            case 'fckeditor':
                FCKeditorAPI.GetInstance('message').Focus();
                break;
            }
        } catch (e) {
            this.focusEditor.bind(this).defer();
        }
    },

    addAttach: function(number, name, type, size)
    {
        var div = new Element('DIV').insert(name + ' [' + type + '] (' + size + ' KB) '),
            input = new Element('INPUT', { type: 'button', atc_id: number, value: DIMP.text_compose.remove });
        div.insert(input);
        $('attach_list').insert(div);
        input.observe('click', this.removeAttach.bind(this, [ input.up() ]));
        this.resizeMsgArea();
    },

    removeAttach: function(e)
    {
        var ids = [];
        e.each(function(n) {
            n = $(n);
            ids.push(n.firstDescendant().readAttribute('atc_id'));
            n.remove();
        });
        DimpCore.doAction('DeleteAttach', { atc_indices: ids, imp_compose: $F('messageCache') });
        this.resizeMsgArea();
    },

    resizeMsgArea: function()
    {
        var m, rows,
            de = document.documentElement,
            msg = $('message');

        if (!this.compose_loaded) {
            return;
        }

        if (this.editor_on) {
            switch (DIMP.conf_compose.js_editor) {
            case 'xinha':
                m = $('messageParent').select('.htmlarea').first();
                break;

            case 'fckeditor':
                m = $('messageParent').select('iframe').last();
                break;
            }
            if (m) {
                m.setStyle({ height: this.getMsgAreaHeight() + 'px' });
            } else {
                this.resizeMsgArea.bind(this).defer();
            }
            return;
        }

        if (!this.row_height) {
            // Change the ID and name to not conflict with msg node.
            m = $(msg.cloneNode(false)).writeAttribute({ id: null, name: null }).setStyle({ visibility: 'hidden' });
            $(document.body).insert(m);
            m.writeAttribute('rows', 1);
            this.row_height = m.getHeight();
            m.writeAttribute('rows', 2);
            this.row_height = m.getHeight() - this.row_height;
            m.remove();
        }

        /* Logic: Determine the size of a given textarea row, divide that size
         * by the available height, round down to the lowest integer row, and
         * resize the textarea. */
        rows = parseInt(this.getMsgAreaHeight() / this.row_height);
        msg.writeAttribute({ rows: rows, disabled: false });
        if (de.scrollHeight - de.clientHeight) {
            msg.writeAttribute({ rows: rows - 1 });
        }
    },

    uploadAttachment: function()
    {
        var u = $('upload');
        $('submit_frame').observe('load', this.attachmentComplete.bind(this));
        this.uniqueSubmit('add_attachment');
        u.stopObserving('change').replace(new Element('DIV', { id: 'upload_wait' }).insert(DIMP.text_compose.uploading + ' ' + $F(u)));
    },

    attachmentComplete: function()
    {
        var sf = $('submit_frame'),
            doc = sf.contentDocument || sf.contentWindow.document;
        sf.stopObserving('load');
        DimpCore.doActionComplete({ responseText: doc.body.innerHTML }, this.uniqueSubmitCallback.bind(this));
    },

    toggleCC: function(type)
    {
        $('send' + type).show();
        $('toggle' + type).up().hide();
    },

    /* Sets the cursor to the given position. */
    setCursorPosition: function(input)
    {
        var pos, range;

        switch (DIMP.conf_compose.compose_cursor) {
        case 'top':
            pos = 0;
            $('message').setValue('\n' + $F('message'));
            break;

        case 'bottom':
            pos = $F('message').length;
            break;

        case 'sig':
            pos = $F('message').replace(/\r\n/g, '\n').lastIndexOf(this.get_identity($F('last_identity')).sig) - 1;
            break;

        default:
            return;
        }

        if (input.setSelectionRange) {
            /* This works in Mozilla */
            Field.focus(input);
            input.setSelectionRange(pos, pos);
        } else if (input.createTextRange) {
            /* This works in IE */
            range = input.createTextRange();
            range.collapse(true);
            range.moveStart('character', pos);
            range.moveEnd('character', 0);
            Field.select(range);
            range.scrollIntoView(true);
        }
    },

    /* Open the addressbook window. */
    openAddressbook: function()
    {
        window.open(DIMP.conf_compose.abook_url, 'contacts', 'toolbar=no,location=no,status=no,scrollbars=yes,resizable=yes,width=550,height=300,left=100,top=100');
    }
},

ResizeTextArea = Class.create({
    // Variables defaulting to empty:
    //   defaultRows, field, onResize
    maxRows: 5,

    initialize: function(field, onResize)
    {
        this.field = $(field);

        this.defaultRows = Math.max(this.field.readAttribute('rows'), 1);
        this.onResize = onResize;

        var func = this.resizeNeeded.bindAsEventListener(this);
        this.field.observe('mousedown', func);
        this.field.observe('keyup', func);

        this.resizeNeeded();
    },

    resizeNeeded: function()
    {
        var lines = $F(this.field).split('\n'),
            cols = this.field.readAttribute('cols'),
            newRows = lines.size(),
            oldRows = this.field.readAttribute('rows');

        lines.each(function(line) {
            if (line.length >= cols) {
                newRows += Math.floor(line.length / cols);
            }
        });

        if (newRows != oldRows) {
            this.field.writeAttribute('rows', (newRows > oldRows) ? Math.min(newRows, this.maxRows) : Math.max(this.defaultRows, newRows));

            if (this.onResize) {
                this.onResize();
            }
        }
    }
});

document.observe('dom:loaded', function() {
    var DC = DimpCompose,
        boundResize = DC.resizeMsgArea.bind(DC),
        C = DimpCore.clickObserveHandler;

    DC.initializeSpellChecker();
    $('upload').observe('change', DC.uploadAttachment.bind(DC));

    // Automatically resize address fields.
    DC.resizeto = new ResizeTextArea('to', boundResize);
    DC.resizecc = new ResizeTextArea('cc', boundResize);
    DC.resizebcc = new ResizeTextArea('bcc', boundResize);

    // Safari requires a submit target iframe to be at least 1x1 size or else
    // it will open content in a new window.  See:
    //   http://blog.caboo.se/articles/2007/4/2/ajax-file-upload
    if (Prototype.Browser.WebKit) {
        $('submit_frame').writeAttribute({ position: 'absolute', width: '1px', height: '1px' }).setStyle({ left: '-999px' }).show();
    }

    /* Attach click handlers. */
    if ($('compose_close')) {
        C({ d: $('compose_close'), f: DC.confirmCancel.bind(DC) });
    }
    C({ d: $('send_button'), f: DC.uniqueSubmit.bind(DC, 'send_message') });
    C({ d: $('draft_button'), f: DC.uniqueSubmit.bind(DC, 'save_draft') });
    [ 'cc', 'bcc' ].each(function(a) {
        C({ d: $('toggle' + a), f: DC.toggleCC.bind(DC, a) });
    });
    if ($('htmlcheckbox')) {
        C({ d: $('htmlcheckbox'), f: DC.toggleHtmlCheckbox.bind(DC), ns: true });
    }
    if ($('compose_specialchars')) {
        C({ d: $('compose_specialchars'), f: function() { window.open(DIMP.conf_compose.specialchars_url, 'chars', 'height=220,width=400'); } });
    }

    $('writemsg').select('.composeAddrbook').each(function(a) {
        C({ d: a, f: DC.openAddressbook.bind(DC) });
    });

    /* Only allow submit through send button. */
    $('compose').observe('submit', Event.stop);

    /* Attach other handlers. */
    $('identity').observe('change', DC.change_identity.bind(DC));

    // Various events that may cause the textarea to grow larger than the
    // window size.
    $('togglecc').observe('click', boundResize);
    $('togglebcc').observe('click', boundResize);
    Event.observe(window, 'resize', boundResize);
});

Event.observe(window, 'load', function() {
    DimpCompose.compose_loaded = true;
    DimpCompose.resizeMsgArea();
});
