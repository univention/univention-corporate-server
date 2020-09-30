<?php

/**
 * LDAP authentication source.
 *
 * See the ldap-entry in config-templates/authsources.php for information about
 * configuration of this authentication source.
 *
 * This class is based on www/auth/login.php.
 *
 * @package simpleSAMLphp
 */
class sspmod_uldap_Auth_Source_uLDAP extends sspmod_core_Auth_UserPassBase {

	/**
	 * A LDAP configuration object.
	 */
	private $ldapConfig;
	private static $_ldap = NULL;
	private $config;


	/**
	 * Constructor for this authentication source.
	 *
	 * @param array $info  Information about this authentication source.
	 * @param array $config  Configuration.
	 */
	public function __construct($info, $config) {
		assert('is_array($info)');
		assert('is_array($config)');

		/* Call the parent constructor first, as required by the interface. */
		parent::__construct($info, $config);

		$this->ldapConfig = new sspmod_ldap_ConfigHelper($config,
			'Authentication source ' . var_export($this->authId, TRUE));
		$this->config = $config;
	}

	private function ldap() {
		if (self::$_ldap === NULL) {
			self::$_ldap = new SimpleSAML_Auth_LDAP($this->config['hostname'], $this->config['enable_tls'], $this->config['debug'], $this->config['timeout']);
			self::$_ldap->bind($this->config['search.username'], $this->config['search.password']);
		}
		return self::$_ldap;
	}

	/**
	 * Attempt to log in using the given username and password.
	 *
	 * @param string $username  The username the user wrote.
	 * @param string $password  The password the user wrote.
	 * param array $sasl_arg  Associative array of SASL options
	 * @return array  Associative array with the users attributes.
	 */
	protected function login($username, $password, array $sasl_args = NULL) {
		assert('is_string($username)');
		assert('is_string($password)');

		$new_password = $this->checkPasswordChange($username, $password);

		try {
			$attributes = $this->ldapConfig->login($username, $new_password, $sasl_args);
		} catch (SimpleSAML_Error_Error $e) {
			if ($password !== $new_password) {  // The password was changed, but the S4-Connector did not yet sync it back to OpenLDAP
				throw new SimpleSAML_Error_Error('univention:PASSWORD_CHANGE_SUCCESS');
			}
			if ($e->getMessage() === 'WRONGUSERPASS') {
				/* Our ldap overlays return INVALID_CREDENTIALS if the password has expired
				 * plus an extended error.
				 * So in case of WRONGUSERPASS and the LDAP extened_error indicates password is expired
				 * we check for pwchange dialog.
				 * In case of only WRONGUSERPASS, the password is really wrong and the logon denied.
				 */
				$expired_messages = array("password expired", "The password has expired.", "account expired");
				if (in_array($this->ldapConfig->extended_error, $expired_messages)) {
					SimpleSAML\Logger::debug('password is expired, checking for password change');
					$user_dn = $this->ldap()->searchfordn($this->config['search.base'], $this->config['search.attributes'], $username, TRUE);
					$attributes = $this->ldap()->getAttributes($user_dn);
					$this->throw_common_login_errors($attributes);
				}
			}
			throw $e;
		}
		$this->throw_common_login_errors($attributes);
		$this->throw_selfservice_login_errors($attributes);
		return $attributes;

	}

	private function checkPasswordChange($username, $password) {
		if (!isset($_POST['new_password'])) {
			return $password;
		}
		$new_password = $_POST['new_password'];
		assert('is_string($new_password)');

		if (isset($_POST['new_password_retype']) && $_POST['new_password_retype'] !== $new_password) {
			throw new SimpleSAML_Error_Error('univention:RETYPE_MISMATCH');
		}

		$config = SimpleSAML_Configuration::getInstance();
		$language = new \SimpleSAML\Locale\Language($config);
		$url = 'https://' . $config->getValue('hostfqdn') . '/univention/auth';
		$data =  json_encode(array("options" => array("username" => $username, "password" => $password, "new_password" => $new_password)));
		$ch = curl_init();
		curl_setopt($ch, CURLOPT_URL, $url);
		curl_setopt($ch, CURLOPT_HTTPHEADER, array('Content-Type: application/json', sprintf('Accept-Language: %s; q=1, en; q=0.5', $language->getLanguage()), 'X-Requested-With: XMLHttpRequest'));
		curl_setopt($ch, CURLOPT_USERAGENT, 'simplesamlphp');
		curl_setopt($ch, CURLOPT_REFERER, 'https://' . $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI']);
		curl_setopt($ch, CURLOPT_POST, TRUE);
		curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
		curl_setopt($ch, CURLOPT_RETURNTRANSFER, TRUE);
		$response = curl_exec($ch);
		if ($response === FALSE) {
			SimpleSAML\Logger::warning('Error: ' . curl_error($ch));
		}
		$httpcode = curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
		SimpleSAML\Logger::debug('Password changing response: ' . var_export(array($httpcode, $response), true));
		if (FALSE !== $response && strpos(curl_getinfo($ch, CURLINFO_CONTENT_TYPE), 'application/json') >= 0) {
			$response = json_decode($response, TRUE);
		} else {
			$message = $response;
			if ($httpcode === 0) {
				$httpcode = 500;
				$message = curl_error($ch);
			}
			$response = array('message' => $message, 'traceback' => '', 'title' => '');
		}
		if ($httpcode !== 200) {
			if ($httpcode >= 500) {
				throw new SimpleSAML_Error_Error(array('univention:ERROR',
					'status' => $httpcode,
					'title' => $response['title'],
					'message' => $response['message'],
					'traceback' => $response['traceback'],
				));
			}
			throw new SimpleSAML_Error_Error(array('univention:PW_CHANGE_FAILED', '%s' => $response['message']));
		}
		curl_close($ch);
		return $new_password;
	}


	/**
	 * Investigate login failure
	 *
	 * @param array $attributes
	 */
	private function throw_common_login_errors($attributes) {
		SimpleSAML\Logger::debug('got LDAP attributes:' . var_export($attributes, true));

		$the_time = time();
		// Account expired
		// Posix: shadowExpire: 1 if set: disabled , or: days since epoch the account expires
		if (isset($attributes['shadowExpire']) && is_string($attributes["shadowExpire"][0])) {
			if ((int)$attributes['shadowExpire'][0] == 1) {
				SimpleSAML\Logger::debug('LDAP Account disabled');
				throw new SimpleSAML_Error_Error('LDAP_ACCDISABLED');
			}
			else if ((int)$attributes['shadowExpire'][0] < (floor($the_time / 86400))) {
				SimpleSAML\Logger::debug('LDAP Account expired');
				throw new SimpleSAML_Error_Error('LDAP_ACCEXPIRED');
			}
		}
		// Kerberos expired
		if (isset($attributes['krb5ValidEnd']) && is_string($attributes['krb5ValidEnd'][0])) {
			// Parse strange krb5ValidEnd format '20151020000000Z' (missing T)
			$date = DateTime::createFromFormat('Ymd+', $attributes['krb5ValidEnd'][0]);
			if ($date->getTimestamp() < ($the_time + 1)) {
				SimpleSAML\Logger::debug('Kerberos Account expired');
				throw new SimpleSAML_Error_Error('KRB_ACCEXPIRED');
			}
		}
		// Samba expired
		if (isset($attributes['sambaKickoffTime']) && is_string($attributes['sambaKickoffTime'][0])) {
			if ((int)$attributes['sambaKickoffTime'][0] < $the_time) {
				SimpleSAML\Logger::debug('Samba Account expired');
				throw new SimpleSAML_Error_Error('SAMBA_ACCEXPIRED');
			}
		}

		// Password change required:
		// shadowMax + shadowLastChange < (floor(time() / 86400))
		if (isset($attributes['shadowMax']) && is_array($attributes['shadowLastChange'])) {
			if (((int)$attributes['shadowMax'][0] + (int)$attributes['shadowLastChange'][0]) < (floor($the_time / 86400))) {
				SimpleSAML\Logger::debug('LDAP password change required');
				throw new SimpleSAML_Error_Error('LDAP_PWCHANGE');
			}
		}
		// krb5PasswordEnd < today (ldap attribute format: 20161020000000Z)
		if (isset($attributes['krb5PasswordEnd']) && is_string($attributes['krb5PasswordEnd'][0])) {
			// Parse strange krb5PasswordEnd format '20151020000000Z' (missing T)
			$date = DateTime::createFromFormat('Ymd+', $attributes['krb5PasswordEnd'][0]);
			if ($date->getTimestamp() < ($the_time + 1)) {
				SimpleSAML\Logger::debug('Kerberos password change required');
				throw new SimpleSAML_Error_Error('KRB_PWCHANGE');
			}
		}
		// samba:
		if (isset($attributes['sambaKickoffTime']) && is_string($attributes['sambaKickoffTime'][0])) {
			if ((int)$attributes['sambaKickoffTime'][0] < $the_time) {
				SimpleSAML\Logger::debug('Samba password change required');
				throw new SimpleSAML_Error_Error('SAMBA_PWCHANGE');
			}
		}

		// Account Locked / deactivated:
		// samba: L in sambaAcctFlags
		if (isset($attributes['sambaAcctFlags']) && is_string($attributes['sambaAcctFlags'][0])) {
			if (strpos($attributes['sambaAcctFlags'][0],'L') !== false) {
				SimpleSAML\Logger::debug('Samba account locked');
				throw new SimpleSAML_Error_Error('SAMBA_ACCLOCKED');
			}
		}
		// krb: krb5KDCFlags=254
		if (isset($attributes['krb5KDCFlags']) && is_string($attributes['krb5KDCFlags'][0])) {
			if ((int)$attributes['krb5KDCFlags'][0] === 254) {
				SimpleSAML\Logger::debug('Kerberos account locked');
				throw new SimpleSAML_Error_Error('KRB_ACCLOCKED');
			}
		}
		// ldap: locking ldap is done by modifying password > but then ldap bind has failed anyway

		return;
	}

	/**
	 * Check if the account needs and has a verified email address
	 *
	 * @param array $attributes
	 */
	private function throw_selfservice_login_errors($attributes) {
		if ($this->config['selfservice.check_email_verification']) {
			$is_self_registered = isset($attributes['univentionRegisteredThroughSelfService']) &&
				$attributes['univentionRegisteredThroughSelfService'][0] === 'TRUE';
			$selfservice_email_verified = isset($attributes['univentionPasswordRecoveryEmailVerified']) &&
				$attributes['univentionPasswordRecoveryEmailVerified'][0] === 'TRUE';
			if ($is_self_registered && !$selfservice_email_verified) {
				SimpleSAML\Logger::debug('Self service mail not verified');
				// The double dot in the error marks this as custom error which is not defined in
				// lib/SimpleSAML/Error/ErrorCodes.php
				// Without it a cgi error is thrown "PHP Notice:  Undefined index: SELFSERVICE_ACCUNVERIFIED"
				throw new SimpleSAML_Error_Error('univention:SELFSERVICE_ACCUNVERIFIED');
			}
		}
	}

}


?>
