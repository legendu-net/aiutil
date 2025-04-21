{pkgs, ...}: {
  channel = "stable-24.11";
  packages = with pkgs; [
    neovim
    ripgrep
    rm-improved
    bat
    python311
    python311Packages.pip
    poetry
  ];
  env = {};
  idx = {
    # check extensions on https://open-vsx.org/
    extensions = [
      "asvetliakov.vscode-neovim"
      "ms-python.python"
      "ms-python.debugpy"
    ];
    workspace = {
      #onCreate = {
      #}
      onStart = {
        poetry-project = ''
        poetry config --local virtualenvs.in-project true
        poetry install
        '';
      };
    };
    # Enable previews and customize configuration
    previews = {};
  };
}
