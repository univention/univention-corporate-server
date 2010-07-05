<h1 class="header"><?php printf(_("Import Notes, Step %d"), (int)$import_step) ?></h1>

<form method="post" name="import_form" enctype="multipart/form-data" action="<?php echo Horde::applicationUrl('data.php') ?>">
<input type="hidden" name="actionID" value="<?php echo htmlspecialchars($next_step) ?>" />
<input type="hidden" name="import_step" value="<?php echo (int)$import_step ?>" />
<div class="item" style="padding:.5em">

    <table cellspacing="0"><tr><td>
        <?php echo Horde::label('import_format', _("Select the format of the source file:")) ?><br />
        <select id="import_format" name="import_format">
            <option value="csv"><?php echo _("CSV") ?></option>
            <option value="vnote"><?php echo _("vNote") ?></option>
        </select><br />

<?php if (!$prefs->isLocked('default_notepad') && count($notepads = Mnemo::listNotepads(false, PERMS_EDIT)) > 1): ?>
        <br /><?php echo Horde::label('notepad_target', _("Which Notepad should the notes be added to?")) ?><br />
        <select id="notepad_target" name="notepad_target">
        <?php
        $default = Mnemo::getDefaultNotepad(PERMS_EDIT);
        foreach (array_keys($notepads) as $id) {
            $sel = ($id == $default) ? ' selected="selected"' : '';
            printf('<option value="%s"%s>%s</option>',
                   htmlspecialchars($id), $sel, htmlspecialchars($notepads[$id]->get('name'))) . "\n";
        } ?>
        </select><br />
<?php else: ?>
        <input type="hidden" name="notepad_target" value="<?php echo htmlspecialchars(Mnemo::getDefaultNotepad(PERMS_EDIT)) ?>" />
<?php endif; ?>
        <br />

        <?php echo Horde::label('import_file', _("Select the file to import:")) ?><br />
        <input type="file" id="import_file" name="import_file" size="40" />
        <br /><br />
        <input type="submit" value="<?php echo _("Next") ?>" class="button" />
    </td></tr></table>
</div>
</form>
