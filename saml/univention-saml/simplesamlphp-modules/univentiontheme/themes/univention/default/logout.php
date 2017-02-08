<?php
$this->includeAtTemplateBase('includes/header.php');

$this->data['header'] = $this->t('{logout:title}');
?>
<div class="container">
	<div class="samlloginwrapper">
		<span class="samllogintext"><?php echo($this->t('{univentiontheme:logout:logged_out_text}')); ?></span>

<?php
echo('<p><a href="/univention/">' .
	htmlspecialchars($this->t('{univentiontheme:logout:default_link_text}')) . '</a></p>');
?>

	</div>
</div>
<?php
$this->includeAtTemplateBase('includes/footer.php');
?>
