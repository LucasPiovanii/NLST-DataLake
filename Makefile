activate-env:
	source .venv/bin/activate

tmux-create:
	tmux new -s nlst-datalake

tmux-attach:
	tmux attach -t nlst-datalake

tmux-kill:
	tmux kill-session -t nlst-datalake

tmux-list:
	tmux ls