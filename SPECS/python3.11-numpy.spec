%global __python3 /usr/bin/python3.11
%global python3_pkgversion 3.11

#uncomment next line for a release candidate or a beta
#%%global relc rc1

# RHEL: Tests disabled due to missing dependencies
%bcond_with tests

%if 0%{?fedora} >= 33 || 0%{?rhel} >= 9
%global blaslib flexiblas
%global blasvar %{nil}
%else
%global blaslib openblas
%global blasvar p
%endif

%global modname numpy

Name:           python%{python3_pkgversion}-numpy
Version:        1.23.5
Release:        1%{?dist}
Summary:        A fast multidimensional array facility for Python

# Everything is BSD except for class SafeEval in numpy/lib/utils.py which is Python
License:        BSD and Python and ASL 2.0
URL:            http://www.numpy.org/
Source0:        https://github.com/%{modname}/%{modname}/releases/download/v%{version}/%{modname}-%{version}.tar.gz

BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-rpm-macros
BuildRequires:  python%{python3_pkgversion}-setuptools
BuildRequires:  python%{python3_pkgversion}-Cython
BuildRequires:  gcc-gfortran gcc gcc-c++
BuildRequires:  lapack-devel
%if %{with tests}
BuildRequires:  python%{python3_pkgversion}-hypothesis
BuildRequires:  python%{python3_pkgversion}-pytest
BuildRequires:  python%{python3_pkgversion}-test
BuildRequires:  python%{python3_pkgversion}-typing-extensions
%endif
BuildRequires: %{blaslib}-devel
BuildRequires: chrpath

%description
NumPy is a general-purpose array-processing package designed to
efficiently manipulate large multi-dimensional arrays of arbitrary
records without sacrificing too much speed for small multi-dimensional
arrays.  NumPy is built on the Numeric code base and adds features
introduced by numarray as well as an extended C-API and the ability to
create arrays of arbitrary type.

There are also basic facilities for discrete fourier transform,
basic linear algebra and random number generation. Also included in
this package is a version of f2py that works properly with NumPy.


%package -n python%{python3_pkgversion}-numpy-f2py
Summary:        f2py for numpy
Requires:       python%{python3_pkgversion}-numpy%{?_isa} = %{version}-%{release}
Requires:       python%{python3_pkgversion}-devel
Provides:       python%{python3_pkgversion}-f2py = %{version}-%{release}

# Require alternatives version that implements the --keep-foreign flag
Requires(postun): alternatives >= 1.19.1-1
# python3.11 installs the alternatives master symlink to which we attach a slave
Requires: python%{python3_pkgversion}
Requires(post): python%{python3_pkgversion}
Requires(postun): python%{python3_pkgversion}

%description -n python%{python3_pkgversion}-numpy-f2py
This package includes a version of f2py that works properly with NumPy.

%prep
%autosetup -n %{modname}-%{version} -p1

# Force re-cythonization (ifed for PKG-INFO presence in setup.py)
rm PKG-INFO

# openblas is provided by flexiblas by default; otherwise,
# Use openblas pthreads as recommended by upstream (see comment in site.cfg.example)
cat >> site.cfg <<EOF
[openblas]
libraries = %{blaslib}%{blasvar}
library_dirs = %{_libdir}
EOF

%build
%set_build_flags

env OPENBLAS=%{_libdir} \
    BLAS=%{_libdir} \
    LAPACK=%{_libdir} CFLAGS="%{optflags}" \
    %{__python3} setup.py build

%install
#%%{__python3} setup.py install -O1 --skip-build --root %%{buildroot}
# skip-build currently broken, this works around it for now
env OPENBLAS=%{_libdir} \
    FFTW=%{_libdir} BLAS=%{_libdir} \
    LAPACK=%{_libdir} CFLAGS="%{optflags}" \
    %{__python3} setup.py install --root %{buildroot} --prefix=%{_prefix}
pushd %{buildroot}%{_bindir} &> /dev/null
# Remove unversioned binaries
rm f2py
rm f2py3
popd &> /dev/null

# All ghost files controlled by alternatives need to exist for the files
# section check to succeed
touch %{buildroot}%{_bindir}/f2py3

# distutils from setuptools don't have the patch that was created to avoid standard runpath here
# we strip it manually instead
# ERROR   0001: file '...' contains a standard runpath '/usr/lib64' in [/usr/lib64]
chrpath --delete %{buildroot}%{python3_sitearch}/%{modname}/core/_multiarray_umath.*.so
chrpath --delete %{buildroot}%{python3_sitearch}/%{modname}/linalg/lapack_lite.*.so
chrpath --delete %{buildroot}%{python3_sitearch}/%{modname}/linalg/_umath_linalg.*.so

%check
%if %{with tests}
export PYTHONPATH=%{buildroot}%{python3_sitearch}
# test_ppc64_ibm_double_double128 is unnecessary now that ppc64le has switched long doubles to IEEE format.
# https://github.com/numpy/numpy/issues/21094
%ifarch %{ix86}
# Weird RuntimeWarnings on i686, similar to https://github.com/numpy/numpy/issues/13173
# Some tests also overflow on 32bit
%global ix86_k and not test_vector_matrix_values and not test_matrix_vector_values and not test_identityless_reduction_huge_array and not (TestKind and test_all)
%endif
%{__python3} runtests.py -v --no-build -- -ra -k 'not test_ppc64_ibm_double_double128 %{?ix86_k}'
%endif

%post -n python%{python3_pkgversion}-numpy-f2py
alternatives --add-slave python3 %{_bindir}/python%{python3_version} \
    %{_bindir}/f2py3 \
    f2py3 \
    %{_bindir}/f2py%{python3_version}

%postun -n python%{python3_pkgversion}-numpy-f2py
# Do this only during uninstall process (not during update)
if [ $1 -eq 0 ]; then
   alternatives --keep-foreign --remove-slave python3 %{_bindir}/python%{python3_version} \
       f2py3
fi


%files -n python%{python3_pkgversion}-numpy
%license LICENSE.txt
%doc THANKS.txt site.cfg.example
%{python3_sitearch}/%{modname}/__pycache__/
%dir %{python3_sitearch}/%{modname}
%{python3_sitearch}/%{modname}/*.py*
%{python3_sitearch}/%{modname}/core
%{python3_sitearch}/%{modname}/distutils
%{python3_sitearch}/%{modname}/doc
%{python3_sitearch}/%{modname}/fft
%{python3_sitearch}/%{modname}/lib
%{python3_sitearch}/%{modname}/linalg
%{python3_sitearch}/%{modname}/ma
%{python3_sitearch}/%{modname}/random
%{python3_sitearch}/%{modname}/testing
%{python3_sitearch}/%{modname}/tests
%{python3_sitearch}/%{modname}/compat
%{python3_sitearch}/%{modname}/matrixlib
%{python3_sitearch}/%{modname}/polynomial
%{python3_sitearch}/%{modname}-*.egg-info
%exclude %{python3_sitearch}/%{modname}/LICENSE.txt
%{python3_sitearch}/%{modname}/__init__.pxd
%{python3_sitearch}/%{modname}/__init__.cython-30.pxd
%{python3_sitearch}/%{modname}/py.typed
%{python3_sitearch}/%{modname}/typing/
%{python3_sitearch}/%{modname}/array_api/
%{python3_sitearch}/%{modname}/_pyinstaller/
%{python3_sitearch}/%{modname}/_typing/

%files -n python%{python3_pkgversion}-numpy-f2py
%{_bindir}/f2py%{python3_pkgversion}
%ghost %{_bindir}/f2py3
%{python3_sitearch}/%{modname}/f2py


%changelog
* Fri Dec 02 2022 Charalampos Stratakis <cstratak@redhat.com> - 1.23.5-1
- Initial package
- Fedora contributions by:
      Bill Nottingham <notting@fedoraproject.org>
      Charalampos Stratakis <cstratak@redhat.com>
      Christian Dersch <lupinix@mailbox.org>
      Dan Horák <sharkcz@fedoraproject.org>
      David Malcolm <dmalcolm@redhat.com>
      David Tardon <dtardon@redhat.com>
      Deji Akingunola <deji@fedoraproject.org>
      Dennis Gilmore <dennis@ausil.us>
      Elliott Sales de Andrade <quantum.analyst@gmail.com>
      Gwyn Ciesla <limburgher@gmail.com>
      Ignacio Vazquez-Abrams <ivazquez@fedoraproject.org>
      Iñaki Úcar <iucar@fedoraproject.org>
      Iryna Shcherbina <shcherbina.iryna@gmail.com>
      Jarod Wilson <jwilson@fedoraproject.org>
      Jaromir Capik <jcapik@redhat.com>
      Jef Spaleta <jspaleta@fedoraproject.org>
      Jesse Keating <jkeating@fedoraproject.org>
      Jon Ciesla <limb@fedoraproject.org>
      Kalev Lember <klember@redhat.com>
      Karolina Surma <ksurma@redhat.com>
      Lumir Balhar <lbalhar@redhat.com>
      Merlin Mathesius <mmathesi@redhat.com>
      Miro Hrončok <miro@hroncok.cz>
      Nikola Forró <nforro@redhat.com>
      Orion Poplawski <orion@nwra.com>
      Pavel Šimovec <psimovec@redhat.com>
      Peter Robinson <pbrobinson@fedoraproject.org>
      Robert Kuska <rkuska@redhat.com>
      Simone Caronni <negativo17@gmail.com>
      Thomas Spura <tomspur@fedoraproject.org>
      Tomáš Hrnčiar <thrnciar@redhat.com>
      Tomas Orsava <torsava@redhat.com>
      Tomas Tomecek <ttomecek@redhat.com>
      Ville Skyttä <scop@fedoraproject.org>
