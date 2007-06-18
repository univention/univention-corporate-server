<script language="JavaScript" type="text/javascript">
<!--

function AnySelected()
{
    for (i = 0; i < document.contacts.elements.length; i++) {
        if (document.contacts.elements[i].checked) {
            return true;
        }
    }
    return false;
}

function Add() 
{
    key = document.targetList.listList[document.targetList.listList.selectedIndex].value;
    if (key == '') {
        alert('<?php echo addslashes(_("You must select a target list.")) ?>');
        return false;
    }

    document.contacts.targetList.value = key;

    if (key == "*new*") {
        var newList = window.prompt('<?php echo addslashes(_("You are creating a distribution list.")) . '\n' . addslashes(_("Please enter the name of the new list:")) ?>\n', '');
        if (newList != null && newList != '') {
            document.contacts.targetNew.value = 1;
            document.contacts.targetList.value = newList;
        } else {
            return false;
        }
    }

    Submit('add');
}

function CopyMove(action)
{
    key = document.copymove.targetAddressbook[document.copymove.targetAddressbook.selectedIndex].value;
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
            confirm('<?php echo addslashes(_("Are you sure that you want to delete the selected entries?")) ?>')) {
            document.contacts.actionID.value = action;
            document.contacts.submit();
        }
    } else {
        window.alert('<?php echo addslashes(_("You must select at least one entry first.")) ?>');
        return false;
    }
}

function Sort(col, direction)
{
    document.contacts.sortby.value = col;
    document.contacts.sortdir.value = direction;
    document.contacts.submit();
}

function SelectAll()
{
    for (i = 0; i < document.contacts.elements.length; i++) {
        document.contacts.elements[i].checked = document.contacts.checkAll.checked;
    }
}

function confirmDelete(name)
{
    return confirm('<?php echo addslashes(_("Are you sure that you want to delete %s?")) ?>'.replace('%s', name));
}

//-->
</script>
