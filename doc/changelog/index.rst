.. SPDX-FileCopyrightText: 2021-2025 Univention GmbH
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

* UCS 5.0-10 includes all issued security updates issued for UCS 5.0-9:

  * :program:`amavisd-new` (:uv:cve:`2024-28054`) (:uv:bug:`57823`)

  * :program:`amd64-microcode` (:uv:cve:`2023-20569`,
    :uv:cve:`2023-20584`, :uv:cve:`2023-31315`, :uv:cve:`2023-31356`)
    (:uv:bug:`57766`)

  * :program:`apache2` (:uv:cve:`2024-38473`, :uv:cve:`2024-38474`,
    :uv:cve:`2024-38475`) (:uv:bug:`57618`, :uv:bug:`57752`)

  * :program:`avahi` (:uv:cve:`2023-1981`, :uv:cve:`2023-38469`,
    :uv:cve:`2023-38470`, :uv:cve:`2023-38471`, :uv:cve:`2023-38472`,
    :uv:cve:`2023-38473`) (:uv:bug:`57809`)

  * :program:`bind9` (:uv:cve:`2024-11187`) (:uv:bug:`57982`)

  * :program:`busybox` (:uv:cve:`2021-28831`, :uv:cve:`2021-42374`,
    :uv:cve:`2021-42378`, :uv:cve:`2021-42379`, :uv:cve:`2021-42380`,
    :uv:cve:`2021-42381`, :uv:cve:`2021-42382`, :uv:cve:`2021-42384`,
    :uv:cve:`2021-42385`, :uv:cve:`2021-42386`, :uv:cve:`2022-48174`,
    :uv:cve:`2023-42364`, :uv:cve:`2023-42365`) (:uv:bug:`57938`)

  * :program:`clamav` (:uv:cve:`2024-20505`, :uv:cve:`2024-20506`)
    (:uv:bug:`57798`)

  * :program:`cups` (:uv:cve:`2024-35235`, :uv:cve:`2024-47175`)
    (:uv:bug:`57647`)

  * :program:`cups-filters` (:uv:cve:`2024-47076`,
    :uv:cve:`2024-47176`) (:uv:bug:`57626`)

  * :program:`e2fsprogs` (:uv:cve:`2022-1304`) (:uv:bug:`57648`)

  * :program:`exim4` (:uv:cve:`2021-38371`, :uv:cve:`2022-3559`,
    :uv:cve:`2023-42117`, :uv:cve:`2023-42119`) (:uv:bug:`57781`)

  * :program:`expat` (:uv:cve:`2024-45490`, :uv:cve:`2024-45491`,
    :uv:cve:`2024-45492`) (:uv:bug:`57644`)

  * :program:`ffmpeg` (:uv:cve:`2020-20898`, :uv:cve:`2020-22040`,
    :uv:cve:`2020-22051`, :uv:cve:`2020-22056`, :uv:cve:`2021-38090`,
    :uv:cve:`2021-38091`, :uv:cve:`2021-38092`, :uv:cve:`2021-38093`,
    :uv:cve:`2021-38094`, :uv:cve:`2022-48434`, :uv:cve:`2023-49502`,
    :uv:cve:`2023-50010`, :uv:cve:`2023-51793`, :uv:cve:`2023-51794`,
    :uv:cve:`2023-51798`, :uv:cve:`2024-31578`, :uv:cve:`2024-32230`,
    :uv:cve:`2024-35366`, :uv:cve:`2024-35367`, :uv:cve:`2024-35368`,
    :uv:cve:`2024-36616`, :uv:cve:`2024-36617`, :uv:cve:`2024-36618`)
    (:uv:bug:`57715`, :uv:bug:`57939`)

  * :program:`firmware-nonfree` (:uv:cve:`2023-35061`,
    :uv:cve:`2023-38417`, :uv:cve:`2023-47210`) (:uv:bug:`57625`)

  * :program:`ghostscript` (:uv:cve:`2024-46951`,
    :uv:cve:`2024-46953`, :uv:cve:`2024-46955`, :uv:cve:`2024-46956`)
    (:uv:bug:`57767`)

  * :program:`git` (:uv:cve:`2024-50349`, :uv:cve:`2024-52006`)
    (:uv:bug:`57937`)

  * :program:`glib2.0` (:uv:cve:`2024-52533`) (:uv:bug:`57769`)

  * :program:`gtk+2.0` (:uv:cve:`2024-6655`) (:uv:bug:`57668`)

  * :program:`gtk+3.0` (:uv:cve:`2024-6655`) (:uv:bug:`57669`)

  * :program:`hplip` (:uv:cve:`2020-6923`) (:uv:bug:`57893`)

  * :program:`intel-microcode` (:uv:cve:`2024-21853`,
    :uv:cve:`2024-23918`, :uv:cve:`2024-23984`, :uv:cve:`2024-24968`)
    (:uv:bug:`57768`, :uv:bug:`57825`)

  * :program:`iproute2` (:uv:cve:`2019-20795`) (:uv:bug:`57624`)

  * :program:`libarchive` (:uv:cve:`2024-20696`) (:uv:bug:`57750`)

  * :program:`libheif` (:uv:cve:`2023-0996`, :uv:cve:`2024-41311`)
    (:uv:bug:`57699`, :uv:bug:`57741`)

  * :program:`libsepol` (:uv:cve:`2021-36084`, :uv:cve:`2021-36085`,
    :uv:cve:`2021-36086`, :uv:cve:`2021-36087`) (:uv:bug:`57696`)

  * :program:`libsoup2.4` (:uv:cve:`2024-52530`, :uv:cve:`2024-52531`,
    :uv:cve:`2024-52532`) (:uv:bug:`57808`)

  * :program:`libxml2` (:uv:cve:`2016-9318`, :uv:cve:`2017-16932`,
    :uv:cve:`2023-39615`, :uv:cve:`2023-45322`, :uv:cve:`2024-25062`)
    (:uv:bug:`57664`, :uv:bug:`57722`)

  * :program:`linux-5.10` (:uv:cve:`2021-3669`, :uv:cve:`2022-43945`,
    :uv:cve:`2022-48666`, :uv:cve:`2022-48733`, :uv:cve:`2023-31083`,
    :uv:cve:`2023-52889`, :uv:cve:`2024-25741`, :uv:cve:`2024-26629`,
    :uv:cve:`2024-27019`, :uv:cve:`2024-27397`, :uv:cve:`2024-31076`,
    :uv:cve:`2024-36014`, :uv:cve:`2024-36015`, :uv:cve:`2024-36016`,
    :uv:cve:`2024-36270`, :uv:cve:`2024-36288`, :uv:cve:`2024-36484`,
    :uv:cve:`2024-36489`, :uv:cve:`2024-36901`, :uv:cve:`2024-36938`,
    :uv:cve:`2024-36974`, :uv:cve:`2024-36978`, :uv:cve:`2024-37078`,
    :uv:cve:`2024-37356`, :uv:cve:`2024-38381`, :uv:cve:`2024-38546`,
    :uv:cve:`2024-38547`, :uv:cve:`2024-38548`, :uv:cve:`2024-38552`,
    :uv:cve:`2024-38555`, :uv:cve:`2024-38558`, :uv:cve:`2024-38559`,
    :uv:cve:`2024-38560`, :uv:cve:`2024-38565`, :uv:cve:`2024-38567`,
    :uv:cve:`2024-38577`, :uv:cve:`2024-38578`, :uv:cve:`2024-38579`,
    :uv:cve:`2024-38582`, :uv:cve:`2024-38583`, :uv:cve:`2024-38586`,
    :uv:cve:`2024-38589`, :uv:cve:`2024-38590`, :uv:cve:`2024-38596`,
    :uv:cve:`2024-38597`, :uv:cve:`2024-38598`, :uv:cve:`2024-38599`,
    :uv:cve:`2024-38601`, :uv:cve:`2024-38605`, :uv:cve:`2024-38607`,
    :uv:cve:`2024-38612`, :uv:cve:`2024-38618`, :uv:cve:`2024-38619`,
    :uv:cve:`2024-38621`, :uv:cve:`2024-38627`, :uv:cve:`2024-38633`,
    :uv:cve:`2024-38634`, :uv:cve:`2024-38635`, :uv:cve:`2024-38637`,
    :uv:cve:`2024-38659`, :uv:cve:`2024-38662`, :uv:cve:`2024-38780`,
    :uv:cve:`2024-39468`, :uv:cve:`2024-39482`, :uv:cve:`2024-39487`,
    :uv:cve:`2024-40947`, :uv:cve:`2024-41007`, :uv:cve:`2024-41009`,
    :uv:cve:`2024-41011`, :uv:cve:`2024-41012`, :uv:cve:`2024-41042`,
    :uv:cve:`2024-41090`, :uv:cve:`2024-41091`, :uv:cve:`2024-41098`,
    :uv:cve:`2024-42114`, :uv:cve:`2024-42228`, :uv:cve:`2024-42246`,
    :uv:cve:`2024-42259`, :uv:cve:`2024-42265`, :uv:cve:`2024-42272`,
    :uv:cve:`2024-42276`, :uv:cve:`2024-42280`, :uv:cve:`2024-42281`,
    :uv:cve:`2024-42283`, :uv:cve:`2024-42284`, :uv:cve:`2024-42285`,
    :uv:cve:`2024-42286`, :uv:cve:`2024-42287`, :uv:cve:`2024-42288`,
    :uv:cve:`2024-42289`, :uv:cve:`2024-42290`, :uv:cve:`2024-42292`,
    :uv:cve:`2024-42295`, :uv:cve:`2024-42297`, :uv:cve:`2024-42301`,
    :uv:cve:`2024-42302`, :uv:cve:`2024-42304`, :uv:cve:`2024-42305`,
    :uv:cve:`2024-42306`, :uv:cve:`2024-42308`, :uv:cve:`2024-42309`,
    :uv:cve:`2024-42310`, :uv:cve:`2024-42311`, :uv:cve:`2024-42312`,
    :uv:cve:`2024-42313`, :uv:cve:`2024-43828`, :uv:cve:`2024-43829`,
    :uv:cve:`2024-43830`, :uv:cve:`2024-43834`, :uv:cve:`2024-43835`,
    :uv:cve:`2024-43839`, :uv:cve:`2024-43841`, :uv:cve:`2024-43846`,
    :uv:cve:`2024-43849`, :uv:cve:`2024-43853`, :uv:cve:`2024-43854`,
    :uv:cve:`2024-43856`, :uv:cve:`2024-43858`, :uv:cve:`2024-43860`,
    :uv:cve:`2024-43861`, :uv:cve:`2024-43867`, :uv:cve:`2024-43871`,
    :uv:cve:`2024-43879`, :uv:cve:`2024-43880`, :uv:cve:`2024-43882`,
    :uv:cve:`2024-43883`, :uv:cve:`2024-43884`, :uv:cve:`2024-43889`,
    :uv:cve:`2024-43890`, :uv:cve:`2024-43892`, :uv:cve:`2024-43893`,
    :uv:cve:`2024-43894`, :uv:cve:`2024-43905`, :uv:cve:`2024-43907`,
    :uv:cve:`2024-43908`, :uv:cve:`2024-43914`, :uv:cve:`2024-44935`,
    :uv:cve:`2024-44944`, :uv:cve:`2024-44946`, :uv:cve:`2024-44947`,
    :uv:cve:`2024-44948`, :uv:cve:`2024-44952`, :uv:cve:`2024-44954`,
    :uv:cve:`2024-44960`, :uv:cve:`2024-44965`, :uv:cve:`2024-44968`,
    :uv:cve:`2024-44971`, :uv:cve:`2024-44974`, :uv:cve:`2024-44987`,
    :uv:cve:`2024-44988`, :uv:cve:`2024-44989`, :uv:cve:`2024-44990`,
    :uv:cve:`2024-44995`, :uv:cve:`2024-44998`, :uv:cve:`2024-44999`,
    :uv:cve:`2024-45003`, :uv:cve:`2024-45006`, :uv:cve:`2024-45008`,
    :uv:cve:`2024-45016`, :uv:cve:`2024-45018`, :uv:cve:`2024-45021`,
    :uv:cve:`2024-45025`, :uv:cve:`2024-45028`, :uv:cve:`2024-46673`,
    :uv:cve:`2024-46674`, :uv:cve:`2024-46675`, :uv:cve:`2024-46676`,
    :uv:cve:`2024-46677`, :uv:cve:`2024-46679`, :uv:cve:`2024-46685`,
    :uv:cve:`2024-46689`, :uv:cve:`2024-46702`, :uv:cve:`2024-46707`,
    :uv:cve:`2024-46713`, :uv:cve:`2024-46714`, :uv:cve:`2024-46719`,
    :uv:cve:`2024-46721`, :uv:cve:`2024-46722`, :uv:cve:`2024-46723`,
    :uv:cve:`2024-46724`, :uv:cve:`2024-46725`, :uv:cve:`2024-46731`,
    :uv:cve:`2024-46737`, :uv:cve:`2024-46738`, :uv:cve:`2024-46739`,
    :uv:cve:`2024-46740`, :uv:cve:`2024-46743`, :uv:cve:`2024-46744`,
    :uv:cve:`2024-46745`, :uv:cve:`2024-46747`, :uv:cve:`2024-46750`,
    :uv:cve:`2024-46755`, :uv:cve:`2024-46756`, :uv:cve:`2024-46757`,
    :uv:cve:`2024-46758`, :uv:cve:`2024-46759`, :uv:cve:`2024-46763`,
    :uv:cve:`2024-46771`, :uv:cve:`2024-46777`, :uv:cve:`2024-46780`,
    :uv:cve:`2024-46781`, :uv:cve:`2024-46782`, :uv:cve:`2024-46783`,
    :uv:cve:`2024-46791`, :uv:cve:`2024-46798`, :uv:cve:`2024-46800`,
    :uv:cve:`2024-46804`, :uv:cve:`2024-46814`, :uv:cve:`2024-46815`,
    :uv:cve:`2024-46817`, :uv:cve:`2024-46818`, :uv:cve:`2024-46819`,
    :uv:cve:`2024-46822`, :uv:cve:`2024-46828`, :uv:cve:`2024-46829`,
    :uv:cve:`2024-46840`, :uv:cve:`2024-46844`) (:uv:bug:`57718`)

  * :program:`linux-signed-5.10-amd64` (:uv:cve:`2021-3669`,
    :uv:cve:`2022-43945`, :uv:cve:`2022-48666`, :uv:cve:`2022-48733`,
    :uv:cve:`2023-31083`, :uv:cve:`2023-52889`, :uv:cve:`2024-25741`,
    :uv:cve:`2024-26629`, :uv:cve:`2024-27019`, :uv:cve:`2024-27397`,
    :uv:cve:`2024-31076`, :uv:cve:`2024-36014`, :uv:cve:`2024-36015`,
    :uv:cve:`2024-36016`, :uv:cve:`2024-36270`, :uv:cve:`2024-36288`,
    :uv:cve:`2024-36484`, :uv:cve:`2024-36489`, :uv:cve:`2024-36901`,
    :uv:cve:`2024-36938`, :uv:cve:`2024-36974`, :uv:cve:`2024-36978`,
    :uv:cve:`2024-37078`, :uv:cve:`2024-37356`, :uv:cve:`2024-38381`,
    :uv:cve:`2024-38546`, :uv:cve:`2024-38547`, :uv:cve:`2024-38548`,
    :uv:cve:`2024-38552`, :uv:cve:`2024-38555`, :uv:cve:`2024-38558`,
    :uv:cve:`2024-38559`, :uv:cve:`2024-38560`, :uv:cve:`2024-38565`,
    :uv:cve:`2024-38567`, :uv:cve:`2024-38577`, :uv:cve:`2024-38578`,
    :uv:cve:`2024-38579`, :uv:cve:`2024-38582`, :uv:cve:`2024-38583`,
    :uv:cve:`2024-38586`, :uv:cve:`2024-38589`, :uv:cve:`2024-38590`,
    :uv:cve:`2024-38596`, :uv:cve:`2024-38597`, :uv:cve:`2024-38598`,
    :uv:cve:`2024-38599`, :uv:cve:`2024-38601`, :uv:cve:`2024-38605`,
    :uv:cve:`2024-38607`, :uv:cve:`2024-38612`, :uv:cve:`2024-38618`,
    :uv:cve:`2024-38619`, :uv:cve:`2024-38621`, :uv:cve:`2024-38627`,
    :uv:cve:`2024-38633`, :uv:cve:`2024-38634`, :uv:cve:`2024-38635`,
    :uv:cve:`2024-38637`, :uv:cve:`2024-38659`, :uv:cve:`2024-38662`,
    :uv:cve:`2024-38780`, :uv:cve:`2024-39468`, :uv:cve:`2024-39482`,
    :uv:cve:`2024-39487`, :uv:cve:`2024-40947`, :uv:cve:`2024-41007`,
    :uv:cve:`2024-41009`, :uv:cve:`2024-41011`, :uv:cve:`2024-41012`,
    :uv:cve:`2024-41042`, :uv:cve:`2024-41090`, :uv:cve:`2024-41091`,
    :uv:cve:`2024-41098`, :uv:cve:`2024-42114`, :uv:cve:`2024-42228`,
    :uv:cve:`2024-42246`, :uv:cve:`2024-42259`, :uv:cve:`2024-42265`,
    :uv:cve:`2024-42272`, :uv:cve:`2024-42276`, :uv:cve:`2024-42280`,
    :uv:cve:`2024-42281`, :uv:cve:`2024-42283`, :uv:cve:`2024-42284`,
    :uv:cve:`2024-42285`, :uv:cve:`2024-42286`, :uv:cve:`2024-42287`,
    :uv:cve:`2024-42288`, :uv:cve:`2024-42289`, :uv:cve:`2024-42290`,
    :uv:cve:`2024-42292`, :uv:cve:`2024-42295`, :uv:cve:`2024-42297`,
    :uv:cve:`2024-42301`, :uv:cve:`2024-42302`, :uv:cve:`2024-42304`,
    :uv:cve:`2024-42305`, :uv:cve:`2024-42306`, :uv:cve:`2024-42308`,
    :uv:cve:`2024-42309`, :uv:cve:`2024-42310`, :uv:cve:`2024-42311`,
    :uv:cve:`2024-42312`, :uv:cve:`2024-42313`, :uv:cve:`2024-43828`,
    :uv:cve:`2024-43829`, :uv:cve:`2024-43830`, :uv:cve:`2024-43834`,
    :uv:cve:`2024-43835`, :uv:cve:`2024-43839`, :uv:cve:`2024-43841`,
    :uv:cve:`2024-43846`, :uv:cve:`2024-43849`, :uv:cve:`2024-43853`,
    :uv:cve:`2024-43854`, :uv:cve:`2024-43856`, :uv:cve:`2024-43858`,
    :uv:cve:`2024-43860`, :uv:cve:`2024-43861`, :uv:cve:`2024-43867`,
    :uv:cve:`2024-43871`, :uv:cve:`2024-43879`, :uv:cve:`2024-43880`,
    :uv:cve:`2024-43882`, :uv:cve:`2024-43883`, :uv:cve:`2024-43884`,
    :uv:cve:`2024-43889`, :uv:cve:`2024-43890`, :uv:cve:`2024-43892`,
    :uv:cve:`2024-43893`, :uv:cve:`2024-43894`, :uv:cve:`2024-43905`,
    :uv:cve:`2024-43907`, :uv:cve:`2024-43908`, :uv:cve:`2024-43914`,
    :uv:cve:`2024-44935`, :uv:cve:`2024-44944`, :uv:cve:`2024-44946`,
    :uv:cve:`2024-44947`, :uv:cve:`2024-44948`, :uv:cve:`2024-44952`,
    :uv:cve:`2024-44954`, :uv:cve:`2024-44960`, :uv:cve:`2024-44965`,
    :uv:cve:`2024-44968`, :uv:cve:`2024-44971`, :uv:cve:`2024-44974`,
    :uv:cve:`2024-44987`, :uv:cve:`2024-44988`, :uv:cve:`2024-44989`,
    :uv:cve:`2024-44990`, :uv:cve:`2024-44995`, :uv:cve:`2024-44998`,
    :uv:cve:`2024-44999`, :uv:cve:`2024-45003`, :uv:cve:`2024-45006`,
    :uv:cve:`2024-45008`, :uv:cve:`2024-45016`, :uv:cve:`2024-45018`,
    :uv:cve:`2024-45021`, :uv:cve:`2024-45025`, :uv:cve:`2024-45028`,
    :uv:cve:`2024-46673`, :uv:cve:`2024-46674`, :uv:cve:`2024-46675`,
    :uv:cve:`2024-46676`, :uv:cve:`2024-46677`, :uv:cve:`2024-46679`,
    :uv:cve:`2024-46685`, :uv:cve:`2024-46689`, :uv:cve:`2024-46702`,
    :uv:cve:`2024-46707`, :uv:cve:`2024-46713`, :uv:cve:`2024-46714`,
    :uv:cve:`2024-46719`, :uv:cve:`2024-46721`, :uv:cve:`2024-46722`,
    :uv:cve:`2024-46723`, :uv:cve:`2024-46724`, :uv:cve:`2024-46725`,
    :uv:cve:`2024-46731`, :uv:cve:`2024-46737`, :uv:cve:`2024-46738`,
    :uv:cve:`2024-46739`, :uv:cve:`2024-46740`, :uv:cve:`2024-46743`,
    :uv:cve:`2024-46744`, :uv:cve:`2024-46745`, :uv:cve:`2024-46747`,
    :uv:cve:`2024-46750`, :uv:cve:`2024-46755`, :uv:cve:`2024-46756`,
    :uv:cve:`2024-46757`, :uv:cve:`2024-46758`, :uv:cve:`2024-46759`,
    :uv:cve:`2024-46763`, :uv:cve:`2024-46771`, :uv:cve:`2024-46777`,
    :uv:cve:`2024-46780`, :uv:cve:`2024-46781`, :uv:cve:`2024-46782`,
    :uv:cve:`2024-46783`, :uv:cve:`2024-46791`, :uv:cve:`2024-46798`,
    :uv:cve:`2024-46800`, :uv:cve:`2024-46804`, :uv:cve:`2024-46814`,
    :uv:cve:`2024-46815`, :uv:cve:`2024-46817`, :uv:cve:`2024-46818`,
    :uv:cve:`2024-46819`, :uv:cve:`2024-46822`, :uv:cve:`2024-46828`,
    :uv:cve:`2024-46829`, :uv:cve:`2024-46840`, :uv:cve:`2024-46844`)
    (:uv:bug:`57718`)

  * :program:`mariadb-10.3` (:uv:cve:`2024-21096`) (:uv:bug:`57652`)

  * :program:`nss` (:uv:cve:`2023-6135`, :uv:cve:`2024-6602`,
    :uv:cve:`2024-6609`) (:uv:bug:`57740`)

  * :program:`ntfs-3g` (:uv:cve:`2021-33285`, :uv:cve:`2021-33286`,
    :uv:cve:`2021-33287`, :uv:cve:`2021-33289`, :uv:cve:`2021-35266`,
    :uv:cve:`2021-35267`, :uv:cve:`2021-35268`, :uv:cve:`2021-35269`,
    :uv:cve:`2021-39251`, :uv:cve:`2021-39252`, :uv:cve:`2021-39253`,
    :uv:cve:`2021-39254`, :uv:cve:`2021-39255`, :uv:cve:`2021-39256`,
    :uv:cve:`2021-39257`, :uv:cve:`2021-39258`, :uv:cve:`2021-39259`,
    :uv:cve:`2021-39260`, :uv:cve:`2021-39261`, :uv:cve:`2021-39262`,
    :uv:cve:`2021-39263`, :uv:cve:`2021-46790`, :uv:cve:`2022-30783`,
    :uv:cve:`2022-30784`, :uv:cve:`2022-30785`, :uv:cve:`2022-30786`,
    :uv:cve:`2022-30787`, :uv:cve:`2022-30788`, :uv:cve:`2022-30789`,
    :uv:cve:`2022-40284`, :uv:cve:`2023-52890`) (:uv:bug:`57646`)

  * :program:`ntp` (:uv:cve:`2020-11868`, :uv:cve:`2020-15025`,
    :uv:cve:`2023-26555`) (:uv:bug:`57807`)

  * :program:`openjdk-11` (:uv:cve:`2024-21208`, :uv:cve:`2024-21210`,
    :uv:cve:`2024-21217`, :uv:cve:`2024-21235`, :uv:cve:`2025-21502`)
    (:uv:bug:`57698`, :uv:bug:`57936`)

  * :program:`openssh` (:uv:cve:`2020-14145`, :uv:cve:`2025-26465`)
    (:uv:bug:`57981`)

  * :program:`openssl` (:uv:cve:`2023-5678`, :uv:cve:`2024-0727`,
    :uv:cve:`2024-2511`, :uv:cve:`2024-4741`, :uv:cve:`2024-5535`,
    :uv:cve:`2024-9143`) (:uv:bug:`57782`)

  * :program:`perl` (:uv:cve:`2020-16156`, :uv:cve:`2023-31484`)
    (:uv:bug:`57716`)

  * :program:`php7.3` (:uv:cve:`2024-11233`, :uv:cve:`2024-11234`,
    :uv:cve:`2024-11236`, :uv:cve:`2024-8925`, :uv:cve:`2024-8927`,
    :uv:cve:`2024-8929`, :uv:cve:`2024-8932`) (:uv:bug:`57683`,
    :uv:bug:`57824`)

  * :program:`postgresql-11` (:uv:cve:`2024-10976`,
    :uv:cve:`2024-10977`, :uv:cve:`2024-10978`, :uv:cve:`2024-10979`)
    (:uv:bug:`57899`)

  * :program:`python-cryptography` (:uv:cve:`2020-25659`)
    (:uv:bug:`57697`)

  * :program:`python-django` (:uv:cve:`2024-53907`,
    :uv:cve:`2024-56374`) (:uv:bug:`57935`)

  * :program:`python-tornado` (:uv:cve:`2023-28370`,
    :uv:cve:`2024-52804`) (:uv:bug:`57850`)

  * :program:`python-urllib3` (:uv:cve:`2024-37891`) (:uv:bug:`57983`)

  * :program:`python3.7` (:uv:cve:`2023-27043`, :uv:cve:`2024-11168`,
    :uv:cve:`2024-6232`, :uv:cve:`2024-6923`, :uv:cve:`2024-7592`,
    :uv:cve:`2024-9287`) (:uv:bug:`57780`)

  * :program:`rsync` (:uv:cve:`2024-12085`, :uv:cve:`2024-12086`,
    :uv:cve:`2024-12087`, :uv:cve:`2024-12088`, :uv:cve:`2024-12747`)
    (:uv:bug:`57883`)

  * :program:`ruby2.5` (:uv:cve:`2024-35176`, :uv:cve:`2024-39908`,
    :uv:cve:`2024-41123`, :uv:cve:`2024-41946`, :uv:cve:`2024-43398`,
    :uv:cve:`2024-49761`) (:uv:bug:`57898`)

  * :program:`shadow` (:uv:cve:`2018-7169`, :uv:cve:`2023-29383`,
    :uv:cve:`2023-4641`) (:uv:bug:`57720`)

  * :program:`simplesamlphp` (:uv:cve:`2024-52596`,
    :uv:cve:`2024-52806`) (:uv:bug:`57799`)

  * :program:`sqlite3` (:uv:cve:`2019-19244`, :uv:cve:`2021-36690`,
    :uv:cve:`2023-7104`) (:uv:bug:`57645`)

  * :program:`tiff` (:uv:cve:`2023-25433`, :uv:cve:`2023-52356`,
    :uv:cve:`2024-7006`) (:uv:bug:`57892`)

  * :program:`unbound` (:uv:cve:`2024-43167`, :uv:cve:`2024-43168`,
    :uv:cve:`2024-8508`) (:uv:bug:`57751`)

  * :program:`xorg-server` (:uv:cve:`2024-9632`) (:uv:bug:`57721`)


.. _debian:

* UCS 5.0-10 includes the following updated packages from Debian ELTS:

  :program:`emacs`
  :program:`krb5`
  :program:`libtasn1-6`
  :program:`libxml2`
  :program:`xorg-server`
  :program:`ca-certificates-java`
  :program:`distro-info-data`
  :program:`ruby2.5`
  :program:`tzdata`
  :program:`ucf`
  :program:`activemq`
  :program:`ark`
  :program:`asterisk`
  :program:`astropy`
  :program:`c-icap-modules`
  :program:`context`
  :program:`cyrus-imapd`
  :program:`dcmtk`
  :program:`dnsmasq`
  :program:`editorconfig-core`
  :program:`fastnetmon`
  :program:`frr`
  :program:`git-lfs`
  :program:`gst-plugins-base1.0`
  :program:`gstreamer1.0`
  :program:`havp`
  :program:`icinga2`
  :program:`iperf3`
  :program:`lemonldap-ng`
  :program:`libapache-mod-jk`
  :program:`libcpan-reporter-smoker-perl`
  :program:`libgsf`
  :program:`libmodule-scandeps-perl`
  :program:`libpam-tacplus`
  :program:`libpgjava`
  :program:`libreoffice`
  :program:`libtar`
  :program:`linux-6.1`
  :program:`linux-signed-6.1-amd64`
  :program:`mpg123`
  :program:`needrestart`
  :program:`nodejs`
  :program:`pg-snakeoil`
  :program:`pypy`
  :program:`python-clamav`
  :program:`qtbase-opensource-src`
  :program:`redis`
  :program:`smarty3`
  :program:`sssd`
  :program:`sympa`
  :program:`texlive-bin`
  :program:`tomcat9`
  :program:`twisted`
  :program:`vlc`
  :program:`waitress`
  :program:`wireshark`
  :program:`zeromq3`

.. _changelog-basic:

*********************
Basic system services
*********************

.. _changelog-basis-ucr:

Univention Configuration Registry
=================================

.. _changelog-basis-ucr-template:

Changes to templates and modules
--------------------------------

* The Linux kernel parameters for the garbage collection of ARP cache entries
  can now be set with UCR and have their default values increased
  (:uv:bug:`57712`).

.. _changelog-basis-boot:

Boot Loader
===========

* To support Secure Boot in Debian 10 (Buster) ELTS, the SecureBoot
  shim needs to be updated to include the ``Freexian`` public certificate which was
  used to sign the ELTS Linux kernel and other packages. This update adds that
  certificate to the shim alongside the Debian public CA, which allows to boot
  both old (signed by Debian) and new (signed by ``Freexian``) packages
  (:uv:bug:`57718`).

.. _changelog-domain:

***************
Domain services
***************

.. _changelog-udm:

LDAP Directory Manager
======================

* Improve performance of ``_ldap_modlist()`` in ``groups/group`` handler to speed
  up modifications of very large groups (:uv:bug:`57960`).

* Enforce JPEG conversion for all profile pictures not just PNG
  (:uv:bug:`57672`).

* The :command:`univention-license-check` didn't count system accounts correctly in
  case of an ``unlimited`` license. This has been fixed (:uv:bug:`57713`).

* Dynamic ``udm_filter`` for UDM syntax classes have been fixed so that a syntax
  which depends on the value of another property for its ``udm_filter`` works
  again (:uv:bug:`57733`).

.. _changelog-umc:

*****************************
Univention Management Console
*****************************

.. _changelog-umc-portal:

Univention Portal
=================

* Unique HTML identifiers have been added to each self-service module to
  simplify custom CSS usage (:uv:bug:`57731`).

.. _changelog-umc-server:

Univention Management Console server
====================================

* As Keycloak's OpenID Connect URIs are checked case sensitively, the default URIs set
  during the join script setup were rejected on servers which contained
  uppercase letters. All generated URIs are converted to lowercase from now on
  (:uv:bug:`57679`).

* Improved database session management under high load to prevent errors.
  Sessions are now properly closed, ensuring better stability in high
  concurrency environments (:uv:bug:`57680`).

* The OpenID Connect front-channel logout feature now works properly in
  environments where the OpenID Connect Provider is hosted on a different domain
  than the UMC (:uv:bug:`57516`).

* Make connection pool settings ``pool_size``, ``max_overflow``, ``pool_timeout``,
  and ``pool_recycle`` configurable through ``univention-management-console-settings`` for
  improved resource management (:uv:bug:`57714`).

* Delete UMC session when OpenID Connect token can't be refreshed after OP session
  deleted (:uv:bug:`57515`).

* A package dependency to the Python library :program:`psycopg2` has been added
  (:uv:bug:`57622`).

* The automatic browser reload of the ``univention-portal`` led to a visual
  logout every 5 minutes, since the initial assertion was expired then
  (:uv:bug:`57563`).

.. _changelog-umc-appcenter:

Univention App Center
=====================

* :command:`univention-app update-check` didn't report all missing apps during a UCS
  upgrade. Some docker apps may be missed due to working on the wrong cache.
  This has been fixed (:uv:bug:`57802`).

* ``univention-appcenter`` now provides UCR templates for PostgreSQL 15
  (:uv:bug:`57802`).

* Files uploaded as an App Setting were saved with the wrong content if
  uploaded during app installation (:uv:bug:`57996`).

.. _changelog-umc-user:

User management
===============

* The ``Message-ID`` header has been added to emails sent through the user self service to
  prevent rejection by certain email providers (:uv:bug:`57953`).

* The UMC module is now a singleton, that means that multiple requests won't create
  new instances of the module, but will be handled by one single module process.
  This can greatly increase performance and decrease memory consumption
  (:uv:bug:`57609`).

.. _changelog-umc-reports:

Univention Directory Reports
============================

* Fixed the handling of UDM properties with complex syntax, for example
  ``dnsEntryZoneForward``, that prevented users from using them in customized
  report templates (:uv:bug:`57431`).

.. _changelog-umc-diagnostic:

System diagnostic module
========================

* The diagnostic check ``04_saml_certificate_check`` could show a traceback if
  UMC wasn't configured for any kind of single sign-on. This has been fixed
  (:uv:bug:`57746`).

* The script :command:`univention-report-support-info` now keeps the generated archive
  per default. The option ``--cleanup`` has been added to the script, to
  overrule this new behavior (:uv:bug:`57641`).

.. _changelog-umc-ldap:

LDAP directory browser
======================

* When using OpenID Connect login the Univention Management Console Univention Directory
  Manager Module sometimes wouldn't load when the LDAP server was restarted
  (:uv:bug:`57533`).

.. _changelog-lib:

*************************
Univention base libraries
*************************

* OpenLDAP is now configured to use the ``sortvals`` option for the attributes
  ``uniqueMember`` and ``memberUid``. This improves the performance when modifying
  user objects or group objects in environments with groups with several thousand members. The
  attributes for the ``sortvals`` option can be configured via the UCR variable
  |UCSUCRV| :envvar:`ldap/server/sortvals` (:uv:bug:`52175`).

.. _changelog-deployment:

*******************
Software deployment
*******************

* After a system update through the *Software Update* UMC module, the user now
  stays in the module to view the system status instead of being redirected to
  the UMC overview page (:uv:bug:`57838`).

* Don't provide the option to update to a new UCS release if some Docker apps
  aren't yet released for that release (:uv:bug:`57802`).

.. _changelog-service:

***************
System services
***************

.. _changelog-service-saml:

SAML
====

* Fixed the link to the 5.2 changelog in ``univention-keycloak-migration-status``
  (:uv:bug:`57975`).

* The tool ``univention-keycloak`` was enabled to update an existing
  authentication flow so that it replaces the Kerberos authentication step with
  a conditional sub-flow which can enable Kerberos authentication depending on
  the client IP address (:uv:bug:`56474`).

* The script :command:`univention-keycloak-migration-status` has been adjusted to check
  the setting :envvar:`ucs/server/sso/uri`, which will be used from UCS 5.2 onward
  (:uv:bug:`57806`).

* Skip ``91univention-saml.inst`` in case the primary is on UCS 5.2. In this case
  :program:`simpleSAMLphp` is no longer supported and the steps in
  ``91univention-saml.inst`` aren't needed (:uv:bug:`57839`).

.. _changelog-service-proxy:

Proxy services
==============

* You can now manually configure the squid cache settings. Any value other than
  ``ufs`` in the UCR variable :envvar:`squid/cache/format` disables the cache configuration in
  :file:`squid.conf`. A custom squid cache configuration can be added to
  :file:`/etc/squid/local.conf` (:uv:bug:`57963`).


.. _changelog-win:

********************
Services for Windows
********************

.. _changelog-win-samba:

Samba
=====

* Since updating from Kernel 4.19 to Kernel 5.10 the behavior of the ``xfs``
  file system seems to have changed with respect to the handling of ``xattrs``. As a
  symptom, ``rsync -aAX`` as used by the script ``sysvol-sync.sh`` seems to remove
  ``trusted.SGI_ACL_FILE`` and ``trusted.SGI_ACL_DEFAULT`` when synchronizing from
  the SYSVOL from a system with an ``ext4`` partition, which doesn't have those,
  but only the usual ``system.posix_acl_access`` and ``system.posix_acl_default``.
  The script ``sysvol-sync.sh`` has been adjusted to filter the synchronized
  ``xattrs`` to only consider ``security.NTACL`` and not touch any other ``xattrs``
  (:uv:bug:`57529`).

* The join script has been adjusted to stop :program:`winbindd` first during provisioning.
  This should avoid unnecessary waiting time when stopping the other samba
  processes in the next step (:uv:bug:`57310`).

* In environments where the *Active Directory Domain Controller* app has been configured to use ``mdb`` as
  backend key value store for the ``sam.ldb`` database, the command :command:`samba-tool
  domain backup offline` could run into a deadlock in case parallel changes to
  the ``sam.ldb`` where made, for example through dynamic DNS updates. That command is used
  by the script ``univention-samba4-backup``. This was caused by an interplay of
  three components, the script ``samba-tool``, the command ``mdb_copy`` and the
  process attempting to modify the ``sam.ldb``. This update avoids this issue by
  reverting upstream changes made for Samba bug 14676 which where introduced
  there in anticipation of ``lmdb`` version ``0.9.26``, which UCS ``5.0`` doesn't use
  (:uv:bug:`57734`).


* The init script :file:`/etc/init.d/samba-ad-dc` has been adjusted to explicitly
  stop ``winbindd`` and ``smbd`` processes too and also check for ``pids`` in their
  respective process group. This can be necessary during package updates, in
  case the ``winbind.postinst`` and ``samba.postinst`` scripts start these
  processes separately instead of as child of the main ``samba`` process. This
  should avoid :command:`/etc/init.d/samba restart`` failing with error message
  ``NT_STATUS_ADDRESS_ALREADY_ASSOCIATED`` in ``log.samba`` (:uv:bug:`57310`).


.. _changelog-win-adc:

Univention Active Directory Connection
======================================

* Rejects in the connector for objects in AD that can't be completely read are
  now properly deleted (:uv:bug:`57737`).

* Starting with UCS 5.0-0 the *AD Connector* had an issue with rewriting mixed
  case AD DNs in the presence of a custom ``position_mapping``. This problem has
  been fixed, so that mixed case DNs from AD are mapped properly to UCS LDAP
  DNs again, avoiding unintelligible rejects (:uv:bug:`57565`).

