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
