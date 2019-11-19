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
	private $ldap;
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
		$this->ldap = new SimpleSAML_Auth_LDAP($config['hostname'], $config['enable_tls'], $config['debug'], $config['timeout']);
		$this->ldap->bind($config['search.username'], $config['search.password']);
		$this->config = $config;
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

		try {
			$attributes = $this->ldapConfig->login($username, $password, $sasl_args);
		} catch (SimpleSAML_Error_Error $e) {
			if ($e->getMessage() == 'WRONGUSERPASS') {
				$user_dn = $this->ldap->searchfordn($this->config['search.base'], $this->config['search.attributes'], $username, TRUE);
				$attributes = $this->ldap->getAttributes($user_dn);
				$this->throw_common_login_errors($attributes);
			}
			throw $e;
		}
		$this->throw_common_login_errors($attributes);
		return $attributes;

	}


	/**
	 * Investigate login failure
	 *
	 * @param array $attributes
	 */
	private function throw_common_login_errors($attributes) {
		SimpleSAML_Logger::debug('got LDAP attributes:' . var_export($attributes, true));

		$the_time = time();
		// Account expired
		// Posix: shadowExpire: 1 if set: disabled , or: days since epoch the account expires
		if (isset($attributes['shadowExpire']) && is_string($attributes["shadowExpire"][0])) {
			if ((int)$attributes['shadowExpire'][0] == 1) {
				SimpleSAML_Logger::debug('LDAP Account disabled');
				throw new SimpleSAML_Error_Error('LDAP_ACCDISABLED');
			}
			else if ((int)$attributes['shadowExpire'][0] < (floor($the_time / 86400))) {
				SimpleSAML_Logger::debug('LDAP Account expired');
				throw new SimpleSAML_Error_Error('LDAP_ACCEXPIRED');
			}
		}
		// Kerberos expired
		if (isset($attributes['krb5ValidEnd']) && is_string($attributes['krb5ValidEnd'][0])) {
			// Parse strange krb5ValidEnd format '20151020000000Z' (missing T)
			$date = DateTime::createFromFormat('Ymd+', $attributes['krb5ValidEnd'][0]);
			if ($date->getTimestamp() < ($the_time + 1)) {
				SimpleSAML_Logger::debug('Kerberos Account expired');
				throw new SimpleSAML_Error_Error('KRB_ACCEXPIRED');
			}
		}
		// Samba expired
		if (isset($attributes['sambaKickoffTime']) && is_string($attributes['sambaKickoffTime'][0])) {
			if ((int)$attributes['sambaKickoffTime'][0] < $the_time) {
				SimpleSAML_Logger::debug('Samba Account expired');
				throw new SimpleSAML_Error_Error('SAMBA_ACCEXPIRED');
			}
		}

		// Password change required:
		// shadowMax + shadowLastChange < (floor(time() / 86400))
		if (isset($attributes['shadowMax']) && is_array($attributes['shadowLastChange'])) {
			if (((int)$attributes['shadowMax'][0] + (int)$attributes['shadowLastChange'][0]) < (floor($the_time / 86400))) {
				SimpleSAML_Logger::debug('LDAP password change required');
				throw new SimpleSAML_Error_Error('LDAP_PWCHANGE');
			}
		}
		// krb5PasswordEnd < today (ldap attribute format: 20161020000000Z)
		if (isset($attributes['krb5PasswordEnd']) && is_string($attributes['krb5PasswordEnd'][0])) {
			// Parse strange krb5PasswordEnd format '20151020000000Z' (missing T)
			$date = DateTime::createFromFormat('Ymd+', $attributes['krb5PasswordEnd'][0]);
			if ($date->getTimestamp() < ($the_time + 1)) {
				SimpleSAML_Logger::debug('Kerberos password change required');
				throw new SimpleSAML_Error_Error('KRB_PWCHANGE');
			}
		}
		// samba:
		if (isset($attributes['sambaKickoffTime']) && is_string($attributes['sambaKickoffTime'][0])) {
			if ((int)$attributes['sambaKickoffTime'][0] < $the_time) {
				SimpleSAML_Logger::debug('Samba password change required');
				throw new SimpleSAML_Error_Error('SAMBA_PWCHANGE');
			}
		}

		// Account Locked / deactivated:
		// samba: L in sambaAcctFlags
		if (isset($attributes['sambaAcctFlags']) && is_string($attributes['sambaAcctFlags'][0])) {
			if (strpos($attributes['sambaAcctFlags'][0],'L') !== false) {
				SimpleSAML_Logger::debug('Samba account locked');
				throw new SimpleSAML_Error_Error('SAMBA_ACCLOCKED');
			}
		}
		// krb: krb5KDCFlags=254
		if (isset($attributes['krb5KDCFlags']) && is_string($attributes['krb5KDCFlags'][0])) {
			if ((int)$attributes['krb5KDCFlags'][0] === 254) {
				SimpleSAML_Logger::debug('Kerberos account locked');
				throw new SimpleSAML_Error_Error('KRB_ACCLOCKED');
			}
		}
		// ldap: locking ldap is done by modifying password > but then ldap bind has failed anyway

		return;
	}

}


?>
