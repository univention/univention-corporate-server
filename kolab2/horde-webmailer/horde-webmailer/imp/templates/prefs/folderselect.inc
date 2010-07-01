<?php if (!$prefs->isLocked('drafts_folder')): ?>
<script type="text/javascript">

function newDraftsFolderName()
{
    document.prefs.drafts.onchange = null;
    if (document.prefs.drafts[document.prefs.drafts.selectedIndex].value == '') {
        var folder = window.prompt('<?php echo addslashes(_("Enter the name for your new drafts folder")) ?>', document.prefs.drafts_new . value ? document.prefs.drafts_new.value : '');
        if (folder != '') {
            document.prefs.drafts_new.value = folder;
            document.prefs.drafts[1].text = '<?php echo addslashes(_("Create a new drafts folder")) ?> [' + document.prefs.drafts_new.value + ']';
        }
    }
    document.prefs.drafts.onchange = newDraftsFolderName;
}

</script>

<?php echo Horde::label('drafts', _("Drafts folder:")) ?><br />
<select id="drafts" name="drafts" onchange="newDraftsFolderName();">
  <option value="<?php echo IMP_PREF_NO_FOLDER ?>"><?php echo _("None") ?></option>
  <?php echo IMP::flistSelect(_("Create a new drafts folder"), true, array('INBOX'), IMP::folderPref($prefs->getValue('drafts_folder'), true)) ?>
</select><br />
<input type="hidden" name="drafts_new" value="" />
<?php endif; ?>
