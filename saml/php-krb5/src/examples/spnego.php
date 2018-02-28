<?php
if(!extension_loaded('krb5')) {
	die('KRB5 Extension not installed');
}

$auth = new KRB5NegotiateAuth('/etc/krb5.keytab');


if($auth->doAuthentication()) {
	echo 'Success - authenticated as ' . $auth->getAuthenticatedUser();
	
	try {
		$cc = new KRB5CCache();
		$auth->getDelegatedCredentials($cc);
	} catch (Exception $error) {
		echo 'No delegated credentials available';
	}
} else {
	if(!empty($_SERVER['PHP_AUTH_USER'])) {
		header('HTTP/1.1 401 Unauthorized');
		header('WWW-Authenticate: Basic', false);
	} else {
		// verify basic authentication data
		echo 'authenticated using BASIC method<br />';
	}
}

?>
