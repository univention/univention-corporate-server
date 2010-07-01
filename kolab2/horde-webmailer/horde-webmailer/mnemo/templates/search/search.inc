<form method="post" name="memo" enctype="multipart/form-data" action="<?php echo Horde::applicationUrl('list.php') ?>">
<input type="hidden" name="actionID" value="search_memos" />

<h1 class="header"><?php echo _("Search") ?></h1>

<table cellspacing="2" width="100%" class="item">
 <tr>
  <td class="rightAlign nowrap">
   <strong><?php echo Horde::label('search_pattern', _("_For: ")) ?></strong>
  </td>
  <td>
   <input name="search_pattern" id="search_pattern" type="text" value="" size="50" maxlength="100" />
  </td>
 </tr>
 <tr>
  <td class="rightAlign" valign="top">
   <strong><?php echo _("In: ") ?></strong>
  </td>
  <td>
   <input name="search_type" id="search_desc" value="desc" type="radio" checked="checked" /> <?php echo Horde::label('search_desc', _("_Title")) ?><br />
   <input name="search_type" id="search_body" value="body" type="radio" /> <?php echo Horde::label('search_body', _("_Body")) ?>
  </td>
 </tr>
</table>

<p>
 <input type="submit" class="button" value="<?php echo _("Search") ?>" />
</p>

</form>
