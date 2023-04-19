{ python3Packages
}:
let
  buildPythonPackage = python3Packages.buildPythonPackage;
  fetchPypi = python3Packages.fetchPypi;
in
  buildPythonPackage rec {
    pname = "sshconf";
    version = "0.2.5";
    format = "pyproject";

    src = fetchPypi {
      inherit pname version;
      sha256 = "sha256-6KOEyvtjRtCJLZvWj8C+gWBLwkefGdqmlQ582G6OXCc=";
    };
    doCheck = false;
    buildInputs = [ ];
    nativeBuildInputs = [ python3Packages.flit ];
    propagatedBuildInputs = [];
    meta = {};
  }
