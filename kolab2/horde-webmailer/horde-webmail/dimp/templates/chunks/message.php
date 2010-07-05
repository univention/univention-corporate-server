<?php
/**
 * $Horde: dimp/templates/chunks/message.php,v 1.1.2.9 2009-01-06 15:22:45 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

$dimp_img = $registry->getImageDir('dimp');
$horde_img = $registry->getImageDir('horde');
$menu_view = $prefs->getValue('menu_view');
$show_text = ($menu_view == 'text' || $menu_view == 'both');

$attachment = Horde::img('attachment.png', '', array('class' => 'attachmentImage'), $dimp_img);

// Small utility function to simplify creating dimpactions buttons.
// As of right now, we don't show text only links.
function _createDAfmsg($text, $image, $id, $class = '', $show_text = true)
{
    $params = array('icon' => $image, 'id' => $id, 'class' => $class);
    if ($show_text) {
        $params['title'] = $text;
    } else {
        $params['tooltip'] = $text;
    }
    echo DIMP::actionButton($params);
}

?>
<div id="pageContainer">
 <div id="msgData">
  <div class="noprint">
   <div class="header">
    <div class="headercloseimg" id="windowclose"><?php echo Horde::img('close.png', 'X', array(), $horde_img) ?></div>
    <div><?php echo _("Message:") . ' ' . $show_msg_result['subject'] ?></div>
   </div>

   <div class="dimpActions">
    <span id="button_reply_cont"><?php _createDAfmsg(_("Reply"), 'reply_menu.png', 'reply_link', 'hasmenu', $show_text) ?></span>
    <span id="button_forward_cont"><?php _createDAfmsg(_("Forward"), 'forward_menu.png', 'forward_link', 'hasmenu', $show_text) ?></span>
<?php if (!empty($conf['spam']['reporting']) && (!$conf['spam']['spamfolder'] || ($folder != IMP::folderPref($prefs->getValue('spam_folder'), true)))): ?>
    <span><?php _createDAfmsg(_("Report Spam"), 'spam_menu.png', 'button_spam', '', $show_text) ?></span>
<?php endif; ?>
<?php if (!empty($conf['notspam']['reporting']) && (!$conf['notspam']['spamfolder'] || ($folder == IMP::folderPref($prefs->getValue('spam_folder'), true)))): ?>
    <span><?php _createDAfmsg(_("Report Innocent"), 'ham_menu.png', 'button_ham', '', $show_text) ?></span>
<?php endif; ?>
    <span class="lastnavbar"><?php _createDAfmsg(_("Delete"), 'delete_menu.png', 'button_deleted', '', $show_text) ?></span>
   </div>
  </div>

  <div class="msgfullread">
   <div class="msgHeaders">
    <div id="msgHeaders">
     <div class="dimpOptions noprint">
      <a id="msg_print"><?php echo Horde::img('print.png', '', '', $horde_img) . _("Print") ?></a>
<?php if (!empty($conf['user']['allow_view_source'])): ?>
      <br />
      <a id="msg_view_source"><?php echo Horde::img('message_source.png', '', '', $dimp_img) . _("View Message Source") ?></a>
<?php endif; ?>
     </div>
     <div id="msgHeadersContent">
      <table cellspacing="0">
       <thead>
        <tr>
         <td class="label"><?php echo _("Subject") ?>:</td>
         <td class="subject"><?php echo $show_msg_result['subject'] ?></td>
        </tr>
<?php foreach($show_msg_result['headers'] as $val): ?>
        <tr<?php if (isset($val['id'])): ?> id="msgHeader<?php echo $val['id'] ?>"<?php endif; ?>>
         <td class="label"><?php echo $val['name'] ?>:</td>
         <td><?php echo $val['value'] ?></td>
        </tr>
<?php endforeach; ?>
<?php if (isset($show_msg_result['atc_label'])): ?>
        <tr id="msgAtc">
         <td class="label"><?php if ($show_msg_result['atc_list']): ?><?php echo Horde::link('') . Horde::img('arrow_collapsed.png', '', array('id' => 'partlist_col'), $dimp_img) . Horde::img('arrow_expanded.png', '', array('id' => 'partlist_exp', 'style' => 'display:none'), $dimp_img) . ' ' . $attachment ?></a><?php else: echo $attachment; endif; ?></td>
         <td>
          <?php echo $show_msg_result['atc_label'] . ' ' . $show_msg_result['atc_download'] ?>
<?php if (isset($show_msg_result['atc_list'])): ?>
          <table id="partlist" cellspacing="2">
           <?php echo $show_msg_result['atc_list'] ?>
          </table>
<?php endif; ?>
         </td>
        </tr>
<?php endif; ?>
       </thead>
      </table>
     </div>
    </div>
   </div>
   <div class="msgBody">
    <table width="100%" cellspacing="0">
     <?php echo $show_msg_result['msgtext'] ?>
    </table>
   </div>
  </div>
 </div>

 <div id="qreply" style="display:none;">
  <div class="header">
   <div class="headercloseimg"><?php echo Horde::img('close.png', 'X', array(), $horde_img) ?></div>
   <div><?php echo _("Message:") . ' ' . $show_msg_result['subject'] ?></div>
  </div>
  <?php echo $compose_result['html']; ?>
 </div>
</div>

<div class="context" id="ctx_replypopdown">
 <div><?php _createDAfmsg(_("To Sender"), 'reply.png', 'ctx_replypopdown_reply') ?></div>
 <div><?php _createDAfmsg(_("To All"), 'replyall.png', 'ctx_replypopdown_reply_all') ?></div>
<?php if ($ob->header->listHeadersExist()): ?>
 <div><?php _createDAfmsg(_("To List"), 'replyall.png', 'ctx_replypopdown_reply_list') ?></div>
<?php endif; ?>
</div>

<div class="context" id="ctx_fwdpopdown">
 <div><?php _createDAfmsg(_("Entire Message"), 'forward.png', 'ctx_fwdpopdown_forward_all') ?></div>
 <div><?php _createDAfmsg(_("Body Text Only"), 'forward.png', 'ctx_fwdpopdown_forward_body') ?></div>
 <div><?php _createDAfmsg(_("Attachments Only"), 'forward.png', 'ctx_fwdpopdown_forward_attachments') ?></div>
</div>

<div class="context" id="ctx_contacts">
 <div><?php _createDAfmsg(_("New Message"), 'compose.png', 'ctx_contacts_new') ?></div>
 <div><?php _createDAfmsg(_("Add to Address Book"), 'add_contact.png', 'ctx_contacts_add') ?></div>
</div>

<?php echo Horde::img('popdown.png', 'v', array('class' => 'popdown', 'id' => 'popdown_img', 'style' => 'display:none'), $dimp_img) ?>
