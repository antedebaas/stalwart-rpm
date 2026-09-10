Name:           stalwart
Version:        0.16.21
Release:        1%{?dist}
Summary:        All-in-one Mail & Collaboration server. Secure, scalable and fluent in every protocol (IMAP, JMAP, SMTP, CalDAV, CardDAV, WebDAV).

%global packageversion 1.0.0

# Define systemd macros if not provided by systemd-rpm-macros
# (openEuler and some older distributions don't have this package)
%{!?_unitdir: %global _unitdir /usr/lib/systemd/system}
%{!?systemd_post: %global systemd_post() \
if [ $1 -eq 1 ] ; then \
    systemctl preset %{1} >/dev/null 2>&1 || : \
fi \
%{nil}}
%{!?systemd_preun: %global systemd_preun() \
if [ $1 -eq 0 ] ; then \
    systemctl --no-reload disable %{1} >/dev/null 2>&1 || : \
    systemctl stop %{1} >/dev/null 2>&1 || : \
fi \
%{nil}}
%{!?systemd_postun_with_restart: %global systemd_postun_with_restart() \
systemctl daemon-reload >/dev/null 2>&1 || : \
if [ $1 -ge 1 ] ; then \
    systemctl try-restart %{1} >/dev/null 2>&1 || : \
fi \
%{nil}}

License:        MIT
URL:            https://github.com/stalwartlabs/%{name}
Source0:        https://github.com/stalwartlabs/%{name}/archive/refs/tags/v%{version}.tar.gz
Source1:        https://forgejo.home.debaas.net/ante/stalwart-rpm/archive/v%{packageversion}.tar.gz

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

# EPEL 7 has libclang too old for modern Rust bindgen (needs LLVM 11+)
%if 0%{?rhel} && 0%{?rhel} < 8
%{error:EPEL 7 is not supported - requires RHEL 8+ or Fedora}
%endif

# For COPR compatibility
%if 0%{?fedora} >= 36 || 0%{?rhel} >= 9
%bcond_without check
%else
%bcond_with check
%endif

%global debug_package %{nil}

Requires:       glibc

%description
All-in-one Mail & Collaboration server. Secure, scalable and fluent in every protocol (IMAP, JMAP, SMTP, CalDAV, CardDAV, WebDAV).

%prep
%autosetup -n %{name}-%{version}
tar -xzf %{SOURCE1} -C %{_builddir}

%build
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

# Set build environment for optimal compilation
export CARGO_TARGET_DIR=%{_builddir}/%{name}-%{version}/target
export RUSTFLAGS="$(cat %{_builddir}/flags.txt)"

# Ensure we have a proper Cargo.lock
[ -f Cargo.lock ] || cargo generate-lockfile

# Build the release binary
cargo build --release -p stalwart --no-default-features --features "sqlite postgres mysql rocks s3 redis azure nats enterprise"

%pre
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null || \
    useradd -r -g %{name} -d %{_sharedstatedir}/%{name} \
    -s /sbin/nologin -c "%{name}" %{name}

%install
# Create data directories
install -d -m 755 %{buildroot}%{_sysconfdir}/%{name}/
install -d -m 755 %{buildroot}%{_sharedstatedir}/%{name}
install -d -m 755 %{buildroot}%{_sharedstatedir}/%{name}/data
install -d -m 755 %{buildroot}%{_sharedstatedir}/%{name}/dumps
install -d -m 755 %{buildroot}%{_sharedstatedir}/%{name}/snapshots
install -d -m 755 %{buildroot}%{_var}/log/%{name}
install -d -m 755 %{buildroot}%{_docdir}/%{name}

# Install binary
install -D -m 755 %{_builddir}/%{name}-%{version}/target/release/%{name} %{buildroot}%{_bindir}/%{name}

# Install README in config directory
install -D -m 644 %{_builddir}/stalwart-rpm/README.configs.md %{buildroot}%{_sysconfdir}/%{name}/README.md

# Install example configuration files
install -D -m 644 %{_builddir}/stalwart-rpm/%{name}.postgres.json %{buildroot}%{_docdir}/%{name}/%{name}.postgres.json
install -D -m 644 %{_builddir}/stalwart-rpm/%{name}.rocksdb.json %{buildroot}%{_docdir}/%{name}/%{name}.rocksdb.json
install -D -m 644 %{_builddir}/stalwart-rpm/%{name}.sqlite.json %{buildroot}%{_docdir}/%{name}/%{name}.sqlite.json
install -D -m 644 %{_builddir}/stalwart-rpm/%{name}.mysql.json %{buildroot}%{_docdir}/%{name}/%{name}.mysql.json
install -D -m 644 %{_builddir}/stalwart-rpm/%{name}.foundationdb.json %{buildroot}%{_docdir}/%{name}/%{name}.foundationdb.json

# Install systemd service
install -D -m 644 %{_builddir}/stalwart-rpm/%{name}.service %{buildroot}%{_unitdir}/%{name}.service

%post
# Set ownership of data directory
chown -R %{name}:%{name} %{_sharedstatedir}/%{name}
chown %{name}:%{name} %{_sysconfdir}/%{name}
chown %{name}:%{name} %{_var}/log/%{name}
if [ ! -f /etc/stalwart/config.json ]; then
    echo "No configuration file found. Please copy an example from /usr/share/doc/stalwart/ to /etc/stalwart/config.json" > /etc/stalwart/config.json.readme
fi

%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service

%files
%{_bindir}/%{name}
%dir %attr(0755,%{name},%{name}) %{_var}/log/%{name}
%dir %attr(0755,%{name},%{name}) %{_sharedstatedir}/%{name}
%dir %attr(0755,%{name},%{name}) %{_sharedstatedir}/%{name}/data
%dir %attr(0755,%{name},%{name}) %{_sharedstatedir}/%{name}/dumps
%dir %attr(0755,%{name},%{name}) %{_sharedstatedir}/%{name}/snapshots
%attr(0644,root,root) %{_sysconfdir}/%{name}/README.md
%ghost %config(noreplace) %attr(0644,%{name},%{name}) %{_sysconfdir}/%{name}/config.json
%{_unitdir}/%{name}.service
%doc %{_docdir}/%{name}/%{name}.postgres.json
%doc %{_docdir}/%{name}/%{name}.rocksdb.json
%doc %{_docdir}/%{name}/%{name}.sqlite.json
%doc %{_docdir}/%{name}/%{name}.mysql.json
%doc %{_docdir}/%{name}/%{name}.foundationdb.json

%changelog
* Thu Sep 10 2026 Ante de Baas <antedebaas@users.github.com> - 0.16.21-1
- bumped to 0.16.21 release

* Wed Sep 02 2026 Ante de Baas <antedebaas@users.github.com> - 0.16.20-1
- bumped to 0.16.20 release

* Tue Jul 28 2026 Ante de Baas <antedebaas@users.github.com> - 0.16.15-1
- bumped to 0.16.15 release

* Sat Jul 18 2026 Ante de Baas <antedebaas@users.github.com> - 0.16.13-1
- bumped to 0.16.13 release

* Tue Jun 23 2026 Ante de Baas <antedebaas@users.github.com> - 0.16.10-1
- bumped to 0.16.10 release

* Tue Jun 16 2026 Ante de Baas <antedebaas@users.github.com> - 0.16.9-1
- bumped to 0.16.9 release

* Wed May 27 2026 Ante de Baas <antedebaas@users.github.com> - 0.16.6-3
- package following 0.16.6 release
