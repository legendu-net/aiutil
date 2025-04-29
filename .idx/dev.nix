{pkgs, ...}: {
  channel = "stable-24.11";
  packages = with pkgs; [
    bash-completion
    gitui
    neovim
    ripgrep
    rm-improved
    bat
    poetry
  ];
  env = {
    PATH = [
      "$HOME/.local/bin"
    ];
  };
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
          icon = ''
        curl -sSL https://raw.githubusercontent.com/legendu-net/icon/main/install_icon.sh | bash -s -- \
            -d ~/.local/bin
        '';
      };
    };
    # Enable previews and customize configuration
    previews = {};
  };
}
