<?php if (!$prefs->isLocked('spam_folder')): ?>
<script type="text/javascript">

function newSpamFolderName()
{
    document.prefs.spam.onchange = null;
    if (document.prefs.spam[document.prefs.spam.selectedIndex].value == '') {
        var folder = window.prompt('<?php echo addslashes(_("Enter the name for your new Spam folder")) ?>', document.prefs.spam_new.value ? document.prefs.spam_new.value : '');
        if (folder != '') {
            document.prefs.spam_new.value = folder;
            document.prefs.spam[1].text = '<?php echo addslashes(_("Create a new Spam folder")) ?> [' + document.prefs.spam_new.value + ']';
        }
    }
    document.prefs.spam.onchange = newSpamFolderName;
}

</script>

<?php echo Horde::label('spam', _("Spam folder:")) ?><br />
<select id="spam" name="spam" onchange="newSpamFolderName();"><option value="<?php echo IMP_PREF_NO_FOLDER ?>"><?php echo _("None") ?></option><?php echo IMP::flistSelect(_("Create a new Spam folder"), true, array('INBOX'), IMP::folderPref($prefs->getValue('spam_folder'), true)) ?></select>
<input type="hidden" name="spam_new" value="" />
<?php endif; ?>
