<?php if (!$prefs->isLocked('initial_page')):

if (empty($GLOBALS['conf']['user']['allow_folders'])) {
    $mailbox_option = '<option value="INBOX" selected="selected">' . _("Inbox") . '</option>';
} else {
    $mailbox_selected = $prefs->getValue('initial_page');
    $mailbox_option = '<option value="folders.php"';
    if ($mailbox_selected == 'folders.php') {
        $mailbox_option .= ' selected="selected"';
    }
    $mailbox_option .= '>' . _("Folder Navigator") . "</option>\n"
        . IMP::flistSelect('', true, array(), $mailbox_selected, false, false, true);
}
?>

<?php echo Horde::label('initial_page', _("View or mailbox to display after login:")) ?><br />
<select id="initial_page" name="initial_page">
 <?php echo $mailbox_option ?>
</select>
<br />
<?php endif; ?>
