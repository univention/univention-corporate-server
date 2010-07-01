<form method="post" name="dateform" action="<?php echo Horde::applicationUrl('data.php') ?>">
<input type="hidden" name="actionID" value="<?php echo (int)$next_step ?>" />
<input type="hidden" name="import_format" value="<?php echo htmlspecialchars(Util::getFormData('import_format')) ?>" />
<input type="hidden" name="import_step" value="<?php echo (int)$import_step ?>" />
<?php Util::pformInput() ?>
<h1 class="header">
 <?php printf(_("Import, Step %d"), (int)$import_step) ?>
</h1>
<table cellspacing="0" width="100%">
<?php foreach ($_SESSION['import_data']['dates'] as $key => $date): ?>
<tr>
    <td>
        <table cellspacing="0" width="100%">
        <tr><td class="item">&nbsp;</td></tr>
        <tr><td class="smallheader"><?php printf(_("Imported field: %s"), htmlspecialchars($app_fields[$_SESSION['import_data']['map'][$key]])) ?></td></tr>
        </table>
    </td>
</tr>
<tr>
    <td class="item">
    <table>
<?php if (count($date['values'])): ?>
    <tr>
        <td><?php echo Horde::label('examples', _("Example values:")) ?></td>
        <td>
            <select id="examples">
<?php foreach ($date['values'] as $val): ?>
                <option><?php echo htmlspecialchars($val) ?></option>
<?php endforeach; ?>
            </select>
        </td>
    </tr>
<?php endif; ?>
<?php include dirname(__FILE__) . '/' . basename($date['type']) . '.inc' ?>
    </table>
    </td>
</tr>
<?php endforeach; ?>
</table>

<input type="submit" class="button" value="<?php echo _("Next") ?>" />
</form>
