<?php
if (!$prefs->isLocked('default_share')):
    $sharelist = Kronolith::listCalendars();
    if (($default_share = $prefs->getValue('default_share')) == null ||
        !isset($sharelist[$default_share])) {
        $default_share = Auth::getAuth();
    }
?>

    <?php echo Horde::label('default_share', _("Your default calendar")) ?><br />
    <select id="default_share" name="default_share">
    <?php foreach ($sharelist as $id => $share): ?>
     <option value="<?php echo htmlspecialchars($id) ?>"<?php if ($id == $default_share) echo ' selected="selected"' ?>><?php echo htmlspecialchars($share->get('name')) ?></option>
    <?php endforeach; ?>
    </select>
<?php endif; ?>
