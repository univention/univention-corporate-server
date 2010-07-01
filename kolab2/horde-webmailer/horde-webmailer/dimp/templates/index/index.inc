<?php
// $Horde: dimp/templates/index/index.inc,v 1.152.2.65 2008-12-07 22:22:20 slusarz Exp $

// Generate various dimp graphics
$imagedir = $registry->getImageDir('dimp');
$mailseen = Horde::img('mail_seen.png');
$mailunseen = Horde::img('mail_unseen.png');
$delete = Horde::img('delete.png', '', '', $imagedir);
$folder_create = Horde::img('folders/folder_create.png');
$folder_edit = Horde::img('folders/folder_edit.png');
$forward = Horde::img('forward.png', '', '', $imagedir);
$flagged = Horde::img('mail_flagged.png');
$clearflag = Horde::img('mail_clearflag.png');
$preview = Horde::img('preview.png', '', '', $imagedir);
$tick = Horde::img('tick.png', '', '', $imagedir);
$newwin = Horde::img('newwin.png', _("Open in new window"), '', $imagedir);
$attachment = Horde::img('attachment.png', '', array('class' => 'attachmentImage'));

// Thread images
require_once IMP_BASE . '/lib/IMAP/Thread.php';
$thread_imgs = IMP_Thread::getImageUrls();

// Attachment images
require_once IMP_BASE . '/lib/UI/Mailbox.php';
$imp_ui = new IMP_UI_Mailbox();
$atc_imgs = array();
foreach ($imp_ui->getAttachmentAltList() as $k => $v) {
    $atc_imgs[] = Horde::img($k . '.png', $v, array('id' => 'atc_img_' . $k));
}

$usetrash = $prefs->getValue('use_trash') || $prefs->getValue('use_vtrash');
$menu_view = $prefs->getValue('menu_view');
$show_text = ($menu_view == 'text' || $menu_view == 'both');
$loading_text = _("Loading...");

$has_blacklist = $registry->hasMethod('mail/blacklistFrom');
$has_whitelist = $registry->hasMethod('mail/whitelistFrom');

// Sidebar width
$sidebar_width = max((int)$prefs->getValue('sidebar_width') - 50, 150) . 'px';

// Small utility function to simplify creating dimpactions buttons.
// As of right now, we don't show text only links.
function _createDA($text, $image, $id = null, $class = '', $show_text = true)
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
<div id="dimpLoading"><?php echo $loading_text ?></div>
<div id="dimpPage" style="display:none;">
 <div id="header"></div>
 <div id="pageContainer">
  <div id="sidebarPanel" class="noprint" style="width:<?php echo $sidebar_width ?>">
   <div id="logo"><h1><a><?php echo _("Horde") ?></a></h1></div>
   <p id="dimpbarActions">
    <span class="composelink"><?php _createDA(_("New Message"), 'compose.png') ?></span>
    <span class="refreshlink"><?php _createDA(_("Get Mail"), 'checkmail.png', 'button_checkmail') ?></span>
   </p>
    <div class="sepfull" style="width:<?php echo $sidebar_width ?>"></div>
   <ul id="serviceActions">
<?php if ($registry->get('status', 'horde') != 'hidden' && $registry->get('status', 'horde') != 'notoolbar'): ?>
    <li class="servicelink">
     <?php echo DIMP::actionButton(array('title' => _("Portal"), 'icon' => 'horde.png', 'id' => 'appportal', 'app' => 'horde')) ?>
    </li>
<?php endif; ?>
<?php if (Horde::showService('options')): ?>
    <li class="servicelink">
     <?php echo DIMP::actionButton(array('title' => _("Options"), 'icon' => 'prefs.png', 'id' => 'appoptions', 'app' => 'horde')) ?>
    </li>
<?php endif; ?>
<?php if (Horde::showService('logout')): ?>
    <li class="servicelink">
     <?php echo DIMP::actionButton(array('title' => _("Log Out"), 'icon' => 'logout.png', 'id' => 'applogout', 'app' => 'horde')) ?>
    </li>
<?php endif; ?>
   </ul>
   <div class="sepfull" style="width:<?php echo $sidebar_width ?>"></div>
   <div id="foldersLoading"><?php echo $loading_text ?></div>
   <div id="foldersSidebar" style="display:none;">
    <ul class="folderlist" id="specialfolders"></ul>
<?php if (!empty($application_folders)): ?>
    <div id="applicationfolders">
     <div class="sep">&nbsp;</div>
     <ul>
<?php foreach ($application_folders as $val): ?>
      <li class="custom">
       <a title="<?php echo $val['name'] ?>" id="app<?php echo $val['app'] ?>" app="<?php echo $val['app'] ?>"><img src="<?php echo $val['icon'] ?>" alt="<?php echo $val['name'] ?>" /><?php echo $val['name'] ?></a>
      </li>
<?php endforeach; ?>
     </ul>
    </div>
<?php endif; ?>
<?php if (!empty($site_menu)): ?>
    <div id="sitemenu">
     <div class="sep">&nbsp;</div>
     <ul>
<?php foreach ($site_menu as $key => $menu_item): ?>
<?php if ($menu_item == 'separator'): ?>
     </ul>
     <div class="sep">&nbsp;</div>
     <ul>
<?php else: ?>
      <li class="custom">
       <a title="<?php echo $menu_item['text'] ?>" id="menu<?php echo $key ?>"><img src="<?php echo $menu_item['icon'] ?>" alt="<?php echo $menu_item['text'] ?>" /><?php echo $menu_item['text'] ?></a>
      </li>
<?php endif; ?>
<?php endforeach; ?>
     </ul>
    </div>
<?php endif; ?>
    <div class="sep">&nbsp;</div>
    <div id="myfolders"><?php echo _("My Folders") ?></div>
    <ul class="folderlist" id="normalfolders">
     <li class="folder" id="newfolder">
      <div class="create"></div>
      <a title="<?php echo _("New Folder") ?>"><?php echo _("New Folder") ?></a>
     </li>
     <li class="folder" id="dropbase" style="display:none">
      <div class="base"></div>
      <a title="<?php echo _("Base Level") ?>"><?php echo _("Base Level") ?></a>
     </li>
    </ul>
   </div>
  </div>

  <div id="dimpmain" style="left:<?php echo $sidebar_width ?>">
   <div id="dimpmain_portal"><?php echo $loading_text ?></div>
   <div id="dimpmain_folder" style="display:none">
    <div id="dimpmain_folder_top" class="noprint">
     <div id="tabbar">
<?php if (!empty($application_folders) || !empty($site_menu)): ?>
      <div class="tabset">
       <ul>
        <li>
         <a id="hometab"><img src="<?php echo $registry->get('icon', 'horde') ?>" alt="<?php echo _("Portal") ?>" /><?php echo _("Portal") ?></a>
        </li>
<?php foreach ($application_folders as $val): ?>
        <li<?php if ($val['app'] == 'dimp') echo ' class="activeTab"' ?>>
         <a class="applicationtab" app="<?php echo $val['app'] ?>"><img src="<?php echo $val['icon'] ?>" alt="<?php echo $val['name'] ?>" /><?php echo $val['name'] ?></a>
        </li>
<?php endforeach; ?>
<?php foreach ($site_menu as $key => $menu_item): if ($menu_item == 'separator') continue; ?>
        <li>
         <a id="tab<?php echo $key ?>"><img src="<?php echo $menu_item['icon'] ?>" alt="<?php echo $menu_item['text'] ?>" /><?php echo $menu_item['text'] ?></a>
        </li>
<?php endforeach; ?>
<?php if (isset($_SESSION['imp']['quota']) && is_array($_SESSION['imp']['quota'])): ?>
        <li id="quota"></li>
<?php endif; ?>
       </ul>
      </div>
<?php elseif (isset($_SESSION['imp']['quota']) && is_array($_SESSION['imp']['quota'])): ?>
      <div id="quota"></div>
<?php endif; ?>
     </div>
     <br class="clear" />
     <div id="mailboxHeader" class="header">
      <div>
       <span class="rightFloat" id="msgHeader"></span>
       <?php echo Horde::img('loading.gif', $loading_text, array('id' => 'folderLoading', 'style' => 'display:none'), $imagedir) ?>
       <span id="folderName"></span>
      </div>
     </div>

     <div class="dimpActions">
      <form action="#" method="post" onsubmit="return false;">
       <input type="text" name="msgList_filter" id="msgList_filter" size="30" />
      </form>
      <span id="button_reply_cont"><?php _createDA(_("Reply"), 'reply_menu.png', 'button_reply', '', $show_text) ?></span>
      <span id="button_forward_cont"><?php _createDA(_("Forward"), 'forward_menu.png', 'button_forward', '', $show_text) ?></span>
<?php if (!empty($conf['spam']['reporting'])): ?>
      <span><?php _createDA(_("Spam"), 'spam_menu.png', 'button_spam', '', $show_text) ?></span>
<?php endif; ?>
<?php if (!empty($conf['notspam']['reporting'])): ?>
      <span style="display:none"><?php _createDA(_("Innocent"), 'ham_menu.png', 'button_ham', '', $show_text) ?></span>
<?php endif; ?>
      <span><?php _createDA(_("Compose"), 'compose_menu.png', 'button_compose', '', $show_text) ?></span>
      <span><?php _createDA(_("Get Mail"), 'checkmail_menu.png', 'button_checkmail2', '', $show_text) ?></span>
      <span><?php _createDA(_("Delete"), 'delete_menu.png', 'button_deleted', '', $show_text) ?></span>
      <span><?php _createDA(_("Other Actions"), 'plus_menu.png', 'button_other', '', $show_text) ?></span>
     </div>

     <div class="qoptions" id="qoptions" style="display:none">
      <div class="qclose"><a>x</a></div>
      <span class="qlabel"><?php echo _("Folders: ") ?></span>
<?php if (!empty($conf['search']['search_all'])): ?>
      <a id="sf_all"><?php echo _("All") ?></a>
<?php endif; ?>
      <a id="sf_current"></a>
      <span class="qlabel">|&nbsp;</span>
      <span class="qlabel"><?php echo _("Message: ") ?></span>
      <a id="sf_msgall"><?php echo _("All") ?></a>
      <a id="sf_from"><?php echo _("From") ?></a>
      <a id="sf_to"><?php echo _("To") ?></a>
      <a id="sf_subject"><?php echo _("Subject") ?></a>
     </div>

     <div id="msglistHeader" class="item">
      <div class="msgStatus">&nbsp;</div>
      <div class="msgFrom">
       <a class="widget" sortby="<?php echo SORTFROM ?>"><?php echo _("From") ?></a>
       <a class="widget" style="display:none" sortby="<?php echo SORTTO ?>"><?php echo _("To") ?></a>
      </div>
      <div class="msgSubject">
       <a class="widget" sortby="<?php echo SORTSUBJECT ?>"><?php echo _("Subject") ?>
        <small sortby="<?php echo SORTTHREAD ?>"><?php echo _("Thread") ?></small>
       </a>
       <a class="widget" style="display:none" sortby="<?php echo SORTTHREAD ?>"><?php echo _("Thread") ?>
        <small sortby="<?php echo SORTSUBJECT ?>"><?php echo _("Subject") ?></small>
       </a>
      </div>
      <div class="msgDate">
       <a class="widget" sortby="<?php echo SORTDATE ?>"><?php echo _("Date") ?>
        <small sortby="<?php echo SORTARRIVAL ?>"><?php echo _("Arrival") ?></small>
       </a>
       <a class="widget" style="display:none" sortby="<?php echo SORTARRIVAL ?>"><?php echo _("Arrival") ?>
        <small sortby="<?php echo SORTDATE ?>"><?php echo _("Date") ?></small>
       </a>
      </div>
      <div class="msgSize"><a class="widget" sortby="<?php echo SORTSIZE ?>"><?php echo _("Size") ?></a></div>
     </div>
     <div class="clear" id="mlistHeaderClear">&nbsp;</div>
    </div>

    <div id="msgSplitPane">
     <div id="msgListDiv" class="noprint">
      <div id="msgList_empty" style="display:none"><em><?php echo _("No messages to display") ?></em></div>
      <div id="msgList_error" style="display:none"><em><?php echo _("Could not get message list from server") ?></em></div>
      <div id="msgList" class="msglist">&nbsp;</div>
     </div>
     <div id="splitBar" style="display:none;" class="splitBar noprint"></div>
     <div id="previewPane" style="display:none;">
      <?php echo Horde::img('loading.gif', $loading_text, array('id' => 'msgLoading', 'style' => 'display:none'), $imagedir) ?>
      <div id="previewInfo" style="display:none;">
       <?php echo _("To preview a message, select it from the list above. A right-click on the messages will display available actions.") ?><br />
       <?php printf(_("Click on a message while holding down the %s key to select multiple messages.  To select a range of messages, click the first message of the range, navigate to the last message of the range, and then click on the last message while holding down the %s key."), '<span class="kbd">' . _("Ctrl") . '</span>', '<span class="kbd">' . _("Shift") . '</span>') ?><br /><br />
       <?php echo _("The following keyboard shortcuts are available:") ?><br />
       <?php echo Horde::img('key_up.png', '', '', $imagedir) ?> / <?php echo Horde::img('key_down.png', '', '', $imagedir) . ' : ' . _("Move up/down through the message list.") ?><br />
       <span class="kbd"><?php echo _("PgUp") ?></span> / <span class="kbd"><?php echo _("PgDown") ?></span> : <?php echo _("Move one page up/down through the message list.") ?><br />
       <span class="kbd"><?php echo _("Home") ?></span> / <span class="kbd"><?php echo _("End") ?></span> : <?php echo  _("Move to the beginning/end of the message list.") ?><br />
       <span class="kbd"><?php echo _("Del") ?></span> : <?php echo _("Delete the currently selected message(s).") ?> <?php printf(_("%s will delete the current message and move to the next message if a single message is selected."), '<span class="kbd">' . _("Shift") . '</span> + <span class="kbd">' . _("Del") . '</span>') ?><br />
       <span class="kbd"><?php echo _("Enter") ?></span> : <?php echo _("Open message in a popup window.") ?><br />
       <span class="kbd"><?php echo _("Ctrl") ?></span> + <span class="kbd"><?php echo 'A' ?></span> : <?php echo _("Select all messages in the current mailbox.") ?><br />
      </div>
      <div id="previewMsg" style="display:none;">
       <div class="msgHeaders">
        <div id="msgHeadersColl">
         <div class="newwin"><a id="msg_newwin"><?php echo $newwin ?></a></div>
         <div class="date"></div>
         <div class="others">
          <div class="toggle"><a id="expandHeaders" class="noprint"><?php echo Horde::img('arrow_collapsed.png', '>', array('title' => _("Expand Headers")), $imagedir) ?></a> <?php echo $attachment ?></div>
          <div class="subject"></div> <?php echo _("from") ?> <span class="from"></span>
         </div>
        </div>
        <div id="msgHeaders" style="display:none">
         <div class="dimpOptions noprint">
          <a id="msg_newwin_options"><?php echo $newwin . _("Open in new window") ?></a>
          <br />
          <a id="msg_print"><?php echo Horde::img('print.png', '', '', $GLOBALS['registry']->getImageDir('horde')) . _("Print") ?></a>
<?php if (!empty($conf['user']['allow_view_source'])): ?>
          <br />
          <a id="msg_view_source"><?php echo Horde::img('message_source.png', '', '', $imagedir) . _("View Message Source") ?></a>
<?php endif; ?>
         </div>
         <div id="msgHeadersContent">
          <table cellspacing="0">
           <thead>
            <tr>
             <td class="label">
              <a id="collapseHeaders" class="noprint"><?php echo Horde::img('arrow_expanded.png', 'v', array('title' => _("Collapse Headers")), $imagedir) ?></a> <?php echo _("Subject") ?>:
             </td>
             <td class="subject"></td>
            </tr>
            <tr id="msgHeaderFrom">
             <td class="label"><?php echo _("From") ?>:</td>
             <td class="from"></td>
            </tr>
            <tr id="msgHeaderDate">
             <td class="label"><?php echo _("Date") ?>:</td>
             <td class="date"></td>
            </tr>
            <tr id="msgHeaderTo">
             <td class="label"><?php echo _("To") ?>:</td>
             <td class="to"></td>
            </tr>
            <tr id="msgHeaderCc">
             <td class="label"><?php echo _("Cc") ?>:</td>
             <td class="cc"></td>
            </tr>
            <tr id="msgAtc" style="display:none">
             <td class="label"><div><?php echo $attachment ?></div><div><?php echo Horde::link('') . Horde::img('arrow_collapsed.png', '', array('id' => 'partlist_col'), $imagedir) . Horde::img('arrow_expanded.png', '', array('id' => 'partlist_exp', 'style' => 'display:none'), $imagedir) . ' ' . $attachment ?></a></div></td>
             <td>
              <div></div>
              <table id="partlist" style="display:none" cellspacing="2">
              </table>
             </td>
            </tr>
           </thead>
          </table>
         </div>
        </div>
       </div>
       <div id="msgBody" class="msgBody">
        <table width="100%" cellspacing="0"></table>
       </div>
      </div>
     </div>
     <div style="clear:left" />
    </div>
   </div>
  </div>
 </div>
</div>

<div class="context" id="ctx_folder" style="display:none;">
 <a id="ctx_folder_create"><?php echo $folder_create . _("Create subfolder") ?></a>
 <a id="ctx_folder_rename"><?php echo $folder_edit . _("Rename Folder") ?></a>
 <a id="ctx_folder_empty"><?php echo $delete . _("Empty Folder") ?></a>
 <a id="ctx_folder_delete"><?php echo Horde::img('folders/folder_delete.png') . _("Delete Folder") ?></a>
 <a id="ctx_folder_rights"><?php echo Horde::img('folders/folder.png') . _("Share Folder") ?></a>
 <div id="ctx_folder_seen_sep" class="sep"></div>
 <a id="ctx_folder_seen"><?php echo $mailseen . _("Mark all as Read") ?></a>
 <a id="ctx_folder_unseen"><?php echo $mailunseen . _("Mark all as New") ?></a>
 <div id="ctx_folder_poll_sep" class="sep"></div>
 <a id="ctx_folder_poll"><?php echo $mailseen . _("Check for New Mail") ?></a>
 <a id="ctx_folder_nopoll"><?php echo $mailseen . _("Do Not Check for New Mail") ?></a>
</div>

<div class="context" id="ctx_container" style="display:none;">
 <a id="ctx_container_create"><?php echo $folder_create . _("Create subfolder") ?></a>
 <a id="ctx_container_rename"><?php echo $folder_edit . _("Rename Folder") ?></a>
</div>

<div class="context" id="ctx_message" style="display:none;">
 <a id="ctx_message_reply"><?php echo Horde::img('reply.png', '', '', $imagedir) . _("Reply to Sender") ?></a>
 <a id="ctx_message_reply_all"><?php echo Horde::img('replyall.png', '', '', $imagedir) . _("Reply to All") ?></a>
 <a id="ctx_message_reply_list"><?php echo Horde::img('replyall.png', '', '', $imagedir) . _("Reply to List") ?></a>
 <div class="sep"></div>
 <a id="ctx_message_forward_all"><?php echo $forward . _("Forward Entire Message") ?></a>
 <a id="ctx_message_forward_body"><?php echo $forward . _("Forward Body Text Only") ?></a>
 <a id="ctx_message_forward_attachments"><?php echo $forward . _("Forward Attachments Only") ?></a>
 <div class="sep"></div>
 <a id="ctx_message_seen"><?php echo $mailseen . _("Mark as Read") ?></a>
 <a id="ctx_message_unseen"><?php echo $mailunseen . _("Mark as New") ?></a>
 <a id="ctx_message_flagged"><?php echo $flagged . _("Flag Message") ?></a>
 <a id="ctx_message_clear"><?php echo $clearflag . _("Clear Flag") ?></a>
 <div class="sep"></div>
<?php if (!empty($conf['spam']['reporting'])): ?>
 <a id="ctx_message_spam"><?php echo Horde::img('spam.png', '', '', $imagedir) . _("Mark as Spam") ?></a>
<?php endif; ?>
<?php if (!empty($conf['notspam']['reporting'])): ?>
 <a id="ctx_message_ham"><?php echo Horde::img('ham.png', '', '', $imagedir) . _("Mark as Innocent") ?></a>
<?php endif; ?>
<?php if ($has_blacklist): ?>
 <a id="ctx_message_blacklist"><?php echo Horde::img('blacklist.png', '', '', $imagedir) . _("Blacklist") ?></a>
<?php endif; ?>
<?php if ($has_whitelist): ?>
 <a id="ctx_message_whitelist"><?php echo Horde::img('whitelist.png', '', '', $imagedir) . _("Whitelist") ?></a>
<?php endif; ?>
 <a id="ctx_message_deleted"><?php echo $delete . _("Delete") ?></a>
<?php if (!$usetrash): ?>
 <a id="ctx_message_undeleted"><?php echo $delete . _("Undelete") ?></a>
<?php endif; ?>
</div>

<div class="context" id="ctx_draft" style="display:none;">
 <a id="ctx_draft_resume"><?php echo Horde::img('mail_draft.png', '', '', $imagedir) . _("Resume Draft") ?></a>
 <div class="sep"></div>
 <a id="ctx_draft_flagged"><?php echo $flagged . _("Flag Message") ?></a>
 <a id="ctx_draft_clear"><?php echo $clearflag . _("Clear Flag") ?></a>
 <div class="sep"></div>
 <a id="ctx_draft_deleted"><?php echo $delete . _("Delete") ?></a>
<?php if (!$usetrash): ?>
 <a id="ctx_draft_undeleted"><?php echo $delete . _("Undelete") ?></a>
<?php endif; ?>
</div>

<div class="context" id="ctx_reply" style="display:none;">
 <a id="ctx_reply_reply"><?php echo Horde::img('replyall.png', '', '', $imagedir) . _("To Sender") ?></a>
 <a id="ctx_reply_reply_all"><?php echo Horde::img('replyall.png', '', '', $imagedir) . _("To All") ?></a>
 <a id="ctx_reply_reply_list"><?php echo Horde::img('replyall.png', '', '', $imagedir) . _("To List") ?></a>
</div>

<div class="context" id="ctx_forward" style="display:none;">
 <a id="ctx_forward_forward_all"><?php echo $forward . _("Entire Message") ?></a>
 <a id="ctx_forward_forward_body"><?php echo $forward . _("Body Text Only") ?></a>
 <a id="ctx_forward_forward_attachments"><?php echo $forward . _("Attachments Only") ?></a>
</div>

<div class="context" id="ctx_otheractions" style="display:none;">
 <a id="previewtoggle"><?php echo $preview; echo ($dimp_prefs->getValue('show_preview') ? _("Hide Preview") : _("Show Preview")); ?></a>
 <div class="sep"></div>
 <a id="oa_seen"><?php echo $mailseen . _("Mark as Read") ?></a>
 <a id="oa_unseen"><?php echo $mailunseen . _("Mark as New") ?></a>
 <a id="oa_flagged"><?php echo $flagged . _("Flag Message") ?></a>
 <a id="oa_clear"><?php echo $clearflag . _("Clear Flag") ?></a>
 <div class="sep" id="oa_sep1"></div>
<?php if ($has_blacklist || $has_whitelist): ?>
<?php if ($has_blacklist): ?>
 <a id="oa_blacklist"><?php echo Horde::img('blacklist.png', '', '', $imagedir) . _("Blacklist") ?></a>
<?php endif; ?>
<?php if ($has_whitelist): ?>
 <a id="oa_whitelist"><?php echo Horde::img('whitelist.png', '', '', $imagedir) . _("Whitelist") ?></a>
<?php endif; ?>
 <div class="sep" id="oa_sep2"></div>
<?php endif; ?>
 <a id="oa_selectall"><?php echo $tick . _("Select All") ?></a>
<?php if (!$prefs->getValue('use_trash')): ?>
 <div class="sep"></div>
 <a id="oa_purge_deleted"><?php echo $delete . _("Purge Deleted") ?></a>
 <a id="oa_undeleted"><?php echo $delete . _("Undelete") ?></a>
<?php endif; ?>
</div>

<div class="context" id="ctx_contacts" style="display:none;">
 <div><?php _createDA(_("New Message"), 'compose.png', 'ctx_contacts_new') ?></div>
 <div><?php _createDA(_("Add to Address Book"), 'add_contact.png', 'ctx_contacts_add') ?></div>
</div>

<div style="display:none;">
 <?php echo Horde::img('popdown.png', 'v', array('class' => 'popdown', 'id' => 'popdown_img'), $imagedir) ?>
 <?php echo Horde::img('mail_priority_high.png', _("High Priority"), array('id' => 'high_priority_img')) ?>
 <?php echo Horde::img('mail_priority_low.png', _("Low Priority"), array('id' => 'low_priority_img')) ?>
 <?php foreach ($thread_imgs as $val) { echo $val; } ?>
 <?php foreach ($atc_imgs as $val) { echo $val; } ?>
</div>
