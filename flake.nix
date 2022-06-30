{
  description = "TCP Proxy";

  inputs.nixpkgs.url = "github:nixos/nixpkgs/22.05";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = {self, flake-utils, nixpkgs}: 
    flake-utils.lib.eachDefaultSystem (system:
  let
    pkgs = import nixpkgs { inherit system; };
  in
  {
    defaultPackage = pkgs.poetry2nix.mkPoetryApplication {
      projectDir = ./.;
    };
  });
}
