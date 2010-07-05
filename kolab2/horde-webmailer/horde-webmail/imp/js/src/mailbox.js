/**
 * Provides the javascript for the mailbox.php script
 *
 * $Horde: imp/js/src/mailbox.js,v 1.10.2.7 2008-10-24 21:52:34 jan Exp $
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

var keyId,
    startrange = null;

function anySelected()
{
    return $H(messagelist).keys().detect(function(e) {
        return $('check' + e).checked;
    });
}

function selectRow(id, select)
{
    var rid = $(id.replace(/check/, 'row'));
    if (select) {
        rid.addClassName('selectedRow');
    } else {
        // Make sure to remove both regular and -over versions.
        rid.removeClassName('selectedRow');
        rid.removeClassName('selectedRow-over');
    }
    $(id).checked = select;
}

function imp_confirm(url, msg)
{
    RedBox.overlay = true;
    RedBox.showHtml('<div id="RB_confirm"><p>' + msg + '</p><input type="button" class="button" onclick="window.location=\'' + url + '\';" value="' + IMP.text.yes + '" />' +
                    '<input type="button" class="button" onclick="RedBox.close();" value="' + IMP.text.no + '" /></div>');
}

function messages_submit(actID)
{
    if (!anySelected()) {
        alert(IMP.text.mailbox_submit);
        return;
    }

    if (actID == 'delete_messages') {
        if (IMP.conf.pop3 && !confirm(IMP.text.mailbox_delete)) {
            return;
        }
    } else if (actID == 'spam_report') {
        if (!confirm(IMP.text.spam_report)) {
            return;
        }
    } else if (actID == 'notspam_report') {
        if (!confirm(IMP.text.notspam_report)) {
            return;
        }
    }
    $('actionID').setValue(actID);
    $('messages').submit();
}

function makeSelection(form)
{
    var flag = '';

    switch (parseInt(form)) {
    case -1:
        if ($('checkAll').checked) {
            flag = '!';
        }
        flag += IMP.conf.IMP_ALL;
        break;

    case 1:
        flag = $F('filter1');
        break;

    default:
        flag = $F('filter2');
    }

    // Fixes Bug #6893
    if (flag.empty()) {
        return;
    } else if (flag.startsWith('!')) {
        selectFlagged(parseInt(flag.substring(1)), false);
    } else if (flag.startsWith('+')) {
        selectFlagged(flag.substring(0, 1), null);
    } else {
        selectFlagged(parseInt(flag), true);
    }

    // Reset the form.
    switch (parseInt(form)) {
    case -1:
        break;

    case 1:
        $('select1').reset();
        break;

    default:
        $('select2').reset();
    }
}

function selectRange(event)
{
    Event.extend(event);
    var id = event.element().id, checkbox = $(id);
    if (!checkbox) {
        return;
    }
    var checked = checkbox.checked;

    if (startrange !== null && event.shiftKey) {
        var elts = [ $(startrange).id, checkbox.id ];
        var count = 0;
        $H(messagelist).keys().detect(function(r) {
            r = 'check' + r;
            if (elts.indexOf(r) != -1) {
                ++count;
            }
            if (count) {
                selectRow(r, checked);
                if (count == 2) {
                    return true;
                }
            }
        });
    } else {
        selectRow(id, checked);
    }
    startrange = id;
}

function updateFolders(form)
{
    var tm2 = $('targetMailbox2');
    if (tm2) {
        var tm1 = $('targetMailbox1');
        if ((form == 1 && $F(tm1) != "") ||
            (form == 2 && $F(tm2) != "")) {
            var index = (form == 1) ? tm1.selectedIndex : tm2.selectedIndex;
            tm1.selectedIndex = tm2.selectedIndex = index;
        }
    }
}

function transfer(actID, form)
{
    if (anySelected()) {
        var tmbox = $('targetMbox');
        tmbox.setValue((form == 1) ? $F('targetMailbox1') : $F('targetMailbox2'));

        // Check for a mailbox actually being selected.
        if ($F(tmbox) == '*new*') {
            var newFolder = prompt(IMP.text.newfolder, '');
            if (newFolder != null && newFolder != '') {
                $('newMbox').setValue(1);
                tmbox.setValue(newFolder);
                messages_submit(actID);
            }
        } else {
            if ($F(tmbox) == '') {
                alert(IMP.text.target_mbox);
            } else {
                messages_submit(actID);
            }
        }
    } else {
        alert(IMP.text.mailbox_selectone);
    }
}

// Put everything reliant on IMAP flags in this section.
function selectFlagged(flag, val)
{
    $H(messagelist).keys().each(function(e) {
        var check, elt = $('check' + e);
        if (flag == '+') {
            check = !elt.checked;
        } else if (flag & messagelist[e]) {
            check = val;
        } else {
            check = !val;
        }
        selectRow(elt.id, check);
    });
}

function flagMessages(form)
{
    var f1 = $('flag1'), f2 = $('flag2');
    if ((form == 1 && $F(f1) != "") ||
        (form == 2 && $F(f2) != "")) {
        if (anySelected()) {
            // Can't use $() here.  See Bug #4736.
            document.messages.flag.value = (form == 1) ? $F(f1) : $F(f2);
            messages_submit('flag_messages');
        } else {
            if (form == 1) {
                f1.selectedIndex = 0;
            } else {
                f2.selectedIndex = 0;
            }
            alert(IMP.text.mailbox_selectone);
        }
    }
}

function getMessage(id, offset)
{
    if (!offset) {
        return id;
    }

    var mlist = $H(messagelist).keys();
    var i = mlist.indexOf(id);
    if (i != -1) {
        var j = i + offset;
        if (j >= 0 && j < mlist.length) {
            return mlist[j];
        }
    }
    return '';
}

function onKeyDownHandler(e)
{
    var o = e.element();
    var key = e.keyCode;
    var next, old;

    if (e.altKey || e.ctrlKey) {
        var checkinc, subjinc;

        switch (key) {
        case Event.KEY_UP:
            checkinc = -1;
            subjinc = -1;
            break;

        case Event.KEY_DOWN:
            checkinc = 1;
            subjinc = 1;
            break;

        default:
            return;
        }

        if (typeof messagelist == 'undefined') {
            return;
        }

        if (o.id.indexOf('check') == 0 && o.tagName == 'INPUT') {
            old = o.id.substring(5);
            keyId = getMessage(old, checkinc);
            next = $('subject' + keyId);
        } else if (o.id.indexOf('subject') == 0 && o.tagName == 'A') {
            old = o.id.substring(7);
            keyId = getMessage(old, subjinc);
            next = $('subject' + keyId);
        } else {
            keyId = ((checkinc + subjinc) > 0) ? $H(messagelist).keys().first() : $H(messagelist).keys().last();
            if (Event.KEY_UP || Event.KEY_DOWN) {
                next = $('subject' + keyId);
            }
        }
    } else if (key == 32 &&
               o.id.indexOf('subject') == 0 &&
               o.tagName == 'A') {
        // Space key - toggle selection of the current message.
        startrange = 'check' + keyId;
        selectRow(startrange, !$(startrange).checked);
    } else if (!e.shiftKey) {
        var loc;
        if (key == Event.KEY_LEFT && $('prev')) {
            loc = $('prev').href;
        } else if (key == Event.KEY_RIGHT && $('next')) {
            loc = $('next').href;
        }

        if (loc) {
            document.location.href = loc;
        }
        return;
    } else {
        return;
    }

    if (next) {
        next.focus();
        var row = $('row' + keyId);
        if (e.altKey) {
            var nextId = next.id.replace(/subject/, 'check');
            selectRow(nextId, !$(nextId).checked);
        } else if (old != next.id && row.className.indexOf('-over') == -1) {
            row.className += '-over';
        }
        if (old) {
            row = $('row' + old);
            if (old != next.id) {
                row.className = row.className.replace(/-over/, '');
            }
        }
    }

    e.stop();
}

if (IMP.conf.hasDOM) {
    document.observe('dom:loaded', function() {
        document.observe('keydown', onKeyDownHandler);
    });
}
