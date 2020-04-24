.PHONY: doc

doc:
	$(MAKE) -C doc html
	open doc/_build/html/index.html
