<?php
if (!$prefs->isLocked('default_share')):
    $sharelist = Kronolith::listCalendars();
    if (($default_share = $prefs->getValue('default_share')) == null ||
        !isset($sharelist[$default_share])) {
        $default_share = Auth::getAuth();
    }
?>

    <b><?php echo _("Your default calendar") ?></b>&nbsp;
    <select name="default_share">
    <?php foreach ($sharelist as $id => $share): ?>
      <option value="<?php echo $id ?>"<?php if ($id == $default_share) echo ' selected="selected"' ?>><?php echo $share->get('name') ?></option>
    <?php endforeach; ?>
    </select>
<?php endif; ?>
