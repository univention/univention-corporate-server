#!/usr/bin/python3
"""Unit test for univention.config_registry.frontend."""
# vim:set fileencoding=utf-8:

import sys
from io import StringIO

import pytest

import univention.config_registry.frontend as ucrfe

if sys.version_info >= (3,):
	from importlib import reload


@pytest.fixture
def defaults(mocker):
	"""Mock default value registration."""
	return mocker.patch("univention.config_registry.frontend._register_variable_default_values")


@pytest.fixture
def gopt():
	"""Set global options for frontend handler functions."""
	old = {}

	def func(**kwargs):
		for key, val in kwargs.items():
			if key not in old:
				old[key] = ucrfe.OPT_FILTERS[key][2]

			ucrfe.OPT_FILTERS[key][2] = val

	yield func

	for key, value in old.items():
		ucrfe.OPT_FILTERS[key][2] = value


@pytest.fixture
def vinfo():
	"""Fake variable info."""
	return {
		"description": "description",
		"type": "str",
		"categories": "category",
		"default": "default",
	}


@pytest.fixture
def rinfo(mocker, vinfo):
	"""Fake registry info."""
	info = mocker.patch("univention.config_registry.frontend._get_config_registry_info")
	info.return_value.get_category.return_value = None
	info.return_value.get_variable.return_value = vinfo
	info.return_value.get_variables.return_value = {"key": vinfo}
	info.return_value.describe_search_term.return_value = {}
	return info


@pytest.fixture
def run(mocker):
	"""Mock frontend._run_changed."""
	return mocker.patch("univention.config_registry.frontend._run_changed")


def test_UnknownKeyException():
	assert str(ucrfe.UnknownKeyException("key")) == 'W: Unknown key: "key"'


class TestReplog(object):

	@pytest.fixture
	def replog(self, monkeypatch, tmpdir, ucr0):
		"""
		Empty UCR for replog testing.
		"""
		log = tmpdir / "replog"
		monkeypatch.setattr(ucrfe, "REPLOG_FILE", str(log))
		return log

	@pytest.fixture
	def ucrr(self, ucr0):
		ucr0["ucr/replog/enabled"] = "true"
		return ucr0

	def test_replog_new(self, replog, ucrr):
		ucrfe.replog(ucrr, u"key", None, u"new")
		assert u": set key=new old:[Previously undefined]\n" in replog.read()

	def test_replog_set(self, replog, ucrr):
		ucrfe.replog(ucrr, u"key", u"old", u"new")
		assert u": set key=new old:old\n" in replog.read()

	def test_replog_unset(self, replog, ucrr):
		ucrfe.replog(ucrr, u"key", u"old")
		assert u": unset 'key' old:old\n" in replog.read()

	def test_replog_error(self, monkeypatch, tmpdir, ucrr):
		log = tmpdir / "dir" / "replog"
		monkeypatch.setattr(ucrfe, "REPLOG_FILE", str(log))
		with pytest.raises(SystemExit) as exc_info:
			ucrfe.replog(ucrr, u"key", u"old")

		assert exc_info.value.code != 0

	def test_replog_bytes(self, replog, ucrr):
		ucrfe.replog(ucrr, "key", "old", "new")
		assert u": set key=new old:old\n" in replog.read()


@pytest.mark.parametrize("opt,scope", [
	("ldap-policy", "LDAP"),
	("force", "FORCED"),
	("schedule", "SCHEDULE"),
	("", "NORMAL"),
])
def test_ucr_from_opts(opt, scope, mocker):
	ucr = mocker.patch("univention.config_registry.frontend.ConfigRegistry")
	assert ucrfe._ucr_from_opts({opt: True}) == ucr.return_value
	ucr.assert_called_once_with(write_registry=getattr(ucr, scope))


class TestHandler(object):

	CHANGES = {"new": "val", "foo": "foo", "bar": "bar", "baz": None}
	CHANGED = {
		"new": (None, "val"),
		"foo": (None, "foo"),
		"bar": ("NORMAL", "bar"),
		"baz": ("NORMAL", None),
	}
	VISIBLE = {
		"new": (None, "val"),
		"baz": ("NORMAL", None),
	}

	@pytest.fixture(autouse=True)
	def ucr1(self, ucrf, mocker):
		mocker.patch("univention.config_registry.frontend._ucr_from_opts", return_value=ucrf)
		return ucrf

	@pytest.fixture
	def handlers(self, mocker):
		h = mocker.patch("univention.config_registry.frontend.ConfigHandlers")
		h.return_value.update.return_value = set()
		return h

	@pytest.mark.parametrize("arg,changed,out,err", [
		("new", {}, "", "W: Missing value for config registry variable 'new'\n"),
		("=", {}, "Not setting \n", ""),
		("?", {}, "Not setting \n", ""),
		("new=1", {"new": (None, "1")}, "Create new\n", ""),
		("new?1", {"new": (None, "1")}, "Create new\n", ""),
		("new?=1", {"new": (None, "=1")}, "Create new\n", ""),
		("new=?1", {"new": (None, "?1")}, "Create new\n", ""),
		("foo=1", {"foo": (None, "1")}, "Create foo\n", ""),
		("foo?1", {"foo": (None, "1")}, "Create foo\n", ""),
		("bar=1", {"bar": ("NORMAL", "1")}, "Setting bar\n", ""),
		("bar?1", {}, "Not updating bar\n", ""),
		("baz=1", {"baz": ("NORMAL", "1")}, "Setting baz\n", ""),
		("baz?1", {}, "Not updating baz\n", ""),
	])
	def test_handler_set(self, arg, changed, out, err, run, mocker, capsys):
		ucrfe.handler_set([arg])

		run.assert_called_once_with(mocker.ANY, changed, mocker.ANY)
		assert capsys.readouterr() == (out, err)

	@pytest.mark.parametrize("arg,changed,out,err", [
		("foo", {}, "", "W: The config registry variable 'foo' does not exist\n"),
		("bar", {"bar": ("NORMAL", None)}, "Unsetting bar\n", ""),
		("baz", {"baz": ("NORMAL", None)}, "Unsetting baz\n", ""),
		("new", {}, "", "W: The config registry variable 'new' does not exist\n"),
	])
	def test_handler_unset(self, arg, changed, out, err, run, mocker, capsys):
		ucrfe.handler_unset([arg])

		run.assert_called_once_with(mocker.ANY, changed, mocker.ANY)
		assert capsys.readouterr() == (out, err)

	def test_ucr_update(self, ucrf, run, mocker):
		ucrfe.ucr_update(ucrf, self.CHANGES)
		run.assert_called_once_with(mocker.ANY, self.CHANGED)

	def test_run_changed(self, ucrf, mocker, capsys, handlers):
		replog = mocker.patch("univention.config_registry.frontend.replog")

		changed = ucrf.update(self.CHANGES)
		assert changed == self.CHANGED

		ucrfe._run_changed(ucrf, self.CHANGED, "%s %s")

		for (key, (old, new)) in self.VISIBLE.items():
			replog.assert_any_call(mocker.ANY, key, old, new)

		handlers.assert_called_once_with()
		handlers.return_value.load.assert_called_once_with()
		handlers.return_value.assert_called_once_with(list(self.VISIBLE), (mocker.ANY, self.VISIBLE))

	@pytest.mark.parametrize("key,val,visible", [
		("foo", "val", {}),
		("foo", None, {}),
		("bar", "val", {}),
		("bar", None, {}),
		("baz", "val", {"baz": ("NORMAL", "val")}),
		("baz", None, {"baz": ("NORMAL", None)}),
	])
	def test_run_changed_normal(self, key, val, visible, ucrf, mocker, handlers):
		changed = ucrf.update({key: val})
		ucrfe._run_changed(ucrf, changed)
		handlers.return_value.assert_called_once_with(list(visible), (mocker.ANY, visible))

	@pytest.mark.ucr_layer(ucrfe.ConfigRegistry.LDAP)
	@pytest.mark.parametrize("key,val,visible", [
		("foo", "val", {"foo": ("LDAP", "val")}),
		("foo", None, {"foo": ("LDAP", None)}),
		("bar", "val", {"bar": ("LDAP", "val")}),
		("bar", None, {"bar": ("LDAP", "NORMAL")}),
		("baz", "val", {"baz": ("NORMAL", "val")}),
		("baz", None, {}),
	])
	def test_run_changed_ldap(self, key, val, visible, ucrf, mocker, handlers):
		changed = ucrf.update({key: val})
		ucrfe._run_changed(ucrf, changed)
		handlers.return_value.assert_called_once_with(list(visible), (mocker.ANY, visible))

	@pytest.mark.ucr_layer(ucrfe.ConfigRegistry.FORCED)
	@pytest.mark.parametrize("key,val,visible", [
		("foo", "val", {"foo": ("LDAP", "val")}),
		("foo", None, {}),
		("bar", "val", {"bar": ("LDAP", "val")}),
		("bar", None, {}),
		("baz", "val", {"baz": ("NORMAL", "val")}),
		("baz", None, {}),
	])
	def test_run_changed_forced(self, key, val, visible, ucrf, mocker, handlers):
		changed = ucrf.update({key: val})
		ucrfe._run_changed(ucrf, changed)
		handlers.return_value.assert_called_once_with(list(visible), (mocker.ANY, visible))

	def test_handler_dump(self):
		assert set(ucrfe.handler_dump([])) == {"foo: LDAP", "bar: LDAP", "baz: NORMAL"}

	def test_handler_update(self, handlers, defaults):
		ucrfe.handler_update([])
		handlers.assert_called_once()
		defaults.assert_called_once()

	def test_handler_commit(self, handlers):
		ucrfe.handler_commit([])
		handlers.return_value.load.assert_called_once()
		handlers.return_value.commit.assert_called_once()

	def test_handler_register(self, handlers, defaults, mocker):
		ucrfe.handler_register(["INFO"])
		handlers.return_value.update.assert_called_once()
		defaults.assert_called_once()
		handlers.return_value.register.assert_called_once_with("INFO", mocker.ANY)

	def test_handler_unregister(self, handlers, defaults, mocker):
		ucrfe.handler_unregister(["INFO"])
		handlers.return_value.update.assert_called_once()
		handlers.return_value.unregister.assert_called_once_with("INFO", mocker.ANY)
		handlers.return_value.update_divert.assert_called_once()
		defaults.assert_called_once()

	def test_handler_filter(self, mocker):
		stdin = mocker.patch("sys.stdin")
		stdin.read.return_value = ""
		stdout = mocker.patch("sys.stdout")
		ucrfe.handler_filter([])
		if sys.version_info >= (3,):
			stdout.buffer.write.assert_called_once()
		else:
			stdout.write.assert_called_once()

	@pytest.mark.parametrize("arg,opts,output", [
		("foo", {}, ["foo: LDAP\n"]),
		("foo", {"key": True}, ["foo: LDAP\n"]),
		("foo", {"value": True}, []),
		("NORMAL", {"value": True}, ["baz: NORMAL\n"]),
		("NORMAL", {"brief": True, "value": True}, ["baz: NORMAL"]),
		("foo", {"all": True}, ["foo: LDAP\n"]),
		("foo", {"non-empty": True}, ["foo: LDAP\n"]),
		("foo", {"brief": True}, ["foo: LDAP"]),
		("foo", {"verbose": True}, ["foo: LDAP\n"]),
		("foo", {"brief": True, "key": True}, ["foo: LDAP"]),
		("fo{2}", {}, ["foo: LDAP\n"]),
		("^fo{2}$", {}, ["foo: LDAP\n"]),
		("^f[oO][oO]$", {}, ["foo: LDAP\n"]),
		("^ba[rz]$", {"brief": True, "key": True}, ["bar: LDAP", "baz: NORMAL"]),
	])
	def test_handler_search(self, arg, opts, output, rinfo):
		assert list(ucrfe.handler_search([arg], opts)) == output

	def test_handler_search_scope(self, ucr1, rinfo):
		ucr1["ucr/output/scope"] = "true"
		ucr1.save()
		assert list(ucrfe.handler_search(["foo"], {})) == ["foo: LDAP\n"]

	def test_handler_search_pattern(self, ucr1, rinfo):
		rinfo.return_value.describe_search_term.return_value = {"key/.*": rinfo.return_value.get_variable.return_value}
		assert list(ucrfe.handler_search(["key/.*"], {})) == ["key/.*: <empty>\n description\n"]

	@pytest.mark.parametrize("args,opts,error", [
		([], {"key": True, "value": True, "all": True}, "E: at most one out of [--key|--value|--all] may be set"),
		([r"?"], {}, "E: invalid regular expression: "),
		([], {"category": "INVALID"}, 'E: unknown category: "INVALID"'),
	])
	def test_handler_search_error(self, args, opts, error, capsys, rinfo):
		with pytest.raises(SystemExit) as exc_info:
			list(ucrfe.handler_search(args, opts))

		assert exc_info.value.code != 0

		out, err = capsys.readouterr()
		assert error in err

	@pytest.mark.parametrize("key,val", [
		("key", []),
		("foo", ["LDAP"]),
		("baz", ["NORMAL"]),
	])
	def test_handler_get(self, key, val):
		assert list(ucrfe.handler_get([key])) == val

	def test_handler_get_shell(self, monkeypatch, gopt):
		gopt(shell=True)
		assert list(ucrfe.handler_get(["baz"])) == ["baz: NORMAL"]

	def test_handler_info(self, rinfo):
		assert list(ucrfe.handler_info(["key"])) == ['key: <empty>\n description\n Categories: category\n Default: default\n']

	def test_handler_info_inknown(self, rinfo, capsys):
		rinfo.return_value.get_variable.return_value = None

		assert list(ucrfe.handler_info(["key"])) == []

		out, err = capsys.readouterr()
		assert err == 'W: Unknown key: "key"\n'


class TestInfo(object):

	def test_unset(self):
		with pytest.raises(ucrfe.UnknownKeyException):
			ucrfe.variable_info_string("key", None, None)

	@pytest.mark.parametrize("value", ["", None])
	def test_simple(self, value, vinfo):
		assert ucrfe.variable_info_string("key", value, vinfo) == ""

	@pytest.mark.parametrize("shell,out", [
		(True, "key: "),
		(False, "key: <empty>"),
	])
	def test_empty(self, shell, out, vinfo, gopt):
		gopt(shell=shell)
		assert ucrfe.variable_info_string("key", None, vinfo, details=ucrfe._SHOW_EMPTY) == out

	@pytest.mark.parametrize("scope,name", enumerate(ucrfe.SCOPE))
	def test_scope(self, scope, name, vinfo):
		assert ucrfe.variable_info_string("key", "value", None, scope=scope, details=ucrfe._SHOW_SCOPE) == "key (%s): value" % name

	def test_description(shell, vinfo, gopt):
		flags = ucrfe._SHOW_DESCRIPTION | ucrfe._SHOW_SCOPE | ucrfe._SHOW_CATEGORIES | ucrfe._SHOW_DEFAULT
		assert ucrfe.variable_info_string("key", "value", vinfo, details=flags) == (
			"key: value\n"
			" description\n"
			" Categories: category\n"
			" Default: default\n"
		)

	def test_no_description(shell, vinfo, gopt):
		del vinfo["description"]
		assert ucrfe.variable_info_string("key", "value", vinfo, details=ucrfe._SHOW_DESCRIPTION) == (
			"key: value\n"
			" no description available\n"
		)


def test_handler_version(capsys):
	with pytest.raises(SystemExit) as exc_info:
		ucrfe.handler_version([])

	assert exc_info.value.code == 0

	out, err = capsys.readouterr()
	assert out.startswith("univention-config-registry ")


def test_handler_help():
	out = StringIO()
	with pytest.raises(SystemExit) as exc_info:
		ucrfe.handler_help([], out=out)

	assert exc_info.value.code == 0
	assert "univention-config-registry" in out.getvalue()


def test_missing_parameter(capsys):
	with pytest.raises(SystemExit) as exc_info:
		ucrfe.missing_parameter("action")

	assert exc_info.value.code == 1

	out, err = capsys.readouterr()
	assert not out
	assert "[action]" in err


def test_get_config_registry_info():
	assert ucrfe._get_config_registry_info()


def test_registry_variable_default_values(ucrf, rinfo, run, mocker):
	ucrfe._register_variable_default_values(ucrf)
	run.assert_called_once_with(ucrf, {"key": (None, "default")}, mocker.ANY)


class TestMain(object):

	@pytest.fixture(autouse=True)
	def reset(self):
		"""Reset frontend global state."""
		reload(ucrfe)

	@pytest.fixture
	def handlers(self, mocker, reset):
		"""Mock frontend handlers."""
		h = {
			key: (mocker.patch("univention.config_registry.frontend.%s" % hdlr.__name__), args)
			for (key, (hdlr, args)) in ucrfe.HANDLERS.items()
		}
		mocker.patch.dict(ucrfe.HANDLERS, h)
		return h

	@pytest.mark.parametrize("args,error", [
		("unknown", 'E: unknown action "unknown", see --help'),
		("set", "E: too few arguments for command [set]"),
		("unset", "E: too few arguments for command [unset]"),
		("register", "E: too few arguments for command [register]"),
		("unregister", "E: too few arguments for command [unregister]"),
		("get", "E: too few arguments for command [get]"),
		("info", "E: too few arguments for command [info]"),
		("info --invalid", "E: invalid option --invalid for command info"),
		("--shell", "E: missing action, see --help"),
		("--shell info", "E: invalid option --shell for command info"),
		("--unknown", "E: unknown option --unknown"),
		("search --category", "E: option --category for command search expects an argument"),
	])
	def test_error(self, args, error, capsys):
		with pytest.raises(SystemExit) as exc_info:
			ucrfe.main(args.split())

		assert exc_info.value.code != 0

		out, err = capsys.readouterr()
		assert error in err

	@pytest.mark.parametrize("args", [
		"",
		"-h",
		"-?",
		"--help",
		"-v",
		"--version",
	])
	def test_exit(self, args):
		with pytest.raises(SystemExit) as exc_info:
			ucrfe.main(args.split() if args else [])

		assert exc_info.value.code == 0

	@pytest.mark.parametrize("args", [
		"set KEY",
		"set --force KEY",
		"set --forced KEY",
		"set --ldap-policy KEY",
		"set --schedule KEY",
		"unset KEY",
		"unset --force KEY",
		"unset --forced KEY",
		"unset --ldap-policy KEY",
		"unset --schedule KEY",
		"dump",
		"--keys-only dump",
		"--shell dump",
		"--sort dump",
		"commit",
		"register FILE",
		"unregister FILE",
		"filter",
		"filter --encode-utf8",
		"filter --disallow-execution",
		"search",
		"search KEY",
		"search --key",
		"search --value",
		"search --all",
		"search --brief",
		"search --category CAT",
		"search --non-empty",
		"search --verbose",
		"--keys-only search",
		"--shell search",
		"--sort search",
		"shell",
		"shell KEY",
		"shell KEY --KEY",
		"get KEY",
		"--shell get KEY",
		"info KEY",
		"--sort info KEY",
	])
	def test_main(self, args, handlers):
		ucrfe.main(args.split())

	def test_output_none(self, handlers):
		handlers["get"][0].return_value = None
		ucrfe.main(["get", "KEY"])

	def test_output_lines(self, handlers):
		handlers["get"][0].return_value = ["out"]
		ucrfe.main(["get", "KEY"])

	def test_raise_exit(self, handlers):
		handlers["get"][0].side_effect = TypeError()
		with pytest.raises(SystemExit):
			ucrfe.main(["get", "KEY"])

	def test_raise_error(self, handlers):
		handlers["get"][0].side_effect = TypeError()
		with pytest.raises(TypeError):
			ucrfe.main(["--debug", "get", "KEY"])
