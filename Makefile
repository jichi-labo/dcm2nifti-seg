include .env
.PHONY: run_preprocessing run_totalsegmentator run_suprem

run_preprocessing:
	docker compose run --rm preprocess

run_totalsegmentator:
	docker compose run --rm totalsegmentator

run_suprem:
	docker compose run --rm suprem