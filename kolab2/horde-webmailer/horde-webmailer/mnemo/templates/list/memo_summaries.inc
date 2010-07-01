 <tr>
  <td>
<?php
if (!is_a($share, 'PEAR_Error') && $share->hasPermission(Auth::getAuth(), PERMS_EDIT)) {
    $label = sprintf(_("Edit \"%s\""), $memo['desc']);
    echo Horde::link(Horde::applicationUrl(Util::addParameter($memourl, 'actionID', 'modify_memo')), $label) .
        Horde::img('edit.png', $label, '', $registry->getImageDir('horde')) . '</a>';
}
?>
  </td>
<?php if ($showNotepad): ?>
  <td><?php echo htmlspecialchars($notepad) ?></td>
<?php endif; ?>
  <td>
   <?php echo Horde::linkTooltip(Horde::applicationUrl($viewurl), '', '', '', '', ($memo['body'] != $memo['desc']) ? Mnemo::getNotePreview($memo) : '') . (strlen($memo['desc']) ? htmlspecialchars($memo['desc']) : '<em>' . _("Empty Note") . '</em>') ?></a>
  </td>
  <td class="category<?php echo md5($memo['category']) ?>"><?php echo htmlspecialchars($memo['category'] ? $memo['category'] : _("Unfiled")) ?></td>
 </tr>
