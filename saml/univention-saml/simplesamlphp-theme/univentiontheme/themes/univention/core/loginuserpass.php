<?php
$this->includeAtTemplateBase('includes/header.php');

$this->data['header'] = $this->t('{login:user_pass_header}');

if (strlen($this->data['username']) > 0) {
	$this->data['autofocus'] = 'password';
} else {
	$this->data['autofocus'] = 'username';
}

?>
	<div class="container">
	<div class="login">
	<div class="loginlogo"></div>
	<div class="logintext">
	<!-- <p><?php echo htmlspecialchars($this->t('{univentiontheme:login:user_pass_header}')); ?></p> -->

	<?php
	if (isset($this->data['SPMetadata']['OrganizationName'])) {
			$login_user_pass_text = str_replace('$$OrganizationName$$', $this->data['SPMetadata']['OrganizationName'] . ' ', $this->t('{univentiontheme:login:user_pass_text}'));
	} else {
			$login_user_pass_text = str_replace('$$OrganizationName$$', '', $this->t('{univentiontheme:login:user_pass_text}'));
	}
		echo('<p>' . htmlspecialchars($login_user_pass_text) . '</p>');
		?>
	<?php
	if (isset($this->data['SPMetadata']['description'])) {
		echo('<p>' . htmlspecialchars($this->data['SPMetadata']['description']) . '</p>');
	}
	if (isset($this->data['SPMetadata']['privacypolicy'])) {
		echo('<p><a href="' . htmlspecialchars($this->data['SPMetadata']['privacypolicy']) . '">' . htmlspecialchars($this->t('{consent:consent:consent_privacypolicy}')) . '</a></p>');
	}
	?>
	</div>
	<form action="?" method="post" name="f" class="loginform">
	<label for="username">
<?php
if ($this->data['forceUsername']) {
	echo '<strong style="font-size: medium">' . htmlspecialchars($this->data['username']) . '</strong>';
} else {
	echo '<input placeholder="' .htmlspecialchars($this->t('{login:username}')) . '" type="text" id="username" tabindex="1" name="username" value="' . htmlspecialchars($this->data['username']) . '" />';
}
?>
	</label>
	<label for="password">
		<?php 
			echo '<input placeholder="' . htmlspecialchars($this->t('{login:password}')) . '" type="password" id="password" tabindex="2" name="password" />';
		?>
<?php
	$text = htmlspecialchars($this->t('{login:login_button}'));
	echo str_repeat("\t", 4);
	//echo "<input type=\"submit\" class=\"btn-small\" tabindex=\"4\" id=\"regularsubmit\" value=\"{$text}\" />";
	echo "<input type=\"submit\" class=\"submit\" value=\"Login\" />";
?>
<?php
if ($this->data['rememberUsernameEnabled']) {
	echo str_repeat("\t", 4);
	echo '<input type="checkbox" id="remember_username" tabindex="4" name="remember_username" value="Yes" ';
	echo ($this->data['rememberUsernameChecked'] ? 'checked="Yes" /> ' : '/> ');
	echo $this->t('{login:remember_username}');
}
?>
</label>
<?php
if (array_key_exists('organizations', $this->data)) {
?>
			<div class="organization">
			<span style="padding: .3em;"><?php echo $this->t('{login:organization}'); ?></span>
			<span><select name="organization" tabindex="3">
<?php
if (array_key_exists('selectedOrg', $this->data)) {
	$selectedOrg = $this->data['selectedOrg'];
} else {
	$selectedOrg = NULL;
}

foreach ($this->data['organizations'] as $orgId => $orgDesc) {
	if (is_array($orgDesc)) {
		$orgDesc = $this->t($orgDesc);
	}

	if ($orgId === $selectedOrg) {
		$selected = 'selected="selected" ';
	} else {
		$selected = '';
	}

	echo '<option ' . $selected . 'value="' . htmlspecialchars($orgId) . '">' . htmlspecialchars($orgDesc) . '</option>';
}
?>
			</select></span>
			</div>
<?php
}
?>

<?php
foreach ($this->data['stateparams'] as $name => $value) {
	echo('<input type="hidden" name="' . htmlspecialchars($name) . '" value="' . htmlspecialchars($value) . '" />');
}
?>

	</form>


<?php

if(!empty($this->data['links'])) {
	echo '<ul class="links" style="margin-top: 2em">';
	foreach($this->data['links'] AS $l) {
		echo '<li><a href="' . htmlspecialchars($l['href']) . '">' . htmlspecialchars($this->t($l['text'])) . '</a></li>';
	}
	echo '</ul>';
}



/*
if ($this->data['errorcode'] !== NULL) {
	echo('<span class="logintitle">' . $this->t('{login:help_header}') . '</span>');
	echo('<span class="logintext">' . $this->t('{login:help_text}') . '</span>');
}
*/
?>

	</div>
<?php

if ($this->data['errorcode'] !== NULL) {
?>
	<div class="errorbox" id="umcLoginMessages" widgetid="umcLoginMessages">
		<h1><?php echo htmlspecialchars($this->t('{errors:title_' . $this->data['errorcode'] . '}', $this->data['errorparams'])); ?></h1>
		<p><?php echo htmlspecialchars($this->t('{errors:descr_' . $this->data['errorcode'] . '}', $this->data['errorparams'])); ?></p>
	</div>
<?php
}
?>
	</div>
<?php
$this->includeAtTemplateBase('includes/footer.php');
?>
