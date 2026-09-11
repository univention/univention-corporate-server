// SPDX-FileCopyrightText: 2026 Univention GmbH
// SPDX-License-Identifier: AGPL-3.0-only

use des::cipher::generic_array::GenericArray;
use des::cipher::{BlockCipher, NewBlockCipher};
use des::Des;
use md4::{Digest, Md4};

pub fn md4(data: &[u8]) -> [u8; 16] {
    let mut hasher = Md4::new();
    hasher.update(data);
    hasher.finalize().into()
}

fn des_encrypt(data: &[u8; 8], key_56bit: &[u8; 7]) -> [u8; 8] {
    let key = expand_des_key(key_56bit);
    let cipher = Des::new(GenericArray::from_slice(&key));
    let mut block = GenericArray::clone_from_slice(data);
    cipher.encrypt_block(&mut block);
    block.into()
}

fn expand_des_key(key56: &[u8; 7]) -> [u8; 8] {
    let mut key64 = [0u8; 8];
    key64[0] = key56[0] >> 1;
    key64[1] = ((key56[0] & 0x01) << 6) | (key56[1] >> 2);
    key64[2] = ((key56[1] & 0x03) << 5) | (key56[2] >> 3);
    key64[3] = ((key56[2] & 0x07) << 4) | (key56[3] >> 4);
    key64[4] = ((key56[3] & 0x0f) << 3) | (key56[4] >> 5);
    key64[5] = ((key56[4] & 0x1f) << 2) | (key56[5] >> 6);
    key64[6] = ((key56[5] & 0x3f) << 1) | (key56[6] >> 7);
    key64[7] = key56[6] & 0x7f;
    for b in &mut key64 {
        *b <<= 1;
    }
    key64
}

pub fn hash_nt_password_hash(password_hash: &[u8]) -> [u8; 16] {
    md4(password_hash)
}

pub fn challenge_response(challenge: &[u8], password_hash: &[u8]) -> [u8; 24] {
    let mut z_password_hash = [0u8; 21];
    let len = password_hash.len().min(21);
    z_password_hash[..len].copy_from_slice(&password_hash[..len]);
    let challenge_block: [u8; 8] = challenge[..8].try_into().expect("challenge must be at least 8 bytes");
    let mut response = [0u8; 24];
    response[0..8].copy_from_slice(&des_encrypt(&challenge_block, z_password_hash[0..7].try_into().unwrap()));
    response[8..16].copy_from_slice(&des_encrypt(&challenge_block, z_password_hash[7..14].try_into().unwrap()));
    response[16..24].copy_from_slice(&des_encrypt(&challenge_block, z_password_hash[14..21].try_into().unwrap()));
    response
}

#[cfg(test)]
mod tests {
    use super::*;

    mod mschapv2_tests {
        use crate::mschapv2::{challenge_response, hash_nt_password_hash};
        use hex::decode as hex_decode;

        #[test]
        fn test_nthash() {
            let password_hash = b"\x44\xEB\xBA\x8D\x53\x12\xB8\xD6\x11\x47\x44\x11\xF5\x69\x89\xAE";
            let expected = b"\x41\xC0\x0C\x58\x4B\xD2\xD9\x1C\x40\x17\xA2\xA1\x2F\xA5\x9F\x3F";
            assert_eq!(hash_nt_password_hash(password_hash), *expected);
        }

        #[test]
        fn test_challenge_response_1() {
            let key = hex_decode("CAA1239D44DA7EDF926BCE39F5C65D0F").unwrap();
            let data = hex_decode("4c29654e436e7844").unwrap();
            let exp = hex_decode("1cffa87d8b48ce73a71e3e6c9a9dd80f112d48dfeea8792c").unwrap();
            assert_eq!(challenge_response(&data, &key).to_vec(), exp);
        }

        #[test]
        fn test_challenge_response_2() {
            let key = hex_decode("3b1b47e42e0463276e3ded6cef349f93").unwrap();
            let data = hex_decode("b019d38bad875c9d").unwrap();
            let exp = hex_decode("e6285df3287c5d194f84df1a94817c7282d09754b6f9e02a").unwrap();
            assert_eq!(challenge_response(&data, &key).to_vec(), exp);
        }

        #[test]
        fn test_challenge_response_3() {
            let key = hex_decode("624aac413795cdc1ff17365faf1ffe89").unwrap();
            let data = hex_decode("6da297169f7aa9c2").unwrap();
            let exp = hex_decode("2e17884ea16177e2b751d53b5cc756c3cd57cdfd6e3bf8b9").unwrap();
            assert_eq!(challenge_response(&data, &key).to_vec(), exp);
        }

        #[test]
        fn test_challenge_response_4() {
            let key = hex_decode("3b1b47e42e0463276e3ded6cef349f93").unwrap();
            let data = hex_decode("eacf7d5a2a6fa7d4").unwrap();
            let exp = hex_decode("d2025bc5d6c201af7472550a677ca9904245a16ebb542a8e").unwrap();
            assert_eq!(challenge_response(&data, &key).to_vec(), exp);
        }

        #[test]
        fn test_challenge_response_5() {
            let key = hex_decode("ae33a32dca8c9821844f740d5b3f4d6c").unwrap();
            let data = hex_decode("677f1c557a5ee96c").unwrap();
            let exp = hex_decode("1bb250184772028e54394762ded81de1f608e6f37e7de5b0").unwrap();
            assert_eq!(challenge_response(&data, &key).to_vec(), exp);
        }

        #[test]
        fn test_challenge_response_6() {
            let key = hex_decode("c4ea95cb148df11bf9d7c3611ad6d722").unwrap();
            let data = hex_decode("514246973ea892c1").unwrap();
            let exp = hex_decode("497e9072282f5d33529e7359177d42ac9e106600630d3a6d").unwrap();
            assert_eq!(challenge_response(&data, &key).to_vec(), exp);
        }

        #[test]
        fn test_challenge_response_rfc() {
            let key = hex_decode("cd06ca7c7e10c99b1d33b7485a2ed808").unwrap();
            let data = hex_decode("0123456789abcdef").unwrap();
            let exp = hex_decode("25a98c1c31e81847466b29b2df4680f39958fb8c213a9cc6").unwrap();
            assert_eq!(challenge_response(&data, &key).to_vec(), exp);
        }

        #[test]
        fn test_challenge_response_rfc2() {
            let key = hex_decode("ff3750bcc2b22412c2265b23734e0dac").unwrap();
            let data = hex_decode("0123456789abcdef").unwrap();
            let exp = hex_decode("c337cd5cbd44fc9782a667af6d427c6de67c20c2d3e77c56").unwrap();
            assert_eq!(challenge_response(&data, &key).to_vec(), exp);
        }

        #[test]
        fn test_challenge_response_9() {
            let key = hex_decode("04b8e0ba74289cc540826bab1dee63ae").unwrap();
            let data = hex_decode("ffffff0011223344").unwrap();
            let exp = hex_decode("c951c8b1ddf71b2f8ec0be33f21ad93b7cd5fb2cd6cf51c5").unwrap();
            assert_eq!(challenge_response(&data, &key).to_vec(), exp);
        }

        // see https://forge.univention.org/bugzilla/show_bug.cgi?id=38785
        #[test]
        fn test_challenge_response_bugzilla_38785() {
            let key = hex_decode("00563126f04f3875c417f789b00e72d2").unwrap();
            let data = hex_decode("5355f4fc60c8888a").unwrap();
            let exp = hex_decode("9681672b365655d0592c3e4009547b9e11bc751b6e97943b").unwrap();
            assert_eq!(challenge_response(&data, &key).to_vec(), exp);
        }
    }
}
