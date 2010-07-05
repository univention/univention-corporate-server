<?php if (is_array($calendar)): ?>

<h2><?php echo htmlspecialchars($calendar['name']) ?></h2>
<p>
 <?php echo _("Remote Calendar from: ") ?>
</p>
<p class="calendar-info-url">
 <?php echo htmlspecialchars($calendar['url']) ?>
</p>

<?php else: ?>

<h2><?php echo htmlspecialchars($calendar->get('name')) ?></h2>
<?php if ($desc = $calendar->get('desc')): ?>
<p><em><?php echo htmlspecialchars($desc) ?></em></p>
<?php endif; ?>
<p>
 <?php printf(_("Local calendar owned by %s."), Kronolith::getUserName($calendar->get('owner'))) ?>
 <?php echo _("To subscribe to this calendar from another calendar program, use this URL: ") ?>
</p>
<p class="calendar-info-url">
 <?php echo htmlspecialchars($subscribe_url) ?>
</p>
<p>
 <?php echo _("To subscribe to this calendar from a feed reader, use this URL: ") ?>
</p>
<p class="calendar-info-url">
 <?php echo htmlspecialchars(Kronolith::feedUrl($calendar->getName())) ?>
</p>

<p>
 <?php echo _("To embed this calendar in another website, use this code: ") ?>
</p>
<p class="calendar-info-url">
<?php echo htmlspecialchars(Kronolith::embedCode($calendar->getName())); ?>
</p>
<?php if (Horde::showService('help')) {
    echo '<p>' . Help::link('kronolith', 'embed') . ' ' . _("Learn how to embed other calendar views.") . '</p>';
} ?>
<?php endif; ?>
