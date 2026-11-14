#!/bin/bash
curl -fsS -o ~/.config/starship.toml http://10.0.2.2:8000/files/os/starship.toml && echo "prompt arrow: sky blue"
sed -i "s/38;2;242;169;122m/38;2;143;180;230m/" ~/.bashrc && echo "greeting: sky blue"
