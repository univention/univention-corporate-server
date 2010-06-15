<table border="0" cellspacing="0" cellpadding="1" width="100%">
<tr>
  <td align="left" class="header">
    <b><?php echo _("Pending Signups:") ?></b>
  </td>
</tr>
<tr>
  <td align="left" class="control">
    <?php printf(_("Are you sure you want to remove the signup request for %s ?"), $f_user_name) ?>

    <form method="post" action="<?php echo Horde::selfURL() ?>">
      <input type="hidden" name="form" value="removequeued" />
      <input type="hidden" name="user_name" value="<?php echo $f_user_name ?>" />

      <input class="button" type="submit" value="<?php echo _("Remove") ?>" />
    </form>
  </td>
</tr>
</table>
<br />
