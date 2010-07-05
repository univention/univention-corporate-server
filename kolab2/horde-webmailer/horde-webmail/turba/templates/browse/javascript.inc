<script type="text/javascript">

function AnySelected()
{
    for (i = 0; i < document.contacts.elements.length; i++) {
        if (document.contacts.elements[i].checked) {
            return true;
        }
    }
    return false;
}

function Add(select)
{
    if (!AnySelected()) {
        window.alert('<?php echo addslashes(_("You must select at least one contact first.")) ?>');
        return false;
    }

    key = select[select.selectedIndex].value;
    if (key == '') {
        alert('<?php echo addslashes(_("You must select a target contact list.")) ?>');
        return false;
    }

    if (key.indexOf(':') == -1 || key.lastIndexOf(':') == key.length - 1) {
        var newList = window.prompt('<?php echo addslashes(_("Please name the new contact list:")) ?>\n', '');
        if (newList != null && newList != '') {
            if (key.lastIndexOf(':') == key.length - 1) {
                key = key.substr(0, key.length - 1);
            }
            document.contacts.targetAddressbook.value = key;
            document.contacts.targetNew.value = 1;
            document.contacts.targetList.value = newList;
        } else {
            return false;
        }
    } else {
        document.contacts.targetList.value = key;
    }

    Submit('add');
}

function CopyMove(action, select)
{
    if (!AnySelected()) {
        window.alert('<?php echo addslashes(_("You must select at least one contact first.")) ?>');
        return false;
    }

    key = select[select.selectedIndex].value;
    if (key == '') {
        alert('<?php echo addslashes(_("You must select a target address book.")) ?>');
        return false;
    }

    document.contacts.targetAddressbook.value = key;
    Submit(action);
}

function Submit(action)
{
    if (AnySelected()) {
        if (action != 'delete' ||
            confirm('<?php echo addslashes(_("Are you sure that you want to delete the selected contacts?")) ?>')) {
            document.contacts.actionID.value = action;
            document.contacts.submit();
        }
    } else {
        window.alert('<?php echo addslashes(_("You must select at least one contact first.")) ?>');
        return false;
    }
}

function SelectAll()
{
    for (var i = 0; i < document.contacts.elements.length; i++) {
        document.contacts.elements[i].checked = document.contacts.checkAll.checked;
    }
}

function confirmDelete(name)
{
    return confirm('<?php echo addslashes(_("Are you sure that you want to delete %s?")) ?>'.replace('%s', name));
}

</script>
