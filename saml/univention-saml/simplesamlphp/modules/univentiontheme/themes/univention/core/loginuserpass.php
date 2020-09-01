<?php
$this->includeAtTemplateBase('includes/header.php');

$this->data['header'] = $this->t('{login:user_pass_header}');

$PW_EXPIRED = $this->data['errorcode'] !== NULL && in_array($this->data['errorcode'], array('LDAP_PWCHANGE', 'KRB_PWCHANGE', 'SAMBA_PWCHANGE', 'univention:RETYPE_MISMATCH'));
// echo '<pre>'; var_dump($this->data); echo '</pre>';

$error_is_notice = !in_array($this->data['errorcode'], array('univention:PW_CHANGE_FAILED', 'univention:RETYPE_MISMATCH'));

if ($this->data['errorcode'] === 'univention:ERROR') {
?>
		<script type="text/javascript">
			//<!--
			require(["umc/tools", ], function(tools) {
				var data = <?php echo json_encode(array(
	"status" => $this->data['errorparams']['status'],
	"title" => $this->data['errorparams']['title'],
	"message" => $this->data['errorparams']['message'],
	"traceback" => $this->data['errorparams']['traceback'],
)); ?>;
				tools.showErrorDialog(data, { hideInformVendor: true, hideInformVendorViaMail: true, noRedirection: true });
			});
			//-->
		</script>
<?php } ?>
		<div id="umcLoginWrapper">
			<h1 style="text-align: center;"><?php echo htmlspecialchars($this->t('{univentiontheme:login:loginat}', array('%s' => $this->configuration->getValue('domainname', '')))); ?></h1>
<?php
if (isset($this->data['SPMetadata']['privacypolicy'])) {
	printf('<h3 style="text-align: center;"><a href="%s">%s</a></h3>', htmlspecialchars($this->data['SPMetadata']['privacypolicy'], ENT_QUOTES), htmlspecialchars($this->t('{consent:consent:consent_privacypolicy}')));
}
// TODO: do we want to display $this->data['SPMetadata']['OrganizationName']) and $this->data['SPMetadata']['description']) ?
// both might be unset, description might be an array -> use is_array() && implode()!
?>
			<div id="umcLoginDialog" class="umcLoginDialog">
				<div id="umcLoginLogo" class="umcLoginLogo">
					<img id="umcLoginLogo" src="/univention/js/dijit/themes/umc/images/login_logo.svg"/>
				</div>
				<div class="umcLoginFormWrapper">
					<p id="umcLoginNotices" class="umcLoginNotices" style="display: <?php echo $this->data['errorcode'] !== NULL && $error_is_notice ? 'block' : 'none'; ?>;">
						<?php
$error_message = '';

if ($this->data['errorcode'] !== NULL && $this->data['errorcode'] !== 'univention:ERROR') {
	$error_message .= htmlspecialchars($this->t('{univentiontheme:errors:title_' . $this->data['errorcode'] . '}', $this->data['errorparams'])) . '. <br />';

	if ($this->data['errorcode'] === 'univention:SELFSERVICE_ACCUNVERIFIED') {
		$error_message .= '<span id="error_decription"></span>';  # FIXME: remove this hack, don't store HTML in UCR variables...
	} else {
		$error_message .= htmlspecialchars($this->t('{univentiontheme:errors:descr_' . $this->data['errorcode'] . '}', $this->data['errorparams']));
	}

	if ($error_is_notice) {
		echo $error_message;
	}
}
?>
					</p>
					<form id="umcLoginForm" name="umcLoginForm" action="?" method="post" class="umcLoginForm" autocomplete="on" <?php if ($PW_EXPIRED) { echo 'style="display: none; "'; } ?>>
						<label for="umcLoginUsername">
							<input placeholder="<?php echo htmlspecialchars($this->t('{login:username}'), ENT_QUOTES); ?>" id="umcLoginUsername" name="username" type="text" autocomplete="username"  tabindex="1" value="<?php echo htmlspecialchars($this->data['username'], ENT_QUOTES); ?>" <?php echo $this->data['forceUsername'] ? 'readonly' : ''; ?>/>
						</label>
						<label for="umcLoginPassword">
							<input placeholder="<?php echo htmlspecialchars($this->t('{login:password}'), ENT_QUOTES); ?>" id="umcLoginPassword" name="password" type="password" tabindex="2" autocomplete="current-password"/>
						</label>
<?php
foreach ($this->data['stateparams'] as $name => $value) {
	echo '<input type="hidden" name="' . htmlspecialchars($name, ENT_QUOTES) . '" value="' . htmlspecialchars($value, ENT_QUOTES) . '" />';
}
if ($this->data['rememberUsernameEnabled']) {
	printf('<input type="checkbox" id="remember_username" tabindex="4" name="remember_username" value="Yes" %s />', $this->data['rememberUsernameChecked'] ? 'checked="checked"' : '');
	echo htmlspecialchars($this->t('{login:remember_username}'));
}
if (array_key_exists('organizations', $this->data)) {
?>
				<div class="organization">
				<span style="padding: .3em;"><?php echo htmlspecialchars($this->t('{login:organization}')); ?></span>
				<span><select name="organization" tabindex="3">
<?php
$selectedOrg = array_key_exists('selectedOrg', $this->data) ? $this->data['selectedOrg'] : NULL;
foreach ($this->data['organizations'] as $orgId => $orgDesc) {
	if (is_array($orgDesc)) {
		$orgDesc = $this->t($orgDesc);
	}

	if ($orgId === $selectedOrg) {
		$selected = 'selected="selected" ';
	} else {
		$selected = '';
	}

	printf('<option %s value="%s">%s</option>', $selected, htmlspecialchars($orgId, ENT_QUOTES), htmlspecialchars($orgDesc));
}
?>
				</select></span>
				</div>
<?php
}
?>
						<input id="umcLoginSubmit" type="submit" name="submit" value="<?php echo htmlspecialchars($this->t('{login:login_button}'), ENT_QUOTES); ?>"/>
					</form>

<?php
if ($PW_EXPIRED) {
?>
					<form id="umcNewPasswordForm" name="umcLoginForm" action="?" method="post" class="umcLoginForm" autocomplete="off" style="display: block;">
						<input name="username" type="hidden" value="<?php echo htmlspecialchars($this->data['username'], ENT_QUOTES); ?>" />
						<input name="password" type="hidden" value="<?php echo htmlspecialchars($_REQUEST['password'], ENT_QUOTES); /* TODO: store instead in the session? */ ?>" />
						<label for="umcLoginNewPassword">
							<input id="umcLoginNewPassword" name="new_password" type="password" autocomplete="new-password" placeholder="<?php echo htmlspecialchars($this->t('{pwchange:new_password}'), ENT_QUOTES); ?>" />
						</label>
						<label for="umcLoginNewPasswordRetype">
							<input id="umcLoginNewPasswordRetype" name="new_password_retype" type="password" autocomplete="new-password" placeholder="<?php echo htmlspecialchars($this->t('{pwchange:new_password_retype}'), ENT_QUOTES); ?>" />
						</label>
						<input id="umcNewPasswordSubmit" type="submit" name="submit" value="<?php echo htmlspecialchars($this->t('{pwchange:change_password}'), ENT_QUOTES); ?>" />
<?php
foreach ($this->data['stateparams'] as $name => $value) {
	echo '<input type="hidden" name="' . htmlspecialchars($name, ENT_QUOTES) . '" value="' . htmlspecialchars($value, ENT_QUOTES) . '" />';
}
?>
					</form>
<?php
}
?>
<?php
if (!$error_is_notice && $error_message) {
?>
					<div id="umcLoginWarnings" class="umcLoginWarnings">
						<p class="umcLoginWarning">
							<?php echo $error_message; ?>
						</p>
					</div>
<?php
}
?>
				</div>
			</div>
			<div id="umcLoginLinks"></div>
			<!-- preload the image! -->
			<img src="/univention/js/dijit/themes/umc/images/login_bg.gif" style="height: 0; width: 0;"/>
<?php

if (!empty($this->data['links'])) {
	echo '<ul class="links" style="margin-top: 2em">';
	foreach ($this->data['links'] AS $l) {
		echo '<li><a href="' . htmlspecialchars($l['href'], ENT_QUOTES) . '">' . htmlspecialchars($this->t($l['text'])) . '</a></li>';
	}
	echo '</ul>';
}
?>
		</div>
		<script type="text/javascript">
			//<!--
			require(['dojo/domReady!'], function() {
				<?php
					printf("var node = document.getElementById('%s');\n", strlen($this->data['username']) > 0 ? 'umcLoginPassword' : 'umcLoginUsername');
				?>
				if (node) {
					setTimeout(function() {
						node.focus();
					}, 0);
				}
			});
<?php if ($this->data['errorcode'] === 'univention:SELFSERVICE_ACCUNVERIFIED') { ?>
			require(['dojo/dom', 'dompurify/purify', 'dojo/domReady!'], function(dom, purify) {
				var node = dom.byId("error_decription");
				<?php
					printf("var error_description_text = purify.sanitize(%s);\n", json_encode($this->t('{univentiontheme:errors:descr_' . $this->data['errorcode'] . '}', $this->data['errorparams'])))
				?>
				if (node) {
					node.innerHTML = error_description_text;
				}
			});
<?php } ?>
			//-->
		</script>
<?php
$this->includeAtTemplateBase('includes/footer.php');
?>
