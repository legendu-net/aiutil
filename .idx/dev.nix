{pkgs, ...}: {
  channel = "stable-24.11";
  packages = with pkgs; [
    bash-completion
    gitui
    neovim
    ripgrep
    rm-improved
    bat
    fzf
    uv
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
