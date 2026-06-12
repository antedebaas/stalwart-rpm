Name:           stalwart-proxy
Version:        1.0.0
Release:        1%{?dist}
Summary:        Multi-protocol e-mail migration proxy

License:        AGPL-3.0-only OR LicenseRef-SEL
URL:            https://github.com/stalwartlabs/proxy
Source0:        https://github.com/stalwartlabs/proxy/archive/refs/tags/v%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  openssl-devel
BuildRequires:  pkgconfig(openssl)
BuildRequires:  cargo
BuildRequires:  curl

# Only build on supported architectures for Rust
ExcludeArch:    i686 s390 %{power64}

# For COPR compatibility
%if 0%{?fedora} >= 36 || 0%{?rhel} >= 9
%bcond_without check
%else
%bcond_with check
%endif

%global debug_package %{nil}

Requires:       glibc

%description
The migration proxy sits in front of one or more mail backends and decides,
on a per-account basis, which backend a given connection belongs to.
It terminates IMAP, POP3, ManageSieve, SMTP submission, SMTP/LMTP
and HTTP (JMAP) sessions, identifies the account behind each connection
from the credentials the client already presents,
looks up the destination that account is assigned to,
replays the authentication to that backend, and bridges the session.
Because the routing decision is made from the existing credentials,
no client reconfiguration is required: users keep the same server name,
ports and passwords while the proxy routes them to the correct system.

%prep
%autosetup -n proxy-%{version}

%build
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

# Set build environment for optimal compilation
export CARGO_TARGET_DIR=%{_builddir}/cli-%{version}/target
export RUSTFLAGS="-Ccodegen-units=1"

# Ensure we have a proper Cargo.lock
[ -f Cargo.lock ] || cargo generate-lockfile

# Build with release optimizations
cargo build --release --verbose --locked

%install
# Install binary
install -D -m 755 %{_builddir}/cli-%{version}/target/release/%{name} %{buildroot}%{_bindir}/%{name}

%files
%{_bindir}/%{name}
%license LICENSES/*
%doc README.md CHANGELOG.md

%changelog
* Thu May 14 2026 Ante de Baas <antedebaas@users.github.com> - 1.0.6-1
- Initial package for Stalwart CLI tool
