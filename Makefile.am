bin_SCRIPTS= \
	data/eos-config-printer

nobase_pkgdata_SCRIPTS=	\
	eos-config-printer.py

nobase_pkgdata_DATA= \
	config.py \
	debug.py \
	killtimer.py \
	pkgvalidator.py \
	utils.py

# D-Bus related files
dbus_DATA =	\
	data/com.endlessm.Config.Printing.conf
dbusdir = $(sysconfdir)/dbus-1/system.d/

dbusinterfaces_DATA =				\
	data/com.endlessm.Config.Printing.xml
dbusinterfacesdir = $(datadir)/dbus-1/interfaces/

dbussystemservices_in_files = data/com.endlessm.Config.Printing.service.in
dbussystemservices_DATA = $(dbussystemservices_in_files:.service.in=.service)
dbussystemservicesdir = $(datadir)/dbus-1/system-services/

$(dbussystemservices_DATA): $(dbussystemservices_in_files)
	@sed -e "s|\@bindir\@|$(bindir)|" $< > $@

# systemd files for D-Bus activated service
systemdservice_in_files = data/eos-config-printer.service.in
systemdservice_DATA = $(systemdservice_in_files:.service.in=.service)
systemdservicedir = $(datadir)/$(systemdsystemunitdir)

$(systemdservice_DATA): $(systemdservice_in_files) $(systemdsystemunitdir)
	@sed -e "s|\@bindir\@|$(bindir)|" $< > $@

# systemd tmpfiles.d
tmpfilesdir = $(prefix)/lib/tmpfiles.d
tmpfiles_DATA = data/eos-config-printer.conf

# polkit files for securig the D-Bus API from unprivileged access
polkit_rules_in_files = data/com.endlessm.Config.Printing.rules.in
polkit_rulesdir = $(datadir)/polkit-1/rules.d
dist_polkit_rules_DATA = $(polkit_rules_in_files:.rules.in=.rules)

$(dist_polkit_rules_DATA): $(polkit_rules_in_files)
	@sed -e "s|\@PRINTERS_ADMIN_GROUP\@|$(PRINTERS_ADMIN_GROUP)|" $< > $@

polkit_policydir = $(datadir)/polkit-1/actions
dist_polkit_policy_DATA = data/com.endlessm.Config.Printing.policy

EXTRA_DIST= \
	$(bin_SCRIPTS) \
	$(nobase_pkgdata_SCRIPTS) \
	$(nobase_pkgdata_DATA) \
	$(dbus_DATA) \
	$(dbusinterfaces_DATA) \
	$(dbussystemservices_in_files) \
	$(polkit_rules_in_files) \
	$(systemdservice_in_files) \
	$(tmpfiles_DATA) \
	autogen.sh \
	README.md \
	$(NULL)

DISTCLEANFILES= \
	$(dbus_DATA) \
	$(dbusinterfaces_DATA) \
	$(dbussystemservices_DATA) \
	$(systemdservice_DATA) \
	$(tmpfiles_DATA) \
	$(dist_polkit_rules_DATA) \
	$(dist_polkit_policy_DATA) \
	$(NULL)
