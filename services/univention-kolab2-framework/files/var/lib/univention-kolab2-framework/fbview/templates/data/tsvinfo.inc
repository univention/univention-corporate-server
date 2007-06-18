<form method="post" name="import_form" action="<?php echo Horde::applicationUrl('data.php') ?>">
<input type="hidden" name="actionID" value="<?php echo $next_step ?>" />
<input type="hidden" name="import_format" value="<?php echo Util::getFormData('import_format') ?>" />
<input type="hidden" name="import_step" value="<?php echo $import_step ?>" />
<?php Util::pformInput() ?>
<table cellspacing="0" cellpadding="0" border="0" width="100%">
<tr>
    <td>
        <table cellpadding="3" cellspacing="0" border="0" width="100%">
        <tr><td class="header" align="center"><?php echo sprintf(_("Import, Step %d"), $import_step) ?></td>
        </tr></table>
    </td>
</tr>
<tr>
    <td class="item">
    <table border="0"><tr><td>
        <?php echo _("Here is the beginning of the file:") ?><br />
        <pre><?php echo htmlspecialchars($_SESSION['import_data']['first_lines']) ?></pre>
        <label for="header"><?php echo _("Does the first row contain the field names? If yes, check this box:") ?></label>
        <input id="header" type="checkbox" name="header" value="1" /><br />
        <input type="submit" value="<?php echo _("Next") ?>" class="button" />
    </td></tr></table>
    </td>
</tr>
</table>
</form>
