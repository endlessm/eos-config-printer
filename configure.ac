AC_INIT(eos-config-printer, 1.0.0)
AC_CONFIG_SRCDIR(eos-config-printer.py)
AM_INIT_AUTOMAKE([1.6 foreign])
AM_PATH_PYTHON([3])

AM_MAINTAINER_MODE([enable])

PKG_PROG_PKG_CONFIG

# For Polkit
PRINTERS_ADMIN_GROUP=lpadmin
AC_SUBST(PRINTERS_ADMIN_GROUP)

# For systemd
AC_SUBST([systemdsystemunitdir], [$($PKG_CONFIG --variable=systemdsystemunitdir systemd)])

AC_CONFIG_FILES([
Makefile
data/eos-config-printer
])
AC_OUTPUT
