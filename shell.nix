{
  pkgs ? import <nixpkgs> { },

}:

pkgs.mkShell {
  buildInputs = [
    pkgs.moon
  ];

  shellHook = ''
    exec ${pkgs.zsh}/bin/zsh
  '';
}
