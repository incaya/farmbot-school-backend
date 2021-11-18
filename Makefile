test:
ifdef res
	pytest -vs resources/${res}_test.py
else
	pytest -vs
endif