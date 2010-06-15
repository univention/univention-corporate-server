<form method="post" name="prefs" action="<?php echo Horde::selfURL() ?>">
<?php Util::pformInput() ?>
<input type="hidden" name="actionID" value="update_prefs" />
<input type="hidden" name="group" value="<?php echo $group ?>" />
<input type="hidden" name="app" value="<?php echo $app ?>" />

<table border="0" align="center" width="100%" cellspacing="0" cellpadding="0">
<tr><td class="header" align="left"><b><?php echo $prefGroups[$group]['label'] ?></b></td>
<?php Prefs_UI::generateNavigationCell($group) ?>
</tr>
</table>
<table border="0" align="center" width="100%" cellspacing="0" cellpadding="3">
<tr><td class="item"><table border="0"><tr valign="top"><td class="item">
