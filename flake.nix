{
  description = "nix starter flake pinned to 22.11";

  inputs = { nixpkgs.url = "github:NixOS/nixpkgs/nixos-22.11"; };

  outputs = { self, nixpkgs }:
    let
      allSystems = [
        "x86_64-linux" # AMD/Intel Linux
        "x86_64-darwin" # AMD/Intel macOS
        "aarch64-linux" # ARM Linux
        "aarch64-darwin" # ARM macOS
      ];

      forAllSystems = fn:
        nixpkgs.lib.genAttrs allSystems
        (system: fn { pkgs = import nixpkgs { inherit system; }; });

    in {
      # used when calling `nix fmt <path/to/flake.nix>`
      #formatter = forAllSystems ({ pkgs }: pkgs.nixfmt);

      # nix develop <flake-ref>#<name>
      # -- 
      # $ nix develop <flake-ref>#blue
      # $ nix develop <flake-ref>#yellow
      devShells = forAllSystems ({ pkgs }: {
        default = pkgs.mkShell {
          name = "nixdev";
          nativeBuildInputs = with self.packages.${pkgs.system}; [
            sshmole
          ];
        };
      });

      # nix run|build <flake-ref>#<pkg-name>
      # -- 
      # $ nix run <flake-ref>#hello
      # $ nix run <flake-ref>#cowsay
      packages = forAllSystems ({ pkgs }: rec {
        sshconf = pkgs.callPackage ./sshconf.nix {};
        sshmole = pkgs.callPackage ./sshmole.nix { inherit sshconf; };
      });
    };
}
