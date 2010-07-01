<?php if (!empty($_SESSION['turba']['has_share'])): ?>
 <div id="vbook-form"<?php if (is_a($driver, 'Turba_Driver_vbook')) echo ' style="display:none"' ?>>
  <input type="checkbox" id="save-vbook" name="save_vbook" />
  <strong><?php echo Horde::label('save-vbook', _("Save search as a virtual address book?")) ?></strong>

  <?php echo Horde::label('vbook_name', _("Name:")) ?>
  <input type="text" id="vbook_name" name="vbook_name" />
  <script type="text/javascript">
  Event.observe($('vbook_name'), 'keyup', function() {
      $('save-vbook').checked = $F('vbook_name') ? true : false;
  });
  </script>
 </div>
<?php endif; ?>
</form>
</div>
<br />
