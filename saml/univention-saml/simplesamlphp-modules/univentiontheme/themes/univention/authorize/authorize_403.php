<?php

$this->includeAtTemplateBase('includes/header.php');

$this->data['403_header'] = $this->t('{authorize:Authorize:403_header}');
$this->data['403_text'] = $this->t('{authorize:Authorize:403_text}');

?>
<div class="container">
	<div class="warning">
		<div class="icon"></div>
		<div class="title"><?php echo($this->data['403_header']); ?></div>
		<div class="text"><?php echo($this->data['403_text']); ?></div>

<?php
if (isset($this->data['LogoutURL'])) {
?>
<p><a href="<?php echo htmlspecialchars($this->data['LogoutURL']); ?>"><?php echo $this->t('{status:logout}'); ?></a></p>
<?php
}
?>
	</div>
</div>
<?php
$this->includeAtTemplateBase('includes/footer.php');
?>
