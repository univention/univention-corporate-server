from base64 import b64decode
from os.path import dirname, join
from importlib.util import module_from_spec, spec_from_file_location
import sys

import pytest


DN = "cn=test"
BASE = {
    "SAMLServiceProviderIdentifier": [b"spi"],
    "isServiceProviderActivated": [b"TRUE"],
}

spec = spec_from_file_location("udl4", join(dirname(__file__), "../listener/univention-saml-simplesamlphp-configuration.py"))
udl = module_from_spec(spec)
spec.loader.exec_module(udl)  # type: ignore
sys.modules["udl4"] = udl


class TestBool(object):
    @pytest.mark.parametrize("value", [b"TRUE", b"True", b"true", b"1"])
    def test_true(self, value):
        assert udl.ldap2bool(value) is True

    @pytest.mark.parametrize("value", [b"FALSE", b"False", b"false", b"0"])
    def test_false(self, value):
        assert udl.ldap2bool(value) is False

    @pytest.mark.parametrize("value", [b"", b"invalid", b"3"])
    def test_invalid(self, value):
        with pytest.raises(TypeError):
            udl.ldap2bool(value)


class TestHandler(object):

    DUMMY = {"objectClass": [b"univentionSAMLServiceProvider"]}

    def test_old(self, mocker):
        mocked_old = mocker.patch("udl4.delete_old")
        mocked_new = mocker.patch("udl4.build_new")
        mocked_inc = mocker.patch("udl4.build_include")
        udl.handler(DN, {}, self.DUMMY)
        mocked_old.assert_called_once_with(self.DUMMY)
        mocked_new.assert_not_called()
        mocked_inc.assert_called_once()

    def test_new(self, mocker):
        mocked_old = mocker.patch("udl4.delete_old")
        mocked_new = mocker.patch("udl4.build_new")
        mocked_inc = mocker.patch("udl4.build_include")
        udl.handler(mocker.sentinel.dn, self.DUMMY, {})
        mocked_old.assert_not_called()
        mocked_new.assert_called_once_with(mocker.sentinel.dn, self.DUMMY)
        mocked_inc.assert_called_once()


def test_spi2filename():
    assert udl.spi2filename(b"some/spi") == "/etc/simplesamlphp/metadata.d/some_spi.php"


def test_delete_old(mocker):
    mocked_exists = mocker.patch("os.path.exists")
    mocked_exists.return_value = True
    mocked_unlink = mocker.patch("os.unlink")
    udl.delete_old(BASE)
    mocked_exists.assert_called_once_with("/etc/simplesamlphp/metadata.d/spi.php")
    mocked_unlink.assert_called_once_with("/etc/simplesamlphp/metadata.d/spi.php")


def test_build_new(mocker, tmpdir):
    cfg = tmpdir.join("cfg")
    mocker.patch("udl4.spi2filename").return_value = str(cfg)
    mocked_wcf = mocker.patch("udl4.write_configuration_file")
    mocked_vc = mocker.patch("udl4.validate_conf")
    udl.build_new(mocker.sentinel.dn, BASE)
    mocked_wcf.assert_called_once_with(mocker.sentinel.dn, BASE, mocker.ANY)
    mocked_vc.assert_called_once_with(str(cfg))


def test_build_include(monkeypatch, tmpdir):
    mdir = tmpdir.mkdir("metadata.d")
    m0 = mdir.ensure("0.php.old")
    m1 = mdir.ensure("1.php")
    m2 = mdir.ensure("2.php")
    cfg = tmpdir.join("metadata_include.php")

    monkeypatch.setattr(udl, "sp_config_dir", str(mdir))
    monkeypatch.setattr(udl, "include_file", str(cfg))
    udl.build_include()

    data = cfg.read()
    assert data.startswith("<?php\n")
    assert "require_once('%s');" % m0 not in data
    assert "require_once('%s');" % m1 in data
    assert "require_once('%s');" % m2 in data


class TestWriteConfiguration_file(object):
    def test_raw(self, mocker):
        new = dict(
            BASE,
            rawsimplesamlSPconfig=[b"RAW"],
        )
        fd = mocker.Mock()
        udl.write_configuration_file(mocker.sentinel.dn, new, fd)
        fd.write.assert_called_once_with("RAW")

    def test_meta(self, mocker):
        mocked_conf = mocker.patch("udl4.build_conf")
        udl.write_configuration_file(mocker.sentinel.dn, BASE, mocker.sentinel.fd)
        mocked_conf.assert_called_once_with(mocker.sentinel.dn, BASE, mocker.sentinel.fd, b"", "spi")



class TestParseMetadata(object):
    DATA = b64decode(
        b"PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0nVVRGLTgnPz4KPG5zMDpFbnRpdHlEZXNjcmlwdG9yIHhtbG5zOm5zMD0idXJuOm9hc2lzOm5hbWVzOnRjOlNBTUw6Mi4wOm1ldGFkYXRhIiB4bWxuczpuczE9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvMD"
        b"kveG1sZHNpZyMiIGVudGl0eUlEPSJodHRwczovL2RjMC5waGFobi5kZXYvdW5pdmVudGlvbi9zYW1sL21ldGFkYXRhIj48bnMwOlNQU1NPRGVzY3JpcHRvciBBdXRoblJlcXVlc3RzU2lnbmVkPSJ0cnVlIiBXYW50QXNzZXJ0aW9uc1NpZ25lZD0idHJ1ZSIgcHJvdG9jb2xTdXBwb3J0RW51b"
        b"WVyYXRpb249InVybjpvYXNpczpuYW1lczp0YzpTQU1MOjIuMDpwcm90b2NvbCI+PG5zMDpLZXlEZXNjcmlwdG9yIHVzZT0ic2lnbmluZyI+PG5zMTpLZXlJbmZvPjxuczE6WDUwOURhdGE+PG5zMTpYNTA5Q2VydGlmaWNhdGU+TUlJRkVqQ0NBL3FnQXdJQkFnSUJCREFOQmdrcWhraUc5dzBC"
        b"QVFzRkFEQ0J0ekVMTUFrR0ExVUVCaE1DUkVVeApDekFKQmdOVkJBZ1RBa1JGTVFzd0NRWURWUVFIRXdKRVJURU9NQXdHQTFVRUNoTUZjR2hoYUc0eEpEQWlCZ05WCkJBc1RHMVZ1YVhabGJuUnBiMjRnUTI5eWNHOXlZWFJsSUZObGNuWmxjakU2TURnR0ExVUVBeE14Vlc1cGRtVnUKZEdsdmJ"
        b"pQkRiM0p3YjNKaGRHVWdVMlZ5ZG1WeUlGSnZiM1FnUTBFZ0tFbEVQWE5DT0dNemVGWk9LVEVjTUJvRwpDU3FHU0liM0RRRUpBUllOYzNOc1FIQm9ZV2h1TG1SbGRqQWVGdzB4TnpBeU1EWXhNakEwTVRaYUZ3MHlNakF5Ck1EVXhNakEwTVRaYU1JR1RNUXN3Q1FZRFZRUUdFd0pFUlRFTE1Ba0"
        b"dBMVVFQ0JNQ1JFVXhDekFKQmdOVkJBY1QKQWtSRk1RNHdEQVlEVlFRS0V3VndhR0ZvYmpFa01DSUdBMVVFQ3hNYlZXNXBkbVZ1ZEdsdmJpQkRiM0p3YjNKaApkR1VnVTJWeWRtVnlNUll3RkFZRFZRUURFdzFrWXpBdWNHaGhhRzR1WkdWMk1Sd3dHZ1lKS29aSWh2Y05BUWtCCkZnMXpjMnhBY"
        b"0doaGFHNHVaR1YyTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUEKNStlZkV6UUFtSHp2b0VBSUtvcDNZLy9GZ0wreWhpYkJMVTFGaTVtclNQTmgwL1QxczV2cmtzaWFvT3BZTXBZWQpWdDJFR1ZQbjJoZVY3eUwwanhIK2E1SW1KY21TekZXZ2NQWW5ranQvQllz"
        b"eW5oT1R0K3pQbnZpampWR1dIYVJECkJDY0RuWkJxV0hMOGh5c3p0WXQvcFlzYnBnc3RJTDR2MGtqckJ6WThpZ1BwYVgrZi9ZMEZpWFNvNU1rN09QQWcKcVNiQ29WbnNZcFkvTVV4N0FWM0lKdWRlR2grcGxwTE9sQUEzMVlVcnEwQnVEMndHc0dVNHVHQkUzMlI5WHpwcwprMlJoUHEvZkhsTGR"
        b"4L0haeFBuOUFVS3VXSFRxVEtQMXgxenhjOVZKYmpjZnUyV3ozRCtlRjJUaFNNNEo2NjJHClZ6dkJGOTdMd1RxN1drZXU2TkJURVFJREFRQUJvNElCU1RDQ0FVVXdDUVlEVlIwVEJBSXdBREFkQmdOVkhRNEUKRmdRVS9uQzg4aXpnd1JCSlEvZW04RzZTdFB1RUt4b3dnZXdHQTFVZEl3U0I1RE"
        b"NCNFlBVVJIMGR0MW1FemMybwoveUt3RkgrOEhScHZ0cldoZ2Iya2dib3dnYmN4Q3pBSkJnTlZCQVlUQWtSRk1Rc3dDUVlEVlFRSUV3SkVSVEVMCk1Ba0dBMVVFQnhNQ1JFVXhEakFNQmdOVkJBb1RCWEJvWVdodU1TUXdJZ1lEVlFRTEV4dFZibWwyWlc1MGFXOXUKSUVOdmNuQnZjbUYwWlNCV"
        b"FpYSjJaWEl4T2pBNEJnTlZCQU1UTVZWdWFYWmxiblJwYjI0Z1EyOXljRzl5WVhSbApJRk5sY25abGNpQlNiMjkwSUVOQklDaEpSRDF6UWpoak0zaFdUaWt4SERBYUJna3Foa2lHOXcwQkNRRVdEWE56CmJFQndhR0ZvYmk1a1pYYUNDUURFSzgzd1RBbERYVEFMQmdOVkhROEVCQU1DQmVBd0hR"
        b"WURWUjBSQkJZd0ZJSU4KWkdNd0xuQm9ZV2h1TG1SbGRvSURaR013TUEwR0NTcUdTSWIzRFFFQkN3VUFBNElCQVFBeHVVRDBKMUFLUTFvNwplRzFHbmRhWm9RZi9rVjNnYkh1Y1o4T0dBazF3RW1OTDZiWG1LbGVhWWVkL1pwWjhQQklieVpycjhLSUJyUEFzCmVZUE8zaHJhY01oTlFLOW1WS2l"
        b"ZUFp6d29hQWpWM2ZVZG05dEVDanh4TUxuNXNvL3drTStCTllrWFpCKytEWmoKN2kyYW1NTms3NVZ2ck9NMEcvRElnbkpqazRXOWx5eTdmaEU1SWNUTGwxTlBRYnlqZklWa00vS3pJS2pGV1dmSgpkZEFhd3FqSnU3RGVRRmVlMmFOSTFJK3pXa1NDTkFoMWhLclR5ZW5UUzNxcUxsRmVPa3JPSl"
        b"I4MjU4WUt4STMxCmNBQUF4K0d6c082WkJtR2dLM0hwQ0RQTjVhL2FnMU13UmFlNW9BblBkSGNEN1c2MG05RWdtSHpCWDFPVDNqdkgKdWR1ME01RTIKPC9uczE6WDUwOUNlcnRpZmljYXRlPjwvbnMxOlg1MDlEYXRhPjwvbnMxOktleUluZm8+PC9uczA6S2V5RGVzY3JpcHRvcj48bnMwOlNpb"
        b"mdsZUxvZ291dFNlcnZpY2UgQmluZGluZz0idXJuOm9hc2lzOm5hbWVzOnRjOlNBTUw6Mi4wOmJpbmRpbmdzOkhUVFAtUE9TVCIgTG9jYXRpb249Imh0dHBzOi8vZGMwLnBoYWhuLmRldi91bml2ZW50aW9uL3NhbWwvc2xvLyIgLz48bnMwOlNpbmdsZUxvZ291dFNlcnZpY2UgQmluZGluZz0i"
        b"dXJuOm9hc2lzOm5hbWVzOnRjOlNBTUw6Mi4wOmJpbmRpbmdzOkhUVFAtUmVkaXJlY3QiIExvY2F0aW9uPSJodHRwczovL2RjMC5waGFobi5kZXYvdW5pdmVudGlvbi9zYW1sL3Nsby8iIC8+PG5zMDpTaW5nbGVMb2dvdXRTZXJ2aWNlIEJpbmRpbmc9InVybjpvYXNpczpuYW1lczp0YzpTQU1"
        b"MOjIuMDpiaW5kaW5nczpIVFRQLVBPU1QiIExvY2F0aW9uPSJodHRwOi8vZGMwLnBoYWhuLmRldi91bml2ZW50aW9uL3NhbWwvc2xvLyIgLz48bnMwOlNpbmdsZUxvZ291dFNlcnZpY2UgQmluZGluZz0idXJuOm9hc2lzOm5hbWVzOnRjOlNBTUw6Mi4wOmJpbmRpbmdzOkhUVFAtUmVkaXJlY3"
        b"QiIExvY2F0aW9uPSJodHRwOi8vZGMwLnBoYWhuLmRldi91bml2ZW50aW9uL3NhbWwvc2xvLyIgLz48bnMwOlNpbmdsZUxvZ291dFNlcnZpY2UgQmluZGluZz0idXJuOm9hc2lzOm5hbWVzOnRjOlNBTUw6Mi4wOmJpbmRpbmdzOkhUVFAtUE9TVCIgTG9jYXRpb249Imh0dHBzOi8vMTkyLjE2O"
        b"C4wLjE1NC91bml2ZW50aW9uL3NhbWwvc2xvLyIgLz48bnMwOlNpbmdsZUxvZ291dFNlcnZpY2UgQmluZGluZz0idXJuOm9hc2lzOm5hbWVzOnRjOlNBTUw6Mi4wOmJpbmRpbmdzOkhUVFAtUmVkaXJlY3QiIExvY2F0aW9uPSJodHRwczovLzE5Mi4xNjguMC4xNTQvdW5pdmVudGlvbi9zYW1s"
        b"L3Nsby8iIC8+PG5zMDpTaW5nbGVMb2dvdXRTZXJ2aWNlIEJpbmRpbmc9InVybjpvYXNpczpuYW1lczp0YzpTQU1MOjIuMDpiaW5kaW5nczpIVFRQLVBPU1QiIExvY2F0aW9uPSJodHRwOi8vMTkyLjE2OC4wLjE1NC91bml2ZW50aW9uL3NhbWwvc2xvLyIgLz48bnMwOlNpbmdsZUxvZ291dFN"
        b"lcnZpY2UgQmluZGluZz0idXJuOm9hc2lzOm5hbWVzOnRjOlNBTUw6Mi4wOmJpbmRpbmdzOkhUVFAtUmVkaXJlY3QiIExvY2F0aW9uPSJodHRwOi8vMTkyLjE2OC4wLjE1NC91bml2ZW50aW9uL3NhbWwvc2xvLyIgLz48bnMwOkFzc2VydGlvbkNvbnN1bWVyU2VydmljZSBCaW5kaW5nPSJ1cm"
        b"46b2FzaXM6bmFtZXM6dGM6U0FNTDoyLjA6YmluZGluZ3M6SFRUUC1QT1NUIiBMb2NhdGlvbj0iaHR0cHM6Ly9kYzAucGhhaG4uZGV2L3VuaXZlbnRpb24vc2FtbC8iIGluZGV4PSIxIiAvPjxuczA6QXNzZXJ0aW9uQ29uc3VtZXJTZXJ2aWNlIEJpbmRpbmc9InVybjpvYXNpczpuYW1lczp0Y"
        b"zpTQU1MOjIuMDpiaW5kaW5nczpIVFRQLVBPU1QiIExvY2F0aW9uPSJodHRwOi8vZGMwLnBoYWhuLmRldi91bml2ZW50aW9uL3NhbWwvIiBpbmRleD0iMiIgLz48bnMwOkFzc2VydGlvbkNvbnN1bWVyU2VydmljZSBCaW5kaW5nPSJ1cm46b2FzaXM6bmFtZXM6dGM6U0FNTDoyLjA6YmluZGlu"
        b"Z3M6SFRUUC1QT1NUIiBMb2NhdGlvbj0iaHR0cHM6Ly8xOTIuMTY4LjAuMTU0L3VuaXZlbnRpb24vc2FtbC8iIGluZGV4PSIzIiAvPjxuczA6QXNzZXJ0aW9uQ29uc3VtZXJTZXJ2aWNlIEJpbmRpbmc9InVybjpvYXNpczpuYW1lczp0YzpTQU1MOjIuMDpiaW5kaW5nczpIVFRQLVBPU1QiIEx"
        b"vY2F0aW9uPSJodHRwOi8vMTkyLjE2OC4wLjE1NC91bml2ZW50aW9uL3NhbWwvIiBpbmRleD0iNCIgLz48bnMwOkF0dHJpYnV0ZUNvbnN1bWluZ1NlcnZpY2UgaW5kZXg9IjEiPjxuczA6U2VydmljZU5hbWUgeG1sOmxhbmc9ImVuIiAvPjxuczA6U2VydmljZURlc2NyaXB0aW9uIHhtbDpsYW"
        b"5nPSJlbiI+VW5pdmVudGlvbiBNYW5hZ2VtZW50IENvbnNvbGUgU0FNTDIuMCBTZXJ2aWNlIFByb3ZpZGVyPC9uczA6U2VydmljZURlc2NyaXB0aW9uPjxuczA6UmVxdWVzdGVkQXR0cmlidXRlIEZyaWVuZGx5TmFtZT0idWlkIiBOYW1lPSJ1cm46b2lkOjAuOS4yMzQyLjE5MjAwMzAwLjEwM"
        b"C4xLjEiIE5hbWVGb3JtYXQ9InVybjpvYXNpczpuYW1lczp0YzpTQU1MOjIuMDphdHRybmFtZS1mb3JtYXQ6dXJpIiBpc1JlcXVpcmVkPSJ0cnVlIiAvPjwvbnMwOkF0dHJpYnV0ZUNvbnN1bWluZ1NlcnZpY2U+PC9uczA6U1BTU09EZXNjcmlwdG9yPjwvbnMwOkVudGl0eURlc2NyaXB0b3I+"
    )

    def test_none(self):
        udl.parse_metadata({}) is None

    def test_incomplete(self):
        new = {"serviceProviderMetadata": [b""]}
        assert udl.parse_metadata(new) is None

    def test_xml(self):
        new = {"serviceProviderMetadata": [self.DATA]}
        metadata, entityid = udl.parse_metadata(new)
        assert metadata
        assert entityid == "https://dc0.phahn.dev/univention/saml/metadata"


class TestBuildConf():
    @pytest.fixture
    def cfg(self, tmpdir):
        return tmpdir.ensure("cfg")

    def test_min(self, cfg, popen):
        metadata = b""
        entityid = "https://dc0.phahn.dev/univention/saml/metadata"
        with cfg.open("w") as fd:
            udl.build_conf(DN, BASE, fd, metadata, entityid)

        data = cfg.read()
        assert data.startswith("<?php\n")
        assert data.endswith(");\n")
        popen.assert_not_called()

    def test_max(self, cfg):
        new = dict(
            BASE,
            AssertionConsumerService=[b"A", b"B"],
            singleLogoutService=[b"A", b"B"],
            signLogouts=[b"TRUE"],
            NameIDFormat=[b"A"],
            simplesamlNameIDAttribute=[b"A"],
            simplesamlAttributes=[b"TRUE"],
            simplesamlLDAPattributes=[b"A", b"B"],
            attributesNameFormat=[b"A"],
            serviceproviderdescription=[b"A"],
            serviceProviderOrganizationName=[b"A"],
            privacypolicyURL=[b"A"],
            assertionLifetime=[b"123"],
        )
        metadata = b""
        entityid = "https://dc0.phahn.dev/univention/saml/metadata"
        with cfg.open("w") as fd:
            udl.build_conf(DN, new, fd, metadata, entityid)

        data = cfg.read()
        assert data.startswith("<?php\n")
        assert data.endswith(");\n")

    def test_metadata(self, cfg, popen, mocker):
        metadata = b"<xml/>"
        entityid = "https://dc0.phahn.dev/univention/saml/metadata"
        with cfg.open("w") as fd:
            udl.build_conf(DN, BASE, fd, metadata, entityid)

        popen.assert_called_once_with(["php",mocker.ANY, entityid], stdout=mocker.ANY, stderr=mocker.ANY, stdin=mocker.ANY)
        popen.return_value.communicate.assert_called_once_with(metadata)


def test_parse_mapping():
    attrs = [b"a", b"b=b", b"c=d", b"c=e"]
    attributes, mapping = udl.parse_mapping(attrs)
    assert attributes == {b"a", b"b", b"c"}
    assert mapping == {b"c": [b"d", b"e"]}


def test_validate_conf(mocker, popen):
    udl.validate_conf(mocker.sentinel.filename)
    popen.assert_called_once_with(['php', '-lf', mocker.sentinel.filename], stderr=mocker.ANY, stdout=mocker.ANY)


@pytest.fixture
def popen(mocker):
    mocked_popen = mocker.patch("udl4.Popen")
    mocked_popen.return_value.communicate.return_value = b"", b""
    mocked_popen.return_value.returncode = 0
    return mocked_popen
