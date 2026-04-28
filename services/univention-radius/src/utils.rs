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
