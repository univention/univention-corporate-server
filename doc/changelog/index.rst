.. _relnotes-changelog:

#########################################################
Changelog for Univention Corporate Server (UCS) |release|
#########################################################

.. _changelog-general:

*******
General
*******

* The server password change script has been improved to track and log the
  execution, allowing a better understanding of failed operations
  (:uv:bug:`54273`).

* The package :program:`univention-keycloak` has been added as a dependency to the
  :program:`univention-server-common` package. It contains a CLI tool used by the
  Univention Keycloak app (:uv:bug:`55383`).

* The package :program:`univention-support-info` is now by default installed on every
  system role (:uv:bug:`55485`).

* The scripts :file:`server_password_change/univention-admin-diary` has been updated to
  generate more useful debug information (:uv:bug:`54273`).

* Instead of an exception now a clear error message is displayed in case the
  admin diary frontend is installed on a different system than the admin diary
  server and the database connection is not correctly configured
  (:uv:bug:`49016`).

* Reading records from database is optimized to use less RAM and CPU
  (:uv:bug:`51902`).

* Some source code has been refactored regarding binding of loop variables to function calls
  (:uv:bug:`55598`).

.. _security:

* All security updates issued for UCS 5.0-2 are included:

  * :program:`zlib` (:uv:cve:`2022-37434`) (:uv:bug:`55198`)

  * :program:`xorg-server` (:uv:cve:`2022-2319`, :uv:cve:`2022-2320`,
    :uv:cve:`2022-3550`, :uv:cve:`2022-3551`, :uv:cve:`2022-4283`,
    :uv:cve:`2022-46340`, :uv:cve:`2022-46341`, :uv:cve:`2022-46342`,
    :uv:cve:`2022-46343`, :uv:cve:`2022-46344`) (:uv:bug:`55072`,
    :uv:bug:`55416`, :uv:bug:`55537`)

  * :program:`vim` (:uv:cve:`2021-3927`, :uv:cve:`2021-3928`,
    :uv:cve:`2021-3974`, :uv:cve:`2021-3984`, :uv:cve:`2021-4019`,
    :uv:cve:`2021-4069`, :uv:cve:`2021-4192`, :uv:cve:`2021-4193`,
    :uv:cve:`2022-0213`, :uv:cve:`2022-0261`, :uv:cve:`2022-0318`,
    :uv:cve:`2022-0319`, :uv:cve:`2022-0351`, :uv:cve:`2022-0359`,
    :uv:cve:`2022-0361`, :uv:cve:`2022-0368`, :uv:cve:`2022-0392`,
    :uv:cve:`2022-0408`, :uv:cve:`2022-0413`, :uv:cve:`2022-0417`,
    :uv:cve:`2022-0443`, :uv:cve:`2022-0554`, :uv:cve:`2022-0572`,
    :uv:cve:`2022-0629`, :uv:cve:`2022-0685`, :uv:cve:`2022-0696`,
    :uv:cve:`2022-0714`, :uv:cve:`2022-0729`, :uv:cve:`2022-0943`,
    :uv:cve:`2022-1154`, :uv:cve:`2022-1616`, :uv:cve:`2022-1619`,
    :uv:cve:`2022-1621`, :uv:cve:`2022-1720`, :uv:cve:`2022-1785`,
    :uv:cve:`2022-1851`, :uv:cve:`2022-1897`, :uv:cve:`2022-1898`,
    :uv:cve:`2022-1942`, :uv:cve:`2022-1968`, :uv:cve:`2022-2000`,
    :uv:cve:`2022-2129`, :uv:cve:`2022-2285`, :uv:cve:`2022-2304`,
    :uv:cve:`2022-2598`, :uv:cve:`2022-2946`, :uv:cve:`2022-3099`,
    :uv:cve:`2022-3134`, :uv:cve:`2022-3234`, :uv:cve:`2022-3235`,
    :uv:cve:`2022-3256`, :uv:cve:`2022-3324`, :uv:cve:`2022-3352`,
    :uv:cve:`2022-3705`) (:uv:bug:`55417`, :uv:bug:`55465`)

  * :program:`unzip` (:uv:cve:`2022-0529`, :uv:cve:`2022-0530`)
    (:uv:bug:`55219`)

  * :program:`tiff` (:uv:cve:`2022-1354`, :uv:cve:`2022-1355`,
    :uv:cve:`2022-2056`, :uv:cve:`2022-2057`, :uv:cve:`2022-2058`,
    :uv:cve:`2022-2867`, :uv:cve:`2022-2868`, :uv:cve:`2022-2869`,
    :uv:cve:`2022-34526`, :uv:cve:`2022-3570`, :uv:cve:`2022-3597`,
    :uv:cve:`2022-3598`, :uv:cve:`2022-3599`, :uv:cve:`2022-3626`,
    :uv:cve:`2022-3627`, :uv:cve:`2022-3970`, :uv:cve:`2022-48281`)
    (:uv:bug:`55589`, :uv:bug:`55624`)

  * :program:`sudo` (:uv:cve:`2021-23239`, :uv:cve:`2023-22809`)
    (:uv:bug:`55397`, :uv:bug:`55586`)

  * :program:`squid` (:uv:cve:`2022-41317`, :uv:cve:`2022-41318`)
    (:uv:bug:`55271`)

  * :program:`sqlite3` (:uv:cve:`2020-35525`, :uv:cve:`2020-35527`,
    :uv:cve:`2021-20223`) (:uv:bug:`55207`)

  * :program:`samba` (:uv:cve:`2022-2031`, :uv:cve:`2022-32742`,
    :uv:cve:`2022-32744`, :uv:cve:`2022-32745`, :uv:cve:`2022-32746`,
    :uv:cve:`2022-3437`, :uv:cve:`2022-37966`, :uv:cve:`2022-37967`,
    :uv:cve:`2022-38023`, :uv:cve:`2022-42898`) (:uv:bug:`54994`,
    :uv:bug:`55275`, :uv:bug:`55406`, :uv:bug:`55486`,
    :uv:bug:`55511`)

  * :program:`qemu` () (:uv:bug:`55167`)

  * :program:`python3.7` (:uv:cve:`2022-37454`) (:uv:bug:`55370`)

  * :program:`postgresql-11` (:uv:cve:`2022-2625`) (:uv:bug:`55093`)

  * :program:`poppler` (:uv:cve:`2018-18897`, :uv:cve:`2018-19058`,
    :uv:cve:`2018-20650`, :uv:cve:`2019-14494`, :uv:cve:`2019-9903`,
    :uv:cve:`2019-9959`, :uv:cve:`2020-27778`, :uv:cve:`2022-27337`,
    :uv:cve:`2022-38784`) (:uv:bug:`55220`)

  * :program:`pixman` (:uv:cve:`2022-44638`) (:uv:bug:`55396`)

  * :program:`php7.3` (:uv:cve:`2021-21707`, :uv:cve:`2022-31625`,
    :uv:cve:`2022-31626`, :uv:cve:`2022-31628`, :uv:cve:`2022-31629`,
    :uv:cve:`2022-37454`) (:uv:bug:`55503`)

  * :program:`paramiko` (:uv:cve:`2022-24302`) (:uv:bug:`55199`)

  * :program:`ntfs-3g` (:uv:cve:`2022-40284`) (:uv:bug:`55443`)

  * :program:`net-snmp` (:uv:cve:`2022-24805`, :uv:cve:`2022-24806`,
    :uv:cve:`2022-24807`, :uv:cve:`2022-24808`, :uv:cve:`2022-24809`,
    :uv:cve:`2022-24810`, :uv:cve:`2022-44792`, :uv:cve:`2022-44793`)
    (:uv:bug:`55152`, :uv:bug:`55572`)

  * :program:`ncurses` (:uv:cve:`2022-29458`) (:uv:bug:`55369`)

  * :program:`multipath-tools` (:uv:cve:`2022-41973`,
    :uv:cve:`2022-41974`) (:uv:bug:`55539`)

  * :program:`mokutil` (:uv:cve:`2021-3695`, :uv:cve:`2021-3696`,
    :uv:cve:`2021-3697`, :uv:cve:`2022-28733`, :uv:cve:`2022-28734`,
    :uv:cve:`2022-28735`, :uv:cve:`2022-28736`) (:uv:bug:`55191`)

  * :program:`mod-wsgi` (:uv:cve:`2022-2255`) (:uv:bug:`55206`)

  * :program:`mariadb-10.3` (:uv:cve:`2021-46669`,
    :uv:cve:`2022-21427`, :uv:cve:`2022-27376`, :uv:cve:`2022-27377`,
    :uv:cve:`2022-27378`, :uv:cve:`2022-27379`, :uv:cve:`2022-27380`,
    :uv:cve:`2022-27381`, :uv:cve:`2022-27383`, :uv:cve:`2022-27384`,
    :uv:cve:`2022-27386`, :uv:cve:`2022-27387`, :uv:cve:`2022-27445`,
    :uv:cve:`2022-27447`, :uv:cve:`2022-27448`, :uv:cve:`2022-27449`,
    :uv:cve:`2022-27452`, :uv:cve:`2022-27456`, :uv:cve:`2022-27458`,
    :uv:cve:`2022-32083`, :uv:cve:`2022-32084`, :uv:cve:`2022-32085`,
    :uv:cve:`2022-32087`, :uv:cve:`2022-32088`, :uv:cve:`2022-32091`)
    (:uv:bug:`55210`)

  * :program:`mako` (:uv:cve:`2022-40023`) (:uv:bug:`55223`)

  * :program:`linux-signed-amd64` (:uv:cve:`2021-33655`,
    :uv:cve:`2021-33656`, :uv:cve:`2021-4159`, :uv:cve:`2021-4197`,
    :uv:cve:`2022-0494`, :uv:cve:`2022-0812`, :uv:cve:`2022-0854`,
    :uv:cve:`2022-1011`, :uv:cve:`2022-1012`, :uv:cve:`2022-1016`,
    :uv:cve:`2022-1048`, :uv:cve:`2022-1184`, :uv:cve:`2022-1195`,
    :uv:cve:`2022-1198`, :uv:cve:`2022-1199`, :uv:cve:`2022-1204`,
    :uv:cve:`2022-1205`, :uv:cve:`2022-1353`, :uv:cve:`2022-1419`,
    :uv:cve:`2022-1462`, :uv:cve:`2022-1516`, :uv:cve:`2022-1652`,
    :uv:cve:`2022-1679`, :uv:cve:`2022-1729`, :uv:cve:`2022-1734`,
    :uv:cve:`2022-1974`, :uv:cve:`2022-1975`, :uv:cve:`2022-20369`,
    :uv:cve:`2022-21123`, :uv:cve:`2022-21125`, :uv:cve:`2022-21166`,
    :uv:cve:`2022-2153`, :uv:cve:`2022-2318`, :uv:cve:`2022-23960`,
    :uv:cve:`2022-2586`, :uv:cve:`2022-2588`, :uv:cve:`2022-26365`,
    :uv:cve:`2022-26373`, :uv:cve:`2022-26490`, :uv:cve:`2022-2663`,
    :uv:cve:`2022-27666`, :uv:cve:`2022-28356`, :uv:cve:`2022-28388`,
    :uv:cve:`2022-28389`, :uv:cve:`2022-28390`, :uv:cve:`2022-29581`,
    :uv:cve:`2022-2978`, :uv:cve:`2022-29901`, :uv:cve:`2022-3028`,
    :uv:cve:`2022-30594`, :uv:cve:`2022-32250`, :uv:cve:`2022-32296`,
    :uv:cve:`2022-32981`, :uv:cve:`2022-33740`, :uv:cve:`2022-33741`,
    :uv:cve:`2022-33742`, :uv:cve:`2022-33744`, :uv:cve:`2022-33981`,
    :uv:cve:`2022-3521`, :uv:cve:`2022-3524`, :uv:cve:`2022-3564`,
    :uv:cve:`2022-3565`, :uv:cve:`2022-3594`, :uv:cve:`2022-3621`,
    :uv:cve:`2022-3628`, :uv:cve:`2022-3640`, :uv:cve:`2022-3643`,
    :uv:cve:`2022-3646`, :uv:cve:`2022-3649`, :uv:cve:`2022-36879`,
    :uv:cve:`2022-36946`, :uv:cve:`2022-39188`, :uv:cve:`2022-40307`,
    :uv:cve:`2022-40768`, :uv:cve:`2022-41849`, :uv:cve:`2022-41850`,
    :uv:cve:`2022-42328`, :uv:cve:`2022-42329`, :uv:cve:`2022-42895`,
    :uv:cve:`2022-42896`, :uv:cve:`2022-43750`, :uv:cve:`2022-4378`)
    (:uv:bug:`54958`, :uv:bug:`55238`, :uv:bug:`55540`)

  * :program:`linux-latest` (:uv:cve:`2021-33655`,
    :uv:cve:`2021-33656`, :uv:cve:`2021-4159`, :uv:cve:`2021-4197`,
    :uv:cve:`2022-0494`, :uv:cve:`2022-0812`, :uv:cve:`2022-0854`,
    :uv:cve:`2022-1011`, :uv:cve:`2022-1012`, :uv:cve:`2022-1016`,
    :uv:cve:`2022-1048`, :uv:cve:`2022-1184`, :uv:cve:`2022-1195`,
    :uv:cve:`2022-1198`, :uv:cve:`2022-1199`, :uv:cve:`2022-1204`,
    :uv:cve:`2022-1205`, :uv:cve:`2022-1353`, :uv:cve:`2022-1419`,
    :uv:cve:`2022-1462`, :uv:cve:`2022-1516`, :uv:cve:`2022-1652`,
    :uv:cve:`2022-1679`, :uv:cve:`2022-1729`, :uv:cve:`2022-1734`,
    :uv:cve:`2022-1974`, :uv:cve:`2022-1975`, :uv:cve:`2022-20369`,
    :uv:cve:`2022-21123`, :uv:cve:`2022-21125`, :uv:cve:`2022-21166`,
    :uv:cve:`2022-2153`, :uv:cve:`2022-2318`, :uv:cve:`2022-23960`,
    :uv:cve:`2022-2586`, :uv:cve:`2022-2588`, :uv:cve:`2022-26365`,
    :uv:cve:`2022-26373`, :uv:cve:`2022-26490`, :uv:cve:`2022-2663`,
    :uv:cve:`2022-27666`, :uv:cve:`2022-28356`, :uv:cve:`2022-28388`,
    :uv:cve:`2022-28389`, :uv:cve:`2022-28390`, :uv:cve:`2022-29581`,
    :uv:cve:`2022-2978`, :uv:cve:`2022-29901`, :uv:cve:`2022-3028`,
    :uv:cve:`2022-30594`, :uv:cve:`2022-32250`, :uv:cve:`2022-32296`,
    :uv:cve:`2022-32981`, :uv:cve:`2022-33740`, :uv:cve:`2022-33741`,
    :uv:cve:`2022-33742`, :uv:cve:`2022-33744`, :uv:cve:`2022-33981`,
    :uv:cve:`2022-3521`, :uv:cve:`2022-3524`, :uv:cve:`2022-3564`,
    :uv:cve:`2022-3565`, :uv:cve:`2022-3594`, :uv:cve:`2022-3621`,
    :uv:cve:`2022-3628`, :uv:cve:`2022-3640`, :uv:cve:`2022-3643`,
    :uv:cve:`2022-3646`, :uv:cve:`2022-3649`, :uv:cve:`2022-36879`,
    :uv:cve:`2022-36946`, :uv:cve:`2022-39188`, :uv:cve:`2022-40307`,
    :uv:cve:`2022-40768`, :uv:cve:`2022-41849`, :uv:cve:`2022-41850`,
    :uv:cve:`2022-42328`, :uv:cve:`2022-42329`, :uv:cve:`2022-42895`,
    :uv:cve:`2022-42896`, :uv:cve:`2022-43750`, :uv:cve:`2022-4378`)
    (:uv:bug:`54958`, :uv:bug:`55238`, :uv:bug:`55540`)

  * :program:`linux` (:uv:cve:`2021-33655`, :uv:cve:`2021-33656`,
    :uv:cve:`2021-4159`, :uv:cve:`2021-4197`, :uv:cve:`2022-0494`,
    :uv:cve:`2022-0812`, :uv:cve:`2022-0854`, :uv:cve:`2022-1011`,
    :uv:cve:`2022-1012`, :uv:cve:`2022-1016`, :uv:cve:`2022-1048`,
    :uv:cve:`2022-1184`, :uv:cve:`2022-1195`, :uv:cve:`2022-1198`,
    :uv:cve:`2022-1199`, :uv:cve:`2022-1204`, :uv:cve:`2022-1205`,
    :uv:cve:`2022-1353`, :uv:cve:`2022-1419`, :uv:cve:`2022-1462`,
    :uv:cve:`2022-1516`, :uv:cve:`2022-1652`, :uv:cve:`2022-1679`,
    :uv:cve:`2022-1729`, :uv:cve:`2022-1734`, :uv:cve:`2022-1974`,
    :uv:cve:`2022-1975`, :uv:cve:`2022-20369`, :uv:cve:`2022-21123`,
    :uv:cve:`2022-21125`, :uv:cve:`2022-21166`, :uv:cve:`2022-2153`,
    :uv:cve:`2022-2318`, :uv:cve:`2022-23960`, :uv:cve:`2022-2586`,
    :uv:cve:`2022-2588`, :uv:cve:`2022-26365`, :uv:cve:`2022-26373`,
    :uv:cve:`2022-26490`, :uv:cve:`2022-2663`, :uv:cve:`2022-27666`,
    :uv:cve:`2022-28356`, :uv:cve:`2022-28388`, :uv:cve:`2022-28389`,
    :uv:cve:`2022-28390`, :uv:cve:`2022-29581`, :uv:cve:`2022-2978`,
    :uv:cve:`2022-29901`, :uv:cve:`2022-3028`, :uv:cve:`2022-30594`,
    :uv:cve:`2022-32250`, :uv:cve:`2022-32296`, :uv:cve:`2022-32981`,
    :uv:cve:`2022-33740`, :uv:cve:`2022-33741`, :uv:cve:`2022-33742`,
    :uv:cve:`2022-33744`, :uv:cve:`2022-33981`, :uv:cve:`2022-3521`,
    :uv:cve:`2022-3524`, :uv:cve:`2022-3564`, :uv:cve:`2022-3565`,
    :uv:cve:`2022-3594`, :uv:cve:`2022-3621`, :uv:cve:`2022-3628`,
    :uv:cve:`2022-3640`, :uv:cve:`2022-3643`, :uv:cve:`2022-3646`,
    :uv:cve:`2022-3649`, :uv:cve:`2022-36879`, :uv:cve:`2022-36946`,
    :uv:cve:`2022-39188`, :uv:cve:`2022-40307`, :uv:cve:`2022-40768`,
    :uv:cve:`2022-41849`, :uv:cve:`2022-41850`, :uv:cve:`2022-42328`,
    :uv:cve:`2022-42329`, :uv:cve:`2022-42895`, :uv:cve:`2022-42896`,
    :uv:cve:`2022-43750`, :uv:cve:`2022-4378`) (:uv:bug:`54958`,
    :uv:bug:`55238`, :uv:bug:`55540`)

  * :program:`libxslt` (:uv:cve:`2019-5815`, :uv:cve:`2021-30560`)
    (:uv:bug:`55194`)

  * :program:`libxml2` (:uv:cve:`2022-40303`, :uv:cve:`2022-40304`)
    (:uv:bug:`55371`)

  * :program:`libtirpc` (:uv:cve:`2021-46828`) (:uv:bug:`55094`)

  * :program:`libtasn1-6` (:uv:cve:`2021-46848`) (:uv:bug:`55566`)

  * :program:`libsndfile` (:uv:cve:`2021-4156`) (:uv:bug:`55237`)

  * :program:`librsvg` (:uv:cve:`2019-20446`) (:uv:bug:`55193`)

  * :program:`libksba` (:uv:cve:`2022-3515`, :uv:cve:`2022-47629`)
    (:uv:bug:`55327`, :uv:bug:`55542`)

  * :program:`libde265` (:uv:cve:`2020-21596`, :uv:cve:`2020-21597`,
    :uv:cve:`2020-21598`, :uv:cve:`2020-21599`, :uv:cve:`2021-35452`,
    :uv:cve:`2021-36408`, :uv:cve:`2021-36409`, :uv:cve:`2021-36410`,
    :uv:cve:`2021-36411`, :uv:cve:`2022-43235`, :uv:cve:`2022-43236`,
    :uv:cve:`2022-43237`, :uv:cve:`2022-43238`, :uv:cve:`2022-43239`,
    :uv:cve:`2022-43240`, :uv:cve:`2022-43241`, :uv:cve:`2022-43242`,
    :uv:cve:`2022-43243`, :uv:cve:`2022-43244`, :uv:cve:`2022-43245`,
    :uv:cve:`2022-43248`, :uv:cve:`2022-43249`, :uv:cve:`2022-43250`,
    :uv:cve:`2022-43252`, :uv:cve:`2022-43253`, :uv:cve:`2022-47655`)
    (:uv:bug:`55504`, :uv:bug:`55594`)

  * :program:`libarchive` (:uv:cve:`2019-19221`, :uv:cve:`2021-23177`,
    :uv:cve:`2021-31566`, :uv:cve:`2022-36227`) (:uv:bug:`55464`,
    :uv:bug:`55625`)

  * :program:`ldb` (:uv:cve:`2022-32745`, :uv:cve:`2022-32746`)
    (:uv:bug:`54994`)

  * :program:`krb5` (:uv:cve:`2022-42898`) (:uv:bug:`55474`)

  * :program:`isc-dhcp` () (:uv:bug:`55270`)

  * :program:`intel-microcode` (:uv:cve:`2022-21123`,
    :uv:cve:`2022-21125`, :uv:cve:`2022-21127`, :uv:cve:`2022-21151`,
    :uv:cve:`2022-21166`) (:uv:bug:`54960`)

  * :program:`heimdal` (:uv:cve:`2019-14870`, :uv:cve:`2021-3671`,
    :uv:cve:`2021-44758`, :uv:cve:`2022-3437`, :uv:cve:`2022-41916`,
    :uv:cve:`2022-42898`, :uv:cve:`2022-44640`) (:uv:bug:`55461`)

  * :program:`gsasl` (:uv:cve:`2022-2469`) (:uv:bug:`55023`)

  * :program:`grub2` (:uv:cve:`2021-3695`, :uv:cve:`2021-3696`,
    :uv:cve:`2021-3697`, :uv:cve:`2022-2601`, :uv:cve:`2022-28733`,
    :uv:cve:`2022-28734`, :uv:cve:`2022-28735`, :uv:cve:`2022-28736`,
    :uv:cve:`2022-3775`) (:uv:bug:`55191`, :uv:bug:`55434`,
    :uv:bug:`55482`)

  * :program:`grub-efi-amd64-signed` (:uv:cve:`2021-3695`,
    :uv:cve:`2021-3696`, :uv:cve:`2021-3697`, :uv:cve:`2022-2601`,
    :uv:cve:`2022-28733`, :uv:cve:`2022-28734`, :uv:cve:`2022-28735`,
    :uv:cve:`2022-28736`, :uv:cve:`2022-3775`) (:uv:bug:`55191`,
    :uv:bug:`55434`, :uv:bug:`55482`)

  * :program:`gnutls28` (:uv:cve:`2021-4209`, :uv:cve:`2022-2509`)
    (:uv:bug:`55095`)

  * :program:`gnupg2` (:uv:cve:`2022-34903`) (:uv:bug:`54957`)

  * :program:`glibc` (:uv:cve:`2016-10228`, :uv:cve:`2019-19126`,
    :uv:cve:`2019-25013`, :uv:cve:`2020-10029`, :uv:cve:`2020-1752`,
    :uv:cve:`2020-27618`, :uv:cve:`2020-6096`, :uv:cve:`2021-27645`,
    :uv:cve:`2021-3326`, :uv:cve:`2021-33574`, :uv:cve:`2021-35942`,
    :uv:cve:`2021-3999`, :uv:cve:`2022-23218`, :uv:cve:`2022-23219`)
    (:uv:bug:`55326`)

  * :program:`glib2.0` (:uv:cve:`2021-3800`) (:uv:bug:`55208`)

  * :program:`giflib` (:uv:cve:`2018-11490`, :uv:cve:`2019-15133`)
    (:uv:bug:`55473`)

  * :program:`ghostscript` () (:uv:bug:`55168`)

  * :program:`fribidi` (:uv:cve:`2022-25308`, :uv:cve:`2022-25309`,
    :uv:cve:`2022-25310`) (:uv:bug:`55190`)

  * :program:`freetype` (:uv:cve:`2022-27404`, :uv:cve:`2022-27405`,
    :uv:cve:`2022-27406`) (:uv:bug:`55192`)

  * :program:`freeradius` (:uv:cve:`2019-13456`, :uv:cve:`2019-17185`)
    (:uv:bug:`55195`)

  * :program:`flac` (:uv:cve:`2021-0561`) (:uv:bug:`55169`)

  * :program:`firefox-esr` (:uv:cve:`2021-32810`,
    :uv:cve:`2021-38491`, :uv:cve:`2021-38493`, :uv:cve:`2021-38494`,
    :uv:cve:`2021-38496`, :uv:cve:`2021-38497`, :uv:cve:`2021-38498`,
    :uv:cve:`2021-38499`, :uv:cve:`2021-38500`, :uv:cve:`2021-38501`,
    :uv:cve:`2021-38503`, :uv:cve:`2021-38504`, :uv:cve:`2021-38506`,
    :uv:cve:`2021-38507`, :uv:cve:`2021-38508`, :uv:cve:`2021-38509`,
    :uv:cve:`2021-4140`, :uv:cve:`2021-43536`, :uv:cve:`2021-43537`,
    :uv:cve:`2021-43538`, :uv:cve:`2021-43539`, :uv:cve:`2021-43540`,
    :uv:cve:`2021-43541`, :uv:cve:`2021-43542`, :uv:cve:`2021-43543`,
    :uv:cve:`2021-43544`, :uv:cve:`2021-43545`, :uv:cve:`2021-43546`,
    :uv:cve:`2022-0511`, :uv:cve:`2022-0843`, :uv:cve:`2022-1097`,
    :uv:cve:`2022-1919`, :uv:cve:`2022-2200`, :uv:cve:`2022-22737`,
    :uv:cve:`2022-22738`, :uv:cve:`2022-22739`, :uv:cve:`2022-22740`,
    :uv:cve:`2022-22741`, :uv:cve:`2022-22742`, :uv:cve:`2022-22743`,
    :uv:cve:`2022-22745`, :uv:cve:`2022-22747`, :uv:cve:`2022-22748`,
    :uv:cve:`2022-22751`, :uv:cve:`2022-22752`, :uv:cve:`2022-22754`,
    :uv:cve:`2022-22755`, :uv:cve:`2022-22756`, :uv:cve:`2022-22759`,
    :uv:cve:`2022-22760`, :uv:cve:`2022-22761`, :uv:cve:`2022-22764`,
    :uv:cve:`2022-24713`, :uv:cve:`2022-2505`, :uv:cve:`2022-26381`,
    :uv:cve:`2022-26382`, :uv:cve:`2022-26383`, :uv:cve:`2022-26384`,
    :uv:cve:`2022-26385`, :uv:cve:`2022-26387`, :uv:cve:`2022-26485`,
    :uv:cve:`2022-26486`, :uv:cve:`2022-28281`, :uv:cve:`2022-28282`,
    :uv:cve:`2022-28283`, :uv:cve:`2022-28284`, :uv:cve:`2022-28285`,
    :uv:cve:`2022-28286`, :uv:cve:`2022-28287`, :uv:cve:`2022-28288`,
    :uv:cve:`2022-28289`, :uv:cve:`2022-29909`, :uv:cve:`2022-29911`,
    :uv:cve:`2022-29912`, :uv:cve:`2022-29914`, :uv:cve:`2022-29915`,
    :uv:cve:`2022-29916`, :uv:cve:`2022-29917`, :uv:cve:`2022-29918`,
    :uv:cve:`2022-31736`, :uv:cve:`2022-31737`, :uv:cve:`2022-31738`,
    :uv:cve:`2022-31740`, :uv:cve:`2022-31741`, :uv:cve:`2022-31742`,
    :uv:cve:`2022-31743`, :uv:cve:`2022-31744`, :uv:cve:`2022-31745`,
    :uv:cve:`2022-31747`, :uv:cve:`2022-31748`, :uv:cve:`2022-34468`,
    :uv:cve:`2022-34470`, :uv:cve:`2022-34471`, :uv:cve:`2022-34472`,
    :uv:cve:`2022-34473`, :uv:cve:`2022-34474`, :uv:cve:`2022-34475`,
    :uv:cve:`2022-34476`, :uv:cve:`2022-34477`, :uv:cve:`2022-34479`,
    :uv:cve:`2022-34480`, :uv:cve:`2022-34481`, :uv:cve:`2022-34482`,
    :uv:cve:`2022-34483`, :uv:cve:`2022-34484`, :uv:cve:`2022-34485`,
    :uv:cve:`2022-36315`, :uv:cve:`2022-36316`, :uv:cve:`2022-36318`,
    :uv:cve:`2022-36319`, :uv:cve:`2022-36320`, :uv:cve:`2022-38472`,
    :uv:cve:`2022-38473`, :uv:cve:`2022-38477`, :uv:cve:`2022-38478`,
    :uv:cve:`2022-42927`, :uv:cve:`2022-42928`, :uv:cve:`2022-42929`,
    :uv:cve:`2022-42932`, :uv:cve:`2022-45403`, :uv:cve:`2022-45404`,
    :uv:cve:`2022-45405`, :uv:cve:`2022-45406`, :uv:cve:`2022-45408`,
    :uv:cve:`2022-45409`, :uv:cve:`2022-45410`, :uv:cve:`2022-45411`,
    :uv:cve:`2022-45412`, :uv:cve:`2022-45416`, :uv:cve:`2022-45418`,
    :uv:cve:`2022-45420`, :uv:cve:`2022-45421`, :uv:cve:`2022-46871`,
    :uv:cve:`2022-46872`, :uv:cve:`2022-46874`, :uv:cve:`2022-46877`,
    :uv:cve:`2022-46878`, :uv:cve:`2022-46880`, :uv:cve:`2022-46881`,
    :uv:cve:`2022-46882`, :uv:cve:`2023-23598`, :uv:cve:`2023-23601`,
    :uv:cve:`2023-23602`, :uv:cve:`2023-23603`, :uv:cve:`2023-23605`)
    (:uv:bug:`54955`, :uv:bug:`55049`, :uv:bug:`55143`,
    :uv:bug:`55221`, :uv:bug:`55349`, :uv:bug:`55441`,
    :uv:bug:`55502`, :uv:bug:`55585`)

  * :program:`expat` (:uv:cve:`2022-40674`, :uv:cve:`2022-43680`)
    (:uv:bug:`55222`, :uv:bug:`55358`)

  * :program:`exim4` (:uv:cve:`2022-37452`) (:uv:bug:`55139`)

  * :program:`emacs` (:uv:cve:`2022-45939`) (:uv:bug:`55541`)

  * :program:`dovecot` (:uv:cve:`2021-33515`, :uv:cve:`2022-30550`)
    (:uv:bug:`55228`)

  * :program:`dbus` () (:uv:bug:`55272`)

  * :program:`curl` (:uv:cve:`2021-22898`, :uv:cve:`2021-22924`,
    :uv:cve:`2021-22946`, :uv:cve:`2021-22947`, :uv:cve:`2022-22576`,
    :uv:cve:`2022-27774`, :uv:cve:`2022-27776`, :uv:cve:`2022-27781`,
    :uv:cve:`2022-27782`, :uv:cve:`2022-32206`, :uv:cve:`2022-32208`,
    :uv:cve:`2022-32221`, :uv:cve:`2022-35252`, :uv:cve:`2022-43552`)
    (:uv:bug:`55140`, :uv:bug:`55626`)

  * :program:`clamav` (:uv:cve:`2022-20770`, :uv:cve:`2022-20771`,
    :uv:cve:`2022-20785`, :uv:cve:`2022-20792`, :uv:cve:`2022-20796`)
    (:uv:bug:`55188`)

  * :program:`bluez` (:uv:cve:`2019-8921`, :uv:cve:`2019-8922`,
    :uv:cve:`2021-41229`, :uv:cve:`2021-43400`, :uv:cve:`2022-0204`,
    :uv:cve:`2022-39176`, :uv:cve:`2022-39177`) (:uv:bug:`55340`)

  * :program:`bind9` (:uv:cve:`2022-2795`, :uv:cve:`2022-38177`,
    :uv:cve:`2022-38178`) (:uv:bug:`55163`, :uv:bug:`55253`)

  * :program:`apache2` (:uv:cve:`2022-22719`, :uv:cve:`2022-22720`,
    :uv:cve:`2022-22721`, :uv:cve:`2022-23943`, :uv:cve:`2022-26377`,
    :uv:cve:`2022-28614`, :uv:cve:`2022-28615`, :uv:cve:`2022-29404`,
    :uv:cve:`2022-30522`, :uv:cve:`2022-30556`, :uv:cve:`2022-31813`)
    (:uv:bug:`55187`)

.. _debian:

* The following updated packages from Debian 10.13 are included:
  :program:`base-files`,
  :program:`bzip2`,
  :program:`clamav`,
  :program:`debootstrap`,
  :program:`distro-info-data`,
  :program:`libnet-ssleay-perl`,
  :program:`postfix`,
  :program:`postgresql-11`,
  :program:`postgresql-common`,
  :program:`shim`,
  :program:`tzdata`,
  :program:`adminer`,
  :program:`asterisk`,
  :program:`awstats`,
  :program:`barbican`,
  :program:`batik`,
  :program:`bcel`,
  :program:`blender`,
  :program:`booth`,
  :program:`cacti`,
  :program:`cargo-mozilla`,
  :program:`cgal`,
  :program:`cinder`,
  :program:`clickhouse`,
  :program:`commons-daemon`,
  :program:`composer`,
  :program:`connman`,
  :program:`debian-installer`,
  :program:`debian-installer-netboot-images`,
  :program:`debian-security-support`,
  :program:`djangorestframework`,
  :program:`dlt-daemon`,
  :program:`dojo`,
  :program:`dpdk`,
  :program:`dropbear`,
  :program:`e17`,
  :program:`epiphany-browser`,
  :program:`esorex`,
  :program:`evemu`,
  :program:`exiv2`,
  :program:`exuberant-ctags`,
  :program:`feature-check`,
  :program:`ffmpeg`,
  :program:`fig2dev`,
  :program:`foxtrotgps`,
  :program:`freecad`,
  :program:`frr`,
  :program:`ftgl`,
  :program:`g810-led`,
  :program:`gdal`,
  :program:`gerbv`,
  :program:`gif2apng`,
  :program:`git`,
  :program:`glance`,
  :program:`gnucash`,
  :program:`golang-github-docker-go-connections`,
  :program:`golang-github-pkg-term`,
  :program:`golang-github-russellhaering-goxmldsig`,
  :program:`graphicsmagick`,
  :program:`gst-plugins-good1.0`,
  :program:`hsqldb`,
  :program:`htmldoc`,
  :program:`http-parser`,
  :program:`inetutils`,
  :program:`ini4j`,
  :program:`iptables-netflow`,
  :program:`isync`,
  :program:`jackson-databind`,
  :program:`jersey1`,
  :program:`jetty9`,
  :program:`jhead`,
  :program:`joblib`,
  :program:`jqueryui`,
  :program:`jupyter-core`,
  :program:`kannel`,
  :program:`kicad`,
  :program:`knot-resolver`,
  :program:`lava`,
  :program:`lemonldap-ng`,
  :program:`leptonlib`,
  :program:`libapache-session-browseable-perl`,
  :program:`libapache-session-ldap-perl`,
  :program:`libapache2-mod-auth-openidc`,
  :program:`libapreq2`,
  :program:`libbluray`,
  :program:`libcommons-net-java`,
  :program:`libdatetime-timezone-perl`,
  :program:`libetpan`,
  :program:`libgoogle-gson-java`,
  :program:`libhtml-stripscripts-perl`,
  :program:`libhttp-cookiejar-perl`,
  :program:`libhttp-daemon-perl`,
  :program:`libitext5-java`,
  :program:`libjettison-java`,
  :program:`libmodbus`,
  :program:`libnet-freedb-perl`,
  :program:`libpgjava`,
  :program:`libraw`,
  :program:`librose-db-object-perl`,
  :program:`libstb`,
  :program:`libvirt-php`,
  :program:`libvncserver`,
  :program:`libxstream-java`,
  :program:`libzen`,
  :program:`lighttpd`,
  :program:`linux-5.10`,
  :program:`linux-signed-5.10-amd64`,
  :program:`llvm-toolchain-13`,
  :program:`mat2`,
  :program:`maven-shared-utils`,
  :program:`mbedtls`,
  :program:`mediawiki`,
  :program:`minidlna`,
  :program:`modsecurity-apache`,
  :program:`modsecurity-crs`,
  :program:`mplayer`,
  :program:`mutt`,
  :program:`ndpi`,
  :program:`netty`,
  :program:`nginx`,
  :program:`node-cached-path-relative`,
  :program:`node-ejs`,
  :program:`node-end-of-stream`,
  :program:`node-eventsource`,
  :program:`node-fetch`,
  :program:`node-hawk`,
  :program:`node-json-schema`,
  :program:`node-loader-utils`,
  :program:`node-log4js`,
  :program:`node-minimatch`,
  :program:`node-minimist`,
  :program:`node-moment`,
  :program:`node-node-forge`,
  :program:`node-object-path`,
  :program:`node-qs`,
  :program:`node-require-from-string`,
  :program:`node-tar`,
  :program:`node-thenify`,
  :program:`node-trim-newlines`,
  :program:`node-xmldom`,
  :program:`nodejs`,
  :program:`nova`,
  :program:`nvidia-graphics-drivers`,
  :program:`nvidia-graphics-drivers-legacy-390xx`,
  :program:`octavia`,
  :program:`open-vm-tools`,
  :program:`openexr`,
  :program:`openjdk-11`,
  :program:`openvswitch`,
  :program:`orca`,
  :program:`pacemaker`,
  :program:`pcs`,
  :program:`pglogical`,
  :program:`php-guzzlehttp-psr7`,
  :program:`php-horde-mime-viewer`,
  :program:`php-horde-turba`,
  :program:`php-phpseclib`,
  :program:`phpseclib`,
  :program:`pngcheck`,
  :program:`postsrsd`,
  :program:`powerline-gitstatus`,
  :program:`procmail`,
  :program:`publicsuffix`,
  :program:`puma`,
  :program:`pysha3`,
  :program:`python-django`,
  :program:`python-keystoneauth1`,
  :program:`python-oslo.utils`,
  :program:`python-scciclient`,
  :program:`python-scrapy`,
  :program:`python-udatetime`,
  :program:`qtbase-opensource-src`,
  :program:`rails`,
  :program:`request-tracker4`,
  :program:`rexical`,
  :program:`ruby-activeldap`,
  :program:`ruby-git`,
  :program:`ruby-hiredis`,
  :program:`ruby-http-parser.rb`,
  :program:`ruby-nokogiri`,
  :program:`ruby-rack`,
  :program:`ruby-rails-html-sanitizer`,
  :program:`ruby-riddle`,
  :program:`ruby-sinatra`,
  :program:`ruby-tzinfo`,
  :program:`rust-cbindgen`,
  :program:`rustc-mozilla`,
  :program:`schroot`,
  :program:`sctk`,
  :program:`smarty3`,
  :program:`snakeyaml`,
  :program:`snapd`,
  :program:`sofia-sip`,
  :program:`spip`,
  :program:`strongswan`,
  :program:`swift`,
  :program:`sysstat`,
  :program:`thunderbird`,
  :program:`tinyxml`,
  :program:`tmux`,
  :program:`tomcat9`,
  :program:`tor`,
  :program:`trafficserver`,
  :program:`twig`,
  :program:`twisted`,
  :program:`ublock-origin`,
  :program:`unrar-nonfree`,
  :program:`varnish`,
  :program:`viewvc`,
  :program:`virglrenderer`,
  :program:`vlc`,
  :program:`webkit2gtk`,
  :program:`wireshark`,
  :program:`wkhtmltopdf`,
  :program:`wordpress`

.. _maintained:

* The following packages have been moved to the maintained repository of UCS:

.. _changelog-basis-ucr:

Univention Configuration Registry
=================================

* Add validation for values of UCR variables. By default only a warning is
  printed if an invalid value is set. By setting the UCR variable
  :envvar:`ucr/check/type` to ``yes`` type checking can be enforced, which will prevent
  invalid values to be set. As the type annotation of several UCR variables is
  currently wrong, types ``int`` and ``bool`` are ignored for now and will be fixed
  by future updates (:uv:bug:`54495`).

* A new variable type ``url_http`` was added in order to support validation of
  http/https URL strings (:uv:bug:`55044`).

* Fixed printing wrong UCR layer name (:uv:bug:`55174`).

* The UCR type checking is now displaying more specific information regarding
  the type constraints (:uv:bug:`55573`).

.. _changelog-basis-ucr-template:

Changes to templates and modules
--------------------------------

* Several UCR variable type annotations have been fixed. Most importantly UCRV
  :envvar:`proxy/http` and :envvar:`proxy/https` are now checked for validity as specifying a
  URL with a path, query or fragment will break several programs
  (:uv:bug:`54495`).

.. _changelog-domain-openldap-replication:

Listener/Notifier domain replication
------------------------------------

* Calls to several OpenLDAP tools (:command:`slaptest` etc.) fail when the :file:`cn=config`
  LDIF exists in the file-system. The package has been adjusted to explicitly
  specify using the configuration file instead to avoid this problem
  (:uv:bug:`54986`).

.. _changelog-domain-dnsserver:

DNS server
==========

* The script :file:`server_password_change.d/univention-bind` has been updated to
  generate more useful debug information (:uv:bug:`54273`).

.. _changelog-umc-web:

Univention Management Console web interface
===========================================

* The UDM command line client now writes error messages and warnings to
  standard error (:uv:bug:`4498`).

* The OpenAPI schema of the UDM REST API has been improved: Nested properties
  are now described more detailed while they previously were only described as
  free form objects. Data de-duplication has been made by referencing global
  data instead of including them. All possible HTTP errors are listed in the
  responses. Experimental features like pagination during search have been
  added as deprecated so that they can be used more easily in the future when
  UCS supports them. Various parameters are now created via code introspection
  (:uv:bug:`55096`).

* The URI template for nested search queries was invalid and has been adjusted
  (:uv:bug:`55115`).

* The script :file:`server_password_change.d/univention-directory-manager-rest` has
  been updated to generate more useful debug information (:uv:bug:`54273`).

* The performance of the UDM REST API has been improved: A duplicated LDAP
  search has been eliminated for ``GET``, ``PATCH`` and ``DELETE`` operations on an
  object (:uv:bug:`55430`).

* The LDAP connections for read and write operations have been separated and
  are now individually configurable via the UCR variables
  :envvar:`directory/manager/rest/ldap-connection/.*/.*` (:uv:bug:`54623`).

* The UDM REST API responses now respect the requested language so that e.g.
  error messages are correctly translated (:uv:bug:`55224`).

* For request tracing a unique ID has been added to each request via the HTTP header ``X-Request-Id`` which is accepted as request header (or if not given
  uniquely created) and returned in the response headers (:uv:bug:`55186`).

* The translation of error messages in the UDM REST API has been corrected
  (:uv:bug:`55446`).

* The error response format has been improved (while being backwards
  compatible). It is now described in the OpenAPI schema (:uv:bug:`50249`).

* A client can now requests all CSS themes. This makes it possible to base
  themes on another themes. This is required for :program:`univention-app-appliance`
  (:uv:bug:`55107`).

* The checkboxes in grids are now rendered in the correct state while scrolling
  (:uv:bug:`54451`).

* Cookie banners have been improved for mobile devices. The accept button is
  now permanently visible for easier use (:uv:bug:`55378`).

* The services :program:`univention-management-console-server` and
  :program:`univention-management-console-web-server` have been migrated to
  :program:`systemd` (:uv:bug:`53885`).

.. _changelog-umc-portal:

Univention Portal
=================

* Some convenient code for Python 2 compatibility has been removed
  (:uv:bug:`55063`).

* Cookie banners have been improved for mobile devices. The accept button is
  now permanently visible for easier use (:uv:bug:`55378`).

* Tiles in portal were not displayed correctly due to a bug while loading
  user's group membership (:uv:bug:`54497`).

* The script :file:`portal-server-password-rotate` has been updated to generate more
  useful debug information (:uv:bug:`54273`).

* The password hash comparison in :file:`UMCAndSecretAuthenticator` has been fixed
  (:uv:bug:`55010`).

.. _changelog-umc-server:

Univention Management Console server
====================================

* SAML Logouts using the SAML binding ``HTTP-POST`` is now supported. This is
  required for the use of UMC with e.g. Keycloak as an identity provider
  (:uv:bug:`55229`).

* The SAML identity cache has been changed to an in-memory cache. This can be
  changed to the filesystem database by setting the UCR variable :envvar:`umc/saml/in- memory-identity-cache` to ``false``. This is done automatically for servers
  with enabled multiprocessing (:uv:bug:`55424`).

* The error handling of the :program:`pysaml2` usage has been improved (:uv:bug:`55248`).

* Exception stack traces are logged again when :envvar:`umc/http/show_tracebacks` is
  set to ``False`` (:uv:bug:`55423`).

* A Keycloak SAML client for the local UMC is created during the join of a new
  server if the Keycloak App is installed in the domain (:uv:bug:`55395`).

* Calls to several OpenLDAP tools (:command:`slaptest` etc.) fail when the :file:`cn=config`
  LDIF exists in the file-system. The package has been adjusted to explicitly
  specify using the configuration file instead to avoid this problem
  (:uv:bug:`55570`).

* The library functions to get cached LDAP connections has been enhanced
  (:uv:bug:`54623`).

.. _changelog-umc-appcenter:

Univention App Center
=====================

* Fixed an internal function for parsing the app argument in the CLI
  :program:`univention-app` (:uv:bug:`55020`).

* Apps can now be pinned. A pinned app will no longer be upgraded or removed.
  They need to be unpinned first. :command:`univention-app pin $appid [--revert]`
  (:uv:bug:`55467`).

* The listener converter script is now a long running process, reducing the CPU
  load that was caused by its constant restart (:uv:bug:`52000`).

* In case of a signature verification error, the App Center now shows the GPG
  error message (:uv:bug:`54123`).

* The listener converter script is now by default writing the UDM REST API representation
  into the JSON files (:uv:bug:`54773`).

* Debian packages that contain non UTF-8 byte sequences do not crash the Provider Portal
  anymore when creating new versions of apps (:uv:bug:`55634`).

.. _changelog-umc-udmcli:

|UCSUDM| and command line interface
===================================

* The syntax classes :py:class:`UDM_Objects`, :py:class:`ldapDn`, :py:class:`ldapDnOrNone` now accept all
  valid LDAP DN characters as input (:uv:bug:`55563`).

* It is now possible to create extended attributes for LDAP operational
  attributes (:uv:bug:`20235`).

* The ``primaryGroup`` of ``users/user`` was unexpectedly reset to the default
  primary group when the primary group could not be read in LDAP. This was the
  case when the LDAP replication was not yet done or when the user had no
  permission to read it. The behavior is now postponed to actual modifications
  of the object (:uv:bug:`42080`).

* The Python backend code to evaluate and apply template defaults has been
  optimized (:uv:bug:`55279`).

* The OpenAPI schema of the UDM REST API has been improved (:uv:bug:`55096`).

* The error format of the UDM REST API now contains property information about
  email address validation failures (:uv:bug:`55394`).

* A missing call to the super method :py:func:`open()` has been added in the
  ``nagios/service`` UDM module so that it is available in the UDM REST API again
  (:uv:bug:`54064`).

* The syntax :py:class:`emailAddress` (and its children) are now checked against the
  external library ``python-email-validator`` by default. This can be disabled with
  the new UCRV :envvar:`directory/manager/mail-address/extra-validation`
  (:uv:bug:`55413`).

* The ``policies/umc`` module now also applied to ``computer`` objects as the UMC-
  Server evaluated them also for those (:uv:bug:`54568`).

* The ``employeeNumber`` attribute has been removed from the default filter for
  user objects. As the attribute is not part of the equality and presence index
  it caused performance problems in larger environments when searching for
  users in the Univention Management Console (:uv:bug:`55412`).

* The Simple UDM API provides policies references as mapping in version 3 to
  conform with the UDM REST API responses (:uv:bug:`50167`).

* The translation of error messages in the UDM REST API has been corrected
  (:uv:bug:`55446`).

* Changes for the UDM REST API required adjustments for the ``users/self`` UDM
  module (:uv:bug:`55430`).

* :py:func:`univention.admin.uldap.access()` now supports LDAP URIs to connect to
  (:uv:bug:`54623`).

* The global uniqueness of ``mailAlternativeAdress`` with ``mailPrimaryAddress`` is
  now configurable via the UCR variable :envvar:`directory/manager/mail-address/uniqueness` (:uv:bug:`54596`).

* The performance and debuggability of the UDM command line client has been
  improved (:uv:bug:`33224`).

* The UDM command line client now writes error messages and warnings to
  standard error (:uv:bug:`4498`).

* A regression in UCS 5.0 for LDAP presence filters (``attribute=*``) has been
  fixed. UDM modules which rewrite filters can now reliably test for LDAP
  presence filters (:uv:bug:`55037`).

* UDM now can store NT hashes in the attribute ``pwhistory``. Until now it used
  the attribute ``sambaPasswordHistory``, which only stores salted hashes of
  hashes, which doesn't allow synchronization to Samba/AD. UDM now doesn't care
  about the attribute ``sambaPasswordHistory`` any longer (:uv:bug:`52230`).

* The UDM modules ``users/user`` and ``groups/group`` now offer two additional UDM
  properties ``univentionObjectIdentifier`` and ``univentionSourceIAM``.
  ``univentionObjectIdentifier`` will be used by some apps to track the object
  identity regardless of the source of the object (e.g. either ``entryUUID`` or
  ``objectGUID``) and in a way that is independent of implementation of the IAM
  backend (e.g. OpenLDAP or Active Directory, :uv:bug:`55154`).

* A regression introduced by :uv:bug:`54883` has been fixed which caused that
  objects ``user/ldap`` could not be fetched via the UDM REST API
  (:uv:bug:`55189`).

* The property ``pwdChangeNextLogin`` of objects ``users/user`` was not correctly
  unmapped in case it was not set. This caused the UDM REST API to wrongly
  represent it as ``None`` instead of ``False`` (:uv:bug:`55226`).

* The property ``groups`` of UDM objects ``users/user`` are now resolved via the
  ``memberOf`` attribute instead of a manual search for group memberships to
  increase performance. Using the group memberships via ``memberOf`` adds all
  groups to the user which he is assigned to, even if the reading user cannot
  read the specific groups of if the memberships are no objects ``groups/group``.
  As there might be code which relies on this behavior and don't do proper
  error handling when iterating over group memberships the new UCR variable
  :envvar:`directory/manager/user/group-memberships-via-memberof` can be used to
  restore the old behavior. The variable is going to be removed in UCS 5.1
  (:uv:bug:`55269`).

* The UDM object ``users/ldap`` and various computer UDM object types have been extended to
  provide PKI user certificate properties (:uv:bug:`54987`).

.. _changelog-umc-setup:

Modules for system settings / setup wizard
==========================================

* The selection and search for countries and cities during the initial system
  setup has been repaired. It was broken since the Python 3 migration
  (:uv:bug:`55156`).

* Calls to several OpenLDAP tools (:command:`slaptest` etc.) fail when the :file:`cn=config`
  LDIF exists in the file-system. The package has been adjusted to explicitly
  specify using the configuration file instead to avoid this problem
  (:uv:bug:`54986`).

* Joining into the domain is now also possible for users containing a zero in
  their usernames (:uv:bug:`45058`).

.. _changelog-umc-join:

Domain join module
==================

* Rebuilt for :program:`libldb2` version 2.5.2 (:uv:bug:`54994`).

* A server with multiple MAC addresses is now able to join correctly again
  (:uv:bug:`54967`).

.. _changelog-umc-license:

License module
==============

* The front-end :program:`univention-system-activation` is now compatible with the new
  Portal framework introduced with UCS 5.0 (:uv:bug:`55107`).

.. _changelog-umc-diagnostic:

System diagnostic module
========================

* Calls to several OpenLDAP tools (:command:`slaptest` etc.) fail when the :file:`cn=config`
  LDIF exists in the file-system. The package has been adjusted to explicitly
  specify using the configuration file instead to avoid this problem
  (:uv:bug:`54986`).

* A new diagnostic routine was added to check and optionally to reestablish the
  correctness of the repository configuration. The following checks are
  performed:

  1. It is checked, if there are deprecated variables still defined.
     In this case by pressing the :guilabel:`ADJUST ALL COMPONENTS` button the merge
     process which is also done in the repository setting module is executed by
     the diagnostic routine including the deletion of the deprecated variables.

  2. It is checked if there are UCR variables :envvar:`repository/online/server` or
  :envvar:`repository/online/component/*/server` having a scheme other
  than ``http`` or ``https``. This can only be corrected manually using either the
  repository settings module or the UCR module to directly modify the
  variables. This second check can be disabled by defining an UCR variable
  :envvar:`diagnostic/check/65_check_repository_config/ignore` to any non-empty
  value (:uv:bug:`55044`).

* It is now possible to disable any diagnostic check by setting the UCR
  variable :envvar:`diagnostic/check/disable/TEST_NAME` to ``true`` (:uv:bug:`55468`).

* An error regarding compatibility with Python 3 has been repaired in the
  action :guilabel:`migrate objects` of :program:`56_univention_types` (:uv:bug:`55548`).

* A new UMC diagnostics module has been added to check UCR variable values for
  validity. As the type annotation of several UCR variables is currently wrong,
  types ``int`` and ``bool`` are ignored for now and will be fixed by future
  updates (:uv:bug:`54495`).

* The checks :program:`40_samba_tool_dbcheck` and :program:`63_proof_uniqueMembers` no longer
  crash due to duplicate decoding of strings during problem resolving
  (:uv:bug:`54988`).

* The diagnostics checks for SAML Identifier and Service Providers has been
  fixed to work again. It now provides more information in case of errors and
  provides automatic fixers to correct issues (:uv:bug:`49417`).

* The diagnostics check for the Univention Directory Notifier Protocol version
  has been extended to provide mot information in case of errors and provides
  an automatic fixer to update the protocol version (:uv:bug:`49417`).

.. _changelog-umc-ucr:

Univention Configuration Registry module
========================================

* In the UCR module of the management console the following deprecated
  variables are hidden and therefore no longer displayed:
  * :envvar:`repository/online/{prefix,port}`
  * :envvar:`repository/online/component/*/{prefix,port,username,password,unmaintained}`
  (:uv:bug:`55044`).

* The UCR module now displays errors regarding the type constraints
  (:uv:bug:`55573`).

.. _changelog-umc-other:

Other modules
=============

* The translation of error messages in the UDM REST API has been corrected
  (:uv:bug:`55446`).

* A typo in the name of the UMC Operation Set ``udm-policies`` has been adjusted
  (:uv:bug:`55460`).

* LDAP syntax classes with :py:attr:`addEmptyValue` or :py:attr:`appendEmptyValue` caused an
  error when opening e.g. the ``users/user`` module (:uv:bug:`54981`).

.. _changelog-lib:

*************************
Univention base libraries
*************************

* :py:mod:`univention.lib.i18n` now provides a method to set the language of all
  already instantiated :py:class:`Translation` instances (:uv:bug:`55224`).

* Calls to several OpenLDAP tools (:command:`slaptest` etc.) fail when the :file:`cn=config`
  LDIF exists in the file-system. The package has been adjusted to explicitly
  specify using the configuration file instead to avoid this problem
  (:uv:bug:`54986`).

* LDAP search requests now evaluate the response of server controls
  (:uv:bug:`49666`).

.. _changelog-deployment:

*******************
Software deployment
*******************

* Calls to several OpenLDAP tools (:command:`slaptest` etc.) fail when the :file:`cn=config`
  LDIF exists in the file-system. The package has been adjusted to explicitly
  specify using the configuration file instead to avoid this problem
  (:uv:bug:`54986`).

* The description of the UCR variables :envvar:`repository/online/*` which is displayed
  by using the command :command:`ucr info` was updated to document which variables are
  defined as deprecated and should no longer be used (:uv:bug:`55044`).

* The types of the UCR variables :envvar:`repository/online/*` and :envvar:`repository/online/component/*` ending
  with ``server`` or ``port`` have been updated to UCR type ``url_http`` and
  respectively ``portnumer`` in order to allow a better type checking
  (:uv:bug:`55044`).

* Updating a local repository server failed when additional components hosted
  on a separate server like ``service.software-univention.de`` were enabled:
  Calling :command:`univention-repository-update net` failed with a :py:exc:`ConfigurationError`
  pointing to a wrong URL on ``updates.software-univention.de`` instead
  (:uv:bug:`55069`).

.. _changelog-service-postgresql:

PostgreSQL
==========

* The script :command:`univention-postgresql-password` has been updated to generate more
  useful debug information (:uv:bug:`54273`).

.. _changelog-service-docker:

Docker
======

* The docker daemon will now be restarted after changing proxy settings
  (:uv:bug:`51033`).

.. _changelog-service-saml:

SAML
====

* Creation of certificate for Keycloak App on UCS Primary Directory Node
  (:uv:bug:`55331`).

* The unmapping of the LDAP attribute ``simplesamlLDAPattributes`` in the UDM
  module ``saml/serviceprovider`` now always unmaps the value in the new mappable
  format to support a representation in the UDM REST API (:uv:bug:`55348`).

* Add debug trace to the joinscript :file:`91univention-saml.inst` to improve error
  reporting (:uv:bug:`44669`).

.. _changelog-service-selfservice:

Univention self service
=======================

* The subject of all self-service emails is now configurable via the UCR
  variables :envvar:`umc/self-service/account-deregistration/email/subject`. :envvar:`umc/self-service/account-verification/email/subject`. and :envvar:`umc/self-service/email-
  change-notification/email/subject` (:uv:bug:`55028`).

* The email subject of the self-service password reset email is now
  configurable via the UCR variable :envvar:`umc/self-service/passwordreset/email/subject` (:uv:bug:`53227`).

.. _changelog-service-mail:

Mail services
=============

* Several UCR variable type annotations have been fixed. Most importantly UCRV
  :envvar:`clamav/proxy/http` is now checked for validity as specifying a URL with a
  path, query or fragment will break ClamAV (:uv:bug:`54495`).

* An unnecessary LDAP ACL for the LDAP root DN has been removed, which caused a
  warning by :command:`slapschema` (:uv:bug:`55159`).

.. _changelog-service-dovecot:

Dovecot
=======

* The template file :file:`/etc/pam.d/dovecot` has been converted to multifile to
  support extending the configuration. For example, OX requires the PAM
  configuration to be extensible to add functional account support
  (:uv:bug:`55510`).

.. _changelog-service-postfix:

Postfix
=======

* The script :file:`server_password_change.d/50univention-mail-server` has been updated
  to generate more useful debug information (:uv:bug:`54273`).

* The filter checking access to restricted mailing lists now accepts emails
  sent by users authenticating with their email address, when the system is
  configured to not use Dovecot SASL (:uv:bug:`55514`).

.. _changelog-service-print:

Printing services
=================

* After adding or removing printers UCS tells Samba to reload the
  configuration. In Samba 4.16 there is a new service :program:`samba-bgqd`, which
  required adjusting the way that the listener :file:`cups-printers.py` initiates the
  reload to make Samba recognize the changes immediately (:uv:bug:`55264`).

* When removing printer share definitions from Samba also remove the
  corresponding entries from the Samba registry and the TDB cache file
  (:uv:bug:`55492`).

.. _changelog-service-nagios:

Nagios
======

* The arguments for calling :command:`nmblookup` have been fixed. The flag ``-R`` has been
  changed to ``--recursion`` in prior Samba releases. This repairs the Nagios
  check ``UNIVENTION_NMBD`` (:uv:bug:`54919`).

.. _changelog-service-proxy:

Proxy services
==============

* The script :file:`squid-pw-rotate` has been updated to generate more useful debug
  information (:uv:bug:`54273`).

* The join process for UCS@School replica servers has been sped up by syncing
  certain objects during join in an earlier erratum. The speedup was only
  applied if there was no S4-Connector installed on the DC primary. This has
  been fixed (:uv:bug:`55218`).

* Joining UCS@School replica servers into environments with many objects could
  fail due to timeouts in the join scripts :file:`97univention-s4-connector`, :file:`98univention-samba4-dn` and :file:`98univention-squid-samba4`. The
  synchronization of existing objects delayed the synchronization of new
  objects which are created during the join and necessary for its completion.
  The S4-Connector and the join scripts have been modified to sync these vital
  objects first, which speeds up the join process considerably
  (:uv:bug:`54791`).

.. _changelog-service-ssl:

SSL
===

* Browsers check the certificate using the Subject Alternative Names (SAN).
  They are verified in order, which stops on first match. Order the SANs by
  length to prioritize the most specific values first (:uv:bug:`54697`).

* Fix cron daily task execution: change shell from :command:`sh` to :command:`bash`
  (:uv:bug:`55030`).

.. _changelog-service-dhcp:

DHCP server
===========

* The script :file:`server_password_change.d/univention-dhcp` has been updated to
  generate more useful debug information (:uv:bug:`54273`).

.. _changelog-service-other:

Other services
==============

* A new script :command:`univention-report-support-info` has been added which has the
  capability to download the latest USI script as well as uploading the
  collected archive to Univention and sending an email to the Univention
  support (:uv:bug:`26684`).

.. _changelog-win-samba:

Samba
=====

* The script :command:`univention-samba4-site-tool.py` attempted to parse the option ``-A``
  (for providing an authentication file), which is now already handled by the
  samba package in UCS. This has been fixed (:uv:bug:`55082`).

* The script command:`s4search-decode` can now be used to decode the attribute
  ``ntPwdHistory`` (:uv:bug:`52230`).

* Grant permission ``SePrintOperatorPrivilege`` to user ``Administrator`` and group
  ``Printer-Admins`` by default (:uv:bug:`54156`).

* Rotate additional log files :file:`log.dcerpcd` and :file:`log.rpcd_*` (:uv:bug:`55435`).

* Added a dependency on a specific package ``samba-dsdb-modules`` version to
  prevent issues with new package installations (:uv:bug:`54994`).

* The join process for UCS@School replica servers has been sped up by syncing
  certain objects during join in an earlier erratum. The speedup was only
  applied if there was no S4-Connector installed on the DC primary. This has
  been fixed (:uv:bug:`55218`).

* Joining UCS@School replica servers into environments with many objects could
  fail due to timeouts in the join scripts :file:`97univention-s4-connector`, :file:`98univention-samba4-dn` and :file:`98univention-squid-samba4`. The
  synchronization of existing objects delayed the synchronization of new
  objects which are created during the join and necessary for its completion.
  The S4-Connector and the join scripts have been modified to sync these vital
  objects first, which speeds up the join process considerably
  (:uv:bug:`54791`).

* Renaming a share works again. This was broken in UCS 5.0-0 due to an error in
  the listener module writing the share configuration (:uv:bug:`55077`).

* The script :file:`server_password_change.d/univention-samba` has been updated to
  generate more useful debug information (:uv:bug:`54273`).

* The UCR template for the Samba ``logrotate`` configuration has been fixed
  (:uv:bug:`55591`).

* Rotate additional log files :file:`log.dcerpcd` and file:`log.rpcd_*` (:uv:bug:`55435`).

* Renaming a share works again. This was broken in UCS 5.0-0 due to an error in
  the listener module writing the share configuration (:uv:bug:`55077`).

* A segmentation fault in :program:`rpcd_spoolss` has been fixed. Adding printer drivers
  is possible again (:uv:bug:`55048`).

.. _changelog-win-s4c:

Univention S4 Connector
=======================

* The password history synchronization now works when the policy ``pwdhistory_length``
  is not defined (:uv:bug:`55232`).

* Joining UCS@School replica servers into environments with many objects could
  fail due to timeouts in the join scripts :file:`97univention-s4-connector`, :file:`98univention-samba4-dn` and :file:`98univention-squid-samba4`. The
  synchronization of existing objects delayed the synchronization of new
  objects which are created during the join and necessary for its completion.
  The S4-Connector and the join scripts have been modified to sync these vital
  objects first, which speeds up the join process considerably
  (:uv:bug:`54791`).

* The script :file:`server_password_change.d/univention-s4-connector` has been updated
  to generate more useful debug information (:uv:bug:`54273`).

* The function :py:func:`group_members_sync_to_ucs` used a UCS DN to search in Samba,
  which usually doesn't cause issues, as long as the group object is located in
  the same position (:uv:bug:`55131`).

* The connector now synchronizes the password history between Samba and UCS
  (:uv:bug:`52230`).

.. _changelog-win-adc:

Univention Active Directory Connection
======================================

* The password history synchronization now works when the policy ``pwdhistory_length``
  is not defined (:uv:bug:`55232`).

* The mapping now evaluates UCR variables with respect to the configbasename.
  Therefore it is now possible again to create additional AD connector
  instances via :command:`prepare-new-instance`, which was broken since UCS 5.0-0
  (:uv:bug:`54780`).

* The function :py:func:`group_members_sync_to_ucs` used the UCS DN to search in AD,
  this regression introduced in UCS 5.0-0 has been fixed (:uv:bug:`55087`).

* The connector now synchronizes the password history between AD and UCS
  (:uv:bug:`52230`).

* When the password in Microsoft AD was reset for a user account with the flag
  :guilabel:`user must change password at next logon` active, the AD-Connector did not
  synchronize the password hashes to UCS in case the UCR variable
  :envvar:`connector/ad/mapping/attributes/irrelevant` was set to the default value.
  This UCR variable lists a number of attributes that should be ignored for
  performance reasons, like e.g. changes to the AD attribute ``lastLogon``. The
  AD flag :guilabel:`user must change password at next logon` is mapped to the Univention
  Directory Manager property ``pwdChangeNextLogin``. The behavior of the AD-
  Connector has been adjusted to always synchronize the ``post_attributes``
  listed in :file:`mapping.py` in this case. Please note that environments running an
  AD-Connector also run Samba/AD should check that UCR variable
  :envvar:`connector/ad/mapping/user/password/kerberos/enabled` is activated. If that's
  not activated, only the NT hash is synchronized from AD to UDM and then the
  S4-Connector only synchronizes the NT-Hash, leaving the previous Kerberos
  hashes in ``supplementalCredentials`` untouched, thus not conforming to the
  desired password reset when Kerberos is used in the UCS Samba/AD domain: Non-
  Kerberos logons would use the new NT-hashes, but Kerberos authentication
  would still use the previous password hashes (:uv:bug:`52192`).

* When objects where changed in Microsoft Active Directory, the AD-Connector
  checked if the object should be ignored. The decision is based on three
  criteria, ``match_filter``, ``ignoresubtree`` and the ``ignorelist`` from which the
  ``ignore_filter`` is constructed. Since :uv:bug:`37351` has been fixed in UCS
  :uv:erratum:`4.0x131` this check is not only applied to the new object, but also
  to the object existing in UDM, which represents the old state at the time of
  sync. In scenarios where an object is present in UDM and Microsoft Active
  Directory but matches the ``ignore_filter`` this had the negative side effect,
  that the AD object would still be ignored even if the administrator changed
  an attribute in a way that the new object did not match the ``ignore_filter``
  any longer. This affected user objects. This problem has been fixed by
  restricting the change for :uv:bug:`37351` to apply only to objects matching
  the criteria of a ``windowscomputer``, as these don't have an ``ignore_filter``
  (:uv:bug:`55150`).

* :program:`univention-adsearch` did not properly work in multi-connector setups
  (:uv:bug:`54781`).

.. _changelog-other:

*************
Other changes
*************

* The login page and tab name of the Keycloak Single-Sign On page have been
  modified to match those of the :program:`simpleSAMLphp` login page (:uv:bug:`55478`).

* Users can now login with their ``mailPrimaryAddress`` as well as their username
  at Keycloak (:uv:bug:`55458`).

* The script :command:`univention-keycloak` didn't evaluate the app setting
  ``keycloak/server/sso/fqdn``. Due to this, the joinscript of the Keycloak app
  failed if this setting is set (:uv:bug:`55569`).

* Many options of the script :command:`univention-keycloak` can now be passed on the
  command line. :command:`univention-config-registry` is not required anymore, but only
  gives sane defaults (:uv:bug:`55513`).

* A traceback in :program:`univention-keycloak` was thrown when trying to enable the two
  factor authentication. This has been fixed (:uv:bug:`55519`).

* A new flag ``--umc-uid-mapper`` has been added to the command line tool :command:`univention-keycloak`.
  This makes it easier to create SAML service-provider for the UMC
  (:uv:bug:`55431`).

* The :program:`univention-keycloak` package has been added. This package contains a CLI
  tool that is used by the Univention Keycloak app (:uv:bug:`55383`).

* StartTLS is now used as default for LDAP federation in Keycloak
  (:uv:bug:`55488`).

* The flag ``--metadata-file`` has been added to :command:`univention-keycloak`. This is
  necessary to create a UMC SAML client during the join since the metadata
  information can not be fetched via https during the join (:uv:bug:`55570`).

* The ownership, group and permissions of LDAP backups are now configurable via
  the UCR variables :envvar:`slapd/backup/owner`, :envvar:`slapd/backup/group` and
  :envvar:`slapd/backup/permissions` (:uv:bug:`54782`).

* The UCR variable description for the variable :envvar:`ldap/database/type` has been
  updated and now describes deprecated and recommended values (:uv:bug:`54821`).

* Create initial fake schema in unjoined Backup/Replica servers too to avoid
  invalid slapd configurations that may break upgrades (:uv:bug:`54465`).

* Allow Directory Node Backup and Replica servers to do an unlimited LDAP
  search, which is required for join in large domains with more than 400k
  entries (:uv:bug:`34877`).

* Change code to emit UCRV :envvar:`ldap/translog-ignore-temporary` only when LDAP
  overlay module ``translog`` is enabled (:uv:bug:`55558`).

* Calls to several OpenLDAP tools (:command:`slaptest` etc.) fail when the :file:`cn=config`
  LDIF exists in the file-system. The package has been adjusted to explicitly
  specify using the configuration file instead to avoid this problem
  (:uv:bug:`54986`).

* The object class ``univentionObject`` now offers two additional optional
  attributes ``univentionObjectIdentifier`` and ``univentionSourceIAM``.
  ``univentionObjectIdentifier`` will be used by some apps to track the object
  identity regardless of the source of the object (e.g. either ``entryUUID`` or
  ``objectGUID``) and in a way that is independent of implementation of the IAM
  backend (e.g. OpenLDAP or Active Directory, :uv:bug:`55154`).

* An additional ACL access directive for the machine account provides faster
  access to DNS zone objects (:uv:bug:`54140`).

* On UCS Replica Directory Nodes the OpenLDAP ``ppolicy`` overlay was not allowed
  to lock user accounts. The server ACLs have been adjusted to allow this
  (:uv:bug:`55501`).

* The Debian package :program:`python-email-validator` has been back ported and updated
  to be used in :program:`univention-directory-manager-modules` (:uv:bug:`55413`).

* An open file descriptor leak has been fixed, which was triggered by
  :py:func:`gdbm_reorganize()`. This affected :program:`univention-group-membership-cache` taking
  up a huge amount of disk space until the Directory Listener was restarted
  (:uv:bug:`55286`).

* The script execution is now restricted to valid system roles. A missing
  metric has been added to the alert ``UNIVENTION_ADCONNECTOR_METRIC_MISSING``. A
  leftover Nagios reference has been removed in in :command:`check_univention_nfsstatus`
  (:uv:bug:`54968`).

* Unassigning alerts from computer objects has been fixed (:uv:bug:`54985`).

* LDAP ACL's allowing DCs and Memberservers to change alerts have been added.
  The alert descriptions have been improved. The authentication when trying to
  reload Prometheus alerts has been fixed. Query expressions are now templated
  and restrict the metrics to the assigned hostnames (:uv:bug:`54947`).

* The alert expressions for checking the SSL validity and the swap usage have
  been repaired. The join status check has been split into two checks. An error
  in :command:`check_univention_samba_drs_failures` has been fixed (:uv:bug:`54919`).

* When :program:`prometheus-node-exporter` was not installed error mails by cron were
  sent due to a missing directory (:uv:bug:`54927`).

* The check script :command:`check_univention_ntp` now handles errors when the NTP
  service is not reachable. The translation of the UDM module has been fixed.
  The property ``templateValues`` is now exposed by the UDM module
  (:uv:bug:`55017`).

* It is now possible to disable the UDM UMC module ``monitoring/alert`` with
  specific UMC ACL's (:uv:bug:`55341`).

* Fixed :command:`ldapsearch` call in :command:`check_univention_joinstatus`. Wrong parameters
  created periodically high load on slapd (:uv:bug:`55068`).

* The scripts :command:`univention-nscd` and :command:`univention-libnss-ldap` have been updated to
  generate more useful debug information (:uv:bug:`54273`).

* The error handling of the directory logger has been improved. Especially in
  regards to corrupted files created by the overlay module ``dellog`` (:uv:bug:`51772`).

* The generated Listener module code has been updated to follow the API for
  Listener modules set with UCS 5.0-2, which deprecated the method
  :py:meth:`ListenerModuleConfiguration.get_configuration()` (:uv:bug:`54502`).

* Tiles in portal were not displayed correctly due to a bug while loading
  user's group membership (:uv:bug:`54497`).

* Improved performance of the function :py:func:`users_groups` which is used in
  :program:`univention-portal` (:uv:bug:`55120`).

* Python 3 compatibility for the SSS (Server Side Search control) has been
  added (:uv:bug:`49666`).

