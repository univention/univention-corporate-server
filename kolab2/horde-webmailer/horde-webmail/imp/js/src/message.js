/**
 * Provides the javascript for the message.php script
 *
 * $Horde: imp/js/src/message.js,v 1.8.2.4 2008-05-20 16:33:02 slusarz Exp $
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

function arrowHandler(e)
{
    if (e.altKey || e.shiftKey || e.ctrlKey) {
        return;
    }

    switch (e.keyCode || e.charCode) {
    case Event.KEY_LEFT:
        if ($('prev')) {
            document.location.href = $('prev').href;
        }
        break;

    case Event.KEY_RIGHT:
        if ($('next')) {
            document.location.href = $('next').href;
        }
        break;
    }
}

function message_submit(actID)
{
    if (actID == 'spam_report') {
        if (!window.confirm(IMP.text.spam_report)) {
            return;
        }
    } else if (actID == 'notspam_report') {
        if (!window.confirm(IMP.text.notspam_report)) {
            return;
        }
    }
    $('actionID').setValue(actID);
    $('messages').submit();
}

function flagMessage(form)
{
    var f1 = $('flag1'), f2 = $('flag2');
    if ((form == 1 && $F(f1)) ||
        (form == 2 && $F(f2))) {
        $('flag').setValue((form == 1) ? $F(f1) : $F(f2));
        message_submit('flag_message');
    }
}

function transfer(actID, form)
{
    var tmbox = $('targetMbox');
    tmbox.setValue((form == 1) ? $F('target1') : $F('target2'));

    // Check for a mailbox actually being selected.
    if ($F(tmbox) == '*new*') {
        var newFolder = window.prompt(IMP.text.newfolder, '');
        if (newFolder != null && newFolder != '') {
            $('newMbox').setValue(1);
            tmbox.setValue(newFolder);
            message_submit(actID);
        }
    } else {
        if (!$F(tmbox)) {
            window.alert(IMP.text.target_mbox);
        } else {
            message_submit(actID);
        }
    }
}

function updateFolders(form)
{
    var f = (form == 1) ? 2 : 1;
    $('target' + f).selectedIndex = $('target' + form).selectedIndex;
}

/* Function needed for IE compatibilty with drop-down menus. */
function messageActionsHover()
{
    var iefix = new Element('IFRAME', { scrolling: 'no', frameborder: 0 }).hide();
    iefix.setStyle({ position: 'absolute' });
    // This can not appear in the new Element() call - Bug #5887
    iefix.setAttribute('src', 'javascript:false;');

    $$('UL.msgactions LI').each(function(li) {
        var fixcopy, ul = li.down('UL'), zindex;
        if (!ul) {
            return;
        }

        fixcopy = iefix.cloneNode(false);
        li.insert(fixcopy);
        fixcopy.clonePosition(ul);

        zindex = li.getStyle('zIndex');
        if (zindex == '') {
            li.setStyle({ zIndex: 2 });
            fixcopy.setStyle({ zIndex: 1 });
        } else {
            fixcopy.setStyle({ zIndex: parseInt(zindex) - 1 });
        }

        li.observe('mouseout', function() {
            this.removeClassName('hover');
            li.down('iframe').hide();
        });
        li.observe('mouseover', function() {
            this.addClassName('hover');
            li.down('iframe').show();
        });
    });
}

document.observe('dom:loaded', function() {
    // Set up left and right arrows to go to the previous/next page.
    document.observe('keydown', arrowHandler);

    if (Prototype.Browser.IE) {
         messageActionsHover();
    }
});
