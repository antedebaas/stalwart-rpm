Name:           stalwart-server
%global app_name stalwart
Version:        1.0.2
Release:        1%{?dist}
Summary:        All-in-one Mail & Collaboration server. Secure, scalable and fluent in every protocol (IMAP, JMAP, SMTP, CalDAV, CardDAV, WebDAV).

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
URL:            https://github.com/stalwartlabs/%{app_name}
Source0:        https://github.com/stalwartlabs/%{app_name}/archive/refs/tags/v%{version}.tar.gz
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
%autosetup -n %{app_name}-%{version}
tar -xzf %{SOURCE1} -C %{_builddir}

%build
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

# Set build environment for optimal compilation
export CARGO_TARGET_DIR=%{_builddir}/%{app_name}-%{version}/target
export RUSTFLAGS="$(cat %{_builddir}/flags.txt)"

# Build the release binary
cargo build --release -p stalwart --no-default-features --features "sqlite postgres mysql rocks s3 redis azure nats enterprise"

%pre
getent group %{app_name} >/dev/null || groupadd -r %{app_name}
getent passwd %{app_name} >/dev/null || \
    useradd -r -g %{app_name} -d %{_sharedstatedir}/%{app_name} \
    -s /sbin/nologin -c "%{app_name}" %{app_name}

%install
# Create data directories
install -d -m 755 %{buildroot}%{_sysconfdir}/%{app_name}/
install -d -m 755 %{buildroot}%{_sharedstatedir}/%{app_name}
install -d -m 755 %{buildroot}%{_sharedstatedir}/%{app_name}/data
install -d -m 755 %{buildroot}%{_sharedstatedir}/%{app_name}/dumps
install -d -m 755 %{buildroot}%{_sharedstatedir}/%{app_name}/snapshots
install -d -m 755 %{buildroot}%{_var}/log/%{app_name}
install -d -m 755 %{buildroot}%{_docdir}/%{app_name}

# Install binary
install -D -m 755 %{_builddir}/%{app_name}-%{version}/target/release/%{app_name} %{buildroot}%{_bindir}/%{app_name}

# Install README in config directory
install -D -m 644 %{_builddir}/stalwart-rpm/README.configs.md %{buildroot}%{_sysconfdir}/%{app_name}/README.md

# Install example configuration files
install -D -m 644 %{_builddir}/stalwart-rpm/%{app_name}.postgres.json %{buildroot}%{_docdir}/%{app_name}/%{app_name}.postgres.json
install -D -m 644 %{_builddir}/stalwart-rpm/%{app_name}.rocksdb.json %{buildroot}%{_docdir}/%{app_name}/%{app_name}.rocksdb.json
install -D -m 644 %{_builddir}/stalwart-rpm/%{app_name}.sqlite.json %{buildroot}%{_docdir}/%{app_name}/%{app_name}.sqlite.json
install -D -m 644 %{_builddir}/stalwart-rpm/%{app_name}.mysql.json %{buildroot}%{_docdir}/%{app_name}/%{app_name}.mysql.json
install -D -m 644 %{_builddir}/stalwart-rpm/%{app_name}.foundationdb.json %{buildroot}%{_docdir}/%{app_name}/%{app_name}.foundationdb.json

# Install systemd service
install -D -m 644 %{_builddir}/stalwart-rpm/%{app_name}.service %{buildroot}%{_unitdir}/%{app_name}.service

%post
# Set ownership of data directory
chown -R %{app_name}:%{app_name} %{_sharedstatedir}/%{app_name}
chown %{app_name}:%{app_name} %{_sysconfdir}/%{app_name}
chown %{app_name}:%{app_name} %{_var}/log/%{app_name}
if [ ! -f /etc/stalwart/config.json ]; then
    echo "No configuration file found. Please copy an example from /usr/share/doc/stalwart/ to /etc/stalwart/config.json" > /etc/stalwart/config.json.readme
fi

%systemd_post %{app_name}.service

%preun
%systemd_preun %{app_name}.service

%postun
%systemd_postun_with_restart %{app_name}.service

%files
%{_bindir}/%{app_name}
%dir %attr(0755,%{app_name},%{app_name}) %{_var}/log/%{app_name}
%dir %attr(0755,%{app_name},%{app_name}) %{_sharedstatedir}/%{app_name}
%dir %attr(0755,%{app_name},%{app_name}) %{_sharedstatedir}/%{app_name}/data
%dir %attr(0755,%{app_name},%{app_name}) %{_sharedstatedir}/%{app_name}/dumps
%dir %attr(0755,%{app_name},%{app_name}) %{_sharedstatedir}/%{app_name}/snapshots
%attr(0644,root,root) %{_sysconfdir}/%{app_name}/README.md
%ghost %config(noreplace) %attr(0644,%{app_name},%{app_name}) %{_sysconfdir}/%{app_name}/config.json
%{_unitdir}/%{app_name}.service
%doc %{_docdir}/%{app_name}/%{app_name}.postgres.json
%doc %{_docdir}/%{app_name}/%{app_name}.rocksdb.json
%doc %{_docdir}/%{app_name}/%{app_name}.sqlite.json
%doc %{_docdir}/%{app_name}/%{app_name}.mysql.json
%doc %{_docdir}/%{app_name}/%{app_name}.foundationdb.json

%changelog
* Wed Nov 4 2026 Ante de Baas <antedebaas@users.github.com> - 1.0.2-1
- Added: OpenPGP (RFC 9580) and S/MIME (RFC 8551) encryption, encryption gateway, external public keys (WKD/VKS/HKP), header protection (RFC 9788), DKIM2 DSN signing and propagation, OAuth scopes, OIDC trustedProvider
- Changed: DKIM2 algorithm replaced by pure ML-DSA-44, vCard/iCalendar decoding as UTF-8/Windows-1252
- Fixed: DKIM relaxed body canonicalization, iTip REQUEST sequence handling, IMAP RENAME loop prevention, JMAP Email/queryChanges collapseThreads, OAuth scope validation, milter SMFIC_BODY, search indexing blob handling, and more

* Wed Oct 14 2026 Ante de Baas <antedebaas@users.github.com> - 0.16.26-1
- Added: sd_notify support, JMAP mailbox operations; Fixed: DNSSEC resolver, RocksDB blob GC, milter end-of-headers, OIDC fallback to email claim, JMAP push notification and VacationResponse bugs

* Sun Oct 11 2026 Ante de Baas <antedebaas@users.github.com> - 0.16.25-1
- Fixed: JMAP MaskedEmail creation, IMAP auth error responses, DKIM key rotation, spam filter DNSBL scoring, RocksDB log rotation, MTA queue quota enforcement, WebUI blob store error handling

* Sun Sep 13 2026 Ante de Baas <antedebaas@users.github.com> - 0.16.22-1
- Fixed: WebDAV namespace declarations, MTA throttle expression evaluation, DMARC reporting, OIDC discovery retry on startup, Sieve fileinto ham classification, IMAP SELECT/EXAMINE ACL checks, OAuth empty key fallback, LDAP filter placeholder escaping, JMAP CalendarEvent/ContactCard get property handling

* Thu Sep 10 2026 Ante de Baas <antedebaas@users.github.com> - 0.16.21-1
- Fixed: JMAP CalendarEvent/set scheduling rejection, Calendar/AddressBook/get fallback properties, IMAP pipelined STATUS batch responses, WebDAV quota advertisement for accounts without quota, LDAP unauthenticated bind handling, OpenTelemetry log exporter span attributes

* Wed Sep 02 2026 Ante de Baas <antedebaas@users.github.com> - 0.16.20-1
- Added: SCIM v2 (Enterprise), CalendarEvent/set synthetic IDs, conference links in invites, 24 language translations; Fixed: DANE TLSA lookups, Redis sentinel TLS, cluster node lease cleanup, CardDAV default address book deletion

* Tue Jul 28 2026 Ante de Baas <antedebaas@users.github.com> - 0.16.15-1
- Fixed: Email/copy alreadyExists and onSuccessDestroyOriginal bugs, CalendarEvent/set uid and DTSTAMP generation, MTA-STS panic, VAPID key PEM format acceptance, cache shard discard causing rebuilds, registry id reference resolution, cluster broadcast re-subscription

* Sat Jul 18 2026 Ante de Baas <antedebaas@users.github.com> - 0.16.13-1
- Added: FreeBSD support, OAuth resource indicators for imap/smtp/pop3/sieve; Fixed: VacationResponse isEnabled reset, RFC-3339 UTCDate literals in capabilities, DNS CAA over-deletion, custom domain logos, Sieve Received header loop detection

* Tue Jun 23 2026 Ante de Baas <antedebaas@users.github.com> - 0.16.10-1
- Added: International Domain Names (IDN), OAuth Profile for Open Public Clients, IMAP Extension for Object Identifiers, GETJMAPACCESS command, HTTP redirectRoot, ACME reuseKey; Fixed: extensive JMAP conformance fixes (jmap-test-suite), DANE TLSA validation, RocksDB blob GC, Cache invalidation

* Tue Jun 16 2026 Ante de Baas <antedebaas@users.github.com> - 0.16.9-1
- Added: ACME preferred certificate chain; Fixed: JMAP */changes id leak for non-shared objects, FoundationDB read cache expiration, ACME certificate renewal freshness check, ACME DNS-01 sequential authorizations

* Wed May 27 2026 Ante de Baas <antedebaas@users.github.com> - 0.16.6-3
- Added: 58 new DNS provider integrations, DNS record logging, Sieve orcpt access, spam classifier logging; Fixed: DAV ACL privilege, IMAP UID FETCH missed messages, ACME defaultCertificateId renewal, Sieve replace extra From header, orphaned ACL JMAP session errors
