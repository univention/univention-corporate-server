<form method="post" name="dateform" action="<?php echo Horde::applicationUrl('data.php') ?>">
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
<?php foreach ($_SESSION['import_data']['dates'] as $key => $date): ?>
<?php if (count($date['values']) > 0): ?>
<tr>
    <td>
        <table cellpadding="2" cellspacing="0" border="0" width="100%">
        <tr><td class="item">&nbsp;</td></tr>
        <tr><td class="smallheader"><b><?php echo sprintf(_("Imported field: %s"), $app_fields[$_SESSION['import_data']['map'][$key]]) ?></b></td></tr>
        </table>
    </td>
</tr>
<tr>
    <td class="item">
    <table border="0">
    <tr>
        <td><?php echo _("Example values:") ?></td>
        <td>
            <select>
<?php foreach ($date['values'] as $val): ?>
                <option><?php echo $val ?></option>
<?php endforeach; ?>
            </select>
        </td>
    </tr>
<?php include $registry->getParam('templates', 'horde') . '/data/' . $date['type'] . '.inc'; ?>
    </table>
    </td>
</tr>
<?php endif; ?>
<?php endforeach; ?>
<tr>
    <td>
        <table cellpadding="2" cellspacing="0" border="0" width="100%">
        <tr><td class="item"><input type="submit" class="button" value="<?php echo _("Next") ?>" /></td></tr>
        </table>
    </td>
</tr>
</table>
</form>
