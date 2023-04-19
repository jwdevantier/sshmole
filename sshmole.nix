{ python3Packages
, fetchFromGithub
, sshuttle
, sshconf
, unixtools
}:
let
  buildPythonPackage = python3Packages.buildPythonPackage;
in
  buildPythonPackage rec {
    pname = "sshmole";
    version = "0.1.0";
    # src = fetchFromGithub {
    #   owner = "jwdevantier";
    #   repo = "sshmole";
    #   rev = "4dea505920d1473fe3ce32ea994a0faf3e73ac91";
    #   hash = "";
    # };
    src = ./.;
    doCheck = false;
    buildInputs = [ sshuttle sshconf unixtools.netstat ];
    propagatedBuildInputs = with python3Packages; [
      click
      pydantic
      pyyaml
      typer
      typing-extensions
    ] ++ [ sshconf sshuttle ];
    meta = {};
  }
