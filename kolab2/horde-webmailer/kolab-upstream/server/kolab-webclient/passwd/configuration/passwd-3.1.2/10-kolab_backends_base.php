<?php

$backends = array();

$backends['kolab'] = array(
    'name' => 'Local Kolab Server',
    'preferred' => '',
    'password policy' => array(
        'minLength' => 3,
        'maxLength' => 8
    ),
    'driver' => 'kolab',
    'params' => array()
);
