<?php echo Horde::label('default_encrypt', _("Your default encryption method for sending messages:")) ?><br />
<select id="default_encrypt" name="default_encrypt">
 <?php echo IMP::encryptList() ?>
</select>
<br />
