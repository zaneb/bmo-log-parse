%global srcname bmo-log-parse

Name:           python-%{srcname}
Version:        0.1.0
Release:        4%{?dist}
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
BuildRequires:  pyproject-rpm-macros

Requires:       %{py3_dist autopage} >= 0.3
Requires:       %{py3_dist PyYAML} < 6.0

%description -n python3-%{srcname} %_description

%prep
%autosetup -n %{srcname}-%{version}
sed -i -e '/^#!/ d' bmo_log_parse.py

%generate_buildrequires
%pyproject_buildrequires -e pep8,%{toxenv}

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files bmo_log_parse

%check
%tox

%files -n python3-%{srcname} -f %{pyproject_files}
%license LICENSE
%doc README.md
%{_bindir}/bmo-log-parse

%changelog
* Fri Jun 25 2021 Zane Bitter <zaneb@fedoraproject.org> 0.1.0-4
- Remove debugging

* Fri Jun 25 2021 Zane Bitter <zaneb@fedoraproject.org> 0.1.0-3
- Fix requirement version format
- Remove #! line from module

* Fri Jun 25 2021 Zane Bitter <zaneb@fedoraproject.org> 0.1.0-2
- Add runtime requirements

* Fri Jun 18 2021 Zane Bitter <zaneb@fedoraproject.org> 0.1.0-1
- Initial build
