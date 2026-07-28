Name:           vandelay
Version:        1.0.7
Release:        1%{?dist}
Summary:        Vandelay: the JMAP importer-exporter (and backup tool)

License:        Apache-2.0 OR MIT
URL:            https://github.com/stalwartlabs/vandelay
Source0:        https://github.com/stalwartlabs/vandelay/archive/refs/tags/v%{version}.tar.gz

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
Vandelay is a one-shot account-migration utility for JMAP, the JMAP analogue
of imapsync generalised to every JMAP data type (mail, contacts, calendars,
identities, sieve scripts, file storage). It imports an account from a wide
range of source protocols into a local SQLite archive, then exports that
archive into a target JMAP server. It doubles as a per-account backup tool.

%prep
%autosetup -n %{name}-%{version}

%build
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

# Set build environment for optimal compilation
export CARGO_TARGET_DIR=%{_builddir}/%{name}-%{version}/target
export RUSTFLAGS="-Ccodegen-units=1"

# Ensure we have a proper Cargo.lock
[ -f Cargo.lock ] || cargo generate-lockfile

# Build with release optimizations
cargo build --release --verbose --locked

%install
# Install binary
install -D -m 755 %{_builddir}/%{name}-%{version}/target/release/%{name} %{buildroot}%{_bindir}/%{name}

%files
%{_bindir}/%{name}
%license LICENSES/*
%doc README.md CHANGELOG.md

%changelog
* Tue Jul 28 2026 Ante de Baas <antedebaas@users.github.com> - 1.0.7-1
- bumped to 1.0.7 release

* Sat Jul 18 2026 Ante de Baas <antedebaas@users.github.com> - 1.0.6-1
- bumped to 1.0.6 release

* Tue Jun 23 2026 Ante de Baas <antedebaas@users.github.com> - 1.0.4-1
- bumped to 1.0.4 release

* Tue Jun 16 2026 Ante de Baas <antedebaas@users.github.com> - 1.0.3-1
- bumped to 1.0.3 release

* Fri May 30 2026 Ante de Baas <antedebaas@users.github.com> - 1.0.0-1
- Initial package for Vandelay JMAP importer-exporter tool
