#!/usr/bin/python3
"""Unit test for univention.config_registry.backend."""
# vim:set fileencoding=utf-8:
# pylint: disable-msg=C0103,E0611,R0904
import sys
from argparse import Namespace
from os import stat_result
from os.path import dirname
try:
	from StringIO import StringIO
except ImportError:
	from io import StringIO  # type: ignore

import pytest

import univention.config_registry.handler as ucrh


@pytest.mark.parametrize("tmpl,out", [
	("", ""),
	("txt", "txt"),
	("@%@foo@%@", "LDAP"),
	("@%@bar@%@", "LDAP"),
	("@%@baz@%@", "NORMAL"),
	("@%@other@%@", ""),
	("1@%@baz@%@2@%@baz@%@3", "1NORMAL2NORMAL3"),
])
def test_filter_var(tmpl, out, ucrf):
	assert ucrh.run_filter(tmpl, ucrf) == out.encode('ASCII')


def test_filter_script(mocker, ucrf):
	Popen = mocker.patch("subprocess.Popen")
	Popen.return_value.communicate.return_value = (b"42", b"")
	assert ucrh.run_filter("@!@print(42)@!@", ucrf) == b"42"
	Popen.assert_called_once()
	Popen.return_value.communicate.assert_called_once()


@pytest.mark.parametrize("tmpl,line", [
	("@%@BCWARNING=// @%@", "// "),
	("@%@UCRWARNING=# @%@", "# "),
	("@%@UCRWARNING_ASCII=;@%@", ";"),
])
def test_filter_warning(tmpl, line, ucrf):
	assert line in ucrh.run_filter(tmpl, ucrf, {"01head", "02tail"}).decode('UTF-8')


def test_run_script(mocker):
	Popen = mocker.patch("subprocess.Popen")

	SCRIPT, ARG = "script", "generate"
	changes = {"key": ("old", "new")}

	ucrh.run_script(SCRIPT, ARG, changes)
	Popen.assert_called_once_with("script generate", shell=True, stdin=ucrh.subprocess.PIPE, close_fds=True)
	Popen.return_value.communicate.assert_called_once_with(b"key@%@old@%@new\n")


@pytest.mark.parametrize("funcname", [
	"handler",
	"preinst",
	"postinst",
])
def test_run_module(funcname, mocker):
	mymodule = mocker.MagicMock()
	mocker.patch.dict(sys.modules, {"pytest": mymodule})

	ucr = {"key": "new"}
	changes = {"key": ("old", "new")}

	ucrh.run_module("pytest", funcname, ucr, changes)

	func = getattr(mymodule, funcname)
	func.assert_called_once_with(ucr, changes)


@pytest.mark.parametrize("prefix,srcfiles,expected", [
	pytest.param("# ", set(), "# Warning: ", id="#"),
	pytest.param(";", set(), ";Warnung: ", id=";"),
	pytest.param("// ", {"tmpl"}, "// \ttmpl\n", id="//"),
	pytest.param(";", {u"Dom\u00e4ne"}, u";\tDom\u00e4ne\n", id="unicode"),
])
def test_warning_string(prefix, srcfiles, expected):
	assert expected in ucrh.warning_string(prefix, srcfiles=srcfiles)


def test_ConfigHandler():
	with pytest.raises(NotImplementedError):
		ucrh.ConfigHandler()(({}, {}))


class TestConfigHandlerDiverting(object):

	@pytest.fixture
	def hdivert(self):
		return ucrh.ConfigHandlerDiverting("/divert")

	def mstats(self, mocker):
		# a fixture would be insteded to early!
		STAT = stat_result([mocker.MagicMock()] * 10)
		m_stat = mocker.patch("os.stat", return_value=STAT)
		m_chmod = mocker.patch("os.chmod")
		m_chown = mocker.patch("os.chown")
		return Namespace(
			STAT=STAT,
			stat=m_stat,
			chmod=m_chmod,
			chown=m_chown,
		)

	def test_comparison(self, hdivert):
		h2 = ucrh.ConfigHandlerDiverting("divert2")
		assert hash(hdivert) == hash(hdivert)
		assert hash(hdivert) != hash(h2)
		assert hdivert == hdivert
		assert hdivert != h2

	def test_perms_none(self, hdivert, mocker):
		mstats = self.mstats(mocker)
		hdivert._set_perm(None)
		assert not mstats.chmod.called
		assert not mstats.chown.called

	def test_perms_stat(self, hdivert, mocker):
		mstats = self.mstats(mocker)
		hdivert._set_perm(mstats.STAT)
		mstats.chmod.assert_called_once_with("/divert", mstats.STAT.st_mode)

	def test_perms_target(self, hdivert, mocker):
		mstats = self.mstats(mocker)
		hdivert._set_perm(None, "/target")
		mstats.stat.assert_called_once_with("/divert")
		mstats.chmod.assert_called_once_with("/target", mstats.STAT.st_mode)
		mstats.chown.assert_called_once_with("/target", mstats.STAT.st_uid, mstats.STAT.st_gid)

	def test_perms_mode(self, hdivert, mocker):
		mstats = self.mstats(mocker)
		hdivert.mode = 0o644
		hdivert._set_perm(None)
		mstats.chmod.assert_called_once_with("/divert", 0o644)

	def test_perms_user_only(self, hdivert, mocker):
		mstats = self.mstats(mocker)
		hdivert.user = 1
		hdivert._set_perm(None)
		mstats.chown.assert_called_once_with("/divert", 1, 0)

	def test_perms_group_only(self, hdivert, mocker):
		mstats = self.mstats(mocker)
		hdivert.group = 1
		hdivert._set_perm(None)
		mstats.chown.assert_called_once_with("/divert", 0, 1)

	def test_perms_user_group(self, hdivert, mocker):
		mstats = self.mstats(mocker)
		hdivert.user = 1
		hdivert.group = 2
		hdivert._set_perm(None)
		mstats.chown.assert_called_once_with("/divert", 1, 2)

	def test_call_silent(self, hdivert, capfd):
		ret = hdivert._call_silent(sys.executable, "-c", "import sys;sys.stdout.write('1');sys.stderr.write('2')")
		out, err = capfd.readouterr()
		assert ret == 0
		assert out == ""
		assert err == ""

	def test_divert(self, hdivert, mocker):
		mocker.patch("os.unlink")
		mocker.patch("os.path.exists").return_value = False
		m_call = mocker.patch("subprocess.call")

		assert not hdivert.need_divert()

		hdivert.install_divert()
		assert m_call.call_args[0][0] == ("dpkg-divert", "--quiet", "--rename", "--local", "--divert", "/divert.debian", "--add", "/divert")

		m_call.reset_mock()
		hdivert.uninstall_divert()
		assert m_call.call_args[0][0] == ("dpkg-divert", "--quiet", "--rename", "--local", "--divert", "/divert.debian", "--remove", "/divert")

	def test_tmpfile(self):
		PATH = "/path/to/divert"
		h = ucrh.ConfigHandlerDiverting(PATH)
		tmp = h._temp_file_name()
		assert tmp != PATH
		assert dirname(tmp) == dirname(PATH)


def test_ConfigHandlerMultifile(mocker):
	h = ucrh.ConfigHandlerMultifile("multifile.dummy", "multifile.to")
	assert not h.need_divert()

	h.add_subfiles([
		("subfile1", {"var1", "var2"}),
		("subfile2", {"var1", "var3"}),
	])
	assert h.need_divert()

	h.remove_subfile("")
	h.remove_subfile("subfile2")

	return  # TODO

	mocker.patch("univention.config_registry.handler.run_module")
	mocker.patch("univention.config_registry.handler.run_script")
	mocker.patch("os.makedirs")
	mocker.patch("os.stat")
	mocker.patch("os.rename")
	mocker.patch("os.unlink")
	ucr, changes = {}, {}
	h((ucr, changes))


def test_ConfigHandlerFile(mocker):
	h = ucrh.ConfigHandlerFile("file.from", "file.to")
	assert h.need_divert()

	return  # TODO

	mocker.patch("univention.config_registry.handler.run_module")
	mocker.patch("univention.config_registry.handler.run_script")
	mocker.patch("os.makedirs")
	mocker.patch("os.stat")
	mocker.patch("os.rename")
	mocker.patch("os.unlink")
	ucr, changes = {}, {}
	h((ucr, changes))


def test_ConfigHandlerScipt(mocker):
	h1 = ucrh.ConfigHandlerScript("script1")
	h2 = ucrh.ConfigHandlerScript("script2")
	assert hash(h1) == hash(h1)
	assert hash(h1) != hash(h2)
	assert h1 == h1
	assert h1 != h2

	mocker.patch("os.path.isfile").return_value = True
	run_script = mocker.patch("univention.config_registry.handler.run_script")
	ucr, changes = {}, {}
	h1((ucr, changes))
	run_script.assert_called_once_with("script1", "generate", changes)


def test_ConfigHandlerModule(mocker):
	h1 = ucrh.ConfigHandlerModule("module1")
	h2 = ucrh.ConfigHandlerModule("module2")
	assert hash(h1) == hash(h1)
	assert hash(h1) != hash(h2)
	assert h1 == h1
	assert h1 != h2

	run_module = mocker.patch("univention.config_registry.handler.run_module")
	ucr, changes = {}, {}
	h1((ucr, changes))
	run_module.assert_called_once_with("module1", "handler", ucr, changes)


@pytest.mark.parametrize("tmpl,vars", [
	("", set()),
	("txt", set()),
	("@%@foo@%@", {"foo"}),
	("@%@foo@%@ @%@foo@%@", {"foo"}),
	("@%@foo@%@@%@bar@%@", {"foo", "bar"}),
])
def test_grep_variables(tmpl, vars):
	assert ucrh.grep_variables(tmpl) == vars


@pytest.fixture
def handler0(mocker):
	"""
	Return empty dummy handler.
	"""
	return mocker.MagicMock(preinst=None, postinst=None, user=None, group=None, mode=None)


@pytest.fixture
def handlers(tmpcache):
	"""
	Return :py:class:`ConfigHandlers` instance with private cache directory.
	"""
	handlers = ucrh.ConfigHandlers()
	return handlers


class TestConfigHandlers():
	COMMON = {
		"Preinst": ["preinst"],
		"Postinst": ["postinst"],
		"User": ["root"],
		"Group": ["root"],
		"Mode": ["0644"],
	}
	FILE = {
		"Type": ["file"],
		"File": ["file"],
	}
	SCRIPT = {
		"Type": ["script"],
		"Script": ["script"],
		"Variables": ["var1"],
	}
	MODULE = {
		"Type": ["module"],
		"Module": ["module"],
		"Variables": ["var1"],
	}
	MULTIFILE = {
		"Type": ["multifile"],
		"Multifile": ["multifile"],
	}
	SUBFILE = {
		"Type": ["subfile"],
		"Multifile": ["multifile"],
		"Subfile": ["subfile"],
	}

	def test_common_unset(self, handlers, handler0):
		entry = {}
		handlers._parse_common_file_handler(handler0, entry)
		assert handler0.preinst is None
		assert handler0.postinst is None
		assert handler0.user is None
		assert handler0.group is None
		assert handler0.mode is None

	def test_common_given(self, handlers, handler0):
		handlers._parse_common_file_handler(handler0, self.COMMON)
		assert handler0.preinst == "preinst"
		assert handler0.postinst == "postinst"
		assert handler0.user == 0
		assert handler0.group == 0
		assert handler0.mode == 0o644

	def test_common_invalid(self, handlers, handler0):
		entry = {
			"User": [" invalid"],
			"Group": [" invalid"],
			"Mode": ["999"],
		}
		handlers._parse_common_file_handler(handler0, entry)
		assert handler0.user is None
		assert handler0.group is None
		assert handler0.mode is None

	def test_get_file(self, handlers):
		handler = handlers._get_handler_file(self.FILE)
		assert isinstance(handler, ucrh.ConfigHandlerFile)

	def test_get_script(self, handlers):
		handler = handlers._get_handler_script(self.SCRIPT)
		assert isinstance(handler, ucrh.ConfigHandlerScript)

	def test_get_module(self, handlers):
		handler = handlers._get_handler_module(self.MODULE)
		assert isinstance(handler, ucrh.ConfigHandlerModule)

	def test_get_multifile(self, handlers):
		handler = handlers._get_handler_multifile(self.MULTIFILE)
		assert isinstance(handler, ucrh.ConfigHandlerMultifile)

	def test_get_subfile(self, handlers):
		handler = handlers._get_handler_subfile(self.SUBFILE)
		assert handler is None

	@pytest.mark.parametrize("entry,typ", [
		(FILE, ucrh.ConfigHandlerFile),
		(SCRIPT, ucrh.ConfigHandlerScript),
		(MODULE, ucrh.ConfigHandlerModule),
		(MULTIFILE, ucrh.ConfigHandlerMultifile),
		(SUBFILE, None),
		({}, None),
		({"Type": ["invalid"]}, None),
		({"Type": ["file"]}, None),
		({"Type": ["script"]}, None),
		({"Type": ["module"]}, None),
		({"Type": ["multifile"]}, None),
		({"Type": ["subfile"]}, None),
	])
	def test_get_handler(self, entry, typ, handlers):
		handler = handlers.get_handler(entry)
		if typ is None:
			assert handler is None
		else:
			assert isinstance(handler, typ)

	@pytest.mark.parametrize("data,version", [
		("", 0),
		("invalid", 0),
		("univention-config cache, version 1\n", 1),
		("univention-config cache, version 2\n", 2),
		("univention-config cache, version 3\n", 3),
	])
	def test_get_cache_version(self, data, version):
		cache = StringIO(data)
		assert version == ucrh.ConfigHandlers._get_cache_version(cache)

	def test_cache(self, handlers):
		handlers._handlers = {"var": set()}
		handlers._subfiles = {"mfile": []}
		handlers._multifiles = {"mfile": None}
		handlers._save_cache()

		h2 = ucrh.ConfigHandlers()
		h2.load()
		if sys.version_info >= (3,):
			pytest.xfail("BUG")
		assert h2._handlers == handlers._handlers
		assert h2._subfiles == handlers._subfiles
		assert h2._multifiles == handlers._multifiles

	@pytest.mark.skip
	def test_update(self, handlers):
		pass

	@pytest.mark.skip
	def test_update_divert(self, handlers):
		pass

	@pytest.mark.skip
	def test_register(self, handlers):
		pass

	@pytest.mark.skip
	def test_unregister(self, handlers):
		pass

	@pytest.mark.skip
	def test_call(self, handlers):
		pass

	@pytest.mark.skip
	def test_commit(self, handlers):
		pass

	@pytest.mark.skip
	def test_call_handler(self, handlers):
		pass
