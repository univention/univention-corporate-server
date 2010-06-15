<?php
include 'Net/DIME.php';

$test='--=_a2cbb051424cc43e72d3c8c8d0b8f70e
Content-Type: text/xml; charset="UTF-8"

<?xml version="1.0" encoding="UTF-8"?>

<SOAP-ENV:Envelope  xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
  xmlns:xsd="http://www.w3.org/2001/XMLSchema"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/"
  SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<SOAP-ENV:Body>

<echoMimeAttachment>
<test href="cid:a223fea3c35b5f0e6dedf8da75efd6b3"/></echoMimeAttachment>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>

--=_a2cbb051424cc43e72d3c8c8d0b8f70e
Content-Disposition: attachment.php
Content-Type: text/plain
Content-Transfer-Encoding: base64
Content-ID: <a223fea3c35b5f0e6dedf8da75efd6b3>

PD9waHANCnJlcXVpcmVfb25jZSgiU09BUC9DbGllbnQucGhwIik7DQpyZXF1aXJlX29uY2UoIlNP
QVAvdGVzdC90ZXN0LnV0aWxpdHkucGhwIik7DQpyZXF1aXJlX29uY2UoIlNPQVAvVmFsdWUucGhw
Iik7DQokc29hcF9iYXNlID0gbmV3IFNPQVBfQmFzZSgpOw0KDQokdiA9ICBuZXcgU09BUF9BdHRh
Y2htZW50KCd0ZXN0JywndGV4dC9wbGFpbicsJ2F0dGFjaG1lbnQucGhwJyk7DQokbWV0aG9kVmFs
dWUgPSBuZXcgU09BUF9WYWx1ZSgndGVzdGF0dGFjaCcsICdTdHJ1Y3QnLCBhcnJheSgkdikpOw0K
DQovLyBzZWUgdGhlIG1pbWUgYXJyYXkNCi8vJHZhbCA9ICRzb2FwX2Jhc2UtPl9tYWtlRW52ZWxv
cGUoJG1ldGhvZFZhbHVlKTsNCi8vcHJpbnRfcigkdmFsKTsNCg0KJGNsaWVudCA9IG5ldyBTT0FQ
X0NsaWVudCgnaHR0cDovL2xvY2FsaG9zdC9zb2FwX2ludGVyb3Avc2VydmVyX3JvdW5kMi5waHAn
KTsNCiRyZXNwID0gJGNsaWVudC0+Y2FsbCgnZWNob01pbWVBdHRhY2htZW50JyxhcnJheSgkdikp
Ow0KI3ByaW50X3IoJHJlc3ApOw0KcHJpbnQgJGNsaWVudC0+d2lyZTsNCj8+
--=_a2cbb051424cc43e72d3c8c8d0b8f70e--
';

$data = NULL;
$dime = new Net_DIME_Record($data);
#$dime->setMB();
$dime->generateID();
$dime->setType('text/plain');
$dime->setData($test);
print_r($dime->_record);
$enc = $dime->encode();
print bin2hex(substr($enc,0,8))."\n";
print chunk_split(bin2hex(substr($enc,8)),72)."\n";
$dime->decode($enc);
print_r($dime->_record);
?>