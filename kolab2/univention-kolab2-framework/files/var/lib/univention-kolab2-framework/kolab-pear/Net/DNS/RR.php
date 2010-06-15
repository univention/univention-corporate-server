<?php
/*
 *  License Information:
 *
 *    Net_DNS:  A resolver library for PHP
 *    Copyright (c) 2002-2003 Eric Kilfoil eric@ypass.net
 *
 *    This library is free software; you can redistribute it and/or
 *    modify it under the terms of the GNU Lesser General Public
 *    License as published by the Free Software Foundation; either
 *    version 2.1 of the License, or (at your option) any later version.
 *
 *    This library is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 *    Lesser General Public License for more details.
 *
 *    You should have received a copy of the GNU Lesser General Public
 *    License along with this library; if not, write to the Free Software
 *    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

/* Include files {{{ */
require_once("$phpdns_basedir/DNS/RR/A.php");
require_once("$phpdns_basedir/DNS/RR/AAAA.php");
require_once("$phpdns_basedir/DNS/RR/NS.php");
require_once("$phpdns_basedir/DNS/RR/CNAME.php");
require_once("$phpdns_basedir/DNS/RR/PTR.php");
require_once("$phpdns_basedir/DNS/RR/SOA.php");
require_once("$phpdns_basedir/DNS/RR/MX.php");
require_once("$phpdns_basedir/DNS/RR/TSIG.php");
require_once("$phpdns_basedir/DNS/RR/TXT.php");
require_once("$phpdns_basedir/DNS/RR/HINFO.php");
require_once("$phpdns_basedir/DNS/RR/SRV.php");
require_once("$phpdns_basedir/DNS/RR/NAPTR.php");
/* }}} */
/* Net_DNS_RR object definition {{{ */
/**
 * Resource Record object definition
 *
 * Builds or parses resource record sections of the DNS  packet including
 * the answer, authority, and additional  sections of the packet.
 *
 * @package Net_DNS
 */
class Net_DNS_RR
{
    /* class variable definitions {{{ */
    var $name;
    var $type;
    var $class;
    var $ttl;
    var $rdlength;
    var $rdata;
    /* }}} */

    /*
     * I finally did it... i pass an array to the function
     * instead of a parameter list... UGH... i hate perl...
     */
    /* class constructor - Net_DNS_RR($rrdata) {{{ */
    function Net_DNS_RR($rrdata)
    {
        if (is_string($rrdata)) {
            $this = $this->new_from_string($rrdata);
        } else if (count($rrdata) == 7) {
            list ($name, $rrtype, $rrclass, $ttl, $rdlength, $data, $offset) = $rrdata;
            $this = $this->new_from_data($name, $rrtype, $rrclass, $ttl, $rdlength, $data, $offset);
        } else {
            $this = $this->new_from_array($rrdata);
        }
    }

    /* }}} */
    /* Net_DNS_RR::new_from_data($name, $ttl, $rrtype, $rrclass, $rdlength, $data, $offset) {{{ */
    function new_from_data($name, $rrtype, $rrclass, $ttl, $rdlength, $data, $offset)
    {
        $this->name = $name;
        $this->type = $rrtype;
        $this->class = $rrclass;
        $this->ttl = $ttl;
        $this->rdlength = $rdlength;
        $this->rdata = substr($data, $offset, $rdlength);
        if (class_exists('Net_DNS_RR_' . $rrtype)) {
            $scn = 'Net_DNS_RR_' . $rrtype;
            $subclass = new $scn($this, $data, $offset);
            return($subclass);
        } else {
            return($this);
        }
    }

    /* }}} */
    /* Net_DNS_RR::new_from_string($rrstring, $update_type = '') {{{ */
    function new_from_string($rrstring, $update_type = '')
    {
        $ttl = 0;
        $parts = preg_split('/[\s]+/', $rrstring);
        while ($s = array_shift($parts)) {
            if (!isset($name)) {
                $name = ereg_replace('\.+$', '', $s);
            } else if (preg_match('/^\d+$/', $s)) {
                $ttl = $s;
            } else if (!isset($rrclass) && ! is_null(Net_DNS::classesbyname(strtoupper($s)))) {
                $rrclass = strtoupper($s);
                $rdata = join(' ', $parts);
            } else if (! is_null(Net_DNS::typesbyname(strtoupper($s)))) {
                $rrtype = strtoupper($s);
                $rdata = join(' ', $parts);
                break;
            } else {
                break;
            }
        }

        /*
         *  Do we need to do this?
         */
        $rdata = trim(chop($rdata));

        if (! strlen($rrtype) && strlen($rrclass) && $rrclass == 'ANY') {
            $rrtype = $rrclass;
            $rrclass = 'IN';
        } else if (! isset($rrclass)) {
            $rrclass = 'IN';
        }

        if (! strlen($rrtype)) {
            $rrtype = 'ANY';
        }

        if (strlen($update_type)) {
            $update_type = strtolower($update_type);
            if ($update_type == 'yxrrset') {
                $ttl = 0;
                if (! strlen($rdata)) {
                    $rrclass = 'ANY';
                }
            } else if ($update_type == 'nxrrset') {
                $ttl = 0;
                $rrclass = 'NONE';
                $rdata = '';
            } else if ($update_type == 'yxdomain') {
                $ttl = 0;
                $rrclass = 'ANY';
                $rrtype = 'ANY';
                $rdata = '';
            } else if ($update_type == 'nxdomain') {
                $ttl = 0;
                $rrclass = 'NONE';
                $rrtype = 'ANY';
                $rdata = '';
            } else if (preg_match('/^(rr_)?add$/', $update_type)) {
                $update_type = 'add';
                if (! $ttl) {
                    $ttl = 86400;
                }
            } else if (preg_match('/^(rr_)?del(ete)?$/', $update_type)) {
                $update_type = 'del';
                $ttl = 0;
                $rrclass = $rdata ? 'NONE' : 'ANY';
            }
        }

        if (strlen($rrtype)) {
            $this->name = $name;
            $this->type = $rrtype;
            $this->class = $rrclass;
            $this->ttl = $ttl;
            $this->rdlength = 0;
            $this->rdata = '';

            if (class_exists('Net_DNS_RR_' . $rrtype)) {
                $scn = 'Net_DNS_RR_' . $rrtype;
                $rc = new $scn($this, $rdata);
                return($rc);
            } else {
                return($this);
            }
        } else {
            return(NULL);
        }
    }

    /* }}} */
    /* Net_DNS_RR::new_from_array($rrarray) {{{ */
    function new_from_array($rrarray)
    {
        foreach ($rrarray as $k => $v) {
            $this->{strtolower($k)} = $v;
        }

        if (! strlen($this->name)) {
            return(NULL);
        }
        if (! strlen($this->type)){
            return(NULL);
        }
        if (! $this->ttl) {
            $this->ttl = 0;
        }
        if (! strlen($this->class)) {
            $this->class = 'IN';
        }
        if (strlen($this->rdata)) {
            $this->rdlength = strlen($rdata);
        }
        if (class_exists('Net_DNS_RR_' . $rrtype)) {
            $scn = 'Net_DNS_RR_' . $rrtype;
            $rc = new $scn($this, $rdata);
            return($rc);
        } else
            return($this);
    }

    /* }}} */
    /* Net_DNS_RR::display() {{{ */
    function display()
    {
        echo $this->string() . "\n";
    }

    /* }}} */
    /* Net_DNS_RR::string() {{{ */
    function string()
    {
        return($this->name . ".\t" . (strlen($this->name) < 16 ? "\t" : '') .
                $this->ttl  . "\t"  .
                $this->class. "\t"  .
                $this->type . "\t"  .
                $this->rdatastr());

    }

    /* }}} */
    /* Net_DNS_RR::rdatastr() {{{ */
    function rdatastr()
    {
        if ($this->rdlength) {
            return('; rdlength = ' . $this->rdlength);
        }
        return('; no data');
    }

    /* }}} */
    /* Net_DNS_RR::rdata() {{{ */
    function rdata(&$packetORrdata, $offset = '')
    {
        if ($offset) {
            return($this->rr_rdata($packetORrdata, $offset));
        } else if (strlen($this->rdata)) {
            return($this->rdata);
        } else {
            return(NULL);
        }
    }

    /* }}} */
    /* Net_DNS_RR::rr_rdata($packet, $offset) {{{ */
    function rr_rdata(&$packet, $offset)
    {
        return((strlen($this->rdata) ? $this->rdata : ''));
    }
    /* }}} */
    /* Net_DNS_RR::data() {{{ */
    function data(&$packet, $offset)
    {
        $data = $packet->dn_comp($this->name, $offset);
        $data .= pack('n', Net_DNS::typesbyname(strtoupper($this->type)));
        $data .= pack('n', Net_DNS::classesbyname(strtoupper($this->class)));
        $data .= pack('N', $this->ttl);

        $offset += strlen($data) + 2;  // The 2 extra bytes are for rdlength

        $rdata = $this->rdata($packet, $offset);
        $data .= pack('n', strlen($rdata));
        $data .= $rdata;

        return($data);
    }
    /* }}} */
}
/* }}} */
/* VIM settings {{{
 * Local variables:
 * tab-width: 4
 * c-basic-offset: 4
 * soft-stop-width: 4
 * c indent on
 * End:
 * vim600: sw=4 ts=4 sts=4 cindent fdm=marker et
 * vim<600: sw=4 ts=4
 * }}} */
?>
