<form method="post" name="import_form" action="<?php echo Horde::applicationUrl('data.php') ?>">
<input type="hidden" name="actionID" value="<?php echo $next_step ?>" />
<input type="hidden" name="import_format" value="csv" />
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
    <?php echo _("What is the delimiter character?") ?>
    <input type="text" name="sep" size="1" value="<?php echo htmlspecialchars($_SESSION['import_data']['sep']) ?>" /><br />
    <?php if (array_key_exists('quote', $_SESSION['import_data'])): ?>
    <?php echo _("What is the quote character?") ?>
    <input type="text" name="quote" size="1" value="<?php echo htmlspecialchars($_SESSION['import_data']['quote']) ?>" /><br />
    <?php endif; ?>
    <?php if (array_key_exists('fields', $_SESSION['import_data'])): ?>
    <?php echo _("How many fields (columns) are there?") ?>
    <input type="text" name="fields" size="2" value="<?php echo $_SESSION['import_data']['fields'] ?>" /><br />
    <?php endif; ?>
    <br />
    <input type="submit" value="<?php echo _("Next") ?>" class="button" />
  </td></tr></table>
  </td>
</tr>
</table>
</form>
