<?php

$credopts = array(
	'forwardable' => true,
	'proxiable' => true
);

$ccache = new KRB5CCache();

$ccache->initPassword("test", "foo", $credopts);

