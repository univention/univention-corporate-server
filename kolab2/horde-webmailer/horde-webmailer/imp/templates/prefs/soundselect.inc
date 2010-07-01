<?php if (!$prefs->isLocked('nav_audio')): ?>
<?php $nav_audio = $prefs->getValue('nav_audio') ?>
<p><?php echo _("Play a sound on new mail?  This requires your browser to support embedded sound files.  Almost all do on Windows and Mac, but other platforms may require a plugin.") ?></p>
<ul class="nav-audio">
 <li><label><input type="radio" name="nav_audio" value=""<?php if (!$nav_audio) echo ' checked="checked"' ?> /> <?php echo _("No Sound") ?></label></li>
<?php foreach (glob($registry->get('themesfs') . '/graphics/audio/*.wav') as $sound): $sound = basename($sound); ?>
 <li>
  <label>
   <input type="radio" name="nav_audio" value="<?php echo htmlspecialchars($sound) ?>"<?php if ($nav_audio == $sound) echo ' checked="checked"' ?> />
   <?php echo htmlspecialchars($sound) ?>
  </label>
  <embed autostart="false" src="<?php echo $registry->getImageDir() . '/audio/' . htmlspecialchars($sound) ?>" />
 </li>
<?php endforeach; ?>
</ul>
<?php endif; ?>
