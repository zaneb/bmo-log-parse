%global srcname bmo-log-parse

# Macros for pyproject (Fedora) vs. setup.py (CentOS)
%if 0%{?fedora}
%bcond_without pyproject
%else
%bcond_with pyproject
%endif

Name:           python-%{srcname}
Version:        0.1.3
Release:        1%{?dist}
Summary:        Utility for logs from the Metal³ baremetal-operator
License:        ASL 2.0
URL:            https://github.com/zaneb/%{srcname}
Source0:        https://github.com/zaneb/%{srcname}/archive/refs/tags/v%{version}.tar.gz

BuildArch:      noarch

%global _description %{expand:
Utility for filtering and displaying logs from the Metal³ baremetal-operator.}


%description %_description

%package -n python3-%{srcname}
Summary:        %{summary}
BuildRequires:  python3-devel

%if %{with pyproject}
BuildRequires:  pyproject-rpm-macros
%else
BuildRequires:  %{py3_dist autopage} >= 0.3
BuildRequires:  %{py3_dist PyYAML}
%endif

Requires:       %{py3_dist autopage} >= 0.3
Requires:       %{py3_dist PyYAML}

%description -n python3-%{srcname} %_description

%prep
%autosetup -n %{srcname}-%{version}
sed -i -e '/^#!/ d' bmo_log_parse.py

%if %{with pyproject}
%generate_buildrequires
%pyproject_buildrequires -e pep8,%{toxenv}
%endif

%build
%if %{with pyproject}
%pyproject_wheel
%else
%py3_build
%endif

%install
%if %{with pyproject}
%pyproject_install
%pyproject_save_files bmo_log_parse
%else
%py3_install
%endif

%check
%if %{with pyproject}
%tox
%else
%{python3} setup.py test
%endif

%if %{with pyproject}
%files -n python3-%{srcname} -f %{pyproject_files}
%else
%files -n python3-%{srcname}
%{python3_sitelib}/bmo_log_parse-*.egg-info/
%{python3_sitelib}/bmo_log_parse.py
%{python3_sitelib}/__pycache__/bmo_log_parse.*
%endif
%license LICENSE
%doc README.md
%{_bindir}/bmo-log-parse

%changelog
* Mon Aug 23 2021 Zane Bitter <zaneb@fedoraproject.org> 0.1.3-1
- Fix bug with error logs at BMO startup.

* Tue Jun 29 2021 Zane Bitter <zaneb@fedoraproject.org> 0.1.2-1
- Fix bugs with controller-runtime error logs in recent versions of the BMO.

* Fri Jun 25 2021 Zane Bitter <zaneb@fedoraproject.org> 0.1.1-1
- Pick up packaging improvements from main branch

* Fri Jun 25 2021 Zane Bitter <zaneb@fedoraproject.org> 0.1.0-6
- Add runtime requirements for EPEL

* Fri Jun 25 2021 Zane Bitter <zaneb@fedoraproject.org> 0.1.0-5
- Support building for EPEL

* Fri Jun 25 2021 Zane Bitter <zaneb@fedoraproject.org> 0.1.0-4
- Remove debugging

* Fri Jun 25 2021 Zane Bitter <zaneb@fedoraproject.org> 0.1.0-3
- Fix requirement version format
- Remove #! line from module

* Fri Jun 25 2021 Zane Bitter <zaneb@fedoraproject.org> 0.1.0-2
- Add runtime requirements

* Fri Jun 18 2021 Zane Bitter <zaneb@fedoraproject.org> 0.1.0-1
- Initial build
