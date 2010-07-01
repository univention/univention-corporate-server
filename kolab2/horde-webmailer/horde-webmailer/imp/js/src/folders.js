/**
 * IMP Folders Javascript
 *
 * Provides the javascript to help the folders.php script.
 * This file should be included via Horde::addScriptFile().
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * $Horde: imp/js/src/folders.js,v 1.9.2.3 2009-10-12 22:36:34 slusarz Exp $
 */

function getChecked()
{
    return getFolders().findAll(function(e) {
        return e.checked;
    });
}

function getFolders()
{
    return $('fmanager').getInputs(null, 'folder_list[]');
}

function selectedFoldersDisplay()
{
    var folder = 0, sel = "";
    getFolders().each(function(e) {
        if (e.checked) {
            sel += displayNames[folder] + "\n";
        }
        ++folder;
    });

    if (sel.endsWith("\n")) {
        sel = sel.substring(0, sel.length - 1);
    }

    return sel;
}

function chooseAction(e)
{
    var id = (e.element().id == 'action_choose0') ? 0 : 1;

    var a = $('action_choose' + id);
    var action = $F(a);
    a.selectedIndex = 0;

    if (action == 'create_folder') {
        createMailbox();
    } else if (action == 'rebuild_tree') {
        submitAction(action);
    } else if (!getChecked().size()) {
        if (action != '') {
            alert(IMP.text.folders_select);
        }
    } else if (action == 'rename_folder') {
        renameMailbox();
    } else if (action == 'subscribe_folder' ||
               action == 'unsubscribe_folder' ||
               action == 'poll_folder' ||
               action == 'expunge_folder' ||
               action == 'nopoll_folder' ||
               action == 'mark_folder_seen' ||
               action == 'mark_folder_unseen' ||
               action == 'delete_folder_confirm' ||
               action == 'folders_empty_mailbox_confirm' ||
               action == 'mbox_size') {
        submitAction(action);
    } else if (action == 'download_folder' ||
               action == 'download_folder_zip') {
        downloadMailbox(action);
    } else if (action == 'import_mbox') {
        if (getChecked().length > 1) {
            alert(IMP.text.folders_oneselect);
        } else {
            submitAction(action);
        }
    }
}

function submitAction(a)
{
    $('actionID').setValue(a);
    $('fmanager').submit();
}

function createMailbox()
{
    var count = getChecked().size(), mbox;
    if (count > 1) {
        window.alert(IMP.text.folders_oneselect);
        return;
    }

    if (count == 1) {
        mbox = window.prompt(IMP.text.folders_subfolder1 + ' ' + selectedFoldersDisplay() + ".\n" + IMP.text.folders_subfolder2 + "\n", '');
    } else {
        mbox = window.prompt(IMP.text.folders_toplevel, '');
    }

    if (mbox) {
        $('new_mailbox').setValue(mbox);
        submitAction('create_folder');
    }
}

function downloadMailbox(actionid)
{
    if (window.confirm(IMP.text.folders_download1 + "\n" + selectedFoldersDisplay() + "\n" + IMP.text.folders_download2)) {
        submitAction(actionid);
    }
}

function renameMailbox()
{
    var newnames = '', oldnames = '', j = 0;

    getFolders().each(function(f) {
        if (f.checked) {
            if (IMP.conf.fixed_folders.indexOf(displayNames[j]) != -1) {
                window.alert(IMP.text.folders_no_rename + ' ' + displayNames[j]);
            } else {
                var tmp = window.prompt(IMP.text.folders_rename1 + ' ' + displayNames[j] + "\n" + IMP.text.folders_rename2, fullNames[j] ? fullNames[j] : displayNames[j]);
                if (tmp) {
                    newnames += tmp + "\n";
                    oldnames += f.value + "\n";
                }
            }
        }
        ++j;
    });

    if (!newnames) {
        return;
    }

    if (newnames.endsWith("\n")) {
        newnames = newnames.substring(0, newnames.length - 1);
    }
    if (oldnames.endsWith("\n")) {
        oldnames = oldnames.substring(0, oldnames.length - 1);
    }

    $('new_names').setValue(newnames);
    $('old_names').setValue(oldnames);
    submitAction('rename_folder');
    return true;
}

function toggleSelection()
{
    var count = getChecked().size(), folders = getFolders();
    var checked = (count != folders.size());
    folders.each(function(f) {
        f.checked = checked;
    });
}

document.observe('dom:loaded', function() {
    if ($('checkAll0')) {
        $('checkAll0').observe('click', toggleSelection);
        $('action_choose0').observe('change', chooseAction);
    }
    if ($('checkAll1')) {
        $('checkAll1').observe('click', toggleSelection);
        $('action_choose1').observe('change', chooseAction);
    }
});
