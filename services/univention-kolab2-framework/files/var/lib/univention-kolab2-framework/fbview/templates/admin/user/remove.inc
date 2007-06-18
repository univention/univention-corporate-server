<form name="removeuser" method="post">
<input type="hidden" name="form" value="remove">

<table border="0" cellspacing="0" cellpadding="2">
<tr>
    <td align="left" class="header">
        <b><?php printf(_("Remove user: %s"), $f_user_name) ?></b>
    </td>
</tr>
<tr>
<td class="item">
<b><?php printf(_("Really delete %s? This operation cannot be undone."), $f_user_name) ?></b>
</td>
<tr>
  <td class="smallheader" align="right">
    <input type="submit" class="button" name="submit" value="<?php echo _("Remove user") ?>" />
    <input type="submit" class="button" name="submit" value="<?php echo _("Cancel") ?>" />
  </td>
</table>
</form>

<br />
