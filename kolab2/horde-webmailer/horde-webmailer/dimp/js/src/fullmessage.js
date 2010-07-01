/**
 * $Horde: dimp/js/src/fullmessage.js,v 1.23.2.13 2009-01-06 15:22:37 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

var DimpFullmessage = {

    quickreply: function(type)
    {
        var func;

        $('msgData').hide();
        $('qreply').show();

        switch (type) {
        case 'reply':
        case 'reply_all':
        case 'reply_list':
            func = 'GetReplyData';
            break;

        case 'forward_all':
        case 'forward_body':
        case 'forward_attachments':
            func = 'GetForwardData';
            break;
        }

        DimpCore.doAction(func,
                          { imp_compose: $F('messageCache'),
                            type: type },
                          [ DimpCore.toUIDString($F('index'), $F('folder')) ],
                          this.msgTextCallback.bind(this));
    },

    msgTextCallback: function(result)
    {
        if (!result.response) {
            return;
        }

        var r = result.response,
            editor_on = ((r.format == 'html') && !DimpCompose.editor_on),
            id = (r.identity === null) ? $F('identity') : r.identity,
            i = DimpCompose.get_identity(id, editor_on);

        $('identity', 'last_identity').invoke('setValue', id);

        DimpCompose.fillForm((i.id[2]) ? ("\n" + i.sig + r.body) : (r.body + "\n" + i.sig), r.header);

        if (r.fwd_list && r.fwd_list.length) {
            r.fwd_list.each(function(ptr) {
                DimpCompose.addAttach(ptr.number, ptr.name, ptr.type, ptr.size);
            });
        }

        if (editor_on) {
            DimpCompose.toggleHtmlEditor(true);
        }

        if (r.imp_compose) {
            $('messageCache').setValue(r.imp_compose);
        }
    }

};

document.observe('dom:loaded', function() {
    window.focus();
    DimpCore.buildAddressLinks('msgHeaders');
    DimpCore.messageOnLoad();
    DimpCore.addPopdown('reply_link', 'replypopdown');
    DimpCore.addPopdown('forward_link', 'fwdpopdown');

    /* Set up click handlers. */
    var C = DimpCore.clickObserveHandler;
    C({ d: $('windowclose'), f: function() { window.close(); } });
    C({ d: $('reply_link'), f: DimpFullmessage.quickreply.bind(DimpFullmessage, 'reply') });
    C({ d: $('forward_link'), f: DimpFullmessage.quickreply.bind(DimpFullmessage, DIMP.conf.forward_default) });
    [ 'spam', 'ham', 'deleted' ].each(function(a) {
        var d = $('button_' + a);
        if (d) {
            C({ d: d, f: function(a) { DIMP.baseWindow.DimpBase.flag(a, DIMP.conf.msg_index, DIMP.conf.msg_folder); window.close(); }.curry(a) });
        }
    });
    C({ d: $('qreply').select('div.headercloseimg img').first(), f: DimpCompose.confirmCancel.bind(DimpCompose) });
    [ 'reply', 'reply_all', 'reply_list' ].each(function(a) {
        var d = $('ctx_replypopdown_' + a);
        if (d) {
            C({ d: d, f: DimpFullmessage.quickreply.bind(DimpFullmessage, a), ns: true });
        }
    });
    [ 'forward_all', 'forward_body', 'forward_attachments' ].each(function(a) {
        C({ d: $('ctx_fwdpopdown_' + a), f: DimpFullmessage.quickreply.bind(DimpFullmessage, a), ns: true });
    });
});
