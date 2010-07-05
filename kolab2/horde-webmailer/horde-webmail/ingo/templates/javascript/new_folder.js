function newFolderName(name, tagname)
{
    var form = document.getElementsByName(name);
    var selector = form[0].elements.namedItem(tagname);

    if (selector.selectedIndex == 1){
        var folder = window.prompt('<?php echo addslashes(_("Please enter the name of the new folder:")) ?>\n', '');

        if ((folder != null) && (folder != '')) {
            form[0].actionID.value = 'create_folder';
            form[0].new_folder_name.value = folder;
            form[0].submit();
        }
    }

    return true;
}
