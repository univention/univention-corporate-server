// SPDX-FileCopyrightText: 2026 Univention GmbH
// SPDX-License-Identifier: AGPL-3.0-only

pub fn decode_station_id(station_id: &str) -> String {
    let norm: String = station_id
        .to_lowercase()
        .chars()
        .filter(|c| c.is_ascii_hexdigit())
        .collect();
    (0..12)
        .step_by(2)
        .filter_map(|i| norm.get(i..i + 2))
        .collect::<Vec<_>>()
        .join(":")
}

pub fn parse_username(username: &str) -> String {
    if !username.starts_with("host/") {
        return username.to_string();
    }
    let without_prefix = &username["host/".len()..];
    let without_domain = without_prefix.split('.').next().unwrap_or(without_prefix);
    format!("{}$", without_domain)
}

#[cfg(test)]
mod tests {
    use super::*;

    mod utils_tests {
        use crate::utils::{decode_station_id, parse_username};

        #[test]
        fn test_mac_colon() {
            assert_eq!(decode_station_id("00:11:22:33:44:55"), "00:11:22:33:44:55");
        }

        #[test]
        fn test_mac_dash() {
            assert_eq!(decode_station_id("00-11-22-33-44-55"), "00:11:22:33:44:55");
        }

        #[test]
        fn test_mac_dot() {
            assert_eq!(decode_station_id("0011.2233.4455"), "00:11:22:33:44:55");
        }

        #[test]
        fn test_mac_plain() {
            assert_eq!(decode_station_id("001122334455"), "00:11:22:33:44:55");
        }

        #[test]
        fn test_mac_empty() {
            assert_eq!(decode_station_id(""), "");
        }

        #[test]
        fn test_username_plain() {
            assert_eq!(parse_username("user"), "user");
        }

        #[test]
        fn test_username_host() {
            assert_eq!(parse_username("host/foo.bar"), "foo$");
        }
    }
}
