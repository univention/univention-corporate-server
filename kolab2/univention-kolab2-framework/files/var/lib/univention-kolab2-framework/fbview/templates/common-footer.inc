<?php if (!empty($title)): ?>
<script language="JavaScript" type="text/javascript">
<!--
if (parent.frames.horde_main) parent.document.title = '<?php echo addslashes($registry->getParam('name') . ' :: ' . $title) ?>';
//-->
</script>
<?php endif; if (isset($GLOBALS['notification'])) $GLOBALS['notification']->notify(array('listeners' => array('javascript'))); ?>
</body>
</html>
