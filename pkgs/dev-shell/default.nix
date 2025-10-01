{ pkgs, mkShell, attr, ... }:

let
  customizedPython = pkgs.python3.withPackages (python-packages:
    with python-packages; [
      # For both Dev and Deploy
      click
      pytz
      tqdm
      loguru
      numpy
      jupyterlab
      ipywidgets
      pyshark
      curl-cffi
      pycryptodome
      # wechatpy
      six
    ]);

  pythonIcon = "f3e2"; # https://fontawesome.com/v5.15/icons/python?style=brands

in mkShell rec {
  name = "seckill";

  packages = with pkgs; [ pkgs.poetry customizedPython pre-commit tshark ];

  shellHook = ''
    export PS1="$(echo -e '\u${pythonIcon}') {\[$(tput sgr0)\]\[\033[38;5;228m\]\w\[$(tput sgr0)\]\[\033[38;5;15m\]} (${name}) \\$ \[$(tput sgr0)\]"
  '';

  buildInputs = [ attr ];
}
