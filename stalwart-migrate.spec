Name:           stalwart-migrate
Version:        1.0.5
Release:        1%{?dist}
Summary:        Stalwart v1.0.0 migration tool

License:        AGPL-3.0-only OR LicenseRef-SEL
URL:            https://github.com/stalwartlabs/stalwart-migrate
Source0:        https://github.com/stalwartlabs/stalwart-migrate/archive/refs/tags/v%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  glibc-devel
BuildRequires:  openssl-devel
# systemd-rpm-macros not available on openEuler
%if 0%{?fedora} || 0%{?rhel} >= 9
BuildRequires:  systemd-rpm-macros
%endif
BuildRequires:  pkgconfig(openssl)
BuildRequires:  make cmake
BuildRequires:  git
BuildRequires:  curl libcurl-devel
BuildRequires:  cargo
# Different distributions have different clang package names
%if 0%{?suse_version}
# openSUSE/SUSE
BuildRequires:  clang-devel
BuildRequires:  llvm-devel
%else
%if 0%{?fedora} && 0%{?fedora} >= 36 && !0%{?mageia} && !0%{?mgaversion}
# Fedora 36+ has versioned clang packages (but not Mageia or derivatives)
BuildRequires:  clang19-devel clang19-libs
%else
# RHEL, AlmaLinux, Rocky, openEuler, Mageia, etc.
BuildRequires:  clang-devel
%endif
%endif

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
The Stalwart migration tool migrates data from older Stalwart Mail Server
versions (v0.16 and earlier) to v1.0. It supports multiple source and
target backends including PostgreSQL, MySQL, SQLite, and various blob
storage systems.

%prep
%autosetup -n stalwart-migrate-%{version}

%build
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

# Set build environment for optimal compilation
export RUSTFLAGS="-Ccodegen-units=1"

# Ensure we have a proper Cargo.lock
[ -f Cargo.lock ] || cargo generate-lockfile

# Build with release optimizations
cargo build --release --verbose --locked

%install
# Install binary
install -D -m 755 target/release/stalwart-migrate %{buildroot}%{_bindir}/%{name}

# Install documentation files
mkdir -p %{buildroot}%{_docdir}/%{name}
install -D -m 644 README.md %{buildroot}%{_docdir}/%{name}/README.md
install -D -m 644 CHANGELOG.md %{buildroot}%{_docdir}/%{name}/CHANGELOG.md

# Install license files
install -D -m 644 -t %{buildroot}%{_docdir}/%{name}/LICENSES LICENSES/*

%files
%{_bindir}/%{name}
%dir %{_docdir}/%{name}
%doc %{_docdir}/%{name}/README.md
%doc %{_docdir}/%{name}/CHANGELOG.md
%doc %{_docdir}/%{name}/LICENSES/*

%changelog
* Tue Nov 3 2026 Ante de Baas <antedebaas@users.github.com> - 1.0.5-1
- Initial package for Stalwart Migrate
- Built from v1.0.5 release
- CLI migration tool for Stalwart v1.0.0 upgrades
