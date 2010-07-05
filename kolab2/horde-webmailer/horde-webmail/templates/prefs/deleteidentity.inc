<?php if (!$prefs->isLocked('default_identity')): ?>
<script type="text/javascript">
<!--
function deleteIdentity()
{
    var index = document.prefs.identity.selectedIndex;
    var id = document.prefs.identity.options[index].value;
    if (id >= 0) {
        document.location.href = "<?php echo str_replace('&amp;', '&', Util::addParameter(Horde::selfUrl(true), array('actionID' => 'delete_identity', 'id' => ''))) ?>" + id;
    }
}
//-->
</script>
<br />
<input type="button" onclick="deleteIdentity()" class="button" value="<?php echo _("Delete selected identity") ?>" /><br /><br />
<?php endif; ?>
