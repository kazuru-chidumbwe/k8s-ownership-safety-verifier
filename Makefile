.PHONY: smoke smoke-fixtures smoke-kind kind-up kind-down help matrix matrix-statefulset kind-up-v135 matrix-v135

help:
	@echo "Targets: smoke-fixtures | kind-up | smoke-kind | smoke | matrix | matrix-statefulset | kind-up-v135 | matrix-v135 | kind-down"

smoke-fixtures:
	python3 experiments/run_fixture_smoke.py

kind-up:
	bash deploy/kind/ensure-tools.sh
	@if ! kind get clusters 2>/dev/null | grep -qx kosv; then \
		kind create cluster --config deploy/kind/cluster.yaml --wait 300s; \
	fi
	kind export kubeconfig --name kosv
	kubectl cluster-info --context kind-kosv

kind-down:
	kind delete cluster --name kosv || true

smoke-kind: kind-up
	python3 experiments/run_kind_smoke.py

smoke: smoke-fixtures smoke-kind
	@echo "SMOKE COMPLETE"

matrix: kind-up
	python3 experiments/run_matrix.py

matrix-statefulset: kind-up
	python3 experiments/run_matrix.py --path statefulset

kind-up-v135:
	bash deploy/kind/ensure-tools.sh
	@kind delete cluster --name kosv 2>/dev/null || true
	kind create cluster --config deploy/kind/cluster-v1.35.yaml --wait 300s
	kind export kubeconfig --name kosv
	kubectl cluster-info --context kind-kosv

matrix-v135: kind-up-v135
	python3 experiments/run_matrix.py --path deployment
