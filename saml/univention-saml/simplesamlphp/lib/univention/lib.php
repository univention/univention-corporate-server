<?php

function get_baseurlpath($baseurls, $request_uri) {
	$default_baseurlpath = 'simplesamlphp/';
	if (!($request_uri)) {
		return $default_baseurlpath;
	}
	$exploded_path = explode('/', $request_uri);
	if (count($exploded_path) < 3) {
		return $default_baseurlpath;
	}
	if (in_array($exploded_path[1] . '/' . $exploded_path[2] . '/', $baseurls)) {
		return $exploded_path[1] . '/' . $exploded_path[2] . '/';
	}
	return $default_baseurlpath;
}
