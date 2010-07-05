<?php
if (!$prefs->isLocked('default_notepad')):
    $notepads = Mnemo::listNotepads();
    if (($default_notepad = $prefs->getValue('default_notepad')) == null ||
        !isset($notepads[$default_notepad])) {
        $default_notepad = Auth::getAuth();
    }
?>

<?php echo Horde::label('default_notepad', _("Your default notepad:")) ?><br />
<select id="default_notepad" name="default_notepad">
<?php foreach (array_keys($notepads) as $id): ?>
    <option value="<?php echo htmlspecialchars($id) ?>"<?php if ($id == $default_notepad) echo ' selected="selected"' ?>><?php echo htmlspecialchars($notepads[$id]->get('name')) ?></option>
<?php endforeach; ?>
</select><br /><br />
<?php endif; ?>
