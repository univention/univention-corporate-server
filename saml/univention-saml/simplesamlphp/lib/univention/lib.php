<?php

function get_baseurlpath($baseurls) {
	$default_baseurlpath = 'simplesamlphp/';
	if (!(array_key_exists('REQUEST_URI', $_SERVER))) {
		return $default_baseurlpath;
	}
	$exploded_path = explode('/', $_SERVER['REQUEST_URI']);
	if (count($exploded_path) < 3) {
		return $default_baseurlpath;
	}
	if (in_array($exploded_path[1] . '/' . $exploded_path[2] . '/', $baseurls)) {
		return $exploded_path[1] . '/' . $exploded_path[2] . '/';
	}
	return $default_baseurlpath;
}
