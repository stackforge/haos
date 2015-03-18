Name:       python-shaker
Epoch:      1
Version:    0.2.2
Release:    1%{?dist}
Summary:    EC2 Salt Minion Launcher
License:    ASL 2.0
URL:        http://pypi.python.org/pypi/%{name}
Source0:    http://pypi.python.org/packages/source/p/%{name}/%{name}-%{version}.tar.gz

BuildArch:  noarch

BuildRequires: python2-devel
BuildRequires: python-setuptools
BuildRequires: python-pbr
BuildRequires: python-d2to1
BuildRequires: python-sphinx
BuildRequires: python-oslo-sphinx
BuildRequires: python-six



Requires:      python-pbr >= 0.8, python-pbr <= 1.0
Requires:      python-iso8601 >= 0.1.9
Requires:      python-jinja2 >= 2.6
Requires:      python-oslo-concurrency >= 1.3.0
Requires:      python-oslo-config >= 1.6.0
Requires:      python-oslo-i18n >= 1.3.0
Requires:      python-oslo-log >= 0.4.0
Requires:      python-oslo-serialization >= 1.2.0
Requires:      python-oslo-utils >= 1.2.0
Requires:      python-glanceclient >= 0.15.0
Requires:      python-keystoneclient >= 1.1.0
Requires:      python-neutronclient >= 2.3.11, python-neutronclient < 3
Requires:      python-novaclient >= 2.18.0, python-novaclient < 2.21.0, python-novaclient > 2.21.0
Requires:      python-heatclient >= 0.3.0
Requires:      PyYAML >= 3.1.0
Requires:      python-zmq >= 14.3.1
Requires:      python-six >= 1.9.0

Requires:      python-setuptools

%description
Shake VMs with our sheer-class tests!

%package doc
Summary:    Documentation for Shaker
Group:      Documentation

BuildRequires: python-sphinx
BuildRequires: python-sphinxcontrib-httpdomain

%description doc
Documentation for the Shacker.

%prep
%setup -q

rm -f test-requirements.txt requirements.txt
rm -rf python_shaker.egg-info

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot}

rm -fr %{buildroot}%{python_sitelib}/tests

export PYTHONPATH="$( pwd ):$PYTHONPATH"
sphinx-build -b html doc/source html
sphinx-build -b man doc/source man
install -p -D -m 644 man/shaker.1 %{buildroot}%{_mandir}/man1/shaker.1

rm -fr html/.doctrees html/.buildinfo

%files
%doc LICENSE README.rst
%{_bindir}/shaker*
%{python_sitelib}/shaker
%{python_sitelib}/*.egg-info
%{_mandir}/man1/shaker.1*

%files doc
%doc LICENSE html

%changelog



