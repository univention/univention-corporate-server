<?php

@%@BCWARNING=// @%@

/**
 * IMP Hooks configuration file.
 *
 * For more information please see the hooks.php.dist file.
 */

class IMP_Hooks
{
    /**
     * PREFERENCE INIT: Set preference values on login.
     *
     * See horde/config/hooks.php.dist for more information.
     */
    public function prefs_init($pref, $value, $username, $scope_ob)
    {
        switch ($pref) {
        case 'add_source':
            // Dynamically set the add_source preference.
            return is_null($username)
                ? $value
                : $GLOBALS['registry']->call('contacts/getDefaultShare');


        case 'search_fields':
        case 'search_sources':
            // Dynamically set the search_fields/search_sources preferences.
            if (!is_null($username)) {
                $sources = $GLOBALS['registry']->call('contacts/sources');

                if ($pref == 'search_fields') {
                    $out = array();
                    foreach (array_keys($sources) as $source) {
                        $out[$source] = array_keys($GLOBALS['registry']->call('contacts/fields', array($source)));
                    }
                } else {
                    $out = array_keys($sources);
                }

                return json_encode($out);
            }

            return $value;
        }
    }

	public function preauthenticate($userId, $credentials) {

		$userId = escapeshellcmd($userId);
		$handle = popen("/usr/share/univention-horde4/univention-horde-login-wrapper '$userId'","r");
		$Id = fread($handle, 2096);
		pclose($handle);

		return array(
			'userId' => $Id,
			'credentials' => $credentials,
		);
	}

}

