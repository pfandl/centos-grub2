# Modules always contain just 32-bit code
%define _libdir %{_exec_prefix}/lib

# 64bit intel machines use 32bit boot loader
# (We cannot just redefine _target_cpu, as we'd get i386.rpm packages then)
%ifarch x86_64
%define _target_platform i386-%{_vendor}-%{_target_os}%{?_gnu}
%endif
# sparc is always compiled 64 bit
%ifarch %{sparc}
%define _target_platform sparc64-%{_vendor}-%{_target_os}%{?_gnu}
%endif

%if ! 0%{?efi}

%global efi_only aarch64
%global efiarchs x86_64 ia64 %{efi_only}

%ifarch x86_64
%global grubefiarch %{_arch}-efi
%global grubefiname grubx64.efi
%global grubeficdname gcdx64.efi
%endif
%ifarch aarch64
%global grubefiarch arm64-efi
%global grubefiname grubaa64.efi
%global grubeficdname gcdaa64.efi
%endif

%if 0%{?rhel}
%global efidir redhat
%endif
%if 0%{?fedora}
%global efidir fedora
%endif

%endif

%global tarversion 2.02~beta2
%undefine _missing_build_ids_terminate_build

Name:           grub2
Epoch:          1
Version:        2.02
Release:        0.44%{?dist}
Summary:        Bootloader with support for Linux, Multiboot and more

Group:          System Environment/Base
License:        GPLv3+
URL:            http://www.gnu.org/software/grub/
Obsoletes:	grub < 1:0.98
Source0:        ftp://alpha.gnu.org/gnu/grub/grub-%{tarversion}.tar.xz
#Source0:	ftp://ftp.gnu.org/gnu/grub/grub-%%{tarversion}.tar.xz
Source1:	securebootca.cer
Source2:	secureboot.cer
Source3:	grub.patches
Source4:	http://unifoundry.com/unifont-5.1.20080820.pcf.gz
Source5:	theme.tar.bz2
Source6:	gitignore
#Source6:	grub-cd.cfg

%include %{SOURCE3}

BuildRequires:  flex bison binutils python
BuildRequires:  ncurses-devel xz-devel bzip2-devel
BuildRequires:  freetype-devel libusb-devel
%ifarch %{sparc} x86_64 aarch64 ppc64le
# sparc builds need 64 bit glibc-devel - also for 32 bit userland
BuildRequires:  /usr/lib64/crt1.o glibc-static
%else
# ppc64 builds need the ppc crt1.o
BuildRequires:  /usr/lib/crt1.o glibc-static
%endif
BuildRequires:  autoconf automake autogen device-mapper-devel
BuildRequires:	freetype-devel gettext-devel git
BuildRequires:	texinfo
BuildRequires:	dejavu-sans-fonts
BuildRequires:	help2man
BuildRequires:	rpm-devel
%ifarch %{efiarchs}
%ifnarch aarch64
BuildRequires:	pesign >= 0.109-3.el7
%endif
%endif

Requires:	gettext os-prober which file
Requires:	%{name}-tools = %{epoch}:%{version}-%{release}
Requires(pre):  dracut
Requires(post): dracut

ExcludeArch:	s390 s390x %{arm}
Obsoletes:	grub2 <= 1:2.00-20%{?dist}

%description
The GRand Unified Bootloader (GRUB) is a highly configurable and customizable
bootloader with modular architecture.  It support rich varietyof kernel formats,
file systems, computer architectures and hardware devices.  This subpackage
provides support for PC BIOS systems.

%ifarch %{efiarchs}
%package efi
Summary:	GRUB for EFI systems.
Group:		System Environment/Base
Requires:	%{name}-tools = %{epoch}:%{version}-%{release}
Obsoletes:	grub2-efi <= 1:2.00-20%{?dist}

%description efi
The GRand Unified Bootloader (GRUB) is a highly configurable and customizable
bootloader with modular architecture.  It support rich varietyof kernel formats,
file systems, computer architectures and hardware devices.  This subpackage
provides support for EFI systems.

%package efi-modules
Summary:	Modules used to build custom grub.efi images
Group:		System Environment/Base
Requires:	%{name}-tools = %{epoch}:%{version}-%{release}
Obsoletes:	grub2-efi <= 1:2.00-20%{?dist}

%description efi-modules
The GRand Unified Bootloader (GRUB) is a highly configurable and customizable
bootloader with modular architecture.  It support rich varietyof kernel formats,
file systems, computer architectures and hardware devices.  This subpackage
provides support for rebuilding your own grub.efi on EFI systems.
%endif

%package tools
Summary:	Support tools for GRUB.
Group:		System Environment/Base
Requires:	gettext os-prober which file system-logos
Requires(pre):	sed grep coreutils

%description tools
The GRand Unified Bootloader (GRUB) is a highly configurable and customizable
bootloader with modular architecture.  It support rich varietyof kernel formats,
file systems, computer architectures and hardware devices.  This subpackage
provides tools for support of all platforms.

%prep
%setup -T -c -n grub-%{tarversion}
%ifarch %{efiarchs}
%setup -D -q -T -a 0 -n grub-%{tarversion}
cd grub-%{tarversion}
# place unifont in the '.' from which configure is run
cp %{SOURCE4} unifont.pcf.gz
cp %{SOURCE6} .gitignore
git init
git config user.email "example@example.com"
git config user.name "RHEL Ninjas"
git add .
git commit -a -q -m "%{tarversion} baseline."
git am %{patches}
cd ..
mv grub-%{tarversion} grub-efi-%{tarversion}
%endif

%ifarch %{efi_only}
ln -s grub-efi-%{tarversion} grub-%{tarversion}
%else
%setup -D -q -T -a 0 -n grub-%{tarversion}
cd grub-%{tarversion}
# place unifont in the '.' from which configure is run
cp %{SOURCE4} unifont.pcf.gz
cp %{SOURCE6} .gitignore
git init
git config user.email "example@example.com"
git config user.name "RHEL Ninjas"
git add .
git commit -a -q -m "%{tarversion} baseline."
git am %{patches}
%endif

%build
%ifarch %{efiarchs}
cd grub-efi-%{tarversion}
./autogen.sh
%configure							\
	CFLAGS="$(echo $RPM_OPT_FLAGS | sed			\
		-e 's/-O.//g'					\
		-e 's/-fstack-protector[[:alpha:]-]\+//g'	\
		-e 's/--param=ssp-buffer-size=4//g'		\
		-e 's/-mregparm=3/-mregparm=4/g'		\
		-e 's/-fexceptions//g'				\
		-e 's/-fasynchronous-unwind-tables//g'		\
		-e 's/^/ -fno-strict-aliasing -std=gnu99 /' )"	\
	TARGET_LDFLAGS=-static					\
        --with-platform=efi					\
	--with-grubdir=%{name}					\
        --program-transform-name=s,grub,%{name},		\
	--disable-grub-mount					\
	--disable-werror
make %{?_smp_mflags}

GRUB_MODULES="	all_video boot btrfs cat chain configfile echo efifwsetup \
		efinet ext2 fat font gfxmenu gfxterm gzio halt hfsplus http \
		iso9660 jpeg loadenv lvm mdraid09 mdraid1x minicmd normal \
		part_apple part_msdos part_gpt password_pbkdf2 png \
		reboot search search_fs_uuid search_fs_file search_label \
		sleep syslinuxcfg test tftp regexp video xfs"
%ifarch aarch64
GRUB_MODULES="${GRUB_MODULES} linux"
%else
GRUB_MODULES="${GRUB_MODULES} linuxefi"
%endif
./grub-mkimage -O %{grubefiarch} -o %{grubefiname}.orig -p /EFI/%{efidir} \
		-d grub-core ${GRUB_MODULES}
./grub-mkimage -O %{grubefiarch} -o %{grubeficdname}.orig -p /EFI/BOOT \
		-d grub-core ${GRUB_MODULES}
%ifarch aarch64
mv %{grubefiname}.orig %{grubefiname}
mv %{grubeficdname}.orig %{grubeficdname}
%else
%pesign -s -i %{grubefiname}.orig -o %{grubefiname} -a %{SOURCE1} -c %{SOURCE2} -n redhatsecureboot301
%pesign -s -i %{grubeficdname}.orig -o %{grubeficdname} -a %{SOURCE1} -c %{SOURCE2} -n redhatsecureboot301
%endif
cd ..
%endif

cd grub-%{tarversion}
%ifnarch %{efi_only}
./autogen.sh
# -static is needed so that autoconf script is able to link
# test that looks for _start symbol on 64 bit platforms
%ifarch %{sparc} ppc ppc64 ppc64le
%define platform ieee1275
%else
%define platform pc
%endif
%configure							\
	CFLAGS="$(echo $RPM_OPT_FLAGS | sed			\
		-e 's/-O.//g'					\
		-e 's/-fstack-protector[[:alpha:]-]\+//g'	\
		-e 's/--param=ssp-buffer-size=4//g'		\
		-e 's/-mregparm=3/-mregparm=4/g'		\
		-e 's/-fexceptions//g'				\
		-e 's/-m64//g'					\
		-e 's/-fasynchronous-unwind-tables//g'		\
		-e 's/-mcpu=power7/-mcpu=power6/g'		\
		-e 's/^/ -fno-strict-aliasing -std=gnu99 /' )"	\
	TARGET_LDFLAGS=-static					\
        --with-platform=%{platform}				\
	--with-grubdir=%{name}					\
        --program-transform-name=s,grub,%{name},		\
	--disable-grub-mount					\
	--disable-werror

make %{?_smp_mflags}
%endif

sed -i -e 's,(grub),(%{name}),g' \
	-e 's,grub.info,%{name}.info,g' \
	-e 's,\* GRUB:,* GRUB2:,g' \
	-e 's,/boot/grub/,/boot/%{name}/,g' \
	-e 's,\([^-]\)grub-\([a-z]\),\1%{name}-\2,g' \
	docs/grub.info
sed -i -e 's,grub-dev,%{name}-dev,g' docs/grub-dev.info

/usr/bin/makeinfo --html --no-split -I docs -o grub-dev.html docs/grub-dev.texi
/usr/bin/makeinfo --html --no-split -I docs -o grub.html docs/grub.texi
sed -i	-e 's,/boot/grub/,/boot/%{name}/,g' \
	-e 's,\([^-]\)grub-\([a-z]\),\1%{name}-\2,g' \
	grub.html

%install
set -e
rm -fr $RPM_BUILD_ROOT

%ifarch %{efiarchs}
cd grub-efi-%{tarversion}
make DESTDIR=$RPM_BUILD_ROOT install
find $RPM_BUILD_ROOT -iname "*.module" -exec chmod a-x {} \;

# Ghost config file
install -m 755 -d $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/
touch $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/grub.cfg
ln -s ../boot/efi/EFI/%{efidir}/grub.cfg $RPM_BUILD_ROOT%{_sysconfdir}/%{name}-efi.cfg

# Install ELF files modules and images were created from into
# the shadow root, where debuginfo generator will grab them from
find $RPM_BUILD_ROOT -name '*.mod' -o -name '*.img' |
while read MODULE
do
        BASE=$(echo $MODULE |sed -r "s,.*/([^/]*)\.(mod|img),\1,")
        # Symbols from .img files are in .exec files, while .mod
        # modules store symbols in .elf. This is just because we
        # have both boot.img and boot.mod ...
        EXT=$(echo $MODULE |grep -q '.mod' && echo '.elf' || echo '.exec')
        TGT=$(echo $MODULE |sed "s,$RPM_BUILD_ROOT,.debugroot,")
#        install -m 755 -D $BASE$EXT $TGT
done
install -m 755 %{grubefiname} $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/%{grubefiname}
install -m 755 %{grubeficdname} $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/%{grubeficdname}
install -D -m 644 unicode.pf2 $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/fonts/unicode.pf2
cd ..
%endif

cd grub-%{tarversion}
%ifnarch %{efi_only}
make DESTDIR=$RPM_BUILD_ROOT install

# Ghost config file
install -d $RPM_BUILD_ROOT/boot/%{name}
touch $RPM_BUILD_ROOT/boot/%{name}/grub.cfg
ln -s ../boot/%{name}/grub.cfg $RPM_BUILD_ROOT%{_sysconfdir}/%{name}.cfg
%endif

cp -a $RPM_BUILD_ROOT%{_datarootdir}/locale/en\@quot $RPM_BUILD_ROOT%{_datarootdir}/locale/en

# Install ELF files modules and images were created from into
# the shadow root, where debuginfo generator will grab them from
find $RPM_BUILD_ROOT -name '*.mod' -o -name '*.img' |
while read MODULE
do
        BASE=$(echo $MODULE |sed -r "s,.*/([^/]*)\.(mod|img),\1,")
        # Symbols from .img files are in .exec files, while .mod
        # modules store symbols in .elf. This is just because we
        # have both boot.img and boot.mod ...
        EXT=$(echo $MODULE |grep -q '.mod' && echo '.elf' || echo '.exec')
        TGT=$(echo $MODULE |sed "s,$RPM_BUILD_ROOT,.debugroot,")
#        install -m 755 -D $BASE$EXT $TGT
done

mv $RPM_BUILD_ROOT%{_infodir}/grub.info $RPM_BUILD_ROOT%{_infodir}/%{name}.info
mv $RPM_BUILD_ROOT%{_infodir}/grub-dev.info $RPM_BUILD_ROOT%{_infodir}/%{name}-dev.info
rm $RPM_BUILD_ROOT%{_infodir}/dir

# Defaults
mkdir ${RPM_BUILD_ROOT}%{_sysconfdir}/default
touch ${RPM_BUILD_ROOT}%{_sysconfdir}/default/grub
mkdir ${RPM_BUILD_ROOT}%{_sysconfdir}/sysconfig
ln -sf %{_sysconfdir}/default/grub \
	${RPM_BUILD_ROOT}%{_sysconfdir}/sysconfig/grub

cd ..
%find_lang grub

# Fedora theme in /boot/grub2/themes/system/
cd $RPM_BUILD_ROOT
tar xjf %{SOURCE5}
$RPM_BUILD_ROOT%{_bindir}/%{name}-mkfont -o boot/grub2/themes/system/DejaVuSans-10.pf2      -s 10 /usr/share/fonts/dejavu/DejaVuSans.ttf # "DejaVu Sans Regular 10"
$RPM_BUILD_ROOT%{_bindir}/%{name}-mkfont -o boot/grub2/themes/system/DejaVuSans-12.pf2      -s 12 /usr/share/fonts/dejavu/DejaVuSans.ttf # "DejaVu Sans Regular 12"
$RPM_BUILD_ROOT%{_bindir}/%{name}-mkfont -o boot/grub2/themes/system/DejaVuSans-Bold-14.pf2 -s 14 /usr/share/fonts/dejavu/DejaVuSans-Bold.ttf # "DejaVu Sans Bold 14"

# Make selinux happy with exec stack binaries.
mkdir ${RPM_BUILD_ROOT}%{_sysconfdir}/prelink.conf.d/
cat << EOF > ${RPM_BUILD_ROOT}%{_sysconfdir}/prelink.conf.d/grub2.conf
# these have execstack, and break under selinux
-b /usr/bin/grub2-script-check
-b /usr/bin/grub2-mkrelpath
-b /usr/bin/grub2-fstest
-b /usr/sbin/grub2-bios-setup
-b /usr/sbin/grub2-probe
-b /usr/sbin/grub2-sparc64-setup
EOF

%ifarch %{efiarchs}
mkdir -p boot/efi/EFI/%{efidir}/
ln -s /boot/efi/EFI/%{efidir}/grubenv boot/grub2/grubenv
%endif

%clean    
rm -rf $RPM_BUILD_ROOT

%pre tools
if [ -f /boot/grub2/user.cfg ]; then
    if grep -q '^GRUB_PASSWORD=' /boot/grub2/user.cfg ; then
	sed -i 's/^GRUB_PASSWORD=/GRUB2_PASSWORD=/' /boot/grub2/user.cfg
    fi
elif [ -f /boot/efi/EFI/%{efidir}/user.cfg ]; then
    if grep -q '^GRUB_PASSWORD=' /boot/efi/EFI/%{efidir}/user.cfg ; then
	sed -i 's/^GRUB_PASSWORD=/GRUB2_PASSWORD=/' \
	    /boot/efi/EFI/%{efidir}/user.cfg
    fi
elif [ -f /etc/grub.d/01_users ] && \
	grep -q '^password_pbkdf2 root' /etc/grub.d/01_users ; then
    if [ -f /boot/efi/EFI/%{efidir}/grub.cfg ]; then
	# on EFI we don't get permissions on the file, but
	# the directory is protected.
	grep '^password_pbkdf2 root' /etc/grub.d/01_users | \
		sed 's/^password_pbkdf2 root \(.*\)$/GRUB2_PASSWORD=\1/' \
	    > /boot/efi/EFI/%{efidir}/user.cfg
    fi
    if [ -f /boot/grub2/grub.cfg ]; then
	install -m 0600 /dev/null /boot/grub2/user.cfg
	chmod 0600 /boot/grub2/user.cfg
	grep '^password_pbkdf2 root' /etc/grub.d/01_users | \
		sed 's/^password_pbkdf2 root \(.*\)$/GRUB2_PASSWORD=\1/' \
	    > /boot/grub2/user.cfg
    fi
fi

%post tools
if [ "$1" = 1 ]; then
	/sbin/install-info --info-dir=%{_infodir} %{_infodir}/%{name}.info.gz || :
	/sbin/install-info --info-dir=%{_infodir} %{_infodir}/%{name}-dev.info.gz || :
fi

%triggerun -- grub2 < 1:1.99-4
# grub2 < 1.99-4 removed a number of essential files in postun. To fix upgrades
# from the affected grub2 packages, we first back up the files in triggerun and
# later restore them in triggerpostun.
# https://bugzilla.redhat.com/show_bug.cgi?id=735259

# Back up the files before uninstalling old grub2
mkdir -p /boot/grub2.tmp &&
mv -f /boot/grub2/*.mod \
      /boot/grub2/*.img \
      /boot/grub2/*.lst \
      /boot/grub2/device.map \
      /boot/grub2.tmp/ || :

%triggerpostun -- grub2 < 1:1.99-4
# ... and restore the files.
test ! -f /boot/grub2/device.map &&
test -d /boot/grub2.tmp &&
mv -f /boot/grub2.tmp/*.mod \
      /boot/grub2.tmp/*.img \
      /boot/grub2.tmp/*.lst \
      /boot/grub2.tmp/device.map \
      /boot/grub2/ &&
rm -r /boot/grub2.tmp/ || :

%preun tools
if [ "$1" = 0 ]; then
	/sbin/install-info --delete --info-dir=%{_infodir} %{_infodir}/%{name}.info.gz || :
	/sbin/install-info --delete --info-dir=%{_infodir} %{_infodir}/%{name}-dev.info.gz || :
fi

%ifnarch %{efi_only}
%files -f grub.lang
%defattr(-,root,root,-)
%{_libdir}/grub/*-%{platform}/
%config(noreplace) %{_sysconfdir}/%{name}.cfg
%ghost %config(noreplace) /boot/%{name}/grub.cfg
%doc grub-%{tarversion}/COPYING
%config(noreplace) %ghost /boot/grub2/grubenv
%endif

%ifarch %{efiarchs}
%files efi
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/%{name}-efi.cfg
%attr(0755,root,root)/boot/efi/EFI/%{efidir}
%attr(0755,root,root)/boot/efi/EFI/%{efidir}/fonts
%ghost %config(noreplace) /boot/efi/EFI/%{efidir}/grub.cfg
%doc grub-%{tarversion}/COPYING
/boot/grub2/grubenv
# I know 0700 seems strange, but it lives on FAT so that's what it'll
# get no matter what we do.
%config(noreplace) %ghost %attr(0700,root,root)/boot/efi/EFI/%{efidir}/grubenv

%files efi-modules
%defattr(-,root,root,-)
%{_libdir}/grub/%{grubefiarch}
%endif

%files tools -f grub.lang
%defattr(-,root,root,-)
%dir %{_libdir}/grub/
%dir %{_datarootdir}/grub/
%dir %{_datarootdir}/grub/themes
%{_datarootdir}/grub/*
%{_sbindir}/%{name}-bios-setup
%{_sbindir}/%{name}-get-kernel-settings
%{_sbindir}/%{name}-install
%{_sbindir}/%{name}-macbless
%{_sbindir}/%{name}-mkconfig
%{_sbindir}/%{name}-ofpathname
%{_sbindir}/%{name}-probe
%{_sbindir}/%{name}-reboot
%{_sbindir}/%{name}-rpm-sort
%{_sbindir}/%{name}-set-default
%{_sbindir}/%{name}-setpassword
%{_sbindir}/%{name}-sparc64-setup
%{_bindir}/%{name}-editenv
%{_bindir}/%{name}-file
%{_bindir}/%{name}-fstest
%{_bindir}/%{name}-glue-efi
%{_bindir}/%{name}-kbdcomp
%{_bindir}/%{name}-menulst2cfg
%{_bindir}/%{name}-mkfont
%{_bindir}/%{name}-mkimage
%{_bindir}/%{name}-mklayout
%{_bindir}/%{name}-mknetdir
%{_bindir}/%{name}-mkpasswd-pbkdf2
%{_bindir}/%{name}-mkrelpath
%ifnarch %{sparc}
%{_bindir}/%{name}-mkrescue
%endif
%{_bindir}/%{name}-mkstandalone
%{_bindir}/%{name}-render-label
%{_bindir}/%{name}-script-check
%{_bindir}/%{name}-syslinux2cfg
%{_datarootdir}/bash-completion/completions/grub
%{_sysconfdir}/prelink.conf.d/grub2.conf
%attr(0700,root,root) %dir %{_sysconfdir}/grub.d
%config %{_sysconfdir}/grub.d/??_*
%{_sysconfdir}/grub.d/README
%attr(0644,root,root) %ghost %config(noreplace) %{_sysconfdir}/default/grub
%{_sysconfdir}/sysconfig/grub
%attr(0700,root,root) %dir /boot/%{name}
%dir /boot/%{name}/themes/
%dir /boot/%{name}/themes/system
%exclude /boot/%{name}/themes/system/*
%exclude %{_datarootdir}/grub/themes/
%{_infodir}/%{name}*
%doc grub-%{tarversion}/COPYING grub-%{tarversion}/INSTALL
%doc grub-%{tarversion}/NEWS grub-%{tarversion}/README
%doc grub-%{tarversion}/THANKS grub-%{tarversion}/TODO
%doc grub-%{tarversion}/grub.html
%doc grub-%{tarversion}/grub-dev.html grub-%{tarversion}/docs/font_char_metrics.png
%doc %{_mandir}/man1/*
%doc %{_mandir}/man3/*
%doc %{_mandir}/man8/*
%dir /boot/%{name}/themes/
%dir %{_datarootdir}/grub/themes
%exclude %{_datarootdir}/grub/themes/starfield

%changelog
* Mon Aug 29 2016 Peter Jones <pjones@redhat.com> - 2.02-0.44
- Work around tftp servers that don't work with multiple consecutive slashes in
  file paths.
  Resolves: rhbz#1217243

* Thu Aug 25 2016 Peter Jones <pjones@redhat.com> - 2.02-0.42
- Make grub2-mkconfig export grub2-get-kernel-settings variables correctly.
  Related: rhbz#1226325

* Tue Aug 23 2016 Peter Jones <pjones@redhat.com> - 2.02-0.42
- Rebuild in the right build root.  Again.
  Related: rhbz#1273974

* Wed Jul 13 2016 Peter Jones <pjones@redhat.com> - 2.02-0.41
- Build with coverity patch I missed last time.
  Related: rhbz#1226325

* Wed Jul 13 2016 rmarshall@redhat.com - 2.02-0.40
- Build with coverity patches.
  Related: rhbz#1226325

* Wed Jul 13 2016 Peter Jones <pjones@redhat.com>
- Remove our patch to force a paricular uefi network interface
  Related: rhbz#1273974
  Related: rhbz#1277599
  Related: rhbz#1298765
- Update some more coverity issues
  Related: rhbz#1226325
  Related: rhbz#1154226

* Mon Jul 11 2016 rmarshall@redhat.com - 2.02-0.39
- Fix all issues discovered during coverity scan. 
  Related: rhbz#1154226
- Fix a couple compiler and CLANG issues discovered during coverity scan.
  Related: rhbz#1154226
- Fix the last few CLANG issues and a deadcode issue discovered by the
  coverity scan.
  Related: rhbz#1154226

* Fri Jul 01 2016 Peter Jones <pjones@redhat.com> - 2.02-0.38
- Pick the right build target.  Again.
  Related: rhbz#1226325

* Tue Jun 21 2016 rmarshall@redhat.com - 2.02-0.37
- Update fix for rhbz#1212114 to reflect the move to handling this case
  in anaconda.
  Related: rhbz#1315468
  Resolves: rhbz#1261926
- Add grub2-get-kernel-settings to allow grub2-mkconfig to take grubby
  configuration changes into account.
  Resolves: rhbz#1226325

* Fri Jun 17 2016 Peter Jones <pjones@redhat.com> - 2.02-0.36
- Better support for EFI network booting with dhcpv6.
  Resolves: rhbz#1154226
- Back out a duplicate change resulting in some EFI network firmware drivers
  not working properly.
  Related: rhbz#1273974
  Related: rhbz#1277599
  Related: rhbz#1298765

* Mon Jun 06 2016 Peter Jones <pjones@redhat.com> - 2.02-0.35
- Don't use legacy methods to make device node variables.
  Resolves: rhbz#1279599
- Don't pad initramfs with zeros
  Resolves: rhbz#1219864

* Thu Apr 28 2016 rmarshall@redhat.com 2.02-0.34
- Exit grub-mkconfig with a proper code when the new configuration would be
  invalid.
  Resolves: rhbz#1252311
- Warn users if grub-mkconfig needs to be run to add support for GRUB
  passwords.
  Resolves: rhbz#1290803
- Fix the information in the --help and man pages for grub-setpassword
  Resolves: rhbz#1290799
- Fix issue where shell substitution expected non-translated output when
  setting a bootloader password.
  Resolves: rhbz#1294243
- Fix an issue causing memory regions with unknown types to be marked available
  through a series of backports from upstream.
  Resolves: rhbz#1288608

* Thu Dec 10 2015 Peter Jones <pjones@redhat.com> - 2.02-0.33
- Don't remove 01_users, it's the wrong thing to do.
  Related: rhbz#1284370

* Wed Dec 09 2015 Peter Jones <pjones@redhat.com> - 2.02-0.32
- Rebuild for .z so the release number is different.
  Related: rhbz#1284370

* Wed Dec 09 2015 Peter Jones <pjones@redhat.com> - 2.02-0.31
- More work on handling of GRUB2_PASSWORD
  Resolves: rhbz#1284370

* Tue Dec 08 2015 Peter Jones <pjones@redhat.com> - 2.02-0.30
- Fix security issue when reading username and password
  Resolves: CVE-2015-8370
- Do a better job of handling GRUB_PASSWORD
  Resolves: rhbz#1284370

* Fri Oct 09 2015 Peter Jones <pjones@redhat.com> - 2.02-0.29
- Fix DHCP6 timeouts due to failed network stack once more.
  Resolves: rhbz#1267139

* Thu Sep 17 2015 Peter Jones <pjones@redhat.com> - 2.02-0.28
- Once again, rebuild for the right build target.
  Resolves: CVE-2015-5281

* Thu Sep 17 2015 Peter Jones <pjones@redhat.com> - 2.02-0.27
- Remove multiboot and multiboot2 modules from the .efi builds; they
  should never have been there.
  Resolves: CVE-2015-5281

* Mon Sep 14 2015 Peter Jones <pjones@redhat.com> - 2.02-0.26
- Be more aggressive about trying to make sure we use the configured SNP
  device in UEFI.
  Resolves: rhbz#1257475

* Wed Aug 05 2015 Robert Marshall <rmarshall@redhat.com> - 2.02-0.25
- Force file sync to disk on ppc64le machines.
  Resolves: rhbz#1212114

* Mon Aug 03 2015 Peter Jones <pjones@redhat.com> - 2.02-0.24
- Undo 0.23 and fix it a different way.
  Resolves: rhbz#1124074

* Thu Jul 30 2015 Peter Jones <pjones@redhat.com> - 2.02-0.23
- Reverse kernel sort order so they're displayed correctly.
  Resolves: rhbz#1124074

* Wed Jul 08 2015 Peter Jones <pjones@redhat.com> - 2.02-0.22
- Make upgrades work reasonably well with grub2-setpassword .
  Related: rhbz#985962

* Tue Jul 07 2015 Peter Jones <pjones@redhat.com> - 2.02-0.21
- Add a simpler grub2 password config tool
  Related: rhbz#985962
- Some more coverity nits.

* Mon Jul 06 2015 Peter Jones <pjones@redhat.com> - 2.02-0.20
- Deal with some coverity nits.
  Related: rhbz#1215839
  Related: rhbz#1124074

* Mon Jul 06 2015 Peter Jones <pjones@redhat.com> - 2.02-0.19
- Rebuild for Aarch64
- Deal with some coverity nits.
  Related: rhbz#1215839
  Related: rhbz#1124074

* Thu Jul 02 2015 Peter Jones <pjones@redhat.com> - 2.02-0.18
- Update for an rpmdiff problem with one of the man pages.
  Related: rhbz#1124074

* Tue Jun 30 2015 Peter Jones <pjones@redhat.com> - 2.02-0.17
- Handle ipv6 better
  Resolves: rhbz#1154226
- On UEFI, use SIMPLE_NETWORK_PROTOCOL when we can.
  Resolves: rhbz#1233378
- Handle rssd disk drives in grub2 utilities.
  Resolves: rhbz#1087962
- Handle xfs CRC disk format.
  Resolves: rhbz#1001279
- Calibrate TCS using the EFI Stall service
  Resolves: rhbz#1150698
- Fix built-in gpg verification when using TFTP
  Resolves: rhbz#1167977
- Generate better stanza titles so grubby can find them easier.
  Resolves: rhbz#1177003
- Don't strip the fw_path variable twice when we're using EFI networking.
  Resolves: rhbz#1211101

* Mon May 11 2015 Peter Jones <pjones@redhat.com> - 2.02-0.17
- Document network boot paths better
  Resolves: rhbz#1148650
- Use an rpm-based version sorted in grub2-mkconfig
  Resolves: rhbz#1124074

* Thu Oct 09 2014 Peter Jones <pjones@redhat.com> - 2.02-0.16
- ... and build it on the right target.
  Related: rhbz#1148652

* Thu Oct 09 2014 Peter Jones <pjones@redhat.com> - 2.02-0.15
- Make netbooting do a better job of picking the config path *again*.
  Resolves: rhbz#1148652

* Sat Oct 04 2014 Peter Jones <pjones@redhat.com> - 2.02-0.14
- Be sure to *install* gcdaa64.efi
  Related: rhbz#1100048

* Fri Sep 26 2014 Peter Jones <pjones@redhat.com> - 2.02-0.13
- Make sure to build a gcdaa64.efi
  Related: rhbz#1100048

* Tue Sep 23 2014 Peter Jones <pjones@redhat.com> - 2.02-0.12
- Fix minor problems rpmdiff found.
  Related: rhbz#1125540

* Mon Sep 22 2014 Peter Jones <pjones@redhat.com> - 2.02-0.11
- Fix grub2 segfault when root isn't set.
  Resolves: rhbz#1084536
- Make the aarch64 loader be SB-aware.
  Related: rhbz#1100048
- Enable regexp module
  Resolves: rhbz#1125916

* Thu Sep 04 2014 Peter Jones <pjones@redhat.com> - 2.02-0.10
- Make editenv utilities (grub2-editenv, grub2-set-default, etc.) from
  non-UEFI builds work with UEFI builds as well, since they're shared
  from grub2-tools.
  Resolves: rhbz#1119943
- Make more grub2-mkconfig generate menu entries with the OS name and version
  included.
  Resolves: rhbz#996794
- Minimize the sort ordering for .debug and -rescue- kernels.
  Resolves: rhbz#1065360
- Add GRUB_DISABLE_UUID to disable filesystem searching by UUID.
  Resolves: rhbz#1027833
- Allow "fallback" to specify titles like the documentation says
  Resolves: rhbz#1026084

* Wed Aug 27 2014 Peter Jones <pjones@redhat.com> - 2.02-0.9.1
- A couple of patches for aarch64 got missed.
  Related: rhbz#967937

* Wed Aug 27 2014 Peter Jones <pjones@redhat.com> - 2.02-0.9
- Once again, I have built with the wrong target.
  Related: rhbz#1125540
  Resolves: rhbz#967937

* Fri Aug 22 2014 Peter Jones <pjones@redhat.com> - 2.02-0.8
- Add patches for ppc64le
  Related: rhbz#1125540

* Thu Mar 20 2014 Peter Jones <pjones@redhat.com> - 2.02-0.2.10
- Fix GRUB_DISABLE_SUBMENU one more time.
  Resolves: rhbz#1063414

* Tue Mar 18 2014 Peter Jones <pjones@redhat.com> - 2.02-0.2.9
- Not sure why the right build target wasn't used *again*.
  Resolves: rhbz#1073337

* Wed Mar 12 2014 Peter Jones <pjones@redhat.com> - 2.02-0.2.8
- Make GRUB_DISABLE_SUBMENU work again.
  Resolves: rhbz#1063414

* Thu Mar 06 2014 Peter Jones <pjones@redhat.com> - 2.02-0.2.7
- Build on the right target.
  Resolves: rhbz#1073337

* Wed Mar 05 2014 Peter Jones <pjones@redhat.com> - 2.02-0.2.6
- Fix minor man page install bug
  Related: rhbz#948847

* Tue Mar 04 2014 Peter Jones <pjones@redhat.com> - 2.02-0.2.5
- Add man pages for common grub utilities.
  Resolves: rhbz#948847
- Fix shift key behavior on UEFI.
  Resolves: rhbz#1068215

* Tue Feb 18 2014 Peter Jones <pjones@redhat.com> - 2.02-0.2.4
- Build against the right target.
  Related: rhbz#1064424

* Tue Feb 18 2014 Peter Jones <pjones@redhat.com> - 2.02-0.2.3
- Don't emit "Booting <foo>" message.
  Resolves: rhbz#1023142
- Don't require a password for booting, only for editing entries.
  Resolves: rhbz#1030176
- Several network fixes from IBM
  Resolves: rhbz#1056324
- Support NVMe device names
  Resolves: rhbz#1019660
- Make control keys work on UEFI systems.
  Resolves: rhbz#1056035

* Fri Jan 31 2014 Peter Jones <pjones@redhat.com> - 2.02-0.2.2
- Fix FORTIFY_SOURCE for util/
  Related: rhbz#1049047

* Tue Jan 21 2014 Peter Jones <pjones@redhat.com> - 2.02-0.2.1
- Don't destroy symlinks when re-writing grub.cfg
  Resolves: rhbz#1032182

* Mon Jan 06 2014 Peter Jones <pjones@redhat.com> - 2.02-0.2
- Update to grub-2.02~beta2

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 1:2.00-23
- Mass rebuild 2013-12-27

* Wed Nov 20 2013 Peter Jones <pjones@redhat.com> - 2.00-22.10
- Rebuild with correct release number and with correct target.
  Related: rhbz#1032530

* Wed Nov 20 2013 Daniel Mach <dmach@redhat.com> - 2.00-22.9.1
- Enable tftp module
  Resolves: rhbz#1032530

* Thu Nov 14 2013 Peter Jones <pjones@redhat.com> - 2.00-22.9
- Make "linux16" happen on x86_64 machines as well.
  Resolves: rhbz#880840

* Wed Nov 06 2013 Peter Jones <pjones@redhat.com> - 2.00-22.8
- Rebuild with correct build target for signing.
  Related: rhbz#996863

* Tue Nov 05 2013 Peter Jones <pjones@redhat.com> - 2.00-22.7
- Build with -mcpu=power6 as we did before redhat-rpm-config changed
  Resolves: rhbz#1026368

* Thu Oct 31 2013 Peter Jones <pjones@redhat.com> - 2.00-22.6
- Make linux16 work with the shell better.
  Resolves: rhbz#880840

* Thu Oct 31 2013 Peter Jones <pjones@redhat.com> - 2.00-22.5
- Rebuild because we were clobbering signing in the spec file...
  Related: rhbz#1017855

* Thu Oct 31 2013 Peter Jones <pjones@redhat.com> - 2.00-22.4
- Rebuild because signing didn't work.
  Related: rhbz#1017855

* Mon Oct 28 2013 Peter Jones <pjones@redhat.com> - 2.00-22.3
- Use linux16 when appropriate:
  Resolves: rhbz#880840
- Enable pager by default:
  Resolves: rhbz#985860
- Don't ask the user to hit keys that won't work.
  Resolves: rhbz#987443
- Sign grub2 during builds
  Resolves: rhbz#1017855

* Thu Aug 29 2013 Peter Jones <pjones@redhat.com> - 2.00-22.2
- Fix minor rpmdiff complaints.

* Wed Aug 07 2013 Peter Jones <pjones@redhat.com> - 2.00-22.1
- Fix url so PkgWrangler doesn't go crazy.

* Fri Jun 21 2013 Peter Jones <pjones@redhat.com> - 2.00-22
- Fix linewrapping in edit menu.
  Resolves: rhbz #976643

* Thu Jun 20 2013 Peter Jones <pjones@redhat.com> - 2.00-21
- Fix obsoletes to pull in -starfield-theme subpackage when it should.

* Fri Jun 14 2013 Peter Jones <pjones@redhat.com> - 2.00-20
- Put the theme entirely ento the subpackage where it belongs (#974667)

* Wed Jun 12 2013 Peter Jones <pjones@redhat.com> - 2.00-19
- Rebase to upstream snapshot.
- Fix PPC build error (#967862)
- Fix crash on net_bootp command (#960624)
- Reset colors on ppc when appropriate (#908519)
- Left align "Loading..." messages (#908492)
- Fix probing of SAS disks on PPC (#953954)
- Add support for UEFI OSes returned by os-prober
- Disable "video" mode on PPC for now (#973205)
- Make grub fit better into the boot sequence, visually (#966719)

* Fri May 10 2013 Matthias Clasen <mclasen@redhat.com> - 2.00-18
- Move the starfield theme to a subpackage (#962004)
- Don't allow SSE or MMX on UEFI builds (#949761)

* Wed Apr 24 2013 Peter Jones <pjones@redhat.com> - 2.00-17.pj0
- Rebase to upstream snapshot.

* Thu Apr 04 2013 Peter Jones <pjones@redhat.com> - 2.00-17
- Fix booting from drives with 4k sectors on UEFI.
- Move bash completion to new location (#922997)
- Include lvm support for /boot (#906203)

* Thu Feb 14 2013 Peter Jones <pjones@redhat.com> - 2.00-16
- Allow the user to disable submenu generation
- (partially) support BLS-style configuration stanzas.

* Tue Feb 12 2013 Peter Jones <pjones@redhat.com> - 2.00-15.pj0
- Add various config file related changes.

* Thu Dec 20 2012 Dennis Gilmore <dennis@ausil.us> - 2.00-15
- bump nvr

* Mon Dec 17 2012 Karsten Hopp <karsten@redhat.com> 2.00-14
- add bootpath device to the device list (pfsmorigo, #886685)

* Tue Nov 27 2012 Peter Jones <pjones@redhat.com> - 2.00-13
- Add vlan tag support (pfsmorigo, #871563)
- Follow symlinks during PReP installation in grub2-install (pfsmorigo, #874234)
- Improve search paths for config files on network boot (pfsmorigo, #873406)

* Tue Oct 23 2012 Peter Jones <pjones@redhat.com> - 2.00-12
- Don't load modules when grub transitions to "normal" mode on UEFI.

* Mon Oct 22 2012 Peter Jones <pjones@redhat.com> - 2.00-11
- Rebuild with newer pesign so we'll get signed with the final signing keys.

* Thu Oct 18 2012 Peter Jones <pjones@redhat.com> - 2.00-10
- Various PPC fixes.
- Fix crash fetching from http (gustavold, #860834)
- Issue separate dns queries for ipv4 and ipv6 (gustavold, #860829)
- Support IBM CAS reboot (pfsmorigo, #859223)
- Include all modules in the core image on ppc (pfsmorigo, #866559)

* Mon Oct 01 2012 Peter Jones <pjones@redhat.com> - 1:2.00-9
- Work around bug with using "\x20" in linux command line.
  Related: rhbz#855849

* Thu Sep 20 2012 Peter Jones <pjones@redhat.com> - 2.00-8
- Don't error on insmod on UEFI/SB, but also don't do any insmodding.
- Increase device path size for ieee1275
  Resolves: rhbz#857936
- Make network booting work on ieee1275 machines.
  Resolves: rhbz#857936

* Wed Sep 05 2012 Matthew Garrett <mjg@redhat.com> - 2.00-7
- Add Apple partition map support for EFI

* Thu Aug 23 2012 David Cantrell <dcantrell@redhat.com> - 2.00-6
- Only require pesign on EFI architectures (#851215)

* Tue Aug 14 2012 Peter Jones <pjones@redhat.com> - 2.00-5
- Work around AHCI firmware bug in efidisk driver.
- Move to newer pesign macros
- Don't allow insmod if we're in secure-boot mode.

* Wed Aug 08 2012 Peter Jones <pjones@redhat.com>
- Split module lists for UEFI boot vs UEFI cd images.
- Add raid modules for UEFI image (related: #750794)
- Include a prelink whitelist for binaries that need execstack (#839813)
- Include fix efi memory map fix from upstream (#839363)

* Wed Aug 08 2012 Peter Jones <pjones@redhat.com> - 2.00-4
- Correct grub-mkimage invocation to use efidir RPM macro (jwb)
- Sign with test keys on UEFI systems.
- PPC - Handle device paths with commas correctly.
  Related: rhbz#828740

* Wed Jul 25 2012 Peter Jones <pjones@redhat.com> - 2.00-3
- Add some more code to support Secure Boot, and temporarily disable
  some other bits that don't work well enough yet.
  Resolves: rhbz#836695

* Wed Jul 11 2012 Matthew Garrett <mjg@redhat.com> - 2.00-2
- Set a prefix for the image - needed for installer work
- Provide the font in the EFI directory for the same reason

* Thu Jun 28 2012 Peter Jones <pjones@redhat.com> - 2.00-1
- Rebase to grub-2.00 release.

* Mon Jun 18 2012 Peter Jones <pjones@redhat.com> - 2.0-0.37.beta6
- Fix double-free in grub-probe.

* Wed Jun 06 2012 Peter Jones <pjones@redhat.com> - 2.0-0.36.beta6
- Build with patch19 applied.

* Wed Jun 06 2012 Peter Jones <pjones@redhat.com> - 2.0-0.35.beta6
- More ppc fixes.

* Wed Jun 06 2012 Peter Jones <pjones@redhat.com> - 2.0-0.34.beta6
- Add IBM PPC fixes.

* Mon Jun 04 2012 Peter Jones <pjones@redhat.com> - 2.0-0.33.beta6
- Update to beta6.
- Various fixes from mads.

* Fri May 25 2012 Peter Jones <pjones@redhat.com> - 2.0-0.32.beta5
- Revert builddep change for crt1.o; it breaks ppc build.

* Fri May 25 2012 Peter Jones <pjones@redhat.com> - 2.0-0.31.beta5
- Add fwsetup command (pjones)
- More ppc fixes (IBM)

* Tue May 22 2012 Peter Jones <pjones@redhat.com> - 2.0-0.30.beta5
- Fix the /other/ grub2-tools require to include epoch.

* Mon May 21 2012 Peter Jones <pjones@redhat.com> - 2.0-0.29.beta5
- Get rid of efi_uga and efi_gop, favoring all_video instead.

* Mon May 21 2012 Peter Jones <pjones@redhat.com> - 2.0-0.28.beta5
- Name grub.efi something that's arch-appropriate (kiilerix, pjones)
- use EFI/$SOMETHING_DISTRO_BASED/ not always EFI/redhat/grub2-efi/ .
- move common stuff to -tools (kiilerix)
- spec file cleanups (kiilerix)

* Mon May 14 2012 Peter Jones <pjones@redhat.com> - 2.0-0.27.beta5
- Fix module trampolining on ppc (benh)

* Thu May 10 2012 Peter Jones <pjones@redhat.com> - 2.0-0.27.beta5
- Fix license of theme (mizmo)
  Resolves: rhbz#820713
- Fix some PPC bootloader detection IBM problem
  Resolves: rhbz#820722

* Thu May 10 2012 Peter Jones <pjones@redhat.com> - 2.0-0.26.beta5
- Update to beta5.
- Update how efi building works (kiilerix)
- Fix theme support to bring in fonts correctly (kiilerix, pjones)

* Wed May 09 2012 Peter Jones <pjones@redhat.com> - 2.0-0.25.beta4
- Include theme support (mizmo)
- Include locale support (kiilerix)
- Include html docs (kiilerix)

* Thu Apr 26 2012 Peter Jones <pjones@redhat.com> - 2.0-0.24
- Various fixes from Mads Kiilerich

* Thu Apr 19 2012 Peter Jones <pjones@redhat.com> - 2.0-0.23
- Update to 2.00~beta4
- Make fonts work so we can do graphics reasonably

* Thu Mar 29 2012 David Aquilina <dwa@redhat.com> - 2.0-0.22
- Fix ieee1275 platform define for ppc

* Thu Mar 29 2012 Peter Jones <pjones@redhat.com> - 2.0-0.21
- Remove ppc excludearch lines (dwa)
- Update ppc terminfo patch (hamzy)

* Wed Mar 28 2012 Peter Jones <pjones@redhat.com> - 2.0-0.20
- Fix ppc64 vs ppc exclude according to what dwa tells me they need
- Fix version number to better match policy.

* Tue Mar 27 2012 Dan Horák <dan[at]danny.cz> - 1.99-19.2
- Add support for serial terminal consoles on PPC by Mark Hamzy

* Sun Mar 25 2012 Dan Horák <dan[at]danny.cz> - 1.99-19.1
- Use Fix-tests-of-zeroed-partition patch by Mark Hamzy

* Thu Mar 15 2012 Peter Jones <pjones@redhat.com> - 1.99-19
- Use --with-grubdir= on configure to make it behave like -17 did.

* Wed Mar 14 2012 Peter Jones <pjones@redhat.com> - 1.99-18
- Rebase from 1.99 to 2.00~beta2

* Wed Mar 07 2012 Peter Jones <pjones@redhat.com> - 1.99-17
- Update for newer autotools and gcc 4.7.0
  Related: rhbz#782144
- Add /etc/sysconfig/grub link to /etc/default/grub
  Resolves: rhbz#800152
- ExcludeArch s390*, which is not supported by this package.
  Resolves: rhbz#758333

* Fri Feb 17 2012 Orion Poplawski <orion@cora.nwra.com> - 1:1.99-16
- Build with -Os (bug 782144)

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.99-15
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Wed Dec 14 2011 Matthew Garrett <mjg@redhat.com> - 1.99-14
- fix up various grub2-efi issues

* Thu Dec 08 2011 Adam Williamson <awilliam@redhat.com> - 1.99-13
- fix hardwired call to grub-probe in 30_os-prober (rhbz#737203)

* Mon Nov 07 2011 Peter Jones <pjones@redhat.com> - 1.99-12
- Lots of .spec fixes from Mads Kiilerich:
  Remove comment about update-grub - it isn't run in any scriptlets
  patch info pages so they can be installed and removed correctly when renamed
  fix references to grub/grub2 renames in info pages (#743964)
  update README.Fedora (#734090)
  fix comments for the hack for upgrading from grub2 < 1.99-4
  fix sed syntax error preventing use of $RPM_OPT_FLAGS (#704820)
  make /etc/grub2*.cfg %config(noreplace)
  make grub.cfg %ghost - an empty file is of no use anyway
  create /etc/default/grub more like anaconda would create it (#678453)
  don't create rescue entries by default - grubby will not maintain them anyway
  set GRUB_SAVEDEFAULT=true so saved defaults works (rbhz#732058)
  grub2-efi should have its own bash completion
  don't set gfxpayload in efi mode - backport upstream r3402
- Handle dmraid better. Resolves: rhbz#742226

* Wed Oct 26 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.99-11
- Rebuilt for glibc bug#747377

* Wed Oct 19 2011 Adam Williamson <awilliam@redhat.com> - 1.99-10
- /etc/default/grub is explicitly intended for user customization, so
  mark it as config(noreplace)

* Tue Oct 11 2011 Peter Jones <pjones@redhat.com> - 1.99-9
- grub has an epoch, so we need that expressed in the obsolete as well.
  Today isn't my day.

* Tue Oct 11 2011 Peter Jones <pjones@redhat.com> - 1.99-8
- Fix my bad obsoletes syntax.

* Thu Oct 06 2011 Peter Jones <pjones@redhat.com> - 1.99-7
- Obsolete grub
  Resolves: rhbz#743381

* Wed Sep 14 2011 Peter Jones <pjones@redhat.com> - 1.99-6
- Use mv not cp to try to avoid moving disk blocks around for -5 fix
  Related: rhbz#735259
- handle initramfs on xen better (patch from Marko Ristola)
  Resolves: rhbz#728775

* Sat Sep 03 2011 Kalev Lember <kalevlember@gmail.com> - 1.99-5
- Fix upgrades from grub2 < 1.99-4 (#735259)

* Fri Sep 02 2011 Peter Jones <pjones@redhat.com> - 1.99-4
- Don't do sysadminny things in %preun or %post ever. (#735259)
- Actually include the changelog in this build (sorry about -3)

* Thu Sep 01 2011 Peter Jones <pjones@redhat.com> - 1.99-2
- Require os-prober (#678456) (patch from Elad Alfassa)
- Require which (#734959) (patch from Elad Alfassa)

* Thu Sep 01 2011 Peter Jones <pjones@redhat.com> - 1.99-1
- Update to grub-1.99 final.
- Fix crt1.o require on x86-64 (fix from Mads Kiilerich)
- Various CFLAGS fixes (from Mads Kiilerich)
  - -fexceptions and -m64
- Temporarily ignore translations (from Mads Kiilerich)

* Thu Jul 21 2011 Peter Jones <pjones@redhat.com> - 1.99-0.3
- Use /sbin not /usr/sbin .

* Thu Jun 23 2011 Peter Lemenkov <lemenkov@gmail.com> - 1:1.99-0.2
- Fixes for ppc and ppc64

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.98-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild
