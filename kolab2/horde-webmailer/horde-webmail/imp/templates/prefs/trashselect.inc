<?php if (!$prefs->isLocked('trash_folder') && !$prefs->isLocked('use_vtrash')): ?>
<script type="text/javascript">
function newTrashFolderName()
{
    var t = document.prefs.trash, tn = document.prefs.trash_new;
    t.onchange = null;
    if (t[t.selectedIndex].value == '') {
        var folder = window.prompt('<?php echo addslashes(_("Enter the name for your new trash folder")) ?>', tn.value ? tn.value : '');
        if (folder != '') {
            tn.value = folder;
            t[1].text = '<?php echo addslashes(_("Create a new trash folder")) ?> [' + tn.value + ']';
        }
    }
    t.onchange = newTrashFolderName;
}
</script>

<?php echo Horde::label('trash', _("Trash folder:")) ?><br />
<input type="hidden" name="trash_new" value="" />
<select id="trash" name="trash" onchange="newTrashFolderName();">
<?php
    $use_vtrash = $prefs->getValue('use_vtrash');
    echo '<option value="' . IMP_PREF_NO_FOLDER . '">' . _("None") . '</option>' .
    '<option value="' . IMP_PREF_VTRASH . '"' . (($use_vtrash) ? ' selected="selected"' : '') . '>' . _("Use Virtual Trash") . '</option>' .
    IMP::flistSelect(_("Create a new trash folder"), true, array('INBOX'), ($use_vtrash) ? null : IMP::folderPref($prefs->getValue('trash_folder'), true));
?>
</select>
<br />
<?php endif; ?>
