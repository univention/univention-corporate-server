.. SPDX-FileCopyrightText: 2021-2026 Univention GmbH
..
.. SPDX-License-Identifier: AGPL-3.0-only

.. _changelog-general:

*******
General
*******

.. _security:

* |UCSUCS| |release| includes all security updates issued for UCS 5.2-4:

  * :program:`apache2` (:uv:cve:`2025-55753`, :uv:cve:`2025-58098`,
    :uv:cve:`2025-59775`, :uv:cve:`2025-65082`, :uv:cve:`2025-66200`)
    (:uv:bug:`58945`)

  * :program:`bind9` (:uv:cve:`2025-13878`) (:uv:bug:`58995`)

  * :program:`clamav` (:uv:cve:`2025-20234`) (:uv:bug:`58962`)

  * :program:`containerd` (:uv:cve:`2024-25621`, :uv:cve:`2025-64329`)
    (:uv:bug:`58893`)

  * :program:`cups-filters` (:uv:cve:`2025-57812`,
    :uv:cve:`2025-64503`, :uv:cve:`2025-64524`) (:uv:bug:`58944`)

  * :program:`ffmpeg` (:uv:cve:`2024-36618`, :uv:cve:`2025-1594`,
    :uv:cve:`2025-63757`) (:uv:bug:`58928`)

  * :program:`firefox-esr` (:uv:cve:`2025-14321`,
    :uv:cve:`2025-14322`, :uv:cve:`2025-14323`, :uv:cve:`2025-14324`,
    :uv:cve:`2025-14325`, :uv:cve:`2025-14327`, :uv:cve:`2025-14328`,
    :uv:cve:`2025-14329`, :uv:cve:`2025-14330`, :uv:cve:`2025-14331`,
    :uv:cve:`2025-14333`, :uv:cve:`2026-0877`, :uv:cve:`2026-0878`,
    :uv:cve:`2026-0879`, :uv:cve:`2026-0880`, :uv:cve:`2026-0882`,
    :uv:cve:`2026-0883`, :uv:cve:`2026-0884`, :uv:cve:`2026-0885`,
    :uv:cve:`2026-0886`, :uv:cve:`2026-0887`, :uv:cve:`2026-0890`,
    :uv:cve:`2026-0891`) (:uv:bug:`58901`, :uv:bug:`58983`)

  * :program:`gdk-pixbuf` (:uv:cve:`2025-7345`) (:uv:bug:`58957`)

  * :program:`git` (:uv:cve:`2025-27613`, :uv:cve:`2025-46835`,
    :uv:cve:`2025-48384`, :uv:cve:`2025-48385`) (:uv:bug:`58951`)

  * :program:`glib2.0` (:uv:cve:`2025-13601`, :uv:cve:`2025-14087`,
    :uv:cve:`2025-14512`) (:uv:bug:`58952`)

  * :program:`gnupg2` (:uv:cve:`2025-68973`) (:uv:bug:`58958`)

  * :program:`gnutls28` (:uv:cve:`2025-14831`, :uv:cve:`2025-9820`)
    (:uv:bug:`59066`)

  * :program:`imagemagick` (:uv:cve:`2025-57803`,
    :uv:cve:`2025-62171`, :uv:cve:`2025-65955`, :uv:cve:`2025-66628`,
    :uv:cve:`2025-68469`, :uv:cve:`2025-68618`, :uv:cve:`2025-68950`,
    :uv:cve:`2025-69204`, :uv:cve:`2026-23874`, :uv:cve:`2026-23876`,
    :uv:cve:`2026-23952`) (:uv:bug:`58947`, :uv:bug:`59014`)

  * :program:`inetutils` (:uv:cve:`2026-24061`) (:uv:bug:`59004`)

  * :program:`libpng1.6` (:uv:cve:`2025-64505`, :uv:cve:`2025-64506`,
    :uv:cve:`2025-64720`, :uv:cve:`2025-65018`, :uv:cve:`2025-66293`,
    :uv:cve:`2026-22695`, :uv:cve:`2026-22801`, :uv:cve:`2026-25646`)
    (:uv:bug:`58902`, :uv:bug:`59065`)

  * :program:`libsodium` (:uv:cve:`2025-69277`) (:uv:bug:`58949`)

  * :program:`libssh` (:uv:cve:`2025-4877`, :uv:cve:`2025-4878`,
    :uv:cve:`2025-5318`, :uv:cve:`2025-5351`, :uv:cve:`2025-5372`,
    :uv:cve:`2025-5987`, :uv:cve:`2025-8114`, :uv:cve:`2025-8277`)
    (:uv:bug:`58948`)

  * :program:`libvpx` (:uv:cve:`2026-1861`, :uv:cve:`2026-2447`)
    (:uv:bug:`59067`)

  * :program:`libxml2` (:uv:cve:`2025-7425`, :uv:cve:`2025-9714`)
    (:uv:bug:`58963`)

  * :program:`linux` (:uv:cve:`2023-52658`, :uv:cve:`2023-53421`,
    :uv:cve:`2023-54285`, :uv:cve:`2024-42079`, :uv:cve:`2024-46786`,
    :uv:cve:`2024-49968`, :uv:cve:`2025-21946`, :uv:cve:`2025-22022`,
    :uv:cve:`2025-22083`, :uv:cve:`2025-22090`, :uv:cve:`2025-22107`,
    :uv:cve:`2025-22111`, :uv:cve:`2025-22121`, :uv:cve:`2025-37899`,
    :uv:cve:`2025-37926`, :uv:cve:`2025-38022`, :uv:cve:`2025-38057`,
    :uv:cve:`2025-38073`, :uv:cve:`2025-38104`, :uv:cve:`2025-38125`,
    :uv:cve:`2025-38129`, :uv:cve:`2025-38232`, :uv:cve:`2025-38361`,
    :uv:cve:`2025-38408`, :uv:cve:`2025-38591`, :uv:cve:`2025-38678`,
    :uv:cve:`2025-38718`, :uv:cve:`2025-39721`, :uv:cve:`2025-39805`,
    :uv:cve:`2025-39871`, :uv:cve:`2025-40039`, :uv:cve:`2025-40083`,
    :uv:cve:`2025-40110`, :uv:cve:`2025-40149`, :uv:cve:`2025-40164`,
    :uv:cve:`2025-40211`, :uv:cve:`2025-40214`, :uv:cve:`2025-40215`,
    :uv:cve:`2025-40253`, :uv:cve:`2025-40254`, :uv:cve:`2025-40257`,
    :uv:cve:`2025-40258`, :uv:cve:`2025-40259`, :uv:cve:`2025-40261`,
    :uv:cve:`2025-40262`, :uv:cve:`2025-40263`, :uv:cve:`2025-40264`,
    :uv:cve:`2025-40269`, :uv:cve:`2025-40271`, :uv:cve:`2025-40272`,
    :uv:cve:`2025-40273`, :uv:cve:`2025-40275`, :uv:cve:`2025-40277`,
    :uv:cve:`2025-40278`, :uv:cve:`2025-40279`, :uv:cve:`2025-40280`,
    :uv:cve:`2025-40281`, :uv:cve:`2025-40282`, :uv:cve:`2025-40283`,
    :uv:cve:`2025-40284`, :uv:cve:`2025-40285`, :uv:cve:`2025-40286`,
    :uv:cve:`2025-40288`, :uv:cve:`2025-40292`, :uv:cve:`2025-40293`,
    :uv:cve:`2025-40294`, :uv:cve:`2025-40297`, :uv:cve:`2025-40301`,
    :uv:cve:`2025-40304`, :uv:cve:`2025-40306`, :uv:cve:`2025-40308`,
    :uv:cve:`2025-40309`, :uv:cve:`2025-40312`, :uv:cve:`2025-40314`,
    :uv:cve:`2025-40315`, :uv:cve:`2025-40317`, :uv:cve:`2025-40318`,
    :uv:cve:`2025-40319`, :uv:cve:`2025-40321`, :uv:cve:`2025-40322`,
    :uv:cve:`2025-40324`, :uv:cve:`2025-40331`, :uv:cve:`2025-40341`,
    :uv:cve:`2025-40342`, :uv:cve:`2025-40343`, :uv:cve:`2025-68211`,
    :uv:cve:`2025-68223`, :uv:cve:`2025-68254`, :uv:cve:`2025-68255`,
    :uv:cve:`2025-68256`, :uv:cve:`2025-68257`, :uv:cve:`2025-68258`,
    :uv:cve:`2025-68259`, :uv:cve:`2025-68261`, :uv:cve:`2025-68263`,
    :uv:cve:`2025-68264`, :uv:cve:`2025-68266`, :uv:cve:`2025-68291`,
    :uv:cve:`2025-68325`, :uv:cve:`2025-68332`, :uv:cve:`2025-68335`,
    :uv:cve:`2025-68336`, :uv:cve:`2025-68337`, :uv:cve:`2025-68340`,
    :uv:cve:`2025-68344`, :uv:cve:`2025-68345`, :uv:cve:`2025-68346`,
    :uv:cve:`2025-68347`, :uv:cve:`2025-68349`, :uv:cve:`2025-68354`,
    :uv:cve:`2025-68362`, :uv:cve:`2025-68363`, :uv:cve:`2025-68364`,
    :uv:cve:`2025-68365`, :uv:cve:`2025-68366`, :uv:cve:`2025-68367`,
    :uv:cve:`2025-68369`, :uv:cve:`2025-68371`, :uv:cve:`2025-68372`,
    :uv:cve:`2025-68380`, :uv:cve:`2025-68724`, :uv:cve:`2025-68725`,
    :uv:cve:`2025-68727`, :uv:cve:`2025-68728`, :uv:cve:`2025-68732`,
    :uv:cve:`2025-68733`, :uv:cve:`2025-68740`, :uv:cve:`2025-68742`,
    :uv:cve:`2025-68746`, :uv:cve:`2025-68753`, :uv:cve:`2025-68757`,
    :uv:cve:`2025-68758`, :uv:cve:`2025-68759`, :uv:cve:`2025-68764`,
    :uv:cve:`2025-68765`, :uv:cve:`2025-68766`, :uv:cve:`2025-68767`,
    :uv:cve:`2025-68769`, :uv:cve:`2025-68771`, :uv:cve:`2025-68772`,
    :uv:cve:`2025-68773`, :uv:cve:`2025-68774`, :uv:cve:`2025-68776`,
    :uv:cve:`2025-68777`, :uv:cve:`2025-68778`, :uv:cve:`2025-68780`,
    :uv:cve:`2025-68781`, :uv:cve:`2025-68782`, :uv:cve:`2025-68783`,
    :uv:cve:`2025-68785`, :uv:cve:`2025-68786`, :uv:cve:`2025-68787`,
    :uv:cve:`2025-68788`, :uv:cve:`2025-68789`, :uv:cve:`2025-68795`,
    :uv:cve:`2025-68796`, :uv:cve:`2025-68797`, :uv:cve:`2025-68798`,
    :uv:cve:`2025-68799`, :uv:cve:`2025-68800`, :uv:cve:`2025-68801`,
    :uv:cve:`2025-68803`, :uv:cve:`2025-68804`, :uv:cve:`2025-68806`,
    :uv:cve:`2025-68808`, :uv:cve:`2025-68813`, :uv:cve:`2025-68814`,
    :uv:cve:`2025-68815`, :uv:cve:`2025-68816`, :uv:cve:`2025-68817`,
    :uv:cve:`2025-68818`, :uv:cve:`2025-68819`, :uv:cve:`2025-68820`,
    :uv:cve:`2025-68821`, :uv:cve:`2025-71064`, :uv:cve:`2025-71066`,
    :uv:cve:`2025-71069`, :uv:cve:`2025-71071`, :uv:cve:`2025-71075`,
    :uv:cve:`2025-71077`, :uv:cve:`2025-71078`, :uv:cve:`2025-71079`,
    :uv:cve:`2025-71081`, :uv:cve:`2025-71082`, :uv:cve:`2025-71083`,
    :uv:cve:`2025-71084`, :uv:cve:`2025-71085`, :uv:cve:`2025-71086`,
    :uv:cve:`2025-71087`, :uv:cve:`2025-71088`, :uv:cve:`2025-71091`,
    :uv:cve:`2025-71093`, :uv:cve:`2025-71094`, :uv:cve:`2025-71095`,
    :uv:cve:`2025-71096`, :uv:cve:`2025-71097`, :uv:cve:`2025-71098`,
    :uv:cve:`2025-71102`, :uv:cve:`2025-71104`, :uv:cve:`2025-71105`,
    :uv:cve:`2025-71108`, :uv:cve:`2025-71111`, :uv:cve:`2025-71112`,
    :uv:cve:`2025-71113`, :uv:cve:`2025-71114`, :uv:cve:`2025-71116`,
    :uv:cve:`2025-71118`, :uv:cve:`2025-71119`, :uv:cve:`2025-71120`,
    :uv:cve:`2025-71121`, :uv:cve:`2025-71123`, :uv:cve:`2025-71125`,
    :uv:cve:`2025-71126`, :uv:cve:`2025-71127`, :uv:cve:`2025-71130`,
    :uv:cve:`2025-71131`, :uv:cve:`2025-71132`, :uv:cve:`2025-71133`,
    :uv:cve:`2025-71136`, :uv:cve:`2025-71137`, :uv:cve:`2025-71147`,
    :uv:cve:`2025-71149`, :uv:cve:`2025-71150`, :uv:cve:`2025-71154`,
    :uv:cve:`2025-71162`, :uv:cve:`2025-71163`, :uv:cve:`2025-71180`,
    :uv:cve:`2025-71182`, :uv:cve:`2025-71183`, :uv:cve:`2025-71185`,
    :uv:cve:`2025-71186`, :uv:cve:`2025-71189`, :uv:cve:`2025-71190`,
    :uv:cve:`2025-71191`, :uv:cve:`2025-71192`, :uv:cve:`2025-71194`,
    :uv:cve:`2025-71196`, :uv:cve:`2025-71197`, :uv:cve:`2025-71199`,
    :uv:cve:`2026-22976`, :uv:cve:`2026-22977`, :uv:cve:`2026-22978`,
    :uv:cve:`2026-22979`, :uv:cve:`2026-22980`, :uv:cve:`2026-22982`,
    :uv:cve:`2026-22984`, :uv:cve:`2026-22990`, :uv:cve:`2026-22991`,
    :uv:cve:`2026-22992`, :uv:cve:`2026-22994`, :uv:cve:`2026-22997`,
    :uv:cve:`2026-22998`, :uv:cve:`2026-22999`, :uv:cve:`2026-23001`,
    :uv:cve:`2026-23003`, :uv:cve:`2026-23005`, :uv:cve:`2026-23006`,
    :uv:cve:`2026-23010`, :uv:cve:`2026-23011`, :uv:cve:`2026-23019`,
    :uv:cve:`2026-23020`, :uv:cve:`2026-23021`, :uv:cve:`2026-23025`,
    :uv:cve:`2026-23026`, :uv:cve:`2026-23030`, :uv:cve:`2026-23031`,
    :uv:cve:`2026-23033`, :uv:cve:`2026-23037`, :uv:cve:`2026-23038`,
    :uv:cve:`2026-23047`, :uv:cve:`2026-23049`, :uv:cve:`2026-23054`,
    :uv:cve:`2026-23056`, :uv:cve:`2026-23058`, :uv:cve:`2026-23060`,
    :uv:cve:`2026-23061`, :uv:cve:`2026-23063`, :uv:cve:`2026-23064`,
    :uv:cve:`2026-23068`, :uv:cve:`2026-23069`, :uv:cve:`2026-23071`,
    :uv:cve:`2026-23073`, :uv:cve:`2026-23074`, :uv:cve:`2026-23075`,
    :uv:cve:`2026-23076`, :uv:cve:`2026-23078`, :uv:cve:`2026-23080`,
    :uv:cve:`2026-23083`, :uv:cve:`2026-23084`, :uv:cve:`2026-23085`,
    :uv:cve:`2026-23086`, :uv:cve:`2026-23087`, :uv:cve:`2026-23089`,
    :uv:cve:`2026-23090`, :uv:cve:`2026-23091`, :uv:cve:`2026-23093`,
    :uv:cve:`2026-23095`, :uv:cve:`2026-23096`, :uv:cve:`2026-23097`,
    :uv:cve:`2026-23098`, :uv:cve:`2026-23099`, :uv:cve:`2026-23101`,
    :uv:cve:`2026-23102`, :uv:cve:`2026-23103`, :uv:cve:`2026-23105`,
    :uv:cve:`2026-23107`, :uv:cve:`2026-23108`, :uv:cve:`2026-23110`)
    (:uv:bug:`58964`, :uv:bug:`59049`)

  * :program:`linux-signed-amd64` (:uv:cve:`2023-52658`,
    :uv:cve:`2023-53421`, :uv:cve:`2023-54285`, :uv:cve:`2024-42079`,
    :uv:cve:`2024-46786`, :uv:cve:`2024-49968`, :uv:cve:`2025-21946`,
    :uv:cve:`2025-22022`, :uv:cve:`2025-22083`, :uv:cve:`2025-22107`,
    :uv:cve:`2025-22111`, :uv:cve:`2025-37899`, :uv:cve:`2025-37926`,
    :uv:cve:`2025-38022`, :uv:cve:`2025-38057`, :uv:cve:`2025-38073`,
    :uv:cve:`2025-38104`, :uv:cve:`2025-38125`, :uv:cve:`2025-38129`,
    :uv:cve:`2025-38232`, :uv:cve:`2025-38361`, :uv:cve:`2025-38408`,
    :uv:cve:`2025-38591`, :uv:cve:`2025-38678`, :uv:cve:`2025-38718`,
    :uv:cve:`2025-39721`, :uv:cve:`2025-39805`, :uv:cve:`2025-39871`,
    :uv:cve:`2025-40039`, :uv:cve:`2025-40083`, :uv:cve:`2025-40110`,
    :uv:cve:`2025-40211`, :uv:cve:`2025-40214`, :uv:cve:`2025-40215`,
    :uv:cve:`2025-40253`, :uv:cve:`2025-40254`, :uv:cve:`2025-40257`,
    :uv:cve:`2025-40258`, :uv:cve:`2025-40259`, :uv:cve:`2025-40261`,
    :uv:cve:`2025-40262`, :uv:cve:`2025-40263`, :uv:cve:`2025-40264`,
    :uv:cve:`2025-40269`, :uv:cve:`2025-40271`, :uv:cve:`2025-40272`,
    :uv:cve:`2025-40273`, :uv:cve:`2025-40275`, :uv:cve:`2025-40277`,
    :uv:cve:`2025-40278`, :uv:cve:`2025-40279`, :uv:cve:`2025-40280`,
    :uv:cve:`2025-40281`, :uv:cve:`2025-40282`, :uv:cve:`2025-40283`,
    :uv:cve:`2025-40284`, :uv:cve:`2025-40285`, :uv:cve:`2025-40286`,
    :uv:cve:`2025-40288`, :uv:cve:`2025-40292`, :uv:cve:`2025-40293`,
    :uv:cve:`2025-40294`, :uv:cve:`2025-40297`, :uv:cve:`2025-40301`,
    :uv:cve:`2025-40304`, :uv:cve:`2025-40306`, :uv:cve:`2025-40308`,
    :uv:cve:`2025-40309`, :uv:cve:`2025-40312`, :uv:cve:`2025-40314`,
    :uv:cve:`2025-40315`, :uv:cve:`2025-40317`, :uv:cve:`2025-40318`,
    :uv:cve:`2025-40319`, :uv:cve:`2025-40321`, :uv:cve:`2025-40322`,
    :uv:cve:`2025-40324`, :uv:cve:`2025-40331`, :uv:cve:`2025-40341`,
    :uv:cve:`2025-40342`, :uv:cve:`2025-40343`, :uv:cve:`2025-68223`,
    :uv:cve:`2025-68254`, :uv:cve:`2025-68255`, :uv:cve:`2025-68257`,
    :uv:cve:`2025-68258`, :uv:cve:`2025-68259`, :uv:cve:`2025-68261`,
    :uv:cve:`2025-68263`, :uv:cve:`2025-68264`, :uv:cve:`2025-68266`,
    :uv:cve:`2025-68325`, :uv:cve:`2025-68332`, :uv:cve:`2025-68335`,
    :uv:cve:`2025-68336`, :uv:cve:`2025-68340`, :uv:cve:`2025-68344`,
    :uv:cve:`2025-68345`, :uv:cve:`2025-68346`, :uv:cve:`2025-68347`,
    :uv:cve:`2025-68349`, :uv:cve:`2025-68354`, :uv:cve:`2025-68362`,
    :uv:cve:`2025-68363`, :uv:cve:`2025-68365`, :uv:cve:`2025-68366`,
    :uv:cve:`2025-68367`, :uv:cve:`2025-68369`, :uv:cve:`2025-68371`,
    :uv:cve:`2025-68372`, :uv:cve:`2025-68380`, :uv:cve:`2025-68724`,
    :uv:cve:`2025-68725`, :uv:cve:`2025-68727`, :uv:cve:`2025-68728`,
    :uv:cve:`2025-68732`, :uv:cve:`2025-68733`, :uv:cve:`2025-68740`,
    :uv:cve:`2025-68742`, :uv:cve:`2025-68746`, :uv:cve:`2025-68753`,
    :uv:cve:`2025-68757`, :uv:cve:`2025-68758`, :uv:cve:`2025-68759`,
    :uv:cve:`2025-68764`, :uv:cve:`2025-68765`, :uv:cve:`2025-68766`,
    :uv:cve:`2025-68767`, :uv:cve:`2025-68769`, :uv:cve:`2025-68771`,
    :uv:cve:`2025-68772`, :uv:cve:`2025-68773`, :uv:cve:`2025-68776`,
    :uv:cve:`2025-68777`, :uv:cve:`2025-68778`, :uv:cve:`2025-68780`,
    :uv:cve:`2025-68781`, :uv:cve:`2025-68782`, :uv:cve:`2025-68783`,
    :uv:cve:`2025-68786`, :uv:cve:`2025-68787`, :uv:cve:`2025-68788`,
    :uv:cve:`2025-68795`, :uv:cve:`2025-68796`, :uv:cve:`2025-68797`,
    :uv:cve:`2025-68798`, :uv:cve:`2025-68799`, :uv:cve:`2025-68800`,
    :uv:cve:`2025-68801`, :uv:cve:`2025-68803`, :uv:cve:`2025-68804`,
    :uv:cve:`2025-68806`, :uv:cve:`2025-68808`, :uv:cve:`2025-68813`,
    :uv:cve:`2025-68814`, :uv:cve:`2025-68815`, :uv:cve:`2025-68816`,
    :uv:cve:`2025-68817`, :uv:cve:`2025-68818`, :uv:cve:`2025-68819`,
    :uv:cve:`2025-68820`, :uv:cve:`2025-68821`, :uv:cve:`2025-71064`,
    :uv:cve:`2025-71066`, :uv:cve:`2025-71069`, :uv:cve:`2025-71075`,
    :uv:cve:`2025-71077`, :uv:cve:`2025-71078`, :uv:cve:`2025-71079`,
    :uv:cve:`2025-71081`, :uv:cve:`2025-71082`, :uv:cve:`2025-71083`,
    :uv:cve:`2025-71084`, :uv:cve:`2025-71086`, :uv:cve:`2025-71087`,
    :uv:cve:`2025-71088`, :uv:cve:`2025-71091`, :uv:cve:`2025-71093`,
    :uv:cve:`2025-71094`, :uv:cve:`2025-71095`, :uv:cve:`2025-71096`,
    :uv:cve:`2025-71097`, :uv:cve:`2025-71102`, :uv:cve:`2025-71104`,
    :uv:cve:`2025-71105`, :uv:cve:`2025-71108`, :uv:cve:`2025-71112`,
    :uv:cve:`2025-71113`, :uv:cve:`2025-71114`, :uv:cve:`2025-71118`,
    :uv:cve:`2025-71119`, :uv:cve:`2025-71120`, :uv:cve:`2025-71121`,
    :uv:cve:`2025-71123`, :uv:cve:`2025-71125`, :uv:cve:`2025-71126`,
    :uv:cve:`2025-71127`, :uv:cve:`2025-71130`, :uv:cve:`2025-71131`,
    :uv:cve:`2025-71132`, :uv:cve:`2025-71133`, :uv:cve:`2025-71136`,
    :uv:cve:`2025-71162`, :uv:cve:`2025-71163`, :uv:cve:`2025-71185`,
    :uv:cve:`2025-71186`, :uv:cve:`2025-71188`, :uv:cve:`2025-71189`,
    :uv:cve:`2025-71190`, :uv:cve:`2025-71191`, :uv:cve:`2025-71196`,
    :uv:cve:`2025-71197`, :uv:cve:`2025-71199`, :uv:cve:`2026-22998`,
    :uv:cve:`2026-22999`, :uv:cve:`2026-23001`, :uv:cve:`2026-23006`,
    :uv:cve:`2026-23010`, :uv:cve:`2026-23025`, :uv:cve:`2026-23026`,
    :uv:cve:`2026-23030`, :uv:cve:`2026-23033`, :uv:cve:`2026-23038`,
    :uv:cve:`2026-23049`, :uv:cve:`2026-23054`, :uv:cve:`2026-23056`,
    :uv:cve:`2026-23063`, :uv:cve:`2026-23064`, :uv:cve:`2026-23068`,
    :uv:cve:`2026-23069`, :uv:cve:`2026-23071`, :uv:cve:`2026-23073`,
    :uv:cve:`2026-23074`, :uv:cve:`2026-23076`, :uv:cve:`2026-23078`,
    :uv:cve:`2026-23083`, :uv:cve:`2026-23084`, :uv:cve:`2026-23085`,
    :uv:cve:`2026-23086`, :uv:cve:`2026-23087`, :uv:cve:`2026-23089`,
    :uv:cve:`2026-23090`, :uv:cve:`2026-23091`, :uv:cve:`2026-23095`,
    :uv:cve:`2026-23096`, :uv:cve:`2026-23097`, :uv:cve:`2026-23098`,
    :uv:cve:`2026-23099`, :uv:cve:`2026-23101`, :uv:cve:`2026-23102`,
    :uv:cve:`2026-23103`, :uv:cve:`2026-23105`, :uv:cve:`2026-23107`,
    :uv:cve:`2026-23110`) (:uv:bug:`58964`, :uv:bug:`59049`)

  * :program:`net-snmp` (:uv:cve:`2025-68615`) (:uv:bug:`58965`)

  * :program:`nvidia-graphics-drivers` (:uv:cve:`2025-23279`,
    :uv:cve:`2025-23286`) (:uv:bug:`58966`)

  * :program:`openjdk-17` (:uv:cve:`2025-53057`, :uv:cve:`2025-53066`,
    :uv:cve:`2026-21925`, :uv:cve:`2026-21932`, :uv:cve:`2026-21933`,
    :uv:cve:`2026-21945`) (:uv:bug:`58994`)

  * :program:`openssl` (:uv:cve:`2025-15467`, :uv:cve:`2025-68160`,
    :uv:cve:`2025-69418`, :uv:cve:`2025-69419`, :uv:cve:`2025-69420`,
    :uv:cve:`2025-69421`, :uv:cve:`2026-22795`, :uv:cve:`2026-22796`)
    (:uv:bug:`59016`)

  * :program:`postgresql-15` (:uv:cve:`2025-12817`,
    :uv:cve:`2025-12818`, :uv:cve:`2026-2003`, :uv:cve:`2026-2004`,
    :uv:cve:`2026-2005`, :uv:cve:`2026-2006`) (:uv:bug:`58954`,
    :uv:bug:`59052`)

  * :program:`pyasn1` (:uv:cve:`2026-23490`) (:uv:bug:`59015`)

  * :program:`python-urllib3` (:uv:cve:`2025-50181`,
    :uv:cve:`2025-66418`, :uv:cve:`2026-21441`) (:uv:bug:`58984`)

  * :program:`qemu` (:uv:cve:`2025-11234`) (:uv:bug:`58953`)

  * :program:`rsync` (:uv:cve:`2025-10158`) (:uv:bug:`58961`)

  * :program:`squid` (:uv:cve:`2023-46728`, :uv:cve:`2024-45802`,
    :uv:cve:`2025-59362`) (:uv:bug:`58959`)

  * :program:`unbound` (:uv:cve:`2023-50387`, :uv:cve:`2023-50868`,
    :uv:cve:`2024-33655`, :uv:cve:`2025-11411`) (:uv:bug:`58943`)

  * :program:`univention-dojo` (:uv:cve:`2021-23450`,
    :uv:cve:`2024-48910`) (:uv:bug:`58843`)

  * :program:`univention-web` (:uv:cve:`2021-23450`,
    :uv:cve:`2024-48910`) (:uv:bug:`58843`)

  * :program:`xen` (:uv:cve:`2024-28956`, :uv:cve:`2024-36350`,
    :uv:cve:`2024-36357`, :uv:cve:`2025-1713`, :uv:cve:`2025-27465`,
    :uv:cve:`2025-27466`, :uv:cve:`2025-58142`, :uv:cve:`2025-58143`,
    :uv:cve:`2025-58144`, :uv:cve:`2025-58145`, :uv:cve:`2025-58147`,
    :uv:cve:`2025-58148`, :uv:cve:`2025-58149`) (:uv:bug:`58892`)


.. _debian:

* |UCSUCS| |release| includes the following updated packages from Debian 12.13:

  :program:`base-files`
  :program:`bash`
  :program:`btrfs-progs`
  :program:`busybox`
  :program:`distro-info-data`
  :program:`intel-microcode`
  :program:`libcap2`
  :program:`python-urllib3`
  :program:`shadow`
  :program:`sudo`
  :program:`allow-html-temp`
  :program:`angular.js`
  :program:`c-icap-modules`
  :program:`calibre`
  :program:`cdebootstrap`
  :program:`chkrootkit`
  :program:`chromium`
  :program:`composer`
  :program:`cyrus-imapd`
  :program:`dar`
  :program:`debian-installer`
  :program:`debian-installer-netboot-images`
  :program:`debian-security-support`
  :program:`dpdk`
  :program:`e2guardian`
  :program:`emacs-libvterm`
  :program:`freerdp2`
  :program:`gegl`
  :program:`ghdl`
  :program:`gimp`
  :program:`golang-github-containerd-stargz-snapshotter`
  :program:`golang-github-containers-buildah`
  :program:`golang-github-openshift-imagebuilder`
  :program:`lemonldap-ng`
  :program:`libclamunrar`
  :program:`libcommons-lang-java`
  :program:`libcommons-lang3-java`
  :program:`libhtp`
  :program:`libnginx-mod-http-lua`
  :program:`libphp-adodb`
  :program:`libpod`
  :program:`libreoffice`
  :program:`libyaml-syck-perl`
  :program:`log4cxx`
  :program:`luksmeta`
  :program:`lxd`
  :program:`mediawiki`
  :program:`modsecurity-apache`
  :program:`modsecurity-crs`
  :program:`mongo-c-driver`
  :program:`munge`
  :program:`mydumper`
  :program:`nginx`
  :program:`nova`
  :program:`nvidia-open-gpu-kernel-modules`
  :program:`onetbb`
  :program:`open-vm-tools`
  :program:`openrefine`
  :program:`openvpn`
  :program:`pg-snakeoil`
  :program:`pgbouncer`
  :program:`python-django`
  :program:`python-django-storages`
  :program:`qpwgraph`
  :program:`r-cran-gh`
  :program:`rails`
  :program:`rear`
  :program:`rlottie`
  :program:`roundcube`
  :program:`ruby-sinatra`
  :program:`rust-cbindgen-web`
  :program:`sash`
  :program:`shaarli`
  :program:`skeema`
  :program:`snapd`
  :program:`sogo`
  :program:`supermin`
  :program:`symfony`
  :program:`syslog-ng`
  :program:`thunderbird`
  :program:`tomcat10`
  :program:`tripwire`
  :program:`u-boot`
  :program:`ublock-origin`
  :program:`usbmuxd`
  :program:`user-mode-linux`
  :program:`vlc`
  :program:`vtk9`
  :program:`webkit2gtk`
  :program:`wordpress`
  :program:`xrdp`
  :program:`zsh`
  :program:`docker.io`

.. _maintained:

* The following packages have been moved to the maintained repository of UCS:

.. _changelog-domain:

***************
Domain services
***************

.. _changelog-udm:

LDAP Directory Manager
======================

* The Recycle Bin listener module is now disabled by default and can be
  activated via setting the UCR variable
  `listener/module/recyclebin/deactivate` to false. Recycle Bin policies can
  now disable the creation of Recycle Bin objects for a whole subtree. All
  occurrences of "Recyclebin" in user facing places have been renamed to
  "Recycle Bin" (:uv:bug:`58887`).

* Allow dash in uid and gid syntaxes also as last character (:uv:bug:`58898`).

* The performance of group membership updates for user and computer objects has
  been improved (:uv:bug:`58899`).

* The DN of objects in the recycle bin has been shortened to just
  "OriginalUniventionObjectIdentifier=$ID,cn=recyclebin,cn=internal"
  (:uv:bug:`58931`).

* Fix UnboundLocalError in logging in syntax.py (:uv:bug:`58982`).

* Fixed: With errata282 a change was introduced to univention-directory-
  manager-modules which requires a restart of some services that depend on
  univention-directory-manager-modules. A UCS@school service was missing in the
  list of services that need to be restarted (:uv:bug:`58992`).

* UDM now shows a default for ``univentionObjectIdentifier`` if not set in
  OpenLDAP (:uv:bug:`58987`).

* When deleting a container, the group membership of the objects within that
  container is now correctly removed (:uv:bug:`56986`).

* All occurrences of "Recyclebin" in user facing places have been renamed to
  "Recycle Bin" (:uv:bug:`58887`).

* A new endpoint `/udm/-/reload` has been added to reload UDM extensions. It is
  automatically called whenever such an extension is registered
  (:uv:bug:`50253`).

* Improved error handling in listener handler for reloading UDM REST service
  (:uv:bug:`58970`).

* Load extended UDM attributes in unmap-ldap-attributes endpoint
  (:uv:bug:`58970`).

* Allow configuration of the root_path, to reduce the complexity on the reverse
  proxy (:uv:bug:`59032`).

.. _changelog-umc:

*****************************
Univention Management Console
*****************************

.. _changelog-umc-server:

Univention Management Console server
====================================

* Allow configuration of the root_path, to reduce the complexity on the reverse
  proxy (:uv:bug:`59033`).

.. _changelog-umc-diagnostic:

System diagnostic module
========================

* Improved error message in ``univentionObjectIdentifier`` test
  (:uv:bug:`58987`).

* Improve the handling of SSL certificate checks when external certificates are
  configured. The diagnostic tool now provides actionable guidance when
  detecting hostname mismatches instead of failing with a traceback
  (:uv:bug:`55576`).

.. _changelog-umc-ldap:

LDAP directory browser
======================

* All occurrences of "Recyclebin" in user facing places have been renamed to
  "Recycle Bin" (:uv:bug:`58887`).

* A new endpoint `/udm/-/reload` has been added to the UDM REST API to reload
  UDM extensions. This packages containes shared code for the reload
  (:uv:bug:`50253`).

.. _changelog-lib:

*************************
Univention base libraries
*************************

* All occurrences of "Recyclebin" in user facing places have been renamed to
  "Recycle Bin" (:uv:bug:`58887`).

* Add functionality to the UMC Client to allow skipping SSL hostname
  verification for local connections (:uv:bug:`55576`).

.. _changelog-service:

***************
System services
***************

.. _changelog-service-saml:

SAML
====

* The UID User Federation Mapper is now created with the "Always Read Value
  From LDAP" setting enabled by default. This establishes LDAP as the single
  source of truth for UIDs, bypassing Keycloak's local database cache on every
  request (:uv:bug:`59040`).

* The univention-keycloak script introduces a flag to enable the "Always Read
  Value From LDAP" setting for new User Federation Mappers (:uv:bug:`59040`).

.. _changelog-service-mail:

Mail services
=============

* A defect in the Fetchmail listener module has been resolved. The issue
  prevented the Fetchmail service from restarting correctly after user
  configuration changes, which prevented emails from being sent or received
  (:uv:bug:`59036`).

.. _changelog-service-imap:

IMAP services
-------------

* The logrotate configuration for reloading rsyslog has been fixed
  (:uv:bug:`58551`).

.. _changelog-win:

********************
Services for Windows
********************

.. _changelog-win-samba:

Samba
=====

* Since Kernel 4.19 the sysvol-sync could fail after reboots with message
  `cannot create /var/lock/sysvol-sync-dir: Permission denied`. This update
  fixes this issue (:uv:bug:`58784`).

.. _changelog-win-s4c:

Univention S4 Connector
=======================

* The S4-Connector now supports restoring objects from the UDM Recyclebin also
  in Samba/AD (:uv:bug:`58844`).

.. _changelog-win-adc:

Univention Active Directory Connection
======================================

* `univention-adsearch` only supported LDAPS against port 636, but not StartTLS
  against port 389. Now it also supports the latter (:uv:bug:`57747`).

* Only consider permitted enctypes when synchronizing Kerberos keys from AD
  supplementalCredentials. This avoids a compatibility issue with the new
  `sha256` and `sha384` hash types generated by Windows Server 2025 until we
  apply the fix for the issue in OpenLDAP (:uv:bug:`57747`).

* Renaming a user object with umlauts in AD led to a connector reject. The
  update fixes this issues (:uv:bug:`58793`).

* In the modify operation also move object in UCS if position has changed in AD
  (:uv:bug:`58793`).

* Ignore order of multi value attributes when checking for changed attributes
  (:uv:bug:`58793`).

* Avoid unnecessary object mapping before checking for changed attributes
  (:uv:bug:`58793`).

* Avoid ldap.ALREADY_EXISTS if move target exists in UCS (:uv:bug:`58793`).

* During DN mapping, lookup samaccountname for olddn from adcache
  (:uv:bug:`58793`).

* Skip resync of reject for uSNCreated if lower than uSNChanged
  (:uv:bug:`58793`).

* Add AD reject reason to reject database. The reason will be shown in the
  univention-adconnector-list-rejected tool (:uv:bug:`58793`).

* The AD-Connector now supports restoring objects from the UDM Recyclebin also
  in Active Directory (:uv:bug:`58844`).

.. _changelog-other:

*************
Other changes
*************

* When setting up a new printer in CUPS via IPP Everywhere, the printer model
  name is no longer correctly queried from the printer via IPP
  (:uv:bug:`58874`).

* When setting up a new printer in CUPS via IPP Everywhere, the printer model
  name is no longer correctly queried from the printer via IPP. This has been
  fixed now. Really (:uv:bug:`58874`).

* The package `univention-provisioning-service` has been added. It ships a
  listener module that pushes new transactions into the Provisioning Service
  App. These packages will be installed automatically when installing the new
  Provisioning Service UCS App (:uv:bug:`58973`).

* The listener module `nubus-provisiong.py` is now capable of reconnecting to
  `NATS` without a restart of the listener being necessary (:uv:bug:`58991`).

