Name:           stalwart-proxy
Version:        1.0.4
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
Requires(pre):  shadow-utils
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

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
export RUSTFLAGS="-Ccodegen-units=1"

# Ensure we have a proper Cargo.lock
[ -f Cargo.lock ] || cargo generate-lockfile

# Build with release optimizations
cargo build --release --verbose --locked

%install
# Install binary (built as 'proxy' but installed as 'stalwart-proxy')
install -D -m 755 target/release/proxy %{buildroot}%{_bindir}/%{name}

# Create and install systemd service file
cat > %{name}.service << 'EOF'
[Unit]
Description=Stalwart Proxy - Multi-protocol e-mail migration proxy
After=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/stalwart-proxy --config /etc/stalwart-proxy/config.toml
User=stalwart-proxy
Group=stalwart-proxy
Restart=on-failure

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/stalwart-proxy

# Grant capability to bind to privileged ports (< 1024) without running as root
AmbientCapabilities=CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
EOF
install -D -m 644 %{name}.service %{buildroot}/usr/lib/systemd/system/%{name}.service

# Install example configuration
install -D -m 644 resources/config.sample.toml %{buildroot}%{_sysconfdir}/%{name}/config.toml

# Install documentation files (if they exist)
if [ -f resources/config.dovecot-postfix.toml ]; then
    install -D -m 644 resources/config.dovecot-postfix.toml %{buildroot}%{_docdir}/%{name}/config.dovecot-postfix.toml
fi
if [ -f resources/config.stalwart-upgrade.toml ]; then
    install -D -m 644 resources/config.stalwart-upgrade.toml %{buildroot}%{_docdir}/%{name}/config.stalwart-upgrade.toml
fi
if [ -f resources/dovecot-postfix-trust.conf ]; then
    install -D -m 644 resources/dovecot-postfix-trust.conf %{buildroot}%{_docdir}/%{name}/dovecot-postfix-trust.conf
fi
if [ -f resources/migrate_v015_to_plan.py ]; then
    install -D -m 644 resources/migrate_v015_to_plan.py %{buildroot}%{_docdir}/%{name}/migrate_v015_to_plan.py
fi

# Ensure doc directory exists even if no extra files
mkdir -p %{buildroot}%{_docdir}/%{name}

%pre
# Create stalwart-proxy user and group
getent group stalwart-proxy >/dev/null || groupadd -r stalwart-proxy
getent passwd stalwart-proxy >/dev/null || \
    useradd -r -g stalwart-proxy -d /var/lib/stalwart-proxy -s /sbin/nologin \
    -c "Stalwart Proxy service account" stalwart-proxy
exit 0

%post
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service

%files
%{_bindir}/%{name}
/usr/lib/systemd/system/%{name}.service
%dir %{_sysconfdir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/config.toml
%dir %{_docdir}/%{name}
%doc %{_docdir}/%{name}/config.dovecot-postfix.toml
%doc %{_docdir}/%{name}/config.stalwart-upgrade.toml
%doc %{_docdir}/%{name}/dovecot-postfix-trust.conf
%doc %{_docdir}/%{name}/migrate_v015_to_plan.py
%license LICENSES/*
%doc README.md CHANGELOG.md

%changelog
* Wed Sep 02 2026 Ante de Baas <antedebaas@users.github.com> - 1.0.3-1
- bumped to 1.0.3 release

* Fri Jun 12 2026 Ante de Baas <antedebaas@users.github.com> - 1.0.0-1
- Initial package for Stalwart Proxy
- Added systemd service file
- Added example configurations and documentation
- Created stalwart-proxy user and group
