# vhs tape for the ReviewLens demo GIF.
#   brew install vhs      # or: go install github.com/charmbracelet/vhs@latest
#   vhs work/demo/demo.tape
# Produces docs/demo.gif. Run from the repo root with a warm cache.

Output docs/demo.gif

Set Shell    "bash"
Set FontSize 15
Set Width    1400
Set Height   860
Set Padding  18
Set Theme    "Catppuccin Mocha"
Set TypingSpeed 45ms
Set PlaybackSpeed 1.0

Type "bash work/demo/demo.sh"
Enter
Sleep 95s
