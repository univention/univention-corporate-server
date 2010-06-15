<table cellpadding="0" cellspacing="0" border="0" width="100%">
<tr>

<?php $count = 0; foreach ($columns as $key => $col): ?>
    <td width="<?php echo $span ?>%">
        <table cellpadding="0" cellspacing="0" border="0" width="100%">
        <tr><td class="header" align="center"><b><?php echo $key ?></b></td></tr>
        </table>
    </td>

<?php $count++; if ($count < count($columns)): ?>
    <td width="1%" rowspan="5">&nbsp;</td>
<?php endif; ?>
<?php endforeach; ?>

</tr>
<tr valign="top">

<?php foreach ($columns as $key => $column): ?>
    <td width="<?php echo $span ?>%">
        <table cellpadding="2" cellspacing="0" border="0" width="100%">

<?php foreach ($column as $group => $gvals): ?>
<?php if (Prefs_UI::groupIsEditable($group)): ?>
<?php if (!empty($gvals['url'])): ?>
            <tr><td class="control"><b><?php echo Horde::widget(Horde::applicationUrl($gvals['url'], $app), $gvals['label'], 'widget', '', '', $gvals['label']) ?></b></td></tr>
<?php else: ?>
            <tr><td class="control"><b><?php echo Horde::widget(Util::addParameter(Horde::selfURL(), array('group' => $group, 'app' => $GLOBALS['app'])), $gvals['label'], 'widget', '', '', $gvals['label']) ?></b></td></tr>
<?php endif; ?>
            <tr><td class="item"><?php echo $gvals['desc'] ?></td></tr>
            <tr><td style="font-size:3px;">&nbsp;</td></tr>
<?php endif; ?>
<?php endforeach; ?>

        </table>
    </td>
<?php endforeach; ?>

</tr>
</table>
<br />
