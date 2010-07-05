<div id="page">

<h1 class="header">
 <?php echo _("Manage Calendars") ?>
</h1>

<div id="calendar-list-buttons">
 <?php if (!$prefs->isLocked('default_share')): ?>
 <form method="get" action="create.php">
  <?php echo Util::formInput() ?>
  <input type="submit" class="button" value="<?php echo _("Create a new Local Calendar") ?>" />
 </form>
 <?php endif; ?>

 <form method="get" action="remote_subscribe.php">
  <?php echo Util::formInput() ?>
  <input type="submit" class="button" value="<?php echo _("Subscribe to a Remote Calendar") ?>" />
 </form>
</div>

<table summary="<?php echo _("Calendar List") ?>" cellspacing="0" id="calendar-list" class="striped sortable">
 <thead>
  <tr>
   <th class="sortdown"><?php echo _("Calendar") ?></th>
   <th><?php echo _("Kind") ?></th>
   <th class="calendar-list-url nosort"><?php echo _("Display URL") ?></th>
   <th class="calendar-list-url nosort"><?php echo _("Subscription URL") ?></th>
   <th class="calendar-list-icon nosort" colspan="<?php echo empty($conf['share']['no_sharing']) ? 3 : 2 ?>">&nbsp;</th>
  </tr>
 </thead>

 <tbody>
<?php foreach (array_keys($sorted_calendars) as $calendar_id): ?>
  <tr>
<?php $calendar = $calendars[$calendar_id]; if (is_array($calendar)): ?>
   <td><?php echo htmlspecialchars($calendar['name']) ?></td>
   <td><?php echo _("Remote") ?></td>
   <td><?php $url = Util::addParameter($display_url_base, 'display_cal', 'remote_' . $calendar['url'], false) ?><a href="<?php echo htmlspecialchars($url) ?>" title="<?php echo _("Click or copy this URL to display this calendar") ?>" target="_blank"><?php echo htmlspecialchars(shorten_url($url)) ?></a></td>
   <td><a href="<?php echo htmlspecialchars($calendar['url']) ?>" title="<?php echo _("Click or copy this URL to display this calendar") ?>" target="_blank"><?php echo htmlspecialchars(shorten_url($calendar['url'])) ?></a></td>
   <td><a href="<?php echo Util::addParameter($remote_edit_url_base, 'url', $calendar['url']) ?>" title="<?php echo _("Edit") ?>"><?php echo $edit_img ?></a></td>
<?php if (empty($conf['share']['no_sharing'])): ?>
   <td>&nbsp;</td>
<?php endif; ?>
   <td><a href="<?php echo Util::addParameter($remote_unsubscribe_url_base, 'url', $calendar['url']) ?>" title="<?php echo _("Unsubscribe") ?>"><?php echo $delete_img ?></a></td>
<?php else: ?>
   <td><?php echo htmlspecialchars($calendar->get('name')) ?></td>
   <td><?php echo _("Local") ?></td>
   <td><?php $url = Util::addParameter($display_url_base, 'display_cal', $calendar->getName(), false) ?><a href="<?php echo htmlspecialchars($url) ?>" title="<?php echo _("Click or copy this URL to display this calendar") ?>" target="_blank"><?php echo htmlspecialchars(shorten_url($url)) ?></a></td>
   <td><?php $url = $webdav ? $subscribe_url_base . $calendar->get('owner') . '/' . $calendar->getName() . '.ics' : Util::addParameter($subscribe_url_base, 'c', $calendar->getName(), false) ?><a href="<?php echo htmlspecialchars($url) ?>" title="<?php echo _("Click or copy this URL to display this calendar") ?>" target="_blank"><?php echo htmlspecialchars(shorten_url($url)) ?></a></td>
   <td><a href="<?php echo Util::addParameter($edit_url_base, 'c', $calendar->getName()) ?>" title="<?php echo _("Edit") ?>"><?php echo $edit_img ?></a></td>
<?php if (empty($conf['share']['no_sharing'])): ?>
   <td><a onclick="return !popup(this.href);" href="<?php echo Util::addParameter($perms_url_base, 'share', $calendar->getName()) ?>" target="_blank" title="<?php echo _("Change Permissions") ?>"><?php echo $perms_img ?></a></td>
<?php endif; ?>
   <td><a href="<?php echo Util::addParameter($delete_url_base, 'c', $calendar->getName()) ?>" title="<?php echo _("Delete") ?>"><?php echo $delete_img ?></a></td>
<?php endif; ?>
  </tr>
<?php endforeach; ?>
 </tbody>
</table>

</div>
