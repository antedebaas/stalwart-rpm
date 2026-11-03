Name:           stalwart-cli
Version:        1.0.14
Release:        1%{?dist}
Summary:        Command line tool for administering Stalwart Mail Server over JMAP API

License:        AGPL-3.0-only OR LicenseRef-SEL
URL:            https://github.com/stalwartlabs/cli
Source0:        https://github.com/stalwartlabs/cli/archive/refs/tags/v%{version}.tar.gz

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
A schema-driven command line tool for administering Stalwart Mail and
Collaboration Server over its JMAP API. The tool fetches the server's schema
on first use and derives every command, validation rule, and rendered view
from it. The same binary works against any compatible Stalwart deployment
without recompilation.

%prep
%autosetup -n cli-%{version}

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
* Tue Nov 3 2026 Ante de Baas <antedebaas@users.github.com> - 1.0.14-1
- `apply --progress` help text now mentions upsert and reconcile batch progress reporting

* Sun Oct 11 2026 Ante de Baas <antedebaas@users.github.com> - 1.0.13-1
- `apply` annotates server IDs in `set` errors with plan reference and replaces base64 with encodify

* Tue Jul 28 2026 Ante de Baas <antedebaas@users.github.com> - 1.0.12-1
- `upsert`/`reconcile` accept `scope`, `reconcile` adds exhaustive upsert+destroy, breaking: reject unknown top-level keys, many fixes

* Sat Jul 18 2026 Ante de Baas <antedebaas@users.github.com> - 1.0.10-1
- `upsert` removes required matchOn field

* Thu May 14 2026 Ante de Baas <antedebaas@users.github.com> - 1.0.6-1
- Adds `--debug` flag for HTTP logging, improves schema cache resilience and error messages
