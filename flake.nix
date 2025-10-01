{
  description = "A tool to monitor data-pipeline.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";

    utils.url = "github:numtide/flake-utils";

  };

  outputs = { self, nixpkgs, ... }@inputs: { 
    overlays.dev = nixpkgs.lib.composeManyExtensions [
        ];
      } // inputs.utils.lib.eachSystem [ "x86_64-linux" ] (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
          overlays = [ self.overlays.dev ];
        };
      in {
        devShells.default = pkgs.callPackage ./pkgs/dev-shell { };
      });
}
