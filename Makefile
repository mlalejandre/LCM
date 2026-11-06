.PHONY: install test data reproduce quick think manifiesto verificar desde-cero
install:
	python -m pip install -r requirements.txt
check:
	python -m scripts.check
test:
	python -m pytest -q tests
data:
	python -m scripts.get_data
reproduce:
	python -m scripts.reproduce
quick:
	python -m scripts.reproduce --rapido
think:
	python -m scripts.think
manifiesto:
	python -m scripts.manifiesto --guardar
verificar:
	python -m scripts.manifiesto --verificar --metricas
desde-cero:
	python -m scripts.empaquetar_todo
