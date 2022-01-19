#!/usr/bin/pytest-3

from binascii import a2b_hex

import pytest

import univention.radius.pyMsChapV2 as mut


def test_nthash():
    password_hash = b'\x44\xEB\xBA\x8D\x53\x12\xB8\xD6\x11\x47\x44\x11\xF5\x69\x89\xAE'
    password_hash_hash = b'\x41\xC0\x0C\x58\x4B\xD2\xD9\x1C\x40\x17\xA2\xA1\x2F\xA5\x9F\x3F'
    assert mut.HashNtPasswordHash(password_hash) == password_hash_hash


@pytest.mark.parametrize("key,data,exp", [
    ('CAA1239D44DA7EDF926BCE39F5C65D0F', '4c29654e436e7844', '1cffa87d8b48ce73a71e3e6c9a9dd80f112d48dfeea8792c'),
    ('3b1b47e42e0463276e3ded6cef349f93', 'b019d38bad875c9d', 'e6285df3287c5d194f84df1a94817c7282d09754b6f9e02a'),
    ('624aac413795cdc1ff17365faf1ffe89', '6da297169f7aa9c2', '2e17884ea16177e2b751d53b5cc756c3cd57cdfd6e3bf8b9'),
    ('3b1b47e42e0463276e3ded6cef349f93', 'eacf7d5a2a6fa7d4', 'd2025bc5d6c201af7472550a677ca9904245a16ebb542a8e'),
    ('ae33a32dca8c9821844f740d5b3f4d6c', '677f1c557a5ee96c', '1bb250184772028e54394762ded81de1f608e6f37e7de5b0'),
    ('c4ea95cb148df11bf9d7c3611ad6d722', '514246973ea892c1', '497e9072282f5d33529e7359177d42ac9e106600630d3a6d'),
    ('cd06ca7c7e10c99b1d33b7485a2ed808', '0123456789abcdef', '25a98c1c31e81847466b29b2df4680f39958fb8c213a9cc6'),
    ('ff3750bcc2b22412c2265b23734e0dac', '0123456789abcdef', 'c337cd5cbd44fc9782a667af6d427c6de67c20c2d3e77c56'),
    ('04b8e0ba74289cc540826bab1dee63ae', 'ffffff0011223344', 'c951c8b1ddf71b2f8ec0be33f21ad93b7cd5fb2cd6cf51c5'),
    # see https://forge.univention.org/bugzilla/show_bug.cgi?id=38785
    ('00563126f04f3875c417f789b00e72d2', '5355f4fc60c8888a', '9681672b365655d0592c3e4009547b9e11bc751b6e97943b'),
])
def test_mschapv2(key, data, exp):
    assert mut.ChallengeResponse(a2b_hex(data), a2b_hex(key)) == a2b_hex(exp)
