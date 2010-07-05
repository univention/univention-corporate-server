<?php
$memourl = Util::addParameter('memo.php', array('memo' => $memo_id,
                                                'memolist' => $memolist_id));

$share = &$GLOBALS['mnemo_shares']->getShare($memolist_id);
?>
<div class="header">
 <div class="rightFloat">
<?php
if (!$print_view) {
    echo Horde::widget(Horde::applicationUrl(Util::addParameter('note/pdf.php', array('note' => $memo_id, 'notepad' => $memolist_id))), _("Save as PDF"), 'smallheader');
    if ($share->hasPermission(Auth::getAuth(), PERMS_EDIT)) {
        echo ' | ' . Horde::widget(Horde::applicationUrl(Util::addParameter($memourl, 'actionID', 'modify_memo')), _("Edit"), 'smallheader', '', '', _("_Edit"));
    }
    if ($share->hasPermission(Auth::getAuth(), PERMS_DELETE)) {
        echo ' | ' . Horde::widget(Horde::applicationUrl(Util::addParameter($memourl, 'actionID', 'delete_memos')), _("Delete"), 'smallheader', '', $prefs->getValue('delete_opt') ? 'return window.confirm(\'' . addslashes(_("Really delete this note?")) . '\');' : '', _("_Delete"));
    }
}
?>
 </div>
 <?php echo htmlspecialchars($title) ?>
</div>

<table cellspacing="0" width="100%" class="headerbox striped nowrap">
<tr>
  <td class="rightAlign"><strong><?php echo _("Category") ?></strong>&nbsp;</td>
  <td width="100%"><?php echo htmlspecialchars($memo['category'] ? $memo['category'] : _("Unfiled")) ?></td>
</tr>

<?php if (isset($created)): ?>
<tr>
  <td align="right"><strong><?php echo _("Created") ?></strong>&nbsp;</td>
  <td><?php echo strftime($prefs->getValue('date_format'), $created) . ' ' . date($prefs->getValue('twentyFour') ? 'G:i' : 'g:i a', $created) . ' ' . @htmlspecialchars($createdby, ENT_COMPAT, NLS::getCharset()) ?></td>
</tr>
<?php endif; ?>

<?php if (isset($modified)): ?>
<tr>
  <td align="right"><strong><?php echo _("Last Modified") ?></strong>&nbsp;</td>
  <td><?php echo strftime($prefs->getValue('date_format'), $modified) . ' ' . date($prefs->getValue('twentyFour') ? 'G:i' : 'g:i a', $modified) . ' ' . @htmlspecialchars($modifiedby, ENT_COMPAT, NLS::getCharset()) ?></td>
</tr>
<?php endif; ?>

 <tr>
  <td colspan="2">
<?php if ($show_passphrase): ?>
   <div class="notePassphrase">
    <form action="view.php" name="passphrase" method="post">
     <?php echo Util::formInput() ?>
     <input type="hidden" name="memolist" value="<?php echo $memolist_id ?>" />
     <input type="hidden" name="memo" value="<?php echo $memo_id ?>" />
     <?php echo Horde::label('memo_passphrase', _("_Password")) ?>:
     <input type="password" id="memo_passphrase" name="memo_passphrase" />
     <input type="submit" class="button" value="<?php echo _("Decrypt") ?>" />
    </form>
   </div>
<?php else: ?>
   <div class="noteBody">
    <?php $body = Text_Filter::filter($memo['body'], 'text2html', array('parselevel' => TEXT_HTML_MICRO, 'class' => null)); echo Horde::callHook('_mnemo_hook_format_description', array($body), 'mnemo', $body); ?>
   </div>
<?php endif; ?>
  </td>
 </tr>
</table>
<?php if ($show_passphrase): ?>
<script type="text/javascript" >
document.passphrase.memo_passphrase.focus();
</script>
<?php endif; ?>
