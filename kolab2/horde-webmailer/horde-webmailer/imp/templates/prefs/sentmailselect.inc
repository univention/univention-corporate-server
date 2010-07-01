<?php if (!$prefs->isLocked('sent_mail_folder')): ?>
<script type="text/javascript">

function newChoice_sent_mail_folder(val)
{
    if (val == "") {
        document.prefs.sent_mail_folder.selectedIndex = 0;
        return;
    }
    var field = document.prefs.sent_mail_folder;
    for (var i = 0; i < field.options.length; i++) {
        if (field.options[i].value == val) {
            field.selectedIndex = i;
            break;
        }
    }
}

function newFolderName()
{
    if (document.prefs.sent_mail_folder.selectedIndex == 2) {
        var folder = window.prompt('<?php echo addslashes(_("Enter the name for your new sent mail folder")) ?>', document.prefs.sent_mail_new.value ? document.prefs.sent_mail_new.value : '');
        if (folder != '' && folder != null) {
            document.prefs.sent_mail_new.value = folder;
            document.prefs.sent_mail_folder[2].text = '<?php echo addslashes(_("Create a new sent mail folder")) ?> [' + document.prefs.sent_mail_new.value + ']';
        }
    }

    if (document.prefs.sent_mail_folder.selectedIndex == 0) {
        document.prefs.save_sent_mail.checked = 0;
    }
}

</script>

<?php echo Horde::label('sent_mail_folder', _("Sent mail folder:")) ?><br />
<select name="sent_mail_folder" id="sent_mail_folder" onchange="newFolderName();">
  <option value=""><?php echo _("None") ?></option>
  <option value="-1" selected="selected"><?php echo _("Use Default Value") ?></option>
  <?php echo IMP::flistSelect(_("Create a new sent mail folder"), true, array('INBOX')) ?>
</select><br />
<input type="hidden" name="sent_mail_new" value="" />
<?php endif; ?>
