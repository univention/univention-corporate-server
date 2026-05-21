.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _relnotes-changelog:

#########################################################
Changelog for Univention Corporate Server (UCS) |release|
#########################################################

.. _changelog-general:

*******
General
*******

.. _security:

* |UCSUCS| |release| includes all security updates issued for UCS 5.3-5:

  * :program:`apache2` (:uv:cve:`2026-23918`, :uv:cve:`2026-24072`,
    :uv:cve:`2026-29169`, :uv:cve:`2026-33006`, :uv:cve:`2026-33007`,
    :uv:cve:`2026-33523`, :uv:cve:`2026-33857`, :uv:cve:`2026-34032`,
    :uv:cve:`2026-34059`) (:uv:bug:`59264`)

  * :program:`bind9` (:uv:cve:`2026-1519`, :uv:cve:`2026-3039`,
    :uv:cve:`2026-3592`, :uv:cve:`2026-5946`, :uv:cve:`2026-5950`)
    (:uv:bug:`59152`, :uv:bug:`59432`)

  * :program:`busybox` (:uv:cve:`2022-48174`, :uv:cve:`2023-42363`,
    :uv:cve:`2023-42364`, :uv:cve:`2023-42365`) (:uv:bug:`59310`)

  * :program:`containerd` (:uv:cve:`2025-64329`) (:uv:bug:`59292`)

  * :program:`dovecot` (:uv:cve:`2025-59031`, :uv:cve:`2025-59032`,
    :uv:cve:`2026-0394`, :uv:cve:`2026-27855`, :uv:cve:`2026-27856`,
    :uv:cve:`2026-27857`, :uv:cve:`2026-27858`, :uv:cve:`2026-27859`,
    :uv:cve:`2026-33603`, :uv:cve:`2026-40016`, :uv:cve:`2026-40020`,
    :uv:cve:`2026-42006`) (:uv:bug:`59168`, :uv:bug:`59244`,
    :uv:bug:`59309`, :uv:bug:`59446`)

  * :program:`dpkg` (:uv:cve:`2025-6297`, :uv:cve:`2026-2219`)
    (:uv:bug:`59293`)

  * :program:`exim4` (:uv:cve:`2026-40684`, :uv:cve:`2026-40685`,
    :uv:cve:`2026-40686`, :uv:cve:`2026-40687`, :uv:cve:`2026-45185`)
    (:uv:bug:`59296`)

  * :program:`firefox-esr` (:uv:cve:`2025-59375`, :uv:cve:`2026-2447`,
    :uv:cve:`2026-2757`, :uv:cve:`2026-2758`, :uv:cve:`2026-2759`,
    :uv:cve:`2026-2760`, :uv:cve:`2026-2761`, :uv:cve:`2026-2762`,
    :uv:cve:`2026-2763`, :uv:cve:`2026-2764`, :uv:cve:`2026-2765`,
    :uv:cve:`2026-2766`, :uv:cve:`2026-2767`, :uv:cve:`2026-2768`,
    :uv:cve:`2026-2769`, :uv:cve:`2026-2770`, :uv:cve:`2026-2771`,
    :uv:cve:`2026-2772`, :uv:cve:`2026-2773`, :uv:cve:`2026-2774`,
    :uv:cve:`2026-2775`, :uv:cve:`2026-2777`, :uv:cve:`2026-2778`,
    :uv:cve:`2026-2779`, :uv:cve:`2026-2780`, :uv:cve:`2026-2781`,
    :uv:cve:`2026-2782`, :uv:cve:`2026-2783`, :uv:cve:`2026-2784`,
    :uv:cve:`2026-2785`, :uv:cve:`2026-2786`, :uv:cve:`2026-2787`,
    :uv:cve:`2026-2788`, :uv:cve:`2026-2789`, :uv:cve:`2026-2790`,
    :uv:cve:`2026-2791`, :uv:cve:`2026-2792`, :uv:cve:`2026-2793`,
    :uv:cve:`2026-4684`, :uv:cve:`2026-4685`, :uv:cve:`2026-4686`,
    :uv:cve:`2026-4687`, :uv:cve:`2026-4688`, :uv:cve:`2026-4689`,
    :uv:cve:`2026-4690`, :uv:cve:`2026-4691`, :uv:cve:`2026-4692`,
    :uv:cve:`2026-4693`, :uv:cve:`2026-4694`, :uv:cve:`2026-4695`,
    :uv:cve:`2026-4696`, :uv:cve:`2026-4697`, :uv:cve:`2026-4698`,
    :uv:cve:`2026-4699`, :uv:cve:`2026-4700`, :uv:cve:`2026-4701`,
    :uv:cve:`2026-4702`, :uv:cve:`2026-4704`, :uv:cve:`2026-4705`,
    :uv:cve:`2026-4706`, :uv:cve:`2026-4707`, :uv:cve:`2026-4708`,
    :uv:cve:`2026-4709`, :uv:cve:`2026-4710`, :uv:cve:`2026-4713`,
    :uv:cve:`2026-4714`, :uv:cve:`2026-4715`, :uv:cve:`2026-4716`,
    :uv:cve:`2026-4717`, :uv:cve:`2026-4718`, :uv:cve:`2026-4719`,
    :uv:cve:`2026-4720`, :uv:cve:`2026-4721`, :uv:cve:`2026-5731`,
    :uv:cve:`2026-5732`, :uv:cve:`2026-5734`, :uv:cve:`2026-6746`,
    :uv:cve:`2026-6747`, :uv:cve:`2026-6748`, :uv:cve:`2026-6749`,
    :uv:cve:`2026-6750`, :uv:cve:`2026-6751`, :uv:cve:`2026-6752`,
    :uv:cve:`2026-6753`, :uv:cve:`2026-6754`, :uv:cve:`2026-6757`,
    :uv:cve:`2026-6761`, :uv:cve:`2026-6762`, :uv:cve:`2026-6763`,
    :uv:cve:`2026-6764`, :uv:cve:`2026-6765`, :uv:cve:`2026-6766`,
    :uv:cve:`2026-6767`, :uv:cve:`2026-6769`, :uv:cve:`2026-6770`,
    :uv:cve:`2026-6771`, :uv:cve:`2026-6772`, :uv:cve:`2026-6776`,
    :uv:cve:`2026-6785`, :uv:cve:`2026-6786`, :uv:cve:`2026-7320`,
    :uv:cve:`2026-7321`, :uv:cve:`2026-7322`, :uv:cve:`2026-7323`,
    :uv:cve:`2026-8090`, :uv:cve:`2026-8092`, :uv:cve:`2026-8094`,
    :uv:cve:`2026-8388`, :uv:cve:`2026-8391`, :uv:cve:`2026-8401`,
    :uv:cve:`2026-8946`, :uv:cve:`2026-8947`, :uv:cve:`2026-8950`,
    :uv:cve:`2026-8953`, :uv:cve:`2026-8954`, :uv:cve:`2026-8955`,
    :uv:cve:`2026-8956`, :uv:cve:`2026-8957`, :uv:cve:`2026-8958`,
    :uv:cve:`2026-8961`, :uv:cve:`2026-8962`, :uv:cve:`2026-8968`,
    :uv:cve:`2026-8970`, :uv:cve:`2026-8974`, :uv:cve:`2026-8975`)
    (:uv:bug:`59126`, :uv:bug:`59154`, :uv:bug:`59181`,
    :uv:bug:`59227`, :uv:bug:`59246`, :uv:bug:`59270`,
    :uv:bug:`59430`)

  * :program:`gdk-pixbuf` (:uv:cve:`2026-5201`) (:uv:bug:`59182`)

  * :program:`glib2.0` (:uv:cve:`2026-0988`, :uv:cve:`2026-1484`,
    :uv:cve:`2026-1485`, :uv:cve:`2026-1489`) (:uv:bug:`59306`)

  * :program:`glibc` (:uv:cve:`2025-15281`, :uv:cve:`2026-0861`,
    :uv:cve:`2026-0915`, :uv:cve:`2026-4046`, :uv:cve:`2026-4437`,
    :uv:cve:`2026-4438`) (:uv:bug:`59294`)

  * :program:`gnutls28` (:uv:cve:`2026-33845`, :uv:cve:`2026-33846`,
    :uv:cve:`2026-3832`, :uv:cve:`2026-3833`, :uv:cve:`2026-42009`,
    :uv:cve:`2026-42010`, :uv:cve:`2026-42011`, :uv:cve:`2026-42012`,
    :uv:cve:`2026-42013`, :uv:cve:`2026-42014`, :uv:cve:`2026-42015`,
    :uv:cve:`2026-5260`, :uv:cve:`2026-5419`) (:uv:bug:`59437`)

  * :program:`grub-efi-amd64-signed` (:uv:cve:`2024-45774`,
    :uv:cve:`2024-45775`, :uv:cve:`2024-45776`, :uv:cve:`2024-45777`,
    :uv:cve:`2024-45778`, :uv:cve:`2024-45779`, :uv:cve:`2024-45780`,
    :uv:cve:`2024-45781`, :uv:cve:`2024-45782`, :uv:cve:`2024-45783`,
    :uv:cve:`2025-0622`, :uv:cve:`2025-0624`, :uv:cve:`2025-0677`,
    :uv:cve:`2025-0678`, :uv:cve:`2025-0684`, :uv:cve:`2025-0685`,
    :uv:cve:`2025-0686`, :uv:cve:`2025-0689`, :uv:cve:`2025-0690`,
    :uv:cve:`2025-1118`, :uv:cve:`2025-1125`) (:uv:bug:`59290`)

  * :program:`grub2` (:uv:cve:`2024-45774`, :uv:cve:`2024-45775`,
    :uv:cve:`2024-45776`, :uv:cve:`2024-45777`, :uv:cve:`2024-45778`,
    :uv:cve:`2024-45779`, :uv:cve:`2024-45780`, :uv:cve:`2024-45781`,
    :uv:cve:`2024-45782`, :uv:cve:`2024-45783`, :uv:cve:`2025-0622`,
    :uv:cve:`2025-0624`, :uv:cve:`2025-0677`, :uv:cve:`2025-0678`,
    :uv:cve:`2025-0684`, :uv:cve:`2025-0685`, :uv:cve:`2025-0686`,
    :uv:cve:`2025-0689`, :uv:cve:`2025-0690`, :uv:cve:`2025-1118`,
    :uv:cve:`2025-1125`) (:uv:bug:`59290`)

  * :program:`haveged` (:uv:cve:`2026-41054`) (:uv:bug:`59431`)

  * :program:`imagemagick` (:uv:cve:`2026-24481`,
    :uv:cve:`2026-24484`, :uv:cve:`2026-24485`, :uv:cve:`2026-25576`,
    :uv:cve:`2026-25638`, :uv:cve:`2026-25795`, :uv:cve:`2026-25796`,
    :uv:cve:`2026-25797`, :uv:cve:`2026-25798`, :uv:cve:`2026-25799`,
    :uv:cve:`2026-25897`, :uv:cve:`2026-25898`, :uv:cve:`2026-25965`,
    :uv:cve:`2026-25968`, :uv:cve:`2026-25970`, :uv:cve:`2026-25971`,
    :uv:cve:`2026-25982`, :uv:cve:`2026-25983`, :uv:cve:`2026-25985`,
    :uv:cve:`2026-25986`, :uv:cve:`2026-25987`, :uv:cve:`2026-25988`,
    :uv:cve:`2026-25989`, :uv:cve:`2026-26066`, :uv:cve:`2026-26283`,
    :uv:cve:`2026-26284`, :uv:cve:`2026-26983`, :uv:cve:`2026-27798`,
    :uv:cve:`2026-27799`, :uv:cve:`2026-28494`, :uv:cve:`2026-28686`,
    :uv:cve:`2026-28687`, :uv:cve:`2026-28688`, :uv:cve:`2026-28689`,
    :uv:cve:`2026-28690`, :uv:cve:`2026-28691`, :uv:cve:`2026-28692`,
    :uv:cve:`2026-28693`, :uv:cve:`2026-30883`, :uv:cve:`2026-30936`,
    :uv:cve:`2026-30937`, :uv:cve:`2026-31853`, :uv:cve:`2026-32259`,
    :uv:cve:`2026-32636`, :uv:cve:`2026-33535`, :uv:cve:`2026-33536`,
    :uv:cve:`2026-33899`, :uv:cve:`2026-33900`, :uv:cve:`2026-33901`,
    :uv:cve:`2026-33905`, :uv:cve:`2026-33908`, :uv:cve:`2026-34238`,
    :uv:cve:`2026-40310`, :uv:cve:`2026-40311`, :uv:cve:`2026-42050`,
    :uv:cve:`2026-42326`, :uv:cve:`2026-45031`, :uv:cve:`2026-45359`,
    :uv:cve:`2026-45624`, :uv:cve:`2026-45664`, :uv:cve:`2026-46520`,
    :uv:cve:`2026-46521`, :uv:cve:`2026-46522`, :uv:cve:`2026-46523`,
    :uv:cve:`2026-46559`, :uv:cve:`2026-46692`, :uv:cve:`2026-46693`,
    :uv:cve:`2026-47165`, :uv:cve:`2026-47166`) (:uv:bug:`59125`,
    :uv:bug:`59201`, :uv:bug:`59248`, :uv:bug:`59448`)

  * :program:`inetutils` (:uv:cve:`2026-24061`, :uv:cve:`2026-28372`,
    :uv:cve:`2026-32746`, :uv:cve:`2026-32772`) (:uv:bug:`59167`)

  * :program:`krb5` (:uv:cve:`2026-40355`, :uv:cve:`2026-40356`)
    (:uv:bug:`59428`)

  * :program:`lcms2` (:uv:cve:`2026-41254`) (:uv:bug:`59271`)

  * :program:`libarchive` (:uv:cve:`2025-5918`, :uv:cve:`2026-4111`,
    :uv:cve:`2026-4424`, :uv:cve:`2026-4426`, :uv:cve:`2026-5121`)
    (:uv:bug:`59305`)

  * :program:`libcap2` (:uv:cve:`2026-4878`) (:uv:bug:`59316`)

  * :program:`libexif` (:uv:cve:`2026-32775`, :uv:cve:`2026-40385`,
    :uv:cve:`2026-40386`) (:uv:bug:`59287`)

  * :program:`libgcrypt20` (:uv:cve:`2026-41989`) (:uv:bug:`59438`)

  * :program:`libnet-cidr-lite-perl` (:uv:cve:`2026-40198`,
    :uv:cve:`2026-40199`) (:uv:bug:`59308`)

  * :program:`libpng1.6` (:uv:cve:`2026-33416`, :uv:cve:`2026-33636`,
    :uv:cve:`2026-34757`) (:uv:bug:`59165`, :uv:bug:`59268`)

  * :program:`libxml-parser-perl` (:uv:cve:`2006-10002`,
    :uv:cve:`2006-10003`) (:uv:bug:`59153`)

  * :program:`linux` (:uv:cve:`2023-53228`, :uv:cve:`2023-53424`,
    :uv:cve:`2023-53510`, :uv:cve:`2023-53545`, :uv:cve:`2024-26822`,
    :uv:cve:`2024-47736`, :uv:cve:`2024-47809`, :uv:cve:`2024-49998`,
    :uv:cve:`2024-50298`, :uv:cve:`2024-56719`, :uv:cve:`2024-57895`,
    :uv:cve:`2025-21676`, :uv:cve:`2025-21682`, :uv:cve:`2025-22026`,
    :uv:cve:`2025-23155`, :uv:cve:`2025-37786`, :uv:cve:`2025-37920`,
    :uv:cve:`2025-37945`, :uv:cve:`2025-37980`, :uv:cve:`2025-38105`,
    :uv:cve:`2025-38162`, :uv:cve:`2025-38192`, :uv:cve:`2025-38201`,
    :uv:cve:`2025-38250`, :uv:cve:`2025-38303`, :uv:cve:`2025-38436`,
    :uv:cve:`2025-38617`, :uv:cve:`2025-38626`, :uv:cve:`2025-38643`,
    :uv:cve:`2025-38659`, :uv:cve:`2025-38704`, :uv:cve:`2025-39748`,
    :uv:cve:`2025-39763`, :uv:cve:`2025-39764`, :uv:cve:`2025-39863`,
    :uv:cve:`2025-40005`, :uv:cve:`2025-40016`, :uv:cve:`2025-40082`,
    :uv:cve:`2025-40135`, :uv:cve:`2025-40219`, :uv:cve:`2025-40242`,
    :uv:cve:`2025-40251`, :uv:cve:`2025-40261`, :uv:cve:`2025-40358`,
    :uv:cve:`2025-68206`, :uv:cve:`2025-68239`, :uv:cve:`2025-68265`,
    :uv:cve:`2025-68358`, :uv:cve:`2025-71067`, :uv:cve:`2025-71089`,
    :uv:cve:`2025-71144`, :uv:cve:`2025-71161`, :uv:cve:`2025-71221`,
    :uv:cve:`2025-71232`, :uv:cve:`2025-71233`, :uv:cve:`2025-71235`,
    :uv:cve:`2025-71236`, :uv:cve:`2025-71237`, :uv:cve:`2025-71265`,
    :uv:cve:`2025-71266`, :uv:cve:`2025-71267`, :uv:cve:`2025-71269`,
    :uv:cve:`2026-23100`, :uv:cve:`2026-23111`, :uv:cve:`2026-23112`,
    :uv:cve:`2026-23113`, :uv:cve:`2026-23141`, :uv:cve:`2026-23154`,
    :uv:cve:`2026-23157`, :uv:cve:`2026-23169`, :uv:cve:`2026-23204`,
    :uv:cve:`2026-23220`, :uv:cve:`2026-23221`, :uv:cve:`2026-23222`,
    :uv:cve:`2026-23227`, :uv:cve:`2026-23228`, :uv:cve:`2026-23229`,
    :uv:cve:`2026-23230`, :uv:cve:`2026-23231`, :uv:cve:`2026-23242`,
    :uv:cve:`2026-23243`, :uv:cve:`2026-23245`, :uv:cve:`2026-23253`,
    :uv:cve:`2026-23270`, :uv:cve:`2026-23271`, :uv:cve:`2026-23273`,
    :uv:cve:`2026-23274`, :uv:cve:`2026-23277`, :uv:cve:`2026-23279`,
    :uv:cve:`2026-23281`, :uv:cve:`2026-23284`, :uv:cve:`2026-23286`,
    :uv:cve:`2026-23287`, :uv:cve:`2026-23289`, :uv:cve:`2026-23290`,
    :uv:cve:`2026-23291`, :uv:cve:`2026-23292`, :uv:cve:`2026-23293`,
    :uv:cve:`2026-23296`, :uv:cve:`2026-23298`, :uv:cve:`2026-23300`,
    :uv:cve:`2026-23303`, :uv:cve:`2026-23304`, :uv:cve:`2026-23306`,
    :uv:cve:`2026-23307`, :uv:cve:`2026-23309`, :uv:cve:`2026-23312`,
    :uv:cve:`2026-23315`, :uv:cve:`2026-23317`, :uv:cve:`2026-23318`,
    :uv:cve:`2026-23319`, :uv:cve:`2026-23321`, :uv:cve:`2026-23324`,
    :uv:cve:`2026-23335`, :uv:cve:`2026-23336`, :uv:cve:`2026-23339`,
    :uv:cve:`2026-23340`, :uv:cve:`2026-23343`, :uv:cve:`2026-23351`,
    :uv:cve:`2026-23352`, :uv:cve:`2026-23356`, :uv:cve:`2026-23357`,
    :uv:cve:`2026-23359`, :uv:cve:`2026-23360`, :uv:cve:`2026-23362`,
    :uv:cve:`2026-23364`, :uv:cve:`2026-23365`, :uv:cve:`2026-23367`,
    :uv:cve:`2026-23368`, :uv:cve:`2026-23370`, :uv:cve:`2026-23372`,
    :uv:cve:`2026-23378`, :uv:cve:`2026-23379`, :uv:cve:`2026-23381`,
    :uv:cve:`2026-23382`, :uv:cve:`2026-23388`, :uv:cve:`2026-23391`,
    :uv:cve:`2026-23392`, :uv:cve:`2026-23395`, :uv:cve:`2026-23396`,
    :uv:cve:`2026-23397`, :uv:cve:`2026-23398`, :uv:cve:`2026-23401`,
    :uv:cve:`2026-23414`, :uv:cve:`2026-23420`, :uv:cve:`2026-23422`,
    :uv:cve:`2026-23426`, :uv:cve:`2026-23428`, :uv:cve:`2026-23434`,
    :uv:cve:`2026-23438`, :uv:cve:`2026-23439`, :uv:cve:`2026-23446`,
    :uv:cve:`2026-23449`, :uv:cve:`2026-23450`, :uv:cve:`2026-23452`,
    :uv:cve:`2026-23454`, :uv:cve:`2026-23455`, :uv:cve:`2026-23456`,
    :uv:cve:`2026-23457`, :uv:cve:`2026-23458`, :uv:cve:`2026-23460`,
    :uv:cve:`2026-23462`, :uv:cve:`2026-23463`, :uv:cve:`2026-23474`,
    :uv:cve:`2026-23475`, :uv:cve:`2026-31389`, :uv:cve:`2026-31391`,
    :uv:cve:`2026-31392`, :uv:cve:`2026-31393`, :uv:cve:`2026-31396`,
    :uv:cve:`2026-31399`, :uv:cve:`2026-31400`, :uv:cve:`2026-31402`,
    :uv:cve:`2026-31403`, :uv:cve:`2026-31405`, :uv:cve:`2026-31408`,
    :uv:cve:`2026-31409`, :uv:cve:`2026-31411`, :uv:cve:`2026-31412`,
    :uv:cve:`2026-31414`, :uv:cve:`2026-31415`, :uv:cve:`2026-31416`,
    :uv:cve:`2026-31417`, :uv:cve:`2026-31418`, :uv:cve:`2026-31421`,
    :uv:cve:`2026-31422`, :uv:cve:`2026-31423`, :uv:cve:`2026-31424`,
    :uv:cve:`2026-31425`, :uv:cve:`2026-31426`, :uv:cve:`2026-31427`,
    :uv:cve:`2026-31428`, :uv:cve:`2026-31431`, :uv:cve:`2026-31433`,
    :uv:cve:`2026-31434`, :uv:cve:`2026-31441`, :uv:cve:`2026-31446`,
    :uv:cve:`2026-31447`, :uv:cve:`2026-31448`, :uv:cve:`2026-31450`,
    :uv:cve:`2026-31452`, :uv:cve:`2026-31453`, :uv:cve:`2026-31454`,
    :uv:cve:`2026-31455`, :uv:cve:`2026-31464`, :uv:cve:`2026-31466`,
    :uv:cve:`2026-31467`, :uv:cve:`2026-31469`, :uv:cve:`2026-31473`,
    :uv:cve:`2026-31476`, :uv:cve:`2026-31477`, :uv:cve:`2026-31478`,
    :uv:cve:`2026-31480`, :uv:cve:`2026-31483`, :uv:cve:`2026-31485`,
    :uv:cve:`2026-31492`, :uv:cve:`2026-31494`, :uv:cve:`2026-31495`,
    :uv:cve:`2026-31496`, :uv:cve:`2026-31497`, :uv:cve:`2026-31498`,
    :uv:cve:`2026-31503`, :uv:cve:`2026-31504`, :uv:cve:`2026-31507`,
    :uv:cve:`2026-31508`, :uv:cve:`2026-31509`, :uv:cve:`2026-31510`,
    :uv:cve:`2026-31512`, :uv:cve:`2026-31515`, :uv:cve:`2026-31518`,
    :uv:cve:`2026-31519`, :uv:cve:`2026-31520`, :uv:cve:`2026-31521`,
    :uv:cve:`2026-31522`, :uv:cve:`2026-31523`, :uv:cve:`2026-31524`,
    :uv:cve:`2026-31533`, :uv:cve:`2026-31540`, :uv:cve:`2026-31545`,
    :uv:cve:`2026-31546`, :uv:cve:`2026-31548`, :uv:cve:`2026-31549`,
    :uv:cve:`2026-31550`, :uv:cve:`2026-31551`, :uv:cve:`2026-31552`,
    :uv:cve:`2026-31555`, :uv:cve:`2026-31563`, :uv:cve:`2026-31565`,
    :uv:cve:`2026-31566`, :uv:cve:`2026-31570`, :uv:cve:`2026-31628`,
    :uv:cve:`2026-31634`, :uv:cve:`2026-31649`, :uv:cve:`2026-31651`,
    :uv:cve:`2026-31656`, :uv:cve:`2026-31657`, :uv:cve:`2026-31658`,
    :uv:cve:`2026-31659`, :uv:cve:`2026-31660`, :uv:cve:`2026-31661`,
    :uv:cve:`2026-31662`, :uv:cve:`2026-31664`, :uv:cve:`2026-31665`,
    :uv:cve:`2026-31667`, :uv:cve:`2026-31668`, :uv:cve:`2026-31669`,
    :uv:cve:`2026-31670`, :uv:cve:`2026-31671`, :uv:cve:`2026-31672`,
    :uv:cve:`2026-31674`, :uv:cve:`2026-31678`, :uv:cve:`2026-31679`,
    :uv:cve:`2026-31680`, :uv:cve:`2026-31682`, :uv:cve:`2026-31683`,
    :uv:cve:`2026-31689`, :uv:cve:`2026-31695`, :uv:cve:`2026-31720`,
    :uv:cve:`2026-31721`, :uv:cve:`2026-31726`, :uv:cve:`2026-31728`,
    :uv:cve:`2026-31737`, :uv:cve:`2026-31738`, :uv:cve:`2026-31747`,
    :uv:cve:`2026-31748`, :uv:cve:`2026-31749`, :uv:cve:`2026-31751`,
    :uv:cve:`2026-31752`, :uv:cve:`2026-31754`, :uv:cve:`2026-31755`,
    :uv:cve:`2026-31756`, :uv:cve:`2026-31758`, :uv:cve:`2026-31759`,
    :uv:cve:`2026-31761`, :uv:cve:`2026-31762`, :uv:cve:`2026-31763`,
    :uv:cve:`2026-31768`, :uv:cve:`2026-31770`, :uv:cve:`2026-31773`,
    :uv:cve:`2026-31778`, :uv:cve:`2026-31779`, :uv:cve:`2026-31780`,
    :uv:cve:`2026-31781`, :uv:cve:`2026-31786`, :uv:cve:`2026-31787`,
    :uv:cve:`2026-31788`, :uv:cve:`2026-43011`, :uv:cve:`2026-43013`,
    :uv:cve:`2026-43014`, :uv:cve:`2026-43015`, :uv:cve:`2026-43017`,
    :uv:cve:`2026-43018`, :uv:cve:`2026-43020`, :uv:cve:`2026-43023`,
    :uv:cve:`2026-43024`, :uv:cve:`2026-43025`, :uv:cve:`2026-43026`,
    :uv:cve:`2026-43027`, :uv:cve:`2026-43028`, :uv:cve:`2026-43030`,
    :uv:cve:`2026-43032`, :uv:cve:`2026-43033`, :uv:cve:`2026-43035`,
    :uv:cve:`2026-43037`, :uv:cve:`2026-43038`, :uv:cve:`2026-43040`,
    :uv:cve:`2026-43041`, :uv:cve:`2026-43043`, :uv:cve:`2026-43046`,
    :uv:cve:`2026-43047`, :uv:cve:`2026-43050`, :uv:cve:`2026-43051`,
    :uv:cve:`2026-43054`, :uv:cve:`2026-43057`, :uv:cve:`2026-43284`,
    :uv:cve:`2026-43500`, :uv:cve:`2026-43503`, :uv:cve:`2026-46300`,
    :uv:cve:`2026-46333`) (:uv:bug:`59124`, :uv:bug:`59245`,
    :uv:bug:`59279`, :uv:bug:`59320`, :uv:bug:`59447`)

  * :program:`linux-signed-amd64` (:uv:cve:`2023-53228`,
    :uv:cve:`2023-53424`, :uv:cve:`2023-53510`, :uv:cve:`2023-53545`,
    :uv:cve:`2024-26822`, :uv:cve:`2024-47736`, :uv:cve:`2024-47809`,
    :uv:cve:`2024-49998`, :uv:cve:`2024-50298`, :uv:cve:`2024-56719`,
    :uv:cve:`2024-57895`, :uv:cve:`2025-21676`, :uv:cve:`2025-21682`,
    :uv:cve:`2025-22026`, :uv:cve:`2025-23155`, :uv:cve:`2025-37786`,
    :uv:cve:`2025-37920`, :uv:cve:`2025-37945`, :uv:cve:`2025-38105`,
    :uv:cve:`2025-38162`, :uv:cve:`2025-38192`, :uv:cve:`2025-38201`,
    :uv:cve:`2025-38250`, :uv:cve:`2025-38303`, :uv:cve:`2025-38643`,
    :uv:cve:`2025-38659`, :uv:cve:`2025-38704`, :uv:cve:`2025-39748`,
    :uv:cve:`2025-39763`, :uv:cve:`2025-39764`, :uv:cve:`2025-39863`,
    :uv:cve:`2025-40005`, :uv:cve:`2025-40082`, :uv:cve:`2025-40135`,
    :uv:cve:`2025-40242`, :uv:cve:`2025-40251`, :uv:cve:`2025-40261`,
    :uv:cve:`2025-68206`, :uv:cve:`2025-68239`, :uv:cve:`2025-68265`,
    :uv:cve:`2025-68358`, :uv:cve:`2025-71067`, :uv:cve:`2025-71089`,
    :uv:cve:`2025-71144`, :uv:cve:`2025-71161`, :uv:cve:`2025-71221`,
    :uv:cve:`2025-71232`, :uv:cve:`2025-71233`, :uv:cve:`2025-71235`,
    :uv:cve:`2025-71236`, :uv:cve:`2025-71237`, :uv:cve:`2025-71269`,
    :uv:cve:`2026-23100`, :uv:cve:`2026-23111`, :uv:cve:`2026-23112`,
    :uv:cve:`2026-23113`, :uv:cve:`2026-23141`, :uv:cve:`2026-23154`,
    :uv:cve:`2026-23157`, :uv:cve:`2026-23169`, :uv:cve:`2026-23204`,
    :uv:cve:`2026-23220`, :uv:cve:`2026-23221`, :uv:cve:`2026-23222`,
    :uv:cve:`2026-23227`, :uv:cve:`2026-23228`, :uv:cve:`2026-23229`,
    :uv:cve:`2026-23230`, :uv:cve:`2026-23231`, :uv:cve:`2026-23245`,
    :uv:cve:`2026-23253`, :uv:cve:`2026-23270`, :uv:cve:`2026-23274`,
    :uv:cve:`2026-23277`, :uv:cve:`2026-23279`, :uv:cve:`2026-23281`,
    :uv:cve:`2026-23284`, :uv:cve:`2026-23286`, :uv:cve:`2026-23287`,
    :uv:cve:`2026-23290`, :uv:cve:`2026-23291`, :uv:cve:`2026-23292`,
    :uv:cve:`2026-23293`, :uv:cve:`2026-23296`, :uv:cve:`2026-23298`,
    :uv:cve:`2026-23300`, :uv:cve:`2026-23303`, :uv:cve:`2026-23304`,
    :uv:cve:`2026-23306`, :uv:cve:`2026-23309`, :uv:cve:`2026-23312`,
    :uv:cve:`2026-23315`, :uv:cve:`2026-23317`, :uv:cve:`2026-23318`,
    :uv:cve:`2026-23319`, :uv:cve:`2026-23324`, :uv:cve:`2026-23335`,
    :uv:cve:`2026-23336`, :uv:cve:`2026-23339`, :uv:cve:`2026-23343`,
    :uv:cve:`2026-23351`, :uv:cve:`2026-23352`, :uv:cve:`2026-23356`,
    :uv:cve:`2026-23357`, :uv:cve:`2026-23359`, :uv:cve:`2026-23360`,
    :uv:cve:`2026-23362`, :uv:cve:`2026-23364`, :uv:cve:`2026-23365`,
    :uv:cve:`2026-23367`, :uv:cve:`2026-23368`, :uv:cve:`2026-23370`,
    :uv:cve:`2026-23372`, :uv:cve:`2026-23378`, :uv:cve:`2026-23379`,
    :uv:cve:`2026-23381`, :uv:cve:`2026-23382`, :uv:cve:`2026-23388`,
    :uv:cve:`2026-23391`, :uv:cve:`2026-23392`, :uv:cve:`2026-23395`,
    :uv:cve:`2026-23396`, :uv:cve:`2026-23397`, :uv:cve:`2026-23398`,
    :uv:cve:`2026-23401`, :uv:cve:`2026-23414`, :uv:cve:`2026-31431`,
    :uv:cve:`2026-31628`, :uv:cve:`2026-31786`, :uv:cve:`2026-31787`,
    :uv:cve:`2026-31788`, :uv:cve:`2026-43284`, :uv:cve:`2026-43500`,
    :uv:cve:`2026-43503`, :uv:cve:`2026-46300`, :uv:cve:`2026-46333`)
    (:uv:bug:`59124`, :uv:bug:`59245`, :uv:bug:`59279`,
    :uv:bug:`59320`, :uv:bug:`59447`)

  * :program:`nghttp2` (:uv:cve:`2026-27135`) (:uv:bug:`59295`)

  * :program:`nss` (:uv:cve:`2026-2781`) (:uv:bug:`59123`)

  * :program:`ntfs-3g` (:uv:cve:`2026-40706`) (:uv:bug:`59228`)

  * :program:`openjdk-17` (:uv:cve:`2026-21925`, :uv:cve:`2026-21932`,
    :uv:cve:`2026-21933`, :uv:cve:`2026-21945`, :uv:cve:`2026-22007`,
    :uv:cve:`2026-22013`, :uv:cve:`2026-22016`, :uv:cve:`2026-22018`,
    :uv:cve:`2026-22021`, :uv:cve:`2026-23865`, :uv:cve:`2026-34268`,
    :uv:cve:`2026-34282`) (:uv:bug:`59247`)

  * :program:`openjpeg2` (:uv:cve:`2026-6192`) (:uv:bug:`59314`)

  * :program:`openssh` (:uv:cve:`2025-61984`, :uv:cve:`2025-61985`,
    :uv:cve:`2026-3497`, :uv:cve:`2026-35385`, :uv:cve:`2026-35386`,
    :uv:cve:`2026-35387`, :uv:cve:`2026-35388`, :uv:cve:`2026-35414`)
    (:uv:bug:`59184`, :uv:bug:`59288`)

  * :program:`openssl` (:uv:cve:`2026-28387`, :uv:cve:`2026-28388`,
    :uv:cve:`2026-28389`, :uv:cve:`2026-28390`, :uv:cve:`2026-31789`,
    :uv:cve:`2026-31790`) (:uv:bug:`59185`, :uv:bug:`59318`)

  * :program:`postgresql-15` (:uv:cve:`2026-2006`,
    :uv:cve:`2026-6472`, :uv:cve:`2026-6473`, :uv:cve:`2026-6474`,
    :uv:cve:`2026-6475`, :uv:cve:`2026-6477`, :uv:cve:`2026-6478`,
    :uv:cve:`2026-6479`, :uv:cve:`2026-6637`) (:uv:bug:`59297`)

  * :program:`pyasn1` (:uv:cve:`2026-30922`) (:uv:bug:`59164`)

  * :program:`pyjwt` (:uv:cve:`2026-32597`) (:uv:bug:`59269`)

  * :program:`python-ldap` (:uv:cve:`2025-61911`,
    :uv:cve:`2025-61912`) (:uv:bug:`59106`)

  * :program:`python-tornado` (:uv:cve:`2025-67724`,
    :uv:cve:`2025-67725`, :uv:cve:`2025-67726`) (:uv:bug:`59166`)

  * :program:`python3.11` (:uv:cve:`2025-11468`, :uv:cve:`2025-12084`,
    :uv:cve:`2025-13836`, :uv:cve:`2025-13837`, :uv:cve:`2025-15282`,
    :uv:cve:`2025-4516`, :uv:cve:`2025-6069`, :uv:cve:`2025-6075`,
    :uv:cve:`2025-8194`, :uv:cve:`2025-8291`, :uv:cve:`2026-0672`,
    :uv:cve:`2026-0865`, :uv:cve:`2026-1299`) (:uv:bug:`59286`)

  * :program:`rsync` (:uv:cve:`2026-29518`, :uv:cve:`2026-43617`,
    :uv:cve:`2026-43618`, :uv:cve:`2026-43619`, :uv:cve:`2026-43620`)
    (:uv:bug:`59436`)

  * :program:`samba` (:uv:cve:`2026-1933`, :uv:cve:`2026-2340`,
    :uv:cve:`2026-3012`, :uv:cve:`2026-3238`, :uv:cve:`2026-4408`,
    :uv:cve:`2026-4480`) (:uv:bug:`59161`, :uv:bug:`59259`)

  * :program:`sed` (:uv:cve:`2026-5958`) (:uv:bug:`59315`)

  * :program:`sudo` (:uv:cve:`2026-35535`) (:uv:bug:`59313`)

  * :program:`systemd` (:uv:cve:`2026-29111`, :uv:cve:`2026-40225`,
    :uv:cve:`2026-40226`, :uv:cve:`2026-4105`) (:uv:bug:`59311`)

  * :program:`tiff` (:uv:cve:`2026-4775`) (:uv:bug:`59183`)

  * :program:`xorg-server` (:uv:cve:`2026-33999`,
    :uv:cve:`2026-34000`, :uv:cve:`2026-34001`, :uv:cve:`2026-34002`,
    :uv:cve:`2026-34003`) (:uv:bug:`59312`)

  * :program:`zvbi` (:uv:cve:`2025-2173`, :uv:cve:`2025-2174`,
    :uv:cve:`2025-2175`, :uv:cve:`2025-2176`, :uv:cve:`2025-2177`)
    (:uv:bug:`59307`)


.. _debian:

* |UCSUCS| |release| includes the following updated packages from Debian 12.14:

  * :program:`7zip`
  * :program:`arduino-core-avr`
  * :program:`augeas`
  * :program:`awstats`
  * :program:`bash`
  * :program:`base-files`
  * :program:`c3p0`
  * :program:`calibre`
  * :program:`cdebootstrap`
  * :program:`chkrootkit`
  * :program:`chromium`
  * :program:`chrony`
  * :program:`composer`
  * :program:`corosync`
  * :program:`dar`
  * :program:`debian-installer-netboot-images`
  * :program:`debsig-verify`
  * :program:`deets`
  * :program:`distro-info-data`
  * :program:`dnsmasq`
  * :program:`docker.io`
  * :program:`erlang`
  * :program:`evince`
  * :program:`exim4`
  * :program:`ffmpeg`
  * :program:`flatpak`
  * :program:`fonttools`
  * :program:`gimp`
  * :program:`glance`
  * :program:`gnuais`
  * :program:`golang-github-containerd-stargz-snapshotter`
  * :program:`golang-github-containers-buildah`
  * :program:`golang-github-openshift-imagebuilder`
  * :program:`gpsd`
  * :program:`gsasl`
  * :program:`gst-plugins-bad1.0`
  * :program:`gst-plugins-base1.0`
  * :program:`gst-plugins-ugly1.0`
  * :program:`gvfs`
  * :program:`jtreg7`
  * :program:`kdenlive`
  * :program:`kissfft`
  * :program:`kpackage`
  * :program:`lemonldap-ng`
  * :program:`libpod`
  * :program:`libreoffice`
  * :program:`libreoffice-texmaths`
  * :program:`libuev`
  * :program:`libvncserver`
  * :program:`libxml-security-java`
  * :program:`libxslt`
  * :program:`libyaml-syck-perl`
  * :program:`lxc`
  * :program:`lxd`
  * :program:`mapserver`
  * :program:`mediawiki`
  * :program:`modsecurity-crs`
  * :program:`mongo-c-driver`
  * :program:`mupdf`
  * :program:`nagios4`
  * :program:`netty`
  * :program:`nginx`
  * :program:`ngtcp2`
  * :program:`node-shell-quote`
  * :program:`nodejs`
  * :program:`opam`
  * :program:`openvpn`
  * :program:`p7zip`
  * :program:`p7zip-rar`
  * :program:`packagekit`
  * :program:`php-dompdf`
  * :program:`php-league-commonmark`
  * :program:`php-phpseclib`
  * :program:`php-phpseclib3`
  * :program:`php-symfony-contracts`
  * :program:`php-twig`
  * :program:`php8.2`
  * :program:`phpseclib`
  * :program:`plastimatch`
  * :program:`postorius`
  * :program:`proftpd-dfsg`
  * :program:`prosody`
  * :program:`pymupdf`
  * :program:`python-authlib`
  * :program:`qemu`
  * :program:`redis`
  * :program:`request-tracker5`
  * :program:`roundcube`
  * :program:`ruby-rack`
  * :program:`sash`
  * :program:`simpleeval`
  * :program:`sioyek`
  * :program:`skeema`
  * :program:`snapd`
  * :program:`starlette`
  * :program:`strongswan`
  * :program:`supermin`
  * :program:`swupdate`
  * :program:`symfony`
  * :program:`taglib`
  * :program:`thunderbird`
  * :program:`tor`
  * :program:`tpm2-pkcs11`
  * :program:`trafficserver`
  * :program:`tripwire`
  * :program:`tzdata`
  * :program:`user-mode-linux`
  * :program:`vips`
  * :program:`webkit2gtk`
  * :program:`wireless-regdb`
  * :program:`wireshark`
  * :program:`xdg-dbus-proxy`
  * :program:`yelp`
  * :program:`zsh`

.. _changelog-basic:

*********************
Basic system services
*********************

.. _changelog-basis-other:

Other system services
=====================

* The ``univentionObjectIdentifier`` is now set for all DNS, DHCP and license
  objects (:uv:bug:`58384`).

* The counts of licensed users, servers, and managed clients are now cached on
  the license object through a cron job.
  The cached numbers improve the performance during UMC startup (:uv:bug:`59060`).

* License initialization no longer resets the log level to ``ERROR``.
  As a result, the UMC UDM modules keep their log messages
  (:uv:bug:`38735`).

* The GPG signing key for UCS 5.3 has been added to the ``univention-archive-key``
  package (:uv:bug:`59471`).

.. _changelog-domain:

***************
Domain services
***************

* The ``univention-telemetry`` package has been added as a recommended dependency
  for :program:`univention-server` (:uv:bug:`59235`).

.. _changelog-domain-openldap:

OpenLDAP
========

.. _changelog-domain-openldap-replication:

Listener/Notifier domain replication
------------------------------------

* The syntax of DNs is now validated in ``univention-replicate-one``
  (:uv:bug:`33898`).

.. _changelog-udm:

LDAP Directory Manager
======================

* The ``univentionObjectIdentifier`` is now set for all DNS, DHCP and license
  objects (:uv:bug:`58384`).

* A new extended attribute hook mechanism has been added, which runs
  before and after moving an object (:uv:bug:`59111`).

* The counts of licensed users, servers, and managed clients are now cached on
  the license object through a cron job. The cached numbers improve the
  performance during UMC startup. Additionally, the obsolete License Version 1,
  Free For Personal Use Edition, Univention Corporate Clients, GPL License,
  Desktop Virtualization Services has been removed from the license evaluation
  (:uv:bug:`59060`).

* Searching in UMC modules now returns correct results regardless of whether
  automatic substring search is turned on or off. Previously, when substring
  search was deactivated, the global search and the standard properties filter didn't
  return results, due to a broken LDAP filter (:uv:bug:`59104`).

* The license interface has been extended to use the ``entryUUID`` of the license
  as fallback key ID (:uv:bug:`59176`).

* The hooks API has been extended to support ``map()`` and ``unmap()`` methods for
  extended attributes (:uv:bug:`59150`).

* The license cache is now also evaluated for unlimited licenses
  (:uv:bug:`59215`).

* The ``univentionObjectIdentifier`` and other technical information about LDAP
  operational attributes has been added to the advanced settings tab of all UDM
  modules (:uv:bug:`59217`).

* The ``unixTime`` UDM syntax is now compatible with UDM HTTP REST API
  (:uv:bug:`58211`).

* The ``users/contact`` UDM module now lets you set the ``cn`` property
  explicitly, so you can create objects deterministically.
  The UDM CLI now also displays the correct new DN after moving an object
  (:uv:bug:`59281`).

* The UDM HTTP REST API now returns HTTP 500 (Internal Server Error) instead of HTTP 400 (Bad
  Request) when concurrent modifications to the same LDAP object cause ``Type or
  value exists`` or ``No such attribute`` errors. This makes the error transparent
  to clients and allows them to retry the request (:uv:bug:`58804`).

* The UDM HTTP REST API now exposes a Prometheus-compatible metrics endpoint at
  ``/univention/udm/-/metrics``. It provides the total number of active users,
  the licensed user limit, and platform/version information for UCS and Nubus
  for Kubernetes. All metrics include a domain label and a stable domain
  identifier derived from the license key. The endpoint is restricted to
  authorized users (:uv:bug:`59176`).

* The Nubus Prometheus metrics are now consistently prefixed with ``nubus_``,
  ensuring clearer namespace separation and easier identification in monitoring
  and alerting configurations. The Nubus Prometheus metrics
  ``nubus_users_user_total`` and ``nubus_settings_license_users_limit_total`` now
  include the license key as a label, enabling per-license observability
  (:uv:bug:`59231`).

* A pre-calculated value for ``univentionObjectIdentifier`` is now hidden in the
  object template, as this might be used to create multiple objects
  (:uv:bug:`59217`).

.. _changelog-umc:

*****************************
Univention Management Console
*****************************

.. _changelog-umc-web:

Univention Management Console web interface
===========================================

* A regression has been fixed, which was introduced by updating Dojo ``dgrid`` to
  version 1.3.3 in UCS 5.3 Erratum 304 and caused the "Select All" checkbox in
  list views and the tree view in the LDAP directory to malfunction
  (:uv:bug:`59095`).

* The ``DateTime`` widget has been fixed to support all and empty date formats
  and respect the configured size (:uv:bug:`59217`).

.. _changelog-umc-server:

Univention Management Console server
====================================

* A file descriptor leak caused during PAM authentication through SSS has been
  fixed (:uv:bug:`59220`).

* The UMC server no longer accepts smuggled HTTP request headers in
  ``X-UMC-Federated-Account`` and ``X-UMC-Roles``.
  These headers handle interprocess communication between the UMC server and UMC
  module processes when delegative administration is enabled
  (:uv:bug:`59280`).

.. _changelog-umc-appcenter:

Univention App Center
=====================

* The App Center now avoids allocating Docker Compose network subnets that
  overlap with host network interfaces, preventing potential routing conflicts
  (:uv:bug:`55073`).

* Links in app descriptions and license agreements now open in a new browser
  tab instead of loading inside the App Center iframe (:uv:bug:`57501`).

.. _changelog-umc-join:

Domain join module
==================

* The version check in :program:`univention-join` used string concatenation with :program:`awk`
  numeric comparison, causing incorrect results for version numbers like 5.0-10
  vs 5.0-9. The fix uses :command:`dpkg --compare-versions` for correct Debian version
  ordering (:uv:bug:`58212`).

.. _changelog-umc-diagnostic:

System diagnostic module
========================

* A new diagnostic check warns when the Docker bridge network overlaps with a
  host network interface, which can cause routing issues (:uv:bug:`55073`).

.. _changelog-umc-ldap:

LDAP directory browser
======================

* The underlying library dependencies to handle certificates have been updated from
  ``M2Crypto`` and ``PyOpenSSL`` to ``python3-cryptography`` to ensure future
  compatibility and to fix a problem for certificate validity dates after 2050
  (:uv:bug:`55411`).

* The ``univentionObjectIdentifier`` is now set for all DNS, DHCP and license
  objects (:uv:bug:`58384`).

* The counts of licensed users, servers, and managed clients are now cached on
  the license object through a cron job.
  The cached numbers improve the performance during UMC startup (:uv:bug:`59060`).

* UDM now lets you add a property to the layout even when its default value is a
  function call.
  All UDM modules now show ``univentionObjectIdentifier`` and other technical
  information about LDAP operational attributes on the *Advanced settings* tab
  (:uv:bug:`59217`).

.. _changelog-lib:

*************************
Univention base libraries
*************************

* The ``univentionObjectIdentifier`` is now set for all DNS, DHCP and license
  objects (:uv:bug:`58384`).

* The counts of licensed users, servers, and managed clients are now cached on
  the license object through a cron job.
  The cached numbers improve the performance during UMC startup (:uv:bug:`59060`).

* The ``crudeoauth`` library has been made compatible with modern compilers
  (:uv:bug:`59470`).

* The Nagios suidwrapper has been modernized to be compatible with modern compilers
  (:uv:bug:`59469`).

.. _changelog-deployment:

*******************
Software deployment
*******************

* After a patchlevel update, UDM extensions are now automatically synchronized again to
  ensure that extensions with version constraints are correctly activated or
  deactivated for the new UCS version (:uv:bug:`59229`).

.. _changelog-service:

***************
System services
***************

.. _changelog-service-saml:

SAML
====

* Fixed a regression introduced in Keycloak 26.6.0 where a change in the
  component lookup API broke the Kerberos configuration update in the
  :program:`univention-keycloak` script (:uv:bug:`59212`).

* The package was rebuilt as part of an internal repository migration. This
  update contains no functional changes (:uv:bug:`59234`).

.. _changelog-service-mail:

Mail services
=============

* The UDM hooks have been adjusted to be compatible with delegative
  administration (:uv:bug:`59150`).

.. _changelog-service-postfix:

Postfix
-------

* Postfix LDAP group lookups now support the ``mailAlternativeAddress`` attribute
  in addition to ``mailPrimaryAddress``. This allows UDM groups to receive emails
  via alternative (alias) addresses (:uv:bug:`28692`).

.. _changelog-win:

********************
Services for Windows
********************

.. _changelog-win-samba:

Samba
=====

* Samba has been updated to version 4.24.2, including the latest security
  patches, so it's equivalent to 4.24.3 (:uv:bug:`59336`). For a full list of
  changes, see the upstream changelogs:

  * `Samba 4.22 Features added/changed <https://wiki.samba.org/index.php/Samba_4.22_Features_added/changed#Samba_4.22.0>`_
  * `Samba 4.23 Features added/changed <https://wiki.samba.org/index.php/Samba_4.23_Features_added/changed#Samba_4.23.0>`_
  * `Samba 4.24 Features added/changed <https://wiki.samba.org/index.php/Samba_4.24_Features_added/changed#Samba_4.24.0>`_

* The Group Policy Management Console was crashing sometimes when modifying the
  user permissions in the Security tab. Afterwards, the new created ACLs were
  malformed, which made the policy inaccessible. The code which parses the
  binary structures sent by the Windows client has been corrected
  (:uv:bug:`59142`).

* An uninitialized file descriptor associated with hanging ``rpcd spoolss``
  processes is now initialized (:uv:bug:`59160`).

.. _changelog-win-takeover:

Univention AD Takeover
======================

* The counts of licensed users, servers, and managed clients are now cached on
  the license object through a cron job.
  The cached numbers improve the performance during UMC startup (:uv:bug:`59060`).

.. _changelog-win-s4c:

Univention S4 Connector
=======================

* The S4 Connector no longer treats stale entries in the connector database as
  deleted objects in Active Directory.
  It now verifies that the AD object has ``isDeleted=TRUE`` before attempting a
  restore.
  This change prevents unnecessary restore attempts and synchronization rejects
  (:uv:bug:`59113`).

* The S4-Connector now removes the attribute ``dNSTombstoned`` in Samba/AD if
  a change for the corresponding DNS object is synchronized from
  OpenLDAP/UDM (:uv:bug:`57174`).

.. _changelog-win-adc:

Univention Active Directory Connection
======================================

* The :program:`Active Directory Connection` no longer treats stale entries in the
  connector database as deleted objects in Active Directory.
  It now verifies that the AD object has ``isDeleted=TRUE`` before attempting a
  restore.
  This change prevents unnecessary restore attempts and synchronization rejects
  (:uv:bug:`59113`).

* Documentation for the obsolete UCR variable
  ``connector/password/service/encoding.`` has been removed (:uv:bug:`59128`).

* The custom position mapping function of :program:`Active Directory Connection` now applies to the
  object mentioned in the mapping as well (:uv:bug:`59200`).

* As Microsoft is continuing with the deprecation of NT-hashes, see
  https://go.microsoft.com/fwlink/?linkid=2344614, the Microsoft update
  ``KB5082063`` changed the default value for ``DefaultDomainSupportedEncTypes`` to
  allow AES-SHA1 only, which blocks issuing Kerberos tickets with ``RC4`` hashes.
  The AD-Connector now implements the advice by Microsoft to set
  ``msDS-SupportedEncryptionTypes`` on a per-account basis during the sync from
  UCS to Microsoft Active Directory, to allow the Microsoft KDC to make use of the synced NT-hash. As
  Microsoft doesn't offer an RPC call to pass stronger Kerberos hashes, this
  workaround is currently necessary. When a password is changed on the Microsoft Active Directory
  side, :program:`Active Directory Connection` removes this setting again, to keep security as high as
  possible (:uv:bug:`58876`).

.. _changelog-other:

*************
Other changes
*************

* Password changes through PAM could fail in long-running processes, for example in UMC, with
  high file descriptor usage. Heimdal Kerberos previously relied on the
  ``select()`` API, which can't handle file descriptor values ≥ ``FD_SETSIZE``
  (1024). In such situations, Kerberos communication with the KDC could fail,
  leading to misleading errors such as ``Authentication token manipulation
  error``. The implementation now uses ``poll()``, eliminating this limitation and
  improving robustness in long-running services (:uv:bug:`59145`).

* The univention-telemetry package is added, which collects telemetry metrics
  from UDM HTTP REST API, anonymizes and transforms them to OTLP/JSON format and
  forwards them to Univention's telemetry receiver. The feature is turned off by
  default (:uv:bug:`59235`).

