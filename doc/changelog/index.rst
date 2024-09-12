.. SPDX-FileCopyrightText: 2021-2024 Univention GmbH
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

* UCS 5.0-9 includes all issued security updates issued for UCS 5.0-8:

  * :program:`aom` (:uv:cve:`2024-5171`) (:uv:bug:`57497`)

  * :program:`apache2` (:uv:cve:`2024-36387`, :uv:cve:`2024-38476`,
    :uv:cve:`2024-38477`, :uv:cve:`2024-38573`, :uv:cve:`2024-39884`,
    :uv:cve:`2024-40725`) (:uv:bug:`57554`)

  * :program:`bind9` (:uv:cve:`2023-4408`, :uv:cve:`2024-1737`,
    :uv:cve:`2024-1975`) (:uv:bug:`57558`)

  * :program:`binutils` (:uv:cve:`2018-1000876`, :uv:cve:`2018-12934`)
    (:uv:bug:`57462`)

  * :program:`bluez` (:uv:cve:`2023-50229`, :uv:cve:`2023-50230`)
    (:uv:bug:`57571`)

  * :program:`cups` (:uv:cve:`2024-35235`) (:uv:bug:`57382`)

  * :program:`curl` (:uv:cve:`2024-7264`) (:uv:bug:`57503`)

  * :program:`dovecot` (:uv:cve:`2024-23184`, :uv:cve:`2024-23185`)
    (:uv:bug:`57570`)

  * :program:`emacs` (:uv:cve:`2024-39331`) (:uv:bug:`57416`)

  * :program:`exim4` (:uv:cve:`2024-39929`) (:uv:bug:`57496`)

  * :program:`firefox-esr` (:uv:cve:`2024-5688`, :uv:cve:`2024-5690`,
    :uv:cve:`2024-5691`, :uv:cve:`2024-5693`, :uv:cve:`2024-5696`,
    :uv:cve:`2024-5700`, :uv:cve:`2024-5702`) (:uv:bug:`57385`)

  * :program:`gdk-pixbuf` (:uv:cve:`2022-48622`) (:uv:bug:`57523`)

  * :program:`git` (:uv:cve:`2019-1387`, :uv:cve:`2023-25652`,
    :uv:cve:`2023-25815`, :uv:cve:`2023-29007`, :uv:cve:`2024-32002`,
    :uv:cve:`2024-32004`, :uv:cve:`2024-32021`, :uv:cve:`2024-32465`)
    (:uv:bug:`57412`)

  * :program:`glibc` (:uv:cve:`2024-33599`, :uv:cve:`2024-33600`,
    :uv:cve:`2024-33601`, :uv:cve:`2024-33602`) (:uv:bug:`57415`)

  * :program:`imagemagick` (:uv:cve:`2023-1289`, :uv:cve:`2023-34151`)
    (:uv:bug:`57461`, :uv:bug:`57478`)

  * :program:`intel-microcode` (:uv:cve:`2023-42667`,
    :uv:cve:`2023-45733`, :uv:cve:`2023-45745`, :uv:cve:`2023-46103`,
    :uv:cve:`2023-47855`, :uv:cve:`2023-49141`, :uv:cve:`2024-24853`,
    :uv:cve:`2024-24980`, :uv:cve:`2024-25939`) (:uv:bug:`57557`)

  * :program:`krb5` (:uv:cve:`2024-26458`, :uv:cve:`2024-26461`,
    :uv:cve:`2024-37370`, :uv:cve:`2024-37371`) (:uv:bug:`57476`)

  * :program:`libvpx` (:uv:cve:`2024-5197`) (:uv:bug:`57387`)

  * :program:`libxml2` (:uv:cve:`2016-3709`, :uv:cve:`2022-2309`)
    (:uv:bug:`57573`)

  * :program:`linux` (:uv:cve:`2021-33630`, :uv:cve:`2022-48627`,
    :uv:cve:`2023-0386`, :uv:cve:`2023-46838`, :uv:cve:`2023-47233`,
    :uv:cve:`2023-52340`, :uv:cve:`2023-52429`, :uv:cve:`2023-52436`,
    :uv:cve:`2023-52439`, :uv:cve:`2023-52443`, :uv:cve:`2023-52444`,
    :uv:cve:`2023-52445`, :uv:cve:`2023-52449`, :uv:cve:`2023-52464`,
    :uv:cve:`2023-52469`, :uv:cve:`2023-52470`, :uv:cve:`2023-52486`,
    :uv:cve:`2023-52583`, :uv:cve:`2023-52587`, :uv:cve:`2023-52594`,
    :uv:cve:`2023-52599`, :uv:cve:`2023-52600`, :uv:cve:`2023-52601`,
    :uv:cve:`2023-52602`, :uv:cve:`2023-52603`, :uv:cve:`2023-52604`,
    :uv:cve:`2023-52609`, :uv:cve:`2023-52612`, :uv:cve:`2023-52615`,
    :uv:cve:`2023-52619`, :uv:cve:`2023-52620`, :uv:cve:`2023-52622`,
    :uv:cve:`2023-52623`, :uv:cve:`2023-52628`, :uv:cve:`2023-52644`,
    :uv:cve:`2023-52650`, :uv:cve:`2023-52670`, :uv:cve:`2023-52679`,
    :uv:cve:`2023-52683`, :uv:cve:`2023-52691`, :uv:cve:`2023-52693`,
    :uv:cve:`2023-52698`, :uv:cve:`2023-52699`, :uv:cve:`2023-52880`,
    :uv:cve:`2023-6040`, :uv:cve:`2023-6270`, :uv:cve:`2023-7042`,
    :uv:cve:`2024-0340`, :uv:cve:`2024-0607`, :uv:cve:`2024-1086`,
    :uv:cve:`2024-22099`, :uv:cve:`2024-23849`, :uv:cve:`2024-24857`,
    :uv:cve:`2024-24858`, :uv:cve:`2024-24861`, :uv:cve:`2024-25739`,
    :uv:cve:`2024-26597`, :uv:cve:`2024-26600`, :uv:cve:`2024-26602`,
    :uv:cve:`2024-26606`, :uv:cve:`2024-26615`, :uv:cve:`2024-26625`,
    :uv:cve:`2024-26633`, :uv:cve:`2024-26635`, :uv:cve:`2024-26636`,
    :uv:cve:`2024-26642`, :uv:cve:`2024-26645`, :uv:cve:`2024-26651`,
    :uv:cve:`2024-26663`, :uv:cve:`2024-26664`, :uv:cve:`2024-26671`,
    :uv:cve:`2024-26675`, :uv:cve:`2024-26679`, :uv:cve:`2024-26685`,
    :uv:cve:`2024-26696`, :uv:cve:`2024-26697`, :uv:cve:`2024-26704`,
    :uv:cve:`2024-26720`, :uv:cve:`2024-26722`, :uv:cve:`2024-26735`,
    :uv:cve:`2024-26744`, :uv:cve:`2024-26752`, :uv:cve:`2024-26754`,
    :uv:cve:`2024-26763`, :uv:cve:`2024-26764`, :uv:cve:`2024-26766`,
    :uv:cve:`2024-26772`, :uv:cve:`2024-26773`, :uv:cve:`2024-26777`,
    :uv:cve:`2024-26778`, :uv:cve:`2024-26779`, :uv:cve:`2024-26791`,
    :uv:cve:`2024-26793`, :uv:cve:`2024-26801`, :uv:cve:`2024-26805`,
    :uv:cve:`2024-26816`, :uv:cve:`2024-26817`, :uv:cve:`2024-26820`,
    :uv:cve:`2024-26825`, :uv:cve:`2024-26839`, :uv:cve:`2024-26840`,
    :uv:cve:`2024-26845`, :uv:cve:`2024-26851`, :uv:cve:`2024-26852`,
    :uv:cve:`2024-26857`, :uv:cve:`2024-26859`, :uv:cve:`2024-26863`,
    :uv:cve:`2024-26874`, :uv:cve:`2024-26875`, :uv:cve:`2024-26878`,
    :uv:cve:`2024-26880`, :uv:cve:`2024-26883`, :uv:cve:`2024-26884`,
    :uv:cve:`2024-26889`, :uv:cve:`2024-26894`, :uv:cve:`2024-26901`,
    :uv:cve:`2024-26903`, :uv:cve:`2024-26917`, :uv:cve:`2024-26922`,
    :uv:cve:`2024-26923`, :uv:cve:`2024-26931`, :uv:cve:`2024-26934`,
    :uv:cve:`2024-26955`, :uv:cve:`2024-26956`, :uv:cve:`2024-26965`,
    :uv:cve:`2024-26966`, :uv:cve:`2024-26969`, :uv:cve:`2024-26973`,
    :uv:cve:`2024-26974`, :uv:cve:`2024-26976`, :uv:cve:`2024-26981`,
    :uv:cve:`2024-26984`, :uv:cve:`2024-26993`, :uv:cve:`2024-26994`,
    :uv:cve:`2024-26997`, :uv:cve:`2024-27001`, :uv:cve:`2024-27008`,
    :uv:cve:`2024-27013`, :uv:cve:`2024-27020`, :uv:cve:`2024-27024`,
    :uv:cve:`2024-27028`, :uv:cve:`2024-27043`, :uv:cve:`2024-27046`,
    :uv:cve:`2024-27059`, :uv:cve:`2024-27074`, :uv:cve:`2024-27075`,
    :uv:cve:`2024-27077`, :uv:cve:`2024-27078`, :uv:cve:`2024-27388`,
    :uv:cve:`2024-27395`, :uv:cve:`2024-27396`, :uv:cve:`2024-27398`,
    :uv:cve:`2024-27399`, :uv:cve:`2024-27401`, :uv:cve:`2024-27405`,
    :uv:cve:`2024-27410`, :uv:cve:`2024-27412`, :uv:cve:`2024-27413`,
    :uv:cve:`2024-27416`, :uv:cve:`2024-27419`, :uv:cve:`2024-27436`,
    :uv:cve:`2024-31076`, :uv:cve:`2024-33621`, :uv:cve:`2024-35789`,
    :uv:cve:`2024-35806`, :uv:cve:`2024-35807`, :uv:cve:`2024-35809`,
    :uv:cve:`2024-35815`, :uv:cve:`2024-35819`, :uv:cve:`2024-35821`,
    :uv:cve:`2024-35822`, :uv:cve:`2024-35823`, :uv:cve:`2024-35825`,
    :uv:cve:`2024-35828`, :uv:cve:`2024-35830`, :uv:cve:`2024-35835`,
    :uv:cve:`2024-35847`, :uv:cve:`2024-35849`, :uv:cve:`2024-35877`,
    :uv:cve:`2024-35886`, :uv:cve:`2024-35888`, :uv:cve:`2024-35893`,
    :uv:cve:`2024-35898`, :uv:cve:`2024-35902`, :uv:cve:`2024-35910`,
    :uv:cve:`2024-35915`, :uv:cve:`2024-35922`, :uv:cve:`2024-35925`,
    :uv:cve:`2024-35930`, :uv:cve:`2024-35933`, :uv:cve:`2024-35935`,
    :uv:cve:`2024-35936`, :uv:cve:`2024-35944`, :uv:cve:`2024-35947`,
    :uv:cve:`2024-35955`, :uv:cve:`2024-35960`, :uv:cve:`2024-35969`,
    :uv:cve:`2024-35973`, :uv:cve:`2024-35978`, :uv:cve:`2024-35982`,
    :uv:cve:`2024-35984`, :uv:cve:`2024-35997`, :uv:cve:`2024-36004`,
    :uv:cve:`2024-36014`, :uv:cve:`2024-36015`, :uv:cve:`2024-36016`,
    :uv:cve:`2024-36017`, :uv:cve:`2024-36020`, :uv:cve:`2024-36286`,
    :uv:cve:`2024-36288`, :uv:cve:`2024-36883`, :uv:cve:`2024-36886`,
    :uv:cve:`2024-36902`, :uv:cve:`2024-36904`, :uv:cve:`2024-36905`,
    :uv:cve:`2024-36919`, :uv:cve:`2024-36933`, :uv:cve:`2024-36934`,
    :uv:cve:`2024-36940`, :uv:cve:`2024-36941`, :uv:cve:`2024-36946`,
    :uv:cve:`2024-36950`, :uv:cve:`2024-36954`, :uv:cve:`2024-36959`,
    :uv:cve:`2024-36960`, :uv:cve:`2024-36964`, :uv:cve:`2024-36971`,
    :uv:cve:`2024-37353`, :uv:cve:`2024-37356`, :uv:cve:`2024-38381`,
    :uv:cve:`2024-38549`, :uv:cve:`2024-38552`, :uv:cve:`2024-38558`,
    :uv:cve:`2024-38559`, :uv:cve:`2024-38560`, :uv:cve:`2024-38565`,
    :uv:cve:`2024-38567`, :uv:cve:`2024-38578`, :uv:cve:`2024-38579`,
    :uv:cve:`2024-38582`, :uv:cve:`2024-38583`, :uv:cve:`2024-38587`,
    :uv:cve:`2024-38589`, :uv:cve:`2024-38596`, :uv:cve:`2024-38598`,
    :uv:cve:`2024-38599`, :uv:cve:`2024-38601`, :uv:cve:`2024-38612`,
    :uv:cve:`2024-38618`, :uv:cve:`2024-38621`, :uv:cve:`2024-38627`,
    :uv:cve:`2024-38633`, :uv:cve:`2024-38634`, :uv:cve:`2024-38637`,
    :uv:cve:`2024-38659`, :uv:cve:`2024-38780`, :uv:cve:`2024-39292`)
    (:uv:bug:`57414`)

  * :program:`linux-5.10` (:uv:cve:`2022-48655`, :uv:cve:`2023-52585`,
    :uv:cve:`2024-26900`, :uv:cve:`2024-27398`, :uv:cve:`2024-27399`,
    :uv:cve:`2024-27401`, :uv:cve:`2024-35848`) (:uv:bug:`57434`)

  * :program:`linux-latest` (:uv:cve:`2021-33630`,
    :uv:cve:`2022-48627`, :uv:cve:`2023-0386`, :uv:cve:`2023-46838`,
    :uv:cve:`2023-47233`, :uv:cve:`2023-52340`, :uv:cve:`2023-52429`,
    :uv:cve:`2023-52436`, :uv:cve:`2023-52439`, :uv:cve:`2023-52443`,
    :uv:cve:`2023-52444`, :uv:cve:`2023-52445`, :uv:cve:`2023-52449`,
    :uv:cve:`2023-52464`, :uv:cve:`2023-52469`, :uv:cve:`2023-52470`,
    :uv:cve:`2023-52486`, :uv:cve:`2023-52583`, :uv:cve:`2023-52587`,
    :uv:cve:`2023-52594`, :uv:cve:`2023-52599`, :uv:cve:`2023-52600`,
    :uv:cve:`2023-52601`, :uv:cve:`2023-52602`, :uv:cve:`2023-52603`,
    :uv:cve:`2023-52604`, :uv:cve:`2023-52609`, :uv:cve:`2023-52612`,
    :uv:cve:`2023-52615`, :uv:cve:`2023-52619`, :uv:cve:`2023-52620`,
    :uv:cve:`2023-52622`, :uv:cve:`2023-52623`, :uv:cve:`2023-52628`,
    :uv:cve:`2023-52644`, :uv:cve:`2023-52650`, :uv:cve:`2023-52670`,
    :uv:cve:`2023-52679`, :uv:cve:`2023-52683`, :uv:cve:`2023-52691`,
    :uv:cve:`2023-52693`, :uv:cve:`2023-52698`, :uv:cve:`2023-52699`,
    :uv:cve:`2023-52880`, :uv:cve:`2023-6040`, :uv:cve:`2023-6270`,
    :uv:cve:`2023-7042`, :uv:cve:`2024-0340`, :uv:cve:`2024-0607`,
    :uv:cve:`2024-1086`, :uv:cve:`2024-22099`, :uv:cve:`2024-23849`,
    :uv:cve:`2024-24857`, :uv:cve:`2024-24858`, :uv:cve:`2024-24861`,
    :uv:cve:`2024-25739`, :uv:cve:`2024-26597`, :uv:cve:`2024-26600`,
    :uv:cve:`2024-26602`, :uv:cve:`2024-26606`, :uv:cve:`2024-26615`,
    :uv:cve:`2024-26625`, :uv:cve:`2024-26633`, :uv:cve:`2024-26635`,
    :uv:cve:`2024-26636`, :uv:cve:`2024-26642`, :uv:cve:`2024-26645`,
    :uv:cve:`2024-26651`, :uv:cve:`2024-26663`, :uv:cve:`2024-26664`,
    :uv:cve:`2024-26671`, :uv:cve:`2024-26675`, :uv:cve:`2024-26679`,
    :uv:cve:`2024-26685`, :uv:cve:`2024-26696`, :uv:cve:`2024-26697`,
    :uv:cve:`2024-26704`, :uv:cve:`2024-26720`, :uv:cve:`2024-26722`,
    :uv:cve:`2024-26735`, :uv:cve:`2024-26744`, :uv:cve:`2024-26752`,
    :uv:cve:`2024-26754`, :uv:cve:`2024-26763`, :uv:cve:`2024-26764`,
    :uv:cve:`2024-26766`, :uv:cve:`2024-26772`, :uv:cve:`2024-26773`,
    :uv:cve:`2024-26777`, :uv:cve:`2024-26778`, :uv:cve:`2024-26779`,
    :uv:cve:`2024-26791`, :uv:cve:`2024-26793`, :uv:cve:`2024-26801`,
    :uv:cve:`2024-26805`, :uv:cve:`2024-26816`, :uv:cve:`2024-26817`,
    :uv:cve:`2024-26820`, :uv:cve:`2024-26825`, :uv:cve:`2024-26839`,
    :uv:cve:`2024-26840`, :uv:cve:`2024-26845`, :uv:cve:`2024-26851`,
    :uv:cve:`2024-26852`, :uv:cve:`2024-26857`, :uv:cve:`2024-26859`,
    :uv:cve:`2024-26863`, :uv:cve:`2024-26874`, :uv:cve:`2024-26875`,
    :uv:cve:`2024-26878`, :uv:cve:`2024-26880`, :uv:cve:`2024-26883`,
    :uv:cve:`2024-26884`, :uv:cve:`2024-26889`, :uv:cve:`2024-26894`,
    :uv:cve:`2024-26901`, :uv:cve:`2024-26903`, :uv:cve:`2024-26917`,
    :uv:cve:`2024-26922`, :uv:cve:`2024-26923`, :uv:cve:`2024-26931`,
    :uv:cve:`2024-26934`, :uv:cve:`2024-26955`, :uv:cve:`2024-26956`,
    :uv:cve:`2024-26965`, :uv:cve:`2024-26966`, :uv:cve:`2024-26969`,
    :uv:cve:`2024-26973`, :uv:cve:`2024-26974`, :uv:cve:`2024-26976`,
    :uv:cve:`2024-26981`, :uv:cve:`2024-26984`, :uv:cve:`2024-26993`,
    :uv:cve:`2024-26994`, :uv:cve:`2024-26997`, :uv:cve:`2024-27001`,
    :uv:cve:`2024-27008`, :uv:cve:`2024-27013`, :uv:cve:`2024-27020`,
    :uv:cve:`2024-27024`, :uv:cve:`2024-27028`, :uv:cve:`2024-27043`,
    :uv:cve:`2024-27046`, :uv:cve:`2024-27059`, :uv:cve:`2024-27074`,
    :uv:cve:`2024-27075`, :uv:cve:`2024-27077`, :uv:cve:`2024-27078`,
    :uv:cve:`2024-27388`, :uv:cve:`2024-27395`, :uv:cve:`2024-27396`,
    :uv:cve:`2024-27398`, :uv:cve:`2024-27399`, :uv:cve:`2024-27401`,
    :uv:cve:`2024-27405`, :uv:cve:`2024-27410`, :uv:cve:`2024-27412`,
    :uv:cve:`2024-27413`, :uv:cve:`2024-27416`, :uv:cve:`2024-27419`,
    :uv:cve:`2024-27436`, :uv:cve:`2024-31076`, :uv:cve:`2024-33621`,
    :uv:cve:`2024-35789`, :uv:cve:`2024-35806`, :uv:cve:`2024-35807`,
    :uv:cve:`2024-35809`, :uv:cve:`2024-35815`, :uv:cve:`2024-35819`,
    :uv:cve:`2024-35821`, :uv:cve:`2024-35822`, :uv:cve:`2024-35823`,
    :uv:cve:`2024-35825`, :uv:cve:`2024-35828`, :uv:cve:`2024-35830`,
    :uv:cve:`2024-35835`, :uv:cve:`2024-35847`, :uv:cve:`2024-35849`,
    :uv:cve:`2024-35877`, :uv:cve:`2024-35886`, :uv:cve:`2024-35888`,
    :uv:cve:`2024-35893`, :uv:cve:`2024-35898`, :uv:cve:`2024-35902`,
    :uv:cve:`2024-35910`, :uv:cve:`2024-35915`, :uv:cve:`2024-35922`,
    :uv:cve:`2024-35925`, :uv:cve:`2024-35930`, :uv:cve:`2024-35933`,
    :uv:cve:`2024-35935`, :uv:cve:`2024-35936`, :uv:cve:`2024-35944`,
    :uv:cve:`2024-35947`, :uv:cve:`2024-35955`, :uv:cve:`2024-35960`,
    :uv:cve:`2024-35969`, :uv:cve:`2024-35973`, :uv:cve:`2024-35978`,
    :uv:cve:`2024-35982`, :uv:cve:`2024-35984`, :uv:cve:`2024-35997`,
    :uv:cve:`2024-36004`, :uv:cve:`2024-36014`, :uv:cve:`2024-36015`,
    :uv:cve:`2024-36016`, :uv:cve:`2024-36017`, :uv:cve:`2024-36020`,
    :uv:cve:`2024-36286`, :uv:cve:`2024-36288`, :uv:cve:`2024-36883`,
    :uv:cve:`2024-36886`, :uv:cve:`2024-36902`, :uv:cve:`2024-36904`,
    :uv:cve:`2024-36905`, :uv:cve:`2024-36919`, :uv:cve:`2024-36933`,
    :uv:cve:`2024-36934`, :uv:cve:`2024-36940`, :uv:cve:`2024-36941`,
    :uv:cve:`2024-36946`, :uv:cve:`2024-36950`, :uv:cve:`2024-36954`,
    :uv:cve:`2024-36959`, :uv:cve:`2024-36960`, :uv:cve:`2024-36964`,
    :uv:cve:`2024-36971`, :uv:cve:`2024-37353`, :uv:cve:`2024-37356`,
    :uv:cve:`2024-38381`, :uv:cve:`2024-38549`, :uv:cve:`2024-38552`,
    :uv:cve:`2024-38558`, :uv:cve:`2024-38559`, :uv:cve:`2024-38560`,
    :uv:cve:`2024-38565`, :uv:cve:`2024-38567`, :uv:cve:`2024-38578`,
    :uv:cve:`2024-38579`, :uv:cve:`2024-38582`, :uv:cve:`2024-38583`,
    :uv:cve:`2024-38587`, :uv:cve:`2024-38589`, :uv:cve:`2024-38596`,
    :uv:cve:`2024-38598`, :uv:cve:`2024-38599`, :uv:cve:`2024-38601`,
    :uv:cve:`2024-38612`, :uv:cve:`2024-38618`, :uv:cve:`2024-38621`,
    :uv:cve:`2024-38627`, :uv:cve:`2024-38633`, :uv:cve:`2024-38634`,
    :uv:cve:`2024-38637`, :uv:cve:`2024-38659`, :uv:cve:`2024-38780`,
    :uv:cve:`2024-39292`) (:uv:bug:`57414`)

  * :program:`linux-signed-5.10-amd64` (:uv:cve:`2022-48655`,
    :uv:cve:`2023-52585`, :uv:cve:`2024-26900`, :uv:cve:`2024-27398`,
    :uv:cve:`2024-27399`, :uv:cve:`2024-27401`, :uv:cve:`2024-35848`)
    (:uv:bug:`57434`)

  * :program:`linux-signed-amd64` (:uv:cve:`2021-33630`,
    :uv:cve:`2022-48627`, :uv:cve:`2023-0386`, :uv:cve:`2023-46838`,
    :uv:cve:`2023-47233`, :uv:cve:`2023-52340`, :uv:cve:`2023-52429`,
    :uv:cve:`2023-52436`, :uv:cve:`2023-52439`, :uv:cve:`2023-52443`,
    :uv:cve:`2023-52444`, :uv:cve:`2023-52445`, :uv:cve:`2023-52449`,
    :uv:cve:`2023-52464`, :uv:cve:`2023-52469`, :uv:cve:`2023-52470`,
    :uv:cve:`2023-52486`, :uv:cve:`2023-52583`, :uv:cve:`2023-52587`,
    :uv:cve:`2023-52594`, :uv:cve:`2023-52599`, :uv:cve:`2023-52600`,
    :uv:cve:`2023-52601`, :uv:cve:`2023-52602`, :uv:cve:`2023-52603`,
    :uv:cve:`2023-52604`, :uv:cve:`2023-52609`, :uv:cve:`2023-52612`,
    :uv:cve:`2023-52615`, :uv:cve:`2023-52619`, :uv:cve:`2023-52620`,
    :uv:cve:`2023-52622`, :uv:cve:`2023-52623`, :uv:cve:`2023-52628`,
    :uv:cve:`2023-52644`, :uv:cve:`2023-52650`, :uv:cve:`2023-52670`,
    :uv:cve:`2023-52679`, :uv:cve:`2023-52683`, :uv:cve:`2023-52691`,
    :uv:cve:`2023-52693`, :uv:cve:`2023-52698`, :uv:cve:`2023-52699`,
    :uv:cve:`2023-52880`, :uv:cve:`2023-6040`, :uv:cve:`2023-6270`,
    :uv:cve:`2023-7042`, :uv:cve:`2024-0340`, :uv:cve:`2024-0607`,
    :uv:cve:`2024-1086`, :uv:cve:`2024-22099`, :uv:cve:`2024-23849`,
    :uv:cve:`2024-24857`, :uv:cve:`2024-24858`, :uv:cve:`2024-24861`,
    :uv:cve:`2024-25739`, :uv:cve:`2024-26597`, :uv:cve:`2024-26600`,
    :uv:cve:`2024-26602`, :uv:cve:`2024-26606`, :uv:cve:`2024-26615`,
    :uv:cve:`2024-26625`, :uv:cve:`2024-26633`, :uv:cve:`2024-26635`,
    :uv:cve:`2024-26636`, :uv:cve:`2024-26642`, :uv:cve:`2024-26645`,
    :uv:cve:`2024-26651`, :uv:cve:`2024-26663`, :uv:cve:`2024-26664`,
    :uv:cve:`2024-26671`, :uv:cve:`2024-26675`, :uv:cve:`2024-26679`,
    :uv:cve:`2024-26685`, :uv:cve:`2024-26696`, :uv:cve:`2024-26697`,
    :uv:cve:`2024-26704`, :uv:cve:`2024-26720`, :uv:cve:`2024-26722`,
    :uv:cve:`2024-26735`, :uv:cve:`2024-26744`, :uv:cve:`2024-26752`,
    :uv:cve:`2024-26754`, :uv:cve:`2024-26763`, :uv:cve:`2024-26764`,
    :uv:cve:`2024-26766`, :uv:cve:`2024-26772`, :uv:cve:`2024-26773`,
    :uv:cve:`2024-26777`, :uv:cve:`2024-26778`, :uv:cve:`2024-26779`,
    :uv:cve:`2024-26791`, :uv:cve:`2024-26793`, :uv:cve:`2024-26801`,
    :uv:cve:`2024-26805`, :uv:cve:`2024-26816`, :uv:cve:`2024-26817`,
    :uv:cve:`2024-26820`, :uv:cve:`2024-26825`, :uv:cve:`2024-26839`,
    :uv:cve:`2024-26840`, :uv:cve:`2024-26845`, :uv:cve:`2024-26851`,
    :uv:cve:`2024-26852`, :uv:cve:`2024-26857`, :uv:cve:`2024-26859`,
    :uv:cve:`2024-26863`, :uv:cve:`2024-26874`, :uv:cve:`2024-26875`,
    :uv:cve:`2024-26878`, :uv:cve:`2024-26880`, :uv:cve:`2024-26883`,
    :uv:cve:`2024-26884`, :uv:cve:`2024-26889`, :uv:cve:`2024-26894`,
    :uv:cve:`2024-26901`, :uv:cve:`2024-26903`, :uv:cve:`2024-26917`,
    :uv:cve:`2024-26922`, :uv:cve:`2024-26923`, :uv:cve:`2024-26931`,
    :uv:cve:`2024-26934`, :uv:cve:`2024-26955`, :uv:cve:`2024-26956`,
    :uv:cve:`2024-26965`, :uv:cve:`2024-26966`, :uv:cve:`2024-26969`,
    :uv:cve:`2024-26973`, :uv:cve:`2024-26974`, :uv:cve:`2024-26976`,
    :uv:cve:`2024-26981`, :uv:cve:`2024-26984`, :uv:cve:`2024-26993`,
    :uv:cve:`2024-26994`, :uv:cve:`2024-26997`, :uv:cve:`2024-27001`,
    :uv:cve:`2024-27008`, :uv:cve:`2024-27013`, :uv:cve:`2024-27020`,
    :uv:cve:`2024-27024`, :uv:cve:`2024-27028`, :uv:cve:`2024-27043`,
    :uv:cve:`2024-27046`, :uv:cve:`2024-27059`, :uv:cve:`2024-27074`,
    :uv:cve:`2024-27075`, :uv:cve:`2024-27077`, :uv:cve:`2024-27078`,
    :uv:cve:`2024-27388`, :uv:cve:`2024-27395`, :uv:cve:`2024-27396`,
    :uv:cve:`2024-27398`, :uv:cve:`2024-27399`, :uv:cve:`2024-27401`,
    :uv:cve:`2024-27405`, :uv:cve:`2024-27410`, :uv:cve:`2024-27412`,
    :uv:cve:`2024-27413`, :uv:cve:`2024-27416`, :uv:cve:`2024-27419`,
    :uv:cve:`2024-27436`, :uv:cve:`2024-31076`, :uv:cve:`2024-33621`,
    :uv:cve:`2024-35789`, :uv:cve:`2024-35806`, :uv:cve:`2024-35807`,
    :uv:cve:`2024-35809`, :uv:cve:`2024-35815`, :uv:cve:`2024-35819`,
    :uv:cve:`2024-35821`, :uv:cve:`2024-35822`, :uv:cve:`2024-35823`,
    :uv:cve:`2024-35825`, :uv:cve:`2024-35828`, :uv:cve:`2024-35830`,
    :uv:cve:`2024-35835`, :uv:cve:`2024-35847`, :uv:cve:`2024-35849`,
    :uv:cve:`2024-35877`, :uv:cve:`2024-35886`, :uv:cve:`2024-35888`,
    :uv:cve:`2024-35893`, :uv:cve:`2024-35898`, :uv:cve:`2024-35902`,
    :uv:cve:`2024-35910`, :uv:cve:`2024-35915`, :uv:cve:`2024-35922`,
    :uv:cve:`2024-35925`, :uv:cve:`2024-35930`, :uv:cve:`2024-35933`,
    :uv:cve:`2024-35935`, :uv:cve:`2024-35936`, :uv:cve:`2024-35944`,
    :uv:cve:`2024-35947`, :uv:cve:`2024-35955`, :uv:cve:`2024-35960`,
    :uv:cve:`2024-35969`, :uv:cve:`2024-35973`, :uv:cve:`2024-35978`,
    :uv:cve:`2024-35982`, :uv:cve:`2024-35984`, :uv:cve:`2024-35997`,
    :uv:cve:`2024-36004`, :uv:cve:`2024-36014`, :uv:cve:`2024-36015`,
    :uv:cve:`2024-36016`, :uv:cve:`2024-36017`, :uv:cve:`2024-36020`,
    :uv:cve:`2024-36286`, :uv:cve:`2024-36288`, :uv:cve:`2024-36883`,
    :uv:cve:`2024-36886`, :uv:cve:`2024-36902`, :uv:cve:`2024-36904`,
    :uv:cve:`2024-36905`, :uv:cve:`2024-36919`, :uv:cve:`2024-36933`,
    :uv:cve:`2024-36934`, :uv:cve:`2024-36940`, :uv:cve:`2024-36941`,
    :uv:cve:`2024-36946`, :uv:cve:`2024-36950`, :uv:cve:`2024-36954`,
    :uv:cve:`2024-36959`, :uv:cve:`2024-36960`, :uv:cve:`2024-36964`,
    :uv:cve:`2024-36971`, :uv:cve:`2024-37353`, :uv:cve:`2024-37356`,
    :uv:cve:`2024-38381`, :uv:cve:`2024-38549`, :uv:cve:`2024-38552`,
    :uv:cve:`2024-38558`, :uv:cve:`2024-38559`, :uv:cve:`2024-38560`,
    :uv:cve:`2024-38565`, :uv:cve:`2024-38567`, :uv:cve:`2024-38578`,
    :uv:cve:`2024-38579`, :uv:cve:`2024-38582`, :uv:cve:`2024-38583`,
    :uv:cve:`2024-38587`, :uv:cve:`2024-38589`, :uv:cve:`2024-38596`,
    :uv:cve:`2024-38598`, :uv:cve:`2024-38599`, :uv:cve:`2024-38601`,
    :uv:cve:`2024-38612`, :uv:cve:`2024-38618`, :uv:cve:`2024-38621`,
    :uv:cve:`2024-38627`, :uv:cve:`2024-38633`, :uv:cve:`2024-38634`,
    :uv:cve:`2024-38637`, :uv:cve:`2024-38659`, :uv:cve:`2024-38780`,
    :uv:cve:`2024-39292`) (:uv:bug:`57414`)

  * :program:`nano` (:uv:cve:`2024-5742`) (:uv:bug:`57399`)

  * :program:`openjdk-11` (:uv:cve:`2024-21131`, :uv:cve:`2024-21138`,
    :uv:cve:`2024-21140`, :uv:cve:`2024-21144`, :uv:cve:`2024-21145`,
    :uv:cve:`2024-21147`) (:uv:bug:`57511`)

  * :program:`php7.3` (:uv:cve:`2024-5458`) (:uv:bug:`57400`)

  * :program:`postgresql-11` (:uv:cve:`2024-7348`) (:uv:bug:`57572`)

  * :program:`pymongo` (:uv:cve:`2024-5629`) (:uv:bug:`57386`)

  * :program:`python3.7` (:uv:cve:`2024-0397`, :uv:cve:`2024-4032`)
    (:uv:bug:`57477`)

  * :program:`ruby2.5` (:uv:cve:`2023-28755`, :uv:cve:`2023-36617`,
    :uv:cve:`2024-27280`, :uv:cve:`2024-27281`, :uv:cve:`2024-27282`)
    (:uv:bug:`57524`)

  * :program:`systemd` (:uv:cve:`2023-50387`, :uv:cve:`2023-50868`,
    :uv:cve:`2023-7008`) (:uv:bug:`57559`)

  * :program:`wpa` (:uv:cve:`2024-5290`) (:uv:bug:`57519`)


.. _debian:

* UCS 5.0-9 includes the following updated packages from Debian ELTS:

  :program:`FIXME`

.. _maintained:

* The following packages have been moved to the maintained repository of UCS:

  :program:`FIXME`

.. _changelog-domain:

***************
Domain services
***************

* The meta-package ``univention-role-server-common`` now installs ``linux-
  image-5.10-amd64`` instead of ``linux-image-amd64``. After the update a reboot
  is recommended to load the new kernel version (:uv:bug:`57427`).

.. _changelog-udm:

LDAP Directory Manager
======================

* In case a UDM property syntax has been overridden via UCR but the specified
  value does not correspond to any defined syntax, UDM logged a traceback. This
  has now been replaced by a proper log message explaining the origin of the
  problem (:uv:bug:`57484`).

* A traceback that was thrown when running ``univention-sync-memberuid`` has
  been fixed. The script now also supports limiting operation to certain
  groups, or excluding certain groups (:uv:bug:`57439`).

* The LDAP attribute ``shadowExpire`` was calculated in a way which resulted in
  users expiring one day later than expected in certain timezones. This has
  been corrected (:uv:bug:`46349`).

* The UDM module ``settings/directory`` provides the default container setting
  for other UDM modules. It is now possible to extend ``settings/directory`` with
  an extended attribute to define default containers for custom UDM modules.
  The name of the ``settings/directory`` property, that defines the default
  container for your module, can be defined by the variable
  ``default_containers_attribute_name`` in the module (:uv:bug:`57526`).

* When the IP address is set when creating a new computer object, the DNS
  entries for this object were not set correctly since erratum 738. The DNS
  entries will now be created correctly again (:uv:bug:`56313`).

* When searching for objects via UDM it was possible to create a faulty state,
  when an object included in the result was deleted before the operation was
  finished. Those deleted objects are now skipped (:uv:bug:`53333`).

.. _changelog-umc:

*****************************
Univention Management Console
*****************************

.. _changelog-umc-portal:

Univention Portal
=================

* All browser tabs where the user is logged into the Portal will now
  automatically refresh when a logout is detected. This feature is enabled by
  default and can be toggled with the Univention Configuration Registry
  Variable ``portal/reload-tabs-on-logout`` (:uv:bug:`57467`).

* The login button in the Portal's sidebar can now be configured to perform
  OIDC authentication by setting the UCR variable ``portal/auth-mode`` to the
  value ``oidc`` (:uv:bug:`57534`).

* The default for ``portal/reload-tabs-on-logout`` has been changed to ``false``
  (:uv:bug:`57562`).

.. _changelog-umc-server:

Univention Management Console server
====================================

* Ensure that ``/usr/share/univention-management-console/oidc/oidc.json`` has
  file permission ``600`` (:uv:bug:`57505`).

* A new endpoint has been added to the UMC, supporting the refresh of all
  browser tabs with the Portal open when a user logs out (:uv:bug:`57467`).

* Added ``oidc-id-token`` hint to UMC logout to disable Keycloak's logout
  confirmation dialog (:uv:bug:`57475`).

* Add a configurable SQL storage for UMC sessions. This now makes OIDC
  backchannel logout possible if the UMC is run in multiprocessing mode
  (:uv:bug:`57482`).

* Fix a bug where it was impossible to change passwords via the UMC due to the
  UMC server not closing file descriptors properly (:uv:bug:`57194`).

* Do not show the OpenID Connect permission consent screen when the UMC is the
  relying party (:uv:bug:`57506`).

* Better support for Portal/UMC OIDC setup with FQDN different from internal
  UCS name (:uv:bug:`57483`).

.. _changelog-umc-appcenter:

Univention App Center
=====================

* ``univention-app configure`` can now be called with ``--set`` being specified
  multiple times (:uv:bug:`57546`).

* The appcenter now executes the joinscript and the configure scripts during
  upgrade in the same order as during the initial installation
  (:uv:bug:`57544`).

.. _changelog-umc-join:

Domain join module
==================

* A bug has been fixed that could cause the domain join to fail if the
  /etc/univention/ssl directory was too big (:uv:bug:`57421`).

.. _changelog-umc-user:

User management
===============

* When a password policy is used together with the self-registration feature it
  was possible that invitation emails were not sent when users are created.
  This was fixed by adjusting the self-service listener module filter
  (:uv:bug:`57226`).

.. _changelog-umc-diagnostic:

System diagnostic module
========================

* The diagnostics module to check for local LDAP schema files and register them
  as an LDAP extension has been fixed and now actually passes the right
  argument to the internal function (:uv:bug:`57279`).

* A diagnostic module now checks for the correct file permissions of the SQLite
  database of both the S4-Connector and the AD-Connector (:uv:bug:`57453`).

* The package ``screen`` has been added to the recommendations as it is a vital
  part of Univention's support. The package has been cut since 5.0-6 while
  optimizing installation size, but is now re-added. The package should be
  automatically installed with this update (:uv:bug:`57406`).

.. _changelog-lib:

*************************
Univention base libraries
*************************

* An ACL has been added that restricts access to the new UMC settings object
  (:uv:bug:`57482`).

* A typo in evaluation of the UCR variable ``backup/clean/min_backups`` caused
  that the specified limit was not considered but instead the default value of
  ``10`` was applied. This has been fixed (:uv:bug:`56736`).

.. _changelog-deployment:

*******************
Software deployment
*******************

* The script ``univention-prune-kernels`` has been adjusted to the new kernel
  version linux-5.10 (:uv:bug:`57427`).

.. _changelog-service:

***************
System services
***************

.. _changelog-service-saml:

SAML
====

* Prevent the creation of two mappers in the default Univention Managment
  Console Keycloak SAML client which caused SAML logins to fail
  (:uv:bug:`57420`).

* In ``univention-keycloak``, fix the option ``--no-frontchannel-logout`` when
  dealing with OIDC Relying parties. It used to activate the frontchannel
  logout, not deactivate it as it was supposed to do (and now does,
  :uv:bug:`57518`).

* The univention-keycloak CLI was fixed, so that you can use --set multiple
  times in the domain-config sub command, as documented (:uv:bug:`57375`).

* There was an error where a provided XML file during serviceprovider creation
  overwrote the options passed on the ``CLI``. This resulted in some of the
  migration guide example creations not working anymore (:uv:bug:`57320`).

* ``univention-keycloak`` had to adapted to Keycloak version 25 to correctly
  create the configuration for the legacy authorization (:uv:bug:`57452`).

.. _changelog-service-cups:

Printing services
=================

* :program:`CUPS` now uses the UCS TLS certificate instead of a self-signed
  certificate (:uv:bug:`52879`).

.. _changelog-win:

********************
Services for Windows
********************

.. _changelog-win-s4c:

Univention S4 Connector
=======================

* SQLite databases used by the S4 Connector were world readable. This has been
  changed (:uv:bug:`57453`).

* The S4-Connector used to skip synchronizing a move operation, if the moved
  object is already present in its DN cache. This could result in the unwanted
  deletion of objects during a subtree rename (:uv:bug:`57510`).

.. _changelog-win-adc:

Univention Active Directory Connection
======================================

* The AD-Connector used to skip synchronizing a move operation, if the moved
  object is already present in its DN cache. This could result in the unwanted
  deletion of objects during a subtree rename (:uv:bug:`57510`).

* The connector can now be configured to only synchronize objects from specific
  subtrees via the newly added UCR variables
  ``connector/ad/mapping/allowsubtree/$NAME/ucs`` and
  ``connector/ad/mapping/allowsubtree/$NAME/ad``. ``$NAME`` is an arbitrary string,
  the value for the ``ucs`` variable is a subtree LDAP DN in the UCS directory
  and the value for the ``ad`` variable is a subtree LDAP DN of the AD directory.
  Both must include the LDAP base of the respective directory. If configured
  only objects from these subtrees are synchronized, everything else is ignored
  (:uv:bug:`57394`).

* The connector can now be configured to only synchronize objects that match a
  specific LDAP filter. For each object type in ``user``, ``group``, ``container``,
  ``ou`` and ``windowscomputer`` the UCR variable ``connector/ad/mapping/{object
  type}/allowfilter`` can be used to configure this LDAP filter
  (:uv:bug:`57442`).

* The connector can now be configured to ignore certain objects that match a
  specific LDAP filter. For each object type in ``user``, ``group``, ``container``,
  ``ou`` and ``windowscomputer`` the UCR variable ``connector/ad/mapping/{object
  type}/ignorefilter`` can be used to configure this LDAP filter
  (:uv:bug:`57465`).

* SQLite databases used by the AD Connector were world readable in certain
  cases. This has been changed (:uv:bug:`57453`).

* The ``dn`` argument of ``resync_object_from_ad.py`` was set as not required
  (:uv:bug:`57504`).

