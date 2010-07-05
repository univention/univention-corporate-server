<h1 class="header"><?php echo htmlspecialchars($title) ?></h1>

<div class="noteArea">
<?php
if ($memo_id):
    $memourl = Util::addParameter('memo.php', array('memo' => $memo_id,
                                                    'memolist' => $memolist_id));

    $share = &$GLOBALS['mnemo_shares']->getShare($memolist_id);
    if (!is_a($share, 'PEAR_Error') && $share->hasPermission(Auth::getAuth(), PERMS_DELETE)): ?>
 <span class="rightFloat"><input type="button" class="button" value="<?php echo _("Delete this note") ?>" onclick="window.location='<?php echo addslashes(Horde::applicationUrl(Util::addParameter($memourl, 'actionID', 'delete_memos'))) ?>';" /></span>
<?php endif; endif; ?>

<?php if ($actionID == 'modify_memo' && $show_passphrase): ?>
 <div class="notePassword">
  <form action="memo.php" name="passphrase" method="post">
   <?php echo Util::formInput() ?>
   <input type="hidden" name="actionID" value="modify_memo" />
   <input type="hidden" name="memolist" value="<?php echo $memolist_id ?>" />
   <input type="hidden" name="memo" value="<?php echo $memo_id ?>" />
   <?php echo Horde::label('memo_passphrase', _("_Password")) ?>:
   <input type="password" id="memo_passphrase" name="memo_passphrase" />
   <input type="submit" class="button" value="<?php echo _("Decrypt") ?>" />
  </form>
 </div>
 <script type="text/javascript" >
 document.passphrase.memo_passphrase.focus();
 </script>
<?php else: ?>
 <script type="text/javascript">
 function updateCharCount()
 {
<?php if (($GLOBALS['browser']->isBrowser('msie') &&
           $GLOBALS['browser']->getMajor() >= 4) ||
          ($GLOBALS['browser']->isBrowser('mozilla') &&
           $GLOBALS['browser']->getMajor() >= 5)): ?>
     if (document.getElementById('memo_body')) {
         document.getElementById('charcount').innerHTML = document.getElementById('memo_body').value.replace(/[\r\n]/g, '').length;
     }
<?php endif; ?>
 }
 </script>
 <?php echo $cManager->getJavaScript('memo', 'memo_category') ?>
 <form method="post" name="memo" action="memo.php">
 <?php Util::pFormInput() ?>
 <input type="hidden" name="actionID" value="save_memo" />
 <input type="hidden" name="memo" value="<?php echo htmlspecialchars($memo_id) ?>" />
 <input type="hidden" name="new_category" value="" />
 <input type="hidden" name="memolist_original" value="<?php echo htmlspecialchars($memolist_id) ?>" />
 <?php if ($prefs->isLocked('default_notepad') || count($notepads) <= 1): ?>
 <input type="hidden" name="notepad_target" value="<?php echo htmlspecialchars($memolist_id) ?>" />
<?php endif; ?>
 <p><?php echo Horde::label('memo_body', _("Note _Text")) ?>&nbsp;(<?php printf(_("%s characters"), '<span id="charcount">' . String::length(str_replace(array("\r", "\n"), '', $memo_body)) . '</span>') ?>):</p>
 <textarea name="memo_body" id="memo_body" class="fixed" rows="20" onchange="updateCharCount()" onclick="updateCharCount()" onkeypress="setTimeout('updateCharCount()', 1)"><?php echo htmlspecialchars($memo_body) ?></textarea>
 <?php echo Horde::callHook('_mnemo_hook_description_help', null, 'mnemo', '') ?>

 <p>
  <input type="submit" class="button" value="<?php echo _("Save") ?>" onclick="return checkCategory();" />
 </p>
 <table>
  <?php if (!$prefs->isLocked('default_notepad') && count($notepads) > 1): ?>
  <tr>
   <td class="rightAlign"><?php echo Horde::label('notepad_target', _("Note_pad:")) ?></td>
   <td>
    <select id="notepad_target" name="notepad_target">
     <?php
     foreach (array_keys($notepads) as $id) {
         $sel = ($id == $memolist_id) ? ' selected="selected"' : '';
         printf('<option value="%s"%s>%s</option>',
                htmlspecialchars($id), $sel, htmlspecialchars($notepads[$id]->get('name'))) . "\n";
     }
     ?>
    </select>
   </td>
  </tr>
  <?php endif; ?>
  <tr>
   <td class="rightAlign"><?php echo Horde::label('memo_category', _("_Category:")) ?></td>
   <td><?php echo $cManager->getSelect('memo_category', $memo_category) ?>
  </tr>
  <?php if ($storage->encryptionSupported()): ?>
  <?php if ($actionID == 'modify_memo' && $memo_encrypted && !$show_passphrase): ?>
  <tr>
   <td class="rightAlign"><?php echo Horde::label('memo_encrypt', _("_Encrypt?")) ?></td>
   <td><input type="checkbox" id="memo_encrypt" name="memo_encrypt" checked="checked" /></td>
  </tr>
  <?php endif; ?>
  <tr>
   <td class="rightAlign"><?php echo Horde::label('memo_passphrase', _("_Password:")) ?></td>
   <td><input type="password" id="memo_passphrase" name="memo_passphrase" /></td>
  </tr>
  <tr>
   <td class="rightAlign"><?php echo Horde::label('memo_passphrase2', _("_Repeat:")) ?></td>
   <td><input type="password" id="memo_passphrase2" name="memo_passphrase2" /></td>
  </tr>
  <?php endif; ?>
 </table>
</form>
<script type="text/javascript" >
document.memo.memo_body.focus();
</script>
<?php endif; ?>
</div>
