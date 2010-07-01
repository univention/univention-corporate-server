<?php
/**
 * @category Horde
 * @package Horde_Rdo
 */

/*
I have been exploring ZF to implement for my client and found a few
interesting things that I thought might be of interest to others using
the Oracle oci8 driver. While not really "broken", the support for the
Oracle oci8 driver does appear to be missing a few useful / convenient
features:

The Zend_Db_Oracle driver ignores the 'host' parameter. This is only
an issue when PHP is compiled with Oracles instant client which need
not use TNS. For instance the following $dsn throws the following
exception "TNS:could not resolve the connect identifier specified"

Fails:

$dsn = array(
    'host'      =>'myhost',
    'username'  => 'zend',
    'password'  => 'zend',
    'dbname'    => 'xe',
    'options'   => $options
);

This is not surprising since the instant client does not use TNS as
stated. To get this to work you need to prepend the 'dbname' parameter
with the host name, which although easy to do is not very intuitive.

Works:

$dsn = array(
    'host' => 'totally ignored',
    'username'  => 'zend',
    'password'  => 'zend',
    'dbname'    => 'myhost/xe',
    'options'   => $options
);

Zend_Db_Statement_Oracle

This class states that it does not support case folding due to a
limitation of the Oci8 driver. The driver may not support case
folding, but after a quick review of the code I was curious as to why
this was not emulated, at least for results being returned as an
associative array (objects would not be much of a stretch either)?
This would be a great feature to have and save those looking for this
feature from having to call the array_change_key_case() function on
every row returned J
*/

/**
 * @TODO
 */
class Horde_Rdo_Adapter_Oci8 extends Horde_Rdo_Adapter {

    /**
     * Build a connection string and connect to the database server.
     *
     * @TODO http://blogs.oracle.com/opal/discuss/msgReader$111
     */
    protected function _connect()
    {
    }

}
